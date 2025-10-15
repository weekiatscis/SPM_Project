<template>
  <div class="manager-dashboard">
    <!-- Page Header -->
    <a-page-header
      title="Manager Dashboard"
      sub-title="Monitor your team's task progress"
      style="background: white; margin-bottom: 24px; border-radius: 8px;"
    >
      <template #extra>
        <a-space>
          <a-tooltip title="Last updated">
            <span style="color: #666; font-size: 12px;">
              {{ lastUpdateText }}
            </span>
          </a-tooltip>
          <a-button @click="handleRefresh" :loading="isLoading">
            <template #icon><ReloadOutlined /></template>
            Refresh
          </a-button>
          <a-button @click="handleExport" :disabled="filteredTasks.length === 0">
            <template #icon><ExportOutlined /></template>
            Export CSV
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- Error Alert -->
    <a-alert
      v-if="error"
      type="error"
      :message="error"
      closable
      @close="error = null"
      style="margin-bottom: 24px;"
    />

    <!-- Metrics Row -->
    <TeamMetrics :tasks="filteredTasks" />

    <!-- Tabs for Table/Charts View -->
    <a-card style="margin-top: 24px; border-radius: 8px;">
      <a-tabs v-model:activeKey="activeTab" type="card" size="large">
        <a-tab-pane key="table" tab="Table View">
          <template #tab>
            <span>
              <TableOutlined />
              Table View
            </span>
          </template>
          
          <!-- Main Content Layout -->
          <a-row :gutter="24" style="margin-top: 16px;">
            <!-- Filters Sidebar (Left) -->
            <a-col :xs="24" :sm="24" :md="6" :lg="5">
              <TaskFilters
                v-model:filters="filters"
                :subordinates="subordinates"
                :is-loading="isLoading"
                @apply="applyFilters"
                @reset="resetFilters"
              />
            </a-col>

            <!-- Tasks Table (Right) -->
            <a-col :xs="24" :sm="24" :md="18" :lg="19">
              <TeamTasksTable
                :tasks="filteredTasks"
                :is-loading="isLoading"
                :subordinates="subordinates"
                @refresh="handleRefresh"
                @view-task="handleViewTask"
              />
            </a-col>
          </a-row>
        </a-tab-pane>

        <a-tab-pane key="charts" tab="Charts View">
          <template #tab>
            <span>
              <BarChartOutlined />
              Charts View
            </span>
          </template>
          
          <!-- Charts View -->
          <div style="margin-top: 16px;">
            <TeamChartsView
              :tasks="filteredTasks"
              :is-loading="isLoading"
              :subordinates="subordinates"
            />
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- Task Detail Modal -->
    <TaskDetailModal
      v-if="selectedTask"
      :is-open="showTaskDetail"
      :task="selectedTask"
      :access-info="taskAccessInfo"
      @close="showTaskDetail = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { notification } from 'ant-design-vue'
import { 
  ReloadOutlined, 
  ExportOutlined, 
  TableOutlined, 
  BarChartOutlined 
} from '@ant-design/icons-vue'
import TeamMetrics from '../components/manager/TeamMetrics.vue'
import TaskFilters from '../components/manager/TaskFilters.vue'
import TeamTasksTable from '../components/manager/TeamTasksTable.vue'
import TeamChartsView from '../components/manager/TeamChartsView.vue'
import TaskDetailModal from '../components/tasks/TaskDetailModal.vue'

const authStore = useAuthStore()

// State
const tasks = ref([])
const subordinates = ref([])
const isLoading = ref(false)
const error = ref(null)
const lastFetchTime = ref(null)
const refreshInterval = ref(null)
const showTaskDetail = ref(false)
const selectedTask = ref(null)
const taskAccessInfo = ref(null)
const activeTab = ref('table') // Default to table view

// Filters
const filters = ref({
  status: null,
  assignees: [],
  dateRange: null,
  priority: null,
  searchText: ''
})

// Service URLs
const TASK_SERVICE_URL = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
const USER_SERVICE_URL = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'

// Debug watchers
watch(showTaskDetail, (newVal) => {
  console.log('showTaskDetail changed to:', newVal)
})

watch(selectedTask, (newVal) => {
  console.log('selectedTask changed to:', newVal)
})

