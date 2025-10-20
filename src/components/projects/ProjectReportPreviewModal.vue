<template>
  <a-modal
    v-model:open="modalVisible"
    :title="null"
    :footer="null"
    :width="1000"
    :closable="false"
    :maskClosable="false"
    @cancel="handleClose"
    class="report-preview-modal"
  >
    <!-- Header -->
    <div class="modal-header">
      <div class="header-content">
        <div class="icon-wrapper">
          <FileTextOutlined class="header-icon" />
        </div>
        <div class="header-text">
          <h3 class="modal-title">Project Report Preview</h3>
          <p class="modal-subtitle">Review the report before exporting to PDF</p>
        </div>
      </div>
      <a-button
        type="text"
        @click="handleClose"
        class="close-button"
        :icon="h(CloseOutlined)"
      />
    </div>

    <!-- Report Content -->
    <div class="report-content" v-if="reportData">
      <!-- Project Overview -->
      <div class="report-section">
        <h2 class="section-title">Project Overview</h2>
        <div class="overview-grid">
          <div class="overview-item">
            <span class="label">Project Name:</span>
            <span class="value">{{ reportData.project.name }}</span>
          </div>
          <div class="overview-item">
            <span class="label">Project Owner:</span>
            <span class="value">{{ reportData.project.owner }}</span>
          </div>
          <div class="overview-item">
            <span class="label">Start Date:</span>
            <span class="value">{{ reportData.project.created_date }}</span>
          </div>
          <div class="overview-item">
            <span class="label">Due Date:</span>
            <span class="value">{{ reportData.project.due_date }}</span>
          </div>
          <div class="overview-item full-width">
            <span class="label">Description:</span>
            <span class="value">{{ reportData.project.description }}</span>
          </div>
        </div>
      </div>

      <!-- Project Performance Summary -->
      <div class="report-section">
        <h2 class="section-title">Project Performance Summary</h2>
        <div class="summary-container">
          <!-- Pie Chart -->
          <div class="pie-chart-container">
            <canvas ref="pieChartCanvas" width="400" height="450"></canvas>
          </div>

          <!-- Stats Cards -->
          <div class="stats-cards">
            <div class="stat-item">
              <span class="stat-label">Total Tasks</span>
              <span class="stat-value">{{ reportData.summary.total_tasks }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Overdue</span>
              <span class="stat-value overdue-color">{{ reportData.summary.overdue_tasks || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Completed</span>
              <span class="stat-value completed-color">{{ reportData.summary.completed_tasks }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">In Progress</span>
              <span class="stat-value progress-color">{{ reportData.summary.ongoing_tasks }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Under Review</span>
              <span class="stat-value review-color">{{ reportData.summary.under_review_tasks }}</span>
            </div>
            <div class="stat-item highlight">
              <span class="stat-label">Completion Rate</span>
              <span class="stat-value">{{ reportData.summary.completion_rate }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Team Member Performance -->
      <div class="report-section" v-if="reportData.team_performance.length > 0">
        <h2 class="section-title">Team Member Performance</h2>
        <a-table
          :dataSource="reportData.team_performance"
          :columns="teamColumns"
          :pagination="false"
          size="small"
          class="team-table"
        />
      </div>

      <!-- Task Breakdown by Status -->
      <div class="report-section">
        <h2 class="section-title">Task Breakdown by Status</h2>
        <a-collapse v-model:activeKey="activeGroups" class="task-groups">
          <a-collapse-panel
            v-for="(tasks, status) in filteredTaskGroups"
            :key="status"
            :header="`${status} (${tasks.length})`"
            :class="`status-${status.toLowerCase().replace(' ', '-')}`"
          >
            <a-table
              :dataSource="tasks"
              :columns="taskColumns"
              :pagination="false"
              size="small"
              class="task-table"
            />
          </a-collapse-panel>
        </a-collapse>
      </div>

      <div class="report-footer">
        <small>Report generated at: {{ reportData.generated_at }}</small>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="loading-container">
      <a-spin size="large" />
      <p>Loading report data...</p>
    </div>

    <!-- Footer Actions -->
    <div class="modal-actions">
      <a-button @click="handleClose" size="large">
        Cancel
      </a-button>
      <a-button
        type="primary"
        size="large"
        @click="handleExportPDF"
        :loading="isExporting"
        :icon="h(DownloadOutlined)"
      >
        Export to PDF
      </a-button>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch, h, nextTick } from 'vue'
import {
  FileTextOutlined,
  CloseOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  reportData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'export'])

const modalVisible = ref(false)
const isExporting = ref(false)
const activeGroups = ref(['Overdue', 'Ongoing'])
const pieChartCanvas = ref(null)

// Watch for prop changes
watch(() => props.isOpen, (newVal) => {
  modalVisible.value = newVal
  if (newVal) {
    activeGroups.value = ['Overdue', 'Ongoing']
  }
}, { immediate: true })

// Watch for reportData changes to draw pie chart
watch(() => props.reportData, (newVal) => {
  if (newVal) {
    nextTick(() => {
      drawPieChart()
    })
  }
}, { immediate: true })

const drawPieChart = () => {
  if (!pieChartCanvas.value || !props.reportData) return

  const canvas = pieChartCanvas.value
  const ctx = canvas.getContext('2d')
  const summary = props.reportData.summary

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // Prepare data
  const data = []
  const labels = []
  const colors = []

  const overdueCount = summary.overdue_tasks || 0
  if (overdueCount > 0) {
    data.push(overdueCount)
    labels.push('Overdue')
    colors.push('#ef4444')
  }

  if (summary.completed_tasks > 0) {
    data.push(summary.completed_tasks)
    labels.push('Completed')
    colors.push('#22c55e')
  }

  if (summary.ongoing_tasks > 0) {
    data.push(summary.ongoing_tasks)
    labels.push('In Progress')
    colors.push('#3b82f6')
  }

  if (summary.under_review_tasks > 0) {
    data.push(summary.under_review_tasks)
    labels.push('Under Review')
    colors.push('#a855f7')
  }

  if (data.length === 0) {
    data.push(1)
    labels.push('No Tasks')
    colors.push('#e5e7eb')
  }

  // Calculate total
  const total = data.reduce((a, b) => a + b, 0)

  // Draw pie chart (centered and larger)
  const centerX = canvas.width / 2
  const centerY = 150
  const radius = 120

  let startAngle = -Math.PI / 2

  data.forEach((value, index) => {
    const sliceAngle = (value / total) * 2 * Math.PI

    // Draw slice
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle)
    ctx.closePath()
    ctx.fillStyle = colors[index]
    ctx.fill()
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 3
    ctx.stroke()

    startAngle += sliceAngle
  })

  // Draw legend below the pie chart
  const legendStartY = 320
  let legendY = legendStartY
  const legendX = 30

  ctx.font = '14px Arial'
  ctx.textAlign = 'left'

  labels.forEach((label, index) => {
    // Draw color box
    ctx.fillStyle = colors[index]
    ctx.fillRect(legendX, legendY - 12, 16, 16)

    // Draw text
    ctx.fillStyle = '#1f2937'
    ctx.fillText(`${label}: ${data[index]}`, legendX + 24, legendY)

    legendY += 28
  })
}

// Team performance table columns
const teamColumns = [
  {
    title: 'Team Member',
    dataIndex: 'member',
    key: 'member'
  },
  {
    title: 'Department',
    dataIndex: 'department',
    key: 'department',
    align: 'center'
  },
  {
    title: 'Total Tasks',
    dataIndex: 'total',
    key: 'total',
    align: 'center'
  },
  {
    title: 'Completed',
    dataIndex: 'completed',
    key: 'completed',
    align: 'center'
  },
  {
    title: 'Completion Rate',
    key: 'rate',
    align: 'center',
    customRender: ({ record }) => `${record.rate}%`
  }
]

// Task table columns
const taskColumns = [
  {
    title: 'Task Title',
    dataIndex: 'title',
    key: 'title',
    width: '40%'
  },
  {
    title: 'Assignee',
    key: 'assignee',
    align: 'center',
    customRender: ({ record }) => record.assignee_name || record.owner_name || 'Unassigned'
  },
  {
    title: 'Priority',
    key: 'priority',
    align: 'center',
    customRender: ({ record }) => {
      const priority = parseInt(record.priority)
      return isNaN(priority) ? 'N/A' : `${priority} / 10`
    }
  },
  {
    title: 'Due Date',
    key: 'dueDate',
    align: 'center',
    customRender: ({ record }) => {
      const date = record.dueDate || record.due_date
      if (!date) return 'N/A'
      try {
        return new Date(date).toLocaleDateString()
      } catch {
        return 'N/A'
      }
    }
  }
]

// Filter out empty task groups
const filteredTaskGroups = computed(() => {
  if (!props.reportData?.task_groups) return {}

  const groups = {}
  Object.entries(props.reportData.task_groups).forEach(([status, tasks]) => {
    if (tasks && tasks.length > 0) {
      groups[status] = tasks
    }
  })
  return groups
})

const getStatusColor = (status) => {
  const colors = {
    'Active': 'blue',
    'Planning': 'cyan',
    'On Hold': 'orange',
    'Completed': 'green',
    'Cancelled': 'red'
  }
  return colors[status] || 'default'
}

const handleClose = () => {
  modalVisible.value = false
  emit('close')
}

const handleExportPDF = () => {
  emit('export')
}
</script>

<style scoped>
.report-preview-modal :deep(.ant-modal-body) {
  padding: 0;
  max-height: 70vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon {
  font-size: 24px;
  color: white;
}

.header-text {
  flex: 1;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.modal-subtitle {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: #6b7280;
}

.close-button {
  color: #6b7280;
}

.close-button:hover {
  color: #1f2937;
}

.report-content {
  padding: 24px;
}

.report-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overview-item.full-width {
  grid-column: 1 / -1;
}

.label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value {
  font-size: 14px;
  color: #1f2937;
}

.summary-container {
  display: flex;
  gap: 48px;
  align-items: flex-start;
}

.pie-chart-container {
  flex: 0 0 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-right: 20px;
}

.stats-cards {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-left: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.stat-item.highlight {
  background: white;
  border: 1px solid #e5e7eb;
}

.stat-item .stat-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-item.highlight .stat-label {
  color: #6b7280;
}

.stat-item .stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.stat-item.highlight .stat-value {
  color: #1f2937;
}

.stat-value.overdue-color {
  color: #ef4444;
}

.stat-value.completed-color {
  color: #22c55e;
}

.stat-value.progress-color {
  color: #3b82f6;
}

.stat-value.review-color {
  color: #a855f7;
}

.team-table,
.task-table {
  margin-top: 8px;
}

.task-groups :deep(.ant-collapse-item) {
  margin-bottom: 8px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.task-groups :deep(.ant-collapse-header) {
  font-weight: 600;
  padding: 12px 16px;
}

.task-groups :deep(.status-overdue .ant-collapse-header) {
  background: #fee2e2;
  color: #dc2626;
}

.task-groups :deep(.status-ongoing .ant-collapse-header) {
  background: #dbeafe;
  color: #2563eb;
}

.task-groups :deep(.status-under-review .ant-collapse-header) {
  background: #e9d5ff;
  color: #9333ea;
}

.task-groups :deep(.status-completed .ant-collapse-header) {
  background: #d1fae5;
  color: #059669;
}

.task-groups :deep(.status-unassigned .ant-collapse-header) {
  background: #f3f4f6;
  color: #6b7280;
}

.report-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  text-align: center;
  color: #6b7280;
}

.loading-container {
  padding: 60px;
  text-align: center;
}

.loading-container p {
  margin-top: 16px;
  color: #6b7280;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

@media (max-width: 768px) {
  .summary-container {
    flex-direction: column;
  }

  .pie-chart-container {
    flex: 1;
    width: 100%;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
