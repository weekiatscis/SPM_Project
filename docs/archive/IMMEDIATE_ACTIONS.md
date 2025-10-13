# IMMEDIATE ACTIONS - Notification Debug

## 🚨 Critical: We Need to See the Logs

You mentioned you rebuilt Docker, but we need to verify the new code is running and see what's happening.

### Step 1: Watch Logs in Real-Time

Open a terminal and run this command:

```bash
docker compose logs -f task-service | grep -E "comment|NOTIFY|stakeholder"
```

**Leave this terminal open.**

### Step 2: Post a Comment

1. Go to any task in your browser
2. Post a comment (any text)
3. **IMMEDIATELY look at the terminal**

### Step 3: What Should You See?

If the new code is running, you should see something like:

```
🔔 Attempting to send comment notifications for task ...
   Task object keys: [...]
   Task title: ...
   Task owner_id: ...
   Task collaborators: ...
🔔 NOTIFY_TASK_COMMENT CALLED
================================================================================
📋 Task Data: {...}
```

### Step 4: Report Back

**SCENARIO A: You see the debug messages**
→ Great! The code is running. Copy ALL the log output and share it with me.

**SCENARIO B: You see NOTHING**
→ Docker wasn't rebuilt properly. Try this:
```bash
docker compose down
docker compose rm -f
docker compose build --no-cache
docker compose up -d
```

**SCENARIO C: You see old-style logs but no emoji/debug messages**
→ Container is using old image. Force rebuild:
```bash
docker compose stop task-service
docker compose rm -f task-service
docker volume prune -f
docker compose build --no-cache task-service
docker compose up -d task-service
```

---

## 🔍 Manual Database Check

While we wait, let's check if notifications ARE being created but just not showing:

### Check 1: Are ANY notifications in the database?

Run this SQL in Supabase:

```sql
SELECT
    id,
    user_id,
    title,
    message,
    type,
    created_at,
    is_read
FROM notifications
WHERE type = 'task_comment'
ORDER BY created_at DESC
LIMIT 5;
```

**Result:**
- **If you see rows:** Notifications ARE being created! It's a frontend issue.
- **If NO rows:** Backend isn't creating them.

### Check 2: What's your user ID?

In browser console:

```javascript
const user = window.$pinia.state.value.auth.user;
console.log('My User ID:', user.user_id);
console.log('My Email:', user.email);
```

Note this down.

### Check 3: Do notifications exist for YOUR user ID?

Run this SQL (replace `YOUR_USER_ID`):

```sql
SELECT
    id,
    title,
    message,
    type,
    created_at
FROM notifications
WHERE user_id = 'YOUR_USER_ID'  -- Replace with your actual user_id
  AND created_at >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY created_at DESC;
```

**Result:**
- **If you see rows:** Notifications exist! Frontend not fetching them.
- **If NO rows:** You're not getting notified (but others might be).

---

## 🎯 Issue #2: Collaborators Not Showing in Home Page Popup

This is a **separate frontend issue**. The collaborators array is being fetched correctly (I can see it in your debug output), but the popup on the home page isn't displaying them.

### Why It Works in Notification Inbox But Not Home Page:

**Notification Inbox → Task Popup:**
Likely calls the full task detail endpoint which includes collaborators.

**Home Page → Task Popup:**
Might be using cached task data that doesn't include collaborators, OR using a different endpoint that doesn't fetch all fields.

### To Fix This:

We need to check which endpoint is being called when you click a task from:
1. Notification inbox (works)
2. Home page (doesn't work)

Let me investigate the task detail modal...

---

## 📊 Expected vs Actual

### For Notifications:

**Expected:**
1. Post comment
2. See debug logs with "🔔 NOTIFY_TASK_COMMENT CALLED"
3. See "✅ SUCCESS: Notification inserted!"
4. Notification appears in inbox (may need refresh)
5. Email sent

**What You're Experiencing:**
1. Post comment ✅
2. Comment appears in task ✅
3. NO debug logs visible ❌
4. NO notifications in inbox ❌
5. NO emails ❌

**This means:** Either old code still running OR function not being called.

### For Collaborators Display:

**Expected:**
- Collaborators show in ALL task popups

**What You're Experiencing:**
- Shows in notification inbox popup ✅
- Doesn't show in home page popup ❌

**This means:** Different code paths or different data being passed.

---

## ⚡ Quick Action Plan

1. **RUN:** `docker compose logs -f task-service | grep -E "comment|NOTIFY"`
2. **POST:** A comment on any task
3. **SHARE:** The complete log output with me
4. **RUN:** The SQL queries above and share results

With this information, I can tell you EXACTLY what's wrong!

---

**Current Branch:** fix/comment-notifications
**Latest Commit:** f63db8a (with debug logging)
