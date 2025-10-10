# SPM Project - Testing Guide

## Overview

This guide provides comprehensive information about testing the SPM Project microservices. The testing infrastructure validates all 5 microservices to ensure they are functioning correctly.

## Microservices Architecture

The SPM Project consists of the following microservices:

| Service | Port | Description | Endpoints |
|---------|------|-------------|-----------|
| **Task Service** | 8080 | Manages tasks, subtasks, comments, and logs | `/tasks`, `/tasks/<id>`, `/tasks/main` |
| **Project Service** | 8082 | Manages projects | `/projects`, `/projects/<id>` |
| **User Service** | 8081 | Manages users, roles, departments | `/users`, `/user`, `/users/<id>/subordinates` |
| **Auth Service** | 8086 | Handles authentication and sessions | `/auth/login`, `/auth/logout`, `/auth/validate` |
| **Notification Service** | 8084 | Manages notifications and reminders | `/notifications`, `/notifications/create` |

Additional infrastructure:
- **RabbitMQ** (Port 5672, 15672) - Message queue for real-time notifications
- **Supabase** - Database backend

## Test Files Structure

```
tests/
├── __init__.py                      # Package initialization
├── README.md                        # Tests documentation
├── requirements-test.txt            # Test dependencies
├── test_task_service.py            # Task Service tests
├── test_project_service.py         # Project Service tests
├── test_user_service.py            # User Service tests
├── test_auth_service.py            # Auth Service tests
├── test_notification_service.py    # Notification Service tests
└── validate_all_services.py        # Comprehensive validation script

.github/
└── workflows/
    └── validate-services.yml       # CI/CD pipeline configuration

run_tests.sh                         # Test runner script (executable)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r tests/requirements-test.txt
```

### 2. Start Services

```bash
docker-compose up -d --build
```

Wait about 30 seconds for all services to initialize.

### 3. Run Tests

**Option A: Using the test runner script (Recommended)**

```bash
# Run all tests
./run_tests.sh

# Run specific service tests
./run_tests.sh task
./run_tests.sh project
./run_tests.sh user
./run_tests.sh auth
./run_tests.sh notification

# Run with pytest
./run_tests.sh pytest

# Run with coverage
./run_tests.sh coverage
```

**Option B: Run individual test files**

```bash
# Comprehensive validation (all services)
python tests/validate_all_services.py

# Individual service tests
python tests/test_task_service.py
python tests/test_project_service.py
python tests/test_user_service.py
python tests/test_auth_service.py
python tests/test_notification_service.py
```

**Option C: Using pytest**

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_task_service.py -v

# Run with coverage
pytest tests/ --cov=src/microservices --cov-report=html
```

## What Each Test Validates

### Task Service Tests ([test_task_service.py](tests/test_task_service.py))

- ✓ Service health and accessibility
- ✓ GET /tasks endpoint (list tasks)
- ✓ GET /tasks with filters (limit, status, priority, etc.)
- ✓ GET /tasks/main (non-subtask tasks)
- ✓ POST /tasks validation (required fields)
- ✓ Task creation validation
- ✓ Comments endpoints
- ✓ Task logs endpoints

### Project Service Tests ([test_project_service.py](tests/test_project_service.py))

- ✓ Service health and accessibility
- ✓ GET /projects endpoint
- ✓ GET /projects with filters
- ✓ POST /projects validation
- ✓ PUT /projects/<id> update endpoint
- ✓ DELETE /projects/<id> endpoint
- ✓ Filter by created_by parameter

### User Service Tests ([test_user_service.py](tests/test_user_service.py))

- ✓ Service health and accessibility
- ✓ GET /users endpoint
- ✓ GET /user (current user) endpoint
- ✓ GET /users/departments/<dept> endpoint
- ✓ GET /users/<id>/subordinates endpoint
- ✓ GET /users/<id>/possible-superiors endpoint
- ✓ Session validation handling
- ✓ Role hierarchy endpoints

### Auth Service Tests ([test_auth_service.py](tests/test_auth_service.py))

- ✓ Service health and accessibility
- ✓ POST /auth/login endpoint
- ✓ Login input validation (email, password)
- ✓ Invalid credentials handling
- ✓ POST /auth/logout endpoint
- ✓ GET /auth/validate session validation
- ✓ POST /auth/register endpoint
- ✓ Registration validation
- ✓ Account lockout mechanism
- ✓ Session token security

### Notification Service Tests ([test_notification_service.py](tests/test_notification_service.py))

- ✓ Service health and accessibility
- ✓ GET /notifications endpoint
- ✓ GET /notifications with limit
- ✓ POST /notifications/create endpoint
- ✓ Notification validation
- ✓ PATCH /notifications/<id>/read endpoint
- ✓ PATCH /notifications/mark-all-read endpoint
- ✓ Test notification endpoint
- ✓ Different notification types support
- ✓ RabbitMQ integration handling

### Comprehensive Validation ([validate_all_services.py](tests/validate_all_services.py))

This is the main validation script that:
1. Checks basic health of all 5 services
2. Validates specific functionality for each service
3. Provides detailed color-coded output
4. Returns exit code 0 on success, 1 on failure
5. Used in CI/CD pipeline

## CI/CD Integration

### GitHub Actions Workflow

The CI/CD pipeline automatically runs on every push to the repository.

**Workflow:** [.github/workflows/validate-services.yml](.github/workflows/validate-services.yml)

**What it does:**
1. Checks out the code
2. Sets up Python 3.11
3. Installs dependencies
4. Creates .env file from GitHub secrets
5. Starts RabbitMQ container
6. Starts all microservices using docker-compose
7. Waits for services to be ready
8. Runs comprehensive validation script
9. Runs individual test files for each service
10. Uploads test results as artifacts
11. Cleans up containers

**Triggers:**
- Push to `main`, `ranentest`, or `develop` branches
- Pull requests to `main` branch

### Required GitHub Secrets

To enable CI/CD, configure these secrets in your GitHub repository:

1. `SUPABASE_URL` - Your Supabase project URL
2. `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
3. `VITE_TASK_OWNER_ID` - Default task owner ID

