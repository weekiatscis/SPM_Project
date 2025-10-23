<template>
  <!-- Task Form Modal -->
  <TaskFormModal 
    :isOpen="showTaskModal" 
    @close="showTaskModal = false" 
    @save="handleTaskSaved"
  />

  <!-- Task Detail Modal -->
  <TaskDetailModal 
    v-if="selectedTask"
    :task="selectedTask"
    :isOpen="showDetailModal"
    @close="closeDetailModal"
    @edit="handleTaskEdit"
    @delete="handleTaskDeleted"
    @open-task="handleOpenTask"
  />

  <!-- Task Form Modal for editing -->
  <TaskFormModal 
    :task="editingTask"
    :isOpen="showEditModal" 
    @close="closeEditModal" 
    @save="handleTaskUpdated"
  />

  <div class="task-list-container">
    <!-- Tasks Section -->
    <a-card 
      class="task-list-card"
    >
      <template #title>
        <div class="task-list-header">
          <h3 class="task-list-title">All Tasks</h3>
          <a-space size="middle" class="sort-buttons">
            <a-button 
              size="middle" 
              :type="sortBy.startsWith('dueDate') ? 'primary' : 'default'"
              @click="toggleDueDateSort"
              class="sort-button"
            >
              <span class="sort-label">Due Date</span>
              <span class="sort-arrow">{{ sortBy === 'dueDate-asc' ? '↑' : sortBy === 'dueDate-desc' ? '↓' : '↑' }}</span>
            </a-button>
            <a-button 
              size="middle" 
              :type="sortBy.startsWith('priority') ? 'primary' : 'default'"
              @click="togglePrioritySort"
              class="sort-button"
            >
              <span class="sort-label">Priority</span>
              <span class="sort-arrow">{{ sortBy === 'priority-asc' ? '↑' : sortBy === 'priority-desc' ? '↓' : '↑' }}</span>
            </a-button>
          </a-space>
        </div>
      </template>
      <template #extra>
        <a-button type="primary" size="middle" :icon="h(PlusOutlined)" @click="showTaskModal = true" class="create-task-button">
          Create Task
        </a-button>
      </template>

      <!-- Tabs for Ongoing and Completed -->
      <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
        <a-tab-pane key="ongoing" tab="Ongoing">
          <template #tab>
            <span>
              Ongoing
              <a-badge 
                :count="ongoingTasks.length" 
                :number-style="{ backgroundColor: '#1890ff', marginLeft: '8px' }" 
              />
            </span>
          </template>
          <a-spin :spinning="isLoading">
            <div v-if="ongoingTasks.length > 0" class="task-grid task-list-scroll">
              <TaskCard
                v-for="item in ongoingTasks"
                :key="item.id"
                :task="item"
                :current-user-id="authStore.user?.user_id"
                :is-expanded="false"
                :has-subtasks="hasSubtasks(item.id)"
                @view-details="handleTaskClick"
                @toggle-expand="toggleExpand"
              />
            </div>
            <a-empty v-else description="No ongoing tasks" class="empty-state" />
          </a-spin>
        </a-tab-pane>

        <a-tab-pane key="completed" tab="Completed">
          <template #tab>
            <span>
              Completed
              <a-badge 
                :count="completedTasks.length" 
                :number-style="{ backgroundColor: '#52c41a', marginLeft: '8px' }" 
              />
            </span>
          </template>
          <a-spin :spinning="isLoading">
            <div v-if="completedTasks.length > 0" class="task-grid task-list-scroll">
              <TaskCard
                v-for="item in completedTasks"
                :key="item.id"
                :task="item"
                :current-user-id="authStore.user?.user_id"
                :is-expanded="false"
                :has-subtasks="hasSubtasks(item.id)"
                @view-details="handleTaskClick"
                @toggle-expand="toggleExpand"
              />
            </div>
            <a-empty v-else description="No completed tasks" class="empty-state" />
          </a-spin>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { notification } from 'ant-design-vue'
import { useAuthStore } from '../../stores/auth'
import TaskFormModal from './TaskFormModal.vue'
import TaskDetailModal from './TaskDetailModal.vue'
import TaskCard from './TaskCard.vue'

