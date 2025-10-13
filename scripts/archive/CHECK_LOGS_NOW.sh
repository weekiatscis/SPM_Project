#!/bin/bash

echo "=================================================="
echo "CHECKING DOCKER LOGS FOR COMMENT NOTIFICATIONS"
echo "=================================================="
echo ""

echo "1. Checking if task-service is running..."
docker compose ps task-service
echo ""

echo "2. Last 100 lines of task-service logs:"
echo "   (Looking for comment notification debug messages)"
echo ""
docker compose logs --tail=100 task-service | grep -E "NOTIFY_TASK_COMMENT|comment|notification|stakeholder|SUCCESS|ERROR" || echo "No relevant logs found"
echo ""

echo "3. Most recent task-service logs (last 50 lines):"
echo ""
docker compose logs --tail=50 task-service
echo ""

echo "=================================================="
echo "INSTRUCTIONS:"
echo "=================================================="
echo ""
echo "If you see '🔔 NOTIFY_TASK_COMMENT CALLED' in the logs:"
echo "  ✅ The new code is running!"
echo "  → Look for '✅ SUCCESS: Notification inserted!'"
echo "  → Look for '📊 SUMMARY: Created X notification(s)'"
echo ""
echo "If you DON'T see '🔔 NOTIFY_TASK_COMMENT CALLED':"
echo "  ❌ Either:"
echo "     1. No comment was posted yet"
echo "     2. Docker wasn't rebuilt with new code"
echo ""
echo "TO TEST AGAIN:"
echo "  1. Run: docker compose logs -f task-service"
echo "  2. Post a comment on any task"
echo "  3. Watch the logs appear in real-time"
echo ""
