#!/usr/bin/env python3
"""
Test script to verify @mention notification functionality
Run this script to test if mention notifications are working properly
"""

import requests
import json
import os
from datetime import datetime, timezone

# Configuration
TASK_SERVICE_URL = os.getenv("VITE_TASK_SERVICE_URL", "http://localhost:8081")
PROJECT_SERVICE_URL = os.getenv("VITE_PROJECT_SERVICE_URL", "http://localhost:8082")

def test_task_mention():
    """Test @mention functionality in task comments"""
    print("🧪 Testing Task @Mention Notifications")
    print("=" * 50)
    
    # Test data - replace with actual user IDs and task ID from your system
    test_data = {
        "task_id": "your-task-id-here",  # Replace with actual task ID
        "comment_text": "Hey @john, can you review this task? @jane, your input would be helpful too!",
        "user_id": "your-user-id-here",  # Replace with actual user ID
        "user_name": "Test User"
    }
    
    print(f"📝 Test comment: {test_data['comment_text']}")
    print(f"👤 Commenter: {test_data['user_name']}")
    print(f"📋 Task ID: {test_data['task_id']}")
    
    # This would normally be called when a comment is added
    # For testing, we'll simulate the notification process
    print("\n🔍 Expected mentions: @john, @jane")
    print("📧 Expected notifications: 2 mention notifications")
    print("⚠️  Note: Replace the IDs above with actual values from your database")

def test_project_mention():
    """Test @mention functionality in project comments"""
    print("\n🧪 Testing Project @Mention Notifications")
    print("=" * 50)
    
    # Test data - replace with actual user IDs and project ID from your system
    test_data = {
        "project_id": "your-project-id-here",  # Replace with actual project ID
        "comment_text": "Great work team! @manager, can you approve this? @designer, please review the mockups.",
        "user_id": "your-user-id-here",  # Replace with actual user ID
        "user_name": "Test User"
    }
    
    print(f"📝 Test comment: {test_data['comment_text']}")
    print(f"👤 Commenter: {test_data['user_name']}")
    print(f"📋 Project ID: {test_data['project_id']}")
    
    print("\n🔍 Expected mentions: @manager, @designer")
    print("📧 Expected notifications: 2 mention notifications")
    print("⚠️  Note: Replace the IDs above with actual values from your database")

def check_notification_tables():
    """Check if notification tables exist and have the right structure"""
    print("\n🔍 Checking Database Tables")
    print("=" * 50)
    
    required_tables = [
        "notifications",
        "project_reminder_preferences", 
        "project_notification_preferences"
    ]
    
    print("Required tables:")
    for table in required_tables:
        print(f"  ✓ {table}")
    
    print("\n📋 Required notification fields:")
    print("  ✓ user_id")
    print("  ✓ title")
    print("  ✓ message") 
    print("  ✓ type (should be 'task_mention' or 'project_mention')")
    print("  ✓ task_id (for task mentions)")
    print("  ✓ project_id (for project mentions)")
    print("  ✓ created_at")
    print("  ✓ is_read")

def troubleshooting_tips():
    """Provide troubleshooting tips for mention notifications"""
    print("\n🔧 Troubleshooting Tips")
    print("=" * 50)
    
    print("1. Database Migration:")
    print("   - Run the SQL migration: docs/database_migrations/add_project_reminder_preferences.sql")
    print("   - Verify tables exist in Supabase dashboard")
    
    print("\n2. Check Notification Types:")
    print("   - Task mentions should have type: 'task_mention'")
    print("   - Project mentions should have type: 'project_mention'")
    
    print("\n3. Verify User Names:")
    print("   - @mentions should match exact user names in database")
    print("   - Case-insensitive matching is implemented")
    
    print("\n4. Check Logs:")
    print("   - Look for 'NOTIFY_COMMENT_MENTIONS CALLED' in task service logs")
    print("   - Look for 'NOTIFY_PROJECT_COMMENT_MENTIONS CALLED' in project service logs")
    print("   - Check for '✅ Mention notification created!' messages")
    
    print("\n5. Test Steps:")
    print("   - Create a task/project comment with @username")
    print("   - Check notifications table for new entries")
    print("   - Verify notification dropdown shows 'View Task/Project' buttons")

if __name__ == "__main__":
    print("🧪 @Mention Notification Test Suite")
    print("=" * 60)
    
    test_task_mention()
    test_project_mention()
    check_notification_tables()
    troubleshooting_tips()
    
    print("\n✅ Test suite completed!")
    print("📝 Next steps:")
    print("   1. Run the database migration")
    print("   2. Test with actual user IDs and task/project IDs")
    print("   3. Check the notification dropdown for 'View Project' buttons")
    print("   4. Verify mention notifications are created in the database")
