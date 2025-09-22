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
  />

  <!-- Task Form Modal for editing -->
  <TaskFormModal 
    :task="editingTask"
    :isOpen="showEditModal" 
    @close="closeEditModal" 
    @save="handleTaskUpdated"
  />

  <div>
    <!-- Tasks Section -->
    <a-card 
      style="height: 500px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 12px;">
          <span>All Tasks</span>
          <a-space size="small">
            <a-button 
              size="small" 
              :type="sortBy.startsWith('dueDate') ? 'primary' : 'default'"
              @click="toggleDueDateSort"
            >
              Due Date {{ sortBy === 'dueDate-asc' ? '↑' : sortBy === 'dueDate-desc' ? '↓' : '↑' }}
            </a-button>
            <a-button 
              size="small" 
              :type="sortBy.startsWith('priority') ? 'primary' : 'default'"
              @click="togglePrioritySort"
            >
              Priority {{ sortBy === 'priority-asc' ? '↑' : sortBy === 'priority-desc' ? '↓' : '↑' }}
            </a-button>
          </a-space>
        </div>
      </template>
      <template #extra>
        <a-button type="primary" size="small" :icon="h(PlusOutlined)" @click="showTaskModal = true">
          Create Task
        </a-button>
      </template>
      <a-list
        :data-source="allTasks"
        :loading="isLoading"
        style="height: 400px; overflow-y: auto;"
      >
        <template #renderItem="{ item }">
          <a-list-item>
            <TaskCard
              :task="item"
              @view-details="handleTaskClick"
            />
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<script>
import { ref, computed, onMounted, h } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { notification } from 'ant-design-vue'
import { useTheme } from '../../composables/useTheme.js'
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
    const { isDarkMode } = useTheme()

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
      status: normalizeStatus(row.status)
    })

    // Handle task saved from TaskFormModal
    const handleTaskSaved = (taskData) => {
      // Transform the API response to match frontend format
      const mappedTask = {
        id: taskData.task_id || taskData.id,
        title: taskData.title,
        dueDate: taskData.due_date || taskData.dueDate,
        status: taskData.status
      }
      
      // Add the new task to the tasks list
      tasks.value.unshift(mappedTask)
      
      // Show success notification
      notification.success({
        message: 'Task created successfully',
        description: `"${mappedTask.title}" has been added to your task list.`,
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
        
        // Transform the API response to match TaskDetailModal expected format
        const taskDetails = {
          id: apiTasks[0].id,
          title: apiTasks[0].title,
          dueDate: apiTasks[0].dueDate,
          status: apiTasks[0].status,
          description: apiTasks[0].description || 'No description available',
          priority: apiTasks[0].priority || 'Medium',
          assignee: apiTasks[0].assignee || 'Unassigned',
          project: apiTasks[0].project || 'Default Project',
          activities: apiTasks[0].activities || [],
          comments: apiTasks[0].comments || []
        }
        
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
    const handleTaskUpdated = (updatedTask) => {
      const index = tasks.value.findIndex(t => t.id === updatedTask.id)
      if (index !== -1) {
        tasks.value[index] = {
          ...tasks.value[index],
          ...updatedTask
        }
        notification.success({
          message: 'Task updated successfully',
          description: `"${updatedTask.title}" has been updated.`,
          placement: 'topRight',
          duration: 3
        })
      }
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

    // All tasks computed property with sorting
    const allTasks = computed(() => {
      const sortedTasks = [...tasks.value]
      
      if (sortBy.value === 'dueDate-asc') {
        return sortedTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(a.dueDate) - new Date(b.dueDate)
        })
      } else if (sortBy.value === 'dueDate-desc') {
        return sortedTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(b.dueDate) - new Date(a.dueDate)
        })
      } else if (sortBy.value === 'priority-asc') {
        const priorityOrder = { 'High': 0, 'Medium': 1, 'Low': 2, 'Lowest': 3 }
        return sortedTasks.sort((a, b) => {
          const aPriority = priorityOrder[a.priority] ?? 4
          const bPriority = priorityOrder[b.priority] ?? 4
          return aPriority - bPriority
        })
      } else if (sortBy.value === 'priority-desc') {
        const priorityOrder = { 'High': 0, 'Medium': 1, 'Low': 2, 'Lowest': 3 }
        return sortedTasks.sort((a, b) => {
          const aPriority = priorityOrder[a.priority] ?? 4
          const bPriority = priorityOrder[b.priority] ?? 4
          return bPriority - aPriority
        })
      }
      
      return sortedTasks
    })

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

    const currentUser = computed(() => {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user) : null
    })

    onMounted(async () => {
      isLoading.value = true
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const ownerId = import.meta.env.VITE_TASK_OWNER_ID || ''
        const url = ownerId
          ? `${baseUrl}/tasks?owner_id=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/tasks`
        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
        tasks.value = apiTasks.map(t => ({
          id: t.id,
          title: t.title,
          dueDate: t.dueDate || null,
          status: normalizeStatus(t.status)
        }))
      } catch (e) {
        console.error('Failed to load tasks via service:', e)
        tasks.value = []
      } finally {
        isLoading.value = false
      }
    })

    return {
      h,
      allTasks,
      isLoading,
      selectedTask,
      showDetailModal,
      isLoadingTaskDetails,
      showTaskModal,
      showEditModal,
      editingTask,
      sortBy,
      toggleDueDateSort,
      togglePrioritySort,
      handleTaskSaved,
      handleTaskClick,
      closeDetailModal,
      handleTaskEdit,
      closeEditModal,
      handleTaskUpdated,
      handleTaskDeleted
    }
  }
}
</script>

<style scoped>
/* Custom scrollbar for better UX */
:deep(.ant-list) {
  scrollbar-width: thin;
  scrollbar-color: #d9d9d9 transparent;
}

:deep(.ant-list::-webkit-scrollbar) {
  width: 6px;
}

:deep(.ant-list::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.ant-list::-webkit-scrollbar-thumb) {
  background-color: #d9d9d9;
  border-radius: 3px;
}

:deep(.ant-list::-webkit-scrollbar-thumb:hover) {
  background-color: #bfbfbf;
}

/* Enhanced card hover effects */
:deep(.ant-card) {
  transition: all 0.2s ease;
}

:deep(.ant-card:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Better spacing for nested cards */
:deep(.ant-card .ant-card) {
  margin-bottom: 8px;
}

:deep(.ant-card .ant-card:last-child) {
  margin-bottom: 0;
}
</style>