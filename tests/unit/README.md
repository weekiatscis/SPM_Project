# Unit Tests for SPM Project

## Overview

This directory contains **unit tests** for the SPM Project microservices. Unlike the integration tests in the parent `tests/` directory, these tests focus on testing individual functions and business logic in **isolation** with **mocked dependencies**.

## Test Structure

```
tests/unit/
├── __init__.py
├── README.md (this file)
├── test_task_service_unit.py       # Task Service unit tests
├── test_user_service_unit.py       # User Service unit tests
├── test_project_service_unit.py    # Project Service unit tests
├── test_auth_service_unit.py       # Auth Service unit tests
└── test_notification_service_unit.py # Notification Service unit tests
```

## What's Tested

### Task Service (`test_task_service_unit.py`)
- ✅ UUID validation
- ✅ Task ID validation
- ✅ Data mapping (DB → API format)
- ✅ Date normalization
- ✅ Reminder days validation
- ✅ Subtasks counting (with mocked DB)
- ✅ Task change logging (with mocked DB)
- ✅ Pydantic validation models
- ✅ Date calculation logic

### User Service (`test_user_service_unit.py`)
- ✅ UUID validation
- ✅ User data mapping
- ✅ Session validation logic
- ✅ Session expiration handling
- ✅ Role hierarchy rules
- ✅ Department filtering
- ✅ Active user filtering
- ✅ Session timeout calculations

### Project Service (`test_project_service_unit.py`)
- ✅ UUID validation
- ✅ Project data mapping
- ✅ Project name validation
- ✅ Whitespace handling
- ✅ Update payload construction
- ✅ Filtering logic (by creator, ID, limit)
- ✅ Default value handling

### Auth Service (`test_auth_service_unit.py`)
- ✅ Password hashing (SHA256)
- ✅ Password verification
- ✅ Session token generation
- ✅ Login attempt tracking
- ✅ Account lockout logic
- ✅ Session expiration calculation
- ✅ Email validation
- ✅ Bearer token extraction
- ✅ Registration validation
- ✅ Session cleanup logic

### Notification Service (`test_notification_service_unit.py`)
- ✅ Notification validation
- ✅ Notification types handling
- ✅ Filtering (by user, read status, type)
- ✅ Limiting results
- ✅ Mark as read logic
- ✅ Notification priority/sorting
- ✅ RabbitMQ message formatting
- ✅ Routing key generation
- ✅ Old notification deletion

## Running Unit Tests

### Run All Unit Tests
```bash
# From project root
pytest tests/unit/ -v

# With coverage report
pytest tests/unit/ -v --cov=src/microservices --cov-report=html
```

### Run Specific Test File
```bash
# Test only Task Service
pytest tests/unit/test_task_service_unit.py -v

# Test only User Service
pytest tests/unit/test_user_service_unit.py -v
```

### Run Specific Test Class
```bash
# Test only UUID validation
pytest tests/unit/test_task_service_unit.py::TestUUIDValidation -v

# Test only session validation
pytest tests/unit/test_user_service_unit.py::TestSessionValidation -v
```

### Run Specific Test Method
```bash
# Test a single function
pytest tests/unit/test_task_service_unit.py::TestUUIDValidation::test_valid_uuid_format -v
```


## Test Coverage

### What We Test
- ✅ Helper functions (validation, mapping, etc.)
- ✅ Business logic (calculations, filtering)
- ✅ Data transformations
- ✅ Edge cases and error handling
- ✅ Pydantic models
- ✅ Authentication logic
- ✅ Session management

### What We Don't Test (covered by integration tests)
- ❌ Flask route handlers
- ❌ Database connections
- ❌ External API calls
- ❌ Docker configuration
- ❌ Service-to-service communication

## Mocking Examples

### Example 1: Mocking Supabase Calls
```python
@patch('task_service.supabase')
def test_get_subtasks_count(mock_supabase):
    mock_response = Mock()
    mock_response.count = 3
    mock_supabase.table().select().eq().eq().execute.return_value = mock_response

    count = get_subtasks_count("parent-task-123")
    assert count == 3
```

### Example 2: Testing Pure Logic (No Mocks Needed)
```python
def test_valid_uuid_format():
    valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
    assert is_valid_uuid(valid_uuid) == True
```


### Template
```python
import pytest
from unittest.mock import Mock, patch

class TestYourFeature:
    """Test description"""

    def test_valid_input(self):
        """Test with valid input"""
        result = your_function("valid-input")
        assert result == expected_value

    def test_invalid_input(self):
        """Test with invalid input"""
        result = your_function("")
        assert result == False

    @patch('your_module.external_dependency')
    def test_with_mocked_dependency(self, mock_dep):
        """Test with mocked external dependency"""
        mock_dep.return_value = Mock(data=[{"id": "123"}])
        result = your_function_with_dependency()
        assert result is not None
```

## Continuous Integration

Unit tests run automatically in CI before integration tests:

```yaml
# In .github/workflows/your-workflow.yml
- name: Run Unit Tests
  run: |
    pytest tests/unit/ -v --tb=short
```

## Test Metrics

Current coverage (estimated):
- **Task Service**: ~80% of helper functions
- **User Service**: ~75% of business logic
- **Project Service**: ~70% of validation logic
- **Auth Service**: ~85% of security logic
- **Notification Service**: ~70% of filtering logic

## Troubleshooting

### Import Errors
If you see import errors, make sure the service modules are in your Python path:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'microservices', 'tasks'))
```

### Mock Not Working
Make sure to patch the correct module path where the function is **used**, not where it's defined:
```python
# ✅ Correct - patch where it's used
@patch('task_service.supabase')

# ❌ Wrong - patching the import location
@patch('supabase.create_client')
```

### Test Failures
- Check that mocked returns match expected structure
- Verify test assertions are correct
- Run with `-v` flag for verbose output
- Use `pytest --pdb` to debug failing tests

## Next Steps

### Improve Coverage
- [ ] Add more edge case tests
- [ ] Test error handling paths
- [ ] Add parameterized tests for multiple inputs
- [ ] Test concurrent scenarios

### Add New Test Types
- [ ] Property-based testing (Hypothesis)
- [ ] Mutation testing (mutmut)
- [ ] Performance benchmarks
- [ ] Security-focused tests

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
