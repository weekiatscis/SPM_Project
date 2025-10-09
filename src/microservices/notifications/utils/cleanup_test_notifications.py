#!/usr/bin/env python3
"""
Cleanup test email notifications from database
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../../.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 70)
print("CLEANUP TEST EMAIL NOTIFICATIONS")
print("=" * 70)
print()

# Get all notifications with test-related titles
print("🔍 Finding test notifications...")
response = supabase.table("notifications").select("*").execute()
all_notifications = response.data or []

# Filter for test notifications
test_patterns = [
    "email test",
    "Email Test",
    "test email",
    "Test Email"
]

test_notifications = [
    n for n in all_notifications
    if any(pattern.lower() in n['title'].lower() or pattern.lower() in n['message'].lower()
           for pattern in test_patterns)
]

if not test_notifications:
    print("✅ No test notifications found!")
    print("   Your inbox is clean!")
    sys.exit(0)

print(f"Found {len(test_notifications)} test notification(s):")
print()

# Show what will be deleted
for i, notif in enumerate(test_notifications, 1):
    print(f"{i}. {notif['title']}")
    print(f"   Message: {notif['message'][:60]}...")
    print(f"   Created: {notif['created_at']}")
    print(f"   ID: {notif['id']}")
    print()

# Confirm deletion
confirm = input(f"Delete these {len(test_notifications)} notification(s)? (yes/no): ").strip().lower()

if confirm not in ['yes', 'y']:
    print("❌ Cancelled. No notifications deleted.")
    sys.exit(0)

print()
print("🗑️  Deleting test notifications...")

deleted_count = 0
for notif in test_notifications:
    try:
        supabase.table("notifications").delete().eq("id", notif['id']).execute()
        deleted_count += 1
        print(f"   ✅ Deleted: {notif['title']}")
    except Exception as e:
        print(f"   ❌ Failed to delete {notif['id']}: {e}")

print()
print("=" * 70)
print(f"✅ CLEANUP COMPLETE!")
print(f"   Deleted {deleted_count} out of {len(test_notifications)} notification(s)")
print("=" * 70)
