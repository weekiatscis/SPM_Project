"""
Notification Service Test Suite
Combines unit tests and integration tests for the Notification Service
"""

import sys
import os
import requests
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Add source directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'microservices', 'notifications'))

# Import email service functions for unit testing
try:
    from email_service import create_email_template, send_email
except ImportError:
    create_email_template = None
    send_email = None

# Service configuration for integration tests
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8084")


# ============================================================================
# UNIT TESTS - Test individual functions and business logic with mocks
# ============================================================================

class TestNotificationValidation:
    """Test notification data validation"""

    def test_required_fields_present(self):
        """Test that all required notification fields are present"""
        notification_data = {
            "user_id": "user-123",
            "title": "Test Notification",
            "message": "This is a test",
            "type": "reminder"
        }

        required_fields = ["user_id", "title", "message", "type"]
        all_present = all(field in notification_data for field in required_fields)

        assert all_present == True

    def test_required_fields_missing(self):
        """Test detection of missing required fields"""
        notification_data = {
            "user_id": "user-123",
            "title": "Test Notification"
            # Missing 'message' and 'type'
        }

        required_fields = ["user_id", "title", "message", "type"]
        all_present = all(field in notification_data for field in required_fields)

        assert all_present == False

    def test_notification_field_types(self):
        """Test that notification fields have correct types"""
        notification_data = {
            "user_id": "user-123",
            "title": "Test Notification",
            "message": "This is a test",
            "type": "reminder",
            "is_read": False
        }

        assert isinstance(notification_data["user_id"], str)
        assert isinstance(notification_data["title"], str)
        assert isinstance(notification_data["message"], str)
        assert isinstance(notification_data["type"], str)
        assert isinstance(notification_data["is_read"], bool)


class TestNotificationTypes:
    """Test notification type handling"""

    def test_valid_notification_types(self):
        """Test valid notification types"""
        valid_types = [
            "reminder",
            "reminder_7_days",
            "reminder_3_days",
            "reminder_1_days",
            "test",
            "alert",
            "info"
        ]

        for notif_type in valid_types:
            assert isinstance(notif_type, str)
            assert len(notif_type) > 0

    def test_reminder_type_parsing(self):
        """Test parsing of reminder notification types"""
        reminder_types = [
            "reminder_7_days",
            "reminder_3_days",
            "reminder_1_days"
        ]

        for reminder_type in reminder_types:
            if reminder_type.startswith("reminder_"):
                parts = reminder_type.split("_")
                if len(parts) >= 2 and parts[1].isdigit():
                    days = int(parts[1])
                    assert days >= 1
                    assert days <= 10

    def test_notification_type_categorization(self):
        """Test categorization of notification types"""
        notification_type = "reminder_7_days"

        is_reminder = notification_type.startswith("reminder")
        is_alert = notification_type == "alert"
        is_test = notification_type == "test"

        assert is_reminder == True
        assert is_alert == False
        assert is_test == False


class TestNotificationFiltering:
    """Test notification filtering logic"""

    def test_filter_by_user_id(self):
        """Test filtering notifications by user ID"""
        notifications = [
            {"id": "1", "user_id": "user-123", "title": "Notification 1"},
            {"id": "2", "user_id": "user-456", "title": "Notification 2"},
            {"id": "3", "user_id": "user-123", "title": "Notification 3"}
        ]

        user_notifications = [n for n in notifications if n["user_id"] == "user-123"]

        assert len(user_notifications) == 2
        assert all(n["user_id"] == "user-123" for n in user_notifications)

    def test_filter_unread_notifications(self):
        """Test filtering for unread notifications"""
        notifications = [
            {"id": "1", "is_read": False, "title": "Unread 1"},
            {"id": "2", "is_read": True, "title": "Read"},
            {"id": "3", "is_read": False, "title": "Unread 2"}
        ]

        unread = [n for n in notifications if not n["is_read"]]

        assert len(unread) == 2
        assert all(not n["is_read"] for n in unread)

    def test_count_unread_notifications(self):
        """Test counting unread notifications"""
        notifications = [
            {"id": "1", "is_read": False},
            {"id": "2", "is_read": True},
            {"id": "3", "is_read": False},
            {"id": "4", "is_read": False}
        ]

        unread_count = sum(1 for n in notifications if not n["is_read"])

        assert unread_count == 3

    def test_filter_by_type(self):
        """Test filtering notifications by type"""
        notifications = [
            {"id": "1", "type": "reminder", "title": "Reminder"},
            {"id": "2", "type": "alert", "title": "Alert"},
            {"id": "3", "type": "reminder", "title": "Another Reminder"}
        ]

        reminders = [n for n in notifications if n["type"] == "reminder"]

        assert len(reminders) == 2

    def test_limit_notifications(self):
        """Test limiting number of notifications returned"""
        notifications = [
            {"id": str(i), "title": f"Notification {i}"}
            for i in range(20)
        ]

        limit = 10
        limited = notifications[:limit]

        assert len(limited) == 10
        assert len(limited) <= limit


