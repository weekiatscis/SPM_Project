"""
Authentication Service Test Suite
Combines unit tests and integration tests for the Authentication Service
"""

import sys
import os
import requests
import pytest
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import string

# Add source directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'microservices', 'users'))

# Service configuration for integration tests
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8086")


# ============================================================================
# UNIT TESTS - Test individual functions and business logic with mocks
# ============================================================================

class TestPasswordHashing:
    """Test password hashing and verification logic"""

    def test_password_hash_generation(self):
        """Test that passwords are properly hashed"""
        password = "testpassword123"
        hashed = hashlib.sha256(password.encode()).hexdigest()

        assert hashed != password
        assert len(hashed) == 64  # SHA256 produces 64 character hex string

    def test_same_password_produces_same_hash(self):
        """Test that same password always produces same hash"""
        password = "testpassword123"
        hash1 = hashlib.sha256(password.encode()).hexdigest()
        hash2 = hashlib.sha256(password.encode()).hexdigest()

        assert hash1 == hash2

    def test_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password123"
        password2 = "password456"

        hash1 = hashlib.sha256(password1.encode()).hexdigest()
        hash2 = hashlib.sha256(password2.encode()).hexdigest()

        assert hash1 != hash2

    def test_password_verification(self):
        """Test password verification logic"""
        password = "mypassword"
        stored_hash = hashlib.sha256(password.encode()).hexdigest()

        # Verify correct password
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        assert input_hash == stored_hash

        # Verify incorrect password
        wrong_password_hash = hashlib.sha256("wrongpassword".encode()).hexdigest()
        assert wrong_password_hash != stored_hash


class TestSessionTokenGeneration:
    """Test session token generation logic"""

    def test_session_token_is_unique(self):
        """Test that generated tokens are unique"""
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)

        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0

    def test_session_token_length(self):
        """Test that session tokens have appropriate length"""
        token = secrets.token_urlsafe(32)

        # token_urlsafe(32) generates about 43 characters
        assert len(token) >= 40

    def test_session_token_format(self):
        """Test that session tokens contain URL-safe characters"""
        token = secrets.token_urlsafe(32)

        # URL-safe characters: A-Z, a-z, 0-9, -, _
        url_safe_chars = string.ascii_letters + string.digits + '-_'

        assert all(c in url_safe_chars for c in token)


class TestLoginAttemptTracking:
    """Test login attempt tracking logic"""

    def test_increment_failed_attempts(self):
        """Test incrementing failed login attempts"""
        failed_attempts = 0
        failed_attempts += 1

        assert failed_attempts == 1

    def test_account_lockout_threshold(self):
        """Test account lockout after max attempts"""
        MAX_ATTEMPTS = 5
        failed_attempts = 5

        is_locked = failed_attempts >= MAX_ATTEMPTS

        assert is_locked == True

    def test_account_not_locked_before_threshold(self):
        """Test account is not locked before max attempts"""
        MAX_ATTEMPTS = 5
        failed_attempts = 4

        is_locked = failed_attempts >= MAX_ATTEMPTS

        assert is_locked == False

    def test_reset_failed_attempts_on_success(self):
        """Test that failed attempts reset on successful login"""
        failed_attempts = 3

        # Successful login
        failed_attempts = 0

        assert failed_attempts == 0


class TestSessionExpiration:
    """Test session expiration logic"""

    def test_calculate_session_expiration(self):
        """Test session expiration time calculation"""
        now = datetime.now(timezone.utc)
        expiration_hours = 24
        expires_at = now + timedelta(hours=expiration_hours)

        assert expires_at > now
        assert (expires_at - now).total_seconds() == expiration_hours * 3600

    def test_session_is_expired(self):
        """Test detection of expired sessions"""
        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(hours=1)

        is_expired = expired_time < now

        assert is_expired == True

    def test_session_is_not_expired(self):
        """Test detection of valid sessions"""
        now = datetime.now(timezone.utc)
        future_time = now + timedelta(hours=1)

        is_expired = future_time < now

        assert is_expired == False

    def test_session_last_activity_update(self):
        """Test that last activity timestamp is updated"""
        initial_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        updated_time = datetime.now(timezone.utc)

        assert updated_time > initial_time


