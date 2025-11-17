#!/bin/bash
# System Update Script
# Updates system packages safely

echo "=========================================="
echo "SYSTEM UPDATE"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠ WARNING: Not running as root. Some operations may fail."
    echo "Run with: sudo $0"
    echo ""
fi

echo "--- Checking Package Manager ---"
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
    echo "Detected: Debian/Ubuntu (APT)"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    echo "Detected: RHEL/CentOS (YUM)"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    echo "Detected: Fedora (DNF)"
else
    echo "✗ No supported package manager found"
    exit 1
fi
echo ""

echo "--- Updating Package Lists ---"
case $PKG_MANAGER in
    apt)
        apt-get update
        ;;
    yum)
        yum check-update
        ;;
    dnf)
        dnf check-update
        ;;
esac
echo ""

echo "--- Checking for Available Updates ---"
case $PKG_MANAGER in
    apt)
        UPDATES=$(apt list --upgradable 2>/dev/null | grep -c upgradable)
        echo "Available updates: $UPDATES"
        apt list --upgradable 2>/dev/null | grep upgradable | head -20
        ;;
    yum)
        yum list updates
        ;;
    dnf)
        dnf list updates
        ;;
esac
echo ""

echo "--- Installing Security Updates ---"
case $PKG_MANAGER in
    apt)
        apt-get upgrade -y --with-new-pkgs
        apt-get dist-upgrade -y
        ;;
    yum)
        yum update -y --security
        ;;
    dnf)
        dnf upgrade -y --security
        ;;
esac
echo ""

echo "--- Cleaning Up ---"
case $PKG_MANAGER in
    apt)
        apt-get autoremove -y
        apt-get autoclean
        ;;
    yum)
        yum autoremove -y
        yum clean all
        ;;
    dnf)
        dnf autoremove -y
        dnf clean all
        ;;
esac
echo ""

echo "--- Checking if Reboot Required ---"
if [ -f /var/run/reboot-required ]; then
    echo "⚠ SYSTEM REBOOT REQUIRED"
    cat /var/run/reboot-required.pkgs 2>/dev/null
elif [ -f /var/run/reboot-required.pkgs ]; then
    echo "⚠ SYSTEM REBOOT MAY BE REQUIRED"
else
    echo "✓ No reboot required"
fi
echo ""

echo "=========================================="
echo "Update Complete"
echo "=========================================="