export default {
  name: 'TaskList',
  components: {
    PlusOutlined,
    TaskFormModal,
    TaskDetailModal,
    TaskCard
  },
  setup() {
    const tasks = ref([])
    const isLoading = ref(false)
    const selectedTask = ref(null)
    const showDetailModal = ref(false)
    const isLoadingTaskDetails = ref(false)
    const sortBy = ref('dueDate-asc')
    const authStore = useAuthStore()
    const expandedParents = ref({})
    const activeTab = ref('ongoing')

    // Modal state for creating task
    const showTaskModal = ref(false)

    // Modal state for editing task
    const showEditModal = ref(false)
    const editingTask = ref(null)

    // Helpers: DB <-> UI mapping
    const normalizeStatus = (value) => value

    const mapFromDb = (row) => ({
      id: row.task_id ?? row.id,
      title: row.title,
      dueDate: row.due_date || null,
      status: normalizeStatus(row.status),
      assignee: row.assignee || null,
      collaborators: row.collaborators || []
    })

    // Handle task saved from TaskFormModal
    const handleTaskSaved = async (taskData) => {
      // Refetch tasks to ensure the list is up-to-date
      await fetchTasks()
      
      // Show success notification
      notification.success({
        message: 'Task created successfully',
        description: `"${taskData.title}" has been added to your task list.`,
        placement: 'topRight',
        duration: 3
      })
      
      // Close the modal
      showTaskModal.value = false
    }

    // Fetch task details from getTask microservice
    const fetchTaskDetails = async (taskId) => {
      isLoadingTaskDetails.value = true
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const url = `${baseUrl}/tasks?task_id=${encodeURIComponent(taskId)}`
        
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
        
        if (apiTasks.length === 0) {
          throw new Error('Task not found')
        }
        
        // Check user access to this task
        let accessInfo = { can_view: true, can_comment: true, can_edit: true, access_type: 'owner' }
        try {
          const currentUserId = authStore.user?.user_id
          if (currentUserId) {
            const accessUrl = `${baseUrl}/tasks/${encodeURIComponent(taskId)}/access?user_id=${encodeURIComponent(currentUserId)}`
            console.log('DEBUG: Checking access at URL:', accessUrl)
            const accessResponse = await fetch(accessUrl)
            if (accessResponse.ok) {
              accessInfo = await accessResponse.json()
              console.log('DEBUG: Access info:', accessInfo)
            } else {
              console.warn('DEBUG: Access check failed with status:', accessResponse.status)
            }
          }
        } catch (error) {
          console.warn('Failed to fetch access info, using defaults:', error)
        }
        
        // Transform the API response to match TaskDetailModal expected format
        const taskDetails = {
          id: apiTasks[0].id,
          title: apiTasks[0].title,
          dueDate: apiTasks[0].dueDate,
          completedDate: apiTasks[0].completedDate, // Add completed date
          status: apiTasks[0].status,
          description: apiTasks[0].description || 'No description available',
          priority: apiTasks[0].priority || 5, // Default to 5 for consistency
          assignee: apiTasks[0].assignee || apiTasks[0].owner_id || 'Unassigned',
          project: apiTasks[0].project || apiTasks[0].project_id || 'No Project',
          owner_id: apiTasks[0].owner_id, // Add owner_id
          created_at: apiTasks[0].created_at, // Add created_at for time taken calculation
          // Parse collaborators if it's a JSON string
          collaborators: typeof apiTasks[0].collaborators === 'string' 
            ? JSON.parse(apiTasks[0].collaborators || '[]') 
            : (apiTasks[0].collaborators || []),
          activities: apiTasks[0].activities || [],
          comments: apiTasks[0].comments || [],
          recurrence: apiTasks[0].recurrence || null, // Add recurrence field
          parent_task_id: apiTasks[0].parent_task_id || null, // Add parent_task_id for subtask detection
          isSubtask: apiTasks[0].isSubtask || false, // Add isSubtask field
          // Add access information
          access_info: accessInfo
        }
        
        console.log('DEBUG fetchTaskDetails - API response:', apiTasks[0])
        console.log('DEBUG fetchTaskDetails - completedDate from API:', apiTasks[0].completedDate)
        console.log('DEBUG fetchTaskDetails - recurrence from API:', apiTasks[0].recurrence, 'taskDetails.recurrence:', taskDetails.recurrence)
        
        return taskDetails
      } catch (error) {
        console.error('Failed to fetch task details:', error)
        notification.error({
          message: 'Failed to load task details',
          description: error.message || 'Unable to fetch task information. Please try again.',
          placement: 'topRight',
          duration: 4
        })
        throw error
      } finally {
        isLoadingTaskDetails.value = false
      }
    }

    // Handle task click
    const handleTaskClick = async (task) => {
      try {
        const taskDetails = await fetchTaskDetails(task.id)
        selectedTask.value = taskDetails
        showDetailModal.value = true
      } catch (error) {
        // Error is already handled in fetchTaskDetails
      }
    }

    // Handle modal close
    const closeDetailModal = () => {
      showDetailModal.value = false
      selectedTask.value = null
    }

    // Handle task edit
    const handleTaskEdit = (task) => {
      editingTask.value = task
      showEditModal.value = true
      showDetailModal.value = false
    }

    // Handle edit modal close
    const closeEditModal = () => {
      showEditModal.value = false
      editingTask.value = null
    }

    // Handle task updated from modal
    const handleTaskUpdated = async (updatedTask) => {
      // Refetch tasks to ensure proper filtering based on access rights
      // This is critical when a manager assigns a task to staff - the task should
      // disappear from manager's list if they're not added as collaborator
      await fetchTasks()
      
      notification.success({
        message: 'Task updated successfully',
        description: `"${updatedTask.title}" has been updated.`,
        placement: 'topRight',
        duration: 3
      })
      closeDetailModal()
      closeEditModal()
    }

    // Handle task deleted from modal
    const handleTaskDeleted = (deletedTask) => {
      tasks.value = tasks.value.filter(t => t.id !== deletedTask.id)
      notification.success({
        message: 'Task deleted successfully',
        description: `"${deletedTask.title}" has been deleted.`,
        placement: 'topRight',
        duration: 3
      })
      closeDetailModal()
    }

    // Fetch tasks from backend
    const fetchTasks = async () => {
      isLoading.value = true
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const ownerId = authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID || ''
        
        console.log('DEBUG: Loading tasks for user:', ownerId)
        
        // Use the new accessible-tasks endpoint to get all tasks user can access
        const url = ownerId
          ? `${baseUrl}/users/${encodeURIComponent(ownerId)}/accessible-tasks`
          : `${baseUrl}/tasks`
          
        console.log('DEBUG: Fetching from URL:', url)
          
        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const payload = await response.json()
        
        console.log('DEBUG: API response:', payload)
        
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
        console.log('DEBUG: Processed tasks:', apiTasks)
        
        tasks.value = apiTasks.map(t => ({
          id: t.id,
          title: t.title,
          dueDate: t.dueDate || null,
          completedDate: t.completedDate || null,
          status: normalizeStatus(t.status),
          recurrence: t.recurrence || null,
          priority: t.priority || 5,
          parent_task_id: t.parent_task_id || null,
          isSubtask: t.isSubtask || !!t.parent_task_id,
          owner_id: t.owner_id || null,
          collaborators: t.collaborators || [],
          assignee: t.assignee || null,
          created_at: t.created_at || null
        }))
        
        // Initialize all parent tasks as expanded by default
        const parentTaskIds = tasks.value
          .filter(t => !t.parent_task_id)
          .filter(t => tasks.value.some(st => st.parent_task_id === t.id))
          .map(t => t.id)
        
        parentTaskIds.forEach(id => {
          expandedParents.value[id] = true
        })
      } catch (e) {
        console.error('Failed to load tasks via service:', e)
        tasks.value = []
      } finally {
        isLoading.value = false
      }
    }

    // Handle opening a task from within the detail modal (for subtasks and parent tasks)
    const handleOpenTask = async (task) => {
      console.log('=== HANDLEOPENTASK CALLED IN TASKLIST ===')
      console.log('Received task:', task)
      try {
        // Fetch full task details
        const taskDetails = await fetchTaskDetails(task.id)
        console.log('Fetched task details:', taskDetails)
        // Update the selected task to the new one
        selectedTask.value = taskDetails
        // Ensure modal stays open
        showDetailModal.value = true
        console.log('Modal should now show task:', taskDetails.title)
      } catch (error) {
        console.error('Error in handleOpenTask:', error)
        // Error is already handled in fetchTaskDetails
      }
    }

    // All tasks computed property with sorting
    const allTasks = computed(() => {
      // Include:
      // 1. Parent tasks (tasks without parent_task_id)
      // 2. Standalone subtasks (subtasks where user doesn't have access to parent)
      // Exclude:
      // - Subtasks where the parent task is also in the user's task list (shown under parent)
      
      console.log('🔍 Computing allTasks, total tasks:', tasks.value.length)
      
      const parentTaskIds = new Set(
        tasks.value.filter(t => !t.parent_task_id).map(t => t.id)
      )
      
      console.log('📋 Parent task IDs in user\'s list:', Array.from(parentTaskIds))
      
      const visibleTasks = tasks.value.filter(t => {
        // Include all parent tasks
        if (!t.parent_task_id && !t.isSubtask) {
          console.log(`✅ Including parent task: ${t.title} (${t.id})`)
          return true
        }
        
        // Include subtasks only if their parent is NOT in the user's accessible tasks
        // This means user has access to subtask but not parent - show as standalone
        if (t.parent_task_id) {
          const hasParentAccess = parentTaskIds.has(t.parent_task_id)
          if (!hasParentAccess) {
            console.log(`✅ Including standalone subtask: ${t.title} (${t.id}) - parent ${t.parent_task_id} not accessible`)
          } else {
            console.log(`⏭️  Excluding subtask: ${t.title} (${t.id}) - parent ${t.parent_task_id} is accessible`)
          }
          return !hasParentAccess
        }
        
        return false
      })
      
      console.log('📊 Visible tasks count:', visibleTasks.length)
      
      // Apply sorting
      let sorted = [...visibleTasks]
      if (sortBy.value === 'dueDate-asc') {
        sorted = visibleTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(a.dueDate) - new Date(b.dueDate)
        })
      } else if (sortBy.value === 'dueDate-desc') {
        sorted = visibleTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(b.dueDate) - new Date(a.dueDate)
        })
      } else if (sortBy.value === 'priority-asc') {
        // Sort by priority: lower numbers (1) = lower priority, higher numbers (10) = higher priority
        // Ascending = low to high (1 to 10)
        sorted = visibleTasks.sort((a, b) => {
          const aPriority = typeof a.priority === 'number' ? a.priority : (parseInt(a.priority) || 5)
          const bPriority = typeof b.priority === 'number' ? b.priority : (parseInt(b.priority) || 5)
          return aPriority - bPriority
        })
      } else if (sortBy.value === 'priority-desc') {
        // Descending = high to low (10 to 1)
        sorted = visibleTasks.sort((a, b) => {
          const aPriority = typeof a.priority === 'number' ? a.priority : (parseInt(a.priority) || 5)
          const bPriority = typeof b.priority === 'number' ? b.priority : (parseInt(b.priority) || 5)
          return bPriority - aPriority
        })
      }
      
      return sorted
    })

    // Ongoing tasks computed property (all statuses except Completed)
    const ongoingTasks = computed(() => {
      return allTasks.value.filter(task => task.status !== 'Completed')
    })

    // Completed tasks computed property
    const completedTasks = computed(() => {
      return allTasks.value.filter(task => task.status === 'Completed')
    })

    // Handle tab change
    const handleTabChange = (key) => {
      activeTab.value = key
    }

    // Function to set sort option
    const setSortBy = (newSortBy) => {
      sortBy.value = newSortBy
    }

    // Function to toggle due date sort between ascending and descending
    const toggleDueDateSort = () => {
      if (sortBy.value === 'dueDate-asc') {
        sortBy.value = 'dueDate-desc'
      } else {
        sortBy.value = 'dueDate-asc'
      }
    }

    // Function to toggle priority sort between ascending and descending
    const togglePrioritySort = () => {
      if (sortBy.value === 'priority-asc') {
        sortBy.value = 'priority-desc'
      } else {
        sortBy.value = 'priority-asc'
      }
    }

    // Check if a task has subtasks
    const hasSubtasks = (taskId) => {
      return tasks.value.some(t => t.parent_task_id === taskId)
    }

    // Toggle expand/collapse for parent tasks
    const toggleExpand = (taskId) => {
      expandedParents.value[taskId] = !expandedParents.value[taskId]
    }

    const currentUser = computed(() => {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user) : null
    })

    // Event listener for opening task edit from notifications
    const handleOpenTaskEdit = (event) => {
      const task = event.detail
      if (task) {
        console.log('Opening task for edit from notification:', task)
        editingTask.value = task
        showEditModal.value = true
      }
    }

    onMounted(async () => {
      // Listen for custom event from NotificationDropdown
      window.addEventListener('open-task-edit', handleOpenTaskEdit)

      // Fetch tasks on mount
      await fetchTasks()
    })

    onUnmounted(() => {
      // Clean up event listener
      window.removeEventListener('open-task-edit', handleOpenTaskEdit)
    })

    return {
      h,
      PlusOutlined,
      authStore,
      allTasks,
      ongoingTasks,
      completedTasks,
      activeTab,
      isLoading,
      selectedTask,
      showDetailModal,
      isLoadingTaskDetails,
      showTaskModal,
      showEditModal,
      editingTask,
      sortBy,
      expandedParents,
      handleTabChange,
      toggleDueDateSort,
      togglePrioritySort,
      hasSubtasks,
      toggleExpand,
      handleTaskSaved,
      handleTaskClick,
      closeDetailModal,
      handleTaskEdit,
      closeEditModal,
      handleTaskUpdated,
      handleTaskDeleted,
      handleOpenTask
    }
  }
}
</script>

