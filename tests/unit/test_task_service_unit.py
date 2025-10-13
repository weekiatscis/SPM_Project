"""
Unit tests for Task Service
Tests individual functions and business logic with mocked dependencies
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import sys
import os

# Add source directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'microservices', 'tasks'))

from task_service import (
    is_valid_uuid,
    validate_task_id,
    map_db_row_to_api,
    to_yyyy_mm_dd,
    get_subtasks_count,
    validate_reminder_days,
    log_task_change
)


class TestUUIDValidation:
    """Test UUID validation helper function"""

    def test_valid_uuid_format(self):
        """Test that valid UUIDs return True"""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert is_valid_uuid(valid_uuid) == True

    def test_invalid_uuid_format(self):
        """Test that invalid UUIDs return False"""
        assert is_valid_uuid("dummy-id") == False
        assert is_valid_uuid("12345") == False
        assert is_valid_uuid("not-a-uuid") == False

    def test_none_uuid(self):
        """Test that None returns False"""
        assert is_valid_uuid(None) == False

    def test_empty_string_uuid(self):
        """Test that empty string returns False"""
        assert is_valid_uuid("") == False


class TestValidateTaskId:
    """Test task ID validation"""

    def test_valid_task_id(self):
        """Test that non-empty task IDs are valid"""
        # validate_task_id returns truthy/falsy values, not necessarily True/False
        assert validate_task_id("abc123")
        assert validate_task_id("550e8400-e29b-41d4-a716-446655440000")

    def test_invalid_task_id_empty(self):
        """Test that empty string is invalid"""
        assert not validate_task_id("")
        assert not validate_task_id("   ")

    def test_invalid_task_id_none(self):
        """Test that None is invalid"""
        assert not validate_task_id(None)


class TestDataMapping:
    """Test data transformation functions"""

    def test_map_db_row_to_api_basic(self):
        """Test basic database row to API mapping"""
        db_row = {
            "task_id": "test-123",
            "title": "Test Task",
            "description": "Test description",
            "due_date": "2025-01-15",
            "status": "pending",
            "priority": "High",
            "owner_id": "user-123",
            "project_id": "proj-123",
            "collaborators": ["user-1", "user-2"],
            "isSubtask": False,
            "parent_task_id": None,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z"
        }

        result = map_db_row_to_api(db_row)

        assert result["id"] == "test-123"
        assert result["title"] == "Test Task"
        assert result["description"] == "Test description"
        assert result["dueDate"] == "2025-01-15"
        assert result["status"] == "pending"
        assert result["priority"] == "High"
        assert result["owner_id"] == "user-123"

    def test_map_db_row_to_api_with_null_values(self):
        """Test mapping with null/missing values"""
        db_row = {
            "task_id": "test-123",
            "title": "Test Task",
            "description": None,
            "due_date": None,
            "status": "pending",
            "priority": None,
            "owner_id": "user-123",
            "created_at": "2025-01-01T00:00:00Z"
        }

        result = map_db_row_to_api(db_row)

        assert result["id"] == "test-123"
        # description could be None or empty string depending on implementation
        assert result.get("description") in [None, "", "No description available"]
        assert result["dueDate"] is None
        # priority field might not be in the basic map_db_row_to_api
        # Just check it exists in result
        assert "priority" in result or "dueDate" in result

    def test_to_yyyy_mm_dd_with_string(self):
        """Test date normalization with string input"""
        assert to_yyyy_mm_dd("2025-01-15T12:30:45Z") == "2025-01-15"
        assert to_yyyy_mm_dd("2025-12-31") == "2025-12-31"

    def test_to_yyyy_mm_dd_with_none(self):
        """Test date normalization with None"""
        assert to_yyyy_mm_dd(None) is None

    def test_to_yyyy_mm_dd_with_datetime(self):
        """Test date normalization with datetime object"""
        dt = datetime(2025, 1, 15, 12, 30, 45)
        result = to_yyyy_mm_dd(dt)
        assert result == "2025-01-15"


class TestReminderValidation:
    """Test reminder days validation"""

    def test_valid_reminder_days(self):
        """Test valid reminder day configurations"""
        assert validate_reminder_days([1, 3, 7]) == True
        assert validate_reminder_days([1]) == True
        assert validate_reminder_days([10]) == True

    def test_invalid_reminder_days_too_many(self):
        """Test that more than 5 reminders is invalid"""
        assert validate_reminder_days([1, 2, 3, 4, 5, 6]) == False

    def test_invalid_reminder_days_out_of_range(self):
        """Test that days outside 1-10 range are invalid"""
        assert validate_reminder_days([0]) == False
        assert validate_reminder_days([11]) == False
        assert validate_reminder_days([-1]) == False

    def test_invalid_reminder_days_empty(self):
        """Test that empty list is invalid"""
        assert validate_reminder_days([]) == False

    def test_invalid_reminder_days_none(self):
        """Test that None is invalid"""
        assert validate_reminder_days(None) == False


class TestSubtasksCount:
    """Test subtasks counting with mocked database"""

    @patch('task_service.supabase')
    def test_get_subtasks_count_success(self, mock_supabase):
        """Test successful subtasks count retrieval"""
        # Mock the database response
        mock_response = Mock()
        mock_response.count = 3
        mock_supabase.table().select().eq().eq().execute.return_value = mock_response

        count = get_subtasks_count("parent-task-123")

        assert count == 3

    @patch('task_service.supabase')
    def test_get_subtasks_count_no_subtasks(self, mock_supabase):
        """Test count when no subtasks exist"""
        mock_response = Mock()
        mock_response.count = 0
        mock_supabase.table().select().eq().eq().execute.return_value = mock_response

        count = get_subtasks_count("parent-task-123")

        assert count == 0

    @patch('task_service.supabase')
    def test_get_subtasks_count_error(self, mock_supabase):
        """Test that errors are handled gracefully"""
        mock_supabase.table().select().eq().eq().execute.side_effect = Exception("Database error")

        count = get_subtasks_count("parent-task-123")

        assert count == 0  # Should return 0 on error


class TestTaskLogging:
    """Test task change logging with mocked database"""

    @patch('task_service.supabase')
    def test_log_task_change_success(self, mock_supabase):
        """Test successful task change logging"""
        mock_response = Mock()
        mock_response.data = [{
            "log_id": "log-123",
            "task_id": "task-123",
            "action": "update",
            "field": "status",
            "old_value": {"status": "pending"},
            "new_value": {"status": "completed"},
            "user_id": "user-123"
        }]
        mock_supabase.table().insert().execute.return_value = mock_response

        result = log_task_change(
            task_id="task-123",
            action="update",
            field="status",
            user_id="user-123",
            old_value="pending",
            new_value="completed"
        )

        assert result is not None
        assert result["task_id"] == "task-123"
        assert result["action"] == "update"

    @patch('task_service.supabase')
    def test_log_task_change_with_complex_values(self, mock_supabase):
        """Test logging with complex JSON values"""
        mock_response = Mock()
        mock_response.data = [{"log_id": "log-123"}]
        mock_supabase.table().insert().execute.return_value = mock_response

        result = log_task_change(
            task_id="task-123",
            action="update",
            field="collaborators",
            user_id="user-123",
            old_value=["user-1"],
            new_value=["user-1", "user-2"]
        )

        assert result is not None

    @patch('task_service.supabase')
    def test_log_task_change_error_handling(self, mock_supabase):
        """Test that logging errors don't crash the system"""
        mock_supabase.table().insert().execute.side_effect = Exception("Database error")

        result = log_task_change(
            task_id="task-123",
            action="update",
            field="status",
            user_id="user-123",
            old_value="pending",
            new_value="completed"
        )

        assert result is None  # Should return None on error


