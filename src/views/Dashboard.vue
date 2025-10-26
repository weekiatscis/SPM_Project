<template>
  <div class="dashboard">
    <!-- Page Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="dashboard-title">{{ dashboardTitle }}</h1>
          <p class="dashboard-subtitle">{{ dashboardSubtitle }}</p>
        </div>
        <div class="header-actions">
          <div class="last-update">
            <a-tooltip title="Last updated">
              <span class="update-text">{{ lastUpdateText }}</span>
            </a-tooltip>
          </div>
          <a-space :size="12">
            <a-button @click="handleRefresh" :loading="isLoading" class="action-button">
              <template #icon><ReloadOutlined /></template>
              Refresh
            </a-button>
            <a-button @click="handleExport" :disabled="filteredTasks.length === 0" class="action-button">
              <template #icon><ExportOutlined /></template>
              Export CSV
            </a-button>
          </a-space>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <a-alert
      v-if="error"
      type="error"
      :message="error"
      closable
      @close="error = null"
      class="error-alert"
    />

    <!-- Metrics Row -->
    <TeamMetrics :tasks="tasks" />

    <!-- Tabs for Table/Charts View -->
    <a-card class="content-card">
      <a-tabs v-model:activeKey="activeTab" type="card" size="large" class="dashboard-tabs">
        <a-tab-pane key="table" tab="Table View">
          <template #tab>
            <span>
              <TableOutlined />
              Table View
            </span>
          </template>
          
          <!-- Main Content Layout -->
          <a-row :gutter="24" class="content-row">
            <!-- Filters Sidebar (Left) -->
            <a-col :xs="24" :sm="24" :md="6" :lg="5">
              <TaskFilters
                v-model:filters="filters"
                :subordinates="subordinates"
                :is-loading="isLoading"
                :user-role="userRole"
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
                :user-role="userRole"
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
          <div class="charts-container">
            <TeamChartsView
              :tasks="filteredTasks"
              :is-loading="isLoading"
              :subordinates="subordinates"
              :user-role="userRole"
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
      @open-task="handleOpenTask"
      @task-updated="handleTaskUpdated"
      @delete="handleTaskDeleted"
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

// Computed properties for role-based behavior
const userRole = computed(() => authStore.user?.role)

const isManagerOrDirector = computed(() => {
  return ['Manager', 'Director'].includes(userRole.value)
})

const dashboardTitle = computed(() => {
  switch (userRole.value) {
    case 'Manager':
    case 'Director':
      return 'Team Dashboard'
    case 'Staff':
      return 'My Dashboard'
    case 'HR':
      return 'HR Dashboard'
    default:
      return 'Dashboard'
  }
})

const dashboardSubtitle = computed(() => {
  switch (userRole.value) {
    case 'Manager':
    case 'Director':
      return "Monitor your team's task progress"
    case 'Staff':
      return 'Track your tasks and progress'
    case 'HR':
      return 'Monitor all employee tasks across the organization'
    default:
      return 'Your task overview'
  }
})

