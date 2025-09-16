"""
⚙️ Pydantic Settings Configuration
Secure configuration management with environment variable validation

Features:
- Type-safe environment variables
- Automatic validation
- Secure defaults
- Environment-specific configurations
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    🔐 Application settings with secure defaults and validation
    """
    
    # Database Configuration
    mongo_url: str = Field(
        default="mongodb://localhost:27017",
        env="MONGO_URL",
        description="MongoDB connection URL"
    )
    
    db_name: str = Field(
        default="license_management",
        env="DB_NAME", 
        description="Database name"
    )
    
    # Security Configuration  
    secret_key: str = Field(
        ...,  # Required
        env="SECRET_KEY",
        min_length=32,
        description="JWT secret key (min 32 characters)"
    )
    
    algorithm: str = Field(
        default="HS256",
        env="JWT_ALGORITHM",
        description="JWT signing algorithm"
    )
    
    access_token_expire_minutes: int = Field(
        default=15,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=5,  # At least 5 minutes
        le=60,  # At most 1 hour
        description="Access token expiration time in minutes"
    )
    
    refresh_token_expire_days: int = Field(
        default=7,
        env="REFRESH_TOKEN_EXPIRE_DAYS", 
        ge=1,  # At least 1 day
        le=30,  # At most 30 days
        description="Refresh token expiration time in days"
    )
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000",
        env="CORS_ORIGINS",
        description="Allowed CORS origins (comma-separated)"
    )
    
    allow_credentials: bool = Field(
        default=True,
        env="ALLOW_CREDENTIALS",
        description="Allow credentials in CORS requests"
    )
    
    # HTTPS Configuration
    https_enabled: bool = Field(
        default=False,
        env="HTTPS_ENABLED",
        description="Enable HTTPS-only cookies"
    )
    
    # Redis Configuration (for caching and sessions)
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    
    redis_password: Optional[str] = Field(
        default=None,
        env="REDIS_PASSWORD",
        description="Redis password if required"
    )
    
    # Application Configuration
    environment: str = Field(
        default="development",
        env="ENVIRONMENT",
        pattern="^(development|staging|production)$",
        description="Application environment"
    )
    
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )
    
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    
    # Multi-tenant Configuration
    default_tenant_id: str = Field(
        default="default",
        env="DEFAULT_TENANT_ID",
        description="Default tenant ID for system"
    )
    
    tenant_isolation_enabled: bool = Field(
        default=True,
        env="TENANT_ISOLATION_ENABLED",
        description="Enable strict tenant isolation"
    )
    
    # Feature Flags
    seed_demo_data: bool = Field(
        default=True,
        env="SEED_DEMO",
        description="Seed demo data on startup"
    )
    
    whatsapp_integration_enabled: bool = Field(
        default=True,
        env="WHATSAPP_ENABLED",
        description="Enable WhatsApp integration"
    )
    
    notifications_enabled: bool = Field(
        default=True,
        env="NOTIFICATIONS_ENABLED", 
        description="Enable notification system"
    )
    
    # Email Configuration
    email_sender: str = Field(
        default="no-reply@licensemanager.local",
        env="EMAIL_SENDER",
        description="Default email sender address"
    )
    
    frontend_base_url: str = Field(
        default="http://localhost:3000",
        env="FRONTEND_BASE_URL",
        description="Frontend base URL for links"
    )
    
    # Invitation System
    invite_ttl_seconds: int = Field(
        default=604800,  # 7 days
        env="INVITE_TTL_SECONDS",
        ge=3600,  # At least 1 hour
        description="Invitation expiration time in seconds"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        env="RATE_LIMIT_ENABLED",
        description="Enable rate limiting"
    )
    
    rate_limit_requests: int = Field(
        default=100,
        env="RATE_LIMIT_REQUESTS",
        ge=10,
        description="Requests per minute per IP"
    )
    
    # Security Headers
    security_headers_enabled: bool = Field(
        default=True,
        env="SECURITY_HEADERS_ENABLED",
        description="Enable security headers middleware"
    )
    
    # Timezone
    timezone: str = Field(
        default="UTC",
        env="TZ",
        description="Application timezone"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            # Remove quotes if present and split by comma
            v = v.strip('"\'')
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Ensure secret key is strong enough"""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("cors_origins")
    def validate_cors_origins(cls, v, values):
        """Validate CORS configuration"""
        allow_credentials = values.get("allow_credentials", True)
        if allow_credentials and "*" in v:
            raise ValueError("Cannot use wildcard CORS origins with credentials enabled")
        return v
    
    @validator("environment")
    def set_debug_based_on_env(cls, v, values):
        """Automatically disable debug in production"""
        if v == "production":
            values["debug"] = False
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env
        
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    @property
    def database_url(self) -> str:
        """Get complete database URL"""
        return f"{self.mongo_url}/{self.db_name}"


# Create global settings instance
settings = Settings()

# Validation functions for runtime checks

def validate_production_settings():
    """Validate settings for production deployment"""
    if not settings.is_production:
        return True
        
    issues = []
    
    # Check critical security settings
    if settings.debug:
        issues.append("Debug mode should be disabled in production")
    
    if settings.secret_key == "your-super-secret-key-change-in-production":
        issues.append("Default secret key detected - change in production")
    
    if not settings.https_enabled:
        issues.append("HTTPS should be enabled in production")
        
    if "localhost" in str(settings.cors_origins):
        issues.append("Localhost CORS origins detected in production")
    
    if issues:
        raise ValueError(f"Production validation failed: {'; '.join(issues)}")
    
    return True


def get_database_info() -> dict:
    """Get database connection information"""
    return {
        "mongo_url": settings.mongo_url,
        "db_name": settings.db_name,
        "database_url": settings.database_url
    }


def get_security_info() -> dict:
    """Get security configuration (safe for logging)"""
    return {
        "access_token_expire_minutes": settings.access_token_expire_minutes,
        "refresh_token_expire_days": settings.refresh_token_expire_days,
        "https_enabled": settings.https_enabled,
        "cors_origins_count": len(settings.cors_origins),
        "environment": settings.environment,
        "tenant_isolation_enabled": settings.tenant_isolation_enabled
    }


# Export commonly used settings
__all__ = [
    "settings",
    "Settings", 
    "validate_production_settings",
    "get_database_info",
    "get_security_info"
]