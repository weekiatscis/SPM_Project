# 🔧 Email Notifications & Scheduler Setup Guide

## 📋 Summary of Issues Fixed

### Issue 1: Emails Not Sending on Task Creation ❌→✅

**Problem:** When creating tasks due in 5 days with reminder schedule [1,3,4,5,6], no emails were sent immediately.

**Root Cause:**
1. Task service running in Docker didn't have email_service.py
2. SMTP credentials weren't passed to Docker container
3. Python print statements buffered (logs not visible)

**Fix Applied:**
1. ✅ Updated `docker-compose.yml` to pass SMTP environment variables
2. ✅ Updated `Dockerfile` to copy `email_service.py` into container
3. ✅ Rebuilt Docker container with `docker-compose up -d --build task-service`

**Current Status:** Email service is now available in Docker, but you need to verify it's working by:

```bash
# Create a test task due in 5 days with schedule [1,3,4,5,6]
python3 src/microservices/notifications/utils/test_create_task_with_email.py

# Check if you received email at zeniakqfoo@gmail.com
```

---

## 🤖 Auto-Start Notification Scheduler (Issue 2 Solution)

### Problem
You have to manually run `python3 src/microservices/notifications/notification_scheduler.py` daily.

### Solution: macOS LaunchAgent (Auto-starts on boot)

Create this file:

**~/Library/LaunchAgents/com.spm.notification_scheduler.plist**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.spm.notification_scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/zenia/Documents/GitHub/SPM_Project/src/microservices/notifications/notification_scheduler.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/zenia/Documents/GitHub/SPM_Project</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/zenia/Documents/GitHub/SPM_Project/logs/notification_scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/zenia/Documents/GitHub/SPM_Project/logs/notification_scheduler_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

### Setup Steps:

```bash
# 1. Create logs directory
mkdir -p ~/Documents/GitHub/SPM_Project/logs

# 2. Create the plist file
nano ~/Library/LaunchAgents/com.spm.notification_scheduler.plist
# (Paste the XML content above)

# 3. Load the agent (starts immediately and on every boot)
launchctl load ~/Library/LaunchAgents/com.spm.notification_scheduler.plist

# 4. Check if it's running
launchctl list | grep spm

# 5. Check logs
tail -f ~/Documents/GitHub/SPM_Project/logs/notification_scheduler.log
```

### Management Commands:

```bash
# Stop the scheduler
launchctl unload ~/Library/LaunchAgents/com.spm.notification_scheduler.plist

# Start the scheduler
launchctl load ~/Library/LaunchAgents/com.spm.notification_scheduler.plist

# Restart after making changes
launchctl unload ~/Library/LaunchAgents/com.spm.notification_scheduler.plist
launchctl load ~/Library/LaunchAgents/com.spm.notification_scheduler.plist

# View logs
tail -f ~/Documents/GitHub/SPM_Project/logs/notification_scheduler.log
tail -f ~/Documents/GitHub/SPM_Project/logs/notification_scheduler_error.log
```

---

## 🧪 Testing Everything

### Test 1: Manual Email Test
```bash
python3 src/microservices/notifications/utils/test_email.py zeniakqfoo@gmail.com
```
✅ Should receive email immediately

### Test 2: Create Task with 5-Day Reminder
```bash
python3 src/microservices/notifications/utils/test_create_task_with_email.py
```
✅ Should create task and send email
✅ Check zeniakqfoo@gmail.com inbox

### Test 3: Verify Scheduler is Running
```bash
# Check if process is running
launchctl list | grep spm

# Check recent activity
tail -20 ~/Documents/GitHub/SPM_Project/logs/notification_scheduler.log
```

### Test 4: Force Notification Check
```bash
# Manually trigger check for all tasks
curl -X POST http://localhost:8080/check-all-tasks-notifications
```

---

## 📊 Expected Behavior After Fix

1. **Create Task (Due in 5 days, Schedule: [1,3,4,5,6], Email Only)**
   - ✅ Task created immediately
   - ✅ Email sent immediately (because 5 is in schedule)
   - ✅ No in-app notification (because disabled)

2. **Next Day (4 days until due)**
   - ✅ Scheduler checks hourly
   - ✅ Sees task is 4 days away
   - ✅ 4 is in schedule → sends email
   - ❌ Doesn't send duplicate (checks database first)

3. **Day After (3 days until due)**
   - ✅ Sends 3-day reminder email

4. **And so on...**

---

## 🔍 Troubleshooting

### Emails Still Not Sending?

1. **Check Docker logs for errors:**
   ```bash
   docker logs spm_project-task-service-1 --tail 100
   ```

2. **Verify SMTP credentials in Docker:**
   ```bash
   docker exec spm_project-task-service-1 env | grep SMTP
   ```

3. **Test email service inside Docker:**
   ```bash
   docker exec spm_project-task-service-1 python -c "
   import sys
   sys.path.insert(0, '../notifications')
   from email_service import send_notification_email
   print('Email service available!')
   "
   ```

4. **Check if email_service.py is in container:**
   ```bash
   docker exec spm_project-task-service-1 ls -la ../notifications/
   ```

### Scheduler Not Running?

1. **Check LaunchAgent status:**
   ```bash
   launchctl list | grep spm
   ```

2. **Check logs for errors:**
   ```bash
   cat ~/Documents/GitHub/SPM_Project/logs/notification_scheduler_error.log
   ```

3. **Verify Python path:**
   ```bash
   which python3
   # Update the plist file if path is different
   ```

### Still Having Issues?

**Run the comprehensive debug script:**
```bash
python3 src/microservices/notifications/utils/debug_task_notifications.py
```

This shows:
- All users and their emails
- All tasks with due dates
- Which tasks should trigger notifications
- Current notification preferences
- What's already been sent

---

## ✅ Success Checklist

- [ ] Docker container rebuilt with email support
- [ ] SMTP environment variables in docker-compose.yml
- [ ] Test email script works
- [ ] LaunchAgent created and loaded
- [ ] Scheduler running (check with `launchctl list`)
- [ ] Created test task and received email
- [ ] Checked logs directory exists
- [ ] Verified scheduler logs show hourly checks

---

## 📝 Notes

1. **Scheduler checks every hour** - not every minute. If you want more frequent checks, edit line 22 in `notification_scheduler.py`:
   ```python
   CHECK_INTERVAL = 600  # 10 minutes instead of 3600 (1 hour)
   ```

2. **Emails go to database email** - Make sure user's email in database matches where you want to receive emails

3. **Docker must be running** - The task service runs in Docker, so Docker Desktop must be running

4. **LaunchAgent runs automatically** - It starts on boot and restarts if it crashes

---

Good luck! 🚀

