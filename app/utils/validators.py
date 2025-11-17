"""Input validation utilities"""
import re
from typing import Optional
from app.config import settings


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"

    return True, None


def validate_hostname(hostname: str) -> tuple[bool, Optional[str]]:
    """
    Validate hostname format

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hostname:
        return False, "Hostname cannot be empty"

    if len(hostname) > 100:
        return False, "Hostname too long (max 100 characters)"

    # Allow alphanumeric, hyphens, underscores, dots
    if not re.match(r"^[a-zA-Z0-9._-]+$", hostname):
        return False, "Hostname contains invalid characters"

    return True, None


def validate_ip_address(ip: str) -> tuple[bool, Optional[str]]:
    """
    Validate IP address format (IPv4 or IPv6)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ip:
        return True, None  # IP is optional

    # IPv4 pattern
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    # IPv6 pattern (simplified)
    ipv6_pattern = r"^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$"

    if re.match(ipv4_pattern, ip):
        # Validate octets
        octets = ip.split(".")
        if all(0 <= int(octet) <= 255 for octet in octets):
            return True, None
        return False, "Invalid IPv4 address"

    if re.match(ipv6_pattern, ip):
        return True, None

    return False, "Invalid IP address format"