<style scoped>
/* ===== IMMERSIVE TASK LIST DESIGN ===== */

/* Container */
.task-list-container {
  width: 100%;
  position: relative;
}

/* Main Card - Enhanced Glassmorphism */
.task-list-card {
  border-radius: 20px !important;
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.06), 
    0 2px 12px rgba(0, 0, 0, 0.03),
    inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%) !important;
  backdrop-filter: blur(30px) saturate(150%);
  -webkit-backdrop-filter: blur(30px) saturate(150%);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  overflow: hidden !important;
  min-height: 720px;
  position: relative;
}

/* Ambient Background Effect */
.task-list-card::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 20%, rgba(0, 122, 255, 0.03) 0%, transparent 50%),
              radial-gradient(circle at 70% 80%, rgba(52, 199, 89, 0.02) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.task-list-card:hover {
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.08), 
    0 4px 16px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 1) !important;
  border-color: rgba(0, 122, 255, 0.1) !important;
  transform: translateY(-2px);
}

/* Header Styling - Premium */
.task-list-header {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  padding: 8px 4px;
  position: relative;
  z-index: 1;
}

.task-list-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #1d1d1f 0%, #3a3a3c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.03em;
  position: relative;
}

.task-list-title::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 40px;
  height: 3px;
  background: linear-gradient(90deg, #007aff 0%, transparent 100%);
  border-radius: 2px;
}

