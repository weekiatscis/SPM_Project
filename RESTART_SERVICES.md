# How to Restart Docker Services with Updated Code

## Current Situation
You are on the `fix/comment-notifications` branch with updated code for:
- ✅ Collaborator display fixes
- ✅ Comment notification system
- ✅ Due date change notifications for all stakeholders

The Docker services need to be restarted to pick up these changes.

---

## Option 1: Rebuild and Restart (Recommended)

This ensures the Docker containers are built with the latest code from your branch.

### Step 1: Stop all running services
```bash
docker compose down
```

### Step 2: Rebuild the services with the new code
```bash
docker compose build --no-cache
```

The `--no-cache` flag ensures a fresh build without using cached layers.

### Step 3: Start the services
```bash
docker compose up -d
```

The `-d` flag runs the services in detached mode (background).

### Step 4: Verify services are running
```bash
docker compose ps
```

You should see all services with status "Up":
- rabbitmq
- notification-service
- task-service (port 8080) ← **Contains your fixes**
- project-service (port 8082) ← **Contains your fixes**
- user-service (port 8081)
- auth-service (port 8086)

### Step 5: Check logs to ensure no errors
```bash
# Check task-service logs
docker compose logs task-service

# Check project-service logs
docker compose logs project-service

# Check notification-service logs
docker compose logs notification-service
```

---

## Option 2: Quick Restart (Faster, but may not pick up all changes)

If you just want to restart without rebuilding:

```bash
docker compose restart task-service project-service notification-service
```

**Warning:** This only restarts the containers. If there are dependency changes or Dockerfile updates, you should use Option 1 instead.

---

## Option 3: Rebuild Specific Services Only

If you only want to rebuild the services we modified:

```bash
# Stop services
docker compose stop task-service project-service

# Rebuild them
docker compose build --no-cache task-service project-service

# Start them
docker compose up -d task-service project-service
```

---

## Verification Steps

After restarting, verify the fixes are working:

### 1. Check Task Service is Running
```bash
curl http://localhost:8080/health
```
Expected response: `{"status": "healthy", "service": "task-service"}`

### 2. Check Project Service is Running
```bash
curl http://localhost:8082/health
```
Expected response: Should return projects (or empty array if no projects)

### 3. Check Notification Service is Running
```bash
curl http://localhost:8084/health
```

---

## Testing the Fixes

Once services are running, test:

1. **Collaborator Display:**
   - Create a task as a manager and assign to staff
   - Verify manager appears in collaborators list
   - Edit the task
   - Verify collaborators are shown in the edit form

2. **Comment Notifications:**
   - Post a comment on a task
   - Check that all stakeholders (except commenter) receive notifications
   - Verify notification appears within 5 seconds

3. **Due Date Change Notifications:**
   - Change a task's due date
   - Verify all stakeholders (except person who changed it) receive notifications

---

## Troubleshooting

### Services won't start
```bash
# Check what's using the ports
lsof -i :8080  # Task service
lsof -i :8082  # Project service
lsof -i :8084  # Notification service

# Or view all Docker logs
docker compose logs -f
```

### Database connection errors
Check your `.env` file has:
```
SUPABASE_URL=your_url
SUPABASE_SERVICE_ROLE_KEY=your_key
```

### RabbitMQ errors
```bash
# Check RabbitMQ is healthy
docker compose logs rabbitmq

# Access RabbitMQ management UI
# Open: http://localhost:15672
# Login: admin / admin123
```

### Port already in use
```bash
# Stop all services
docker compose down

# Remove all containers
docker compose rm -f

# Start fresh
docker compose up -d --build
```

---

## Quick Commands Reference

```bash
# View all running containers
docker compose ps

# View logs (follow mode)
docker compose logs -f

# View logs for specific service
docker compose logs -f task-service

# Stop all services
docker compose down

# Start all services
docker compose up -d

# Rebuild and restart everything
docker compose down && docker compose build --no-cache && docker compose up -d

# Restart specific service
docker compose restart task-service
```

---

## After Restarting

Once services are running with the updated code:

1. ✅ Manager auto-collaboration should work
2. ✅ Collaborators should display correctly when editing tasks
3. ✅ Comment notifications should be sent to all stakeholders
4. ✅ Due date change notifications should be sent to all stakeholders

**Note:** The UI issue (collaborators showing as assignees) is a **frontend issue** and needs to be fixed in the Vue components, not the backend.

---

**Branch:** `fix/comment-notifications`
**Services to restart:** task-service, project-service, notification-service
