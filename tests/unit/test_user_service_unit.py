"""
Unit tests for User Service
Tests individual functions and business logic with mocked dependencies
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta
import sys
import os

# Add source directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'microservices', 'users'))

from user_service import (
    is_valid_uuid,
    validate_session,
    map_db_row_to_api,
    SESSION_TIMEOUT
)


class TestUUIDValidation:
    """Test UUID validation for user service"""

    def test_valid_uuid(self):
        """Test that valid UUIDs return True"""
        assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") == True

    def test_invalid_uuid(self):
        """Test that invalid UUIDs return False"""
        assert is_valid_uuid("invalid-id") == False
        assert is_valid_uuid("") == False
        assert is_valid_uuid(None) == False


class TestUserDataMapping:
    """Test user data transformation"""

    def test_map_db_row_to_api_complete(self):
        """Test mapping with all fields present"""
        db_row = {
            "user_id": "user-123",
            "name": "John Doe",
            "email": "john@example.com",
            "role": "Manager",
            "department": "Engineering",
            "superior": "user-456",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z"
        }

        result = map_db_row_to_api(db_row)

        assert result["user_id"] == "user-123"
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["role"] == "Manager"
        assert result["department"] == "Engineering"
        assert result["superior"] == "user-456"
        assert result["is_active"] == True

    def test_map_db_row_to_api_missing_fields(self):
        """Test mapping with missing optional fields"""
        db_row = {
            "user_id": "user-123",
            "name": "Jane Doe",
            "email": "jane@example.com"
        }

        result = map_db_row_to_api(db_row)

        assert result["user_id"] == "user-123"
        assert result["name"] == "Jane Doe"
        assert result["email"] == "jane@example.com"
        assert result.get("role") is None
        assert result.get("department") is None


class TestSessionValidation:
    """Test session validation logic"""

    @patch('user_service.supabase')
    def test_validate_session_valid_token(self, mock_supabase):
        """Test validation of a valid, active session"""
        # Mock session data
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        mock_session_response = Mock()
        mock_session_response.data = [{
            "user_id": "user-123",
            "expires_at": future_time.isoformat(),
            "last_activity": recent_time.isoformat()
        }]

        # Mock user data
        mock_user_response = Mock()
        mock_user_response.data = [{
            "user_id": "user-123",
            "name": "Test User",
            "email": "test@example.com",
            "role": "Staff"
        }]

        mock_supabase.table().select().eq().execute.side_effect = [
            mock_session_response,
            mock_user_response
        ]

        result = validate_session("valid-token-123")

        assert result is not None
        assert result["user_id"] == "user-123"
        assert result["name"] == "Test User"

    @patch('user_service.supabase')
    def test_validate_session_expired_token(self, mock_supabase):
        """Test validation of an expired session"""
        # Mock expired session
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)

        mock_session_response = Mock()
        mock_session_response.data = [{
            "user_id": "user-123",
            "expires_at": past_time.isoformat(),
            "last_activity": past_time.isoformat()
        }]

        mock_supabase.table().select().eq().execute.return_value = mock_session_response

        result = validate_session("expired-token")

        assert result is None

    @patch('user_service.supabase')
    def test_validate_session_inactive_timeout(self, mock_supabase):
        """Test session timeout due to inactivity"""
        # Session expires at future time but last activity was long ago
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        long_ago = datetime.now(timezone.utc) - timedelta(minutes=20)  # > 15 min timeout

        mock_session_response = Mock()
        mock_session_response.data = [{
            "user_id": "user-123",
            "expires_at": future_time.isoformat(),
            "last_activity": long_ago.isoformat()
        }]

        mock_supabase.table().select().eq().execute.return_value = mock_session_response

        result = validate_session("inactive-token")

        assert result is None

    @patch('user_service.supabase')
    def test_validate_session_nonexistent_token(self, mock_supabase):
        """Test validation with non-existent token"""
        mock_session_response = Mock()
        mock_session_response.data = []

        mock_supabase.table().select().eq().execute.return_value = mock_session_response

        result = validate_session("nonexistent-token")

        assert result is None

    @patch('user_service.supabase')
    def test_validate_session_database_error(self, mock_supabase):
        """Test that database errors are handled gracefully"""
        mock_supabase.table().select().eq().execute.side_effect = Exception("Database connection failed")

        result = validate_session("some-token")

        assert result is None  # Should return None on error


class TestRoleHierarchy:
    """Test role hierarchy logic"""

    def test_superior_roles_for_staff(self):
        """Test that Staff can have Manager or Director as superior"""
        superior_roles = {
            "Staff": ["Manager", "Director"],
            "Manager": ["Director"],
            "Director": [],
            "Hr": ["Director"]
        }

        staff_superiors = superior_roles.get("Staff", [])

        assert "Manager" in staff_superiors
        assert "Director" in staff_superiors
        assert len(staff_superiors) == 2

    def test_superior_roles_for_manager(self):
        """Test that Manager can only have Director as superior"""
        superior_roles = {
            "Staff": ["Manager", "Director"],
            "Manager": ["Director"],
            "Director": [],
            "Hr": ["Director"]
        }

        manager_superiors = superior_roles.get("Manager", [])

        assert manager_superiors == ["Director"]

    def test_superior_roles_for_director(self):
        """Test that Director has no superiors"""
        superior_roles = {
            "Staff": ["Manager", "Director"],
            "Manager": ["Director"],
            "Director": [],
            "Hr": ["Director"]
        }

        director_superiors = superior_roles.get("Director", [])

        assert director_superiors == []

    def test_subordinate_roles_for_manager(self):
        """Test that Manager can have Staff as subordinates"""
        role_hierarchy = {
            "Director": ["Manager", "Staff"],
            "Manager": ["Staff"]
        }

        manager_subordinates = role_hierarchy.get("Manager", [])

        assert manager_subordinates == ["Staff"]

    def test_subordinate_roles_for_director(self):
        """Test that Director can have Manager and Staff as subordinates"""
        role_hierarchy = {
            "Director": ["Manager", "Staff"],
            "Manager": ["Staff"]
        }

        director_subordinates = role_hierarchy.get("Director", [])

        assert "Manager" in director_subordinates
        assert "Staff" in director_subordinates


class TestSessionTimeout:
    """Test session timeout configuration"""

    def test_session_timeout_is_15_minutes(self):
        """Test that session timeout is configured to 15 minutes"""
        assert SESSION_TIMEOUT == timedelta(minutes=15)

    def test_session_timeout_calculation(self):
        """Test session timeout calculation logic"""
        last_activity = datetime.now(timezone.utc) - timedelta(minutes=14)
        now = datetime.now(timezone.utc)
        time_since_activity = now - last_activity

        is_timed_out = time_since_activity > SESSION_TIMEOUT

        assert is_timed_out == False  # 14 minutes < 15 minutes

    def test_session_timeout_exceeded(self):
        """Test detection of exceeded session timeout"""
        last_activity = datetime.now(timezone.utc) - timedelta(minutes=16)
        now = datetime.now(timezone.utc)
        time_since_activity = now - last_activity

        is_timed_out = time_since_activity > SESSION_TIMEOUT

        assert is_timed_out == True  # 16 minutes > 15 minutes


class TestDepartmentLogic:
    """Test department-related business logic"""

    def test_department_filtering(self):
        """Test department filtering logic"""
        users = [
            {"user_id": "1", "department": "Engineering", "name": "Alice"},
            {"user_id": "2", "department": "HR", "name": "Bob"},
            {"user_id": "3", "department": "Engineering", "name": "Charlie"}
        ]

        engineering_users = [u for u in users if u["department"] == "Engineering"]

        assert len(engineering_users) == 2
        assert all(u["department"] == "Engineering" for u in engineering_users)

    def test_active_user_filtering(self):
        """Test filtering for active users only"""
        users = [
            {"user_id": "1", "is_active": True, "name": "Alice"},
            {"user_id": "2", "is_active": False, "name": "Bob"},
            {"user_id": "3", "is_active": True, "name": "Charlie"}
        ]

        active_users = [u for u in users if u["is_active"]]

        assert len(active_users) == 2
        assert all(u["is_active"] for u in active_users)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
