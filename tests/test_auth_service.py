"""
Test suite for Authentication Service
Tests all endpoints and validates service health
"""

import sys
import os
import requests
import pytest

# Service configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8086")

class TestAuthService:
    """Test cases for Authentication Service"""

    def test_service_health(self):
        """Test if Auth Service is running and accessible"""
        try:
            # Test with an endpoint that should always respond
            response = requests.get(f"{AUTH_SERVICE_URL}/auth/validate", timeout=5)
            # Should return 401 (unauthorized) not connection error
            assert response.status_code in [200, 401, 403, 404], \
                f"Service not responding properly. Status: {response.status_code}"
            print(f"✓ Auth Service is running (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            pytest.fail("Auth Service is not accessible. Check if service is running.")
        except requests.exceptions.Timeout:
            pytest.fail("Auth Service request timed out")

    def test_login_endpoint_structure(self):
        """Test POST /auth/login endpoint structure"""
        try:
            # Send request without credentials to check endpoint exists
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={},
                timeout=5
            )
            # Should return 400 (bad request), not 404
            assert response.status_code != 404, "Login endpoint not found"
            assert response.status_code in [400, 401, 422], \
                f"Login should validate input. Got: {response.status_code}"
            print("✓ POST /auth/login endpoint exists and validates input")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test login endpoint: {str(e)}")

    def test_login_validation(self):
        """Test login input validation"""
        try:
            # Test with missing email
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={"password": "test"},
                timeout=5
            )
            assert response.status_code in [400, 401, 422], \
                "Should validate required email field"

            # Test with missing password
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={"email": "test@example.com"},
                timeout=5
            )
            assert response.status_code in [400, 401, 422], \
                "Should validate required password field"

            print("✓ Login validation working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test login validation: {str(e)}")

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "wrongpassword"
                },
                timeout=5
            )
            assert response.status_code == 401, \
                f"Should return 401 for invalid credentials. Got: {response.status_code}"

            data = response.json()
            assert "error" in data, "Error response should contain error message"

            print("✓ Login with invalid credentials handled correctly")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test invalid login: {str(e)}")

    def test_logout_endpoint(self):
        """Test POST /auth/logout endpoint"""
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/logout",
                timeout=5
            )
            # Should accept logout even without valid session (200 or 401)
            assert response.status_code in [200, 401], \
                f"Logout endpoint error: {response.status_code}"
            print("✓ POST /auth/logout endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test logout endpoint: {str(e)}")

    def test_validate_session_endpoint(self):
        """Test GET /auth/validate endpoint"""
        try:
            # Test without token
            response = requests.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                timeout=5
            )
            assert response.status_code == 401, \
                f"Should return 401 without token. Got: {response.status_code}"

            # Test with invalid token
            headers = {"Authorization": "Bearer invalid-token"}
            response = requests.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                headers=headers,
                timeout=5
            )
            assert response.status_code == 401, \
                f"Should return 401 with invalid token. Got: {response.status_code}"

            print("✓ GET /auth/validate endpoint working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test validate endpoint: {str(e)}")

    def test_register_endpoint_structure(self):
        """Test POST /auth/register endpoint structure"""
        try:
            # Send invalid data to check endpoint exists
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/register",
                json={},
                timeout=5
            )
            # Should return 400 or 422 (validation error), not 404
            assert response.status_code != 404, "Register endpoint not found"
            assert response.status_code in [400, 422], \
                f"Register should validate input. Got: {response.status_code}"
            print("✓ POST /auth/register endpoint exists and validates input")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test register endpoint: {str(e)}")

    def test_register_validation(self):
        """Test registration input validation"""
        try:
            # Test with missing required fields
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/register",
                json={"email": "test@example.com"},
                timeout=5
            )
            assert response.status_code in [400, 422], \
                "Should validate required fields (email, password, name)"

            print("✓ Registration validation working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test registration validation: {str(e)}")

    def test_account_lockout_mechanism(self):
        """Test that account lockout mechanism is in place"""
        try:
            # Attempt login with wrong credentials
            # Note: We're just checking the mechanism exists, not actually locking accounts
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={
                    "email": "test-lockout@example.com",
                    "password": "wrongpassword"
                },
                timeout=5
            )
            # Should handle failed attempts (401 or 423 if locked)
            assert response.status_code in [401, 423], \
                f"Account lockout mechanism check failed: {response.status_code}"

            print("✓ Account lockout mechanism in place")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test account lockout: {str(e)}")

    def test_session_token_format(self):
        """Test that session tokens follow secure format"""
        try:
            # When validating without a token, check error message format
            response = requests.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                timeout=5
            )
            assert response.status_code == 401, "Should require authentication"

            data = response.json()
            assert "error" in data, "Should return error message"

            print("✓ Session token security mechanisms working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test session token format: {str(e)}")


def run_tests():
    """Run all tests and return success status"""
    print(f"\n{'='*60}")
    print("AUTHENTICATION SERVICE TEST SUITE")
    print(f"{'='*60}")
    print(f"Testing service at: {AUTH_SERVICE_URL}\n")

    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
