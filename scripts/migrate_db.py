#!/usr/bin/env python3
"""Database migration script - Adds missing columns to existing database"""
import sys
import os
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings


def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_database():
    """Apply database migrations"""
    # Extract database path from DATABASE_URL (e.g., "sqlite:///./data/c2panel.db")
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        # Handle relative paths
        if db_path.startswith("./"):
            db_path = db_path[2:]
    else:
        print("✗ Only SQLite databases are supported for migration")
        sys.exit(1)

    print("========================================")
    print("Database Migration")
    print("========================================")
    print(f"Database: {db_path}")
    print("")

    if not os.path.exists(db_path):
        print("✗ Database file not found, skipping migration")
        return

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        migrations_applied = 0

        # Migration 1: Add custom_gsrn_server column to hosts table
        if not column_exists(cursor, 'hosts', 'custom_gsrn_server'):
            print("→ Adding 'custom_gsrn_server' column to hosts table...")
            cursor.execute("""
                ALTER TABLE hosts
                ADD COLUMN custom_gsrn_server VARCHAR(255)
            """)
            conn.commit()
            print("✓ Column 'custom_gsrn_server' added")
            migrations_applied += 1
        else:
            print("✓ Column 'custom_gsrn_server' already exists")

        # Migration 2: Create settings table
        if not table_exists(cursor, 'settings'):
            print("→ Creating 'settings' table...")
            cursor.execute("""
                CREATE TABLE settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    value_type VARCHAR(20) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    description TEXT
                )
            """)
            cursor.execute("CREATE INDEX ix_settings_key ON settings(key)")
            conn.commit()
            print("✓ Table 'settings' created")
            migrations_applied += 1

            # Initialize default settings
            print("→ Initializing default settings...")
            import subprocess
            subprocess.run([sys.executable, "scripts/init_settings.py"], check=True)
            print("✓ Default settings initialized")

        else:
            print("✓ Table 'settings' already exists")

        # Migration 3: Add category column to scripts table
        if table_exists(cursor, 'scripts') and not column_exists(cursor, 'scripts', 'category'):
            print("→ Adding 'category' column to scripts table...")
            cursor.execute("""
                ALTER TABLE scripts
                ADD COLUMN category VARCHAR(50)
            """)
            conn.commit()
            print("✓ Column 'category' added")
            migrations_applied += 1
        elif table_exists(cursor, 'scripts'):
            print("✓ Column 'category' already exists")

        # Future migrations can be added here
        # Example:
        # if not column_exists(cursor, 'table_name', 'new_column'):
        #     print("→ Adding 'new_column' to table_name...")
        #     cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TYPE")
        #     conn.commit()
        #     migrations_applied += 1

        conn.close()

        print("")
        print("========================================")
        if migrations_applied > 0:
            print(f"✓ Applied {migrations_applied} migration(s)")
        else:
            print("✓ Database is up to date")
        print("========================================")
        print("")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()
