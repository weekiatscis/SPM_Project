<template>
  <div class="project-details-container">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <a-spin size="large" />
      <p>Loading project details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
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
    <div v-else-if="project" class="project-content">
      <!-- Back Button -->
      <a-button
        type="text"
        @click="$router.push('/projects')"
        class="back-button"
      >
        <template #icon>
          <LeftOutlined />
        </template>
        Back to Projects
      </a-button>

      <!-- Project Header -->
      <div class="project-header">
        <div class="header-top">
          <div class="title-section">
            <h1 class="project-title">{{ project.project_name }}</h1>
            <a-tag :class="['status-tag', getStatusClass(project.status)]">
              {{ getStatusText(project.status) }}
            </a-tag>
          </div>

          <!-- Action Buttons Row -->
          <div class="button-groups">
            <div class="action-buttons-group">
              <a-button @click="handleCreateTask" class="action-btn primary-action">
                <template #icon>
                  <PlusOutlined />
                </template>
                New Task
              </a-button>
              <a-button @click="handleGenerateReport" class="action-btn">
                <template #icon>
                  <FileTextOutlined />
                </template>
                Report
              </a-button>
            </div>

            <!-- Management Buttons Row - Only show to project owner -->
            <div class="management-buttons-group" v-if="isProjectOwner">
              <a-button type="primary" @click="handleEdit" class="action-btn">
                <template #icon>
                  <EditOutlined />
                </template>
                Edit
              </a-button>
              <a-button danger @click="handleDelete" class="action-btn">
                <template #icon>
                  <DeleteOutlined />
                </template>
                Delete
              </a-button>
            </div>
          </div>
        </div>

        <p class="project-description">
          {{ project.project_description || 'No description available' }}
        </p>

        <!-- Project Meta Info and Progress -->
        <div class="meta-and-progress">
          <div class="meta-info">
            <div class="meta-item">
              <CalendarOutlined class="meta-icon" />
              <div class="meta-content">
                <span class="meta-label">Created</span>
                <span class="meta-value">{{ formatDate(project.created_at) }}</span>
              </div>
            </div>
            <div class="meta-divider"></div>
            <div class="meta-item">
              <UserOutlined class="meta-icon" />  
              <div class="meta-content">
                <span class="meta-label">Owned By</span>
                <span class="meta-value">{{ project.created_by || 'Unknown' }}</span>
              </div>
            </div>
            <div class="meta-divider"></div>
            <div class="meta-item">
              <ClockCircleOutlined class="meta-icon" />
              <div class="meta-content">
                <span class="meta-label">Due Date</span>
                <span class="meta-value">{{ formatDate(project.due_date) || 'No due date' }}</span>
              </div>
            </div>
            <div class="meta-divider"></div>
            <div class="meta-item meta-item-clickable" @click="showTeamMembersModal = true">
              <TeamOutlined class="meta-icon" />
              <div class="meta-content">
                <span class="meta-label">Team Members</span>
                <span class="meta-value">{{ getTeamMembersCount() }}</span>
              </div>
            </div>
          </div>

          <!-- Project Progress Stats (Inline) -->
          <div class="progress-stats-inline">
            <div class="stat-item-inline">
              <div class="stat-number-inline">{{ projectTasks.length }}</div>
              <div class="stat-label-inline">Total</div>
            </div>
            <div class="stat-item-inline completed">
              <div class="stat-number-inline">{{ getCompletedTasksCount() }}</div>
              <div class="stat-label-inline">Completed</div>
            </div>
            <div class="stat-item-inline ongoing">
              <div class="stat-number-inline">{{ getOngoingTasksCount() }}</div>
              <div class="stat-label-inline">Ongoing</div>
            </div>
            <div class="stat-item-inline overdue">
              <div class="stat-number-inline">{{ getOverdueTasksCount() }}</div>
              <div class="stat-label-inline">Overdue</div>
            </div>
            <div class="progress-inline">
              <div class="progress-percentage-inline">{{ getCompletionPercentage() }}%</div>
              <div class="progress-bar-inline">
                <div class="progress-fill-inline" :style="{ width: getCompletionPercentage() + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- My Tasks Section -->
      <div class="section-card">
        <div class="section-header">
          <h2 class="section-title">
            <CheckCircleOutlined class="title-icon" />
            My Tasks
          </h2>
          <span class="task-count">{{ getMyTasks().length }}</span>
        </div>

        <div v-if="isLoadingTasks" class="loading-content">
          <a-spin size="large" />
          <p>Loading tasks...</p>
        </div>

        <div v-else-if="getMyTasks().length === 0" class="empty-content">
          <a-empty description="You have no tasks in this project yet" />
        </div>

        <div v-else class="tasks-grid">
          <div
            v-for="task in getMyTasks()"
            :key="task.id"
            @click="handleTaskClick(task)"
            :class="['task-card', { 'overdue': isOverdue(task.dueDate) }]"
          >
            <div class="task-header">
              <h3 class="task-title">{{ task.title }}</h3>
              <a-tag :class="['task-status', getStatusClass(task.status)]">
                {{ getStatusText(task.status) }}
              </a-tag>
            </div>

            <p class="task-description">{{ truncateText(task.description, 80) }}</p>

            <div class="task-footer">
              <div class="task-meta">
                <CalendarOutlined />
                <span :class="{ 'overdue-text': isOverdue(task.dueDate) }">
                  {{ formatTaskDate(task.dueDate) }}
                </span>
              </div>
              <div :class="['task-priority', getPriorityClass(task.priority)]">
                <FlagOutlined />
                {{ getPriorityText(task.priority) }}
              </div>
            </div>

            <div :class="['priority-indicator', getPriorityClass(task.priority)]"></div>
          </div>
        </div>
      </div>

      <!-- Other Project Tasks Section -->
      <div class="section-card" v-if="getOtherTasks().length > 0">
        <div class="section-header">
          <h2 class="section-title">
            <UnorderedListOutlined class="title-icon" />
            Other Project Tasks
          </h2>
          <span class="task-count">{{ getOtherTasks().length }}</span>
        </div>

        <div class="tasks-grid">
          <div
            v-for="task in getOtherTasks()"
            :key="task.id"
            @click="handleTaskClick(task)"
            :class="['task-card', 'other-task', { 'overdue': isOverdue(task.dueDate) }]"
          >
            <div class="task-header">
              <h3 class="task-title">{{ task.title }}</h3>
              <a-tag :class="['task-status', getStatusClass(task.status)]">
                {{ getStatusText(task.status) }}
              </a-tag>
            </div>

            <p class="task-description">{{ truncateText(task.description, 80) }}</p>

            <div class="task-footer">
              <div class="task-meta">
                <CalendarOutlined />
                <span :class="{ 'overdue-text': isOverdue(task.dueDate) }">
                  {{ formatTaskDate(task.dueDate) }}
                </span>
              </div>
              <div :class="['task-priority', getPriorityClass(task.priority)]">
                <FlagOutlined />
                {{ getPriorityText(task.priority) }}
              </div>
            </div>

            <div :class="['priority-indicator', getPriorityClass(task.priority)]"></div>
          </div>
        </div>
      </div>

      <!-- Project Comments -->
      <div class="section-card">
        <div class="section-header">
          <h2 class="section-title">
            <MessageOutlined class="title-icon" />
            Project Comments
          </h2>
        </div>
        <div class="comments-content">
          <ProjectComments
            v-if="project"
            :projectId="project.project_id"
          />
        </div>
      </div>
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

    <!-- Team Members Modal -->
    <TeamMembersModal
      v-if="project"
      :isOpen="showTeamMembersModal"
      :project="project"
      @close="showTeamMembersModal = false"
      @update="handleTeamUpdate"
    />

    <!-- Create Project Task Modal -->
    <CreateProjectTaskModal
      v-if="project"
      :isOpen="showCreateTaskModal"
      :project="project"
      @close="showCreateTaskModal = false"
      @save="handleTaskCreated"
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
      <div class="delete-modal-content">
        <div class="warning-icon">
          <ExclamationCircleOutlined />
        </div>

        <p class="warning-title">
          <strong>Are you sure you want to delete this project?</strong>
        </p>

        <p class="warning-subtitle">
          This action cannot be undone. All data associated with "<strong>{{ project?.project_name }}</strong>" will be permanently deleted.
        </p>

        <div class="confirmation-input">
          <label>
            Type <strong class="delete-text">delete</strong> to confirm:
          </label>
          <a-input
            v-model:value="deleteConfirmText"
            placeholder="Type 'delete' here"
            size="large"
            @pressEnter="confirmDelete"
            :status="deleteConfirmText && deleteConfirmText !== 'delete' ? 'error' : ''"
          />
          <span
            v-if="deleteConfirmText && deleteConfirmText !== 'delete'"
            class="error-text"
          >
            Please type exactly "delete" to confirm
          </span>
        </div>

        <div class="modal-actions">
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
import {
  FileTextOutlined,
  EditOutlined,
  DeleteOutlined,
  LeftOutlined,
  ExclamationCircleOutlined,
  CalendarOutlined,
  UserOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  DashboardOutlined,
  CheckCircleOutlined,
  UnorderedListOutlined,
  MessageOutlined,
  FlagOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useProjectEvents } from '../composables/useProjectEvents'