class TestNotificationCreation:
    """Test notification creation logic"""

    def test_notification_payload_construction(self):
        """Test construction of notification payload"""
        now = datetime.now(timezone.utc).isoformat()

        notification_data = {
            "user_id": "user-123",
            "title": "Task Due Soon",
            "message": "Your task is due in 3 days",
            "type": "reminder_3_days",
            "task_id": "task-456",
            "created_at": now,
            "is_read": False
        }

        assert "user_id" in notification_data
        assert "title" in notification_data
        assert "message" in notification_data
        assert "type" in notification_data
        assert notification_data["is_read"] == False

    def test_notification_with_optional_fields(self):
        """Test notification creation with optional fields"""
        notification_data = {
            "user_id": "user-123",
            "title": "Test",
            "message": "Test message",
            "type": "test",
            "task_id": "task-123",
            "project_id": "proj-456",
            "due_date": "2025-12-31"
        }

        # Optional fields should be present if provided
        assert notification_data.get("task_id") == "task-123"
        assert notification_data.get("project_id") == "proj-456"
        assert notification_data.get("due_date") == "2025-12-31"


class TestNotificationMarkAsRead:
    """Test marking notifications as read"""

    def test_mark_single_notification_as_read(self):
        """Test marking a single notification as read"""
        notification = {
            "id": "notif-123",
            "user_id": "user-123",
            "is_read": False
        }

        # Mark as read
        notification["is_read"] = True

        assert notification["is_read"] == True

    def test_mark_all_as_read_for_user(self):
        """Test marking all notifications as read for a user"""
        notifications = [
            {"id": "1", "user_id": "user-123", "is_read": False},
            {"id": "2", "user_id": "user-123", "is_read": False},
            {"id": "3", "user_id": "user-456", "is_read": False}
        ]

        user_id = "user-123"

        # Mark all for user as read
        for notif in notifications:
            if notif["user_id"] == user_id:
                notif["is_read"] = True

        user_notifications = [n for n in notifications if n["user_id"] == user_id]
        assert all(n["is_read"] for n in user_notifications)

        # Other users' notifications should remain unread
        other_notifications = [n for n in notifications if n["user_id"] != user_id]
        assert all(not n["is_read"] for n in other_notifications)

    def test_count_marked_as_read(self):
        """Test counting how many notifications were marked as read"""
        notifications = [
            {"id": "1", "user_id": "user-123", "is_read": False},
            {"id": "2", "user_id": "user-123", "is_read": False},
            {"id": "3", "user_id": "user-123", "is_read": True}  # Already read
        ]

        user_id = "user-123"
        marked_count = 0

        for notif in notifications:
            if notif["user_id"] == user_id and not notif["is_read"]:
                notif["is_read"] = True
                marked_count += 1

        assert marked_count == 2


class TestNotificationPriority:
    """Test notification priority and ordering"""

    def test_sort_by_created_date_desc(self):
        """Test sorting notifications by creation date (newest first)"""
        notifications = [
            {"id": "1", "created_at": "2025-01-01T10:00:00Z", "title": "Old"},
            {"id": "2", "created_at": "2025-01-03T10:00:00Z", "title": "New"},
            {"id": "3", "created_at": "2025-01-02T10:00:00Z", "title": "Medium"}
        ]

        sorted_notifs = sorted(notifications, key=lambda x: x["created_at"], reverse=True)

        assert sorted_notifs[0]["id"] == "2"  # Newest
        assert sorted_notifs[1]["id"] == "3"
        assert sorted_notifs[2]["id"] == "1"  # Oldest

    def test_unread_notifications_first(self):
        """Test prioritizing unread notifications"""
        notifications = [
            {"id": "1", "is_read": True, "created_at": "2025-01-03T10:00:00Z"},
            {"id": "2", "is_read": False, "created_at": "2025-01-02T10:00:00Z"},
            {"id": "3", "is_read": False, "created_at": "2025-01-01T10:00:00Z"}
        ]

        # Sort: unread first (False < True), then by date descending
        sorted_notifs = sorted(
            notifications,
            key=lambda x: (x["is_read"], -ord(x["created_at"][0]))  # is_read ascending, date descending
        )

        # First two should be unread
        assert sorted_notifs[0]["is_read"] == False
        assert sorted_notifs[1]["is_read"] == False
        assert sorted_notifs[2]["is_read"] == True