/* Sort Buttons - Elevated Design */
.sort-buttons {
  display: flex;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.sort-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px !important;
  height: 38px !important;
  border-radius: 12px !important;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: -0.01em;
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.sort-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.1) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.sort-button:hover::before {
  opacity: 1;
}

.sort-button .sort-label {
  font-size: 13px;
  letter-spacing: -0.01em;
  position: relative;
  z-index: 1;
}

.sort-button .sort-arrow {
  font-size: 16px;
  font-weight: 700;
  position: relative;
  z-index: 1;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.sort-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 122, 255, 0.2) !important;
}

.sort-button:hover .sort-arrow {
  transform: scale(1.2);
}

.sort-button:active {
  transform: translateY(0);
}

/* Active Sort Button */
.sort-button[type="primary"] {
  background: linear-gradient(135deg, #007aff 0%, #0051d5 100%) !important;
  border: 1px solid rgba(0, 122, 255, 0.3) !important;
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.sort-button[type="primary"] .sort-label,
.sort-button[type="primary"] .sort-arrow {
  color: white !important;
}

/* Create Task Button - Hero CTA */
.create-task-button {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 8px 20px !important;
  height: 38px !important;
  border-radius: 12px !important;
  font-weight: 650 !important;
  font-size: 13px !important;
  letter-spacing: -0.01em !important;
  background: linear-gradient(135deg, #007aff 0%, #0051d5 100%) !important;
  border: none !important;
  box-shadow: 
    0 4px 16px rgba(0, 122, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  position: relative;
  overflow: hidden;
  z-index: 1;
}

.create-task-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.create-task-button:hover::before {
  opacity: 1;
}

.create-task-button:hover {
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 
    0 8px 24px rgba(0, 122, 255, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.create-task-button:active {
  transform: translateY(0) scale(0.98) !important;
}

:deep(.create-task-button .anticon) {
  display: inline-flex !important;
  align-items: center !important;
  font-size: 16px !important;
}

/* Tabs - Modern Segmented Control */
:deep(.ant-tabs) {
  margin-top: 0px;
  position: relative;
  z-index: 1;
}

:deep(.ant-tabs-nav) {
  margin-bottom: 20px !important;
  padding: 4px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 14px;
  backdrop-filter: blur(10px);
}

:deep(.ant-tabs-tab) {
  padding: 10px 20px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  color: #86868b !important;
  letter-spacing: -0.01em !important;
  margin: 0 !important;
}

:deep(.ant-tabs-tab:hover) {
  background: rgba(255, 255, 255, 0.5) !important;
  color: #1d1d1f !important;
  transform: translateY(-1px);
}

:deep(.ant-tabs-tab-active) {
  background: rgba(255, 255, 255, 0.95) !important;
  color: #007aff !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

:deep(.ant-tabs-ink-bar) {
  display: none !important;
}

/* Badge - Polished */
:deep(.ant-badge) {
  margin-left: 8px;
}

:deep(.ant-badge-count) {
  font-weight: 700;
  font-size: 10px;
  padding: 0 8px;
  height: 20px;
  line-height: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  letter-spacing: 0;
}

/* Task Grid - 2 Column Layout */
.task-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 14px;
  width: 100%;
  align-content: start;
  grid-auto-rows: min-content;
}

/* Scrollable List - Smooth */
.task-list-scroll {
  height: 540px;
  overflow-y: auto;
  padding: 4px;
  margin: -4px;
  position: relative;
  z-index: 1;
}

/* Custom Scrollbar - Premium */
.task-list-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 122, 255, 0.2) transparent;
}

.task-list-scroll::-webkit-scrollbar {
  width: 8px;
}

.task-list-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.task-list-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(0, 122, 255, 0.2) 0%, rgba(0, 122, 255, 0.3) 100%);
  border-radius: 4px;
  transition: all 0.3s ease;
}

.task-list-scroll::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(0, 122, 255, 0.3) 0%, rgba(0, 122, 255, 0.4) 100%);
}

