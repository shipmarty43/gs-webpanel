#!/bin/bash
# System Information Script
# Collects comprehensive system information

echo "=========================================="
echo "SYSTEM INFORMATION REPORT"
echo "Generated: $(date)"
echo "=========================================="
echo ""

echo "--- Hostname ---"
hostname
echo ""

echo "--- OS Information ---"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME $VERSION"
else
    uname -a
fi
echo ""

echo "--- CPU Information ---"
echo "CPU Model: $(grep 'model name' /proc/cpuinfo | head -n1 | cut -d':' -f2 | xargs)"
echo "CPU Cores: $(nproc)"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo ""

echo "--- Memory Information ---"
free -h
echo ""

echo "--- Disk Usage ---"
df -h | grep -v tmpfs | grep -v devtmpfs
echo ""

echo "--- Network Interfaces ---"
ip -br addr
echo ""

echo "--- Uptime ---"
uptime
echo ""

echo "--- Load Average ---"
cat /proc/loadavg
echo ""

echo "--- Top 5 Processes by Memory ---"
ps aux --sort=-%mem | head -n 6
echo ""

echo "--- Top 5 Processes by CPU ---"
ps aux --sort=-%cpu | head -n 6
echo ""

echo "=========================================="
echo "Report Complete"
echo "=========================================="
