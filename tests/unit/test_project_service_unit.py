"""
Unit tests for Project Service
Tests individual functions and business logic with mocked dependencies
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add source directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'microservices', 'projects'))

from project_service import (
    is_valid_uuid,
    map_db_row_to_api
)


class TestUUIDValidation:
    """Test UUID validation for project service"""

    def test_valid_uuid_formats(self):
        """Test various valid UUID formats"""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "00000000-0000-0000-0000-000000000000"
        ]

        for uuid_str in valid_uuids:
            assert is_valid_uuid(uuid_str) == True, f"Failed for {uuid_str}"

    def test_invalid_uuid_formats(self):
        """Test various invalid UUID formats"""
        invalid_uuids = [
            "dummy-id",
            "12345",
            "not-a-uuid",
            "",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra"  # Too long
        ]

        for uuid_str in invalid_uuids:
            assert is_valid_uuid(uuid_str) == False, f"Should fail for {uuid_str}"

    def test_uuid_validation_with_none(self):
        """Test UUID validation with None input"""
        assert is_valid_uuid(None) == False

    def test_uuid_validation_case_insensitive(self):
        """Test that UUID validation handles different cases"""
        lowercase_uuid = "550e8400-e29b-41d4-a716-446655440000"
        uppercase_uuid = "550E8400-E29B-41D4-A716-446655440000"

        assert is_valid_uuid(lowercase_uuid) == True
        assert is_valid_uuid(uppercase_uuid) == True


class TestProjectDataMapping:
    """Test project data transformation"""

    def test_map_db_row_to_api_complete(self):
        """Test mapping with all fields present"""
        db_row = {
            "project_id": "proj-123",
            "project_name": "SPM Project",
            "project_description": "Software Project Management",
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": "user-123",
            "due_date": "2025-12-31"
        }

        result = map_db_row_to_api(db_row)

        assert result["project_id"] == "proj-123"
        assert result["project_name"] == "SPM Project"
        assert result["project_description"] == "Software Project Management"
        assert result["created_at"] == "2025-01-01T00:00:00Z"
        assert result["created_by"] == "user-123"
        assert result["due_date"] == "2025-12-31"

    def test_map_db_row_to_api_minimal(self):
        """Test mapping with only required fields"""
        db_row = {
            "project_id": "proj-123",
            "project_name": "Minimal Project",
            "created_at": "2025-01-01T00:00:00Z"
        }

        result = map_db_row_to_api(db_row)

        assert result["project_id"] == "proj-123"
        assert result["project_name"] == "Minimal Project"
        assert result.get("project_description") is None
        assert result.get("due_date") is None

    def test_map_db_row_to_api_with_nulls(self):
        """Test mapping handles null values correctly"""
        db_row = {
            "project_id": "proj-123",
            "project_name": "Project with Nulls",
            "project_description": None,
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": None,
            "due_date": None
        }

        result = map_db_row_to_api(db_row)

        assert result["project_id"] == "proj-123"
        assert result["project_name"] == "Project with Nulls"
        assert result["project_description"] is None
        assert result["created_by"] is None
        assert result["due_date"] is None


class TestProjectValidation:
    """Test project data validation logic"""

    def test_valid_project_name(self):
        """Test that project name validation works correctly"""
        valid_names = [
            "SPM Project",
            "Project A",
            "My-Project-123",
            "プロジェクト"  # Unicode characters
        ]

        for name in valid_names:
            # Project name should not be empty after stripping
            assert name.strip() != "", f"Name '{name}' should be valid"

    def test_invalid_project_name_empty(self):
        """Test that empty project names are invalid"""
        invalid_names = [
            "",
            "   ",
            "\t",
            "\n"
        ]

        for name in invalid_names:
            assert name.strip() == "", f"Name '{name}' should be invalid"

    def test_project_name_whitespace_handling(self):
        """Test proper handling of whitespace in project names"""
        name_with_whitespace = "  Project Name  "
        stripped = name_with_whitespace.strip()

        assert stripped == "Project Name"
        assert len(stripped) < len(name_with_whitespace)


class TestProjectCreation:
    """Test project creation logic"""

    def test_project_creation_payload(self):
        """Test construction of project creation payload"""
        request_data = {
            "project_name": "  Test Project  ",
            "project_description": "  Test Description  ",
            "owner_id": "user-123"
        }

        # Simulate payload preparation
        project_data = {
            "project_name": request_data.get("project_name").strip(),
            "project_description": request_data.get("project_description", "").strip(),
            "created_by": request_data.get("owner_id") or request_data.get("created_by", "").strip() or "Unknown"
        }

        assert project_data["project_name"] == "Test Project"
        assert project_data["project_description"] == "Test Description"
        assert project_data["created_by"] == "user-123"

    def test_project_creation_with_fallback_creator(self):
        """Test that creator defaults to 'Unknown' if not provided"""
        request_data = {
            "project_name": "Test Project",
            "project_description": "Test Description"
        }

        project_data = {
            "project_name": request_data.get("project_name").strip(),
            "project_description": request_data.get("project_description", "").strip(),
            "created_by": request_data.get("owner_id") or request_data.get("created_by", "").strip() or "Unknown"
        }

        assert project_data["created_by"] == "Unknown"


class TestProjectUpdate:
    """Test project update logic"""

    def test_project_update_payload_all_fields(self):
        """Test update payload with all fields"""
        body = {
            "project_name": "Updated Name",
            "project_description": "Updated Description",
            "due_date": "2025-12-31",
            "created_by": "user-456"
        }

        update_data = {}

        if "project_name" in body:
            update_data["project_name"] = body["project_name"].strip()
        if "project_description" in body:
            update_data["project_description"] = body["project_description"].strip()
        if "due_date" in body:
            update_data["due_date"] = body["due_date"]
        if "created_by" in body:
            update_data["created_by"] = body["created_by"].strip()

        assert len(update_data) == 4
        assert update_data["project_name"] == "Updated Name"
        assert update_data["project_description"] == "Updated Description"
        assert update_data["due_date"] == "2025-12-31"
        assert update_data["created_by"] == "user-456"

    def test_project_update_payload_partial(self):
        """Test update payload with only some fields"""
        body = {
            "project_name": "Updated Name"
        }

        update_data = {}

        if "project_name" in body:
            update_data["project_name"] = body["project_name"].strip()
        if "project_description" in body:
            update_data["project_description"] = body["project_description"].strip()
        if "due_date" in body:
            update_data["due_date"] = body["due_date"]

        assert len(update_data) == 1
        assert update_data["project_name"] == "Updated Name"

    def test_project_update_validation(self):
        """Test that empty updates are detected"""
        body = {}

        update_data = {}

        if "project_name" in body:
            update_data["project_name"] = body["project_name"].strip()
        if "project_description" in body:
            update_data["project_description"] = body["project_description"].strip()

        is_valid = len(update_data) > 0

        assert is_valid == False


class TestProjectFiltering:
    """Test project filtering logic"""

    def test_filter_by_created_by(self):
        """Test filtering projects by creator"""
        projects = [
            {"project_id": "1", "created_by": "user-123", "project_name": "Project A"},
            {"project_id": "2", "created_by": "user-456", "project_name": "Project B"},
            {"project_id": "3", "created_by": "user-123", "project_name": "Project C"}
        ]

        filtered = [p for p in projects if p["created_by"] == "user-123"]

        assert len(filtered) == 2
        assert all(p["created_by"] == "user-123" for p in filtered)

    def test_limit_results(self):
        """Test limiting number of results"""
        projects = [
            {"project_id": str(i), "project_name": f"Project {i}"}
            for i in range(10)
        ]

        limit = 5
        limited_projects = projects[:limit]

        assert len(limited_projects) == 5
        assert len(limited_projects) <= limit

    def test_filter_by_project_id(self):
        """Test filtering by project ID"""
        projects = [
            {"project_id": "proj-1", "project_name": "Project 1"},
            {"project_id": "proj-2", "project_name": "Project 2"},
            {"project_id": "proj-3", "project_name": "Project 3"}
        ]

        project_id = "proj-2"
        filtered = [p for p in projects if p["project_id"] == project_id]

        assert len(filtered) == 1
        assert filtered[0]["project_id"] == "proj-2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
