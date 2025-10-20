# SPM Project - Test Suite

This directory contains comprehensive tests for all microservices in the SPM Project. Each test file combines both unit tests (testing business logic with mocks) and integration tests (testing actual service endpoints).

## Test Files

Each service has a single test file containing both unit and integration tests:

- **test_auth_service.py** - Authentication Service tests (Unit + Integration)
- **test_notification_service.py** - Notification Service tests (Unit + Integration)
- **test_project_service.py** - Project Service tests (Unit + Integration)
- **test_task_service.py** - Task Service tests (Unit + Integration)
- **test_user_service.py** - User Service tests (Unit + Integration)

### Additional Files

- **validate_all_services.py** - Comprehensive validation script for all services
  - Used in CI/CD pipeline
  - Validates service health and functionality
  - Provides detailed output with color-coded results

## Test Structure

Each test file is organized into two main sections:

### 1. Unit Tests
Tests individual functions and business logic with mocked dependencies. These tests:
- Run quickly without external dependencies
- Test pure logic and data transformations
- Use mocking for database and external service calls
- Validate edge cases and error handling

### 2. Integration Tests
Tests actual service endpoints with running services. These tests:
- Require services to be running via docker-compose
- Test API endpoints and responses
- Validate service health and connectivity
- Check error responses and validation

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r tests/requirements-test.txt
```

2. For integration tests, ensure all microservices are running:
```bash
docker-compose up -d
```

### Run All Tests with Coverage

Run all tests and generate coverage report:

```bash
pytest tests/ -v --cov=src/microservices --cov-report=term-missing --cov-report=html
```

This will:
- Run all unit and integration tests
- Generate a coverage report in the terminal
- Create an HTML coverage report in `htmlcov/`

View the HTML coverage report:
```bash
open htmlcov/index.html
```

### Run Specific Test Files

Test a specific service:

```bash
# Run all tests for Task Service
pytest tests/test_task_service.py -v

# Run all tests for Auth Service
pytest tests/test_auth_service.py -v
```

### Run Only Unit Tests or Integration Tests

Run only unit tests (fast, no services required):
```bash
pytest tests/ -v -k "not Integration"
```

Run only integration tests (requires running services):
```bash
pytest tests/ -v -k "Integration"
```

### Run Individual Test Classes

Run tests from a specific class:
```bash
# Run only password hashing unit tests
pytest tests/test_auth_service.py::TestPasswordHashing -v

# Run only auth service integration tests
pytest tests/test_auth_service.py::TestAuthServiceIntegration -v
```

### Run with Different Output Modes

```bash
# Quiet mode - less verbose
pytest tests/ -q

# Show test names and results
pytest tests/ -v

# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x
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
pytest tests/ -v
```

## CI/CD Integration

The tests are automatically run on every push to the repository via GitHub Actions.

See `.github/workflows/validate-services.yml` for the CI/CD configuration.

The workflow:
1. Runs unit tests first (fast feedback)
2. Starts all microservices using docker-compose
3. Waits for services to be healthy
4. Runs integration tests for all services
5. Generates and reports code coverage
6. Uploads coverage reports as artifacts

## Code Coverage

### Target Coverage

The project aims for **~80% code coverage** across all microservices.

### Checking Coverage

After running tests with `--cov`, you'll see a coverage summary:

```
---------- coverage: platform darwin, python 3.11.x -----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/microservices/tasks/task_service.py   245     48    80%   45-52, 89-91
src/microservices/users/user_service.py   198     39    80%   67-71, 134-139
...
---------------------------------------------------------------------
TOTAL                                    1247    251    80%
```

### Improving Coverage

To identify untested code:
1. Run tests with coverage: `pytest tests/ --cov=src/microservices --cov-report=html`
2. Open the HTML report: `open htmlcov/index.html`
3. Click on individual files to see which lines are not covered
4. Add tests for uncovered code paths

## Troubleshooting

### Unit Tests Failing

If unit tests fail:
1. Check that the tested functions haven't changed
2. Review mock setups - ensure mocks match actual function signatures
3. Check for import errors - ensure source paths are correct

### Integration Tests Failing

If integration tests fail because services aren't responding:

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
   sleep 30 && pytest tests/ -k "Integration" -v
   ```

### Connection Refused Errors

- Ensure docker-compose services are running
- Check if ports are already in use
- Verify environment variables are set correctly
- Try restarting services: `docker-compose restart`

### Test Discovery Issues

If pytest can't find tests:
- Ensure test files start with `test_`
- Ensure test functions start with `test_`
- Ensure test classes start with `Test`
- Check that `__init__.py` exists in the tests directory

## Best Practices

1. **Keep tests independent** - Each test should be able to run independently
2. **Use descriptive test names** - Test names should clearly describe what they test
3. **Don't modify production data** - Integration tests should be read-only when possible
4. **Use appropriate timeouts** - Default timeout is 5 seconds for integration tests
5. **Check multiple status codes** - Services may return different codes based on auth state
6. **Clean up after tests** - Always clean up any test data created
7. **Mock external dependencies** - Unit tests should not make real API calls or database queries
8. **Test edge cases** - Include tests for error conditions, boundary values, and edge cases

## Adding New Tests

To add a new test to an existing file:

1. Determine if it's a unit or integration test
2. Add it to the appropriate section of the test file
3. Follow the existing naming conventions
4. Ensure it follows the test class structure

Example unit test:
```python
class TestMyBusinessLogic:
    """Test my business logic"""

    def test_calculation(self):
        """Test that calculation works correctly"""
        result = my_function(2, 3)
        assert result == 5
```

Example integration test:
```python
class TestMyServiceIntegration:
    """Integration tests for My Service"""

    def test_endpoint_health(self):
        """Test if endpoint is accessible"""
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        assert response.status_code == 200
```

## Support

For issues or questions about the tests:
1. Check the test output for error messages
2. Review service logs with `docker-compose logs`
3. Consult this README for common issues
4. Open an issue on GitHub with test output and service logs
