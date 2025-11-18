"""Application configuration"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "dev-encryption-key-change-in-production"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./data/c2panel.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 3000
    WORKERS: int = 4

    # Security
    SESSION_TIMEOUT: int = 28800  # 8 hours
    PASSWORD_MIN_LENGTH: int = 12
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Monitoring
    HOST_CHECK_INTERVAL: int = 180  # 3 minutes
    PING_TIMEOUT: int = 10

    # Tasks
    MAX_CONCURRENT_TASKS: int = 150
    DEFAULT_TASK_TIMEOUT: int = 300
    DEFAULT_GSOCKET_WAIT: int = 10

    # GSocket / GSRN
    DEFAULT_GSRN_SERVER: Optional[str] = None  # e.g., "relay.example.com:443"
    GSRN_CONNECT_TIMEOUT: int = 30
    ENABLE_CUSTOM_GSRN: bool = True  # Allow hosts to use custom GSRN servers

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 90
    TASK_RETENTION_DAYS: int = 180

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
