<template>
  <a-card :bordered="false" class="report-card">
    <template #title>
      <div class="card-header">
        <FileTextOutlined class="header-icon" />
        <span>Generate Report</span>
      </div>
    </template>

    <div class="report-content">
      <!-- Role Information -->
      <div class="role-info" v-if="currentUser">
        <a-tag :color="getRoleColor(currentUser.role)" class="role-tag">
          {{ currentUser.role }}
        </a-tag>
        <span class="department-info">{{ currentUser.department }}</span>
      </div>

      <!-- Report Type Selection (only show if user has multiple options) -->
      <div class="filter-section" v-if="reportOptions.available_report_types.length > 1">
        <label class="filter-label">Report Type</label>
        <a-select v-model:value="selectedReportType" :style="{ width: '100%' }" :disabled="isGenerating"
          @change="onReportTypeChange">
          <a-select-option v-for="type in reportOptions.available_report_types" :key="type" :value="type">
            {{ formatReportType(type) }}
          </a-select-option>
        </a-select>
      </div>

      <!-- INDIVIDUAL REPORT FILTERS -->
      <div v-if="selectedReportType === 'individual'">
        <!-- For HR selecting individuals -->
        <div class="filter-section" v-if="currentUser?.role === 'HR'">
          <label class="filter-label">Select Individual</label>
          <a-select v-model:value="selectedIndividual" :style="{ width: '100%' }" :disabled="isGenerating"
            placeholder="Select an individual to analyze" show-search :filter-option="filterIndividualOption">
            <a-select-option v-for="individual in availableIndividuals" :key="individual.user_id"
              :value="individual.user_id">
              {{ individual.name }} ({{ individual.department }}) - {{ individual.role }}
            </a-select-option>
          </a-select>
          <div class="filter-hint">
            <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
            Generate detailed task report for any team member in the organization
          </div>
        </div>

        <!-- For Director selecting department members -->
        <div class="filter-section" v-if="currentUser?.role === 'Director'">
          <label class="filter-label">Select Individual</label>
          <a-select v-model:value="selectedIndividual" :style="{ width: '100%' }" :disabled="isGenerating"
            placeholder="Select yourself or a department member">
            <!-- Self option -->
            <a-select-option :value="currentUser.user_id">
              {{ currentUser.name }} (Me)
            </a-select-option>
            <!-- Department members -->
            <a-select-option v-for="member in departmentMembers" :key="member.user_id" :value="member.user_id">
              {{ member.name }} ({{ member.role }})
            </a-select-option>
          </a-select>
          <div class="filter-hint">
            <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
            Generate detailed task report for yourself or anyone in your department
          </div>
        </div>

        <!-- For Manager selecting subordinates -->
        <div class="filter-section" v-if="currentUser?.role === 'Manager'">
          <label class="filter-label">Select Team Member</label>
          <a-select v-model:value="selectedIndividual" :style="{ width: '100%' }" :disabled="isGenerating"
            placeholder="Select yourself or a team member">
            <!-- Self option -->
            <a-select-option :value="currentUser.user_id">
              {{ currentUser.name }} (Me)
            </a-select-option>
            <!-- Team members -->
            <a-select-option v-for="member in teamMembers" :key="member.user_id" :value="member.user_id">
              {{ member.name }}
            </a-select-option>
          </a-select>
          <div class="filter-hint">
            <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
            Generate detailed task report for yourself or your team members
          </div>
        </div>
      </div>

      <!-- TEAM REPORT FILTERS -->
      <div v-if="selectedReportType === 'team'">
        <!-- For Manager (their own team) -->
        <div class="filter-section" v-if="currentUser?.role === 'Manager'">
          <div class="filter-hint">
            <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
            Generating report for your team
          </div>
        </div>

        <!-- For Director and HR (select a team) -->
        <div class="filter-section" v-if="currentUser?.role === 'Director' || currentUser?.role === 'HR'">
          <label class="filter-label">Select Team</label>
          <a-select v-model:value="selectedTeam" :style="{ width: '100%' }" :disabled="isGenerating"
            placeholder="Select a team to analyze">
            <a-select-option v-for="team in reportOptions.teams" :key="team" :value="team">
              {{ team }}
            </a-select-option>
          </a-select>
          <div class="filter-hint">
            <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
            Analyze performance metrics for the selected team
          </div>
        </div>
      </div>

      <!-- DEPARTMENT REPORT FILTERS -->
      <div v-if="selectedReportType === 'department'">
        <!-- For Director: Team Selection within their department -->
        <div class="filter-section" v-if="currentUser?.role === 'Director'">
          <label class="filter-label">Select Teams in Your Department</label>
          <a-select v-model:value="selectedTeams" mode="multiple" :style="{ width: '100%' }" :disabled="isGenerating"
            placeholder="Select teams to compare (leave empty for all teams)" allow-clear>
            <a-select-option v-for="team in reportOptions.teams" :key="team" :value="team">
              {{ team }}
            </a-select-option>
          </a-select>
          <div class="filter-hint">
            <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
            Compare completion rates, overdue percentages, and time spent across teams
          </div>
        </div>

        <!-- For HR: Department Selection -->
        <div class="filter-section" v-if="currentUser?.role === 'HR'">
          <label class="filter-label">Select Department</label>
          <a-select v-model:value="selectedDepartment" :style="{ width: '100%' }" :disabled="isGenerating"
            placeholder="Select a department to analyze">
            <a-select-option v-for="dept in reportOptions.departments" :key="dept" :value="dept">
              {{ dept }}
            </a-select-option>
          </a-select>
          <div class="filter-hint">
            <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
            Analyze department-wide performance metrics
          </div>
        </div>
      </div>

      <!-- ORGANIZATION REPORT FILTERS -->
      <div v-if="selectedReportType === 'organization' && currentUser?.role === 'HR'" class="hr-organization-filters">
        <!-- Analysis Scope Type -->
        <div class="filter-section">
          <label class="filter-label">Analysis Scope</label>
          <a-radio-group v-model:value="scopeType" :disabled="isGenerating" @change="onScopeTypeChange">
            <a-radio-button value="departments">All Departments</a-radio-button>
            <a-radio-button value="teams">All Teams</a-radio-button>
            <a-radio-button value="individuals">Multiple Individuals</a-radio-button>
          </a-radio-group>
        </div>

        <!-- Department Selection (for organization scope) -->
        <div class="filter-section" v-if="scopeType === 'departments'">
          <label class="filter-label">Select Departments</label>
          <a-select v-model:value="selectedDepartments" mode="multiple" :style="{ width: '100%' }"
            :disabled="isGenerating" placeholder="Select specific departments (at least one team)"
            allow-clear>
            <a-select-option v-for="dept in reportOptions.departments" :key="dept" :value="dept">
              {{ dept }}
            </a-select-option>
          </a-select>
        </div>

        <!-- Team Selection (for organization scope) -->
        <div class="filter-section" v-if="scopeType === 'teams'">
          <label class="filter-label">Select Teams</label>
          <a-select v-model:value="selectedTeams" mode="multiple" :style="{ width: '100%' }" :disabled="isGenerating"
            placeholder="Select specific teams (at least one team)" allow-clear>
            <a-select-option v-for="team in reportOptions.teams" :key="team" :value="team">
              {{ team }}
            </a-select-option>
          </a-select>
        </div>

        <!-- Individual Selection (for organization scope) -->
        <div class="filter-section" v-if="scopeType === 'individuals'">
          <label class="filter-label">Select Individuals</label>
          <a-select v-model:value="selectedIndividuals" mode="multiple" :style="{ width: '100%' }"
            :disabled="isGenerating" placeholder="Select individuals to compare (at least one individual)" show-search
            :filter-option="filterIndividualOption">
            <a-select-option v-for="individual in availableIndividuals" :key="individual.user_id"
              :value="individual.user_id">
              {{ individual.name }} ({{ individual.department }}) - {{ individual.role }}
            </a-select-option>
          </a-select>
        </div>

        <div class="filter-hint">
          <InfoCircleOutlined style="color: #1890ff; margin-right: 4px;" />
          Generate comprehensive organization-wide performance analysis
        </div>
      </div>

      <!-- Date Range Picker -->
      <div class="filter-section">
        <label class="filter-label">Date Range</label>
        <a-range-picker v-model:value="dateRange" format="YYYY-MM-DD" :style="{ width: '100%' }"
          :disabled="isGenerating" />
      </div>

      <!-- Status Filter -->
      <div class="filter-section">
        <label class="filter-label">Task Status</label>
        <a-checkbox-group v-model:value="statusFilter" :style="{ width: '100%' }" :disabled="isGenerating">
          <div class="checkbox-grid">
            <a-checkbox value="Unassigned">Unassigned</a-checkbox>
            <a-checkbox value="Ongoing">Ongoing</a-checkbox>
            <a-checkbox value="Completed">Completed</a-checkbox>
            <a-checkbox value="Under Review">Under Review</a-checkbox>
          </div>
        </a-checkbox-group>
      </div>

      <!-- Generate Button -->
      <a-button type="primary" block size="large" :loading="isGenerating" :disabled="!currentUser || !canGenerateReport"
        @click="generateReport" class="generate-button">
        <template #icon>
          <DownloadOutlined v-if="!isGenerating" />
        </template>
        {{ isGenerating ? 'Generating Report...' : getGenerateButtonText() }}
      </a-button>

      <!-- Info Message -->
      <div class="info-message" v-if="!currentUser">
        <InfoCircleOutlined />
        Please log in to generate reports
      </div>

      <!-- Success/Error Messages -->
      <a-alert v-if="successMessage" :message="successMessage" type="success" show-icon closable
        @close="successMessage = ''" style="margin-top: 12px" />

      <a-alert v-if="errorMessage" :message="errorMessage" type="error" show-icon closable @close="errorMessage = ''"
        style="margin-top: 12px" />

      <!-- Role-Specific Report Info -->
      <div class="report-info">
        <div class="role-specific-info">
          <h4 class="info-title">{{ getRoleSpecificTitle() }}</h4>
          <div class="info-item" v-for="feature in getRoleSpecificFeatures()" :key="feature.text">
            <component :is="feature.icon" :class="`info-icon ${feature.color}`" />
            <span>{{ feature.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
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
  UserOutlined,
  PercentageOutlined,
  ClockCircleOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue'

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
    UserOutlined,
    PercentageOutlined,
    ClockCircleOutlined,
    BarChartOutlined
  },
  setup() {
    const authStore = useAuthStore()
    const currentUser = computed(() => authStore.user)

    const dateRange = ref(null)
    const statusFilter = ref([])
    const isGenerating = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')

    // Enhanced state for role-based reporting
    const reportOptions = ref({
      user_role: '',
      available_report_types: [],
      departments: [],
      teams: []
    })
    const selectedReportType = ref('individual')
    const selectedDepartments = ref([])
    const selectedTeams = ref([])
    const selectedIndividuals = ref([])
    const selectedIndividual = ref(null) // Single individual selection
    const selectedTeam = ref(null) // Single team selection
    const selectedDepartment = ref(null) // Single department selection
    const scopeType = ref('departments')
    const availableIndividuals = ref([])
    const teamMembers = ref([])
    const departmentMembers = ref([])

    // Computed properties
    const canGenerateReport = computed(() => {
      if (!currentUser.value) return false

      const role = currentUser.value.role

      // Individual report validations
      if (selectedReportType.value === 'individual') {
        if (role === 'HR' || role === 'Director') {
          return selectedIndividual.value !== null
        }
        return true // Staff and Manager can always generate their own report
      }

      // Team report validations
      if (selectedReportType.value === 'team') {
        if (role === 'Manager') {
          return true // Managers don't need to select - it's automatically their team
        }
        return selectedTeam.value !== null // Directors and HR need to select a team
      }

      // Department report validations
      if (selectedReportType.value === 'department') {
        if (role === 'HR') {
          return selectedDepartment.value !== null
        }
        return true // Director can generate for their department
      }

      // Organization report validations
      if (selectedReportType.value === 'organization' && role === 'HR') {
        if (scopeType.value === 'individuals') {
          return selectedIndividuals.value.length > 0
        }
        return true
      }

      return true
    })

    // Methods
    const fetchReportOptions = async () => {
      if (!currentUser.value) return

      try {
        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'
        const response = await fetch(`${reportServiceUrl}/report-options?user_id=${currentUser.value.user_id}`)

        if (response.ok) {
          const options = await response.json()
          reportOptions.value = options
          selectedReportType.value = options.available_report_types[0] || 'individual'

          // Set default report type based on role
          if (currentUser.value.role === 'Director') {
            selectedReportType.value = 'department'
          } else if (currentUser.value.role === 'HR') {
            selectedReportType.value = 'organization'
          }

          // Set default individual for Staff
          if (currentUser.value.role === 'Staff') {
            selectedIndividual.value = currentUser.value.user_id
          }
        }
      } catch (error) {
        console.error('Error fetching report options:', error)
      }
    }

    const fetchAvailableIndividuals = async () => {
      if (!currentUser.value || (currentUser.value.role !== 'HR' && currentUser.value.role !== 'Manager')) return

      try {
        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'
        const response = await fetch(`${reportServiceUrl}/available-users`)

        if (response.ok) {
          const users = await response.json()
          availableIndividuals.value = users

          // For managers, filter to get team members
          if (currentUser.value.role === 'Manager') {
            teamMembers.value = users.filter(user =>
              user.superior === currentUser.value.user_id ||
              user.user_id === currentUser.value.user_id
            )
          }
        }
      } catch (error) {
        console.error('Error fetching available individuals:', error)
      }
    }

    const getRoleColor = (role) => {
      const colors = {
        'Staff': 'blue',
        'Manager': 'green',
        'Director': 'orange',
        'HR': 'purple'
      }
      return colors[role] || 'default'
    }

    const formatReportType = (type) => {
      const formats = {
        'individual': 'Individual Report',
        'team': 'Team Report',
        'department': 'Department Report',
        'organization': 'Organization Report'
      }
      return formats[type] || type
    }

    const onReportTypeChange = () => {
      // Reset all selections when report type changes
      selectedDepartments.value = []
      selectedTeams.value = []
      selectedIndividuals.value = []
      selectedIndividual.value = null
      selectedTeam.value = null
      selectedDepartment.value = null
      scopeType.value = 'departments'

      // Set defaults based on new report type and role
      if (selectedReportType.value === 'individual') {
        if (currentUser.value?.role === 'Staff') {
          selectedIndividual.value = currentUser.value.user_id
        } else if (currentUser.value?.role === 'Director' || currentUser.value?.role === 'Manager') {
          // Directors and Managers default to their own report
          selectedIndividual.value = currentUser.value.user_id
        }
      }

      // Fetch data if needed
      if (selectedReportType.value === 'individual' ||
        (selectedReportType.value === 'organization' && scopeType.value === 'individuals')) {
        fetchAvailableIndividuals()
      }
    }
    const onScopeTypeChange = () => {
      // Reset selections when scope type changes
      selectedDepartments.value = []
      selectedTeams.value = []
      selectedIndividuals.value = []

      if (scopeType.value === 'individuals') {
        fetchAvailableIndividuals()
      }
    }

    const filterIndividualOption = (input, option) => {
      return option.children.toLowerCase().includes(input.toLowerCase())
    }

    const getGenerateButtonText = () => {
      const role = currentUser.value?.role
      const reportType = selectedReportType.value

      if (reportType === 'individual') {
        return role === 'Staff' ? 'Generate My Task Report' : 'Generate Individual Report'
      } else if (reportType === 'team') {
        return 'Generate Team Report'
      } else if (reportType === 'department') {
        return role === 'Director' ? 'Generate Department Performance Report' : 'Generate Department Report'
      } else if (reportType === 'organization') {
        return `Generate ${scopeType.value.charAt(0).toUpperCase() + scopeType.value.slice(1)} Analysis`
      }

      return 'Generate Report'
    }

    const getRoleSpecificTitle = () => {
      const reportType = selectedReportType.value

      if (reportType === 'individual') {
        return 'Individual Task Analysis'
      } else if (reportType === 'team') {
        return 'Team Performance Analysis'
      } else if (reportType === 'department') {
        return 'Department Performance Analytics'
      } else if (reportType === 'organization') {
        return 'Organization-Wide Analysis'
      }

      return 'Report Features'
    }

    const getRoleSpecificFeatures = () => {
      const reportType = selectedReportType.value

      if (reportType === 'individual') {
        return [
          { icon: CheckCircleOutlined, color: 'success', text: 'Personal task completion tracking' },
          { icon: PieChartOutlined, color: 'primary', text: 'Task status distribution' },
          { icon: CalendarOutlined, color: 'secondary', text: 'Time spent analysis' }
        ]
      } else if (reportType === 'team') {
        return [
          { icon: TeamOutlined, color: 'primary', text: 'Team productivity metrics' },
          { icon: PercentageOutlined, color: 'success', text: 'Team completion rates' },
          { icon: ClockCircleOutlined, color: 'warning', text: 'Team time tracking' }
        ]
      } else if (reportType === 'department') {
        return [
          { icon: PercentageOutlined, color: 'success', text: 'Team completion rates comparison' },
          { icon: ClockCircleOutlined, color: 'warning', text: 'Overdue task percentages by team' },
          { icon: BarChartOutlined, color: 'info', text: 'Total time spent per team' },
          { icon: TeamOutlined, color: 'primary', text: 'Multi-team performance analysis' }
        ]
      } else if (reportType === 'organization') {
        return [
          { icon: BankOutlined, color: 'primary', text: 'Organization-wide metrics' },
          { icon: TeamOutlined, color: 'info', text: 'Cross-department analysis' },
          { icon: UserOutlined, color: 'success', text: 'Individual performance insights' },
          { icon: BarChartOutlined, color: 'warning', text: 'Comprehensive reporting flexibility' }
        ]
      }

      return []
    }

    const fetchDepartmentMembers = async () => {
      if (!currentUser.value || currentUser.value.role !== 'Director') return

      try {
        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'
        const response = await fetch(`${reportServiceUrl}/available-users`)

        if (response.ok) {
          const users = await response.json()
          // Filter to only department members (excluding self)
          departmentMembers.value = users.filter(user =>
            user.department === currentUser.value.department &&
            user.user_id !== currentUser.value.user_id
          )
        }
      } catch (error) {
        console.error('Error fetching department members:', error)
      }
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
    const role = currentUser.value.role

    // Build request body based on report type and selection
    const requestBody = {
      requesting_user_id: currentUser.value.user_id,
      report_type: selectedReportType.value,
      status_filter: statusFilter.value.length > 0 ? statusFilter.value : ['All']
    }

    // Add date range if selected
    if (dateRange.value && dateRange.value.length === 2) {
      requestBody.start_date = dateRange.value[0].format('YYYY-MM-DD')
      requestBody.end_date = dateRange.value[1].format('YYYY-MM-DD')
    }

    // Report type specific request body setup
    if (selectedReportType.value === 'individual') {
      const targetUserId = selectedIndividual.value || currentUser.value.user_id
      requestBody.user_id = targetUserId

      // Get user name for the target user
      if (targetUserId === currentUser.value.user_id) {
        requestBody.user_name = currentUser.value.name
      } else {
        const targetUser = availableIndividuals.value.find(u => u.user_id === targetUserId) ||
          teamMembers.value.find(u => u.user_id === targetUserId) ||
          departmentMembers.value.find(u => u.user_id === targetUserId)
        requestBody.user_name = targetUser?.name || 'Unknown User'
      }
    } 
    else if (selectedReportType.value === 'team') {
      if (role === 'Manager') {
        // For managers, don't send teams array - let backend handle it
        // The backend will automatically get their team members
      } else if (role === 'Director' || role === 'HR') {
        // Only send teams array for Director/HR who need to select a team
        if (!selectedTeam.value) {
          message.error('Please select a team')
          return
        }
        requestBody.teams = [selectedTeam.value]
      }
    } 
    else if (selectedReportType.value === 'department') {
      if (role === 'Director') {
        requestBody.department = currentUser.value.department
        if (selectedTeams.value.length > 0) {
          requestBody.teams = selectedTeams.value
        }
      } else if (role === 'HR') {
        if (!selectedDepartment.value) {
          message.error('Please select a department')
          return
        }
        requestBody.department = selectedDepartment.value
      }
    } 
    else if (selectedReportType.value === 'organization' && role === 'HR') {
      requestBody.scope_type = scopeType.value

      if (scopeType.value === 'departments' && selectedDepartments.value.length > 0) {
        requestBody.scope_values = selectedDepartments.value
      } else if (scopeType.value === 'teams' && selectedTeams.value.length > 0) {
        requestBody.scope_values = selectedTeams.value
      } else if (scopeType.value === 'individuals' && selectedIndividuals.value.length > 0) {
        requestBody.scope_values = selectedIndividuals.value
      }
    }

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

    // Download the PDF
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0]
    let filename = `${selectedReportType.value}_report_${timestamp}.pdf`

    if (selectedReportType.value === 'organization') {
      filename = `organization_${scopeType.value}_report_${timestamp}.pdf`
    }

    a.download = filename

    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    successMessage.value = `Report generated successfully!`
    message.success('Report downloaded successfully!')

  } catch (error) {
    console.error('Error generating report:', error)
    errorMessage.value = error.message || 'Failed to generate report. Please try again.'
    message.error('Failed to generate report')
  } finally {
    isGenerating.value = false
  }
}

