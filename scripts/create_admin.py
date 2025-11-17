#!/usr/bin/env python3
"""Create admin user"""
import sys
import os
import getpass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash
from app.utils.validators import validate_password


def main():
    """Create admin user"""
    print("=== Create Admin User ===\n")

    db = SessionLocal()

    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("✗ Admin user already exists!")
            print("  If you want to reset password, delete the user from database first.")
            sys.exit(1)

        # Get username
        while True:
            username = input("Username (default: admin): ").strip() or "admin"
            if len(username) >= 3:
                break
            print("✗ Username must be at least 3 characters")

        # Check if username exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"✗ User '{username}' already exists!")
            sys.exit(1)

        # Get password
        while True:
            password = getpass.getpass("Password: ")
            password_confirm = getpass.getpass("Confirm password: ")

            if password != password_confirm:
                print("✗ Passwords do not match!\n")
                continue

            is_valid, error = validate_password(password)
            if not is_valid:
                print(f"✗ {error}\n")
                continue

            break

        # Create user
        user = User(
            username=username,
            password_hash=get_password_hash(password)
        )

        db.add(user)
        db.commit()

        print(f"\n✓ Admin user '{username}' created successfully!")
        print(f"✓ You can now login at http://localhost:8000/login")

    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Failed to create user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
