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
          <a-list
            :data-source="ongoingTasks"
            :loading="isLoading"
            class="task-list-scroll"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <TaskCard
                  :task="item"
                  :current-user-id="authStore.user?.user_id"
                  :is-expanded="false"
                  :has-subtasks="hasSubtasks(item.id)"
                  @view-details="handleTaskClick"
                  @toggle-expand="toggleExpand"
                />
              </a-list-item>
            </template>
            <template #empty>
              <a-empty description="No ongoing tasks" />
            </template>
          </a-list>
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
          <a-list
            :data-source="completedTasks"
            :loading="isLoading"
            class="task-list-scroll"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <TaskCard
                  :task="item"
                  :current-user-id="authStore.user?.user_id"
                  :is-expanded="false"
                  :has-subtasks="hasSubtasks(item.id)"
                  @view-details="handleTaskClick"
                  @toggle-expand="toggleExpand"
                />
              </a-list-item>
            </template>
            <template #empty>
              <a-empty description="No completed tasks" />
            </template>
          </a-list>
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

    // All tasks computed property with sorting (subtasks excluded from list)
    const allTasks = computed(() => {
      // Filter out subtasks - only show parent tasks in the list
      const parentTasks = tasks.value.filter(t => !t.parent_task_id && !t.isSubtask)
      
      // Apply sorting
      let sorted = [...parentTasks]
      if (sortBy.value === 'dueDate-asc') {
        sorted = parentTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(a.dueDate) - new Date(b.dueDate)
        })
      } else if (sortBy.value === 'dueDate-desc') {
        sorted = parentTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(b.dueDate) - new Date(a.dueDate)
        })
      } else if (sortBy.value === 'priority-asc') {
        // Sort by priority: lower numbers (1) = lower priority, higher numbers (10) = higher priority
        // Ascending = low to high (1 to 10)
        sorted = parentTasks.sort((a, b) => {
          const aPriority = typeof a.priority === 'number' ? a.priority : (parseInt(a.priority) || 5)
          const bPriority = typeof b.priority === 'number' ? b.priority : (parseInt(b.priority) || 5)
          return aPriority - bPriority
        })
      } else if (sortBy.value === 'priority-desc') {
        // Descending = high to low (10 to 1)
        sorted = parentTasks.sort((a, b) => {
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
/* Container */
.task-list-container {
  width: 100%;
}

/* Main Card Styling */
.task-list-card {
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(229, 231, 235, 0.8) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden !important;
  min-height: 700px;
}

.task-list-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04) !important;
  border-color: rgba(24, 144, 255, 0.2) !important;
}

/* Header Styling */
.task-list-header {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  padding: 12px;
}

.task-list-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  letter-spacing: -0.02em;
}

/* Sort Buttons */
.sort-buttons {
  display: flex;
  gap: 12px;
}

.sort-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px !important;
  height: 38px !important;
  border-radius: 10px !important;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sort-button .sort-label {
  font-size: 14px;
}

.sort-button .sort-arrow {
  font-size: 16px;
  font-weight: 600;
}

.sort-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

/* Create Task Button */
.create-task-button {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 8px 20px !important;
  height: 38px !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.25) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.create-task-button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.35) !important;
}

.create-task-button:active {
  transform: translateY(0) !important;
}

:deep(.create-task-button .anticon) {
  display: inline-flex !important;
  align-items: center !important;
  font-size: 16px !important;
}

/* Tabs Styling */
:deep(.ant-tabs) {
  margin-top: 0px;
}

:deep(.ant-tabs-nav) {
  margin-bottom: 20px !important;
  padding: 0 4px;
}

:deep(.ant-tabs-tab) {
  padding: 12px 20px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}

:deep(.ant-tabs-tab:hover) {
  background: rgba(24, 144, 255, 0.05) !important;
}

:deep(.ant-tabs-tab-active) {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08), rgba(64, 169, 255, 0.08)) !important;
}

:deep(.ant-tabs-ink-bar) {
  height: 3px !important;
  border-radius: 2px !important;
  background: linear-gradient(90deg, #1890ff, #40a9ff) !important;
}

/* Badge Styling */
:deep(.ant-badge) {
  margin-left: 8px;
}

:deep(.ant-badge-count) {
  font-weight: 600;
  font-size: 12px;
  padding: 0 8px;
  height: 20px;
  line-height: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Scrollable List */
.task-list-scroll {
  height: 520px;
  overflow-y: auto;
  padding: 4px;
  margin: -4px;
}

/* Custom Scrollbar */
.task-list-scroll {
  scrollbar-width: thin;
  scrollbar-color: #d1d5db #f3f4f6;
}

.task-list-scroll::-webkit-scrollbar {
  width: 8px;
}

.task-list-scroll::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

.task-list-scroll::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.task-list-scroll::-webkit-scrollbar-thumb:hover {
  background-color: #9ca3af;
}

/* List Items */
:deep(.ant-list-item) {
  padding: 12px 0 !important;
  border-bottom: none !important;
}

/* Empty State */
:deep(.ant-empty) {
  padding: 60px 20px;
}

:deep(.ant-empty-description) {
  font-size: 15px;
  color: #6b7280;
  font-weight: 500;
}

/* Card Body Padding */
:deep(.ant-card-body) {
  padding: 24px !important;
}

:deep(.ant-card-head) {
  padding: 20px 24px !important;
  border-bottom: 1px solid #f3f4f6 !important;
}

/* Dark Mode Support */
:global(.dark) .task-list-card {
  background-color: rgba(31, 41, 55, 1) !important;
  border-color: rgba(55, 65, 81, 0.8) !important;
}

:global(.dark) .task-list-card:hover {
  border-color: rgba(24, 144, 255, 0.3) !important;
}

:global(.dark) .task-list-title {
  color: #f9fafb;
}

:global(.dark) .task-list-scroll::-webkit-scrollbar-track {
  background: #1f2937;
}

:global(.dark) .task-list-scroll::-webkit-scrollbar-thumb {
  background-color: #4b5563;
}

:global(.dark) .task-list-scroll::-webkit-scrollbar-thumb:hover {
  background-color: #6b7280;
}

:global(.dark) :deep(.ant-card-head) {
  border-bottom-color: #374151 !important;
}

/* Responsive Design */
@media (max-width: 768px) {
  .task-list-card {
    min-height: 600px;
  }
  
  .task-list-scroll {
    height: 450px;
  }
  
  .task-list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .task-list-title {
    font-size: 18px;
  }
  
  .sort-button,
  .create-task-button {
    height: 36px !important;
    font-size: 13px !important;
  }
}
</style>