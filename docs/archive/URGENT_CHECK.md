# URGENT: Check if Notifications Are in Database

## Run this SQL query in Supabase NOW:

```sql
-- Check the most recent notifications
SELECT
    id,
    user_id,
    title,
    message,
    type,
    task_id,
    is_read,
    created_at
FROM notifications
ORDER BY created_at DESC
LIMIT 20;
```

## What to look for:

1. **Are there ANY notifications with `type = 'task_comment'`?**
   - YES → Backend is creating them! Problem is frontend/API
   - NO → Backend notification code isn't running

2. **When was the most recent notification created?**
   - If it's old (before your recent comment), backend isn't creating new ones

3. **What's the user_id in the notifications?**
   - Does it match your logged-in user ID?
   - Check by running: `SELECT user_id, email FROM "user" LIMIT 10;`

---

## Also Check: Recent Comments

```sql
-- Find the most recent comments
SELECT
    tc.comment_id,
    tc.task_id,
    tc.user_id as commenter_id,
    tc.comment_text,
    tc.created_at,
    t.title as task_title,
    t.owner_id,
    t.collaborators
FROM task_comments tc
JOIN task t ON tc.task_id = t.task_id
ORDER BY tc.created_at DESC
LIMIT 5;
```

For the most recent comment, there should be notifications created for:
- The task owner (if they're not the commenter)
- All collaborators (except the commenter)

---

## Check if Notifications Were Created for That Comment

Take the `task_id` from the comment above and run:

```sql
-- Replace 'TASK_ID_FROM_ABOVE' with the actual task_id
SELECT
    n.id,
    n.user_id,
    n.title,
    n.message,
    n.created_at,
    u.email as recipient_email
FROM notifications n
LEFT JOIN "user" u ON n.user_id = u.user_id
WHERE n.task_id = 'TASK_ID_FROM_ABOVE'
  AND n.type = 'task_comment'
ORDER BY n.created_at DESC;
```

**Expected:** You should see 1 notification per stakeholder (owner + collaborators, minus the commenter)

**If empty:** Backend isn't creating notifications at all!

---

## Please copy and paste the results of these queries!

This will help me identify exactly where the problem is:
1. Notifications not being created at all
2. Notifications created but for wrong user_id
3. Notifications created but API not returning them
