#!/bin/bash

echo "=========================================="
echo "CODE VERSION VERIFICATION"
echo "=========================================="
echo ""

echo "Current Git Branch and Commit:"
echo "-------------------------------"
git branch --show-current
git log --oneline -1
echo ""

echo "Checking task_service.py for notification features:"
echo "----------------------------------------------------"

# Check for notify_task_comment function
if grep -q "def notify_task_comment" src/microservices/tasks/task_service.py; then
    echo "✅ notify_task_comment() function EXISTS in code"
else
    echo "❌ notify_task_comment() function NOT FOUND in code"
fi

# Check if it's being called
if grep -q "notify_task_comment(" src/microservices/tasks/task_service.py; then
    echo "✅ notify_task_comment() is CALLED in code"
else
    echo "❌ notify_task_comment() is NOT called in code"
fi

# Check for stakeholder loop in due date notifications
if grep -q "for stakeholder_id in stakeholders:" src/microservices/tasks/task_service.py; then
    echo "✅ Due date notifications loop through stakeholders"
else
    echo "❌ Due date notifications do NOT loop through stakeholders"
fi

echo ""
echo "Docker Container Status:"
echo "------------------------"
docker compose ps task-service 2>/dev/null || echo "Docker services not running or docker not available"

echo ""
echo "=========================================="
echo "ACTION REQUIRED:"
echo "=========================================="
echo ""
echo "If functions exist in code but notifications still don't work:"
echo ""
echo "1. REBUILD the Docker containers to use the latest code:"
echo "   cd /Users/zenia/Documents/GitHub/SPM_Project"
echo "   docker compose down"
echo "   docker compose build --no-cache task-service notification-service"
echo "   docker compose up -d"
echo ""
echo "2. Verify services are running:"
echo "   docker compose ps"
echo ""
echo "3. Watch logs while testing:"
echo "   docker compose logs -f task-service"
echo ""
echo "4. Post a comment on a task and look for:"
echo "   - 'Notifying X stakeholder(s) about new comment'"
echo "   - '✅ Sent comment notification to stakeholder'"
echo "   - '✅ Task comment notifications sent for task'"
echo ""
echo "5. If you see errors in logs, copy them and I can help debug"
echo ""
