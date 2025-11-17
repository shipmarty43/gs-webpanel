#!/bin/bash
# Network Diagnostic Script
# Performs comprehensive network diagnostics

echo "=========================================="
echo "NETWORK DIAGNOSTIC"
echo "Date: $(date)"
echo "=========================================="
echo ""

echo "--- Network Interfaces ---"
ip addr show || ifconfig
echo ""

echo "--- Routing Table ---"
ip route show || route -n
echo ""

echo "--- DNS Configuration ---"
echo "Nameservers:"
cat /etc/resolv.conf | grep nameserver
echo ""

echo "--- DNS Resolution Test ---"
echo "Testing DNS resolution..."
for domain in google.com cloudflare.com; do
    echo -n "$domain: "
    if nslookup "$domain" >/dev/null 2>&1; then
        echo "✓ OK"
    else
        echo "✗ FAILED"
    fi
done
echo ""

echo "--- Network Connectivity Test ---"
echo "Testing connectivity..."
PING_TARGETS=("8.8.8.8" "1.1.1.1" "google.com")
for target in "${PING_TARGETS[@]}"; do
    echo -n "$target: "
    if ping -c 1 -W 2 "$target" >/dev/null 2>&1; then
        echo "✓ Reachable"
    else
        echo "✗ Unreachable"
    fi
done
echo ""

echo "--- Active Network Connections ---"
echo "Established connections:"
ss -tunap 2>/dev/null | grep ESTAB | head -20 || netstat -tunap 2>/dev/null | grep ESTABLISHED | head -20
echo ""

echo "--- Listening Ports ---"
echo "TCP Listening Ports:"
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null
echo ""

echo "--- Firewall Status ---"
if command -v ufw &> /dev/null; then
    echo "UFW Status:"
    ufw status verbose 2>/dev/null
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld Status:"
    firewall-cmd --list-all 2>/dev/null
elif command -v iptables &> /dev/null; then
    echo "iptables Rules:"
    iptables -L -n -v 2>/dev/null | head -30
fi
echo ""

echo "--- Network Statistics ---"
echo "Interface statistics:"
ip -s link || netstat -i
echo ""

echo "--- Bandwidth Usage ---"
if command -v vnstat &> /dev/null; then
    echo "vnstat summary:"
    vnstat
else
    echo "vnstat not installed (install with: apt-get install vnstat)"
fi
echo ""

echo "--- Public IP Address ---"
echo -n "Public IP: "
curl -s ifconfig.me || wget -qO- ifconfig.me || echo "Unable to determine"
echo ""
echo ""

echo "--- Traceroute to 8.8.8.8 ---"
if command -v traceroute &> /dev/null; then
    traceroute -m 10 8.8.8.8 2>/dev/null || echo "Traceroute failed"
else
    echo "traceroute not installed"
fi
echo ""

echo "=========================================="
echo "Network Diagnostic Complete"
echo "=========================================="
