<template>
  <div style="max-width: 1200px; margin: 0 auto; padding: 0px;">
    <!-- Loading State -->
    <div v-if="isLoading" style="text-align: center; padding: 50px;">
      <a-spin size="large" />
      <p style="margin-top: 16px;">Loading project details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" style="text-align: center; padding: 50px;">
      <a-result
        status="error"
        title="Failed to load project"
        :sub-title="error"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/projects')">
            Back to Projects
          </a-button>
        </template>
      </a-result>
    </div>

    <!-- Project Details Content -->
    <div v-else-if="project">
      <!-- Header -->
      <a-card :bordered="false" :style="headerStyle" style="margin-bottom: 24px;">
        <a-row :gutter="24" align="middle">
          <a-col :span="18">
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
              <a-button
                type="text"
                @click="$router.push('/projects')"
                style="padding: 4px;"
              >
                <template #icon>
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                  </svg>
                </template>
              </a-button>
              <a-typography-title :level="2" :style="titleStyle" style="margin: 0;">
                {{ project.project_name }}
              </a-typography-title>
              <a-tag :color="getStatusColor(project.status)" size="large">
                {{ getStatusText(project.status) }}
              </a-tag>
            </div>
            <a-typography-paragraph :style="subtitleStyle" style="margin: 0;">
              {{ project.project_description || 'No description available' }}
            </a-typography-paragraph>
          </a-col>
          <a-col :span="6" style="text-align: right;">
            <a-space direction="vertical" align="end">
              <a-space>
                <a-button type="default" @click="handleGenerateReport">
                  <template #icon>
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                  </template>
                  Generate Report
                </a-button>
                <a-button type="primary" @click="handleEdit">
                  <template #icon>
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </template>
                  Edit Project
                </a-button>
              </a-space>
              <a-button danger @click="handleDelete">
                <template #icon>
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </template>
                Delete Project
              </a-button>
            </a-space>
          </a-col>
        </a-row>
      </a-card>

      <!-- Project Information - Full Width -->
      <a-row style="margin-bottom: 24px;">
        <a-col :span="24">
          <a-card title="Project Information" size="small">
            <a-row :gutter="24">
              <a-col :span="6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Project ID
                  </label>
                  <p class="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-md font-mono">
                    {{ project.project_id }}
                  </p>
                </div>
              </a-col>
              <a-col :span="6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Created By
                  </label>
                  <p class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                    {{ project.created_by || 'Unknown' }}
                  </p>
                </div>
              </a-col>
              <a-col :span="6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Created Date
                  </label>
                  <p class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                    {{ formatFullDate(project.created_at) }}
                  </p>
                </div>
              </a-col>
              <a-col :span="6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Due Date
                  </label>
                  <p class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                    {{ formatFullDate(project.due_date) || 'No due date' }}
                  </p>
                </div>
              </a-col>
            </a-row>
          </a-card>
        </a-col>
      </a-row>

      <!-- Project Tasks -->
      <a-row style="margin-bottom: 24px;">
        <a-col :span="24">
          <a-card title="Project Tasks" size="small">
            <div v-if="isLoadingTasks" style="text-align: center; padding: 50px;">
              <a-spin size="large" />
              <p style="margin-top: 16px;">Loading tasks...</p>
            </div>

            <div v-else-if="projectTasks.length === 0" style="text-align: center; padding: 50px;">
              <a-empty description="No tasks assigned to this project yet" />
            </div>

            <a-row v-else :gutter="[16, 16]">
              <a-col
                v-for="task in projectTasks"
                :key="task.id"
                :span="8"
              >
                <TaskCard
                  :task="task"
                  @view-details="handleTaskClick"
                />
              </a-col>
            </a-row>
          </a-card>
        </a-col>
      </a-row>

    </div>

    <!-- Edit Project Modal -->
    <ProjectFormModal
      v-if="project"
      :isOpen="showEditModal"
      :project="project"
      @close="showEditModal = false"
      @save="handleProjectUpdated"
    />

    <!-- Task Detail Modal -->
    <TaskDetailModal
      v-if="selectedTask"
      :task="selectedTask"
      :isOpen="showTaskDetailModal"
      @close="closeTaskDetailModal"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notification } from 'ant-design-vue'
import { useTheme } from '../composables/useTheme.js'
import ProjectFormModal from '../components/projects/ProjectFormModal.vue'
import TaskCard from '../components/tasks/TaskCard.vue'
import TaskDetailModal from '../components/tasks/TaskDetailModal.vue'

