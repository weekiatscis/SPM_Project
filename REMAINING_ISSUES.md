# Remaining Issues and Solutions

## ✅ Fixed in Latest Commit (d48a5dd)

1. **Due date reminders for collaborators** - Now ALL stakeholders receive reminders
2. **Comment notifications** - Now properly sends notifications with full task data

---

## ⚠️ Remaining Issues

### Issue #1: In-App Notifications Require Manual Refresh
**Problem:** Notifications don't appear in real-time; users have to refresh the page.

**Root Cause:** The frontend is not connected to WebSocket for real-time updates.

**Solution Options:**

#### Option A: Connect Frontend to WebSocket (Recommended)
The notification service already supports WebSocket (Socket.IO), but the frontend isn't connected.

**Frontend changes needed:**
1. Install socket.io-client in your Vue app
2. Connect to notification service WebSocket
3. Listen for 'new_notification' events
4. Update notification store when events received

**Example code for Vue:**
```javascript
// In your notification store or main.js
import { io } from 'socket.io-client'

const socket = io('http://localhost:8084')

// Join user's notification room
socket.emit('join_notifications', { user_id: currentUserId })

// Listen for new notifications
socket.on('new_notification', (notification) => {
  // Add to notifications store
  notificationStore.addNotification(notification)
})
```

#### Option B: Polling (Quick Fix, Not Ideal)
Set up automatic polling every 5-10 seconds to fetch new notifications.

**Frontend changes:**
```javascript
// In notification store
setInterval(() => {
  if (user.isLoggedIn) {
    notificationStore.fetchNotifications(user.id)
  }
}, 5000) // Poll every 5 seconds
```

**Recommendation:** Use Option A for better performance and real-time experience.

---

### Issue #2: UI Shows Collaborators as Assignees
**Problem:** When viewing a task, both Staff 1 and Staff 2 see themselves as "assignee" even though only Staff 1 is the actual assignee.

**Root Cause:** Frontend is confusing `owner_id` with being in the `collaborators` array.

**Backend Data Structure (CORRECT):**
```json
{
  "id": "task-123",
  "title": "Complete report",
  "owner_id": "staff-1-id",     // ← The ASSIGNEE
  "collaborators": [             // ← People HELPING with the task
    "manager-id",
    "staff-2-id"
  ]
}
```

**Frontend Issue:**
The Vue component (likely TaskCard.vue or TaskDetailModal.vue) is probably checking:
```javascript
// WRONG - This makes everyone think they're the assignee
if (task.owner_id === currentUserId || task.collaborators.includes(currentUserId)) {
  showAsAssignee() // ❌ Wrong!
}
```

**Should be:**
```javascript
// CORRECT - Only owner is assignee
const isAssignee = task.owner_id === currentUserId
const isCollaborator = task.collaborators.includes(currentUserId)

// Then display appropriately:
if (isAssignee) {
  badge = "Assignee"
} else if (isCollaborator) {
  badge = "Collaborator"
}
```

**Files to check and fix:**
1. `src/components/tasks/TaskCard.vue` - Task display logic
2. `src/components/tasks/TaskDetailModal.vue` - Task detail view
3. `src/components/tasks/TaskFormModal.vue` - Edit form (already correct?)
4. `src/views/Home.vue` - Dashboard task display

**Search for:**
```bash
grep -r "Assignee" src/components/tasks/
grep -r "owner_id" src/components/tasks/
```

---

### Issue #3: Manager Not Added as Collaborator (Verification Needed)
**Current Status:** The backend code exists to auto-add manager as collaborator (lines 1046-1068 in task_service.py).

**Verification Steps:**

1. **Check if frontend sends `created_by` parameter:**
   ```bash
   # Check TaskFormModal.vue
   grep -A 5 "created_by" src/components/tasks/TaskFormModal.vue
   ```

   Should see:
   ```javascript
   created_by: authStore.user?.user_id  // ← Must be sent!
   ```

2. **Check database directly:**
   After creating a task as manager assigned to staff:
   ```sql
   SELECT task_id, title, owner_id, collaborators
   FROM task
   WHERE task_id = 'your-task-id';
   ```

   Should show:
   ```
   owner_id: staff-1-id
   collaborators: ["manager-id"]  // ← Manager should be here
   ```

