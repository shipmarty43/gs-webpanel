#!/bin/bash

###############################################################################
# Quick Update Script - Fast update without full rebuild
###############################################################################

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}→ Pulling latest changes...${NC}"
git pull origin "$(git branch --show-current)"

echo -e "${BLUE}→ Restarting containers...${NC}"
docker-compose restart

echo -e "${GREEN}✓ Update completed!${NC}"
echo -e "${BLUE}→ Panel: http://localhost:3000${NC}"
