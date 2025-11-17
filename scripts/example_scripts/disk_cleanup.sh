#!/bin/bash
# Disk Cleanup Script
# Safely cleans common temporary files and caches

echo "=========================================="
echo "DISK CLEANUP UTILITY"
echo "Date: $(date)"
echo "=========================================="
echo ""

echo "--- Disk Usage Before Cleanup ---"
df -h /
echo ""

echo "--- Cleaning Package Manager Cache ---"
if command -v apt-get &> /dev/null; then
    echo "Cleaning APT cache..."
    apt-get clean 2>/dev/null && echo "✓ APT cache cleaned"
    apt-get autoclean 2>/dev/null && echo "✓ APT autoclean completed"
    apt-get autoremove --purge -y 2>/dev/null && echo "✓ Unused packages removed"
elif command -v yum &> /dev/null; then
    echo "Cleaning YUM cache..."
    yum clean all 2>/dev/null && echo "✓ YUM cache cleaned"
fi
echo ""

echo "--- Cleaning System Temporary Files ---"
echo "Cleaning /tmp (files older than 7 days)..."
find /tmp -type f -atime +7 -delete 2>/dev/null && echo "✓ Old files in /tmp removed"

echo "Cleaning /var/tmp (files older than 30 days)..."
find /var/tmp -type f -atime +30 -delete 2>/dev/null && echo "✓ Old files in /var/tmp removed"
echo ""

echo "--- Cleaning Log Files ---"
echo "Truncating large log files (>100MB)..."
find /var/log -type f -size +100M 2>/dev/null | while read -r log; do
    echo "Truncating: $log"
    : > "$log" 2>/dev/null || echo "Cannot truncate $log (need root)"
done
echo ""

echo "--- Cleaning Journal Logs ---"
if command -v journalctl &> /dev/null; then
    echo "Cleaning systemd journal (keeping last 7 days)..."
    journalctl --vacuum-time=7d 2>/dev/null && echo "✓ Journal cleaned"
fi
echo ""

echo "--- Cleaning User Cache ---"
if [ -d "$HOME/.cache" ]; then
    echo "Cleaning user cache in $HOME/.cache..."
    du -sh "$HOME/.cache" 2>/dev/null
    rm -rf "$HOME/.cache/*" 2>/dev/null && echo "✓ User cache cleaned"
fi
echo ""

echo "--- Finding Large Files (top 10) ---"
echo "Largest files in /var:"
find /var -type f -exec du -h {} + 2>/dev/null | sort -rh | head -10
echo ""

echo "--- Disk Usage After Cleanup ---"
df -h /
echo ""

echo "=========================================="
echo "Cleanup Complete"
echo "=========================================="
