<template>
  <a-card :bordered="false" class="report-card">
    <template #title>
      <div class="card-header">
        <FileTextOutlined class="header-icon" />
        <span>Generate Report</span>
      </div>
    </template>

    <div class="report-content">
      <!-- Date Range Picker -->
      <div class="filter-section">
        <label class="filter-label">Date Range</label>
        <a-range-picker
          v-model:value="dateRange"
          format="YYYY-MM-DD"
          :style="{ width: '100%' }"
          :disabled="isGenerating"
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
        size="large"
        :loading="isGenerating"
        :disabled="!currentUser"
        @click="generateReport"
        class="generate-button"
      >
        <template #icon>
          <DownloadOutlined v-if="!isGenerating" />
        </template>
        {{ isGenerating ? 'Generating Report...' : 'Generate & Download PDF' }}
      </a-button>

      <!-- Info Message -->
      <div class="info-message" v-if="!currentUser">
        <InfoCircleOutlined />
        Please log in to generate reports
      </div>

      <!-- Success/Error Messages -->
      <a-alert
        v-if="successMessage"
        :message="successMessage"
        type="success"
        show-icon
        closable
        @close="successMessage = ''"
        style="margin-top: 12px"
      />

      <a-alert
        v-if="errorMessage"
        :message="errorMessage"
        type="error"
        show-icon
        closable
        @close="errorMessage = ''"
        style="margin-top: 12px"
      />

      <!-- Report Info -->
      <div class="report-info">
        <div class="info-item">
          <CheckCircleOutlined class="info-icon success" />
          <span>Includes task details</span>
        </div>
        <div class="info-item">
          <PieChartOutlined class="info-icon primary" />
          <span>Visual status breakdown</span>
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
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.header-icon {
  color: #1890ff;
  font-size: 20px;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-weight: 500;
  color: #262626;
  font-size: 14px;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 12px;
  background-color: #fafafa;
  border-radius: 6px;
  border: 1px solid #d9d9d9;
}

.generate-button {
  margin-top: 8px;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
}

.info-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background-color: #f0f0f0;
  border-radius: 6px;
  color: #595959;
  font-size: 14px;
}

.report-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 6px;
  margin-top: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #595959;
}

.info-icon {
  font-size: 16px;
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
