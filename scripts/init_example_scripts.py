#!/usr/bin/env python3
"""Initialize example administration scripts in database"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.script import Script


EXAMPLE_SCRIPTS = [
    {
        "name": "System Information",
        "description": "Collects comprehensive system information including CPU, memory, disk, and network",
        "file_path": "scripts/example_scripts/system_info.sh",
        "category": "monitoring"
    },
    {
        "name": "Security Audit",
        "description": "Performs basic security checks: failed logins, SSH config, firewall, open ports",
        "file_path": "scripts/example_scripts/security_audit.sh",
        "category": "security"
    },
    {
        "name": "Disk Cleanup",
        "description": "Safely cleans temporary files, package cache, and old logs to free disk space",
        "file_path": "scripts/example_scripts/disk_cleanup.sh",
        "category": "maintenance"
    },
    {
        "name": "System Update",
        "description": "Updates system packages and installs security patches",
        "file_path": "scripts/example_scripts/update_system.sh",
        "category": "maintenance"
    },
    {
        "name": "Service Status Check",
        "description": "Checks status of critical services: web servers, databases, Docker, etc.",
        "file_path": "scripts/example_scripts/service_check.sh",
        "category": "monitoring"
    },
    {
        "name": "Network Diagnostic",
        "description": "Performs network diagnostics: connectivity, DNS, routing, firewall, bandwidth",
        "file_path": "scripts/example_scripts/network_diagnostic.sh",
        "category": "diagnostics"
    }
]


def init_example_scripts():
    """Initialize example scripts in database"""
    db = SessionLocal()

    try:
        print("Initializing example administration scripts...")
        print("")

        for script_data in EXAMPLE_SCRIPTS:
            # Check if script already exists
            existing = db.query(Script).filter(Script.name == script_data["name"]).first()

            if existing:
                print(f"  ✓ {script_data['name']} already exists")
                continue

            # Read script content
            script_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                script_data['file_path']
            )

            try:
                with open(script_path, 'r') as f:
                    content = f.read()
            except FileNotFoundError:
                print(f"  ✗ {script_data['name']}: file not found at {script_path}")
                continue

            # Create script
            script = Script(
                name=script_data['name'],
                description=script_data['description'],
                content=content,
                category=script_data.get('category')
            )

            db.add(script)
            print(f"  + Created {script_data['name']}")

        db.commit()
        print("")
        print("✓ Example scripts initialized successfully!")
        print("")
        print("Available scripts:")
        for script_data in EXAMPLE_SCRIPTS:
            print(f"  - {script_data['name']}: {script_data['description']}")

    except Exception as e:
        print(f"✗ Failed to initialize example scripts: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    init_example_scripts()
