# Unit Tests Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
pip install -r tests/unit/requirements-test.txt
```

### 2. Run Tests
```bash
# Basic run
pytest tests/unit/ -v

# With coverage
python tests/run_unit_tests.py --coverage
```

### 3. View Results
```bash
# Open coverage report
open htmlcov/index.html
```

## 📊 What's Included

### 85+ Unit Tests Across 5 Services

| Service | Tests | Coverage | File |
|---------|-------|----------|------|
| Task | 20+ | ~85% | `test_task_service_unit.py` |
| User | 15+ | ~75% | `test_user_service_unit.py` |
| Project | 15+ | ~70% | `test_project_service_unit.py` |
| Auth | 20+ | ~85% | `test_auth_service_unit.py` |
| Notification | 15+ | ~70% | `test_notification_service_unit.py` |

## 🎯 Common Commands

```bash
# Run all tests
pytest tests/unit/ -v

# Run specific service
python tests/run_unit_tests.py --service task

# Quick run (no coverage)
python tests/run_unit_tests.py --quick

# Run specific file
pytest tests/unit/test_task_service_unit.py -v

# Run specific test
pytest tests/unit/test_task_service_unit.py::TestUUIDValidation::test_valid_uuid_format -v

# Show print statements
pytest tests/unit/ -v -s

# Stop on first failure
pytest tests/unit/ -x
```

## ✅ Key Features

- **No Docker Required** - Runs standalone
- **Very Fast** - Completes in seconds
- **Isolated** - Uses mocks for dependencies
- **High Coverage** - 75-85% of business logic

## 📚 What's Tested

### Helper Functions
- ✅ UUID validation
- ✅ Data transformation (DB ↔ API)
- ✅ Date normalization
- ✅ Input validation

### Business Logic
- ✅ Session management
- ✅ Password hashing
- ✅ Role hierarchy
- ✅ Reminder validation
- ✅ Filtering & sorting

### Edge Cases
- ✅ Empty/null inputs
- ✅ Invalid formats
- ✅ Boundary conditions
- ✅ Error handling

## 🔍 Example Tests

### Test UUID Validation
```python
def test_valid_uuid_format():
    valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
    assert is_valid_uuid(valid_uuid) == True

def test_invalid_uuid_format():
    assert is_valid_uuid("dummy-id") == False
```

### Test with Mocked Database
```python
@patch('task_service.supabase')
def test_get_subtasks_count(mock_supabase):
    mock_response = Mock()
    mock_response.count = 3
    mock_supabase.table().select().eq().eq().execute.return_value = mock_response

    count = get_subtasks_count("parent-task-123")
    assert count == 3
```

## 📈 View Coverage

```bash
# Generate HTML report
pytest tests/unit/ --cov=src/microservices --cov-report=html

# Open in browser
open htmlcov/index.html

# Terminal report with missing lines
pytest tests/unit/ --cov=src/microservices --cov-report=term-missing
```

## 🐛 Troubleshooting

### Import Errors
Make sure service modules are in Python path (already handled in test files):
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'microservices', 'tasks'))
```

### Mock Not Working
Patch where function is **used**, not where it's defined:
```python
# ✅ Correct
@patch('task_service.supabase')

# ❌ Wrong
@patch('supabase.create_client')
```

## 📖 More Info

- Full Documentation: [tests/unit/README.md](README.md)
- Testing Guide: [TESTING_GUIDE.md](../../TESTING_GUIDE.md)
- Test Runner Help: `python tests/run_unit_tests.py --help`

## 🎓 Next Steps

1. **Run the tests** - See them pass!
2. **Check coverage** - Find gaps
3. **Add more tests** - Improve coverage
4. **Write new features** - Test as you code

Happy Testing! 🧪✨
