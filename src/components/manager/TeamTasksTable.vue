<template>
  <a-card :bordered="false" class="tasks-table-card">
    <!-- Card Header -->
    <template #title>
      <div class="table-header">
        <span class="table-title">
          Team Tasks
          <a-tag color="blue" style="margin-left: 12px;">
            {{ displayedTaskCount }} / {{ tasks.length }}
          </a-tag>
        </span>
      </div>
    </template>

    <template #extra>
      <a-space>
        <a-tooltip title="Refresh data">
          <a-button 
            @click="handleRefresh" 
            :loading="isLoading"
            shape="circle"
            type="text"
          >
            <template #icon><ReloadOutlined /></template>
          </a-button>
        </a-tooltip>
      </a-space>
    </template>

    <!-- Main Table -->
    <a-table
      :columns="columns"
      :data-source="tasks"
      :loading="isLoading"
      :pagination="paginationConfig"
      :row-key="record => record.id"
      :scroll="{ x: 1200 }"
      @change="handleTableChange"
      size="middle"
    >
      <!-- Task Title Column -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'title'">
          <a-button 
            type="link" 
            @click="handleViewTask(record)"
            style="padding: 0; text-align: left; height: auto; white-space: normal;"
          >
            {{ record.title }}
          </a-button>
        </template>

        <!-- Assignee Column -->
        <template v-else-if="column.key === 'assignee'">
          <a-space>
            <a-avatar 
              :style="{ backgroundColor: getAvatarColor(record.assigneeName) }"
              size="small"
            >
              {{ getInitials(record.assigneeName) }}
            </a-avatar>
            <div>
              <div style="font-weight: 500;">{{ record.assigneeName }}</div>
              <div style="font-size: 12px; color: #666;">{{ record.assigneeRole }}</div>
            </div>
          </a-space>
        </template>

        <!-- Department Column (HR Only) -->
        <template v-else-if="column.key === 'department'">
          <div style="font-weight: 500;">{{ record.assigneeDepartment || 'N/A' }}</div>
        </template>

        <!-- Due Date Column -->
        <template v-else-if="column.key === 'dueDate'">
          <div v-if="record.dueDate">
            <div :class="getDueDateClass(record.dueDate)">
              {{ formatDate(record.dueDate) }}
            </div>
            <div v-if="record.status !== 'Completed'" style="font-size: 11px; color: #999;">
              {{ getRelativeTime(record.dueDate) }}
            </div>
          </div>
          <span v-else style="color: #999;">No due date</span>
        </template>

        <!-- Status Column -->
        <template v-else-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ record.status }}
          </a-tag>
        </template>

        <!-- Priority Column -->
        <template v-else-if="column.key === 'priority'">
          <a-tag :color="getPriorityColor(record.priority)">
            {{ record.priority || 'Medium' }}
          </a-tag>
        </template>
      </template>
    </a-table>
  </a-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ReloadOutlined, EyeOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  tasks: {
    type: Array,
    required: true,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  subordinates: {
    type: Array,
    default: () => []
  },
  userRole: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['refresh', 'view-task'])

// Pagination state
const currentPage = ref(1)
const pageSize = ref(20)

// Computed
const displayedTaskCount = computed(() => {
  return props.tasks.length
})

