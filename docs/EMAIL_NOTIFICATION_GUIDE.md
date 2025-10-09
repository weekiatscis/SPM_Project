# Email Notification System - Complete Guide

## ✅ What's Working

1. **Email Service**: Fully functional, tested and working
2. **SMTP Configuration**: Correct (`smu.spm.group5@gmail.com`)
3. **Email Delivery**: Successfully sends to `zeniakqfoo@gmail.com`
4. **Notification Preferences**: Saving correctly (Email/In-App toggles)
5. **Reminder Schedules**: Custom reminder days are saved properly

## 🔍 Root Cause of "Not Receiving Emails"

The notification system only checks when:
1. You create a task
2. You update a task
3. You manually call the API endpoint

**It does NOT continuously monitor tasks in the background.**

### Example:
- You create a task due in 7 days at 2:00 PM
- System checks: "Is today 7 days before due date?" → YES
- Email sent immediately ✅
- Tomorrow at 2:00 PM: System does NOT check again ❌
- No more notifications unless you manually trigger them

## 🚀 Solutions

### Option 1: Manual Trigger (For Testing)

Use the force send script:
```bash
python3 src/microservices/notifications/utils/force_send_email.py
```

### Option 2: Scheduled Checker (Recommended)

Run the notification scheduler in the background:
```bash
# Start the scheduler (runs every hour)
python3 src/microservices/notifications/notification_scheduler.py &

# Or use macOS launchd (runs on startup)
# Save this to ~/Library/LaunchAgents/com.spm.notifications.plist
```

### Option 3: Cron Job (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add this line to check every hour
0 * * * * cd /Users/zenia/Documents/GitHub/SPM_Project && python3 -c "import requests; requests.post('http://localhost:8080/check-all-tasks-notifications')"
```

## 📧 Email Delivery Details

### Where Emails Are Sent
Emails go to the **task owner's email in the database**, NOT your login email.

Your database user:
- Name: Zenia
- Email: `zeniakqfoo@gmail.com`
- User ID: `67de0c44-...`

### Email Appearance
- **Subject**: ⏰ Task Reminder: [Task Title]
- **Design**: Beautiful HTML with purple gradient header
- **Content**: Task details, priority badge, due date
- **Button**: "View Task Details" (links to frontend)

### If You Don't See Emails

1. **Check spam/junk folder**
2. **Check Promotions/Updates tabs** in Gmail
3. **Search for** "Task Reminder" or "Task Manager"
4. **Check the correct email**: `zeniakqfoo@gmail.com` (not `smu.spm.group5@gmail.com`)

## 🧪 Testing Guide

### Test 1: Direct Email Test
```bash
python3 test_email.py zeniakqfoo@gmail.com
```
✅ Should receive email immediately

### Test 2: Check Existing Tasks
```bash
python3 src/microservices/notifications/utils/debug_task_notifications.py
```
Shows all tasks and which ones should trigger notifications

### Test 3: Force Send for Specific Task
```bash
python3 src/microservices/notifications/utils/force_send_email.py
```
Sends email for "test email 1" task immediately

### Test 4: Create New Task Due in 7 Days
1. Create task with due date exactly 7 days from today
2. Select "Email Only" for notifications
3. Check console logs for:
   ```
   ➕ Creating notification preferences... email=True, in_app=False
   ✅ Successfully saved notification preferences
   Sending email notification to zeniakqfoo@gmail.com...
   ✅ Email notification sent successfully
   ```
4. Check your email immediately

## 🐛 Troubleshooting

### Email Not Received?

1. **Check task service is running:**
   ```bash
   curl http://localhost:8080/tasks
   ```

2. **Check task service logs:**
   Look for error messages about email sending

3. **Verify SMTP credentials:**
   ```bash
   grep SMTP_ .env
   ```
   Should show:
   - `SMTP_USER=smu.spm.group5@gmail.com`
   - `SMTP_PASSWORD=hxmceollbqlckkve` (no spaces!)

4. **Test email service directly:**
   ```bash
   python3 test_email.py YOUR_EMAIL@gmail.com
   ```

5. **Check notification preferences:**
   ```bash
   python3 debug_task_notifications.py | grep -A 5 "YOUR_TASK_NAME"
   ```

### "Email Only" Not Saving?

This IS working correctly! Check with:
```bash
python3 src/microservices/notifications/utils/debug_task_notifications.py
```

Look for: `Notification prefs: Email=True, In-App=False`

If you see both as `True`, clear your browser cache and try again.

## 📝 Important Notes

1. **Emails send to database email, not login email**
   - Login email: Used for authentication
   - Database email: Used for notifications

2. **Notifications checked at specific times**
   - Task creation/update
   - Manual API call
   - Scheduled job (if running)

3. **Reminder days must match exactly**
   - Task due in 2 days → Only sends if 2 is in reminder schedule
   - Task due in 5 days → Only sends if 5 is in reminder schedule

4. **Duplicate prevention**
   - System won't send same notification twice
   - E.g., Won't send "7-day reminder" twice for same task

## 🎯 Recommended Setup

For production use:

1. **Start task service:**
   ```bash
   cd src/microservices/tasks
   python3 task_service.py &
   ```

2. **Start notification scheduler:**
   ```bash
   python3 src/microservices/notifications/notification_scheduler.py &
   ```

3. **Verify both are running:**
   ```bash
   ps aux | grep python3 | grep -E 'task_service|notification_scheduler'
   ```

Now you'll get email notifications automatically! 🎉

## 📞 Need Help?

Check the console logs for detailed debugging information with emoji indicators:
- ✅ Success messages
- ❌ Error messages
- ⚠️ Warnings
- 📧 Email operations
- ➕ Creating records
- 📝 Updating records
