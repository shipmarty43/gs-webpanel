#!/usr/bin/env python3
"""
Check and recreate admin user

This script checks if admin user exists and recreates it with correct password.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    print("=" * 60)
    print("Admin User Check & Reset")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        # Check for existing users
        users = db.query(User).all()
        print(f"→ Found {len(users)} user(s) in database:")
        for user in users:
            print(f"  - {user.username} (ID: {user.id}, Created: {user.created_at})")
        print()

        # Check for admin user
        admin = db.query(User).filter(User.username == "admin").first()

        if admin:
            print("→ Admin user exists, deleting and recreating...")
            db.delete(admin)
            db.commit()
        else:
            print("→ No admin user found, creating new one...")

        # Create new admin user
        password = "Admin123456!"
        password_hash = pwd_context.hash(password)

        new_admin = User(
            username="admin",
            password_hash=password_hash
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        print()
        print("✓ Admin user created successfully!")
        print()
        print("=" * 60)
        print("Login Credentials:")
        print("=" * 60)
        print(f"URL:      http://localhost:3000/login")
        print(f"Username: admin")
        print(f"Password: {password}")
        print("=" * 60)
        print()
        print("⚠️  IMPORTANT: Change this password after first login!")
        print()

        # Verify password
        print("→ Verifying password hash...")
        if pwd_context.verify(password, new_admin.password_hash):
            print("✓ Password hash verification successful")
        else:
            print("✗ Password hash verification FAILED - there may be an issue")

        return 0

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    exit(main())
