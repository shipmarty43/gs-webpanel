#!/bin/bash

###############################################################################
# GSocket C2 Panel - Automated Deployment Script
#
# This script automates the process of:
# - Pulling latest changes from git
# - Rebuilding Docker containers
# - Restarting services
# - Showing logs
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BRANCH="${1:-claude/gsocket-c2-panel-01CChs23hpBqkFEJi2ygWxWR}"
COMPOSE_FILE="docker-compose.yml"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

# Check if docker and docker-compose are available
check_dependencies() {
    print_header "Checking dependencies"

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Backup database before update
backup_database() {
    print_header "Backing up database"

    BACKUP_DIR="./backups"
    mkdir -p "$BACKUP_DIR"

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/c2panel_${TIMESTAMP}.db"

    if [ -f "./data/c2panel.db" ]; then
        cp "./data/c2panel.db" "$BACKUP_FILE"
        print_success "Database backed up to $BACKUP_FILE"
    else
        print_warning "No database found to backup"
    fi
}

# Pull latest changes from git
pull_updates() {
    print_header "Pulling latest changes from git"

    print_info "Current branch: $(git branch --show-current)"
    print_info "Fetching updates from remote..."

    git fetch origin "$BRANCH"

    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse "@{u}")

    if [ "$LOCAL" = "$REMOTE" ]; then
        print_warning "Already up to date"
        return 1
    else
        print_info "New changes detected, pulling..."
        git pull origin "$BRANCH"
        print_success "Code updated successfully"
        return 0
    fi
}

# Stop running containers
stop_containers() {
    print_header "Stopping containers"

    if docker-compose ps | grep -q "Up"; then
        docker-compose down
        print_success "Containers stopped"
    else
        print_warning "No running containers found"
    fi
}

# Build Docker images
build_images() {
    print_header "Building Docker images"

    print_info "This may take a few minutes..."
    docker-compose build --no-cache
    print_success "Images built successfully"
}

# Start containers
start_containers() {
    print_header "Starting containers"

    docker-compose up -d
    print_success "Containers started"

    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 5
}

# Check container status
check_status() {
    print_header "Container Status"

    docker-compose ps
}

# Show logs
show_logs() {
    print_header "Recent logs"

    docker-compose logs --tail=50
}

# Main deployment flow
main() {
    print_header "GSocket C2 Panel - Automated Deployment"
    echo ""

    # Check dependencies
    check_dependencies
    echo ""

    # Backup database
    backup_database
    echo ""

    # Pull updates
    if pull_updates; then
        REBUILD=true
    else
        echo ""
        read -p "No updates found. Do you want to rebuild anyway? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            REBUILD=true
        else
            REBUILD=false
        fi
    fi
    echo ""

    if [ "$REBUILD" = true ]; then
        # Stop containers
        stop_containers
        echo ""

        # Build images
        build_images
        echo ""

        # Start containers
        start_containers
        echo ""

        # Check status
        check_status
        echo ""

        print_success "Deployment completed successfully!"
        echo ""
        print_info "Panel URL: http://localhost:3000"
        print_info "Default credentials: admin / Admin123456!"
        echo ""

        # Ask if user wants to see logs
        read -p "Do you want to see the logs? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            show_logs
        fi
    else
        print_info "Deployment cancelled"
    fi
}

# Handle script arguments
case "${2:-deploy}" in
    logs)
        docker-compose logs -f
        ;;
    status)
        check_status
        ;;
    stop)
        stop_containers
        ;;
    start)
        start_containers
        check_status
        ;;
    restart)
        stop_containers
        start_containers
        check_status
        ;;
    backup)
        backup_database
        ;;
    *)
        main
        ;;
esac