import ProjectFormModal from '../components/projects/ProjectFormModal.vue'
import TaskDetailModal from '../components/tasks/TaskDetailModal.vue'
import ProjectComments from '../components/projects/ProjectComments.vue'
import TeamMembersModal from '../components/projects/TeamMembersModal.vue'
import CreateProjectTaskModal from '../components/projects/CreateProjectTaskModal.vue'

export default {
  name: 'ProjectDetails',
  components: {
    ProjectFormModal,
    TaskDetailModal,
    ProjectComments,
    TeamMembersModal,
    CreateProjectTaskModal,
    FileTextOutlined,
    EditOutlined,
    DeleteOutlined,
    LeftOutlined,
    ExclamationCircleOutlined,
    CalendarOutlined,
    UserOutlined,
    ClockCircleOutlined,
    TeamOutlined,
    DashboardOutlined,
    CheckCircleOutlined,
    UnorderedListOutlined,
    MessageOutlined,
    FlagOutlined,
    PlusOutlined
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const authStore = useAuthStore()
    const { emitProjectUpdated, emitProjectDeleted } = useProjectEvents()

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

    // Team members modal state
    const showTeamMembersModal = ref(false)

    // Create task modal state
    const showCreateTaskModal = ref(false)

    // Check if current user is the project owner
    const isProjectOwner = computed(() => {
      if (!project.value || !authStore.user) return false
      return project.value.created_by_id === authStore.user.user_id
    })

    // Helper functions
    const formatDate = (dateString) => {
      if (!dateString) return 'Not set'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const formatTaskDate = (dateString) => {
      if (!dateString) return 'No due date'

      const dueDate = new Date(dateString + 'T00:00:00')
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      dueDate.setHours(0, 0, 0, 0)

      const diffTime = dueDate.getTime() - today.getTime()
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) {
        return `${Math.abs(diffDays)} days overdue`
      } else if (diffDays === 0) {
        return 'Due today'
      } else if (diffDays === 1) {
        return 'Due tomorrow'
      } else if (diffDays <= 7) {
        return `Due in ${diffDays} days`
      } else {
        return formatDate(dateString)
      }
    }

    const isOverdue = (dateString) => {
      if (!dateString) return false
      const dueDate = new Date(dateString + 'T00:00:00')
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      dueDate.setHours(0, 0, 0, 0)
      return dueDate < today
    }

    const truncateText = (text, maxLength) => {
      if (!text || text === 'No description available') return 'No description'
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    const getStatusClass = (status) => {
      const statusMap = {
        'Active': 'status-active',
        'Planning': 'status-planning',
        'On Hold': 'status-hold',
        'Completed': 'status-completed',
        'Cancelled': 'status-cancelled',
        'Unassigned': 'status-unassigned',
        'Ongoing': 'status-ongoing',
        'Under Review': 'status-review'
      }
      return statusMap[status] || 'status-default'
    }

    const getStatusText = (status) => {
      return status || 'Active'
    }

    const getPriorityClass = (priority) => {
      const priorityStr = String(priority).toLowerCase()
      if (priorityStr === 'high' || priorityStr === '1') return 'priority-high'
      if (priorityStr === 'medium' || priorityStr === '2' || priorityStr === '3') return 'priority-medium'
      if (priorityStr === 'low' || priorityStr === '4') return 'priority-low'
      if (priorityStr === 'lowest' || priorityStr === '5') return 'priority-lowest'
      return 'priority-medium'
    }

    const getPriorityText = (priority) => {
      const priorityStr = String(priority).toLowerCase()
      if (priorityStr === 'high' || priorityStr === '1') return 'High'
      if (priorityStr === 'medium' || priorityStr === '2' || priorityStr === '3') return 'Medium'
      if (priorityStr === 'low' || priorityStr === '4') return 'Low'
      if (priorityStr === 'lowest' || priorityStr === '5') return 'Lowest'
      return 'Medium'
    }

    const getTeamMembersCount = () => {
      // Team members = Project creator (1) + Project collaborators
      if (!project.value) return 1

      // 1 for project creator + number of collaborators
      const collaboratorsCount = Array.isArray(project.value.collaborators)
        ? project.value.collaborators.length
        : 0

      return 1 + collaboratorsCount
    }

    const getCompletedTasksCount = () => {
      return projectTasks.value.filter(t => t.status === 'Completed').length
    }

    const getOngoingTasksCount = () => {
      return projectTasks.value.filter(t => t.status === 'Ongoing').length
    }

    const getOverdueTasksCount = () => {
      return projectTasks.value.filter(t =>
        isOverdue(t.dueDate) && t.status !== 'Completed'
      ).length
    }

    const getCompletionPercentage = () => {
      if (projectTasks.value.length === 0) return 0
      return Math.round((getCompletedTasksCount() / projectTasks.value.length) * 100)
    }

    const getMyTasks = () => {
      const userId = authStore.user?.user_id
      if (!userId) return []

      return projectTasks.value.filter(task => {
        if (task.owner_id === userId) return true
        if (task.collaborators && Array.isArray(task.collaborators)) {
          return task.collaborators.includes(userId)
        }
        return false
      })
    }

    const getOtherTasks = () => {
      const userId = authStore.user?.user_id
      if (!userId) return projectTasks.value

      return projectTasks.value.filter(task => {
        if (task.owner_id === userId) return false
        if (task.collaborators && Array.isArray(task.collaborators)) {
          if (task.collaborators.includes(userId)) return false
        }
        return true
      })
    }

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
          owner_id: t.owner_id,
          collaborators: t.collaborators || [],
          project: t.project || project.value.project_name
        }))
      } catch (err) {
        console.error('Failed to load project tasks:', err)
        projectTasks.value = []
      } finally {
        isLoadingTasks.value = false
      }
    }

    const handleTaskClick = async (task) => {
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const url = `${baseUrl}/tasks?task_id=${encodeURIComponent(task.id)}`

        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []

        if (apiTasks.length === 0) throw new Error('Task not found')

        const taskDetails = {
          id: apiTasks[0].id,
          title: apiTasks[0].title,
          dueDate: apiTasks[0].dueDate,
          status: apiTasks[0].status,
          description: apiTasks[0].description || 'No description available',
          priority: apiTasks[0].priority || 'Medium',
          owner_id: apiTasks[0].owner_id,
          collaborators: apiTasks[0].collaborators || [],
          project: apiTasks[0].project || project.value.project_name,
          activities: apiTasks[0].activities || [],
          comments: apiTasks[0].comments || []
        }

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

        const url = ownerId
          ? `${baseUrl}/projects?created_by=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/projects`

        const response = await fetch(url)
        if (!response.ok) throw new Error(`Failed to load projects (HTTP ${response.status})`)

        const payload = await response.json()
        const apiProjects = Array.isArray(payload?.projects) ? payload.projects : []

        const foundProject = apiProjects.find(p => p.project_id === projectId)
        if (!foundProject) throw new Error('Project not found')

        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        let createdByName = foundProject.created_by

        try {
          const userResponse = await fetch(`${taskServiceUrl}/users/${foundProject.created_by}`)
          if (userResponse.ok) {
            const userData = await userResponse.json()
            createdByName = userData.user?.name || foundProject.created_by
          }
        } catch (err) {
          console.error(`Failed to fetch user name for ${foundProject.created_by}:`, err)
        }

        project.value = {
          project_id: foundProject.project_id,
          project_name: foundProject.project_name,
          project_description: foundProject.project_description,
          created_at: foundProject.created_at,
          created_by: createdByName,
          created_by_id: foundProject.created_by,
          due_date: foundProject.due_date,
          status: 'Active',
          collaborators: foundProject.collaborators || []
        }

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
      showDeleteModal.value = true
      deleteConfirmText.value = ''
    }

    const closeDeleteModal = () => {
      showDeleteModal.value = false
      deleteConfirmText.value = ''
      isDeletingProject.value = false
    }

    const confirmDelete = async () => {
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
        const userId = authStore.user?.user_id
        if (!userId) {
          throw new Error('User not authenticated')
        }

        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const response = await fetch(`${baseUrl}/projects/${project.value.project_id}?user_id=${encodeURIComponent(userId)}`, {
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

        // Emit event to update sidebar
        emitProjectDeleted(project.value.project_id)

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

      // Emit event to update sidebar
      emitProjectUpdated(updatedProject)

      loadProject()
    }

    const handleGenerateReport = () => {
      notification.info({
        message: 'Feature Coming Soon',
        description: 'Project report generation will be available soon.',
        placement: 'topRight',
        duration: 3
      })
    }

    const closeTaskDetailModal = () => {
      showTaskDetailModal.value = false
      selectedTask.value = null
    }

    const handleTeamUpdate = (updatedProject) => {
      // Update local project data
      project.value = {
        ...project.value,
        ...updatedProject
      }

      // Reload project to ensure consistency
      loadProject()
    }

    const handleCreateTask = () => {
      showCreateTaskModal.value = true
    }

    const handleTaskCreated = (newTask) => {
      showCreateTaskModal.value = false

      notification.success({
        message: 'Task Created',
        description: `"${newTask.title}" has been added to ${project.value.project_name}.`,
        placement: 'topRight',
        duration: 3
      })

      // Reload project tasks to show the new task
      loadProjectTasks()
    }

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
      showTeamMembersModal,
      showCreateTaskModal,
      isProjectOwner,
      handleTeamUpdate,
      handleCreateTask,
      handleTaskCreated,
      formatDate,
      formatTaskDate,
      isOverdue,
      truncateText,
      getStatusClass,
      getStatusText,
      getPriorityClass,
      getPriorityText,
      getTeamMembersCount,
      getCompletedTasksCount,
      getOngoingTasksCount,
      getOverdueTasksCount,
      getCompletionPercentage,
      getMyTasks,
      getOtherTasks,
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
/* Container */
.project-details-container {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 48px 32px;
}

.project-content {
  max-width: 1400px;
  margin: 0 auto;
}

/* Loading and Error States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.loading-state p {
  margin-top: 16px;
  font-size: 16px;
  color: #6b7280;
}

/* Back Button */
.back-button {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 32px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  transition: all 0.2s ease;
}

.back-button:hover {
  color: #667eea;
}

/* Project Header */
.project-header {
  background: white;
  border-radius: 16px;
  padding: 48px;
  margin-bottom: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 32px;
}

.title-section {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.project-title {
  font-size: 36px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  letter-spacing: -0.5px;
}

.status-tag {
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  border: none;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-active { background: #667eea; color: white; }
.status-planning { background: #06b6d4; color: white; }
.status-hold { background: #f59e0b; color: white; }
.status-completed { background: #10b981; color: white; }
.status-cancelled { background: #ef4444; color: white; }
.status-unassigned { background: #e5e7eb; color: #6b7280; }
.status-ongoing { background: #667eea; color: white; }
.status-review { background: #8b5cf6; color: white; }

.project-description {
  font-size: 16px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 32px 0;
}

/* Button Groups */
.button-groups {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
}

.action-buttons-group,
.management-buttons-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  height: 40px;
  padding: 0 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.action-btn.primary-action {
  background: #10b981;
  border-color: #10b981;
  color: white;
}

.action-btn.primary-action:hover {
  background: #059669;
  border-color: #059669;
}

/* Meta Info and Progress Container */
.meta-and-progress {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 48px;
  padding-top: 32px;
  border-top: 1px solid #e5e7eb;
}

.meta-info {
  display: flex;
  align-items: center;
  gap: 32px;
  flex: 0 1 auto;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-item-clickable {
  cursor: pointer;
  padding: 8px;
  margin: -8px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.meta-item-clickable:hover {
  background: #f3f4f6;
}

.meta-item-clickable:hover .meta-icon {
  color: #5568d3;
}

.meta-item-clickable:hover .meta-value {
  color: #667eea;
}

.meta-icon {
  font-size: 20px;
  color: #667eea;
  transition: all 0.2s ease;
}

.meta-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.meta-value {
  font-size: 15px;
  color: #111827;
  font-weight: 500;
}

.meta-divider {
  width: 1px;
  height: 40px;
  background: #e5e7eb;
}

/* Inline Progress Stats */
.progress-stats-inline {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 0 0 auto;
}

.stat-item-inline {
  text-align: center;
  min-width: 60px;
}

.stat-number-inline {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-item-inline.completed .stat-number-inline { color: #10b981; }
.stat-item-inline.ongoing .stat-number-inline { color: #667eea; }
.stat-item-inline.overdue .stat-number-inline { color: #ef4444; }

.stat-label-inline {
  font-size: 11px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.progress-inline {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 140px;
  padding-left: 24px;
  border-left: 1px solid #e5e7eb;
}

.progress-percentage-inline {
  font-size: 24px;
  font-weight: 700;
  color: #667eea;
  text-align: right;
}

.progress-bar-inline {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill-inline {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.6s ease;
}

/* Section Cards */
.section-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  margin-bottom: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 24px;
  color: #667eea;
}

.task-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  padding: 0 12px;
  background: #f3f4f6;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
}

/* Progress Stats */
.progress-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.stat-card {
  padding: 32px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  text-align: center;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.stat-number {
  font-size: 48px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 8px;
  line-height: 1;
}

.stat-card.completed .stat-number { color: #10b981; }
.stat-card.ongoing .stat-number { color: #667eea; }
.stat-card.overdue .stat-number { color: #ef4444; }

.stat-label {
  font-size: 13px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

/* Progress Bar */
.progress-bar-section {
  padding: 32px;
  background: #f9fafb;
  border-radius: 12px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.progress-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.progress-percentage {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
}

.progress-bar {
  height: 12px;
  background: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 6px;
  transition: width 0.6s ease;
}

/* Tasks Grid */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.task-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.task-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.12);
}

.task-card.overdue {
  border-color: #fecaca;
  background: #fef2f2;
}

.task-card.other-task {
  opacity: 0.7;
}

.task-card.other-task:hover {
  opacity: 1;
}

.priority-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
}

.priority-indicator.priority-high { background: #ef4444; }
.priority-indicator.priority-medium { background: #f59e0b; }
.priority-indicator.priority-low { background: #06b6d4; }
.priority-indicator.priority-lowest { background: #9ca3af; }

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.task-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.task-status {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.task-description {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 16px 0;
  min-height: 44px;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.overdue-text {
  color: #ef4444;
  font-weight: 600;
}

.task-priority {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.task-priority.priority-high {
  background: #fef2f2;
  color: #ef4444;
}

.task-priority.priority-medium {
  background: #fffbeb;
  color: #f59e0b;
}

.task-priority.priority-low {
  background: #ecfeff;
  color: #06b6d4;
}

.task-priority.priority-lowest {
  background: #f3f4f6;
  color: #6b7280;
}

/* Loading and Empty States */
.loading-content,
.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-content p {
  margin-top: 16px;
  color: #6b7280;
}

/* Comments */
.comments-content {
  padding: 0;
}

/* Delete Modal */
.delete-modal-content {
  padding: 16px 0;
}

.warning-icon {
  text-align: center;
  margin-bottom: 16px;
  font-size: 48px;
  color: #ff4d4f;
}

.warning-title {
  text-align: center;
  font-size: 16px;
  margin-bottom: 8px;
}

.warning-subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 24px;
}

.confirmation-input {
  margin-bottom: 24px;
}

.confirmation-input label {
  display: block;
  margin-bottom: 8px;
  color: #666;
}

.delete-text {
  color: #ff4d4f;
}

.error-text {
  font-size: 12px;
  color: #ff4d4f;
  display: block;
  margin-top: 4px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .meta-and-progress {
    gap: 32px;
  }

  .meta-info {
    gap: 20px;
  }

  .progress-stats-inline {
    gap: 16px;
  }

  .stat-item-inline {
    min-width: 50px;
  }

  .stat-number-inline {
    font-size: 24px;
  }

  .progress-inline {
    min-width: 120px;
  }

  .progress-percentage-inline {
    font-size: 20px;
  }
}

@media (max-width: 1024px) {
  .meta-and-progress {
    flex-direction: column;
    align-items: flex-start;
    gap: 24px;
  }

  .meta-info {
    flex-wrap: wrap;
  }

  .meta-divider {
    display: none;
  }

  .progress-stats-inline {
    width: 100%;
    justify-content: space-between;
    padding-top: 24px;
    border-top: 1px solid #e5e7eb;
  }

  .progress-inline {
    border-left: none;
    padding-left: 0;
  }
}

@media (max-width: 768px) {
  .project-details-container {
    padding: 24px 16px;
  }

  .project-header,
  .section-card {
    padding: 24px;
  }

  .project-title {
    font-size: 28px;
  }

  .header-top {
    flex-direction: column;
    gap: 24px;
  }

  .header-actions {
    width: 100%;
  }

  .action-btn {
    flex: 1;
  }

  .meta-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .progress-stats-inline {
    flex-wrap: wrap;
    gap: 12px;
  }

  .stat-item-inline {
    flex: 1 1 calc(50% - 6px);
    min-width: 0;
  }

  .progress-inline {
    flex: 1 1 100%;
    min-width: 0;
    margin-top: 12px;
  }

  .progress-percentage-inline {
    text-align: left;
  }

  .tasks-grid {
    grid-template-columns: 1fr;
  }

  .section-title {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .project-title {
    font-size: 24px;
  }

  .title-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .stat-number-inline {
    font-size: 20px;
  }

  .stat-label-inline {
    font-size: 10px;
  }

  .progress-percentage-inline {
    font-size: 18px;
  }
}
</style>
