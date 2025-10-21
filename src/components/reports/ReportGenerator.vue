<template>
  <a-card :bordered="false" class="report-card">
    <template #title>
      <div class="card-header">
        <FileTextOutlined class="header-icon" />
        <span>Generate Report</span>
      </div>
    </template>

    <div class="report-content">
      <div class="filters-wrapper">
        <!-- Date Range Picker -->
        <div class="filter-section">
          <label class="filter-label">Date Range</label>
          <a-range-picker
            v-model:value="dateRange"
            format="YYYY-MM-DD"
            :style="{ width: '100%' }"
            :disabled="isGenerating"
            size="middle"
          />
        </div>

        <!-- Status Filter -->
        <div class="filter-section">
          <label class="filter-label">Task Status</label>
          <a-checkbox-group
            v-model:value="statusFilter"
            :style="{ width: '100%' }"
            :disabled="isGenerating"
          >
            <div class="checkbox-grid">
              <a-checkbox value="Unassigned">Unassigned</a-checkbox>
              <a-checkbox value="Ongoing">Ongoing</a-checkbox>
              <a-checkbox value="Completed">Completed</a-checkbox>
              <a-checkbox value="Under Review">Under Review</a-checkbox>
            </div>
          </a-checkbox-group>
        </div>

        <!-- Generate Button -->
        <a-button
          type="primary"
          block
          size="middle"
          :loading="isGenerating"
          :disabled="!currentUser"
          @click="generateReport"
          class="generate-button"
        >
          <template #icon>
            <DownloadOutlined v-if="!isGenerating" />
          </template>
          {{ isGenerating ? 'Generating...' : 'Generate PDF' }}
        </a-button>

        <!-- Info Message -->
        <div class="info-message" v-if="!currentUser">
          <InfoCircleOutlined />
          <span>Please log in to generate reports</span>
        </div>

        <!-- Success/Error Messages -->
        <a-alert
          v-if="successMessage"
          :message="successMessage"
          type="success"
          show-icon
          closable
          @close="successMessage = ''"
          class="compact-alert"
        />

        <a-alert
          v-if="errorMessage"
          :message="errorMessage"
          type="error"
          show-icon
          closable
          @close="errorMessage = ''"
          class="compact-alert"
        />
      </div>

      <!-- Report Info -->
      <div class="report-info">
        <div class="info-item">
          <CheckCircleOutlined class="info-icon success" />
          <span>Task details</span>
        </div>
        <div class="info-item">
          <PieChartOutlined class="info-icon primary" />
          <span>Status breakdown</span>
        </div>
        <div class="info-item">
          <CalendarOutlined class="info-icon secondary" />
          <span>Duration tracking</span>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script>
import { ref, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { message } from 'ant-design-vue'
import {
  FileTextOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  PieChartOutlined,
  CalendarOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'ReportGenerator',
  components: {
    FileTextOutlined,
    DownloadOutlined,
    InfoCircleOutlined,
    CheckCircleOutlined,
    PieChartOutlined,
    CalendarOutlined
  },
  setup() {
    const authStore = useAuthStore()
    const currentUser = computed(() => authStore.user)

    const dateRange = ref(null)
    const statusFilter = ref([])
    const isGenerating = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')

    const generateReport = async () => {
      if (!currentUser.value) {
        message.error('Please log in to generate reports')
        return
      }

      isGenerating.value = true
      errorMessage.value = ''
      successMessage.value = ''

      try {
        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'

        // Prepare request body
        const requestBody = {
          user_id: currentUser.value.user_id,
          user_name: currentUser.value.name || 'Unknown User',
          status_filter: statusFilter.value.length > 0 ? statusFilter.value : ['All']
        }

        // Add date range if selected
        if (dateRange.value && dateRange.value.length === 2) {
          requestBody.start_date = dateRange.value[0].format('YYYY-MM-DD')
          requestBody.end_date = dateRange.value[1].format('YYYY-MM-DD')
        }

        // Make request to report service
        const response = await fetch(`${reportServiceUrl}/generate-report`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody)
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to generate report')
        }

        // Get the PDF blob
        const blob = await response.blob()

        // Create download link
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url

        // Generate filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0]
        const userName = currentUser.value.name?.replace(/\s+/g, '_') || 'user'
        a.download = `task_report_${userName}_${timestamp}.pdf`

        // Trigger download
        document.body.appendChild(a)
        a.click()

        // Cleanup
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)

        successMessage.value = 'Report generated successfully!'
        message.success('Report downloaded successfully!')

      } catch (error) {
        console.error('Error generating report:', error)
        errorMessage.value = error.message || 'Failed to generate report. Please try again.'
        message.error('Failed to generate report')
      } finally {
        isGenerating.value = false
      }
    }

    return {
      currentUser,
      dateRange,
      statusFilter,
      isGenerating,
      successMessage,
      errorMessage,
      generateReport
    }
  }
}
</script>

<style scoped>
.report-card {
  height: 100%;
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(229, 231, 235, 0.8) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  display: flex;
  flex-direction: column;
}

:deep(.ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px !important;
}

.report-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04) !important;
  border-color: rgba(24, 144, 255, 0.2) !important;
}

:deep(.ant-card-head) {
  padding: 16px 20px !important;
  border-bottom: 1px solid #f3f4f6 !important;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  letter-spacing: -0.02em;
}

.header-icon {
  color: #1890ff;
  font-size: 20px;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.filters-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 12px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

:deep(.ant-checkbox-wrapper) {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.generate-button {
  height: 44px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.25) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.generate-button:hover:not(:disabled) {
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.35) !important;
}

.generate-button:active:not(:disabled) {
  transform: translateY(0) !important;
}

.compact-alert {
  margin-top: 0 !important;
}

.info-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background-color: #fef3c7;
  border-radius: 8px;
  color: #92400e;
  font-size: 13px;
  border: 1px solid #fde68a;
}

.report-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.info-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.info-icon.success {
  color: #52c41a;
}

.info-icon.primary {
  color: #1890ff;
}

.info-icon.secondary {
  color: #722ed1;
}

/* Dark mode support */
:global(.dark) .filter-label {
  color: #ffffff;
}

:global(.dark) .checkbox-grid {
  background-color: #1f1f1f;
  border-color: #434343;
}

:global(.dark) .info-message {
  background-color: #1f1f1f;
  color: #bfbfbf;
}

:global(.dark) .report-info {
  background-color: #1f1f1f;
}

:global(.dark) .info-item {
  color: #bfbfbf;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card-header {
    font-size: 16px;
  }

  .generate-button {
    height: 44px;
    font-size: 15px;
  }

  .report-info {
    padding: 12px;
  }
}
</style>
