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
              <span class="stat-label">Ongoing</span>
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

        <!-- Team Member Bar Chart -->
        <div class="bar-chart-section">
          <h3 class="chart-title">Task Status by Team Member</h3>
          <div class="bar-chart-container">
            <canvas ref="teamBarChartCanvas" width="800" height="450"></canvas>
          </div>
        </div>

        <a-table
          :dataSource="reportData.team_performance"
          :columns="teamColumns"
          :pagination="false"
          size="small"
          class="team-table"
          :row-class-name="(record) => record.member === reportData.requesting_user_name ? 'highlight-current-user' : ''"
        />
      </div>

      <!-- My Tasks Section -->
      <div class="report-section" v-if="reportData.my_tasks && reportData.my_tasks.length > 0">
        <h2 class="section-title">My Tasks ({{ reportData.my_tasks.length }})</h2>
        <a-table
          :dataSource="reportData.my_tasks"
          :columns="taskColumns"
          :pagination="false"
          size="small"
          class="task-table"
        />
      </div>

      <!-- Other Tasks Section -->
      <div class="report-section" v-if="reportData.other_tasks && reportData.other_tasks.length > 0">
        <h2 class="section-title">Other Tasks ({{ reportData.other_tasks.length }})</h2>
        <a-table
          :dataSource="reportData.other_tasks"
          :columns="taskColumns"
          :pagination="false"
          size="small"
          class="task-table"
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
const teamBarChartCanvas = ref(null)

// Watch for prop changes
watch(() => props.isOpen, (newVal) => {
  modalVisible.value = newVal
  if (newVal) {
    activeGroups.value = ['Overdue', 'Ongoing']
  }
}, { immediate: true })

