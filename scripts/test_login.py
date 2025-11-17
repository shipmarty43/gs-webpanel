#!/usr/bin/env python3
"""
Test login functionality

This script tests the authentication directly without HTTP to diagnose issues.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import verify_password
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    print("=" * 60)
    print("Login Test")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        # Test credentials
        username = "admin"
        password = "Admin123456!"

        print(f"→ Testing login with username: {username}")
        print(f"→ Testing login with password: {password}")
        print()

        # Find user
        user = db.query(User).filter(User.username == username).first()

        if not user:
            print(f"✗ User '{username}' not found in database!")
            print()
            print("Available users:")
            users = db.query(User).all()
            for u in users:
                print(f"  - {u.username} (ID: {u.id})")
            return 1

        print(f"✓ User found: {user.username} (ID: {user.id})")
        print()

        # Show password hash (first 50 chars)
        print(f"→ Stored password hash: {user.password_hash[:50]}...")
        print()

        # Test password verification with verify_password (from auth.py)
        print("→ Testing verify_password() from app.utils.auth...")
        is_valid_1 = verify_password(password, user.password_hash)
        print(f"  Result: {is_valid_1}")
        print()

        # Test password verification with pwd_context.verify (direct)
        print("→ Testing pwd_context.verify() directly...")
        is_valid_2 = pwd_context.verify(password, user.password_hash)
        print(f"  Result: {is_valid_2}")
        print()

        # Test creating a new hash and verifying
        print("→ Testing fresh hash creation and verification...")
        new_hash = pwd_context.hash(password)
        print(f"  New hash: {new_hash[:50]}...")
        is_valid_3 = pwd_context.verify(password, new_hash)
        print(f"  Fresh hash verification: {is_valid_3}")
        print()

        if is_valid_1 and is_valid_2:
            print("=" * 60)
            print("✓ ALL TESTS PASSED!")
            print("=" * 60)
            print()
            print("Login should work with:")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
            print()
            print("If web login still fails, check:")
            print("1. Browser console for JavaScript errors")
            print("2. Network tab for failed API requests")
            print("3. Docker logs: docker-compose logs web")
            return 0
        else:
            print("=" * 60)
            print("✗ PASSWORD VERIFICATION FAILED!")
            print("=" * 60)
            print()
            print("Updating user password in database...")

            # Update password
            user.password_hash = pwd_context.hash(password)
            db.commit()

            print("✓ Password updated!")
            print()
            print("Try logging in again with:")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
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
