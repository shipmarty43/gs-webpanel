#!/usr/bin/env python3
"""Initialize default settings in database"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.settings import Settings


DEFAULT_SETTINGS = [
    {
        "key": "host_check_interval",
        "value": "180",
        "value_type": "int",
        "category": "monitoring",
        "description": "Interval in seconds between host availability checks (default: 180 = 3 minutes)"
    },
    {
        "key": "ping_timeout",
        "value": "10",
        "value_type": "int",
        "category": "monitoring",
        "description": "Timeout in seconds for ping/connection tests (default: 10)"
    },
    {
        "key": "max_concurrent_tasks",
        "value": "150",
        "value_type": "int",
        "category": "tasks",
        "description": "Maximum number of tasks that can run concurrently (default: 150)"
    },
    {
        "key": "default_task_timeout",
        "value": "300",
        "value_type": "int",
        "category": "tasks",
        "description": "Default timeout in seconds for task execution (default: 300 = 5 minutes)"
    },
    {
        "key": "default_gsocket_wait",
        "value": "10",
        "value_type": "int",
        "category": "gsocket",
        "description": "Default wait time for gsocket listener in seconds (default: 10)"
    },
    {
        "key": "log_retention_days",
        "value": "90",
        "value_type": "int",
        "category": "maintenance",
        "description": "Number of days to retain logs before cleanup (default: 90)"
    },
    {
        "key": "task_retention_days",
        "value": "180",
        "value_type": "int",
        "category": "maintenance",
        "description": "Number of days to retain task history (default: 180)"
    }
]


def init_settings():
    """Initialize default settings"""
    db = SessionLocal()

    try:
        print("Initializing default settings...")

        for setting_data in DEFAULT_SETTINGS:
            # Check if setting already exists
            existing = db.query(Settings).filter(Settings.key == setting_data["key"]).first()

            if existing:
                print(f"  ✓ {setting_data['key']} already exists (value: {existing.value})")
            else:
                setting = Settings(**setting_data)
                db.add(setting)
                print(f"  + Created {setting_data['key']} = {setting_data['value']}")

        db.commit()
        print("\n✓ Settings initialized successfully!")

    except Exception as e:
        print(f"✗ Failed to initialize settings: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    init_settings()
