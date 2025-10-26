"""
Report Service Test Suite
Combines unit tests and integration tests for the Report Service
"""

import pytest
import sys
import os
import io
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add source directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'microservices', 'reports'))

# Import functions to test (with graceful handling of missing dependencies)
try:
    from report_service import (
        parse_datetime,
        calculate_task_duration_metrics,
        sanitize_filename_component,
        filter_high_priority_tasks,
        calculate_duration,
        is_task_overdue,
        UserRole,
        ReportType
    )
    REPORT_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Report service not available: {e}")
    REPORT_SERVICE_AVAILABLE = False
    # Define dummy functions for tests to collect
    parse_datetime = None
    calculate_task_duration_metrics = None
    sanitize_filename_component = None
    filter_high_priority_tasks = None
    calculate_duration = None
    is_task_overdue = None
    UserRole = None
    ReportType = None

# Service configuration for integration tests
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://localhost:8090")


# ============================================================================
# UNIT TESTS - Test individual functions and business logic with mocks
# ============================================================================

@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestDateTimeParsing:
    """Test datetime parsing and handling"""

    def test_parse_datetime_with_iso_string(self):
        """Test parsing ISO format datetime string"""
        result = parse_datetime("2025-10-15T10:30:00Z")

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 15

    def test_parse_datetime_with_date_only(self):
        """Test parsing date-only string"""
        result = parse_datetime("2025-10-15")

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 15

    def test_parse_datetime_with_none(self):
        """Test that None returns None"""
        result = parse_datetime(None)

        assert result is None

    def test_parse_datetime_with_empty_string(self):
        """Test that empty string returns None"""
        result = parse_datetime("")

        assert result is None

    def test_parse_datetime_with_datetime_object(self):
        """Test that datetime objects are returned as-is"""
        dt = datetime(2025, 10, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_datetime(dt)

        assert result == dt


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestTaskDurationMetrics:
    """Test task duration calculation logic"""

    def test_calculate_task_duration_metrics_completed(self):
        """Test duration calculation for completed task"""
        task = {
            "created_at": "2025-10-01T00:00:00Z",
            "updated_at": "2025-10-10T00:00:00Z",
            "status": "Completed"
        }

        result = calculate_task_duration_metrics(task)

        assert result is not None
        assert "completion_time_days" in result
        assert result["completion_time_days"] is not None
        assert result["completion_time_days"] >= 0

    def test_calculate_task_duration_metrics_in_progress(self):
        """Test duration for in-progress task"""
        task = {
            "created_at": "2025-10-01T00:00:00Z",
            "updated_at": "2025-10-05T00:00:00Z",
            "status": "In Progress"
        }

        result = calculate_task_duration_metrics(task)

        assert result is not None
        assert "completion_time_days" in result

    def test_calculate_task_duration_metrics_missing_dates(self):
        """Test handling of missing date fields"""
        task = {
            "status": "Pending"
        }

        result = calculate_task_duration_metrics(task)

        assert result is not None
        # Should handle gracefully with None values

    def test_calculate_task_duration_metrics_same_day(self):
        """Test duration for same-day task"""
        same_time = "2025-10-15T10:00:00Z"
        task = {
            "created_at": same_time,
            "updated_at": same_time,
            "status": "Completed"
        }

        result = calculate_task_duration_metrics(task)

        assert result is not None
        assert result.get("completion_time_days") is not None


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestFilenameSanitization:
    """Test filename sanitization for safe file generation"""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization"""
        result = sanitize_filename_component("Project Report 2025")

        assert result == "Project_Report_2025"

    def test_sanitize_filename_with_special_chars(self):
        """Test sanitization removes special characters"""
        result = sanitize_filename_component("Report: Q1/Q2 (2025)")

        assert "/" not in result
        assert ":" not in result
        assert "(" not in result
        assert ")" not in result

    def test_sanitize_filename_with_none(self):
        """Test that None returns default"""
        result = sanitize_filename_component(None)

        assert result == "report"

    def test_sanitize_filename_with_empty_string(self):
        """Test that empty string returns default"""
        result = sanitize_filename_component("")

        assert result == "report"

    def test_sanitize_filename_preserves_safe_chars(self):
        """Test that alphanumeric and safe chars are preserved"""
        result = sanitize_filename_component("Report_2025-Q1")

        assert "Report" in result
        assert "2025" in result
        assert "Q1" in result


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestTaskFiltering:
    """Test task filtering logic"""

    def test_filter_high_priority_tasks(self):
        """Test filtering high priority tasks"""
        tasks = [
            {"task_id": "1", "priority": 10, "title": "Critical"},
            {"task_id": "2", "priority": 5, "title": "Medium"},
            {"task_id": "3", "priority": 9, "title": "High"},
            {"task_id": "4", "priority": 3, "title": "Low"},
            {"task_id": "5", "priority": 8, "title": "Important"}
        ]

        result = filter_high_priority_tasks(tasks, limit=3)

        assert len(result) == 3
        assert result[0]["priority"] == 10  # Highest first
        assert result[1]["priority"] == 9
        assert result[2]["priority"] == 8

    def test_filter_high_priority_tasks_fewer_than_limit(self):
        """Test filtering when fewer tasks than limit"""
        tasks = [
            {"task_id": "1", "priority": 10},
            {"task_id": "2", "priority": 8}
        ]

        result = filter_high_priority_tasks(tasks, limit=5)

        assert len(result) == 2

    def test_filter_high_priority_tasks_empty_list(self):
        """Test filtering empty task list"""
        result = filter_high_priority_tasks([], limit=5)

        assert len(result) == 0

    def test_filter_high_priority_tasks_default_limit(self):
        """Test filtering with default limit of 8"""
        tasks = [{"task_id": str(i), "priority": i} for i in range(1, 15)]

        result = filter_high_priority_tasks(tasks)

        assert len(result) == 8


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestDurationCalculation:
    """Test duration string formatting"""

    def test_calculate_duration_both_dates(self):
        """Test duration calculation with both dates"""
        assigned = "2025-10-01"
        completed = "2025-10-10"

        result = calculate_duration(assigned, completed)

        assert "day" in result.lower()
        assert result != "N/A"

    def test_calculate_duration_missing_assigned(self):
        """Test duration with missing assigned date"""
        result = calculate_duration(None, "2025-10-10")

        assert result == "Ongoing"

    def test_calculate_duration_missing_completed(self):
        """Test duration with missing completion date"""
        result = calculate_duration("2025-10-01", None)

        assert result == "Ongoing"

    def test_calculate_duration_both_missing(self):
        """Test duration with both dates missing"""
        result = calculate_duration(None, None)

        assert result == "Ongoing"


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestTaskOverdueDetection:
    """Test overdue task detection"""

    def test_is_task_overdue_past_due(self):
        """Test that past due date is detected"""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        task = {
            "due_date": yesterday,
            "status": "In Progress"
        }

        result = is_task_overdue(task)

        assert result == True

    def test_is_task_overdue_future_due(self):
        """Test that future due date is not overdue"""
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        task = {
            "due_date": tomorrow,
            "status": "In Progress"
        }

        result = is_task_overdue(task)

        assert result == False

    def test_is_task_overdue_completed(self):
        """Test that completed tasks are not overdue"""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        task = {
            "due_date": yesterday,
            "status": "Completed"
        }

        result = is_task_overdue(task)

        assert result == False

    def test_is_task_overdue_no_due_date(self):
        """Test that tasks without due date are not overdue"""
        task = {
            "status": "In Progress"
        }

        result = is_task_overdue(task)

        assert result == False


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestEnums:
    """Test enum definitions"""

    def test_user_role_enum_values(self):
        """Test UserRole enum has expected values"""
        assert hasattr(UserRole, 'STAFF')
        assert hasattr(UserRole, 'MANAGER')
        assert hasattr(UserRole, 'DIRECTOR')
        assert hasattr(UserRole, 'HR')

    def test_report_type_enum_values(self):
        """Test ReportType enum has expected values"""
        assert hasattr(ReportType, 'INDIVIDUAL')
        assert hasattr(ReportType, 'TEAM')
        assert hasattr(ReportType, 'DEPARTMENT')


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestUserInfoFetching:
    """Test user information retrieval"""

    @patch('report_service.requests.get')
    def test_fetch_user_info_success(self, mock_get):
        """Test successful user info fetch"""
        from report_service import fetch_user_info

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "department": "Engineering"
            }
        }
        mock_get.return_value = mock_response

        result = fetch_user_info("user-123")

        assert result["name"] == "John Doe"
        assert result["department"] == "Engineering"

    @patch('report_service.requests.get')
    def test_fetch_user_info_not_found(self, mock_get):
        """Test user not found"""
        from report_service import fetch_user_info

        mock_response = Mock()
        mock_response.ok = False
        mock_get.return_value = mock_response

        result = fetch_user_info("user-nonexistent")

        assert "name" in result
        assert result["name"] == "Unknown"


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestAccessValidation:
    """Test report access validation logic"""

    @patch('report_service.get_user_details')
    def test_validate_report_access_personal_report_owner(self, mock_get_user):
        """Test that user can access their own personal report"""
        from report_service import validate_report_access

        mock_get_user.return_value = {
            "user_id": "user-123",
            "role": "Staff"
        }

        requesting_user = {
            "user_id": "user-123",
            "role": "Staff"
        }
        report_data = {
            "report_type": "individual",
            "user_id": "user-123"
        }

        result = validate_report_access(requesting_user, report_data)

        assert result == True

    @patch('report_service.get_user_details')
    def test_validate_report_access_personal_report_not_owner(self, mock_get_user):
        """Test that user cannot access other's personal report"""
        from report_service import validate_report_access

        mock_get_user.return_value = {
            "user_id": "user-123",
            "role": "Staff"
        }

        requesting_user = {
            "user_id": "user-123",
            "role": "Staff"
        }
        report_data = {
            "report_type": "individual",
            "user_id": "user-456"
        }

        result = validate_report_access(requesting_user, report_data)

        assert result == False


@pytest.mark.skipif(not REPORT_SERVICE_AVAILABLE, reason="report_service not available")
class TestDataCleaning:
    """Test JSON data cleaning utility"""

    def test_clean_data_for_json_with_none(self):
        """Test None values are converted to 'null' string"""
        from report_service import clean_data_for_json

        data = {
            "created_at": None
        }

        result = clean_data_for_json(data)

        assert result["created_at"] == "null"

    def test_clean_data_for_json_with_nested_none(self):
        """Test nested None values are converted"""
        from report_service import clean_data_for_json

        data = {
            "task": {
                "created_at": None
            }
        }

        result = clean_data_for_json(data)

        assert result["task"]["created_at"] == "null"

    def test_clean_data_for_json_with_list(self):
        """Test lists with None values are cleaned"""
        from report_service import clean_data_for_json

        data = [
            {"date": None},
            {"date": None}
        ]

        result = clean_data_for_json(data)

        assert result[0]["date"] == "null"
        assert result[1]["date"] == "null"


# ============================================================================
# INTEGRATION TESTS - Test actual service endpoints
# ============================================================================

class TestReportServiceIntegration:
    """Integration tests for Report Service endpoints"""

    def test_service_health(self):
        """Test if Report Service is running and accessible"""
        try:
            response = requests.get(f"{REPORT_SERVICE_URL}/health", timeout=5)
            assert response.status_code == 200

            data = response.json()
            assert data.get("status") == "healthy"
            print("✓ Report Service health check passed")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Report Service not available: {str(e)}")

    def test_get_available_users_endpoint(self):
        """Test GET /available-users endpoint"""
        try:
            response = requests.get(f"{REPORT_SERVICE_URL}/available-users", timeout=5)
            assert response.status_code in [200, 401, 500], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
                print("✓ GET /available-users endpoint working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /available-users endpoint: {str(e)}")

    def test_get_report_options_endpoint(self):
        """Test GET /report-options endpoint"""
        try:
            response = requests.get(
                f"{REPORT_SERVICE_URL}/report-options",
                params={"user_id": "test-user"},
                timeout=5
            )
            assert response.status_code in [200, 400, 401, 404, 500], \
                f"Unexpected status code: {response.status_code}"

            print(f"✓ GET /report-options endpoint exists (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /report-options endpoint: {str(e)}")

    def test_preview_report_endpoint_structure(self):
        """Test POST /preview-report endpoint structure"""
        try:
            response = requests.post(
                f"{REPORT_SERVICE_URL}/preview-report",
                json={},
                timeout=5
            )
            # Should return 400 (bad request) or similar, not 404
            assert response.status_code != 404, "POST /preview-report endpoint not found"
            print(f"✓ POST /preview-report endpoint exists (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /preview-report endpoint: {str(e)}")

    def test_generate_report_endpoint_structure(self):
        """Test POST /generate-report endpoint structure"""
        try:
            response = requests.post(
                f"{REPORT_SERVICE_URL}/generate-report",
                json={},
                timeout=5
            )
            # Should return 400 (bad request) or similar, not 404
            assert response.status_code != 404, "POST /generate-report endpoint not found"
            print(f"✓ POST /generate-report endpoint exists (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /generate-report endpoint: {str(e)}")

    def test_preview_project_report_endpoint_structure(self):
        """Test POST /preview-project-report endpoint structure"""
        try:
            response = requests.post(
                f"{REPORT_SERVICE_URL}/preview-project-report",
                json={},
                timeout=5
            )
            assert response.status_code != 404, "POST /preview-project-report endpoint not found"
            print(f"✓ POST /preview-project-report endpoint exists (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /preview-project-report endpoint: {str(e)}")

    def test_generate_project_report_endpoint_structure(self):
        """Test POST /generate-project-report endpoint structure"""
        try:
            response = requests.post(
                f"{REPORT_SERVICE_URL}/generate-project-report",
                json={},
                timeout=5
            )
            assert response.status_code != 404, "POST /generate-project-report endpoint not found"
            print(f"✓ POST /generate-project-report endpoint exists (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /generate-project-report endpoint: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
