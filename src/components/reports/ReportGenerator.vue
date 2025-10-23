<template>
  <a-card :bordered="false" class="report-card">
    <template #title>
      <div class="card-header">
        <FileTextOutlined class="header-icon" />
        <span>Generate Report</span>
      </div>
    </template>

    <div class="report-content">
      <!-- User Role Info -->
      <div v-if="currentUser" class="role-info">
      <a-tag :color="getRoleColor(currentUser.role)" class="role-tag">
        {{ currentUser.role || 'Staff' }}
      </a-tag>
      <span class="department-info">
        {{ currentUser.department || 'No Department' }}
      </span>
      </div>

      <!-- Report Type Selection (for non-Staff users) -->
      <div v-if="canSelectReportType" class="filter-section">
      <label class="filter-label">Report Type</label>
      <a-select
        v-model:value="reportType"
        :style="{ width: '100%' }"
        :disabled="isGenerating"
        @change="onReportTypeChange"
      >
        <a-select-option value="individual">Individual Report</a-select-option>
        <a-select-option v-if="canGenerateTeamReports" value="team">Team Report</a-select-option>
        <a-select-option v-if="canGenerateDepartmentReports" value="department">Department Report</a-select-option>
        <a-select-option v-if="isHR" value="organization">Organization Report</a-select-option>
      </a-select>
      </div>

      <!-- Target Selection (for Managers/Directors/HR generating individual reports) -->
      <div v-if="showTargetSelection" class="filter-section">
      <label class="filter-label">
        {{ reportType === 'individual' ? 'Target User' : 'Target Selection' }}
      </label>
      <a-select
        v-model:value="selectedTargets"
        :style="{ width: '100%' }"
        :mode="reportType === 'individual' ? 'default' : 'multiple'"
        :placeholder="getTargetPlaceholder()"
        :disabled="isGenerating || isLoadingOptions"
        :loading="isLoadingOptions"
      >
        <a-select-option
        v-for="option in availableTargets"
        :key="option.value"
        :value="option.value"
        >
        {{ option.label }}
        </a-select-option>
      </a-select>
      </div>

      <!-- HR Organization Filters -->
      <div v-if="isHR && reportType === 'organization'" class="hr-organization-filters">
      <div class="filter-section">
        <label class="filter-label">Trend Interval</label>
        <a-select
        v-model:value="trendGranularity"
        :style="{ width: '100%' }"
        :disabled="isGenerating"
        >
        <a-select-option value="monthly">Monthly</a-select-option>
        <a-select-option value="weekly">Weekly</a-select-option>
        <a-select-option value="daily">Daily</a-select-option>
        </a-select>
      </div>

      <div class="filter-hint">
        <InfoCircleOutlined />
        <span>Organization report compares departments and highlights trends for the selected interval</span>
      </div>
      </div>

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
      :loading="isGeneratingPreview"
      :disabled="!canGenerate"
      @click="generatePreview"
      class="generate-button"
      >
      <template #icon>
        <FileTextOutlined v-if="!isGeneratingPreview" />
      </template>
      {{ isGeneratingPreview ? 'Generating Preview...' : 'Generate Preview' }}
      </a-button>

      <!-- Preview Modal -->
      <ReportPreviewModal 
      :isOpen="showPreviewModal"
      :reportData="previewData"
      @close="handleClosePreview"
      @export="generateReport"
      />

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

      <!-- Role-specific Report Info -->
      <div class="role-specific-info">
      <h4 class="info-title">Available Features for {{ currentUser?.role || 'Staff' }}</h4>
      <div class="report-info">
        <div class="info-item">
        <CheckCircleOutlined class="info-icon success" />
        <span>Individual task reports</span>
        </div>
        <div v-if="canGenerateTeamReports" class="info-item">
        <TeamOutlined class="info-icon primary" />
        <span>Team performance reports</span>
        </div>
        <div v-if="canGenerateDepartmentReports" class="info-item">
        <BankOutlined class="info-icon secondary" />
        <span>Department analysis</span>
        </div>
        <div v-if="isHR" class="info-item">
        <GlobalOutlined class="info-icon warning" />
        <span>Organization-wide insights</span>
        </div>
        <div class="info-item">
        <PieChartOutlined class="info-icon primary" />
        <span>Visual analytics & charts</span>
        </div>
        <div class="info-item">
        <CalendarOutlined class="info-icon secondary" />
        <span>Duration & deadline tracking</span>
        </div>
        <div class="info-item">
        <FilterOutlined class="info-icon info" />
        <span>Advanced filtering options</span>
        </div>
      </div>
      </div>
    </div>
  </a-card>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { message } from 'ant-design-vue'
