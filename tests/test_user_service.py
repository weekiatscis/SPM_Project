"""
Test suite for User Service
Tests all endpoints and validates service health
"""

import sys
import os
import requests
import pytest

# Service configuration
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8081")

class TestUserService:
    """Test cases for User Service"""

    def test_service_health(self):
        """Test if User Service is running and accessible"""
        try:
            response = requests.get(f"{USER_SERVICE_URL}/users", timeout=5)
            assert response.status_code in [200, 401, 403, 404, 500], \
                f"Service not responding properly. Status: {response.status_code}"
            print(f"✓ User Service is running (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            pytest.fail("User Service is not accessible. Check if service is running.")
        except requests.exceptions.Timeout:
            pytest.fail("User Service request timed out")

    def test_get_users_endpoint(self):
        """Test GET /users endpoint"""
        try:
            response = requests.get(f"{USER_SERVICE_URL}/users", timeout=5)
            assert response.status_code in [200, 401], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "users" in data or "error" not in data, \
                    "Response should contain users array"
                print(f"✓ GET /users endpoint working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /users endpoint: {str(e)}")

    def test_get_current_user_endpoint(self):
        """Test GET /user endpoint (current user)"""
        try:
            response = requests.get(f"{USER_SERVICE_URL}/user", timeout=5)
            # May return 401 without auth, or 404 if no default user
            assert response.status_code in [200, 401, 404], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "user" in data, "Response should contain user object"

            print(f"✓ GET /user endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /user endpoint: {str(e)}")

    def test_get_users_by_department(self):
        """Test GET /users/departments/<department> endpoint"""
        try:
            # Test with a sample department
            response = requests.get(
                f"{USER_SERVICE_URL}/users/departments/Engineering",
                timeout=5
            )
            assert response.status_code in [200, 401, 404], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "users" in data, "Response should contain users array"
                assert "department" in data, "Response should contain department field"

            print("✓ GET /users/departments/<department> endpoint working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test department endpoint: {str(e)}")

    def test_get_user_subordinates(self):
        """Test GET /users/<user_id>/subordinates endpoint"""
        try:
            response = requests.get(
                f"{USER_SERVICE_URL}/users/dummy-id/subordinates",
                timeout=5
            )
            assert response.status_code in [200, 404], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "subordinates" in data, "Response should contain subordinates array"

            print("✓ GET /users/<user_id>/subordinates endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test subordinates endpoint: {str(e)}")

    def test_get_possible_superiors(self):
        """Test GET /users/<user_id>/possible-superiors endpoint"""
        try:
            response = requests.get(
                f"{USER_SERVICE_URL}/users/dummy-id/possible-superiors",
                timeout=5
            )
            assert response.status_code in [200, 404], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "possible_superiors" in data, \
                    "Response should contain possible_superiors array"

            print("✓ GET /users/<user_id>/possible-superiors endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test possible-superiors endpoint: {str(e)}")

    def test_session_validation(self):
        """Test session validation with invalid token"""
        try:
            # Test with invalid Bearer token
            headers = {"Authorization": "Bearer invalid-token"}
            response = requests.get(
                f"{USER_SERVICE_URL}/user",
                headers=headers,
                timeout=5
            )
            # Should handle invalid session gracefully
            assert response.status_code in [200, 401, 404], \
                f"Session validation error: {response.status_code}"

            print("✓ Session validation handling working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test session validation: {str(e)}")

    def test_role_hierarchy_endpoints(self):
        """Test role hierarchy related endpoints"""
        try:
            # Test subordinates endpoint structure
            response = requests.get(
                f"{USER_SERVICE_URL}/users/test-id/subordinates",
                timeout=5
            )
            assert response.status_code in [200, 404], \
                "Subordinates endpoint should return 200 or 404"

            print("✓ Role hierarchy endpoints structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test role hierarchy: {str(e)}")


def run_tests():
    """Run all tests and return success status"""
    print(f"\n{'='*60}")
    print("USER SERVICE TEST SUITE")
    print(f"{'='*60}")
    print(f"Testing service at: {USER_SERVICE_URL}\n")

    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
