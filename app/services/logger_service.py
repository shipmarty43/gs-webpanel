"""Logging service for centralized application logging"""
import logging
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.log import Log
from app.config import settings


# Configure Python logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class LoggerService:
    """Service for logging to database and console"""

    @staticmethod
    def log(
        db: Session,
        level: str,
        message: str,
        category: Optional[str] = None,
        host_id: Optional[int] = None,
        task_id: Optional[int] = None,
        details: Optional[dict] = None
    ):
        """
        Log a message to database and console

        Args:
            db: Database session
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            message: Log message
            category: Log category (connection, execution, system, auth)
            host_id: Related host ID (optional)
            task_id: Related task ID (optional)
            details: Additional details as dict (optional)
        """
        try:
            # Log to console
            log_func = getattr(logger, level.lower(), logger.info)
            console_msg = f"[{category or 'general'}] {message}"
            if host_id:
                console_msg += f" | Host ID: {host_id}"
            if task_id:
                console_msg += f" | Task ID: {task_id}"
            log_func(console_msg)

            # Log to database
            log_entry = Log(
                level=level.upper(),
                category=category,
                host_id=host_id,
                task_id=task_id,
                message=message,
                details=json.dumps(details) if details else None
            )
            db.add(log_entry)
            db.commit()

        except Exception as e:
            logger.error(f"Failed to write log to database: {e}")

    @staticmethod
    def info(db: Session, message: str, **kwargs):
        """Log INFO level message"""
        LoggerService.log(db, "INFO", message, **kwargs)

    @staticmethod
    def warning(db: Session, message: str, **kwargs):
        """Log WARNING level message"""
        LoggerService.log(db, "WARNING", message, **kwargs)

    @staticmethod
    def error(db: Session, message: str, **kwargs):
        """Log ERROR level message"""
        LoggerService.log(db, "ERROR", message, **kwargs)

    @staticmethod
    def debug(db: Session, message: str, **kwargs):
        """Log DEBUG level message"""
        LoggerService.log(db, "DEBUG", message, **kwargs)


# Singleton instance
logger_service = LoggerService()
