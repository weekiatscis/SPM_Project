#!/bin/bash

# Test script to verify task email notifications work end-to-end

echo "======================================================================"
echo "TASK EMAIL NOTIFICATION TEST"
echo "======================================================================"
echo ""

# Calculate due date (7 days from today)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DUE_DATE=$(date -v+7d +%Y-%m-%d)
else
    # Linux
    DUE_DATE=$(date -d "+7 days" +%Y-%m-%d)
fi

echo "Creating test task with:"
echo "  - Due date: $DUE_DATE (7 days from today)"
echo "  - Email notifications: ENABLED"
echo "  - In-app notifications: DISABLED"
echo ""

# Get user ID (you'll need to replace this)
echo "Enter your user_id (from debug script above):"
read USER_ID

if [ -z "$USER_ID" ]; then
    echo "❌ Error: user_id is required"
    exit 1
fi

# Create task
echo ""
echo "Creating task..."
TASK_RESPONSE=$(curl -s -X POST http://localhost:8080/tasks \
    -H "Content-Type: application/json" \
    -d "{
        \"title\": \"Email Test Task $(date +%H:%M:%S)\",
        \"description\": \"Testing email notifications\",
        \"due_date\": \"$DUE_DATE\",
        \"status\": \"Ongoing\",
        \"priority\": \"High\",
        \"owner_id\": \"$USER_ID\",
        \"reminder_days\": [7, 3, 1],
        \"email_enabled\": true,
        \"in_app_enabled\": false
    }")

echo "$TASK_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TASK_RESPONSE"

# Extract task ID
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['task']['id'])" 2>/dev/null)

if [ -z "$TASK_ID" ]; then
    echo ""
    echo "❌ Failed to create task"
    exit 1
fi

echo ""
echo "✅ Task created with ID: $TASK_ID"
echo ""
echo "======================================================================"
echo "Now check the task service logs for:"
echo "  1. ➕ Creating notification preferences... email=True, in_app=False"
echo "  2. ✅ Successfully saved notification preferences"
echo "  3. Sending email notification to YOUR_EMAIL..."
echo "  4. ✅ Email notification sent successfully"
echo ""
echo "Then check your inbox at the email in the database!"
echo "======================================================================"
