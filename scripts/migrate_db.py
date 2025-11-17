#!/usr/bin/env python3
"""Database migration script - Adds missing columns to existing database"""
import sys
import os
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings


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
