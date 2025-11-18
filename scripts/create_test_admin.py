#!/usr/bin/env python3
"""Create test admin user automatically"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    """Create test admin user"""
    db = SessionLocal()

    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("✓ Admin user already exists!")
            return

        # Create admin with default credentials
        user = User(
            username="admin",
            password_hash=pwd_context.hash("Admin123456!")  # Default password
        )

        db.add(user)
        db.commit()

        print("✓ Test admin user created successfully!")
        print("  Username: admin")
        print("  Password: Admin123456!")
        print("\nYou can login at http://localhost:3000/login")

    except Exception as e:
        print(f"✗ Failed to create user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
