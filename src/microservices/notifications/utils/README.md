# Notification Utilities

This folder contains utility scripts for debugging and testing the notification system.

## Testing Scripts

### 1. `test_email.py`
Quick test to verify SMTP email configuration works.

**Usage:**
```bash
# From project root
python3 src/microservices/notifications/utils/test_email.py YOUR_EMAIL@example.com
```

**Example:**
```bash
python3 src/microservices/notifications/utils/test_email.py zeniakqfoo@gmail.com
```

**What it does:**
- Sends a test email immediately
- Shows success/failure message
- Helpful for verifying SMTP credentials

---

### 2. `test_task_email.sh`
Bash script to create a test task and trigger email notifications.

**Usage:**
```bash
# From project root
bash src/microservices/notifications/utils/test_task_email.sh
```

**What it does:**
- Calculates due date (7 days from today)
- Creates a test task with email-only notifications
- Shows you what to look for in logs

---

## Debug Scripts

### 3. `debug_task_notifications.py`
Debug tool to check all tasks and their notification status.

**Usage:**
```bash
# From project root
python3 src/microservices/notifications/utils/debug_task_notifications.py
```

**What it shows:**
- All users in the database
- All tasks with due dates
- Days until due for each task
- Whether notifications should be sent today
- Notification preferences (Email/In-App)
- Reminder schedules
- Existing notifications

---

### 4. `force_send_email.py`
Manually send email notification for a specific task (bypasses normal checks).

**Usage:**
```bash
# From project root
python3 src/microservices/notifications/utils/force_send_email.py
```

**When to use:**
- Testing email delivery
- Resending missed notifications
- Debugging email issues

**Note:** Currently hardcoded to send for task titled "test email 1". Edit the script to change the task.

---

## Parent Directory Scripts

### `notification_scheduler.py`
Runs continuously in the background, checking for task reminders every hour.

**Usage:**
```bash
# From project root
python3 src/microservices/notifications/notification_scheduler.py &
```

**What it does:**
- Checks all tasks every hour
- Sends notifications for tasks due in 7, 3, or 1 days (or custom schedule)
- Respects user notification preferences (Email/In-App)
- Prevents duplicate notifications

**Recommended:** Run this in production to ensure users get timely reminders!

---

## Requirements

All scripts require:
- Python 3.x
- `supabase` package
- `python-dotenv` package
- `requests` package
- Valid `.env` file at project root

Install dependencies:
```bash
pip3 install supabase python-dotenv requests
```

---

## Documentation

See `/docs/EMAIL_NOTIFICATION_GUIDE.md` for complete documentation on the email notification system.
