#!/bin/bash

# SPM Project - Microservices Test Runner
# This script helps run tests for all microservices

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}SPM Project - Test Runner${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip3 install -q -r tests/requirements-test.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}"

if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}Services are not running. Starting them now...${NC}"
    docker-compose up -d --build

    echo -e "${YELLOW}Waiting for services to start (30 seconds)...${NC}"
    sleep 30

    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${GREEN}✓ Services are already running${NC}"
fi
echo ""

# Show running services
echo -e "${BLUE}Running services:${NC}"
docker-compose ps
echo ""

# Parse command line arguments
TEST_TYPE=${1:-all}

case "$TEST_TYPE" in
    all)
        echo -e "${BLUE}Running comprehensive validation...${NC}"
        echo ""
        python3 tests/validate_all_services.py
        ;;

    task)
        echo -e "${BLUE}Running Task Service tests...${NC}"
        echo ""
        python3 tests/test_task_service.py
        ;;

    project)
        echo -e "${BLUE}Running Project Service tests...${NC}"
        echo ""
        python3 tests/test_project_service.py
        ;;

    user)
        echo -e "${BLUE}Running User Service tests...${NC}"
        echo ""
        python3 tests/test_user_service.py
        ;;

    auth)
        echo -e "${BLUE}Running Auth Service tests...${NC}"
        echo ""
        python3 tests/test_auth_service.py
        ;;

    notification)
        echo -e "${BLUE}Running Notification Service tests...${NC}"
        echo ""
        python3 tests/test_notification_service.py
        ;;

    individual)
        echo -e "${BLUE}Running all individual service tests...${NC}"
        echo ""

        echo -e "${YELLOW}Task Service:${NC}"
        python3 tests/test_task_service.py
        echo ""

        echo -e "${YELLOW}Project Service:${NC}"
        python3 tests/test_project_service.py
        echo ""

        echo -e "${YELLOW}User Service:${NC}"
        python3 tests/test_user_service.py
        echo ""

        echo -e "${YELLOW}Auth Service:${NC}"
        python3 tests/test_auth_service.py
        echo ""

        echo -e "${YELLOW}Notification Service:${NC}"
        python3 tests/test_notification_service.py
        ;;

    pytest)
        echo -e "${BLUE}Running tests with pytest...${NC}"
        echo ""
        pytest tests/ -v
        ;;

    coverage)
        echo -e "${BLUE}Running tests with coverage...${NC}"
        echo ""
        pytest tests/ --cov=src/microservices --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;

    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Available test types:"
        echo "  all          - Run comprehensive validation (default)"
        echo "  task         - Run Task Service tests only"
        echo "  project      - Run Project Service tests only"
        echo "  user         - Run User Service tests only"
        echo "  auth         - Run Auth Service tests only"
        echo "  notification - Run Notification Service tests only"
        echo "  individual   - Run all individual service tests"
        echo "  pytest       - Run all tests with pytest"
        echo "  coverage     - Run tests with coverage report"
        echo ""
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✓ All tests passed successfully!${NC}"
    echo -e "${GREEN}======================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}======================================${NC}"
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${RED}======================================${NC}"
    exit 1
fi