export default {
  name: 'ProjectDetails',
  components: {
    ProjectFormModal,
    TaskCard,
    TaskDetailModal
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { isDarkMode } = useTheme()

    const project = ref(null)
    const isLoading = ref(true)
    const error = ref(null)
    const showEditModal = ref(false)

    // Task-related state
    const projectTasks = ref([])
    const isLoadingTasks = ref(false)
    const selectedTask = ref(null)
    const showTaskDetailModal = ref(false)

    // Theme-aware styles
    const headerStyle = computed(() => {
      const lightGradient = 'linear-gradient(135deg, #f3e8ff 0%, #e0e7ff 100%)'
      const darkGradient = 'linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)'

      return {
        background: isDarkMode.value ? darkGradient : lightGradient
      }
    })

    const titleStyle = computed(() => ({
      color: isDarkMode.value ? 'white' : '#7c3aed'
    }))

    const subtitleStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.9)' : 'rgba(124,58,237,0.8)',
      fontSize: '16px'
    }))

    const formatFullDate = (dateString) => {
      if (!dateString) return 'Unknown'

      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

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

    const getStatusText = (status) => {
      return status || 'Active'
    }

    // Load tasks for this project
    const loadProjectTasks = async () => {
      if (!project.value?.project_id) return

      isLoadingTasks.value = true
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const url = `${baseUrl}/tasks?project_id=${encodeURIComponent(project.value.project_id)}`

        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []

        // Filter tasks that are actually assigned to this project
        const filteredTasks = apiTasks.filter(task =>
          task.project_id === project.value.project_id
        )

        projectTasks.value = filteredTasks.map(t => ({
          id: t.id,
          title: t.title,
          dueDate: t.dueDate || null,
          status: t.status,
          description: t.description || 'No description available',
          priority: t.priority || 'Medium',
          assignee: t.assignee || 'Unassigned',
          project: t.project || project.value.project_name
        }))
      } catch (err) {
        console.error('Failed to load project tasks:', err)
        projectTasks.value = []
      } finally {
        isLoadingTasks.value = false
      }
    }

    // Handle task click - same functionality as home page
    const handleTaskClick = async (task) => {
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const url = `${baseUrl}/tasks?task_id=${encodeURIComponent(task.id)}`

        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []

        if (apiTasks.length === 0) {
          throw new Error('Task not found')
        }

        // Transform the API response to match TaskDetailModal expected format
        const taskDetails = {
          id: apiTasks[0].id,
          title: apiTasks[0].title,
          dueDate: apiTasks[0].dueDate,
          status: apiTasks[0].status,
          description: apiTasks[0].description || 'No description available',
          priority: apiTasks[0].priority || 'Medium',
          assignee: apiTasks[0].assignee || 'Unassigned',
          project: apiTasks[0].project || project.value.project_name,
          activities: apiTasks[0].activities || [],
          comments: apiTasks[0].comments || []
        }

        // Show task detail modal
        selectedTask.value = taskDetails
        showTaskDetailModal.value = true

      } catch (error) {
        console.error('Failed to fetch task details:', error)
        notification.error({
          message: 'Failed to load task details',
          description: error.message || 'Unable to fetch task information. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      }
    }

    const loadProject = async () => {
      try {
        isLoading.value = true
        error.value = null

        const projectId = route.params.id
        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8083'
        const ownerId = import.meta.env.VITE_TASK_OWNER_ID || ''

        // Fetch all projects since there's no single project endpoint
        const url = ownerId
          ? `${baseUrl}/projects?created_by=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/projects`

        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`Failed to load projects (HTTP ${response.status})`)
        }

        const payload = await response.json()
        const apiProjects = Array.isArray(payload?.projects) ? payload.projects : []

        // Find the specific project
        const foundProject = apiProjects.find(p => p.project_id === projectId)
        if (!foundProject) {
          throw new Error('Project not found')
        }

        project.value = {
          project_id: foundProject.project_id,
          project_name: foundProject.project_name,
          project_description: foundProject.project_description,
          created_at: foundProject.created_at,
          created_by: foundProject.created_by,
          due_date: foundProject.due_date,
          status: 'Active' // Default status
        }

        // Load tasks for this project
        await loadProjectTasks()

      } catch (err) {
        console.error('Failed to load project:', err)
        error.value = err.message
      } finally {
        isLoading.value = false
      }
    }

    const handleEdit = () => {
      showEditModal.value = true
    }

    const handleDelete = async () => {
      if (!confirm(`Are you sure you want to delete "${project.value.project_name}"? This action cannot be undone.`)) {
        return
      }

      try {
        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8083'
        const response = await fetch(`${baseUrl}/projects/${project.value.project_id}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        notification.success({
          message: 'Project deleted successfully',
          description: `"${project.value.project_name}" has been deleted.`,
          placement: 'topRight',
          duration: 3
        })

        router.push('/projects')
      } catch (err) {
        console.error('Failed to delete project:', err)
        notification.error({
          message: 'Failed to delete project',
          description: err.message,
          placement: 'topRight',
          duration: 4
        })
      }
    }

    const handleProjectUpdated = (updatedProject) => {
      project.value = {
        ...project.value,
        ...updatedProject
      }
      showEditModal.value = false

      notification.success({
        message: 'Project updated successfully',
        description: `"${updatedProject.project_name}" has been updated.`,
        placement: 'topRight',
        duration: 3
      })
    }

    const handleGenerateReport = () => {
      // Generate project report
      notification.info({
        message: 'Feature Coming Soon',
        description: 'Project report generation will be available soon.',
        placement: 'topRight',
        duration: 3
      })
    }

    // Handle task modal close
    const closeTaskDetailModal = () => {
      showTaskDetailModal.value = false
      selectedTask.value = null
    }

    // Watch for route parameter changes
    watch(() => route.params.id, (newId, oldId) => {
      if (newId && newId !== oldId) {
        loadProject()
      }
    }, { immediate: true })

    onMounted(() => {
      loadProject()
    })

    return {
      project,
      isLoading,
      error,
      showEditModal,
      projectTasks,
      isLoadingTasks,
      selectedTask,
      showTaskDetailModal,
      headerStyle,
      titleStyle,
      subtitleStyle,
      formatFullDate,
      getStatusColor,
      getStatusText,
      handleEdit,
      handleDelete,
      handleProjectUpdated,
      handleTaskClick,
      closeTaskDetailModal,
      handleGenerateReport
    }
  }
}
</script>

<style scoped>
.space-y-4 > * + * {
  margin-top: 1rem;
}
</style>