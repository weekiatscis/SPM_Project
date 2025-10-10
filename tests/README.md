# SPM Project - Microservices Test Suite

This directory contains comprehensive tests for all microservices in the SPM Project.

## Test Files

### Individual Service Tests
- **test_task_service.py** - Tests for Task Service (Port 8080)
- **test_project_service.py** - Tests for Project Service (Port 8082)
- **test_user_service.py** - Tests for User Service (Port 8081)
- **test_auth_service.py** - Tests for Authentication Service (Port 8086)
- **test_notification_service.py** - Tests for Notification Service (Port 8084)

### Comprehensive Validation
- **validate_all_services.py** - Main validation script that checks all services
  - Used in CI/CD pipeline
  - Validates service health and functionality
  - Provides detailed output with color-coded results

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r tests/requirements-test.txt
```

2. Make sure all microservices are running:
```bash
docker-compose up -d
```

### Run All Services Validation

This is the main test that validates all microservices:

```bash
python tests/validate_all_services.py
```

### Run Individual Service Tests

Test a specific microservice:

```bash
# Task Service
python tests/test_task_service.py

# Project Service
python tests/test_project_service.py

# User Service
python tests/test_user_service.py

# Auth Service
python tests/test_auth_service.py

# Notification Service
python tests/test_notification_service.py
```

### Run with pytest

You can also run tests using pytest:

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_task_service.py -v

# Run with coverage
pytest tests/ --cov=src/microservices --cov-report=html
```

## Environment Variables

The tests use the following environment variables (with defaults):

- `TASK_SERVICE_URL` - Default: `http://localhost:8080`
- `PROJECT_SERVICE_URL` - Default: `http://localhost:8082`
- `USER_SERVICE_URL` - Default: `http://localhost:8081`
- `AUTH_SERVICE_URL` - Default: `http://localhost:8086`
- `NOTIFICATION_SERVICE_URL` - Default: `http://localhost:8084`

To test against different environments:

```bash
export TASK_SERVICE_URL=http://your-server:8080
python tests/validate_all_services.py
```

## CI/CD Integration

The tests are automatically run on every push to the repository via GitHub Actions.

See `.github/workflows/validate-services.yml` for the CI/CD configuration.

The workflow:
1. Starts all microservices using docker-compose
2. Waits for services to be ready
3. Runs the comprehensive validation script
4. Runs individual test files for each service
5. Reports results and uploads artifacts

## Test Structure

Each test file follows this structure:

1. **Service Health Check** - Verifies service is running and accessible
2. **Endpoint Tests** - Tests each API endpoint
3. **Validation Tests** - Tests input validation
4. **Error Handling Tests** - Tests error responses

## Adding New Tests

To add a new test:

1. Create a new test file: `test_<service_name>.py`
2. Import the necessary modules
3. Create a test class: `TestServiceName`
4. Add test methods (must start with `test_`)
5. Update `validate_all_services.py` to include the new service
6. Update this README

Example:

```python
import pytest
import requests

SERVICE_URL = "http://localhost:8000"

class TestMyService:
    def test_service_health(self):
        response = requests.get(f"{SERVICE_URL}/health")
        assert response.status_code == 200

    def test_endpoint(self):
        response = requests.get(f"{SERVICE_URL}/api/endpoint")
        assert response.status_code in [200, 401]
```

## Troubleshooting

### Services not responding

If tests fail because services aren't responding:

1. Check if all services are running:
   ```bash
   docker-compose ps
   ```

2. Check service logs:
   ```bash
   docker-compose logs <service-name>
   ```

3. Wait longer for services to start:
   ```bash
   # Services may take 30-60 seconds to start
   sleep 30 && python tests/validate_all_services.py
   ```

### Connection refused errors

- Ensure docker-compose services are running
- Check if ports are already in use
- Verify environment variables are set correctly

### Test failures

- Check the test output for specific error messages
- Review service logs for errors
- Verify database and RabbitMQ are accessible
- Ensure all required environment variables are set

## Best Practices

1. **Keep tests independent** - Each test should be able to run independently
2. **Don't modify data** - Tests should be read-only when possible
3. **Use appropriate timeouts** - Default timeout is 5 seconds
4. **Check multiple status codes** - Services may return 200, 401, etc. based on auth
5. **Clean up after tests** - Always clean up any test data created

## Support

For issues or questions about the tests, please:
1. Check the test output for error messages
2. Review service logs
3. Open an issue on GitHub with test output and service logs
