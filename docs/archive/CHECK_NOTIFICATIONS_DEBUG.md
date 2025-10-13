# Debug: Comment Notifications Not Appearing in Frontend

## Quick Diagnostic Steps

### Step 1: Check if notifications are being created in the database

Open your browser console (F12) and run this when logged in:

```javascript
// Get your user ID from the auth store
const userId = 'YOUR_USER_ID_HERE'; // Replace with actual user ID

// Check notification service
fetch(`http://localhost:8084/notifications?user_id=${userId}`)
  .then(r => r.json())
  .then(data => {
    console.log('=== NOTIFICATIONS FROM SERVICE ===');
    console.log('Total notifications:', data.notifications?.length || 0);
    console.log('Notifications:', data.notifications);

    // Filter for comment notifications
    const commentNotifs = data.notifications?.filter(n => n.type === 'task_comment' || n.type === 'project_comment');
    console.log('Comment notifications:', commentNotifs?.length || 0, commentNotifs);
  });
```

### Step 2: Check what the frontend is receiving

In browser console:

```javascript
// Check the notification store
const notifStore = window.$pinia?.state?.value?.notifications;
console.log('=== FRONTEND NOTIFICATION STORE ===');
console.log('Store:', notifStore);
console.log('Notifications:', notifStore?.notifications);
console.log('Unread count:', notifStore?.unreadCount);
```

### Step 3: Manually post a comment and watch logs

1. Open terminal and run:
```bash
docker compose logs -f task-service | grep -i "comment\|notification"
```

2. In another terminal:
```bash
docker compose logs -f notification-service
```

3. Post a comment on a task

4. Look for these messages in task-service logs:
```
Notifying X stakeholder(s) about new comment on task...
✅ Sent comment notification to stakeholder ...
✅ Task comment notifications sent for task...
```

5. Look for this in notification-service logs:
```
Sent real-time notification to user...
```

---

## Common Issues and Solutions

### Issue 1: Notifications created in DB but not showing in frontend

**Symptoms:**
- Database has notifications
- Fetch endpoint returns notifications
- Frontend shows "0 notifications"

**Causes:**
1. Frontend not fetching correctly
2. User ID mismatch
3. Notification store not updating

**Debug:**
```javascript
// In browser console
const authStore = window.$pinia?.state?.value?.auth;
const notifStore = window.$pinia?.state?.value?.notifications;

console.log('Auth User ID:', authStore?.user?.user_id);
console.log('Fetching notifications for:', authStore?.user?.user_id);

// Manually trigger fetch
fetch(`http://localhost:8084/notifications?user_id=${authStore?.user?.user_id}`)
  .then(r => r.json())
  .then(data => console.log('Manual fetch result:', data))
  .catch(e => console.error('Fetch error:', e));
```

**Solution:**
- Click the "🔄 Refresh" button in the notification dropdown
- Check browser console for errors
- Verify user_id matches between auth and notification tables

---

### Issue 2: Notifications not being created at all

**Symptoms:**
- Post comment
- No logs in Docker
- Database has no new notifications

**Cause:** Docker containers running old code

**Solution:**
```bash
docker compose down
docker compose build --no-cache task-service project-service
docker compose up -d
docker compose logs -f task-service
```

---

### Issue 3: Getting "Total: 0" but database has notifications

**Symptoms:**
- Direct database query shows notifications exist
- Endpoint returns empty array
- User is logged in

**Debug SQL Query:**
```sql
-- Check notifications table directly
SELECT id, user_id, title, message, type, created_at, is_read
FROM notifications
WHERE user_id = 'YOUR_USER_ID_HERE'
ORDER BY created_at DESC
LIMIT 10;

-- Check if user_id format matches
SELECT user_id FROM "user" LIMIT 5;
SELECT DISTINCT user_id FROM notifications LIMIT 5;
```

**Possible Causes:**
1. User ID mismatch (UUID format vs string)
2. Notifications created for different user_id
3. Database connection issue

---

### Issue 4: Collaborators not receiving notifications

**Symptoms:**
- Owner receives notification
- Collaborators don't receive notification

**Debug:**
Check task collaborators:
```sql
SELECT task_id, title, owner_id, collaborators
FROM task
WHERE task_id = 'YOUR_TASK_ID_HERE';
```

Should show:
```
owner_id: "abc-123"
collaborators: ["xyz-456", "def-789"]  -- JSON array
```

Check if notifications were created for all stakeholders:
```sql
SELECT user_id, title, message, type, created_at
FROM notifications
WHERE task_id = 'YOUR_TASK_ID_HERE'
  AND type = 'task_comment'
