# Email Notification Setup Guide

This guide will help you configure email notifications for the Task Manager system.

## Overview

The system can send email notifications for:
- **Task Reminders**: Sent 7/3/1 days before due date (or custom schedule)
- **Due Date Changes**: Sent to collaborators when task due date is modified
- **General Notifications**: Other task-related updates

## Prerequisites

You need an email account that supports SMTP. The easiest options are:
1. **Gmail** (Recommended for development)
2. **SendGrid** (Recommended for production)
3. **AWS SES** (For AWS users)
4. **Outlook/Office365**

## Setup Instructions

### Option 1: Gmail (Development/Testing)

1. **Enable 2-Factor Authentication**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification

2. **Generate App Password**
   - Visit [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Configure Environment Variables**
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   FROM_EMAIL=your_email@gmail.com
   FROM_NAME=Task Manager Notifications
   FRONTEND_URL=http://localhost:3000
   ```

### Option 2: SendGrid (Production)

1. **Create SendGrid Account**
   - Sign up at [SendGrid](https://sendgrid.com/)
   - Verify your sender email/domain

2. **Generate API Key**
   - Go to Settings → API Keys
   - Create new API key with "Mail Send" permissions

3. **Configure Environment Variables**
   ```bash
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=your_sendgrid_api_key
   FROM_EMAIL=verified@yourdomain.com
   FROM_NAME=Task Manager
   FRONTEND_URL=https://your-domain.com
   ```

### Option 3: AWS SES

1. **Setup AWS SES**
   - Enable SES in AWS Console
   - Verify your email/domain
   - Request production access (to send to any email)

2. **Create SMTP Credentials**
   - Go to SES → SMTP Settings
   - Create SMTP credentials

3. **Configure Environment Variables**
   ```bash
   SMTP_HOST=email-smtp.us-east-1.amazonaws.com
   SMTP_PORT=587
   SMTP_USER=your_ses_smtp_username
   SMTP_PASSWORD=your_ses_smtp_password
   FROM_EMAIL=verified@yourdomain.com
   FROM_NAME=Task Manager
   FRONTEND_URL=https://your-domain.com
   ```

## Testing Email Service

### 1. Test Standalone Email Service

Run the email service test:

```bash
cd src/microservices/notifications
python email_service.py
```

This sends a test email. Check your console for success/failure messages.

### 2. Test with Task Creation

Create a task due in 3 days:

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Email Task",
    "description": "Testing email notifications",
    "due_date": "2025-01-18",
    "priority": "High",
    "owner_id": "your_user_id"
  }'
```

Check:
- ✅ In-app notification appears
- ✅ Email received (check spam folder)

### 3. Test Due Date Change Notification

Update the task due date:

```bash
curl -X PUT http://localhost:8080/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{
    "due_date": "2025-01-20"
  }'
```

Collaborators should receive email notifications.

## Email Templates

The system includes beautiful HTML email templates:

### Reminder Email
```
⏰ Task Reminder
─────────────────
Task: [Task Title]
Due: [Date]
Priority: [Badge]

This task is due in X day(s).

[View Task Details Button]
```

### Due Date Change Email
```
📅 Due Date Changed
─────────────────
Task: [Task Title]
Previous: [Old Date] ❌
New: [New Date] ✅

[View Task Details Button]
```

## Troubleshooting

### Email Not Sending

**Check Environment Variables**
```python
import os
print(f"SMTP_USER: {os.getenv('SMTP_USER')}")
print(f"SMTP_PASSWORD: {'*' * 10 if os.getenv('SMTP_PASSWORD') else 'NOT SET'}")
```

**Check Logs**
Look for these messages in task service console:
- ✅ `"Email notification sent to user@email.com"`
- ❌ `"Failed to send email notification: [error]"`

**Common Issues:**
1. **"Authentication failed"**
   - Gmail: Use App Password, not regular password
   - SendGrid: Ensure API key has Mail Send permission

2. **"Email not received"**
   - Check spam folder
   - Verify sender email is verified (SendGrid/SES)
   - Check SMTP_HOST and SMTP_PORT are correct

3. **"Email service not available"**
   - Ensure `email_service.py` is in the notifications folder
   - Check Python import errors in console

### Disable Email Notifications

If you want to disable emails temporarily:

1. **Remove SMTP credentials from .env**
   ```bash
   # Comment out or remove:
   # SMTP_USER=
   # SMTP_PASSWORD=
   ```

2. **Or disable in UI**
   - When creating/editing task
   - Uncheck "Email Notifications"

## User Preferences

Users can control notification channels per task:

```
✅ In-App Notifications  ← Always shown in inbox
✅ Email Notifications   ← Sent to user's email
```

These preferences are stored in the `notification_preferences` table.

## Production Recommendations

1. **Use SendGrid or AWS SES** (not Gmail)
2. **Set up SPF/DKIM/DMARC** for your domain
3. **Monitor email delivery rates**
4. **Implement bounce handling**
5. **Add unsubscribe link** (for compliance)
6. **Use environment-specific FROM_NAME**
   - Dev: "Task Manager (Dev)"
   - Prod: "Task Manager"

## Email Delivery Status

Currently, the system logs email success/failure to console. For production, consider:

- Storing delivery status in database
- Setting up webhooks for bounce/complaint handling
- Monitoring email delivery metrics

## Security Notes

- ⚠️ **Never commit credentials to git**
- ⚠️ **Use App Passwords for Gmail (never regular password)**
- ⚠️ **Rotate API keys regularly**
- ⚠️ **Use environment variables for all sensitive data**

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review console logs for error messages
3. Test with `email_service.py` standalone
4. Verify SMTP credentials are correct

---

**Quick Start Checklist:**
- [ ] Choose SMTP provider (Gmail for dev)
- [ ] Generate credentials (App Password for Gmail)
- [ ] Add to `.env` file
- [ ] Test with `python email_service.py`
- [ ] Create test task with due date
- [ ] Check email received
- [ ] Configure user notification preferences