**How to add secrets:**
1. Go to your repository on GitHub
2. Click Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with the exact names listed above

## Environment Variables

The tests use these environment variables:

```bash
# Service URLs (defaults shown)
TASK_SERVICE_URL=http://localhost:8080
PROJECT_SERVICE_URL=http://localhost:8082
USER_SERVICE_URL=http://localhost:8081
AUTH_SERVICE_URL=http://localhost:8086
NOTIFICATION_SERVICE_URL=http://localhost:8084

# Database and messaging
SUPABASE_URL=<your-supabase-url>
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-key>
RABBITMQ_URL=amqp://admin:admin123@localhost:5672
```

## Troubleshooting

### Services Not Responding

**Problem:** Tests fail with "Connection refused" errors

**Solutions:**
1. Check if services are running:
   ```bash
   docker-compose ps
   ```

2. Wait longer for services to start:
   ```bash
   sleep 30
   ```

3. Check service logs:
   ```bash
   docker-compose logs task-service
   docker-compose logs notification-service
   ```

4. Restart services:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

### Port Already in Use

**Problem:** Services fail to start due to port conflicts

**Solutions:**
1. Stop other applications using ports 8080-8086
2. Or modify ports in docker-compose.yml

### RabbitMQ Connection Issues

**Problem:** Notification service can't connect to RabbitMQ

**Solutions:**
1. Ensure RabbitMQ container is running:
   ```bash
   docker ps | grep rabbitmq
   ```

2. Wait for RabbitMQ to fully initialize (15-20 seconds)

3. Check RabbitMQ logs:
   ```bash
   docker logs rabbitmq
   ```

### Test Failures

**Problem:** Individual tests failing

**Solutions:**
1. Check the specific error message in test output
2. Review service logs for errors
3. Verify environment variables are set
4. Ensure database is accessible
5. Run tests individually to isolate issues

## Best Practices

### Writing Tests

1. **Keep tests independent** - Each test should run independently
2. **Use timeouts** - All HTTP requests have 5-second timeout
3. **Check multiple status codes** - Services may return different codes based on auth
4. **Don't modify data** - Tests should be read-only when possible
5. **Clean up resources** - Always clean up test data

### Running Tests

1. **Start services first** - Always ensure services are running
2. **Wait for initialization** - Give services 30 seconds to start
3. **Run comprehensive validation first** - Use `validate_all_services.py`
4. **Check logs on failure** - Review service logs for errors
5. **Use the test runner script** - Simplifies test execution

### CI/CD

1. **Keep secrets secure** - Never commit secrets to repository
2. **Monitor workflow runs** - Check GitHub Actions tab regularly
3. **Review test artifacts** - Download and review uploaded artifacts
4. **Fix failing tests immediately** - Don't let broken tests accumulate
5. **Test before pushing** - Run tests locally before pushing

## Test Output Example

```
======================================================================
SPM PROJECT - MICROSERVICES VALIDATION
======================================================================
Timestamp: 2025-10-10 12:34:56

STEP 1: Basic Health Checks

Checking Task Service... ✓ Service is healthy (Status: 200)
Checking Project Service... ✓ Service is healthy (Status: 200)
Checking User Service... ✓ Service is healthy (Status: 200)
Checking Auth Service... ✓ Service is healthy (Status: 401)
Checking Notification Service... ✓ Service is healthy (Status: 200)

STEP 2: Functional Validation

Task Service:
  ✓ GET /tasks endpoint working
  ✓ GET /tasks/main endpoint working
  ✓ POST /tasks validation working

Project Service:
  ✓ GET /projects endpoint working
  ✓ POST /projects validation working

...

======================================================================
VALIDATION SUMMARY
======================================================================

✓ Task Service: Service is healthy (Status: 200)
✓ Project Service: Service is healthy (Status: 200)
✓ User Service: Service is healthy (Status: 200)
✓ Auth Service: Service is healthy (Status: 401)
✓ Notification Service: Service is healthy (Status: 200)

Services Healthy: 5/5

✓ ALL SERVICES VALIDATED SUCCESSFULLY
```

## Additional Resources

- [Tests README](tests/README.md) - Detailed test documentation
- [Docker Compose Configuration](docker-compose.yml) - Service orchestration
- [GitHub Actions Workflow](.github/workflows/validate-services.yml) - CI/CD pipeline
- [Test Runner Script](run_tests.sh) - Test execution helper

## Support

If you encounter issues:

1. Check this guide for troubleshooting steps
2. Review test output and service logs
3. Verify all prerequisites are installed
4. Ensure environment variables are configured
5. Open an issue on GitHub with:
   - Test output
   - Service logs
   - Environment details
   - Steps to reproduce

## Summary

This testing infrastructure provides:

- ✓ Comprehensive validation of all 5 microservices
- ✓ Individual test files for each service
- ✓ Automated CI/CD pipeline with GitHub Actions
- ✓ Easy-to-use test runner script
- ✓ Detailed documentation and troubleshooting guides
- ✓ Color-coded output for easy reading
- ✓ Support for pytest and coverage reports

The tests ensure that all microservices are functioning correctly and that any code changes don't break existing functionality.