ORDER BY created_at DESC;
```

Should see one notification per stakeholder.

---

## Step-by-Step Testing Procedure

### 1. Verify Backend is Running Updated Code

```bash
cd /Users/zenia/Documents/GitHub/SPM_Project

# Check current branch
git branch --show-current  # Should show: fix/comment-notifications

# Check latest commit
git log --oneline -1  # Should show: d48a5dd

# Rebuild services
docker compose down
docker compose build --no-cache task-service project-service notification-service
docker compose up -d

# Verify services are running
docker compose ps
```

### 2. Create Test Scenario

1. **As Manager:**
   - Create a task due in 4 days
   - Assign to Staff 1 (they become owner)
   - Add Staff 2 as collaborator
   - Note the task ID

2. **Verify Task Data:**
```sql
SELECT task_id, title, owner_id, collaborators
FROM task
WHERE task_id = 'YOUR_TASK_ID';
```

Expected:
- `owner_id`: Staff 1's user_id
- `collaborators`: `["manager_id", "staff_2_id"]` (JSON array)

### 3. Test Comment Notification

1. **Watch Logs:**
```bash
docker compose logs -f task-service notification-service
```

2. **As Staff 2, post a comment:**
   - Comment text: "Test comment"
   - Submit

3. **Check task-service logs for:**
```
Notifying 2 stakeholder(s) about new comment on task abc-123
✅ Sent comment notification to stakeholder (Manager ID)
✅ Sent comment notification to stakeholder (Staff 1 ID)
✅ Task comment notifications sent for task abc-123
```

4. **Check database:**
```sql
SELECT user_id, title, message, type, created_at
FROM notifications
WHERE task_id = 'YOUR_TASK_ID'
  AND type = 'task_comment'
ORDER BY created_at DESC
LIMIT 5;
```

Should show 2 notifications (one for Manager, one for Staff 1).

### 4. Check Frontend

1. **As Manager, open notification dropdown**
   - Should show notification about Staff 2's comment
   - Without needing to refresh!

2. **As Staff 1, open notification dropdown**
   - Should show notification about Staff 2's comment

3. **As Staff 2, open notification dropdown**
   - Should NOT show notification (they posted it)

### 5. If Notifications Don't Appear

**Option A: Check Browser Console**
```javascript
// See if there are any JavaScript errors
// Check network tab for failed requests
// Check if fetch is returning data
```

**Option B: Manual Refresh**
- Click the "🔄 Refresh" button in notification dropdown
- Check if notifications appear after refresh

**Option C: Check Notification Store**
```javascript
// In browser console
const notifStore = window.$pinia?.state?.value?.notifications;
console.log('Notifications in store:', notifStore?.notifications);
```

---

## Quick Fixes

### Fix 1: Force refresh notifications

```javascript
// In browser console, manually trigger a refresh
const userId = 'YOUR_USER_ID';
fetch(`http://localhost:8084/notifications?user_id=${userId}`)
  .then(r => r.json())
  .then(data => console.log('Notifications:', data.notifications))
```

### Fix 2: Check if WebSocket is connected

```javascript
// The frontend should connect to WebSocket for real-time updates
// Check if socket connection exists
console.log('WebSocket status:', window.socket || 'Not connected');
```

Note: Currently the frontend requires manual refresh because WebSocket might not be fully set up.

### Fix 3: Rebuild and restart everything

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Expected Behavior

✅ **When working correctly:**

1. Staff 2 posts comment
2. Within 5 seconds:
   - Manager sees notification (without refresh)
   - Staff 1 sees notification (without refresh)
   - Staff 2 does NOT see notification
3. Notifications show:
   - Title: "New comment on 'Task Name'"
   - Message: "Staff 2 Name commented: Test comment"
   - Time: "Just now"
   - View Task button works

---

## Next Steps if Still Not Working

If after all these steps notifications still don't appear:

1. **Copy and paste:**
   - Docker logs from task-service
   - Database query results
   - Browser console errors
   - Network tab showing the API request/response

2. **Provide:**
   - User IDs of Manager, Staff 1, Staff 2
   - Task ID being tested
   - Screenshot of notification dropdown showing "0 notifications"

I'll help debug based on that information!
