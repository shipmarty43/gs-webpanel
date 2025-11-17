#!/bin/bash
# Security Audit Script
# Performs basic security checks on the system

echo "=========================================="
echo "SECURITY AUDIT"
echo "Date: $(date)"
echo "=========================================="
echo ""

echo "--- Checking for Failed Login Attempts ---"
if [ -f /var/log/auth.log ]; then
    echo "Failed SSH attempts (last 20):"
    grep "Failed password" /var/log/auth.log 2>/dev/null | tail -20 || echo "No failed attempts found"
elif [ -f /var/log/secure ]; then
    echo "Failed SSH attempts (last 20):"
    grep "Failed password" /var/log/secure 2>/dev/null | tail -20 || echo "No failed attempts found"
fi
echo ""

echo "--- Checking SSH Configuration ---"
if [ -f /etc/ssh/sshd_config ]; then
    echo "PermitRootLogin: $(grep "^PermitRootLogin" /etc/ssh/sshd_config || echo "Not explicitly set")"
    echo "PasswordAuthentication: $(grep "^PasswordAuthentication" /etc/ssh/sshd_config || echo "Not explicitly set")"
    echo "Port: $(grep "^Port" /etc/ssh/sshd_config || echo "Default (22)")"
else
    echo "SSH config not found"
fi
echo ""

echo "--- Checking for Users with UID 0 (root privileges) ---"
awk -F: '($3 == 0) {print $1}' /etc/passwd
echo ""

echo "--- Checking for Empty Password Users ---"
awk -F: '($2 == "") {print $1}' /etc/shadow 2>/dev/null || echo "Cannot access shadow file (need root)"
echo ""

echo "--- Firewall Status ---"
if command -v ufw &> /dev/null; then
    echo "UFW Status:"
    ufw status 2>/dev/null || echo "Cannot check UFW status (need root)"
elif command -v firewalld &> /dev/null; then
    echo "Firewalld Status:"
    firewall-cmd --state 2>/dev/null || echo "Cannot check firewalld status (need root)"
elif command -v iptables &> /dev/null; then
    echo "iptables rules count:"
    iptables -L -n 2>/dev/null | wc -l || echo "Cannot check iptables (need root)"
else
    echo "No firewall detected"
fi
echo ""

echo "--- Listening Ports ---"
echo "Open TCP ports:"
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || echo "Cannot list ports (need root or ss/netstat)"
echo ""

echo "--- Recently Modified System Files (last 7 days) ---"
find /etc -type f -mtime -7 2>/dev/null | head -20 || echo "Cannot search (need root)"
echo ""

echo "--- Check for World-Writable Files in /etc ---"
find /etc -type f -perm -002 2>/dev/null | head -20 || echo "No world-writable files found or need root"
echo ""

echo "--- Installed Security Packages ---"
if command -v dpkg &> /dev/null; then
    dpkg -l | grep -E "fail2ban|ufw|apparmor|selinux" 2>/dev/null
elif command -v rpm &> /dev/null; then
    rpm -qa | grep -E "fail2ban|firewalld|selinux" 2>/dev/null
fi
echo ""

echo "=========================================="
echo "Security Audit Complete"
echo "=========================================="