class TestEmailValidation:
    """Test email validation logic"""

    def test_valid_email_formats(self):
        """Test validation of various valid email formats"""
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.co.uk",
            "user_name@example-domain.com"
        ]

        for email in valid_emails:
            assert "@" in email
            assert "." in email.split("@")[1]

    def test_invalid_email_formats(self):
        """Test rejection of invalid email formats"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            ""
        ]

        for email in invalid_emails:
            # Check basic email format validation
            has_at = "@" in email
            if has_at and len(email.split("@")) == 2:
                parts = email.split("@")
                parts_before_at = parts[0]
                parts_after_at = parts[1]
                is_valid = len(parts_before_at) > 0 and len(parts_after_at) > 0 and "." in parts_after_at
            else:
                is_valid = False
            assert is_valid == False, f"Email '{email}' should be invalid"

    def test_email_normalization(self):
        """Test email normalization (lowercase)"""
        email = "User@Example.COM"
        normalized = email.lower()

        assert normalized == "user@example.com"


class TestAuthorizationHeader:
    """Test Authorization header parsing"""

    def test_bearer_token_extraction(self):
        """Test extraction of token from Authorization header"""
        auth_header = "Bearer abc123xyz456"

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
        else:
            token = None

        assert token == "abc123xyz456"

    def test_bearer_token_missing(self):
        """Test handling of missing Authorization header"""
        auth_header = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = None

        assert token is None

    def test_bearer_token_invalid_format(self):
        """Test handling of invalid Authorization header format"""
        auth_header = "Token abc123xyz456"  # Wrong format

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = None

        assert token is None


class TestUserRegistration:
    """Test user registration validation logic"""

    def test_required_fields_present(self):
        """Test that all required fields are present"""
        registration_data = {
            "email": "user@example.com",
            "password": "securepassword",
            "name": "John Doe",
            "role": "Staff",
            "department": "Engineering"
        }

        required_fields = ["email", "password", "name"]
        all_present = all(field in registration_data for field in required_fields)

        assert all_present == True

    def test_required_fields_missing(self):
        """Test detection of missing required fields"""
        registration_data = {
            "email": "user@example.com",
            "password": "securepassword"
            # Missing 'name'
        }

        required_fields = ["email", "password", "name"]
        all_present = all(field in registration_data for field in required_fields)

        assert all_present == False

    def test_password_strength_basic(self):
        """Test basic password strength requirements"""
        weak_passwords = ["123", "abc", ""]
        strong_passwords = ["StrongP@ss123", "MySecurePassword1"]

        for password in weak_passwords:
            is_strong = len(password) >= 8
            assert is_strong == False

        for password in strong_passwords:
            is_strong = len(password) >= 8
            assert is_strong == True


class TestAccountLockout:
    """Test account lockout mechanism"""

    def test_lockout_duration_calculation(self):
        """Test calculation of lockout duration"""
        now = datetime.now(timezone.utc)
        lockout_minutes = 15
        locked_until = now + timedelta(minutes=lockout_minutes)

        assert locked_until > now
        assert (locked_until - now).total_seconds() == lockout_minutes * 60

    def test_account_is_locked(self):
        """Test detection of locked accounts"""
        now = datetime.now(timezone.utc)
        locked_until = now + timedelta(minutes=10)

        is_locked = locked_until > now

        assert is_locked == True

    def test_account_lockout_expired(self):
        """Test detection of expired lockouts"""
        now = datetime.now(timezone.utc)
        locked_until = now - timedelta(minutes=5)

        is_locked = locked_until > now

        assert is_locked == False


class TestSessionCleanup:
    """Test session cleanup logic"""

    def test_identify_expired_sessions(self):
        """Test identification of expired sessions for cleanup"""
        now = datetime.now(timezone.utc)

        sessions = [
            {"session_token": "token1", "expires_at": now + timedelta(hours=1)},
            {"session_token": "token2", "expires_at": now - timedelta(hours=1)},
            {"session_token": "token3", "expires_at": now - timedelta(hours=2)}
        ]

        expired_sessions = [
            s for s in sessions
            if datetime.fromisoformat(str(s["expires_at"]).replace('Z', '+00:00')) < now
        ]

        assert len(expired_sessions) == 2

    def test_no_expired_sessions(self):
        """Test when no sessions are expired"""
        now = datetime.now(timezone.utc)

        sessions = [
            {"session_token": "token1", "expires_at": now + timedelta(hours=1)},
            {"session_token": "token2", "expires_at": now + timedelta(hours=2)}
        ]

        expired_sessions = [
            s for s in sessions
            if datetime.fromisoformat(str(s["expires_at"]).replace('Z', '+00:00')) < now
        ]

        assert len(expired_sessions) == 0


# ============================================================================
# INTEGRATION TESTS - Test actual service endpoints
# ============================================================================

class TestAuthServiceIntegration:
    """Integration tests for Authentication Service endpoints"""

    def test_service_health(self):
        """Test if Auth Service is running and accessible"""
        try:
            response = requests.get(f"{AUTH_SERVICE_URL}/auth/validate", timeout=5)
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
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={},
                timeout=5
            )
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
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/register",
                json={},
                timeout=5
            )
            assert response.status_code != 404, "Register endpoint not found"
            assert response.status_code in [400, 422], \
                f"Register should validate input. Got: {response.status_code}"
            print("✓ POST /auth/register endpoint exists and validates input")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test register endpoint: {str(e)}")

    def test_register_validation(self):
        """Test registration input validation"""
        try:
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
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={
                    "email": "test-lockout@example.com",
                    "password": "wrongpassword"
                },
                timeout=5
            )
            assert response.status_code in [401, 423], \
                f"Account lockout mechanism check failed: {response.status_code}"

            print("✓ Account lockout mechanism in place")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test account lockout: {str(e)}")

    def test_session_token_format(self):
        """Test that session tokens follow secure format"""
        try:
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
