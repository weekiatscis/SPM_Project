#!/usr/bin/env python3
"""
Notification Scheduler - Runs every hour to check for task reminders

Run this script in the background:
  python3 src/microservices/notifications/notification_scheduler.py &

Or use a cron job:
  0 * * * * cd /path/to/SPM_Project && python3 src/microservices/notifications/notification_scheduler.py
"""

import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../.env'))

TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8080")
CHECK_INTERVAL = 3600  # 1 hour in seconds

def check_notifications():
    """Call the task service to check all tasks for notifications"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*70}")
        print(f"[{timestamp}] Checking task notifications...")
        print(f"{'='*70}")

        # Only check for due date reminders, not comment notifications
        response = requests.post(
            f"{TASK_SERVICE_URL}/check-all-tasks-notifications",
            timeout=30
        )

        if response.ok:
            data = response.json()
            print(f"✅ Successfully checked {data.get('tasks_processed', 0)} tasks for due date reminders")
            print(f"   {data.get('message', 'Due date notifications processed')}")
        else:
            print(f"❌ Failed to check notifications: HTTP {response.status_code}")
            print(f"   {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to task service at {TASK_SERVICE_URL}")
        print(f"   Make sure the task service is running!")
    except Exception as e:
        print(f"❌ Error checking notifications: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("NOTIFICATION SCHEDULER STARTED")
    print("=" * 70)
    print(f"Task Service: {TASK_SERVICE_URL}")
    print(f"Check Interval: Every {CHECK_INTERVAL//60} minutes")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)

    # Run immediately on start
    check_notifications()

    # Then run every hour
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            check_notifications()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("Notification scheduler stopped")
        print("=" * 70)