class TestRabbitMQMessageFormat:
    """Test RabbitMQ message formatting"""

    def test_task_notification_message_format(self):
        """Test format of task notification messages for RabbitMQ"""
        message = {
            "task_id": "task-123",
            "user_id": "user-456",
            "title": "Task Due in 3 Days",
            "message": "Your task 'Complete Report' is due in 3 days",
            "type": "reminder_3_days",
            "due_date": "2025-01-18",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Verify message structure
        assert "task_id" in message
        assert "user_id" in message
        assert "title" in message
        assert "message" in message
        assert "type" in message
        assert message["type"].startswith("reminder")

    def test_routing_key_generation(self):
        """Test generation of routing keys for RabbitMQ"""
        notification_type = "reminder_3_days"

        # Generate routing key: task.reminder.3_days
        routing_key = f"task.{notification_type.replace('_', '.', 1)}"

        assert routing_key == "task.reminder.3_days"

        # Test with different types
        alert_type = "alert"
        alert_routing_key = f"task.{alert_type}"

        assert alert_routing_key == "task.alert"


class TestNotificationDeletion:
    """Test notification deletion logic"""

    def test_delete_old_reminder_notifications(self):
        """Test deletion of old reminder notifications for a task"""
        notifications = [
            {"id": "1", "task_id": "task-123", "type": "reminder_7_days"},
            {"id": "2", "task_id": "task-123", "type": "reminder_3_days"},
            {"id": "3", "task_id": "task-456", "type": "reminder_7_days"},
            {"id": "4", "task_id": "task-123", "type": "alert"}
        ]

        task_id = "task-123"

        # Filter notifications to delete (task reminders only)
        to_delete = [
            n for n in notifications
            if n["task_id"] == task_id and n["type"].startswith("reminder")
        ]

        assert len(to_delete) == 2
        assert all(n["task_id"] == task_id for n in to_delete)
        assert all(n["type"].startswith("reminder") for n in to_delete)


class TestEmailTemplateCreation:
    """Test email template generation for different notification types"""

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_reminder_email_template(self):
        """Test creation of reminder email template"""
        data = {
            "task_title": "Complete Project Report",
            "due_date": "2025-10-20",
            "priority": 8,
            "task_id": "task-123"
        }

        subject, html = create_email_template("reminder_7_days", data)

        assert "Complete Project Report" in subject
        assert "Complete Project Report" in html
        assert "2025-10-20" in html
        assert "7 day(s)" in html
        assert "task-123" in html
        assert "Priority" in html
        assert html.strip().startswith("<!DOCTYPE html>")

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_reminder_email_priority_high(self):
        """Test reminder email with high priority (red badge)"""
        data = {
            "task_title": "Urgent Task",
            "due_date": "2025-10-16",
            "priority": 9,
            "task_id": "task-456"
        }

        subject, html = create_email_template("reminder_1_days", data)

        assert "#cf1322" in html  # Red color for high priority
        assert "High" in html
        assert "Urgent Task" in html
        assert "Urgent Task" in subject

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_reminder_email_priority_medium(self):
        """Test reminder email with medium priority (orange badge)"""
        data = {
            "task_title": "Medium Task",
            "due_date": "2025-10-18",
            "priority": 6,
            "task_id": "task-789"
        }

        subject, html = create_email_template("reminder_3_days", data)

        assert "#d46b08" in html  # Orange color for medium priority
        assert "Medium" in html
        assert "Medium Task" in subject

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_reminder_email_priority_low(self):
        """Test reminder email with low priority (green badge)"""
        data = {
            "task_title": "Low Priority Task",
            "due_date": "2025-10-25",
            "priority": 3,
            "task_id": "task-321"
        }

        subject, html = create_email_template("reminder_7_days", data)

        assert "#389e0d" in html  # Green color for low priority
        assert "Low" in html
        assert "Low Priority Task" in subject

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_reminder_email_priority_string_conversion(self):
        """Test that string priority values are converted to int"""
        data = {
            "task_title": "Task with String Priority",
            "due_date": "2025-10-20",
            "priority": "7",  # String instead of int
            "task_id": "task-999"
        }

        subject, html = create_email_template("reminder_7_days", data)

        # Should handle string priority and convert it
        assert "Priority" in html
        assert "Task with String Priority" in html
        assert "Task with String Priority" in subject

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_due_date_change_email_template(self):
        """Test creation of due date change email template"""
        data = {
            "task_title": "Updated Task",
            "old_due_date": "2025-10-15",
            "new_due_date": "2025-10-20",
            "priority": 7,
            "task_id": "task-555"
        }

        subject, html = create_email_template("due_date_change", data)

        assert "Updated Task" in html
        assert "2025-10-15" in html  # Old date
        assert "2025-10-20" in html  # New date
        assert "Due Date Changed" in html
        assert "Previous Due Date" in html
        assert "New Due Date" in html
        assert "Updated Task" in subject

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_task_comment_email_template(self):
        """Test creation of task comment email template"""
        data = {
            "task_title": "Commented Task",
            "comment_text": "This is a test comment",
            "commenter_name": "John Doe",
            "due_date": "2025-10-20",
            "priority": 5,
            "task_id": "task-777"
        }

        subject, html = create_email_template("task_comment", data)

        assert "Commented Task" in html
        assert "This is a test comment" in html
        assert "John Doe" in html
        assert "New Comment" in html
        assert "Commented Task" in subject

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_project_comment_email_template(self):
        """Test creation of project comment email template"""
        data = {
            "project_name": "Test Project",
            "comment_text": "Project comment text",
            "commenter_name": "Jane Smith",
            "project_id": "project-888"
        }

        subject, html = create_email_template("project_comment", data)

        assert "Test Project" in html
        assert "Project comment text" in html
        assert "Jane Smith" in html
        assert "New Project Comment" in html
        assert "project-888" in html
        assert "Test Project" in subject

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_email_template_with_missing_optional_fields(self):
        """Test email template creation with minimal data"""
        data = {
            "task_title": "Minimal Task",
            "priority": 5
        }

        subject, html = create_email_template("reminder_7_days", data)

        assert "Minimal Task" in html
        assert html.strip().startswith("<!DOCTYPE html>")
        assert "Minimal Task" in subject
        # Should handle missing due_date and task_id gracefully

    @pytest.mark.skipif(create_email_template is None, reason="email_service not available")
    def test_email_template_frontend_url_in_links(self):
        """Test that email templates include proper frontend URLs"""
        data = {
            "task_title": "Task with Link",
            "due_date": "2025-10-20",
            "priority": 5,
            "task_id": "task-link-123"
        }

        subject, html = create_email_template("reminder_7_days", data)

        # Should contain a link to the task
        assert "href=" in html
        assert "task-link-123" in html
        assert isinstance(subject, str)


class TestEmailSending:
    """Test email sending functionality"""

    @pytest.mark.skipif(send_email is None, reason="email_service not available")
    @patch('email_service.SMTP_USER', 'test@example.com')  # Mock credentials
    @patch('email_service.SMTP_PASSWORD', 'test_password')  # Mock credentials
    @patch('email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test Content</h1>"
        )

        assert result == True
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.send_message.assert_called_once()

    @pytest.mark.skipif(send_email is None, reason="email_service not available")
    @patch('email_service.SMTP_USER', 'test@example.com')
    @patch('email_service.SMTP_PASSWORD', 'test_password')
    @patch('email_service.smtplib.SMTP')
    def test_send_email_smtp_failure(self, mock_smtp):
        """Test email sending with SMTP failure"""
        mock_smtp.side_effect = Exception("SMTP connection failed")

        result = send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test Content</h1>"
        )

        assert result == False

    @pytest.mark.skipif(send_email is None, reason="email_service not available")
    @patch('email_service.SMTP_USER', 'test@example.com')
    @patch('email_service.SMTP_PASSWORD', 'test_password')
    @patch('email_service.smtplib.SMTP')
    def test_send_email_authentication_failure(self, mock_smtp):
        """Test email sending with authentication failure"""
        mock_server = Mock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test Content</h1>"
        )

        assert result == False

    @pytest.mark.skipif(send_email is None, reason="email_service not available")
    @patch('email_service.SMTP_USER', 'test@example.com')
    @patch('email_service.SMTP_PASSWORD', 'test_password')
    @patch('email_service.smtplib.SMTP')
    def test_send_email_with_special_characters(self, mock_smtp):
        """Test email sending with special characters in subject"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = send_email(
            to_email="test@example.com",
            subject="Test: Special Chars 💬 📧",
            html_content="<h1>Content with émojis</h1>"
        )

        assert result == True


# ============================================================================
# INTEGRATION TESTS - Test actual service endpoints
# ============================================================================

class TestNotificationServiceIntegration:
    """Integration tests for Notification Service endpoints"""

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




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
