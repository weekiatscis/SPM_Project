-- SQL Script to Debug Notification Issues
-- Run these queries in your Supabase SQL editor or database tool

-- 1. Check recent notifications (all types)
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

-- 2. Check comment notifications specifically
SELECT
    id,
    user_id,
    title,
    message,
    type,
    task_id,
    created_at
FROM notifications
WHERE type IN ('task_comment', 'project_comment')
ORDER BY created_at DESC
LIMIT 10;

-- 3. Count notifications by type
SELECT
    type,
    COUNT(*) as count,
    COUNT(CASE WHEN is_read = false THEN 1 END) as unread_count
FROM notifications
GROUP BY type
ORDER BY count DESC;

-- 4. Check notifications for a specific user (REPLACE WITH YOUR USER ID)
-- Find your user ID first:
SELECT user_id, email, name, first_name, last_name, role
FROM "user"
LIMIT 5;

-- Then check notifications for that user (replace 'YOUR_USER_ID' below):
SELECT
    n.id,
    n.title,
    n.message,
    n.type,
    n.task_id,
    n.is_read,
    n.created_at,
    u.email as user_email,
    u.name as user_name
FROM notifications n
LEFT JOIN "user" u ON n.user_id = u.user_id
WHERE n.user_id = 'YOUR_USER_ID'  -- REPLACE THIS
ORDER BY n.created_at DESC
LIMIT 20;

-- 5. Check a specific task's collaborators and notifications
-- (replace 'YOUR_TASK_ID' with actual task ID)
SELECT
    t.task_id,
    t.title,
    t.owner_id,
    t.collaborators,
    jsonb_array_length(COALESCE(t.collaborators, '[]'::jsonb)) as collaborator_count
FROM task t
WHERE t.task_id = 'YOUR_TASK_ID';  -- REPLACE THIS

-- 6. Check comments on a task and who should have been notified
-- (replace 'YOUR_TASK_ID')
SELECT
    tc.comment_id,
    tc.comment_text,
    tc.user_id as commenter_id,
    tc.created_at as comment_created_at,
    u.email as commenter_email,
    u.name as commenter_name,
    t.owner_id as task_owner_id,
    t.collaborators as task_collaborators
FROM task_comments tc
JOIN task t ON tc.task_id = t.task_id
LEFT JOIN "user" u ON tc.user_id = u.user_id
WHERE tc.task_id = 'YOUR_TASK_ID'  -- REPLACE THIS
ORDER BY tc.created_at DESC;

-- 7. Find notifications that should have been created for a task comment
-- (replace 'YOUR_TASK_ID')
SELECT
    n.id,
    n.user_id,
    n.title,
    n.message,
    n.created_at,
    u.email as recipient_email,
    u.name as recipient_name
FROM notifications n
LEFT JOIN "user" u ON n.user_id = u.user_id
WHERE n.task_id = 'YOUR_TASK_ID'  -- REPLACE THIS
  AND n.type = 'task_comment'
ORDER BY n.created_at DESC;

-- 8. Check if there are ANY notifications created today
SELECT
    DATE(created_at) as notification_date,
    type,
    COUNT(*) as count
FROM notifications
WHERE created_at >= CURRENT_DATE
GROUP BY DATE(created_at), type
ORDER BY notification_date DESC, count DESC;

-- 9. Check the most recent task comments (to find a task ID to test with)
SELECT
    tc.task_id,
    tc.comment_text,
    tc.created_at,
    t.title as task_title,
    u.email as commenter_email
FROM task_comments tc
JOIN task t ON tc.task_id = t.task_id
LEFT JOIN "user" u ON tc.user_id = u.user_id
ORDER BY tc.created_at DESC
LIMIT 10;

-- 10. Diagnostic: Check if notifications were created within last 5 minutes
SELECT
    COUNT(*) as notifications_last_5min,
    COUNT(CASE WHEN type = 'task_comment' THEN 1 END) as task_comments_last_5min,
    COUNT(CASE WHEN type = 'project_comment' THEN 1 END) as project_comments_last_5min
FROM notifications
WHERE created_at >= NOW() - INTERVAL '5 minutes';

-- 11. Check recent tasks with collaborators
SELECT
    task_id,
    title,
    owner_id,
    collaborators,
    jsonb_array_length(COALESCE(collaborators, '[]'::jsonb)) as collaborator_count,
    created_at
FROM task
WHERE collaborators IS NOT NULL
  AND jsonb_array_length(collaborators) > 0
ORDER BY created_at DESC
LIMIT 10;
