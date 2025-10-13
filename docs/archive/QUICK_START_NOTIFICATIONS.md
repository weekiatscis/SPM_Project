# 🚀 Quick Start: Email Notifications

## ⚡ TL;DR - Get It Working Now!

### 1. Setup Auto-Start Scheduler (One-Time Setup)
```bash
./setup_scheduler_autostart.sh
```

This will:
- ✅ Create scheduler that runs every hour
- ✅ Auto-start on system boot
- ✅ Send emails for tasks due in 7, 3, 1 days (or custom schedules)

### 2. Test Email Right Now
```bash
# Test SMTP configuration
python3 src/microservices/notifications/utils/test_email.py zeniakqfoo@gmail.com

# Create test task and check if email sent
python3 src/microservices/notifications/utils/test_create_task_with_email.py
```

### 3. Check Your Email!
📧 Check **zeniakqfoo@gmail.com** (and spam folder!)

---

## 📋 What Was Fixed Today

### Problem 1: "I create tasks but don't get emails" ❌

**Fixed By:**
1. ✅ Added SMTP credentials to Docker container
2. ✅ Added email_service.py to Docker container
3. ✅ Rebuilt Docker: `docker-compose up -d --build task-service`

**Now:** Emails should send when you create tasks!

### Problem 2: "I have to manually run scheduler daily" ❌

**Fixed By:**
1. ✅ Created auto-start script: `setup_scheduler_autostart.sh`
2. ✅ Uses macOS LaunchAgent (runs on boot)

**Now:** Scheduler runs automatically forever!

---

## 🎯 How It Works Now

### When You Create a Task:

**Example:** Task due **October 14** (5 days away), schedule **[1, 3, 4, 5, 6]**

1. **Immediately (Task Creation):**
   - ✅ Task created in database
   - ✅ Preferences saved (email/in-app toggles)
   - ✅ Reminder schedule saved
   - ✅ System checks: "Is today 5 days before due date?" → YES!
   - ✅ **Email sent immediately** to zeniakqfoo@gmail.com

2. **Tomorrow (4 days away):**
   - ⏰ Scheduler runs (every hour)
   - ✅ Finds your task is 4 days away
   - ✅ 4 is in schedule → **sends 4-day reminder email**

3. **Next Day (3 days away):**
   - ✅ **Sends 3-day reminder email**

4. **Next Day (2 days away):**
   - ❌ 2 NOT in schedule → no email

5. **Final Day (1 day away):**
   - ✅ **Sends final 1-day reminder email**

---

## 📊 Verification Checklist

Run these to verify everything works:

```bash
# 1. Check Docker container has email service
docker exec spm_project-task-service-1 ls -la ../notifications/
# Should see: email_service.py

# 2. Check SMTP credentials in Docker
docker exec spm_project-task-service-1 env | grep SMTP
# Should see your Gmail credentials

# 3. Check scheduler is running
launchctl list | grep spm
# Should see: com.spm.notification_scheduler with a PID

# 4. Check scheduler logs
tail -f ~/Documents/GitHub/SPM_Project/logs/notification_scheduler.log
# Should see hourly check messages

# 5. Debug all tasks
python3 src/microservices/notifications/utils/debug_task_notifications.py
# Shows which tasks should trigger notifications
```

---

## 🐛 Troubleshooting

### "Still not getting emails when creating tasks"

```bash
# Check Docker logs for errors
docker logs spm_project-task-service-1 --tail 50

# Rebuild Docker container
docker-compose down
docker-compose up -d --build task-service

# Test email service
python3 src/microservices/notifications/utils/test_email.py zeniakqfoo@gmail.com
```

### "Scheduler not running"

```bash
# Check status
launchctl list | grep spm

# View error logs
cat ~/Documents/GitHub/SPM_Project/logs/notification_scheduler_error.log

# Restart scheduler
launchctl unload ~/Library/LaunchAgents/com.spm.notification_scheduler.plist
launchctl load ~/Library/LaunchAgents/com.spm.notification_scheduler.plist
```

### "How do I know if it's working?"

```bash
# Watch scheduler in real-time
tail -f ~/Documents/GitHub/SPM_Project/logs/notification_scheduler.log

# Create test task
python3 src/microservices/notifications/utils/test_create_task_with_email.py

# Check if notification was created
python3 src/microservices/notifications/utils/debug_task_notifications.py
```

---

## 📖 Full Documentation

- **Complete Guide**: [docs/EMAIL_FIX_AND_SCHEDULER_SETUP.md](docs/EMAIL_FIX_AND_SCHEDULER_SETUP.md)
- **Email Notification Guide**: [docs/EMAIL_NOTIFICATION_GUIDE.md](docs/EMAIL_NOTIFICATION_GUIDE.md)
- **File Organization**: [NOTIFICATION_FILES.md](NOTIFICATION_FILES.md)

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ **Immediate email on task creation** (if due date matches schedule)
2. ✅ **Hourly scheduler checks** show in logs
3. ✅ **Emails arrive in zeniakqfoo@gmail.com**
4. ✅ **Scheduler auto-starts after reboot**
5. ✅ **No more manual intervention needed!**

---

## 🎉 You're Done!

Your notification system is now:
- ✅ Fully automated
- ✅ Sending emails correctly
- ✅ Running 24/7 in background
- ✅ Starts automatically on boot

**Enjoy your automated task reminders!** 🚀

