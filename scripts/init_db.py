#!/usr/bin/env python3
"""Initialize database and create tables"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, engine, init_db
from app.models import User, Host, Script, Task, TaskExecution, Log, PingHistory


def main():
    """Initialize database"""
    print("Initializing database...")

    try:
        # Create all tables
        init_db()

        print("✓ Database initialized successfully!")
        print(f"✓ Database location: {engine.url}")
        print("\nCreated tables:")
        print("  - users")
        print("  - hosts")
        print("  - scripts")
        print("  - tasks")
        print("  - task_executions")
        print("  - logs")
        print("  - ping_history")

        print("\nNext step: Run 'python scripts/create_admin.py' to create admin user")

    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
