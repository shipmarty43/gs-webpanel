#!/usr/bin/env python3
"""
Debug login endpoint - shows what data is being received
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import verify_password
import json


def test_credentials(username, password):
    """Test if credentials would work"""

    print(f"\n{'='*60}")
    print(f"Testing Credentials")
    print(f"{'='*60}")
    print(f"Username: '{username}'")
    print(f"Password: '{password}'")
    print(f"Username length: {len(username)}")
    print(f"Password length: {len(password)}")
    print()

    db = SessionLocal()

    try:
        # Find user
        user = db.query(User).filter(User.username == username).first()

        if not user:
            print(f"❌ User '{username}' NOT FOUND")
            print()
            print("Available users:")
            all_users = db.query(User).all()
            for u in all_users:
                print(f"  - '{u.username}' (length: {len(u.username)})")
            return False

        print(f"✓ User found: {user.username}")
        print()

        # Test password
        print("Testing password verification...")
        is_valid = verify_password(password, user.password_hash)

        if is_valid:
            print("✓ Password is CORRECT")
            print()
            print("Login should work!")
            return True
        else:
            print("❌ Password is INCORRECT")
            print()
            print("Checking for common issues:")

            # Test with trimmed password
            if verify_password(password.strip(), user.password_hash):
                print("  - Password works when trimmed (extra spaces?)")

            # Test with different case
            if verify_password(password.lower(), user.password_hash):
                print("  - Password works in lowercase")
            if verify_password(password.upper(), user.password_hash):
                print("  - Password works in uppercase")

            print()
            print("Try resetting password:")
            print("  python3 scripts/reset_admin.py")

            return False

    finally:
        db.close()


def main():
    print("\n" + "="*60)
    print("Login Debug Tool")
    print("="*60)

    # Test with expected credentials
    test_credentials("admin", "Admin123456!")

    print("\n" + "="*60)
    print("Testing via simulated HTTP request")
    print("="*60)

    # Simulate what the frontend sends
    request_body = {
        "username": "admin",
        "password": "Admin123456!"
    }

    print("Request body (JSON):")
    print(json.dumps(request_body, indent=2))
    print()

    result = test_credentials(
        request_body["username"],
        request_body["password"]
    )

    if result:
        print("\n" + "="*60)
        print("✓ DIAGNOSIS: Credentials are correct!")
        print("="*60)
        print()
        print("If login still fails, the issue is likely:")
        print("1. Typing error in browser (check carefully!)")
        print("2. Browser auto-fill adding extra characters")
        print("3. Copy-paste adding invisible characters")
        print()
        print("Recommendations:")
        print("- Type credentials manually, don't copy-paste")
        print("- Check Caps Lock is OFF")
        print("- Try in incognito/private window")
        print("- Clear browser cache and cookies")
    else:
        print("\n" + "="*60)
        print("❌ DIAGNOSIS: Credentials don't match!")
        print("="*60)
        print()
        print("Run: python3 scripts/reset_admin.py")

    print()


if __name__ == "__main__":
    main()