// Lifecycle hooks
onMounted(() => {
  fetchReportOptions()
  fetchAvailableIndividuals()
  fetchDepartmentMembers()  // Add this line
})

watch(currentUser, (newUser) => {
  if (newUser) {
    fetchReportOptions()
    fetchAvailableIndividuals()
    fetchDepartmentMembers()  // Add this line
  }
})

return {
  currentUser,
  dateRange,
  statusFilter,
  isGenerating,
  successMessage,
  errorMessage,
  reportOptions,
  selectedReportType,
  selectedDepartments,
  selectedTeams,
  selectedIndividuals,
  selectedIndividual,
  selectedTeam,
  selectedDepartment,
  scopeType,
  availableIndividuals,
  teamMembers,
  canGenerateReport,
  getRoleColor,
  formatReportType,
  onReportTypeChange,
  onScopeTypeChange,
  filterIndividualOption,
  getGenerateButtonText,
  getRoleSpecificTitle,
  getRoleSpecificFeatures,
  generateReport
}
  }
}
</script>

<style scoped>
.role-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px;
  background-color: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.role-tag {
  font-weight: 600;
  font-size: 12px;
}

.department-info {
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
}

.hr-organization-filters {
  padding: 16px;
  background-color: #f0f5ff;
  border-radius: 6px;
  border: 1px solid #d6e4ff;
  margin-bottom: 12px;
}

.filter-hint {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #e6f7ff;
  border-radius: 4px;
  font-size: 12px;
  color: #1890ff;
}

.role-specific-info {
  background-color: #f8fafc;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.info-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

/* Keep existing styles */
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

.info-icon.info {
  color: #13c2c2;
}

.info-icon.warning {
  color: #fa8c16;
}
</style>
