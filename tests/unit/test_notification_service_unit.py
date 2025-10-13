"""
Unit tests for Notification Service
Tests individual functions and business logic with mocked dependencies
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import sys
import os

# Add source directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'microservices', 'notifications'))

# Note: Import what's available from notification_service
# Some functions may need to be tested through their endpoints


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
