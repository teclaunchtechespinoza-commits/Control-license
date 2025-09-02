import os, re
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request, HTTPException, status

TENANT_DB_PREFIX = os.getenv("TENANT_DB_PREFIX", "licenser_")
_mongo_client: Optional[AsyncIOMotorClient] = None

def init_mongo(uri: str) -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(uri)
    return _mongo_client

def _sanitize(tid: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "-", tid.lower())[:48]

def db_name_for(tenant_id: str) -> str:
    return f"{TENANT_DB_PREFIX}{_sanitize(tenant_id)}"

def resolve_tenant_db(request: Request):
    db = getattr(request.state, "db", None)
    if db is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant DB não resolvido")
    return db

def current_tenant(request: Request) -> str:
    tid = getattr(request.state, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tenant context")
    return tid