// Computed properties
const lastUpdateText = computed(() => {
  if (!lastFetchTime.value) return 'Never'
  const now = new Date()
  const diff = Math.floor((now - lastFetchTime.value) / 1000)
  
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`
  return lastFetchTime.value.toLocaleTimeString()
})

const filteredTasks = computed(() => {
  let result = [...tasks.value]
  
  // Filter by status
  if (filters.value.status) {
    result = result.filter(t => t.status === filters.value.status)
  }
  
  // Filter by assignees
  if (filters.value.assignees && filters.value.assignees.length > 0) {
    result = result.filter(t => filters.value.assignees.includes(t.assigneeId))
  }
  
  // Filter by date range
  if (filters.value.dateRange && filters.value.dateRange.length === 2) {
    const [start, end] = filters.value.dateRange
    result = result.filter(t => {
      if (!t.dueDate) return false
      const dueDate = new Date(t.dueDate)
      const startDate = new Date(start)
      const endDate = new Date(end)
      
      // Normalize dates to compare at day level
      const dueDateOnly = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate())
      const startDateOnly = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate())
      const endDateOnly = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate())
      
      const isInRange = dueDateOnly >= startDateOnly && dueDateOnly <= endDateOnly
      
      // If date range ends yesterday or earlier (overdue filter), exclude completed tasks
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const endDateEndOfDay = new Date(endDateOnly)
      endDateEndOfDay.setHours(23, 59, 59, 999)
      
      if (endDateEndOfDay < today) {
        // This is likely an overdue filter - exclude completed tasks
        return isInRange && t.status !== 'Completed'
      }
      
      return isInRange
    })
  }
  
  // Filter by priority
  if (filters.value.priority) {
    result = result.filter(t => t.priority === filters.value.priority)
  }
  
  // Search filter
  if (filters.value.searchText) {
    const search = filters.value.searchText.toLowerCase()
    result = result.filter(t =>
      t.title?.toLowerCase().includes(search) ||
      t.assigneeName?.toLowerCase().includes(search) ||
      t.description?.toLowerCase().includes(search)
    )
  }
  
  return result
})

// Methods
const fetchSubordinates = async () => {
  const userId = authStore.user?.user_id
  if (!userId) {
    throw new Error('User ID not available')
  }
  
  const response = await fetch(`${USER_SERVICE_URL}/users/${userId}/subordinates`)
  if (!response.ok) {
    throw new Error('Failed to fetch subordinates')
  }
  
  const data = await response.json()
  return data.subordinates || []
}

const fetchTeamTasks = async () => {
  isLoading.value = true
  error.value = null
  
  try {
    // 1. Get subordinates
    const subs = await fetchSubordinates()
    subordinates.value = subs
    
    if (subs.length === 0) {
      tasks.value = []
      notification.info({
        message: 'No Team Members',
        description: 'You currently have no subordinates assigned to you.',
        placement: 'topRight'
      })
      return
    }
    
    // 2. Fetch tasks for each subordinate
    const taskPromises = subs.map(async (sub) => {
      try {
        const res = await fetch(`${TASK_SERVICE_URL}/tasks?owner_id=${sub.user_id}`)
        if (!res.ok) {
          console.warn(`Failed to fetch tasks for ${sub.name}`)
          return []
        }
        const data = await res.json()
        return (data.tasks || []).map(task => ({
          ...task,
          assigneeName: sub.name,
          assigneeRole: sub.role,
          assigneeId: sub.user_id,
          assigneeDepartment: sub.department
        }))
      } catch (err) {
        console.error(`Error fetching tasks for ${sub.name}:`, err)
        return []
      }
    })
    
    const results = await Promise.all(taskPromises)
    tasks.value = results.flat()
    lastFetchTime.value = new Date()
    
  } catch (err) {
    error.value = err.message
    notification.error({
      message: 'Failed to Load Team Tasks',
      description: err.message || 'An unexpected error occurred. Please try again.',
      placement: 'topRight',
      duration: 5
    })
  } finally {
    isLoading.value = false
  }
}

const handleRefresh = () => {
  fetchTeamTasks()
}

const handleExport = () => {
  try {
    const headers = ['Task Title', 'Assignee', 'Role', 'Due Date', 'Status', 'Priority', 'Description']
    const rows = filteredTasks.value.map(t => [
      t.title || '',
      t.assigneeName || '',
      t.assigneeRole || '',
      t.dueDate || 'No due date',
      t.status || '',
      t.priority || '',
      (t.description || '').replace(/"/g, '""') // Escape quotes
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const timestamp = new Date().toISOString().split('T')[0]
    link.href = URL.createObjectURL(blob)
    link.download = `team-tasks-${timestamp}.csv`
    link.click()
    
    notification.success({
      message: 'Export Successful',
      description: `Exported ${filteredTasks.value.length} tasks to CSV.`,
      placement: 'topRight',
      duration: 3
    })
  } catch (err) {
    notification.error({
      message: 'Export Failed',
      description: err.message || 'Failed to export tasks.',
      placement: 'topRight'
    })
  }
}

const applyFilters = () => {
  // Filters are reactive, so this is mainly for UI feedback
  notification.info({
    message: 'Filters Applied',
    description: `Showing ${filteredTasks.value.length} of ${tasks.value.length} tasks.`,
    placement: 'topRight',
    duration: 2
  })
}

const resetFilters = () => {
  filters.value = {
    status: null,
    assignees: [],
    dateRange: null,
    priority: null,
    searchText: ''
  }
  
  notification.info({
    message: 'Filters Reset',
    description: `Showing all ${tasks.value.length} tasks.`,
    placement: 'topRight',
    duration: 2
  })
}

const handleViewTask = async (task) => {
  console.log('handleViewTask called with task:', task)
  selectedTask.value = task
  
  // Fetch access info for the selected task
  try {
    const userId = authStore.user?.user_id
    console.log('Fetching access info for task:', task.id, 'user:', userId)
    const response = await fetch(
      `${TASK_SERVICE_URL}/tasks/${task.id}/access?user_id=${userId}`
    )
    if (response.ok) {
      taskAccessInfo.value = await response.json()
      console.log('Access info fetched:', taskAccessInfo.value)
    } else {
      console.warn('Access info fetch failed, using defaults')
      taskAccessInfo.value = {
        can_view: true,
        can_comment: true,
        can_edit: false,
        access_type: 'viewer'
      }
    }
  } catch (err) {
    console.warn('Failed to fetch access info:', err)
    taskAccessInfo.value = {
      can_view: true,
      can_comment: true,
      can_edit: false,
      access_type: 'viewer'
    }
  }
  
  console.log('Opening modal, showTaskDetail set to true')
  showTaskDetail.value = true
}

const handleTaskUpdated = (updatedTask) => {
  // Update task in the list
  const index = tasks.value.findIndex(t => t.id === updatedTask.id)
  if (index !== -1) {
    tasks.value[index] = { ...tasks.value[index], ...updatedTask }
  }
  
  notification.success({
    message: 'Task Updated',
    description: 'The task has been updated successfully.',
    placement: 'topRight',
    duration: 2
  })
}

// Auto-refresh every 5 minutes
const startAutoRefresh = () => {
  refreshInterval.value = setInterval(() => {
    console.log('Auto-refreshing team tasks...')
    fetchTeamTasks()
  }, 5 * 60 * 1000) // 5 minutes
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// Lifecycle hooks
onMounted(() => {
  // Check if user has required role
  const userRole = authStore.user?.role
  if (!['Manager', 'Director'].includes(userRole)) {
    notification.error({
      message: 'Access Denied',
      description: 'You do not have permission to access this page.',
      placement: 'topRight',
      duration: 5
    })
    return
  }
  
  fetchTeamTasks()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.manager-dashboard {
  max-width: 1800px;
  margin: 0 auto;
  padding: 24px;
  background: transparent;
  min-height: 100vh;
}

:deep(.ant-tabs-card > .ant-tabs-nav .ant-tabs-tab) {
  background: #fafafa;
  border: 1px solid #d9d9d9;
  transition: all 0.3s;
}

:deep(.ant-tabs-card > .ant-tabs-nav .ant-tabs-tab-active) {
  background: white;
  border-bottom-color: white;
}

:deep(.ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:hover) {
  color: #1890ff;
}

:deep(.ant-tabs-card > .ant-tabs-content) {
  margin-top: -16px;
}

@media (max-width: 768px) {
  .manager-dashboard {
    padding: 12px;
  }
  
  :deep(.ant-tabs-tab) {
    font-size: 12px;
    padding: 4px 8px;
  }
}
</style>
