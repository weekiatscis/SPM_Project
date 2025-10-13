#!/bin/bash

echo "🔨 Rebuilding Docker services with the critical fix..."
echo "=================================================="
echo ""

# Stop existing containers
echo "1️⃣ Stopping existing containers..."
docker compose down

echo ""
echo "2️⃣ Rebuilding services (no cache)..."
docker compose build --no-cache task-service notification-service project-service

echo ""
echo "3️⃣ Starting all services..."
docker compose up -d

echo ""
echo "4️⃣ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Services are running!"
echo ""
echo "📋 Check service status:"
docker compose ps

echo ""
echo "=================================================="
echo "🎯 NEXT STEPS:"
echo "=================================================="
echo ""
echo "1. Open your frontend application"
echo "2. Post a comment on a task that has collaborators"
echo "3. Check terminal logs for emoji debug output:"
echo "   docker compose logs -f task-service | grep '🔔'"
echo ""
echo "4. Check your notification inbox - notifications should appear!"
echo ""
echo "5. If you want to see ALL logs in real-time:"
echo "   docker compose logs -f task-service"
echo ""
echo "=================================================="
