from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from enum import Enum
import os
import logging
import uuid
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="License Management System", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"

# Pydantic Models
class UserBase(BaseModel):
    email: str
    name: str
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class LicenseBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_users: int = 1
    expires_at: Optional[datetime] = None
    features: List[str] = []

class LicenseCreate(LicenseBase):
    assigned_user_id: Optional[str] = None

class License(LicenseBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    license_key: str = Field(default_factory=lambda: f"LIC-{uuid.uuid4().hex[:16].upper()}")
    status: LicenseStatus = LicenseStatus.PENDING
    assigned_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class LicenseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[LicenseStatus] = None
    max_users: Optional[int] = None
    expires_at: Optional[datetime] = None
    assigned_user_id: Optional[str] = None
    features: Optional[List[str]] = None

# Utility Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication Routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict(exclude={"password"})
    user_dict["password_hash"] = hashed_password
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": user_credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login
    await db.users.update_one(
        {"email": user_credentials.email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_credentials.email}, expires_delta=access_token_expires
    )
    
    user = User(**user_doc)
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# User Management Routes (Admin only)
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_admin_user)):
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User role updated successfully"}

# License Management Routes
@api_router.post("/licenses", response_model=License)
async def create_license(
    license_data: LicenseCreate,
    current_user: User = Depends(get_current_admin_user)
):
    license_dict = license_data.dict()
    license_dict["created_by"] = current_user.id
    
    license = License(**license_dict)
    await db.licenses.insert_one(license.dict())
    
    return license

@api_router.get("/licenses", response_model=List[License])
async def get_licenses(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        # Admin can see all licenses
        licenses = await db.licenses.find().to_list(1000)
    else:
        # Regular users can only see their assigned licenses
        licenses = await db.licenses.find({"assigned_user_id": current_user.id}).to_list(1000)
    
    return [License(**license) for license in licenses]

@api_router.get("/licenses/{license_id}", response_model=License)
async def get_license(license_id: str, current_user: User = Depends(get_current_user)):
    license_doc = await db.licenses.find_one({"id": license_id})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    license = License(**license_doc)
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and license.assigned_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return license

@api_router.put("/licenses/{license_id}", response_model=License)
async def update_license(
    license_id: str,
    license_update: LicenseUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in license_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.licenses.update_one(
        {"id": license_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License not found")
    
    updated_license = await db.licenses.find_one({"id": license_id})
    return License(**updated_license)

@api_router.delete("/licenses/{license_id}")
async def delete_license(
    license_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.licenses.delete_one({"id": license_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="License not found")
    
    return {"message": "License deleted successfully"}

# Dashboard Stats (Admin)
@api_router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_admin_user)):
    total_licenses = await db.licenses.count_documents({})
    active_licenses = await db.licenses.count_documents({"status": LicenseStatus.ACTIVE})
    total_users = await db.users.count_documents({})
    expired_licenses = await db.licenses.count_documents({"status": LicenseStatus.EXPIRED})
    
    return {
        "total_licenses": total_licenses,
        "active_licenses": active_licenses,
        "total_users": total_users,
        "expired_licenses": expired_licenses
    }

# Demo credentials endpoint
@api_router.get("/demo-credentials")
async def get_demo_credentials():
    return {
        "admin": {
            "email": "admin@demo.com",
            "password": "admin123"
        },
        "user": {
            "email": "user@demo.com", 
            "password": "user123"
        }
    }

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_client():
    # Create demo users on startup if they don't exist
    admin_exists = await db.users.find_one({"email": "admin@demo.com"})
    if not admin_exists:
        admin_user = User(
            email="admin@demo.com",
            name="Demo Admin",
            role=UserRole.ADMIN
        )
        admin_dict = admin_user.dict()
        admin_dict["password_hash"] = get_password_hash("admin123")
        await db.users.insert_one(admin_dict)
        logger.info("Demo admin user created")
    
    user_exists = await db.users.find_one({"email": "user@demo.com"})
    if not user_exists:
        demo_user = User(
            email="user@demo.com",
            name="Demo User",
            role=UserRole.USER
        )
        user_dict = demo_user.dict()
        user_dict["password_hash"] = get_password_hash("user123")
        await db.users.insert_one(user_dict)
        logger.info("Demo regular user created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()