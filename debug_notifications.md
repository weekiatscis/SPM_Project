# Debug Guide for Notification Issues

## Issue 1: No "View Project" Button in Notifications

### Root Cause Analysis:
The "View Project" button appears when `notification.project_id` exists. If it's not showing, the notifications don't have the `project_id` field.

### Debug Steps:
1. **Check Notification Data Structure:**
   ```javascript
   // In browser console, check notification objects:
   console.log('Notifications:', notifications)
   console.log('Project notifications:', notifications.filter(n => n.type.includes('project')))
   ```

2. **Verify Database Records:**
   ```sql
   -- Check if project notifications have project_id
   SELECT id, type, project_id, task_id, title, message 
   FROM notifications 
   WHERE type LIKE '%project%' 
   ORDER BY created_at DESC 
   LIMIT 10;
   ```

3. **Check Backend Logs:**
   - Look for "✅ Sent project comment notification" messages
   - Verify `project_id` is being set in notification_data

## Issue 2: @Mention Notifications Not Working

### Root Cause Analysis:
Mention notifications depend on:
1. Correct regex pattern matching
2. User name resolution
3. Notification creation with proper type

### Debug Steps:

1. **Test Mention Detection:**
   ```python
   import re
   comment_text = "Hey @john, can you review this?"
   mention_pattern = r'@([^\s]+)'
   mentions = re.findall(mention_pattern, comment_text)
   print(f"Detected mentions: {mentions}")
   ```

2. **Check User Name Resolution:**
   ```sql
   -- Verify user names in database
   SELECT user_id, name, email 
   FROM "user" 
   WHERE name ILIKE '%john%' OR name ILIKE '%jane%';
   ```

3. **Verify Notification Creation:**
   ```sql
   -- Check for mention notifications
   SELECT id, type, user_id, title, message, created_at
   FROM notifications 
   WHERE type LIKE '%mention%' 
   ORDER BY created_at DESC 
   LIMIT 10;
   ```

4. **Check Backend Logs:**
   - Look for "🔔 NOTIFY_COMMENT_MENTIONS CALLED"
   - Check for "✅ Matched mention" messages
   - Verify "✅ Mention notification created!" messages

## Quick Fixes:

### Fix 1: Ensure Project Notifications Have project_id
In `project_service.py`, verify the notification_data includes:
```python
notification_data = {
    "user_id": stakeholder_id,
    "title": f"New comment on project '{project_data['project_name']}'",
    "message": f"{commenter_name} commented: {truncated_comment}",
    "type": "project_comment",
    "task_id": None,
    "project_id": project_data.get("project_id"),  # This is crucial!
    "due_date": project_data.get("due_date"),
    "priority": "Medium",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "is_read": False
}
```

### Fix 2: Ensure Mention Notifications Have Correct Type
In `task_service.py`, verify the notification type:
```python
notification_data = {
    "user_id": mentioned_user_id,
    "title": f"You were mentioned in '{task_data['title']}'",
    "message": f"{commenter_name} mentioned you: {truncated_comment}",
    "type": "task_mention",  # Should be 'task_mention', not 'mention'
    "task_id": task_data["task_id"],
    "due_date": task_data.get("due_date"),
    "priority": "High",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "is_read": False
}
```

## Testing Steps:

1. **Test Project Notifications:**
   - Create a project comment
   - Check if notification has `project_id` field
   - Verify "View Project" button appears

2. **Test Mention Notifications:**
   - Add a comment with @username (use exact name from database)
   - Check if mention notification is created
   - Verify notification type is 'task_mention' or 'project_mention'

3. **Check Database:**
   - Run the SQL migration if not done
   - Verify all required tables exist
   - Check notification records have correct fields

## Common Issues:

1. **User Name Mismatch:** @mentions must match exact user names in database
2. **Missing project_id:** Project notifications need project_id field
3. **Wrong Notification Type:** Mentions should use 'task_mention'/'project_mention' types
4. **Database Migration:** New tables might not exist
5. **Case Sensitivity:** User name matching is case-insensitive but should match database

## Next Steps:
1. Run the database migration
2. Test with actual user names from your database
3. Check browser console for notification data
4. Verify backend logs for mention processing
