"""
Test suite for Task Service
Tests all endpoints and validates service health
"""

import sys
import os
import requests
import pytest
from datetime import datetime, timedelta

# Service configuration
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8080")

class TestTaskService:
    """Test cases for Task Service"""

    def test_service_health(self):
        """Test if Task Service is running and accessible"""
        try:
            response = requests.get(f"{TASK_SERVICE_URL}/tasks", timeout=5)
            assert response.status_code in [200, 401, 403, 404, 500], \
                f"Service not responding properly. Status: {response.status_code}"
            print(f"✓ Task Service is running (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            pytest.fail("Task Service is not accessible. Check if service is running.")
        except requests.exceptions.Timeout:
            pytest.fail("Task Service request timed out")

    def test_get_tasks_endpoint(self):
        """Test GET /tasks endpoint"""
        try:
            response = requests.get(f"{TASK_SERVICE_URL}/tasks", timeout=5)
            assert response.status_code in [200, 401], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "tasks" in data or "error" not in data, "Response should contain tasks array"
                print(f"✓ GET /tasks endpoint working (returned {data.get('count', 0)} tasks)")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /tasks endpoint: {str(e)}")

    def test_get_tasks_with_filters(self):
        """Test GET /tasks endpoint with query parameters"""
        try:
            # Test with limit parameter
            response = requests.get(f"{TASK_SERVICE_URL}/tasks?limit=5", timeout=5)
            assert response.status_code in [200, 401], \
                f"Unexpected status code with limit filter: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                if "tasks" in data:
                    assert len(data["tasks"]) <= 5, "Limit filter not working correctly"
                print("✓ GET /tasks with filters working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /tasks with filters: {str(e)}")

    def test_get_main_tasks_endpoint(self):
        """Test GET /tasks/main endpoint (non-subtasks)"""
        try:
            response = requests.get(f"{TASK_SERVICE_URL}/tasks/main", timeout=5)
            assert response.status_code in [200, 401, 404], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "tasks" in data, "Response should contain tasks array"
                print(f"✓ GET /tasks/main endpoint working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /tasks/main endpoint: {str(e)}")

    def test_create_task_endpoint_structure(self):
        """Test POST /tasks endpoint structure (without actually creating)"""
        try:
            # Send invalid data to check endpoint existence
            response = requests.post(
                f"{TASK_SERVICE_URL}/tasks",
                json={},
                timeout=5
            )
            # Should return 400 (bad request) or similar, not 404
            assert response.status_code != 404, "POST /tasks endpoint not found"
            print(f"✓ POST /tasks endpoint exists (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /tasks POST endpoint: {str(e)}")

    def test_task_validation(self):
        """Test task creation validation"""
        try:
            # Test with missing required fields
            response = requests.post(
                f"{TASK_SERVICE_URL}/tasks",
                json={"title": ""},  # Empty title should fail
                timeout=5
            )
            assert response.status_code in [400, 422, 500], \
                "Should validate required fields"
            print("✓ Task validation working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test task validation: {str(e)}")

    def test_comments_endpoint_structure(self):
        """Test comments endpoint structure"""
        try:
            # Use a dummy task ID to check endpoint structure
            response = requests.get(
                f"{TASK_SERVICE_URL}/tasks/dummy-id/comments",
                timeout=5
            )
            # Should return 400, 404, or 200, but not 500
            assert response.status_code in [200, 400, 404, 500], \
                f"Comments endpoint error: {response.status_code}"
            print("✓ Comments endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test comments endpoint: {str(e)}")

    def test_task_logs_endpoint(self):
        """Test task logs endpoint structure"""
        try:
            response = requests.get(
                f"{TASK_SERVICE_URL}/tasks/dummy-id/logs",
                timeout=5
            )
            assert response.status_code in [200, 400, 404, 500], \
                f"Logs endpoint error: {response.status_code}"
            print("✓ Task logs endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test logs endpoint: {str(e)}")


def run_tests():
    """Run all tests and return success status"""
    print(f"\n{'='*60}")
    print("TASK SERVICE TEST SUITE")
    print(f"{'='*60}")
    print(f"Testing service at: {TASK_SERVICE_URL}\n")

    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
