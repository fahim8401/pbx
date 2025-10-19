"""
Application settings from environment variables
"""
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://hplink:hplink@localhost/hplink_pbx"

    # Security
    JWT_SECRET: str = "change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # HMAC Auth
    HMAC_CLOCK_SKEW_SECONDS: int = 300

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # PBX Core
    PBX_CORE_URL: str = "http://localhost:5000"

    # Storage
    STORAGE_ROOT: str = "/var/lib/hplink-pbx/storage"
    RECORDINGS_ROOT: str = "/var/lib/hplink-pbx/recordings"

    # SMTP (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@hplinkpbx.com"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
