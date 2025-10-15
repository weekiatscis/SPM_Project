# Conflict Resolution Cheat Sheet

## Understanding Conflict Markers

When you see a conflict, it looks like this:

```
<<<<<<< HEAD (your fix/comment-notifications branch)
your code here
=======
main's code here
>>>>>>> main
```

## Resolution Strategy: KEEP BOTH

Since main has new features and you have fixes, you usually want to **KEEP BOTH**.

---

## Example 1: Import Statements

### CONFLICT:
```python
<<<<<<< HEAD
from datetime import datetime, timezone, timedelta
import requests
=======
from datetime import datetime, timezone
import requests
import asyncio
>>>>>>> main
```

### RESOLUTION (keep both):
```python
from datetime import datetime, timezone, timedelta
import requests
import asyncio
```

**Why**: Your branch needs `timedelta`, main added `asyncio`. Keep both!

---

## Example 2: Function Added in Both Branches

### CONFLICT:
```python
<<<<<<< HEAD
def notify_project_comment(data):
    # Your implementation
    send_notification(data)
    return True
=======
def send_realtime_update(data):
    # Main's new function
    socketio.emit('update', data)
    return True
>>>>>>> main
```

### RESOLUTION (keep both functions):
```python
def notify_project_comment(data):
    # Your implementation
    send_notification(data)
    return True

def send_realtime_update(data):
    # Main's new function
    socketio.emit('update', data)
    return True
```

**Why**: These are two different functions. Keep both!

---

## Example 3: Same Function Modified Differently

### CONFLICT:
```python
<<<<<<< HEAD
def create_task(task_data):
    # Your version with notification fix
    task = db.create(task_data)
    notify_stakeholders(task)  # You added this
    return task
=======
def create_task(task_data):
    # Main's version with validation
    validate_task_data(task_data)  # Main added this
    task = db.create(task_data)
    return task
>>>>>>> main
```

### RESOLUTION (combine both improvements):
```python
def create_task(task_data):
    # Combined: validation + notifications
    validate_task_data(task_data)  # Keep main's validation
    task = db.create(task_data)
    notify_stakeholders(task)  # Keep your notification
    return task
```

**Why**: Both improvements are valuable. Combine them!

---

## Example 4: Vue Template Conflicts

### CONFLICT:
```vue
<<<<<<< HEAD
<button
  v-if="notification.project_id"
  @click="handleViewProject(notification)"
>
  View Project →
</button>
=======
<button
  v-if="notification.task_id"
  @click="handleViewTask(notification)"
  class="action-btn"
>
  View Task →
</button>
>>>>>>> main
```

### RESOLUTION (keep both buttons):
```vue
<button
  v-if="notification.task_id"
  @click="handleViewTask(notification)"
  class="action-btn"
>
  View Task →
</button>
<button
  v-if="notification.project_id"
  @click="handleViewProject(notification)"
  class="action-btn"
>
  View Project →
</button>
```

**Why**: You added project navigation, main had task navigation. Keep both!

---

## Example 5: CSS/Style Conflicts

### CONFLICT:
```css
<<<<<<< HEAD
.notification-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}
=======
.notification-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  background: white;
  border-radius: 4px;
}
>>>>>>> main
```

### RESOLUTION (merge styles):
```css
.notification-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  background: white;
  border-radius: 4px;
}
```

**Why**: Both added different properties. Combine them!

---

## Step-by-Step Conflict Resolution Process

1. **Open the conflicted file** in your editor
2. **Search for** `<<<<<<<` to find conflicts
3. **Read both versions** carefully
4. **Decide**:
   - Is this a new feature in main? → Keep it
   - Is this your fix? → Keep it
   - Are both needed? → Combine intelligently
5. **Edit the file** to keep what's needed
6. **Remove** the markers (`<<<<<<<`, `=======`, `>>>>>>>`)
7. **Save** the file
8. **Mark as resolved**: `git add <filename>`
9. **Repeat** for all conflicted files
10. **Commit**: `git commit` (after ALL files resolved)

---

## Common Patterns to Watch For

### Pattern 1: You added a field to a dictionary
```python
# Your version
data = {
    "user_id": user_id,
    "project_id": project_id,  # You added this
    "title": title
}

# Main's version  
data = {
    "user_id": user_id,
    "title": title,
    "priority": "high"  # Main added this
}

# RESOLUTION: Include both new fields
data = {
    "user_id": user_id,
    "project_id": project_id,  # Keep your addition
    "title": title,
    "priority": "high"  # Keep main's addition
}
```

### Pattern 2: You modified a query, main added a new query
**RESOLUTION**: Keep both queries

### Pattern 3: Same line modified differently
**RESOLUTION**: Understand the intent of both changes and combine

---

## Tools to Help

### See what changed in YOUR branch:
```bash
git diff main HEAD -- <filename>
```

### See what changed in MAIN:
```bash
git diff HEAD main -- <filename>
```

### See the conflict in detail:
```bash
git diff --name-only --diff-filter=U
```

### List all conflicted files:
```bash
git status | grep "both modified"
```

---

## Red Flags 🚩

**DON'T**:
- ❌ Delete entire functions without understanding what they do
- ❌ Choose one side blindly
- ❌ Remove imports that you don't recognize
- ❌ Delete new features from main

**DO**:
- ✅ Read both versions carefully
- ✅ Understand what each change does
- ✅ Keep both when possible
- ✅ Test after resolving
- ✅ Ask for help if unsure

---

## After Resolving All Conflicts

```bash
# Check that no conflicts remain
git status

# Should see "All conflicts fixed but you are still merging"
# If so, commit the merge:
git commit

# Git will open an editor with a default message like:
# "Merge branch 'main' into fix/comment-notifications"
# Save and close to complete the merge
```

---

## Testing After Merge

Before pushing, test:

1. **Backend services start**: `docker-compose up -d`
2. **No errors in logs**: `docker-compose logs -f`
3. **Notifications work**: Create a task, add a comment
4. **New features work**: Test anything that was in main
5. **No duplicates**: Verify notification system works correctly

---

## Remember

> When in doubt, KEEP IT! It's easier to remove something later than to figure out what was accidentally deleted.

**The goal**: Preserve ALL functionality - both new features AND your fixes!

