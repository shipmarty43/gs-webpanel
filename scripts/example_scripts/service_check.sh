#!/bin/bash
# Service Status Check Script
# Checks status of critical services

echo "=========================================="
echo "SERVICE STATUS CHECK"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Function to check service status
check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo "✓ $service: RUNNING"
    else
        echo "✗ $service: STOPPED"
    fi
}

echo "--- Common System Services ---"
SERVICES=(
    "sshd"
    "ssh"
    "cron"
    "crond"
    "rsyslog"
    "systemd-journald"
    "systemd-networkd"
    "systemd-resolved"
)

for service in "${SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "^$service"; then
        check_service "$service"
    fi
done
echo ""

echo "--- Web Servers ---"
WEB_SERVICES=(
    "nginx"
    "apache2"
    "httpd"
)

for service in "${WEB_SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "^$service"; then
        check_service "$service"
    fi
done
echo ""

echo "--- Databases ---"
DB_SERVICES=(
    "mysql"
    "mysqld"
    "mariadb"
    "postgresql"
    "mongodb"
    "redis"
    "redis-server"
)

for service in "${DB_SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "^$service"; then
        check_service "$service"
    fi
done
echo ""

echo "--- Docker ---"
if systemctl list-unit-files | grep -q "^docker"; then
    check_service "docker"
    if command -v docker &> /dev/null; then
        echo "  Running containers: $(docker ps -q | wc -l)"
        echo "  Total containers: $(docker ps -a -q | wc -l)"
        echo "  Images: $(docker images -q | wc -l)"
    fi
fi
echo ""

echo "--- Failed Services ---"
systemctl --failed
echo ""

echo "--- Services Using Most Memory ---"
systemctl status | grep -E "memory|\.service" | head -20
echo ""

echo "=========================================="
echo "Service Check Complete"
echo "=========================================="
