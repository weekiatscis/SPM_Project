#!/bin/bash

echo "🔍 Checking if comment notifications are working..."
echo "=================================================="
echo ""

echo "1️⃣ Checking task-service logs for emoji debug output..."
echo "   (Looking for 🔔 NOTIFY_TASK_COMMENT CALLED)"
echo ""

# Check recent logs for the notification function being called
if docker compose logs task-service --tail=200 | grep -q "🔔 NOTIFY_TASK_COMMENT CALLED"; then
    echo "   ✅ Found notification function calls!"
    echo ""
    echo "   Last notification attempt:"
    docker compose logs task-service --tail=200 | grep -A 15 "🔔 NOTIFY_TASK_COMMENT CALLED" | tail -20
else
    echo "   ❌ No notification attempts found yet"
    echo "   👉 Try posting a comment, then run this script again"
fi

echo ""
echo "=================================================="
echo ""
echo "2️⃣ Checking for HTTP 500 errors (the old bug)..."
echo ""

if docker compose logs task-service --tail=100 | grep -q "POST /tasks/.*/comments.*500"; then
    echo "   ❌ Still seeing 500 errors - something is wrong!"
    echo "   Recent 500 errors:"
    docker compose logs task-service --tail=100 | grep "POST /tasks/.*/comments.*500"
else
    echo "   ✅ No 500 errors found - good sign!"
fi

echo ""
echo "=================================================="
echo ""
echo "3️⃣ Checking for successful comment POSTs..."
echo ""

if docker compose logs task-service --tail=100 | grep -q "POST /tasks/.*/comments.*20[01]"; then
    echo "   ✅ Comments are posting successfully!"
    docker compose logs task-service --tail=100 | grep "POST /tasks/.*/comments.*20[01]" | tail -5
else
    echo "   ⚠️  No successful comment POSTs found yet"
    echo "   👉 Try posting a comment"
fi

echo ""
echo "=================================================="
echo ""
echo "💡 TIP: To watch logs in real-time while testing:"
echo "   docker compose logs -f task-service"
echo ""