/* Empty State - Elegant */
.empty-state {
  padding: 100px 20px;
  grid-column: 1 / -1;
}

:deep(.ant-empty) {
  padding: 100px 20px;
}

:deep(.ant-empty-description) {
  font-size: 15px;
  color: #86868b;
  font-weight: 500;
  letter-spacing: -0.01em;
}

/* Card Padding - Refined */
:deep(.ant-card-body) {
  padding: 28px 32px !important;
  position: relative;
  z-index: 1;
}

:deep(.ant-card-head) {
  padding: 24px 32px !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03) !important;
  position: relative;
  z-index: 1;
}

/* Dark Mode - Premium Dark */
:global(.dark) .task-list-card {
  background: linear-gradient(135deg, rgba(28, 28, 30, 0.95) 0%, rgba(20, 20, 22, 0.95) 100%) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.4), 
    0 2px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

:global(.dark) .task-list-card::before {
  background: radial-gradient(circle at 30% 20%, rgba(0, 122, 255, 0.08) 0%, transparent 50%),
              radial-gradient(circle at 70% 80%, rgba(52, 199, 89, 0.05) 0%, transparent 50%);
}

:global(.dark) .task-list-card:hover {
  border-color: rgba(0, 122, 255, 0.2) !important;
}

:global(.dark) .task-list-title {
  background: linear-gradient(135deg, #f5f5f7 0%, #a1a1a6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:global(.dark) .sort-button {
  background: rgba(44, 44, 46, 0.8) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}

:global(.dark) .task-list-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(0, 122, 255, 0.3) 0%, rgba(0, 122, 255, 0.4) 100%);
}

:global(.dark) :deep(.ant-card-head) {
  border-bottom-color: rgba(255, 255, 255, 0.05) !important;
}

:global(.dark) :deep(.ant-tabs-nav) {
  background: rgba(255, 255, 255, 0.05);
}

:global(.dark) :deep(.ant-tabs-tab-active) {
  background: rgba(44, 44, 46, 0.95) !important;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .task-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px 14px;
    align-content: start;
    grid-auto-rows: min-content;
  }
}

@media (max-width: 768px) {
  .task-grid {
    grid-template-columns: 1fr;
    gap: 8px;
    align-content: start;
    grid-auto-rows: min-content;
  }
  
  .task-list-card {
    min-height: 620px;
    border-radius: 18px !important;
  }
  
  .task-list-scroll {
    height: 480px;
  }
  
  .task-list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .task-list-title {
    font-size: 22px;
  }
  
  .sort-button,
  .create-task-button {
    height: 36px !important;
    font-size: 12.5px !important;
  }
  
  :deep(.ant-card-body) {
    padding: 22px 24px !important;
  }
  
  :deep(.ant-card-head) {
    padding: 20px 24px !important;
  }
}
</style>