#!/bin/bash

###############################################################################
# Test API Login
#
# This script tests the login API endpoint directly
###############################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo "API Login Test"
echo "============================================================"
echo ""

# Test credentials
USERNAME="admin"
PASSWORD="Admin123456!"
API_URL="http://localhost:8000/api/auth/login"

echo -e "${BLUE}→ Testing login endpoint${NC}"
echo "  URL: $API_URL"
echo "  Username: $USERNAME"
echo "  Password: $PASSWORD"
echo ""

# Make login request
echo -e "${BLUE}→ Sending POST request...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

# Split response body and status code
BODY=$(echo "$RESPONSE" | head -n -1)
STATUS=$(echo "$RESPONSE" | tail -n 1)

echo ""
echo "HTTP Status: $STATUS"
echo "Response Body:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}✓ LOGIN SUCCESSFUL!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""

    # Extract token
    TOKEN=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

    if [ -n "$TOKEN" ]; then
        echo "Access Token (first 50 chars):"
        echo "${TOKEN:0:50}..."
        echo ""

        # Test token with /api/auth/status
        echo -e "${BLUE}→ Testing token with /api/auth/status...${NC}"
        STATUS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/auth/status" \
          -H "Authorization: Bearer $TOKEN")

        echo "User Info:"
        echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
        echo ""
        echo -e "${GREEN}✓ Token is valid!${NC}"
    fi

else
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}✗ LOGIN FAILED!${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
    echo "Possible issues:"
    echo "1. Web server not running (check: docker-compose ps)"
    echo "2. Port 8000 not accessible"
    echo "3. Database issue"
    echo ""
    echo "Run these commands to debug:"
    echo "  docker-compose logs web"
    echo "  docker-compose ps"
    echo "  python3 scripts/test_login.py"
fi

echo ""