3. **Check Docker logs:**
   ```bash
   docker compose logs task-service | grep "Manager is creating task"
   ```

**If manager is NOT in collaborators:**
- Check if frontend sends `created_by` in the API request
- Check Docker logs for errors
- Restart services after code changes

---

## 🔧 Steps to Fix Everything

### Step 1: Restart Docker Services with Latest Code
```bash
docker compose down
docker compose build --no-cache task-service
docker compose up -d
```

### Step 2: Verify Backend Fixes are Working

**Test Due Date Notifications:**
```bash
# Check task-service logs
docker compose logs -f task-service

# Look for:
# "Will send reminders to X stakeholder(s): [user-id-1, user-id-2]"
# "✅ Successfully stored X-day notification for stakeholder..."
# "✅ Email notification sent successfully to..."
```

**Test Comment Notifications:**
```bash
# Post a comment, check logs for:
# "Notifying X stakeholder(s) about new comment on task..."
# "✅ Sent comment notification to stakeholder..."
```

### Step 3: Fix Frontend Issues

#### Fix #1: Real-time Notifications (WebSocket)
**File:** `src/stores/notifications.js` (or wherever you manage notifications)

```javascript
import { io } from 'socket.io-client'

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [],
    socket: null
  }),

  actions: {
    connectWebSocket(userId) {
      if (this.socket) return

      this.socket = io('http://localhost:8084')

      this.socket.emit('join_notifications', { user_id: userId })

      this.socket.on('new_notification', (notification) => {
        console.log('📬 New notification received:', notification)
        this.notifications.unshift(notification)
      })
    },

    disconnectWebSocket() {
      if (this.socket) {
        this.socket.disconnect()
        this.socket = null
      }
    }
  }
})
```

**Then in App.vue or main entry:**
```javascript
onMounted(() => {
  if (authStore.user?.user_id) {
    notificationStore.connectWebSocket(authStore.user.user_id)
  }
})

onBeforeUnmount(() => {
  notificationStore.disconnectWebSocket()
})
```

#### Fix #2: Assignee vs Collaborator Display
**File:** `src/components/tasks/TaskCard.vue` (example)

Find the section that determines the badge/label and update:

```vue
<template>
  <div class="task-card">
    <!-- ... -->
    <span v-if="isAssignee" class="badge badge-primary">Assignee</span>
    <span v-else-if="isCollaborator" class="badge badge-secondary">Collaborator</span>
    <!-- ... -->
  </div>
</template>

<script>
const isAssignee = computed(() => {
  return task.owner_id === authStore.user?.user_id
})

const isCollaborator = computed(() => {
  return task.collaborators?.includes(authStore.user?.user_id) && !isAssignee.value
})
</script>
```

### Step 4: Install Socket.IO Client (if not already installed)
```bash
npm install socket.io-client
```

---

## 🧪 Final Testing Checklist

After making all fixes:

- [ ] **Restart Docker services** with latest code
- [ ] **Create task** as Manager, assign to Staff 1, add Staff 2 as collaborator
- [ ] **Verify database:** Manager in collaborators array
- [ ] **Check UI:** Staff 1 sees "Assignee", Staff 2 sees "Collaborator"
- [ ] **Post comment** as Staff 2
- [ ] **Verify:** Manager and Staff 1 receive notification **without refresh**
- [ ] **Verify:** Staff 2 (commenter) does NOT receive notification
- [ ] **Check email:** Manager and Staff 1 receive email
- [ ] **Create task due in 4 days**
- [ ] **Verify:** Both owner and collaborators receive reminder email
- [ ] **Verify:** Notifications appear **without refresh**

---

## 📝 Summary

**Backend:** ✅ **FIXED** (in branch `fix/comment-notifications`)
- Due date reminders for all stakeholders
- Comment notifications for all stakeholders
- Proper collaborator data structure

**Frontend:** ⚠️ **NEEDS FIX**
1. Connect to WebSocket for real-time notifications
2. Fix assignee vs collaborator display logic
3. Verify `created_by` is sent when creating tasks

**Next Steps:**
1. Merge backend fixes to main OR continue testing in this branch
2. Fix frontend issues
3. Test end-to-end
4. Deploy

---

**Branch:** `fix/comment-notifications`
**Latest Commit:** d48a5dd