import {
  FileTextOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  PieChartOutlined,
  CalendarOutlined,
  TeamOutlined,
  BankOutlined,
  GlobalOutlined,
  FilterOutlined
} from '@ant-design/icons-vue'
import ReportPreviewModal from './ReportPreviewModal.vue'

export default {
  name: 'ReportGenerator',
  components: {
    FileTextOutlined,
    DownloadOutlined,
    InfoCircleOutlined,
    CheckCircleOutlined,
    PieChartOutlined,
    CalendarOutlined,
    TeamOutlined,
    BankOutlined,
    GlobalOutlined,
    FilterOutlined,
    ReportPreviewModal
  },
  setup() {
    const authStore = useAuthStore()
    const currentUser = computed(() => authStore.user)

    // Basic filters
    const dateRange = ref(null)
    const statusFilter = ref([])
    const isGenerating = ref(false)
    const isGeneratingPreview = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')

    // Preview data and modal
    const previewData = ref(null)
    const showPreviewModal = ref(false)

    // Advanced role-based filters
    const reportType = ref('individual')
    const selectedTargets = ref(null)
    const availableTargets = ref([])
    const isLoadingOptions = ref(false)
    const trendGranularity = ref('monthly')

    // Team member table columns
    const teamMemberColumns = [
      {
        title: 'Name',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: 'Total Tasks',
        dataIndex: 'total_tasks',
        key: 'total_tasks',
        align: 'center'
      },
      {
        title: 'Completed',
        dataIndex: 'completed',
        key: 'completed',
        align: 'center'
      },
      {
        title: 'In Progress',
        dataIndex: 'in_progress',
        key: 'in_progress',
        align: 'center'
      },
      {
        title: 'Overdue',
        dataIndex: 'overdue',
        key: 'overdue',
        align: 'center'
      },
      {
        title: 'Completion Rate',
        dataIndex: 'completion_rate',
        key: 'completion_rate',
        align: 'center'
      }
    ]

    // User role computed properties
    const userRole = computed(() => currentUser.value?.role || 'Staff')
    const isStaff = computed(() => userRole.value === 'Staff')
    const isManager = computed(() => userRole.value === 'Manager')
    const isDirector = computed(() => userRole.value === 'Director')
    const isHR = computed(() => userRole.value === 'HR')

    // Role-based permissions
    const canSelectReportType = computed(() => !isStaff.value)
    const canGenerateTeamReports = computed(() => isManager.value || isDirector.value || isHR.value)
    const canGenerateDepartmentReports = computed(() => isDirector.value || isHR.value)

    // UI state
    const showTargetSelection = computed(() => {
      if (reportType.value === 'individual' && (isManager.value || isDirector.value || isHR.value)) {
        return true
      }
      if (reportType.value === 'team' && (isDirector.value || isHR.value)) {
        return true
      }
      if (reportType.value === 'department' && isHR.value) {
        return true
      }
      return false
    })

    const canGenerate = computed(() => {
      if (!currentUser.value) return false
      
      // Staff can always generate their own reports
      if (isStaff.value) return true
      
      // For team reports, target selection is mandatory
      if (reportType.value === 'team' && (!selectedTargets.value || (Array.isArray(selectedTargets.value) && selectedTargets.value.length === 0))) {
        return false
      }
      
      // For other roles, check if required selections are made
        if (showTargetSelection.value && !selectedTargets.value) return false
      
      return true
    })

    // Role color mapping
    const getRoleColor = (role) => {
      const colors = {
        'Staff': 'blue',
        'Manager': 'green',
        'Director': 'orange',
        'HR': 'red'
      }
      return colors[role] || 'default'
    }

    const getTargetPlaceholder = () => {
      if (reportType.value === 'individual') return 'Select a user'
      if (reportType.value === 'team') return 'Select at least ONE team'
      if (reportType.value === 'department') return 'Select departments'
      return 'Select targets'
    }

    // Load available options based on user role and report type
    const loadAvailableTargets = async () => {
      if (!showTargetSelection.value) return

      isLoadingOptions.value = true
      try {
        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'
        const response = await fetch(`${reportServiceUrl}/report-options?user_id=${currentUser.value.user_id}&report_type=${reportType.value}`)
        
          if (response.ok) {
            const data = await response.json()
            const options = (data.options || []).filter(option => option && option.value)
            availableTargets.value = options
        } else {
          console.error('Failed to load report options')
          availableTargets.value = []
        }
      } catch (error) {
        console.error('Error loading report options:', error)
        availableTargets.value = []
      } finally {
        isLoadingOptions.value = false
      }
    }

    // Event handlers
    const onReportTypeChange = () => {
      // Reset selection based on report type - start empty for user selection
      if (reportType.value === 'team' || reportType.value === 'department') {
        selectedTargets.value = []  // Empty array for multi-select
      } else {
        selectedTargets.value = null  // Null for single select
      }
      trendGranularity.value = 'monthly'
      loadAvailableTargets()  // Load options but don't auto-select
    }

    const generatePreview = async () => {
      if (!currentUser.value) {
        message.error('Please log in to generate reports')
        return
      }

      isGeneratingPreview.value = true
      errorMessage.value = ''
      successMessage.value = ''

      try {
        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'

        // Prepare request body for preview
        const requestBody = {
          requesting_user_id: currentUser.value.user_id,
          user_name: currentUser.value.name || 'Unknown User',
          report_type: reportType.value,
          status_filter: statusFilter.value.length > 0 ? statusFilter.value : ['All']
        }

        // Add target selection for non-staff users
      if (reportType.value === 'individual' && selectedTargets.value) {
        requestBody.user_id = selectedTargets.value
      } else if (reportType.value === 'team' && selectedTargets.value) {
        requestBody.teams = Array.isArray(selectedTargets.value) ? selectedTargets.value : [selectedTargets.value]
      } else if (reportType.value === 'department' && selectedTargets.value) {
        requestBody.departments = Array.isArray(selectedTargets.value) ? selectedTargets.value : [selectedTargets.value]
      } else if (reportType.value === 'organization' && isHR.value) {
        requestBody.trend_granularity = trendGranularity.value
      }

        // Add date range if selected
        if (dateRange.value && dateRange.value.length === 2) {
          requestBody.start_date = dateRange.value[0].format('YYYY-MM-DD')
          requestBody.end_date = dateRange.value[1].format('YYYY-MM-DD')
        }

        // Make request to preview endpoint
        const response = await fetch(`${reportServiceUrl}/preview-report`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody)
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to generate preview')
        }

        const data = await response.json()
        previewData.value = data
        showPreviewModal.value = true
        message.success('Preview generated successfully!')

      } catch (error) {
        console.error('Error generating preview:', error)
        errorMessage.value = error.message || 'Failed to generate preview. Please try again.'
        message.error('Failed to generate preview')
      } finally {
        isGeneratingPreview.value = false
      }
    }

    const clearPreview = () => {
      previewData.value = null
      showPreviewModal.value = false
      successMessage.value = ''
      errorMessage.value = ''
    }

    const handleClosePreview = () => {
      showPreviewModal.value = false
    }

    const getReportTitle = () => {
      if (!previewData.value) return 'Report'
      
      const typeLabels = {
        'individual': 'Individual Report',
        'team': 'Team Report', 
        'department': 'Department Report',
        'organization': 'Organization Report'
      }
      
      return typeLabels[previewData.value.report_type] || 'Report'
    }

    const getTargetLabel = () => {
      if (!previewData.value) return ''
      
      const type = previewData.value.report_type
      if (type === 'individual') return 'Target User'
      if (type === 'team') return 'Team'
      if (type === 'department') return 'Department'
      if (type === 'organization') return 'Organization Scope'
      return 'Target'
    }

    const getTargetInfo = () => {
      if (!previewData.value) return ''
      
      const summary = previewData.value.summary
      if (summary.target_user) return summary.target_user
      if (summary.selected_teams?.length) return summary.selected_teams.join(', ')
      if (summary.team_name) return summary.team_name
      if (summary.department) return summary.department
      if (summary.scope_type) {
        if (summary.scope_type === 'Organization' && summary.trend_granularity) {
          const trendLabel = summary.trend_granularity.charAt(0).toUpperCase() + summary.trend_granularity.slice(1)
          return `${summary.scope_type} (${trendLabel} trend)`
        }
        return `${summary.scope_type} analysis`
      }
      return ''
    }

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

        // Prepare request body based on user role and report type
        const requestBody = {
          requesting_user_id: currentUser.value.user_id,
          user_name: currentUser.value.name || 'Unknown User',
          report_type: reportType.value,
          status_filter: statusFilter.value.length > 0 ? statusFilter.value : ['All']
        }

        // Add target selection for non-staff users
      if (reportType.value === 'individual' && selectedTargets.value) {
        requestBody.user_id = selectedTargets.value
      } else if (reportType.value === 'team' && selectedTargets.value) {
        requestBody.teams = Array.isArray(selectedTargets.value) ? selectedTargets.value : [selectedTargets.value]
      } else if (reportType.value === 'department' && selectedTargets.value) {
        requestBody.departments = Array.isArray(selectedTargets.value) ? selectedTargets.value : [selectedTargets.value]
      } else if (reportType.value === 'organization' && isHR.value) {
        requestBody.trend_granularity = trendGranularity.value
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
        const reportTypeText = reportType.value.replace('_', '-')
        a.download = `${reportTypeText}_report_${userName}_${timestamp}.pdf`

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

    // Watchers
    watch(() => reportType.value, () => {
      onReportTypeChange()
      clearPreview() // Clear preview when report type changes
    })

    watch(() => selectedTargets.value, () => {
      clearPreview() // Clear preview when targets change
    })

    watch(() => dateRange.value, () => {
      clearPreview() // Clear preview when date range changes
    })

    watch(() => statusFilter.value, () => {
      clearPreview() // Clear preview when status filter changes
    })

    watch(() => trendGranularity.value, () => {
      clearPreview()
    })

    // Load initial data
    onMounted(() => {
      if (showTargetSelection.value) {
        // Load available targets but don't auto-select - let user choose
        loadAvailableTargets()
      }
    })

    return {
      currentUser,
      dateRange,
      statusFilter,
      isGenerating,
      isGeneratingPreview,
      successMessage,
      errorMessage,
      previewData,
      showPreviewModal,
      reportType,
      selectedTargets,
      availableTargets,
      isLoadingOptions,
      trendGranularity,
      teamMemberColumns,
      userRole,
      isStaff,
      isManager,
      isDirector,
      isHR,
      canSelectReportType,
      canGenerateTeamReports,
      canGenerateDepartmentReports,
      showTargetSelection,
      canGenerate,
      getRoleColor,
      getTargetPlaceholder,
      onReportTypeChange,
      generatePreview,
      clearPreview,
      handleClosePreview,
      getReportTitle,
      getTargetLabel,
      getTargetInfo,
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

/* Role-based styling additions */
.role-info-container {
  margin-bottom: 24px;
}

.role-tag {
  margin-right: 8px;
}

.permissions-list {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
  margin-top: 8px;
}

.permissions-list li {
  margin-bottom: 4px;
  color: #666;
}

.permissions-list li:last-child {
  margin-bottom: 0;
}

.form-section {
  margin-bottom: 20px;
}

.form-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.form-row .ant-form-item {
  flex: 1;
  margin-bottom: 0;
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #262626;
}

.message-container {
  margin-top: 16px;
}

.success-message {
  color: #52c41a;
  text-align: center;
  font-weight: 500;
}

.error-message {
  color: #ff4d4f;
  text-align: center;
  font-weight: 500;
}

/* Role-specific styling */
.staff-role {
  border-left: 4px solid #1890ff;
}

.manager-role {
  border-left: 4px solid #52c41a;
}

.director-role {
  border-left: 4px solid #fa8c16;
}

.hr-role {
  border-left: 4px solid #f5222d;
}

/* Loading state styling */
.ant-select-loading {
  opacity: 0.7;
}

.loading-placeholder {
  color: #bfbfbf;
  font-style: italic;
}

/* Advanced filters styling */
.advanced-filters {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 16px;
  background: #fafafa;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

/* Enhanced visual hierarchy */
.report-type-section {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.target-selection-section {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.basic-filters-section {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
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
  
  .form-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .summary-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .preview-actions {
    flex-direction: column;
  }

  .preview-action-btn {
    width: 100%;
  }
}

/* Animation for role changes */
.role-transition {
  transition: all 0.3s ease;
}

/* Custom button states */
.generate-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.generate-button.generating {
  position: relative;
  overflow: hidden;
}

.generate-button.generating::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: loading-shine 1.5s infinite;
}

@keyframes loading-shine {
  0% { left: -100%; }
  100% { left: 100%; }
}
</style>