// Filters
const filters = ref({
  status: null,
  assignees: [],
  dateRange: null,
  priority: null,
  searchText: '',
  departments: [],
  roles: []
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
  if (filters.value.priority !== null && filters.value.priority !== undefined) {
    console.log('🎯 Priority filter active:', filters.value.priority, 'Type:', typeof filters.value.priority)
    console.log('📊 Sample task priorities:', result.slice(0, 3).map(t => ({ title: t.title, priority: t.priority, type: typeof t.priority })))
    result = result.filter(t => {
      const taskPriority = Number(t.priority)
      const filterPriority = Number(filters.value.priority)
      const matches = taskPriority === filterPriority
      if (matches) {
        console.log('✅ Match found:', t.title, 'priority:', taskPriority)
      }
      return matches
    })
    console.log('✅ Tasks after priority filter:', result.length)
  }
  
  // Filter by departments (HR-specific)
  if (filters.value.departments && filters.value.departments.length > 0) {
    result = result.filter(t => filters.value.departments.includes(t.assigneeDepartment))
  }
  
  // Filter by roles (HR-specific)
  if (filters.value.roles && filters.value.roles.length > 0) {
    result = result.filter(t => filters.value.roles.includes(t.assigneeRole))
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

const fetchAllEmployees = async () => {
  const response = await fetch(`${USER_SERVICE_URL}/users`)
  if (!response.ok) {
    throw new Error('Failed to fetch all employees')
  }
  
  const data = await response.json()
  // Filter out all employees from the HR department
  return (data.users || []).filter(user => user.role !== 'HR')
}

const fetchTeamTasks = async () => {
  isLoading.value = true
  error.value = null
  
  try {
    // For Staff: Fetch all accessible tasks (owned + collaborated)
    if (userRole.value === 'Staff') {
      const userId = authStore.user?.user_id
      if (!userId) {
        throw new Error('User ID not available')
      }
      
      // Use accessible-tasks endpoint to include tasks where user is owner or collaborator
      const res = await fetch(`${TASK_SERVICE_URL}/users/${userId}/accessible-tasks`)
      if (!res.ok) {
        throw new Error('Failed to fetch tasks')
      }
      const data = await res.json()
      tasks.value = (data.tasks || []).map(task => ({
        ...task,
        assigneeName: authStore.user?.name,
        assigneeRole: authStore.user?.role,
        assigneeId: userId,
        assigneeDepartment: authStore.user?.department
      }))
      subordinates.value = [] // No subordinates for Staff
      lastFetchTime.value = new Date()
      return
    }
    
    // For HR: Fetch all employee tasks
    if (userRole.value === 'HR') {
      const employees = await fetchAllEmployees()
      subordinates.value = employees
      
      if (employees.length === 0) {
        tasks.value = []
        notification.info({
          message: 'No Employees',
          description: 'No employees found in the system.',
          placement: 'topRight'
        })
        return
      }
      
      // Fetch tasks for each employee
      const taskPromises = employees.map(async (employee) => {
        try {
          const res = await fetch(`${TASK_SERVICE_URL}/tasks?owner_id=${employee.user_id}`)
          if (!res.ok) {
            console.warn(`Failed to fetch tasks for ${employee.name}`)
            return []
          }
          const data = await res.json()
          return (data.tasks || []).map(task => ({
            ...task,
            assigneeName: employee.name,
            assigneeRole: employee.role,
            assigneeId: employee.user_id,
            assigneeDepartment: employee.department
          }))
        } catch (err) {
          console.error(`Error fetching tasks for ${employee.name}:`, err)
          return []
        }
      })
      
      const results = await Promise.all(taskPromises)
      tasks.value = results.flat()
      lastFetchTime.value = new Date()
      return
    }
    
    // For Manager/Director: Fetch team tasks
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
      message: 'Failed to Load Tasks',
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
    const role = userRole.value?.toLowerCase() || 'user'
    link.href = URL.createObjectURL(blob)
    link.download = `${role}-tasks-${timestamp}.csv`
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
    searchText: '',
    departments: [],
    roles: []
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
  
  try {
    // Fetch full task details to ensure all fields are present (including project_id)
    const taskResponse = await fetch(`${TASK_SERVICE_URL}/tasks/${task.id}`)
    if (!taskResponse.ok) {
      throw new Error('Failed to fetch task details')
    }
    const taskData = await taskResponse.json()
    const fullTask = taskData.task || taskData
    
    // Merge with existing task data to preserve any computed fields
    selectedTask.value = {
      ...task,
      ...fullTask
    }
    
    console.log('Full task details loaded:', selectedTask.value)
    
    // Fetch access info for the selected task
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
    console.warn('Failed to fetch task details:', err)
    // Fallback to using the task as-is
    selectedTask.value = task
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

const handleOpenTask = async (task) => {
  try {
    console.log('handleOpenTask called with task:', task)
    
    // Fetch full task details
    const taskResponse = await fetch(`${TASK_SERVICE_URL}/tasks/${task.id}`)
    if (!taskResponse.ok) {
      throw new Error('Failed to fetch task details')
    }
    const taskData = await taskResponse.json()
    const rawTask = taskData.task || taskData
    
    // Transform the task data to match expected format
    const transformedTask = {
      ...rawTask,
      project: rawTask.project || rawTask.project_id || 'No Project',
      assignee: rawTask.assignee || rawTask.owner_id || 'Unassigned',
      description: rawTask.description || 'No description available',
      priority: rawTask.priority || 5,
      collaborators: typeof rawTask.collaborators === 'string' 
        ? JSON.parse(rawTask.collaborators || '[]') 
        : (rawTask.collaborators || []),
    }
    
    // Fetch access info for the new task
    const userId = authStore.user?.user_id
    const accessResponse = await fetch(
      `${TASK_SERVICE_URL}/tasks/${task.id}/access?user_id=${userId}`
    )
    if (accessResponse.ok) {
      taskAccessInfo.value = await accessResponse.json()
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
    
    // Update selected task with transformed details
    selectedTask.value = transformedTask
    console.log('Task details loaded and transformed:', selectedTask.value)
    // Modal is already open, so it will just update with new task
  } catch (err) {
    console.warn('Failed to fetch task details:', err)
    taskAccessInfo.value = {
      can_view: true,
      can_comment: true,
      can_edit: false,
      access_type: 'viewer'
    }
    // Fallback to the task object passed in
    selectedTask.value = task
  }
}

const handleTaskUpdated = (updatedTask) => {
  // Update task in the list
  const index = tasks.value.findIndex(t => t.id === updatedTask.id)
  if (index !== -1) {
    tasks.value[index] = { ...tasks.value[index], ...updatedTask }
  }
  
  // Also update the selected task to reflect changes immediately
  if (selectedTask.value && selectedTask.value.id === updatedTask.id) {
    selectedTask.value = { ...selectedTask.value, ...updatedTask }
  }
  
  notification.success({
    message: 'Task Updated',
    description: 'The task has been updated successfully.',
    placement: 'topRight',
    duration: 2
  })
}

const handleTaskDeleted = (deletedTask) => {
  // Remove task from the list
  const index = tasks.value.findIndex(t => t.id === deletedTask.id)
  if (index !== -1) {
    tasks.value.splice(index, 1)
  }
  
  // Close the modal
  showTaskDetail.value = false
  selectedTask.value = null
  
  notification.success({
    message: 'Task Deleted',
    description: 'The task has been deleted successfully.',
    placement: 'topRight',
    duration: 2
  })
}

// Auto-refresh every 10 minutes with intelligent caching
const startAutoRefresh = () => {
  refreshInterval.value = setInterval(() => {
    console.log('Auto-refreshing team tasks...')
    fetchTeamTasks()
  }, 10 * 60 * 1000) // 10 minutes - reduced frequency
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}


// Lifecycle hooks
onMounted(() => {
  fetchTeamTasks()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
/* Dashboard Container */
.dashboard {
  max-width: 1800px;
  margin: 0 auto;
  padding: 32px 40px;
  background: transparent;
  min-height: 100vh;
}

/* Modern Header */
.dashboard-header {
  background: linear-gradient(to bottom, #ffffff, #f9fafb);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(229, 231, 235, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dashboard-header:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
  border-color: rgba(24, 144, 255, 0.2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  flex-wrap: wrap;
}

.header-text {
  flex: 1;
  min-width: 300px;
}

.dashboard-title {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.dashboard-subtitle {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.last-update {
  padding: 6px 12px;
  background: #f3f4f6;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.update-text {
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
}

/* Action Buttons */
.action-button {
  height: 40px !important;
  padding: 0 16px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  border-radius: 10px !important;
  border: 1px solid #d1d5db !important;
  background: #ffffff !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.action-button:hover:not(:disabled) {
  border-color: #1890ff !important;
  color: #1890ff !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15) !important;
}

.action-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Error Alert */
.error-alert {
  margin-bottom: 24px;
  border-radius: 12px;
}

/* Content Card */
.content-card {
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(229, 231, 235, 0.8) !important;
  margin-top: 32px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.content-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04) !important;
}

:deep(.content-card .ant-card-body) {
  padding: 24px !important;
}

/* Modern Tabs */
.dashboard-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 24px !important;
}

.dashboard-tabs :deep(.ant-tabs-tab) {
  padding: 12px 24px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  border-radius: 10px 10px 0 0 !important;
  background: #f3f4f6 !important;
  border: 1px solid #e5e7eb !important;
  transition: all 0.3s ease !important;
  margin-right: 4px !important;
}

.dashboard-tabs :deep(.ant-tabs-tab:hover) {
  background: #e5e7eb !important;
  color: #1890ff !important;
}

.dashboard-tabs :deep(.ant-tabs-tab-active) {
  background: #ffffff !important;
  border-bottom-color: #ffffff !important;
  color: #1890ff !important;
  box-shadow: 0 -2px 8px rgba(24, 144, 255, 0.1) !important;
}

.dashboard-tabs :deep(.ant-tabs-tab .anticon) {
  margin-right: 8px;
  font-size: 16px;
}

.dashboard-tabs :deep(.ant-tabs-content) {
  margin-top: 0 !important;
}

/* Content Rows */
.content-row {
  margin-top: 0 !important;
}

.charts-container {
  margin-top: 0;
}

/* Dark Mode Support */
:global(.dark) .dashboard-header {
  background: linear-gradient(to bottom, #1f2937, #111827);
  border-color: rgba(55, 65, 81, 0.8);
}

:global(.dark) .dashboard-title {
  color: #f9fafb;
}

:global(.dark) .dashboard-subtitle {
  color: #d1d5db;
}

:global(.dark) .last-update {
  background: #374151;
  border-color: #4b5563;
}

:global(.dark) .update-text {
  color: #d1d5db;
}

:global(.dark) .content-card {
  background-color: rgba(31, 41, 55, 1) !important;
  border-color: rgba(55, 65, 81, 0.8) !important;
}

:global(.dark) .dashboard-tabs :deep(.ant-tabs-tab) {
  background: #374151 !important;
  border-color: #4b5563 !important;
  color: #d1d5db !important;
}

:global(.dark) .dashboard-tabs :deep(.ant-tabs-tab-active) {
  background: #1f2937 !important;
  color: #60a5fa !important;
}

/* Responsive Design */
@media (max-width: 1400px) {
  .dashboard {
    padding: 28px 32px;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 20px 16px;
  }
  
  .dashboard-header {
    padding: 20px 24px;
  }
  
  .dashboard-title {
    font-size: 24px;
  }
  
  .dashboard-subtitle {
    font-size: 14px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions :deep(.ant-space) {
    width: 100%;
    flex-direction: column;
  }
  
  .header-actions :deep(.ant-space-item) {
    width: 100%;
  }
  
  .action-button,
  .approval-button {
    width: 100% !important;
  }
  
  .dashboard-tabs :deep(.ant-tabs-tab) {
    padding: 8px 16px !important;
    font-size: 13px !important;
  }
}
</style>
