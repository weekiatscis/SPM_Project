# Final Debugging Steps - Comment Notifications Not Appearing

## 🚨 MOST IMPORTANT: Ensure Services are Running Updated Code

**THE #1 REASON notifications don't work:** Docker containers are running old code.

### Run these commands NOW:

```bash
cd /Users/zenia/Documents/GitHub/SPM_Project

# 1. Stop all services
docker compose down

# 2. Rebuild with NO CACHE (critical!)
docker compose build --no-cache task-service project-service notification-service

# 3. Start services
docker compose up -d

# 4. Verify all services are running
docker compose ps
```

All services should show status "Up".

---

## 🔍 Quick Test: Are Notifications Being Created?

### Step 1: Get Your User ID

1. Log into your app
2. Open browser console (F12)
3. Type:
```javascript
// Get your user ID
const authStore = window.$pinia?.state?.value?.auth;
console.log('My User ID:', authStore?.user?.user_id);
```

### Step 2: Check Database Directly

Go to Supabase SQL Editor and run:

```sql
-- Replace 'YOUR_USER_ID' with the actual user ID from Step 1
SELECT
    id,
    title,
    message,
    type,
    created_at,
    is_read
FROM notifications
WHERE user_id = 'YOUR_USER_ID'
ORDER BY created_at DESC
LIMIT 10;
```

**If you see notifications:** The backend is working! Problem is frontend not fetching.
**If you see NO notifications:** Backend isn't creating them. Check Docker logs.

---

## 🧪 Step-by-Step Test

### Test 1: Post a Comment and Watch Logs

1. **Open two terminal windows:**

**Terminal 1:**
```bash
docker compose logs -f task-service | grep -i "comment"
```

**Terminal 2:**
```bash
docker compose logs -f notification-service
```

2. **Post a comment on any task** (as any user who has access)

3. **Look for these messages in Terminal 1 (task-service):**
```
Notifying X stakeholder(s) about new comment on task...
✅ Sent comment notification to stakeholder ...
✅ Task comment notifications sent for task...
```

**✅ If you see these messages:** Backend is creating notifications!
**❌ If you DON'T see these messages:** Services not rebuilt. Go back to top and rebuild.

---

## 🖥️ Frontend Debugging

### Check 1: Is Frontend Fetching Notifications?

In browser console:

```javascript
// Check if notifications are in the store
const notifStore = window.$pinia?.state?.value?.notifications;
console.log('===FRONTEND CHECK===');
console.log('Store:', notifStore);
console.log('Notifications:', notifStore?.notifications);
console.log('Count:', notifStore?.notifications?.length || 0);
console.log('Unread:', notifStore?.unreadCount || 0);
```

### Check 2: Manually Fetch Notifications

```javascript
// Get user ID
const authStore = window.$pinia?.state?.value?.auth;
const userId = authStore?.user?.user_id;

// Manually fetch
fetch(`http://localhost:8084/notifications?user_id=${userId}`)
  .then(r => r.json())
  .then(data => {
    console.log('===MANUAL FETCH RESULT===');
    console.log('Total:', data.notifications?.length || 0);
    console.log('Notifications:', data.notifications);
  })
  .catch(e => console.error('Fetch failed:', e));
```

**✅ If fetch returns notifications:** Database has them, frontend needs to refresh
**❌ If fetch returns empty:** Backend not creating notifications

---

## 🛠️ Common Fixes

### Fix #1: Manual Refresh

Click the **🔄 Refresh** button in the notification dropdown.

Notifications should appear if they exist in the database.

### Fix #2: Check Network Tab

1. Open browser DevTools (F12)
2. Go to Network tab
3. Open notification dropdown
4. Look for request to `http://localhost:8084/notifications?user_id=...`
5. Click on it and check:
   - Status: Should be 200
   - Response: Should have `notifications` array

**If request is not made:** Frontend code issue
**If request returns empty:** Backend not creating notifications
**If request fails:** Notification service not running

### Fix #3: Verify Notification Service is Running

```bash
curl http://localhost:8084/notifications?user_id=YOUR_USER_ID
```

Replace `YOUR_USER_ID` with actual ID.

**Should return JSON with notifications array.**
**If "connection refused":** Notification service not running. Run `docker compose up -d notification-service`

---

## 📊 Expected Results

When everything is working:

1. **Post a comment** → Within 5 seconds:
   - ✅ Docker logs show "✅ Sent comment notification"
   - ✅ Database has new notification
   - ✅ Frontend shows notification (may need refresh if WebSocket not set up)

2. **Who gets notified:**
   - ✅ Task owner (if they didn't post the comment)
   - ✅ All collaborators (except the one who posted)
   - ❌ Person who posted comment (should NOT be notified)

3. **Notification content:**
   - Title: "New comment on 'Task Name'"
   - Message: "John Doe commented: Comment text here"
   - Type: "task_comment"
   - Has "View Task" button

---

## 🆘 Still Not Working?

If after following ALL steps above notifications still don't appear, please provide:

### 1. Docker Logs
```bash
docker compose logs task-service | tail -50 > task-service-logs.txt
docker compose logs notification-service | tail -50 > notification-service-logs.txt
```

### 2. Database Query Results
Run this SQL:
```sql
SELECT COUNT(*) as total,
       COUNT(CASE WHEN type = 'task_comment' THEN 1 END) as comment_count,
       MAX(created_at) as most_recent
FROM notifications
WHERE created_at >= CURRENT_DATE - INTERVAL '1 day';
```

### 3. Browser Console Output
After clicking notification dropdown, copy all console logs.

### 4. Task Info
```sql
-- Replace with your test task ID
SELECT task_id, title, owner_id, collaborators
FROM task
WHERE task_id = 'YOUR_TASK_ID';
```

---

## ✅ Checklist

Before asking for help, verify:

- [ ] You're on branch `fix/comment-notifications`
- [ ] Latest commit is `d48a5dd`
- [ ] Ran `docker compose down`
- [ ] Ran `docker compose build --no-cache`
- [ ] Ran `docker compose up -d`
- [ ] All services show "Up" in `docker compose ps`
- [ ] Posted a comment while watching Docker logs
- [ ] Checked database has notifications
- [ ] Checked browser Network tab shows fetch request
- [ ] Tried clicking Refresh button in notification dropdown
- [ ] Checked browser console for errors

If ALL boxes are checked and it still doesn't work, there may be a deeper issue that needs live debugging.

---

## 🎯 Quick Summary

**Problem:** Notifications not appearing in frontend inbox
**Most Common Cause:** Docker running old code
**Solution:** Rebuild containers with `--no-cache`
**Verification:** Check Docker logs when posting comment
**Fallback:** Manual refresh button works if notifications exist in DB

Good luck! 🚀
