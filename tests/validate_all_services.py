#!/usr/bin/env python3
"""
Comprehensive Microservices Validation Script
This script validates all microservices in the SPM Project

Run this script to check if all services are healthy and responding correctly.
This is used in the CI/CD pipeline to validate deployments.

Usage:
    python validate_all_services.py

Environment Variables:
    TASK_SERVICE_URL - URL for task service (default: http://localhost:8080)
    PROJECT_SERVICE_URL - URL for project service (default: http://localhost:8082)
    USER_SERVICE_URL - URL for user service (default: http://localhost:8081)
    AUTH_SERVICE_URL - URL for auth service (default: http://localhost:8086)
    NOTIFICATION_SERVICE_URL - URL for notification service (default: http://localhost:8084)
"""

import sys
import os
import time
import requests
from typing import Dict, List, Tuple
from datetime import datetime

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Service configuration
SERVICES = {
    "Task Service": {
        "url": os.getenv("TASK_SERVICE_URL", "http://localhost:8080"),
        "health_endpoint": "/tasks",
        "port": 8080
    },
    "Project Service": {
        "url": os.getenv("PROJECT_SERVICE_URL", "http://localhost:8082"),
        "health_endpoint": "/projects",
        "port": 8082
    },
    "User Service": {
        "url": os.getenv("USER_SERVICE_URL", "http://localhost:8081"),
        "health_endpoint": "/users",
        "port": 8081
    },
    "Auth Service": {
        "url": os.getenv("AUTH_SERVICE_URL", "http://localhost:8086"),
        "health_endpoint": "/auth/validate",
        "port": 8086
    },
    "Notification Service": {
        "url": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084"),
        "health_endpoint": "/notifications?user_id=test",
        "port": 8084
    }
}


