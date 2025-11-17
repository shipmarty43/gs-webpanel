"""Settings service for managing application settings"""
from sqlalchemy.orm import Session
from app.models.settings import Settings
from app.database import SessionLocal
from app.config import settings as config_settings
import logging

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing application settings"""

    def __init__(self):
        self._cache = {}
        self._load_settings()

    def _load_settings(self):
        """Load all settings from database into cache"""
        db = SessionLocal()
        try:
            all_settings = db.query(Settings).all()
            for setting in all_settings:
                self._cache[setting.key] = setting.get_typed_value()
            logger.info(f"Loaded {len(self._cache)} settings from database")
        except Exception as e:
            logger.warning(f"Failed to load settings from database: {e}. Using defaults from config.")
        finally:
            db.close()

    def get(self, key: str, default=None):
        """
        Get setting value by key

        Priority:
        1. Database setting (if exists)
        2. Config file setting (if exists)
        3. Default value provided
        """
        # Try cache first
        if key in self._cache:
            return self._cache[key]

        # Try config
        if hasattr(config_settings, key.upper()):
            return getattr(config_settings, key.upper())

        return default

    def set(self, key: str, value, db: Session = None):
        """Update setting value"""
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        try:
            setting = db.query(Settings).filter(Settings.key == key).first()
            if setting:
                setting.set_typed_value(value)
                db.commit()
                # Update cache
                self._cache[key] = setting.get_typed_value()
                logger.info(f"Updated setting: {key} = {value}")
                return True
            else:
                logger.warning(f"Setting not found: {key}")
                return False
        except Exception as e:
            logger.error(f"Failed to update setting {key}: {e}")
            db.rollback()
            return False
        finally:
            if should_close_db:
                db.close()

    def get_all(self, db: Session = None) -> dict:
        """Get all settings as a dictionary"""
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        try:
            all_settings = db.query(Settings).all()
            result = {}
            for setting in all_settings:
                result[setting.key] = {
                    "value": setting.get_typed_value(),
                    "value_type": setting.value_type,
                    "category": setting.category,
                    "description": setting.description
                }
            return result
        finally:
            if should_close_db:
                db.close()

    def get_by_category(self, category: str, db: Session = None) -> dict:
        """Get all settings in a specific category"""
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        try:
            settings = db.query(Settings).filter(Settings.category == category).all()
            result = {}
            for setting in settings:
                result[setting.key] = {
                    "value": setting.get_typed_value(),
                    "value_type": setting.value_type,
                    "category": setting.category,
                    "description": setting.description
                }
            return result
        finally:
            if should_close_db:
                db.close()

    def reload(self):
        """Reload settings from database"""
        self._cache.clear()
        self._load_settings()
        logger.info("Settings reloaded from database")


# Singleton instance
settings_service = SettingsService()
