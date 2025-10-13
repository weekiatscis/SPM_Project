# Debug Comment Notifications with Enhanced Logging

## ✅ Changes Made

I've added **comprehensive debug logging** to the notification system. The logs will now show:
- When `notify_task_comment()` is called
- What task data is passed in
- How many stakeholders are found
- Each notification creation attempt
- Success/failure of database inserts
- Complete error details with stack traces

---

## 🚀 What You Need to Do Now

### Step 1: Rebuild Docker with New Logging Code

```bash
cd /Users/zenia/Documents/GitHub/SPM_Project

# Stop services
docker compose down

# Rebuild task-service with NO CACHE
docker compose build --no-cache task-service

# Start services
docker compose up -d

# Verify task-service is running
docker compose ps
```

### Step 2: Watch Logs in Real-Time

Open a terminal and run:

```bash
docker compose logs -f task-service
```

**Leave this terminal open** so you can see the logs as they happen.

### Step 3: Post a Comment

1. In your browser, navigate to a task
2. Post a comment (any text)
3. **Immediately look at the terminal** showing logs

### Step 4: What to Look For in Logs

You should see output like this:

```
================================================================================
🔔 NOTIFY_TASK_COMMENT CALLED
================================================================================
📋 Task Data: {'task_id': 'abc-123', 'title': 'My Task', 'owner_id': 'user-1', ...}
💬 Comment Text: Your comment here
👤 Commenter ID: user-2
👤 Commenter Name: John Doe

🔍 Getting stakeholders for task abc-123...
👥 Stakeholders found: ['user-1', 'user-3'] (count: 2)
✅ Notifying 2 stakeholder(s) about new comment on task abc-123

--- Processing stakeholder: user-1 ---
📝 Notification data prepared: {...}
⚙️  Notification preferences: email=True, in_app=True
💾 Inserting notification into database for user user-1...
✅ SUCCESS: Notification inserted! ID: notif-123
   Notification title: New comment on 'My Task'
   For user: user-1

--- Processing stakeholder: user-3 ---
📝 Notification data prepared: {...}
⚙️  Notification preferences: email=True, in_app=True
💾 Inserting notification into database for user user-3...
✅ SUCCESS: Notification inserted! ID: notif-124
   Notification title: New comment on 'My Task'
   For user: user-3

================================================================================
📊 SUMMARY: Created 2 notification(s) for task comment
================================================================================
```

---

## 🔍 Diagnosing Issues from Logs

### Scenario 1: You DON'T see "🔔 NOTIFY_TASK_COMMENT CALLED"

**Problem:** The function is not being called at all.

**Possible Causes:**
- Docker still has old code (didn't rebuild properly)
- Comment endpoint isn't reaching the notification code

**Solution:**
```bash
# Force rebuild with clean slate
docker compose down
docker compose rm -f task-service
docker compose build --no-cache task-service
docker compose up -d task-service
```

---

### Scenario 2: You see "❌ No stakeholders found"

**Problem:** The function runs but finds no stakeholders.

**Logs will show:**
```
❌ No stakeholders found for comment notification
   Task owner_id: abc-123
   Task collaborators: []
```

**Possible Causes:**
- Task has no owner_id
- Task has no collaborators
- Manager wasn't added as collaborator

**Solution:** Check the task in database:
```sql
SELECT task_id, title, owner_id, collaborators
FROM task
WHERE task_id = 'YOUR_TASK_ID';
```

---

### Scenario 3: You see "❌ ERROR: Missing required task fields"

**Problem:** Task data is incomplete.

**Logs will show:**
```
❌ ERROR: Missing required task fields: ['title']
Task data received: {'task_id': 'abc', 'owner_id': 'xyz'}
```

**Cause:** The `task` object fetched from database is missing fields.

**Solution:** This is a code bug. The SELECT query needs to use `*` instead of specific fields.

---

### Scenario 4: You see stakeholders but "❌ ERROR: Supabase insert returned no data!"

**Problem:** Database insert failing.

**Logs will show:**
```
💾 Inserting notification into database for user user-1...
❌ ERROR: Supabase insert returned no data!
   Response: <some error>
```

**Possible Causes:**
- Database permissions issue
- Invalid data format
- Supabase connection problem

**Solution:** Check Supabase logs and database permissions.

---

### Scenario 5: You see "✅ SUCCESS: Notification inserted!" but it's not in inbox

**Problem:** Notifications created successfully but not showing in frontend.

**This means:**
- ✅ Backend is working correctly
- ❌ Frontend fetch issue OR user_id mismatch

**Solution:**

1. **Verify notifications in database:**
```sql
SELECT id, user_id, title, message, type, created_at
FROM notifications
WHERE type = 'task_comment'
ORDER BY created_at DESC
LIMIT 10;
```

2. **Check if user_id matches your logged-in user:**
   - Note the `user_id` in the notifications
   - In browser console: `console.log(window.$pinia.state.value.auth.user.user_id)`
   - Do they match?

3. **Manually fetch notifications:**
   In browser console:
   ```javascript
   const userId = window.$pinia.state.value.auth.user.user_id;
   fetch(`http://localhost:8084/notifications?user_id=${userId}`)
     .then(r => r.json())
     .then(data => console.log('API returned:', data.notifications))
   ```

4. **If API returns notifications but inbox is empty:**
   - Click the 🔄 Refresh button
   - Check browser console for errors
   - Frontend issue with notification store

---

## 📋 Quick Checklist

After posting a comment, check logs for:

- [ ] `🔔 NOTIFY_TASK_COMMENT CALLED` appears
- [ ] Task data shows all fields (task_id, title, owner_id, collaborators)
- [ ] `👥 Stakeholders found: [...]` shows the correct user IDs
- [ ] `✅ SUCCESS: Notification inserted!` appears for each stakeholder
- [ ] `📊 SUMMARY: Created X notification(s)` shows count > 0

If ALL checkboxes pass:
- ✅ Backend is working perfectly!
- ❌ Issue is in frontend fetch/display

If ANY checkbox fails:
- ❌ Backend issue
- Copy the complete log output and share it

---

## 📊 Expected vs Actual

### Expected Behavior (Working):
1. Post comment → See "🔔 NOTIFY_TASK_COMMENT CALLED"
2. See stakeholders list with 2+ users
3. See "✅ SUCCESS" for each stakeholder
4. See summary with count > 0
5. Notifications appear in inbox (may need refresh)

### What You're Experiencing (Not Working):
1. Post comment → Comments appear in task view ✅
2. BUT → Notifications don't appear in inbox ❌

### After This Debug Session:
The logs will tell us EXACTLY where it's failing!

---

## 🆘 Next Steps

1. **Rebuild Docker** (see Step 1 above)
2. **Watch logs** while posting comment
3. **Copy the ENTIRE log output** from when you post the comment
4. **Share the logs** with me

With the detailed logs, I'll be able to identify the exact problem immediately!

---

**Commit:** f63db8a
**Branch:** fix/comment-notifications