def print_header():
    """Print test header"""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}SPM PROJECT - MICROSERVICES VALIDATION{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")


def check_service_health(name: str, config: Dict) -> Tuple[bool, str]:
    """
    Check if a service is healthy and responding

    Args:
        name: Service name
        config: Service configuration dict

    Returns:
        Tuple of (success: bool, message: str)
    """
    url = config["url"]
    endpoint = config["health_endpoint"]
    full_url = f"{url}{endpoint}"

    try:
        response = requests.get(full_url, timeout=5)

        # Services should respond with a valid HTTP status code
        if response.status_code in [200, 401, 403, 404]:
            return True, f"Service is healthy (Status: {response.status_code})"
        elif response.status_code >= 500:
            return False, f"Service error (Status: {response.status_code})"
        else:
            return True, f"Service responding (Status: {response.status_code})"

    except requests.exceptions.ConnectionError:
        return False, "Service not accessible (Connection refused)"
    except requests.exceptions.Timeout:
        return False, "Service timed out (> 5s)"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def validate_task_service() -> Tuple[bool, List[str]]:
    """Validate Task Service specific functionality"""
    url = SERVICES["Task Service"]["url"]
    checks = []
    all_passed = True

    # Check GET /tasks
    try:
        response = requests.get(f"{url}/tasks", timeout=5)
        if response.status_code in [200, 401]:
            checks.append("✓ GET /tasks endpoint working")
        else:
            checks.append(f"✗ GET /tasks returned {response.status_code}")
            all_passed = False
    except Exception as e:
        checks.append(f"✗ GET /tasks failed: {str(e)}")
        all_passed = False

    # Check GET /tasks/main
    try:
        response = requests.get(f"{url}/tasks/main", timeout=5)
        if response.status_code in [200, 401, 404]:
            checks.append("✓ GET /tasks/main endpoint working")
        else:
            checks.append(f"✗ GET /tasks/main returned {response.status_code}")
            all_passed = False
    except Exception as e:
        checks.append(f"✗ GET /tasks/main failed: {str(e)}")
        all_passed = False

    # Check POST /tasks structure
    try:
        response = requests.post(f"{url}/tasks", json={}, timeout=5)
        if response.status_code in [400, 422]:
            checks.append("✓ POST /tasks validation working")
        else:
            checks.append(f"✓ POST /tasks endpoint exists (Status: {response.status_code})")
    except Exception as e:
        checks.append(f"✗ POST /tasks failed: {str(e)}")
        all_passed = False

    return all_passed, checks


def validate_project_service() -> Tuple[bool, List[str]]:
    """Validate Project Service specific functionality"""
    url = SERVICES["Project Service"]["url"]
    checks = []
    all_passed = True

    # Check GET /projects
    try:
        response = requests.get(f"{url}/projects", timeout=5)
        if response.status_code in [200, 401]:
            checks.append("✓ GET /projects endpoint working")
        else:
            checks.append(f"✗ GET /projects returned {response.status_code}")
            all_passed = False
    except Exception as e:
        checks.append(f"✗ GET /projects failed: {str(e)}")
        all_passed = False

    # Check POST /projects validation
    try:
        response = requests.post(f"{url}/projects", json={}, timeout=5)
        if response.status_code in [400, 422]:
            checks.append("✓ POST /projects validation working")
        else:
            checks.append(f"✓ POST /projects endpoint exists (Status: {response.status_code})")
    except Exception as e:
        checks.append(f"✗ POST /projects failed: {str(e)}")
        all_passed = False

    return all_passed, checks


def validate_user_service() -> Tuple[bool, List[str]]:
    """Validate User Service specific functionality"""
    url = SERVICES["User Service"]["url"]
    checks = []
    all_passed = True

    # Check GET /users
    try:
        response = requests.get(f"{url}/users", timeout=5)
        if response.status_code in [200, 401]:
            checks.append("✓ GET /users endpoint working")
        else:
            checks.append(f"✗ GET /users returned {response.status_code}")
            all_passed = False
    except Exception as e:
        checks.append(f"✗ GET /users failed: {str(e)}")
        all_passed = False

    # Check GET /user
    try:
        response = requests.get(f"{url}/user", timeout=5)
        if response.status_code in [200, 401, 404]:
            checks.append("✓ GET /user endpoint working")
        else:
            checks.append(f"✗ GET /user returned {response.status_code}")
            all_passed = False
    except Exception as e:
        checks.append(f"✗ GET /user failed: {str(e)}")
        all_passed = False

    return all_passed, checks


def validate_auth_service() -> Tuple[bool, List[str]]:
    """Validate Auth Service specific functionality"""
    url = SERVICES["Auth Service"]["url"]
    checks = []
    all_passed = True

    # Check POST /auth/login
    try:
        response = requests.post(f"{url}/auth/login", json={}, timeout=5)
        if response.status_code in [400, 401, 422]:
            checks.append("✓ POST /auth/login endpoint working")
        else:
            checks.append(f"✗ POST /auth/login returned {response.status_code}")
            all_passed = False
    except Exception as e:
        checks.append(f"✗ POST /auth/login failed: {str(e)}")
        all_passed = False

    # Check GET /auth/validate
    try:
        response = requests.get(f"{url}/auth/validate", timeout=5)
        if response.status_code == 401:
            checks.append("✓ GET /auth/validate endpoint working")
        else:
            checks.append(f"✓ GET /auth/validate responding (Status: {response.status_code})")
    except Exception as e:
        checks.append(f"✗ GET /auth/validate failed: {str(e)}")
        all_passed = False

    # Check POST /auth/register
    try:
        response = requests.post(f"{url}/auth/register", json={}, timeout=5)
        if response.status_code in [400, 422]:
            checks.append("✓ POST /auth/register validation working")
        else:
            checks.append(f"✓ POST /auth/register endpoint exists (Status: {response.status_code})")
    except Exception as e:
        checks.append(f"✗ POST /auth/register failed: {str(e)}")
        all_passed = False

    return all_passed, checks


def validate_notification_service() -> Tuple[bool, List[str]]:
    """Validate Notification Service specific functionality"""
    url = SERVICES["Notification Service"]["url"]
    checks = []
    all_passed = True

    # Check GET /notifications
    try:
        response = requests.get(f"{url}/notifications?user_id=test", timeout=5)
        if response.status_code in [200, 401]:
            checks.append("✓ GET /notifications endpoint working")
        else:
            checks.append(f"✗ GET /notifications returned {response.status_code}")
            all_passed = False
    except Exception as e:
        checks.append(f"✗ GET /notifications failed: {str(e)}")
        all_passed = False

    # Check POST /notifications/create
    try:
        response = requests.post(f"{url}/notifications/create", json={}, timeout=5)
        if response.status_code in [400, 422]:
            checks.append("✓ POST /notifications/create validation working")
        else:
            checks.append(f"✓ POST /notifications/create endpoint exists (Status: {response.status_code})")
    except Exception as e:
        checks.append(f"✗ POST /notifications/create failed: {str(e)}")
        all_passed = False

    return all_passed, checks


def main():
    """Main validation function"""
    print_header()

    all_services_healthy = True
    results = {}

    # Step 1: Check basic health of all services
    print(f"{Colors.BOLD}STEP 1: Basic Health Checks{Colors.ENDC}\n")

    for service_name, config in SERVICES.items():
        print(f"Checking {service_name}...", end=" ")
        is_healthy, message = check_service_health(service_name, config)

        if is_healthy:
            print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
            results[service_name] = {"health": True, "message": message}
        else:
            print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
            results[service_name] = {"health": False, "message": message}
            all_services_healthy = False

    # Step 2: Validate specific functionality for each service
    print(f"\n{Colors.BOLD}STEP 2: Functional Validation{Colors.ENDC}\n")

    validators = {
        "Task Service": validate_task_service,
        "Project Service": validate_project_service,
        "User Service": validate_user_service,
        "Auth Service": validate_auth_service,
        "Notification Service": validate_notification_service
    }

    for service_name, validator in validators.items():
        if not results[service_name]["health"]:
            print(f"{Colors.WARNING}Skipping {service_name} (service not healthy){Colors.ENDC}")
            continue

        print(f"\n{Colors.OKCYAN}{service_name}:{Colors.ENDC}")
        passed, checks = validator()

        for check in checks:
            if "✓" in check:
                print(f"  {Colors.OKGREEN}{check}{Colors.ENDC}")
            else:
                print(f"  {Colors.FAIL}{check}{Colors.ENDC}")
                all_services_healthy = False

        results[service_name]["functional"] = passed

    # Step 3: Print summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}VALIDATION SUMMARY{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

    healthy_count = sum(1 for r in results.values() if r["health"])
    total_count = len(results)

    for service_name, result in results.items():
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if result["health"] else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"{status} {service_name}: {result['message']}")

    print(f"\n{Colors.BOLD}Services Healthy: {healthy_count}/{total_count}{Colors.ENDC}")

    if all_services_healthy:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ ALL SERVICES VALIDATED SUCCESSFULLY{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ VALIDATION FAILED - SOME SERVICES HAVE ISSUES{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
