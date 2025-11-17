#!/usr/bin/env python3
"""
Database migration script to add custom_gsrn_server field to hosts table

This script adds support for custom GSRN (Global Socket Relay Network) servers
per host, allowing hosts to use different relay servers.

Usage:
    python scripts/migrate_add_custom_gsrn.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models.host import Host


def check_column_exists():
    """Check if custom_gsrn_server column already exists"""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(hosts)"))
        columns = [row[1] for row in result]
        return 'custom_gsrn_server' in columns


def add_custom_gsrn_column():
    """Add custom_gsrn_server column to hosts table"""
    try:
        # Check if column already exists
        if check_column_exists():
            print("✓ Column 'custom_gsrn_server' already exists in hosts table")
            return True

        print("→ Adding 'custom_gsrn_server' column to hosts table...")

        # Add column using SQLite ALTER TABLE
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE hosts ADD COLUMN custom_gsrn_server VARCHAR(255)"
            ))
            conn.commit()

        print("✓ Column added successfully")
        return True

    except Exception as e:
        print(f"✗ Error adding column: {e}")
        return False


def verify_migration():
    """Verify the migration was successful"""
    try:
        db = SessionLocal()

        # Try to query the new column
        hosts = db.query(Host).all()
        for host in hosts:
            # Access the new attribute
            _ = host.custom_gsrn_server

        db.close()

        print("✓ Migration verified successfully")
        return True

    except Exception as e:
        print(f"✗ Migration verification failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Database Migration: Add custom_gsrn_server field")
    print("=" * 60)
    print()

    # Check current state
    print("→ Checking current database schema...")
    if check_column_exists():
        print("✓ Migration already applied, nothing to do")
        return 0

    # Run migration
    if not add_custom_gsrn_column():
        print()
        print("✗ Migration failed!")
        return 1

    # Verify
    if not verify_migration():
        print()
        print("⚠ Migration completed but verification failed")
        return 1

    print()
    print("=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)
    print()
    print("Notes:")
    print("- Existing hosts will have NULL custom_gsrn_server (use default)")
    print("- You can now specify custom GSRN servers per host")
    print("- Format: relay.example.com:443")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
