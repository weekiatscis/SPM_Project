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
            <span class="label">Status:</span>
            <a-tag :color="getStatusColor(reportData.project.status)">
              {{ reportData.project.status }}
            </a-tag>
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
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ reportData.summary.total_tasks }}</div>
            <div class="stat-label">Total Tasks</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ reportData.summary.completed_tasks }}</div>
            <div class="stat-label">Completed</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ reportData.summary.ongoing_tasks }}</div>
            <div class="stat-label">In Progress</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ reportData.summary.under_review_tasks }}</div>
            <div class="stat-label">Under Review</div>
          </div>
          <div class="stat-card highlight">
            <div class="stat-value">{{ reportData.summary.completion_rate }}%</div>
            <div class="stat-label">Completion Rate</div>
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
import { ref, computed, watch, h } from 'vue'
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

// Watch for prop changes
watch(() => props.isOpen, (newVal) => {
  modalVisible.value = newVal
  if (newVal) {
    activeGroups.value = ['Overdue', 'Ongoing']
  }
}, { immediate: true })

// Team performance table columns
const teamColumns = [
  {
    title: 'Team Member',
    dataIndex: 'member',
    key: 'member'
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.stat-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-card.highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-card.highlight .stat-value {
  color: white;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

.stat-card.highlight .stat-label {
  color: rgba(255, 255, 255, 0.9);
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
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
