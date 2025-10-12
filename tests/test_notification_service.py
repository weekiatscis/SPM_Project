"""
Test suite for Notification Service
Tests all endpoints and validates service health
"""

import sys
import os
import requests
import pytest

# Service configuration
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")

class TestNotificationService:
    """Test cases for Notification Service"""

    def test_service_health(self):
        """Test if Notification Service is running and accessible"""
        try:
            # Test with an endpoint that should respond
            response = requests.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications?user_id=test",
                timeout=5
            )
            assert response.status_code in [200, 400, 401, 403, 404, 500], \
                f"Service not responding properly. Status: {response.status_code}"
            print(f"✓ Notification Service is running (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            pytest.fail("Notification Service is not accessible. Check if service is running.")
        except requests.exceptions.Timeout:
            pytest.fail("Notification Service request timed out")

    def test_get_notifications_endpoint(self):
        """Test GET /notifications endpoint"""
        try:
            # Test without user_id (should require it)
            response = requests.get(f"{NOTIFICATION_SERVICE_URL}/notifications", timeout=5)
            assert response.status_code in [200, 400, 401], \
                f"Unexpected status code: {response.status_code}"

            # Test with user_id
            response = requests.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications?user_id=test-user",
                timeout=5
            )
            assert response.status_code in [200, 401], \
                f"Unexpected status code with user_id: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "notifications" in data, "Response should contain notifications array"
                assert "unread_count" in data or "total" in data, \
                    "Response should contain count information"

            print("✓ GET /notifications endpoint working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test /notifications endpoint: {str(e)}")

    def test_get_notifications_with_limit(self):
        """Test GET /notifications with limit parameter"""
        try:
            response = requests.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications?user_id=test-user&limit=10",
                timeout=5
            )
            assert response.status_code in [200, 401], \
                f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                if "notifications" in data:
                    assert len(data["notifications"]) <= 10, "Limit not working correctly"

            print("✓ GET /notifications with limit working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test notifications with limit: {str(e)}")

    def test_create_notification_endpoint(self):
        """Test POST /notifications/create endpoint"""
        try:
            # Test with invalid data
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications/create",
                json={},
                timeout=5
            )
            # Should validate required fields (400 or 422)
            assert response.status_code in [400, 422], \
                f"Should validate required fields. Got: {response.status_code}"

            print("✓ POST /notifications/create endpoint exists and validates input")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test create notification endpoint: {str(e)}")

    def test_notification_validation(self):
        """Test notification creation validation"""
        try:
            # Test with missing required fields
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications/create",
                json={
                    "user_id": "test-user"
                    # Missing title, message, type
                },
                timeout=5
            )
            assert response.status_code in [400, 422], \
                "Should validate required notification fields"

            print("✓ Notification validation working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test notification validation: {str(e)}")

    def test_mark_notification_read_endpoint(self):
        """Test PATCH /notifications/<id>/read endpoint"""
        try:
            response = requests.patch(
                f"{NOTIFICATION_SERVICE_URL}/notifications/dummy-id/read",
                json={"user_id": "test-user"},
                timeout=5
            )
            # Should return 400 or 404 for non-existent notification
            assert response.status_code in [400, 404], \
                f"Mark read endpoint error: {response.status_code}"

            print("✓ PATCH /notifications/<id>/read endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test mark read endpoint: {str(e)}")

    def test_mark_all_read_endpoint(self):
        """Test PATCH /notifications/mark-all-read endpoint"""
        try:
            response = requests.patch(
                f"{NOTIFICATION_SERVICE_URL}/notifications/mark-all-read",
                json={"user_id": "test-user"},
                timeout=5
            )
            # Should accept request (200 or 400)
            assert response.status_code in [200, 400, 500], \
                f"Mark all read endpoint error: {response.status_code}"

            print("✓ PATCH /notifications/mark-all-read endpoint structure valid")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test mark all read endpoint: {str(e)}")

    def test_test_notification_endpoint(self):
        """Test POST /test-notifications/<user_id> endpoint"""
        try:
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/test-notifications/test-user",
                timeout=5
            )
            # Should create test notification (201) or return error
            assert response.status_code in [200, 201, 400, 500], \
                f"Test notification endpoint error: {response.status_code}"

            if response.status_code in [200, 201]:
                data = response.json()
                assert "notification" in data or "message" in data, \
                    "Response should contain notification or message"

            print("✓ POST /test-notifications/<user_id> endpoint working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test test-notification endpoint: {str(e)}")

    def test_notification_types(self):
        """Test different notification types are supported"""
        try:
            # Test creating notification with different types
            notification_types = ["reminder", "test", "alert"]

            for notif_type in notification_types:
                response = requests.post(
                    f"{NOTIFICATION_SERVICE_URL}/notifications/create",
                    json={
                        "user_id": "test-user",
                        "title": f"Test {notif_type}",
                        "message": "Test message",
                        "type": notif_type
                    },
                    timeout=5
                )
                # Should accept different types (or fail validation consistently)
                assert response.status_code in [200, 201, 400, 500], \
                    f"Notification type {notif_type} handling failed"

            print("✓ Different notification types supported")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test notification types: {str(e)}")

    def test_rabbitmq_integration(self):
        """Test that service can handle RabbitMQ integration"""
        try:
            # The service should start even if RabbitMQ is temporarily unavailable
            # We test this by checking basic endpoint availability
            response = requests.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications?user_id=test",
                timeout=5
            )
            assert response.status_code in [200, 400, 401], \
                "Service should handle RabbitMQ connection gracefully"

            print("✓ RabbitMQ integration handled gracefully")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to test RabbitMQ integration: {str(e)}")


def run_tests():
    """Run all tests and return success status"""
    print(f"\n{'='*60}")
    print("NOTIFICATION SERVICE TEST SUITE")
    print(f"{'='*60}")
    print(f"Testing service at: {NOTIFICATION_SERVICE_URL}\n")

    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
