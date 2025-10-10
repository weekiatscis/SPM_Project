#!/usr/bin/env python3
"""
Debug script to check why task notifications aren't being sent
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../../.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 70)
print("TASK NOTIFICATION DEBUG TOOL")
print("=" * 70)
print()

# Get all users
print("📋 USERS IN DATABASE:")
print("-" * 70)
users_response = supabase.table("user").select("user_id, name, email").execute()
users = users_response.data or []

if not users:
    print("❌ No users found in database!")
    sys.exit(1)

for i, user in enumerate(users, 1):
    print(f"{i}. {user['name']} ({user['email']}) - ID: {user['user_id'][:8]}...")

print()
print("=" * 70)
print("📅 TASKS WITH DUE DATES:")
print("-" * 70)

# Get all tasks with due dates
tasks_response = supabase.table("task").select("*").not_.is_("due_date", "null").execute()
tasks = tasks_response.data or []

if not tasks:
    print("❌ No tasks with due dates found!")
    sys.exit(1)

today = datetime.now().date()

for task in tasks:
    task_id = task['task_id']
    title = task['title']
    due_date = datetime.strptime(str(task['due_date'])[:10], "%Y-%m-%d").date()
    owner_id = task['owner_id']
    days_until = (due_date - today).days

    # Find owner
    owner = next((u for u in users if u['user_id'] == owner_id), None)
    owner_email = owner['email'] if owner else "Unknown"
    owner_name = owner['name'] if owner else "Unknown"

    print(f"\n📝 Task: {title}")
    print(f"   ID: {task_id[:8]}...")
    print(f"   Due: {due_date} ({days_until} days from today)")
    print(f"   Owner: {owner_name} ({owner_email})")

    # Check if this task should trigger a notification
    if days_until in [1, 3, 7]:
        print(f"   ⚠️  SHOULD SEND NOTIFICATION! ({days_until}-day reminder)")
    elif days_until < 0:
        print(f"   ⏰ OVERDUE by {abs(days_until)} days")
    else:
        print(f"   ℹ️  No reminder needed today")

    # Check notification preferences
    prefs_response = supabase.table("notification_preferences").select("*").eq("user_id", owner_id).eq("task_id", task_id).execute()
    prefs = prefs_response.data

    if prefs:
        email_enabled = prefs[0].get('email_enabled', True)
        in_app_enabled = prefs[0].get('in_app_enabled', True)
        print(f"   Notification prefs: Email={email_enabled}, In-App={in_app_enabled}")
    else:
        print(f"   ⚠️  No notification preferences found (will use defaults)")

    # Check reminder preferences
    reminder_prefs_response = supabase.table("task_reminder_preferences").select("*").eq("task_id", task_id).execute()
    reminder_prefs = reminder_prefs_response.data

    if reminder_prefs:
        reminder_days = reminder_prefs[0].get('reminder_days', [7, 3, 1])
        print(f"   Reminder schedule: {reminder_days} days before")
    else:
        print(f"   Reminder schedule: [7, 3, 1] (default)")

    # Check existing notifications
    notif_response = supabase.table("notifications").select("*").eq("task_id", task_id).execute()
    existing_notifs = notif_response.data or []

    if existing_notifs:
        print(f"   Existing notifications: {len(existing_notifs)}")
        for notif in existing_notifs[:3]:
            print(f"      - {notif['type']}: {notif['title']}")
    else:
        print(f"   No notifications yet")

print()
print("=" * 70)
print("💡 RECOMMENDATIONS:")
print("-" * 70)

# Check if any tasks should trigger notifications today
tasks_to_notify = [t for t in tasks if (datetime.strptime(str(t['due_date'])[:10], "%Y-%m-%d").date() - today).days in [1, 3, 7]]

if tasks_to_notify:
    print(f"✅ {len(tasks_to_notify)} task(s) should trigger notifications today!")
    print(f"\nTo trigger notifications, run:")
    print(f"   curl -X POST http://localhost:8080/check-all-tasks-notifications")
    print(f"\nOr for a specific task:")
    for task in tasks_to_notify:
        print(f"   curl -X POST http://localhost:8080/tasks/{task['task_id']}/check-notifications")
else:
    print(f"⚠️  No tasks are 1, 3, or 7 days away from due date.")
    print(f"\nTo test, create a task with due date:")
    print(f"   - {today + timedelta(days=7)} (7 days from today)")
    print(f"   - {today + timedelta(days=3)} (3 days from today)")
    print(f"   - {today + timedelta(days=1)} (tomorrow)")

print()
print("=" * 70)
