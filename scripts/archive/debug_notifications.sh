#!/bin/bash

echo "=========================================="
echo "NOTIFICATION DEBUG SCRIPT"
echo "=========================================="
echo ""

echo "1. Checking if Docker services are running..."
docker compose ps
echo ""

echo "2. Checking task-service logs for comment notifications..."
echo "   (Looking for '✅ Task comment notifications sent')"
docker compose logs task-service | tail -50 | grep -i "comment\|notification" || echo "No comment notification logs found"
echo ""

echo "3. Checking notification-service logs..."
docker compose logs notification-service | tail -30 || echo "No notification service logs"
echo ""

echo "4. Checking current git branch and latest commit..."
git branch --show-current
git log --oneline -1
echo ""

echo "5. Checking if task_service.py has notify_task_comment function..."
grep -n "def notify_task_comment" src/microservices/tasks/task_service.py && echo "✅ Function exists" || echo "❌ Function NOT found"
echo ""

echo "6. Checking if add_task_comment calls notify_task_comment..."
grep -A 10 "def add_task_comment" src/microservices/tasks/task_service.py | grep "notify_task_comment" && echo "✅ Function is called" || echo "❌ Function is NOT called"
echo ""

echo "=========================================="
echo "TROUBLESHOOTING STEPS:"
echo "=========================================="
echo ""
echo "If services are not running:"
echo "  docker compose up -d"
echo ""
echo "If using old code (function not found):"
echo "  docker compose down"
echo "  docker compose build --no-cache"
echo "  docker compose up -d"
echo ""
echo "To follow logs in real-time:"
echo "  docker compose logs -f task-service"
echo ""
echo "To test if notification is created in database:"
echo "  - Post a comment on a task"
echo "  - Check: SELECT * FROM notifications ORDER BY created_at DESC LIMIT 5;"
echo ""
