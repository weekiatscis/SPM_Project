# 📁 Notification System File Organization

## Directory Structure

```
SPM_Project/
│
├── docs/
│   └── EMAIL_NOTIFICATION_GUIDE.md          # Complete email notification documentation
│
├── src/
│   └── microservices/
│       ├── tasks/
│       │   └── task_service.py               # Main task service (handles task CRUD + notifications)
│       │
│       └── notifications/
│           ├── notification_service.py       # Real-time notification service
│           ├── email_service.py              # Email sending functionality
│           ├── notification_scheduler.py     # 🆕 Runs every hour to check for reminders
│           │
│           └── utils/                        # 🆕 Utility scripts for debugging/testing
│               ├── README.md                 # Documentation for utility scripts
│               ├── test_email.py             # Quick SMTP test
│               ├── test_task_email.sh        # Create test task with email
│               ├── debug_task_notifications.py   # Debug tool to check all tasks
│               └── force_send_email.py       # Manually send email for a task
```

## 📋 Quick Reference

### Services (Always Running)
- `task_service.py` - Port 8080
- `notification_service.py` - Port 8084
- `notification_scheduler.py` - Background process (checks every hour)

### Utilities (Run When Needed)
- `test_email.py` - Test SMTP configuration
- `test_task_email.sh` - Create test task with email notifications
- `debug_task_notifications.py` - Check task notification status
- `force_send_email.py` - Send email immediately for testing

### Documentation
- `EMAIL_NOTIFICATION_GUIDE.md` - Complete guide
- `utils/README.md` - Utility scripts documentation

## 🚀 How to Run

### Start All Services
```bash
# Terminal 1: Task Service
cd src/microservices/tasks
python3 task_service.py

# Terminal 2: Notification Service
cd src/microservices/notifications
python3 notification_service.py

# Terminal 3: Notification Scheduler
python3 src/microservices/notifications/notification_scheduler.py
```

### Debug/Test
```bash
# Test SMTP configuration
python3 src/microservices/notifications/utils/test_email.py your_email@example.com

# Create test task with email notifications
bash src/microservices/notifications/utils/test_task_email.sh

# Check all tasks and notification status
python3 src/microservices/notifications/utils/debug_task_notifications.py

# Force send email for testing
python3 src/microservices/notifications/utils/force_send_email.py
```

## 📝 Notes

- **Services** should run continuously in production
- **Scheduler** is essential for automatic reminders
- **Utilities** are for debugging and testing only
- **Documentation** in `docs/` folder for easy reference

All organized and neat! 🎯
