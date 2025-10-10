#!/usr/bin/env python3
"""
Test script to create a task and verify email notification is sent
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../../.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8080")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 70)
print("TEST: Create Task and Verify Email Notification")
print("=" * 70)
print()

# Get Zenia's user ID
print("1️⃣ Finding user 'Zenia'...")
user_response = supabase.table("user").select("*").eq("name", "Zenia").execute()
if not user_response.data:
    print("❌ User 'Zenia' not found!")
    sys.exit(1)

user = user_response.data[0]
user_id = user['user_id']
user_email = user['email']
print(f"✅ Found: {user['name']} ({user_email})")
print()

# Calculate due date (5 days from now)
due_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
print(f"2️⃣ Creating task due in 5 days: {due_date}")
print()

# Create task payload
task_payload = {
    "title": f"Email Test {datetime.now().strftime('%H:%M:%S')}",
    "description": "Testing email notification on creation",
    "due_date": due_date,
    "status": "Ongoing",
    "priority": "High",
    "owner_id": user_id,
    "reminder_days": [1, 3, 4, 5, 6],  # Should trigger 5-day reminder
    "email_enabled": True,
    "in_app_enabled": False
}

print("📤 Sending request to task service...")
print(f"   URL: {TASK_SERVICE_URL}/tasks")
print(f"   Reminder days: {task_payload['reminder_days']}")
print(f"   Email enabled: {task_payload['email_enabled']}")
print(f"   In-app enabled: {task_payload['in_app_enabled']}")
print()

try:
    response = requests.post(
        f"{TASK_SERVICE_URL}/tasks",
        headers={"Content-Type": "application/json"},
        json=task_payload,
        timeout=10
    )

    if response.ok:
        result = response.json()
        task_id = result['task']['id']
        print("✅ Task created successfully!")
        print(f"   Task ID: {task_id}")
        print()

        # Wait a moment for async operations
        import time
        print("⏳ Waiting 2 seconds for notifications to process...")
        time.sleep(2)
        print()

        # Check notification preferences
        print("3️⃣ Checking notification preferences...")
        prefs = supabase.table("notification_preferences")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("task_id", task_id)\
            .execute()

        if prefs.data:
            email_enabled = prefs.data[0]['email_enabled']
            in_app_enabled = prefs.data[0]['in_app_enabled']
            print(f"✅ Preferences saved: Email={email_enabled}, In-App={in_app_enabled}")

            if email_enabled and not in_app_enabled:
                print("   ✅ Correct! Email-only as requested")
            else:
                print(f"   ⚠️  Expected Email=True, In-App=False")
        else:
            print("❌ No notification preferences found!")
        print()

        # Check reminder preferences
        print("4️⃣ Checking reminder schedule...")
        reminder_prefs = supabase.table("task_reminder_preferences")\
            .select("*")\
            .eq("task_id", task_id)\
            .execute()

        if reminder_prefs.data:
            reminder_days = reminder_prefs.data[0]['reminder_days']
            print(f"✅ Reminder schedule saved: {reminder_days}")

            if 5 in reminder_days:
                print("   ✅ Contains 5! Should trigger email immediately")
            else:
                print(f"   ⚠️  Does not contain 5. Won't trigger today.")
        else:
            print("❌ No reminder preferences found!")
        print()

        # Check if notification was created
        print("5️⃣ Checking if notification was created...")
        notifs = supabase.table("notifications")\
            .select("*")\
            .eq("task_id", task_id)\
            .execute()

        if notifs.data:
            print(f"✅ Found {len(notifs.data)} notification(s):")
            for notif in notifs.data:
                print(f"   - Type: {notif['type']}")
                print(f"     Title: {notif['title']}")
        else:
            print("❌ No notifications created!")
            print()
            print("⚠️  This means the email notification logic didn't run.")
            print("   Possible reasons:")
            print("   1. Task service isn't calling check_and_send_due_date_notifications()")
            print("   2. The function is failing silently")
            print("   3. Docker logs aren't showing the errors")
        print()

        print("=" * 70)
        print("📧 EXPECTED RESULT:")
        print("=" * 70)
        print(f"✉️  Email should be sent to: {user_email}")
        print(f"   Subject: ⏰ Task Reminder: {task_payload['title']}")
        print(f"   Check your inbox (and spam folder)!")
        print()
        print("If you didn't receive an email, the issue is in the task service.")
        print("Check Docker logs: docker logs <container_id>")
        print("=" * 70)

    else:
        print(f"❌ Failed to create task: HTTP {response.status_code}")
        print(f"   {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