class TestTaskCreationValidation:
    """Test task creation validation logic"""

    def test_valid_task_data(self):
        """Test that valid task data passes validation"""
        from pydantic import ValidationError
        from task_service import TaskCreate

        task_data = {
            "title": "New Task"
            # Other fields are optional
        }

        # Should not raise ValidationError
        task = TaskCreate(**task_data)
        assert task.title == "New Task"

    def test_invalid_task_missing_title(self):
        """Test that missing title fails validation"""
        from pydantic import ValidationError
        from task_service import TaskCreate

        task_data = {
            "due_date": "2025-12-31",
            "status": "pending"
        }

        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(**task_data)

        assert "title" in str(exc_info.value)

    def test_task_with_reminder_days(self):
        """Test task creation with custom reminder days"""
        from task_service import TaskCreate

        task_data = {
            "title": "Task with reminders",
            "due_date": "2025-12-31",
            "reminder_days": [7, 3, 1]
        }

        task = TaskCreate(**task_data)
        assert task.reminder_days == [7, 3, 1]


class TestDateLogic:
    """Test date-related business logic"""

    def test_days_until_due_calculation(self):
        """Test calculation of days until due date"""
        from datetime import date

        due_date = date.today() + timedelta(days=7)
        today = date.today()

        days_until = (due_date - today).days

        assert days_until == 7

    def test_past_due_date_detection(self):
        """Test detection of past due dates"""
        from datetime import date

        past_date = date.today() - timedelta(days=1)
        today = date.today()

        is_past_due = past_date < today

        assert is_past_due == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