// Watch for reportData changes to draw charts
watch(() => props.reportData, (newVal) => {
  if (newVal) {
    console.log('ProjectReportPreviewModal - reportData received:', newVal)
    console.log('Team performance data:', newVal.team_performance)
    nextTick(() => {
      drawPieChart()
      drawTeamBarChart()
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
    labels.push('Ongoing')
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

const drawTeamBarChart = () => {
  if (!teamBarChartCanvas.value || !props.reportData?.team_performance?.length) return

  const canvas = teamBarChartCanvas.value
  const ctx = canvas.getContext('2d')
  const teamMembers = props.reportData.team_performance

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // Calculate dimensions for HORIZONTAL bars
  const barHeight = 30
  const barSpacing = 50
  const leftMargin = 150  // Space for member names on left
  const rightMargin = 50
  const topMargin = 100   // Space for title and legend
  const bottomMargin = 20

  const maxTotalTasks = Math.max(...teamMembers.map(member => member.total || 0))
  const chartWidth = canvas.width - leftMargin - rightMargin

  // Define colors for each status
  const colors = {
    overdue: '#ef4444',      // Red
    ongoing: '#3b82f6',      // Blue
    underReview: '#eab308',  // Yellow
    completed: '#22c55e'     // Green
  }

  // Add title
  ctx.fillStyle = '#1f2937'
  ctx.font = 'bold 16px Arial'
  ctx.textAlign = 'center'
  ctx.fillText('Task Status by Team Member', canvas.width/2, 25)

  // Add legend in a single row
  const legendY = 50
  const legendStartX = 200

  ctx.font = '11px Arial'
  ctx.textAlign = 'left'

  // Overdue legend
  ctx.fillStyle = colors.overdue
  ctx.fillRect(legendStartX, legendY, 18, 12)
  ctx.fillStyle = '#1f2937'
  ctx.fillText('Overdue', legendStartX + 24, legendY + 10)

  // Ongoing legend
  ctx.fillStyle = colors.ongoing
  ctx.fillRect(legendStartX + 100, legendY, 18, 12)
  ctx.fillStyle = '#1f2937'
  ctx.fillText('Ongoing', legendStartX + 124, legendY + 10)

  // Under Review legend
  ctx.fillStyle = colors.underReview
  ctx.fillRect(legendStartX + 200, legendY, 18, 12)
  ctx.fillStyle = '#1f2937'
  ctx.fillText('Under Review', legendStartX + 224, legendY + 10)

  // Completed legend
  ctx.fillStyle = colors.completed
  ctx.fillRect(legendStartX + 320, legendY, 18, 12)
  ctx.fillStyle = '#1f2937'
  ctx.fillText('Completed', legendStartX + 344, legendY + 10)

  // Draw horizontal stacked bars for each member
  teamMembers.forEach((member, i) => {
    const yPos = topMargin + i * barSpacing

    // Get task counts for each status
    const overdue = member.overdue || 0
    const ongoing = member.ongoing || 0
    const underReview = member.under_review || 0
    const completed = member.completed || 0
    const total = member.total || 0

    // Calculate widths for each section based on actual task count (scaled to maxTotalTasks)
    const scale = maxTotalTasks > 0 ? chartWidth / maxTotalTasks : 0
    const overdueWidth = overdue * scale
    const ongoingWidth = ongoing * scale
    const underReviewWidth = underReview * scale
    const completedWidth = completed * scale

    // Draw member name on the left
    ctx.fillStyle = '#1f2937'
    ctx.font = '12px Arial'
    ctx.textAlign = 'right'
    ctx.fillText(
      member.member.length > 18 ? member.member.substring(0, 18) + '...' : member.member,
      leftMargin - 10,
      yPos + barHeight/2 + 4
    )

    // Draw stacked sections from left to right
    let currentX = leftMargin

    // Overdue (red) - leftmost
    if (overdue > 0) {
      ctx.fillStyle = colors.overdue
      ctx.fillRect(currentX, yPos, overdueWidth, barHeight)

      // Draw count if section is wide enough
      if (overdueWidth > 25) {
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 11px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(overdue, currentX + overdueWidth/2, yPos + barHeight/2 + 4)
      }

      currentX += overdueWidth
    }

    // Ongoing (blue)
    if (ongoing > 0) {
      ctx.fillStyle = colors.ongoing
      ctx.fillRect(currentX, yPos, ongoingWidth, barHeight)

      if (ongoingWidth > 25) {
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 11px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(ongoing, currentX + ongoingWidth/2, yPos + barHeight/2 + 4)
      }

      currentX += ongoingWidth
    }

    // Under Review (yellow)
    if (underReview > 0) {
      ctx.fillStyle = colors.underReview
      ctx.fillRect(currentX, yPos, underReviewWidth, barHeight)

      if (underReviewWidth > 25) {
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 11px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(underReview, currentX + underReviewWidth/2, yPos + barHeight/2 + 4)
      }

      currentX += underReviewWidth
    }

    // Completed (green) - rightmost
    if (completed > 0) {
      ctx.fillStyle = colors.completed
      ctx.fillRect(currentX, yPos, completedWidth, barHeight)

      if (completedWidth > 25) {
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 11px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(completed, currentX + completedWidth/2, yPos + barHeight/2 + 4)
      }

      currentX += completedWidth
    }

    // Draw total count at the end of the bar
    ctx.fillStyle = '#1f2937'
    ctx.font = 'bold 12px Arial'
    ctx.textAlign = 'left'
    ctx.fillText(
      total,
      currentX + 8,
      yPos + barHeight/2 + 4
    )
  })

  // Draw X-axis with scale
  const xAxisY = topMargin + teamMembers.length * barSpacing + 10
  ctx.strokeStyle = '#9ca3af'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(leftMargin, xAxisY)
  ctx.lineTo(leftMargin + chartWidth, xAxisY)
  ctx.stroke()

  // Draw X-axis labels (0, max/4, max/2, 3*max/4, max)
  ctx.fillStyle = '#6b7280'
  ctx.font = '10px Arial'
  ctx.textAlign = 'center'

  const xAxisLabels = 5
  for (let i = 0; i < xAxisLabels; i++) {
    const value = Math.round((maxTotalTasks / (xAxisLabels - 1)) * i)
    const xPos = leftMargin + (chartWidth / (xAxisLabels - 1)) * i

    // Draw tick mark
    ctx.beginPath()
    ctx.moveTo(xPos, xAxisY)
    ctx.lineTo(xPos, xAxisY + 5)
    ctx.stroke()

    // Draw label
    ctx.fillText(value, xPos, xAxisY + 18)
  }

  // Draw X-axis title
  ctx.fillStyle = '#1f2937'
  ctx.font = '11px Arial'
  ctx.textAlign = 'center'
  ctx.fillText('Number of Tasks', leftMargin + chartWidth/2, xAxisY + 35)
}

// Team performance table columns
const teamColumns = [
  {
    title: 'Team Member',
    dataIndex: 'member',
    key: 'member',
    customRender: ({ record }) => {
      const requesting_user_name = props.reportData?.requesting_user_name
      if (requesting_user_name && record.member === requesting_user_name) {
        return `${record.member} (me)`
      }
      return record.member
    }
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
    title: 'Overdue',
    dataIndex: 'overdue',
    key: 'overdue',
    align: 'center',
    customRender: ({ record }) => record.overdue || 0
  },
  {
    title: 'Ongoing',
    dataIndex: 'ongoing',
    key: 'ongoing',
    align: 'center',
    customRender: ({ record }) => record.ongoing || 0
  },
  {
    title: 'Under Review',
    dataIndex: 'under_review',
    key: 'under_review',
    align: 'center',
    customRender: ({ record }) => record.under_review || 0
  },
  {
    title: 'Completed',
    dataIndex: 'completed',
    key: 'completed',
    align: 'center',
    customRender: ({ record }) => record.completed || 0
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

/* Bar Chart Section */
.bar-chart-section {
  margin-top: 32px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
  text-align: center;
}

.bar-chart-container {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

/* Highlight current user row in team performance table */
.team-table :deep(.highlight-current-user) {
  background-color: #dbeafe !important;
}

.team-table :deep(.highlight-current-user td) {
  color: #1e40af !important;
  font-weight: 600 !important;
}

/* Colored column headers for team performance table */
.team-table :deep(th:nth-child(4)) {
  background-color: #ef4444 !important; /* Overdue - Red */
  color: white !important;
}

.team-table :deep(th:nth-child(5)) {
  background-color: #3b82f6 !important; /* Ongoing - Blue */
  color: white !important;
}

.team-table :deep(th:nth-child(6)) {
  background-color: #eab308 !important; /* Under Review - Yellow */
  color: white !important;
}

.team-table :deep(th:nth-child(7)) {
  background-color: #22c55e !important; /* Completed - Green */
  color: white !important;
}

/* Colored values in status columns */
.team-table :deep(td:nth-child(4)) {
  color: #dc2626; /* Overdue values - darker red */
  font-weight: 600;
}

.team-table :deep(td:nth-child(5)) {
  color: #2563eb; /* Ongoing values - darker blue */
  font-weight: 600;
}

.team-table :deep(td:nth-child(6)) {
  color: #ca8a04; /* Under Review values - darker yellow */
  font-weight: 600;
}

.team-table :deep(td:nth-child(7)) {
  color: #16a34a; /* Completed values - darker green */
  font-weight: 600;
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
  background: #ef4444;
  color: white;
}

.task-groups :deep(.status-ongoing .ant-collapse-header) {
  background: #3b82f6;
  color: white;
}

.task-groups :deep(.status-under-review .ant-collapse-header) {
  background: #eab308;
  color: white;
}

.task-groups :deep(.status-completed .ant-collapse-header) {
  background: #22c55e;
  color: white;
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
