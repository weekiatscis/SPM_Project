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
        <a-row :gutter="[16, 16]" align="middle">
          <a-col :xs="24" :sm="24" :md="16" :lg="18">
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px; flex-wrap: wrap;">
              <a-button
                type="text"
                @click="$router.push('/projects')"
                style="padding: 4px;"
              >
                <template #icon>
                  <LeftOutlined />
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
          <a-col :xs="24" :sm="24" :md="8" :lg="6">
            <a-space
              direction="vertical"
              :style="{ width: '100%' }"
              :size="8"
              class="action-buttons"
            >
              <a-button
                type="default"
                @click="handleGenerateReport"
                block
              >
                <template #icon>
                  <FileTextOutlined />
                </template>
                Report
              </a-button>
              <a-button
                type="primary"
                @click="handleEdit"
                block
              >
                <template #icon>
                  <EditOutlined />
                </template>
                Edit
              </a-button>
              <a-button
                danger
                @click="handleDelete"
                block
              >
                <template #icon>
                  <DeleteOutlined />
                </template>
                Delete
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

    <!-- Delete Confirmation Modal -->
    <a-modal
      v-model:open="showDeleteModal"
      title="Delete Project"
      :closable="true"
      :maskClosable="false"
      @cancel="closeDeleteModal"
      :footer="null"
      width="500px"
    >
      <div style="padding: 16px 0;">
        <!-- Warning Icon -->
        <div style="text-align: center; margin-bottom: 16px;">
          <ExclamationCircleOutlined style="font-size: 48px; color: #ff4d4f;" />
        </div>

        <!-- Warning Message -->
        <a-typography-paragraph style="text-align: center; font-size: 16px; margin-bottom: 8px;">
          <strong>Are you sure you want to delete this project?</strong>
        </a-typography-paragraph>

        <a-typography-paragraph style="text-align: center; color: #666; margin-bottom: 24px;">
          This action cannot be undone. All data associated with "<strong>{{ project?.project_name }}</strong>" will be permanently deleted.
        </a-typography-paragraph>

        <!-- Confirmation Input -->
        <div style="margin-bottom: 24px;">
          <a-typography-text style="display: block; margin-bottom: 8px; color: #666;">
            Type <strong style="color: #ff4d4f;">delete</strong> to confirm:
          </a-typography-text>
          <a-input
            v-model:value="deleteConfirmText"
            placeholder="Type 'delete' here"
            size="large"
            @pressEnter="confirmDelete"
            :status="deleteConfirmText && deleteConfirmText !== 'delete' ? 'error' : ''"
          />
          <a-typography-text
            v-if="deleteConfirmText && deleteConfirmText !== 'delete'"
            type="danger"
            style="font-size: 12px; display: block; margin-top: 4px;"
          >
            Please type exactly "delete" to confirm
          </a-typography-text>
        </div>

        <!-- Action Buttons -->
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
          <a-button @click="closeDeleteModal" size="large">
            Cancel
          </a-button>
          <a-button
            type="primary"
            danger
            size="large"
            @click="confirmDelete"
            :disabled="deleteConfirmText !== 'delete'"
            :loading="isDeletingProject"
          >
            <template #icon>
              <DeleteOutlined />
            </template>
            Delete Project
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notification } from 'ant-design-vue'
import { FileTextOutlined, EditOutlined, DeleteOutlined, LeftOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import ProjectFormModal from '../components/projects/ProjectFormModal.vue'
import TaskCard from '../components/tasks/TaskCard.vue'
import TaskDetailModal from '../components/tasks/TaskDetailModal.vue'

export default {
  name: 'ProjectDetails',
  components: {
    ProjectFormModal,
    TaskCard,
    TaskDetailModal,
    FileTextOutlined,
    EditOutlined,
    DeleteOutlined,
    LeftOutlined,
    ExclamationCircleOutlined
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const authStore = useAuthStore()

    const project = ref(null)
    const isLoading = ref(true)
    const error = ref(null)
    const showEditModal = ref(false)

    // Task-related state
    const projectTasks = ref([])
    const isLoadingTasks = ref(false)
    const selectedTask = ref(null)
    const showTaskDetailModal = ref(false)

    // Delete modal state
    const showDeleteModal = ref(false)
    const deleteConfirmText = ref('')
    const isDeletingProject = ref(false)

    // Light theme styles
    const headerStyle = computed(() => {
      const lightGradient = 'linear-gradient(135deg, #f3e8ff 0%, #e0e7ff 100%)'

      return {
        background: lightGradient
      }
    })

    const titleStyle = computed(() => ({
      color: '#7c3aed'
    }))

    const subtitleStyle = computed(() => ({
      color: 'rgba(124,58,237,0.8)',
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
        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const ownerId = authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID || ''

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

    const handleDelete = () => {
      // Open the delete confirmation modal
      showDeleteModal.value = true
      deleteConfirmText.value = ''
    }

    const closeDeleteModal = () => {
      showDeleteModal.value = false
      deleteConfirmText.value = ''
      isDeletingProject.value = false
    }

    const confirmDelete = async () => {
      // Check if user typed "delete" correctly
      if (deleteConfirmText.value !== 'delete') {
        notification.warning({
          message: 'Invalid confirmation',
          description: 'Please type "delete" to confirm project deletion.',
          placement: 'topRight',
          duration: 3
        })
        return
      }

      isDeletingProject.value = true

      try {
        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
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

        closeDeleteModal()
        router.push('/projects')
      } catch (err) {
        console.error('Failed to delete project:', err)
        notification.error({
          message: 'Failed to delete project',
          description: err.message,
          placement: 'topRight',
          duration: 4
        })
      } finally {
        isDeletingProject.value = false
      }
    }

    const handleProjectUpdated = (updatedProject) => {
      // Update the local project state with the new data
      project.value = {
        ...project.value,
        ...updatedProject
      }

      // Close the modal
      showEditModal.value = false

      // Show success notification
      notification.success({
        message: 'Project updated successfully',
        description: `"${updatedProject.project_name}" has been updated.`,
        placement: 'topRight',
        duration: 3
      })

      // Optionally refresh the project data from the server to ensure consistency
      loadProject()
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
      showDeleteModal,
      deleteConfirmText,
      isDeletingProject,
      headerStyle,
      titleStyle,
      subtitleStyle,
      formatFullDate,
      getStatusColor,
      getStatusText,
      handleEdit,
      handleDelete,
      closeDeleteModal,
      confirmDelete,
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

/* Action buttons styling */
.action-buttons {
  width: 100%;
}

.action-buttons :deep(.ant-btn) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-buttons :deep(.ant-btn:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .action-buttons {
    margin-top: 16px;
  }
}

@media (min-width: 769px) {
  .action-buttons {
    align-items: flex-end;
  }
}

/* Delete modal styling */
:deep(.ant-modal-header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
}

:deep(.ant-modal-body) {
  padding: 0 24px;
}

:deep(.ant-input-status-error) {
  border-color: #ff4d4f;
}

:deep(.ant-input-status-error:focus) {
  border-color: #ff4d4f;
  box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.1);
}
</style>