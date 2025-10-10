#!/usr/bin/env python3
"""
Force send email notification for a specific task
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Add parent directory to path to import email_service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from email_service import send_notification_email

# Load environment variables from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../../.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 70)
print("FORCE SEND EMAIL NOTIFICATION")
print("=" * 70)
print()

# Get task by title
task_title = "test email 1"
print(f"Looking for task: '{task_title}'")
print()

task_response = supabase.table("task").select("*").eq("title", task_title).execute()
tasks = task_response.data

if not tasks:
    print(f"❌ Task '{task_title}' not found!")
    sys.exit(1)

task = tasks[0]
task_id = task['task_id']
owner_id = task['owner_id']
due_date_str = task['due_date']
title = task['title']
priority = task.get('priority', 'Medium')

print(f"✅ Found task:")
print(f"   ID: {task_id}")
print(f"   Title: {title}")
print(f"   Due: {due_date_str}")
print(f"   Priority: {priority}")
print()

# Get owner email
user_response = supabase.table("user").select("name, email").eq("user_id", owner_id).execute()
if not user_response.data:
    print(f"❌ Owner not found!")
    sys.exit(1)

owner_email = user_response.data[0]['email']
owner_name = user_response.data[0]['name']

print(f"Owner: {owner_name} ({owner_email})")
print()

# Calculate days until due
due_date = datetime.strptime(str(due_date_str)[:10], "%Y-%m-%d").date()
today = datetime.now().date()
days_until = (due_date - today).days

print(f"📅 Days until due: {days_until}")
print()

# Check notification preferences
prefs_response = supabase.table("notification_preferences")\
    .select("*")\
    .eq("user_id", owner_id)\
    .eq("task_id", task_id)\
    .execute()

if prefs_response.data:
    email_enabled = prefs_response.data[0].get('email_enabled', True)
    in_app_enabled = prefs_response.data[0].get('in_app_enabled', True)
    print(f"Notification preferences: Email={email_enabled}, In-App={in_app_enabled}")
else:
    email_enabled = True
    in_app_enabled = True
    print(f"⚠️  No preferences found, using defaults")

print()

if not email_enabled:
    print("❌ Email notifications are DISABLED for this task!")
    print("   Cannot send email.")
    sys.exit(1)

# Send email
print("=" * 70)
print(f"📧 SENDING EMAIL to {owner_email}")
print("=" * 70)
print()

try:
    success = send_notification_email(
        user_email=owner_email,
        notification_type=f"reminder_{days_until}_days",
        task_title=title,
        due_date=due_date.strftime('%B %d, %Y'),
        priority=priority,
        task_id=task_id
    )

    if success:
        print()
        print("=" * 70)
        print("✅ SUCCESS! Email sent!")
        print("=" * 70)
        print()
        print(f"Check your inbox at: {owner_email}")
        print("Subject: ⏰ Task Reminder: " + title)
        print()
        print("If you don't see it:")
        print("1. Check your spam/junk folder")
        print("2. Check 'Promotions' or 'Updates' tabs in Gmail")
        print("3. Search for 'Task Reminder' in your inbox")
        print()

        # Also create in-app notification if enabled
        if in_app_enabled:
            notification_data = {
                "user_id": owner_id,
                "title": f"Task Due in {days_until} Day{'s' if days_until != 1 else ''}",
                "message": f"Task '{title}' is due on {due_date.strftime('%B %d, %Y')}",
                "type": f"reminder_{days_until}_days",
                "task_id": task_id,
                "due_date": due_date_str,
                "priority": priority,
                "is_read": False
            }

            supabase.table("notifications").insert(notification_data).execute()
            print("✅ Also created in-app notification")

    else:
        print()
        print("=" * 70)
        print("❌ FAILED to send email")
        print("=" * 70)
        print()
        print("Check the error messages above for details.")

except Exception as e:
    print()
    print("=" * 70)
    print(f"❌ ERROR: {e}")
    print("=" * 70)
    import traceback
    traceback.print_exc()
