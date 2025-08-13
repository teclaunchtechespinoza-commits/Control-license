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

class CompanySize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"

# Base Models
class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# User Models
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

# Category Models
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    icon: Optional[str] = "folder"

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase, BaseEntity):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None

# Company Models
class CompanyBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "Brasil"
    website: Optional[str] = None
    size: CompanySize = CompanySize.SMALL
    notes: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase, BaseEntity):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    size: Optional[CompanySize] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

# Product Models
class ProductBase(BaseModel):
    name: str
    version: Optional[str] = "1.0"
    description: Optional[str] = None
    category_id: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "BRL"
    features: List[str] = []
    requirements: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase, BaseEntity):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    features: Optional[List[str]] = None
    requirements: Optional[str] = None
    is_active: Optional[bool] = None

# License Plan Models
class LicensePlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_users: int = 1
    duration_days: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = "BRL"
    features: List[str] = []
    restrictions: List[str] = []

class LicensePlanCreate(LicensePlanBase):
    pass

class LicensePlan(LicensePlanBase, BaseEntity):
    pass

class LicensePlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_users: Optional[int] = None
    duration_days: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    features: Optional[List[str]] = None
    restrictions: Optional[List[str]] = None
    is_active: Optional[bool] = None

# Enhanced License Models
class LicenseBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_users: int = 1
    expires_at: Optional[datetime] = None
    features: List[str] = []
    category_id: Optional[str] = None
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    plan_id: Optional[str] = None

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
    category_id: Optional[str] = None
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    plan_id: Optional[str] = None

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

# Category Management Routes
@api_router.post("/categories", response_model=Category)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_admin_user)
):
    category = Category(**category_data.dict())
    await db.categories.insert_one(category.dict())
    return category

@api_router.get("/categories", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await db.categories.find({"is_active": True}).to_list(1000)
    return [Category(**category) for category in categories]

@api_router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str, current_user: User = Depends(get_current_user)):
    category_doc = await db.categories.find_one({"id": category_id})
    if not category_doc:
        raise HTTPException(status_code=404, detail="Category not found")
    return Category(**category_doc)

@api_router.put("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in category_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updated_category = await db.categories.find_one({"id": category_id})
    return Category(**updated_category)

@api_router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    # Soft delete - just mark as inactive
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted successfully"}

# Company Management Routes
@api_router.post("/companies", response_model=Company)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_admin_user)
):
    company = Company(**company_data.dict())
    await db.companies.insert_one(company.dict())
    return company

@api_router.get("/companies", response_model=List[Company])
async def get_companies(current_user: User = Depends(get_current_user)):
    companies = await db.companies.find({"is_active": True}).to_list(1000)
    return [Company(**company) for company in companies]

@api_router.get("/companies/{company_id}", response_model=Company)
async def get_company(company_id: str, current_user: User = Depends(get_current_user)):
    company_doc = await db.companies.find_one({"id": company_id})
    if not company_doc:
        raise HTTPException(status_code=404, detail="Company not found")
    return Company(**company_doc)

@api_router.put("/companies/{company_id}", response_model=Company)
async def update_company(
    company_id: str,
    company_update: CompanyUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in company_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.companies.update_one(
        {"id": company_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    updated_company = await db.companies.find_one({"id": company_id})
    return Company(**updated_company)

@api_router.delete("/companies/{company_id}")
async def delete_company(
    company_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.companies.update_one(
        {"id": company_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {"message": "Company deleted successfully"}

# Product Management Routes
@api_router.post("/products", response_model=Product)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_admin_user)
):
    product = Product(**product_data.dict())
    await db.products.insert_one(product.dict())
    return product

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: User = Depends(get_current_user)):
    products = await db.products.find({"is_active": True}).to_list(1000)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, current_user: User = Depends(get_current_user)):
    product_doc = await db.products.find_one({"id": product_id})
    if not product_doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product_doc)

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated_product = await db.products.find_one({"id": product_id})
    return Product(**updated_product)

@api_router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

# License Plan Management Routes
@api_router.post("/license-plans", response_model=LicensePlan)
async def create_license_plan(
    plan_data: LicensePlanCreate,
    current_user: User = Depends(get_current_admin_user)
):
    plan = LicensePlan(**plan_data.dict())
    await db.license_plans.insert_one(plan.dict())
    return plan

@api_router.get("/license-plans", response_model=List[LicensePlan])
async def get_license_plans(current_user: User = Depends(get_current_user)):
    plans = await db.license_plans.find({"is_active": True}).to_list(1000)
    return [LicensePlan(**plan) for plan in plans]

@api_router.get("/license-plans/{plan_id}", response_model=LicensePlan)
async def get_license_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    plan_doc = await db.license_plans.find_one({"id": plan_id})
    if not plan_doc:
        raise HTTPException(status_code=404, detail="License plan not found")
    return LicensePlan(**plan_doc)

@api_router.put("/license-plans/{plan_id}", response_model=LicensePlan)
async def update_license_plan(
    plan_id: str,
    plan_update: LicensePlanUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in plan_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.license_plans.update_one(
        {"id": plan_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License plan not found")
    
    updated_plan = await db.license_plans.find_one({"id": plan_id})
    return LicensePlan(**updated_plan)

@api_router.delete("/license-plans/{plan_id}")
async def delete_license_plan(
    plan_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.license_plans.update_one(
        {"id": plan_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License plan not found")
    
    return {"message": "License plan deleted successfully"}

# License Management Routes (Enhanced)
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

# Enhanced Dashboard Stats (Admin)
@api_router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_admin_user)):
    total_licenses = await db.licenses.count_documents({})
    active_licenses = await db.licenses.count_documents({"status": LicenseStatus.ACTIVE})
    total_users = await db.users.count_documents({})
    expired_licenses = await db.licenses.count_documents({"status": LicenseStatus.EXPIRED})
    total_companies = await db.companies.count_documents({"is_active": True})
    total_products = await db.products.count_documents({"is_active": True})
    total_categories = await db.categories.count_documents({"is_active": True})
    
    return {
        "total_licenses": total_licenses,
        "active_licenses": active_licenses,
        "total_users": total_users,
        "expired_licenses": expired_licenses,
        "total_companies": total_companies,
        "total_products": total_products,
        "total_categories": total_categories
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
@api_router.get("/")
async def root():
    return {"message": "License Management System API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=['*'],  # Allow all origins for development
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

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
        
    # Create some demo data
    categories_exist = await db.categories.count_documents({}) > 0
    if not categories_exist:
        demo_categories = [
            {"name": "Software", "description": "Licenças de software", "color": "#3B82F6", "icon": "code"},
            {"name": "Office", "description": "Ferramentas de escritório", "color": "#10B981", "icon": "briefcase"},
            {"name": "Design", "description": "Ferramentas de design", "color": "#8B5CF6", "icon": "palette"},
            {"name": "Segurança", "description": "Ferramentas de segurança", "color": "#EF4444", "icon": "shield"}
        ]
        for cat_data in demo_categories:
            category = Category(**cat_data)
            await db.categories.insert_one(category.dict())
        logger.info("Demo categories created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()