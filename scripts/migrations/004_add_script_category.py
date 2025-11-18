#!/usr/bin/env python3
"""
Migration: Add category column to scripts table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.database import SessionLocal, engine
from sqlalchemy import text


def migrate():
    """Add category column to scripts table"""
    db = SessionLocal()

    try:
        print("Running migration: Add category column to scripts table")

        # Check if column already exists
        result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('scripts')
            WHERE name = 'category'
        """)).fetchone()

        if result[0] > 0:
            print("  ✓ Category column already exists")
            return

        # Add category column
        db.execute(text("""
            ALTER TABLE scripts
            ADD COLUMN category VARCHAR(50)
        """))

        db.commit()
        print("  ✓ Category column added successfully")

    except Exception as e:
        print(f"  ✗ Migration failed: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    migrate()
