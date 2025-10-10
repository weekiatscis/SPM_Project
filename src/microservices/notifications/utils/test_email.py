#!/usr/bin/env python3
"""
Quick email test script
Run: python test_email.py your_email@example.com
"""

import sys
import os

# Add notifications module to path
sys.path.insert(0, 'src/microservices/notifications')

from email_service import send_notification_email

if len(sys.argv) < 2:
    print("Usage: python test_email.py your_email@example.com")
    print("Example: python test_email.py john@outlook.com")
    sys.exit(1)

test_email = sys.argv[1]

print("=" * 60)
print("SENDING TEST EMAIL")
print("=" * 60)
print(f"To: {test_email}")
print(f"Type: Task Reminder (3 days)")
print()
print("Sending... please wait...")

success = send_notification_email(
    user_email=test_email,
    notification_type="reminder_3_days",
    task_title="Complete Project Documentation",
    due_date="January 18, 2025",
    priority="High",
    task_id="test-123"
)

print()
print("=" * 60)
if success:
    print("✅ SUCCESS! Email sent!")
    print(f"\nCheck your inbox at: {test_email}")
    print("(Also check spam/junk folder)")
    print("\nWhat the email looks like:")
    print("  - Subject: ⏰ Task Reminder: Complete Project Documentation")
    print("  - Beautiful HTML design with gradient header")
    print("  - High priority badge (red)")
    print("  - 'View Task Details' button")
else:
    print("❌ FAILED!")
    print("\nPossible issues:")
    print("1. Gmail App Password is incorrect")
    print("2. 2FA not enabled on Gmail")
    print("3. SMTP blocked by firewall")
    print("\nCheck your .env file:")
    print(f"  SMTP_USER={os.getenv('SMTP_USER')}")
    print(f"  SMTP_PASSWORD={'*' * 10 if os.getenv('SMTP_PASSWORD') else 'NOT SET'}")
print("=" * 60)