const paginationConfig = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: props.tasks.length,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} tasks`,
  pageSizeOptions: ['10', '20', '50', '100'],
  position: ['bottomCenter']
}))

// Create filter options from subordinates
const assigneeFilters = computed(() => {
  const filters = props.subordinates.map(sub => ({
    text: sub.name,
    value: sub.user_id
  }))
  // Sort alphabetically
  return filters.sort((a, b) => a.text.localeCompare(b.text))
})

// Create department filter options (for HR)
const departmentFilters = computed(() => {
  const departments = [...new Set(props.subordinates.map(sub => sub.department).filter(Boolean))]
  return departments.sort().map(dept => ({
    text: dept,
    value: dept
  }))
})

// Check if user is HR
const isHRUser = computed(() => props.userRole === 'HR')

// Table columns configuration
const columns = computed(() => {
  const baseColumns = [
    {
      title: 'Task Title',
      dataIndex: 'title',
      key: 'title',
      width: 300,
      ellipsis: true,
      fixed: 'left',
      sorter: (a, b) => (a.title || '').localeCompare(b.title || '')
    },
    {
      title: 'Assignee',
      dataIndex: 'assigneeName',
      key: 'assignee',
      width: 200,
      filters: assigneeFilters.value,
      onFilter: (value, record) => record.assigneeId === value
    }
  ]

  // Add Department column for HR users only
  if (isHRUser.value) {
    baseColumns.push({
      title: 'Department',
      dataIndex: 'assigneeDepartment',
      key: 'department',
      width: 180,
      filters: departmentFilters.value,
      onFilter: (value, record) => record.assigneeDepartment === value,
      sorter: (a, b) => (a.assigneeDepartment || '').localeCompare(b.assigneeDepartment || '')
    })
  }

  // Add remaining columns
  baseColumns.push(
    {
      title: 'Due Date',
      dataIndex: 'dueDate',
      key: 'dueDate',
      width: 150,
      sorter: (a, b) => {
        if (!a.dueDate) return 1
        if (!b.dueDate) return -1
        return new Date(a.dueDate) - new Date(b.dueDate)
      },
      defaultSortOrder: 'ascend'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      filters: [
        { text: 'Unassigned', value: 'Unassigned' },
        { text: 'On Going', value: 'On Going' },
        { text: 'Under Review', value: 'Under Review' },
        { text: 'Completed', value: 'Completed' }
      ],
      onFilter: (value, record) => record.status === value
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 120,
      filters: [
        { text: '1', value: 1 },
        { text: '2', value: 2 },
        { text: '3', value: 3 },
        { text: '4', value: 4 },
        { text: '5', value: 5 },
        { text: '6', value: 6 },
        { text: '7', value: 7 },
        { text: '8', value: 8 },
        { text: '9', value: 9 },
        { text: '10', value: 10 }
      ],
      onFilter: (value, record) => Number(record.priority) === Number(value),
      sorter: (a, b) => Number(a.priority || 5) - Number(b.priority || 5)
    }
  )

  return baseColumns
})

// Methods
const handleTableChange = (pagination, filters, sorter) => {
  currentPage.value = pagination.current
  pageSize.value = pagination.pageSize
}

const handleRefresh = () => {
  emit('refresh')
}

const handleViewTask = (task) => {
  console.log('TeamTasksTable: handleViewTask called, emitting view-task event with:', task)
  emit('view-task', task)
}

// Color helpers
const getStatusColor = (status) => {
  const colorMap = {
    'Unassigned': 'default',
    'On Going': 'processing',
    'Under Review': 'warning',
    'Completed': 'success'
  }
  return colorMap[status] || 'default'
}

const getPriorityColor = (priority) => {
  const colorMap = {
    'High': 'red',
    'Medium': 'orange',
    'Low': 'blue'
  }
  return colorMap[priority || 'Medium'] || 'orange'
}

const getDueDateClass = (dueDate) => {
  if (!dueDate) return ''
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dueDate)
  due.setHours(0, 0, 0, 0)
  const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return 'overdue-date'      // Red
  if (diffDays <= 3) return 'urgent-date'      // Orange
  return 'normal-date'
}

const formatDate = (date) => {
  if (!date) return 'No due date'
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

const getRelativeTime = (date) => {
  if (!date) return ''
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(date)
  due.setHours(0, 0, 0, 0)
  const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return `${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''} overdue`
  if (diffDays === 0) return 'Due today'
  if (diffDays === 1) return 'Due tomorrow'
  if (diffDays <= 7) return `Due in ${diffDays} days`
  return ''
}

const getAvatarColor = (name) => {
  if (!name) return '#1890ff'
  const colors = [
    '#f56a00', '#7265e6', '#ffbf00', '#00a2ae', '#1890ff',
    '#52c41a', '#eb2f96', '#722ed1', '#13c2c2', '#fa8c16'
  ]
  const charCode = name.charCodeAt(0) + (name.charCodeAt(name.length - 1) || 0)
  return colors[charCode % colors.length]
}

const getInitials = (name) => {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}
</script>

<style scoped>
.tasks-table-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
}

.overdue-date {
  color: #ff4d4f;
  font-weight: 600;
}

.urgent-date {
  color: #fa8c16;
  font-weight: 600;
}

.normal-date {
  color: #262626;
}

:deep(.ant-table) {
  font-size: 14px;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background-color: #f5f5f5;
}

:deep(.ant-table-cell) {
  padding: 12px 16px;
}

@media (max-width: 768px) {
  :deep(.ant-table-cell) {
    padding: 8px 12px;
  }
}
</style>
