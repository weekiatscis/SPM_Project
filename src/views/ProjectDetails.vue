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
              <a-button v-if="project.status !== 'Completed'" @click="handleCreateTask" class="action-btn primary-action">
                <template #icon>
                  <PlusOutlined />
                </template>
                New Task
              </a-button>
              <a-button @click="showTeamMembersModal = true" class="action-btn">
                <template #icon>
                  <TeamOutlined />
                </template>
                Team
              </a-button>
              <a-button @click="handleGenerateReport" class="action-btn">
                <template #icon>
                  <FileTextOutlined />
                </template>
                Report
              </a-button>

              <!-- Three-dot dropdown menu - Only show to project owner -->
              <a-dropdown v-if="isProjectOwner" :trigger="['click']">
                <a-button class="action-btn action-menu-btn">
                  <template #icon>
                    <MoreOutlined />
                  </template>
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item key="edit" @click="handleEdit" class="menu-item-edit">
                      <EditOutlined class="menu-icon-edit" />
                      <span style="margin-left: 8px;">Edit Project</span>
                    </a-menu-item>
                    <a-menu-item v-if="project.status !== 'Completed'" key="complete" @click="handleMarkAsCompleted" class="menu-item-complete">
                      <CheckCircleOutlined class="menu-icon-complete" />
                      <span style="margin-left: 8px;">Mark as Completed</span>
                    </a-menu-item>
                    <a-menu-item v-if="project.status === 'Completed'" key="active" @click="handleMarkAsActive" class="menu-item-active">
                      <CheckCircleOutlined class="menu-icon-active" />
                      <span style="margin-left: 8px;">Mark as Active</span>
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="delete" @click="handleDelete" danger>
                      <DeleteOutlined />
                      <span style="margin-left: 8px;">Delete Project</span>
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
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
            <div class="meta-item">
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
          <div class="section-title-group">
            <h2 class="section-title">
              <CheckCircleOutlined class="title-icon" />
              My Tasks
            </h2>
            <span class="task-count">{{ getMyTasks().length }}</span>
          </div>

          <!-- Search Input for My Tasks -->
          <a-input
            v-model:value="myTasksSearchQuery"
            placeholder="Search my tasks by name..."
            allowClear
            class="search-input"
          >
            <template #prefix>
              <SearchOutlined class="search-icon" />
            </template>
          </a-input>
        </div>

        <div v-if="isLoadingTasks" class="loading-content">
          <a-spin size="large" />
          <p>Loading tasks...</p>
        </div>

        <div v-else-if="getMyTasks().length === 0" class="empty-content">
          <a-empty description="You have no tasks in this project yet" />
        </div>

        <div v-else-if="getFilteredMyTasks().length === 0 && myTasksSearchQuery" class="empty-content">
          <a-empty description="No tasks match your search" />
        </div>

        <div v-else class="tasks-table-container">
          <a-table
            :dataSource="getFilteredMyTasks()"
            :columns="taskColumns"
            :pagination="false"
            :rowKey="record => record.id"
            :customRow="(record) => ({
              onClick: () => handleTaskClick(record),
              class: isTaskOverdue(record) ? 'overdue-task-row' : ''
            })"
            class="tasks-table"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'title'">
                <div class="task-title-cell">
                  <a-tooltip v-if="isParentTask(record)" title="This is a parent task">
                    <span class="badge-icon parent-task">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                    </span>
                  </a-tooltip>

                  <a-tooltip v-if="record.isSubtask" title="This is a subtask">
                    <span class="badge-icon subtask">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </span>
                  </a-tooltip>

                  <a-tooltip v-if="isUserCollaborator(record)" title="You are a collaborator">
                    <span class="badge-icon collaborator">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                    </span>
                  </a-tooltip>

                  <span class="task-title-text">{{ record.title }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'description'">
                <div class="task-description-cell">
                  {{ truncateText(record.description, 100) }}
                </div>
              </template>
              <template v-else-if="column.key === 'status'">
                <a-tag :class="['task-status', getStatusClass(record.status)]">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'priority'">
                <div :class="['task-priority-cell', getPriorityClass(record.priority)]">
                  <FlagOutlined />
                  {{ getPriorityText(record.priority) }}
                </div>
              </template>
              <template v-else-if="column.key === 'dueDate'">
                <span :class="{
                  'overdue-text': isOverdue(record.dueDate) && record.status !== 'Completed',
                  'completed-text': record.status === 'Completed'
                }">
                  {{ formatTaskDate(record.dueDate) }}
                </span>
              </template>
              <template v-else-if="column.key === 'timeTaken'">
                <span class="time-taken-cell">
                  {{ getTaskTimeTaken(record) }}
                </span>
              </template>
              <template v-else-if="column.key === 'department'">
                {{ record.department || 'N/A' }}
              </template>
              <template v-else-if="column.key === 'assignee'">
                {{ formatAssigneeNames(record.assignee_name) }}
              </template>
            </template>
          </a-table>
        </div>
      </div>

      <!-- Other Project Tasks Section -->
      <div class="section-card" v-if="getOtherTasks().length > 0">
        <div class="section-header">
          <div class="section-title-group">
            <h2 class="section-title">
              <UnorderedListOutlined class="title-icon" />
              Other Project Tasks
            </h2>
            <span class="task-count">{{ getOtherTasks().length }}</span>
          </div>

          <!-- Search Input for Other Tasks -->
          <a-input
            v-model:value="otherTasksSearchQuery"
            placeholder="Search other tasks by name..."
            allowClear
            class="search-input"
          >
            <template #prefix>
              <SearchOutlined class="search-icon" />
            </template>
          </a-input>
        </div>

        <div v-if="getFilteredOtherTasks().length === 0 && otherTasksSearchQuery" class="empty-content">
          <a-empty description="No tasks match your search" />
        </div>

        <div v-else class="tasks-table-container">
          <a-table
            :dataSource="getFilteredOtherTasks()"
            :columns="taskColumns"
            :pagination="false"
            :rowKey="record => record.id"
            :customRow="(record) => ({
              onClick: () => handleTaskClick(record),
              class: isTaskOverdue(record) ? 'overdue-task-row' : ''
            })"
            class="tasks-table"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'title'">
                <div class="task-title-cell">
                  <a-tooltip v-if="isParentTask(record)" title="This is a parent task">
                    <span class="badge-icon parent-task">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                    </span>
                  </a-tooltip>

                  <a-tooltip v-if="record.isSubtask" title="This is a subtask">
                    <span class="badge-icon subtask">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </span>
                  </a-tooltip>

                  <a-tooltip v-if="isUserCollaborator(record)" title="You are a collaborator">
                    <span class="badge-icon collaborator">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                    </span>
                  </a-tooltip>

                  <span class="task-title-text">{{ record.title }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'description'">
                <div class="task-description-cell">
                  {{ truncateText(record.description, 100) }}
                </div>
              </template>
              <template v-else-if="column.key === 'status'">
                <a-tag :class="['task-status', getStatusClass(record.status)]">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'priority'">
                <div :class="['task-priority-cell', getPriorityClass(record.priority)]">
                  <FlagOutlined />
                  {{ getPriorityText(record.priority) }}
                </div>
              </template>
              <template v-else-if="column.key === 'dueDate'">
                <span :class="{
                  'overdue-text': isOverdue(record.dueDate) && record.status !== 'Completed',
                  'completed-text': record.status === 'Completed'
                }">
                  {{ formatTaskDate(record.dueDate) }}
                </span>
              </template>
              <template v-else-if="column.key === 'timeTaken'">
                <span class="time-taken-cell">
                  {{ getTaskTimeTaken(record) }}
                </span>
              </template>
              <template v-else-if="column.key === 'department'">
                {{ record.department || 'N/A' }}
              </template>
              <template v-else-if="column.key === 'assignee'">
                {{ formatAssigneeNames(record.assignee_name) }}
              </template>
            </template>
          </a-table>
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
      @open-task="handleOpenTask"
      @edit="handleTaskEdit"
      @delete="handleTaskDelete"
      @task-updated="handleTaskUpdated"
    />

    <!-- Task Edit Modal -->
    <TaskFormModal
      v-if="editingTask"
      :task="editingTask"
      :isOpen="showEditTaskModal"
      @close="closeEditTaskModal"
      @save="handleTaskUpdated"
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

    <!-- Project Report Preview Modal -->
    <ProjectReportPreviewModal
      :isOpen="showReportPreviewModal"
      :reportData="reportPreviewData"
      @close="closeReportPreview"
      @export="handleExportPDF"
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
  PlusOutlined,
  MoreOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useProjectEvents } from '../composables/useProjectEvents'
import { calculateTimeTaken } from '../utils/dateUtils'
import ProjectFormModal from '../components/projects/ProjectFormModal.vue'
import TaskDetailModal from '../components/tasks/TaskDetailModal.vue'
import TaskFormModal from '../components/tasks/TaskFormModal.vue'
import ProjectComments from '../components/projects/ProjectComments.vue'
import TeamMembersModal from '../components/projects/TeamMembersModal.vue'
import CreateProjectTaskModal from '../components/projects/CreateProjectTaskModal.vue'
import ProjectReportPreviewModal from '../components/projects/ProjectReportPreviewModal.vue'

export default {
  name: 'ProjectDetails',
  components: {
    ProjectFormModal,
    TaskDetailModal,
    TaskFormModal,
    ProjectComments,
    TeamMembersModal,
    CreateProjectTaskModal,
    ProjectReportPreviewModal,
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
    PlusOutlined,
    MoreOutlined,
    SearchOutlined
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
    const editingTask = ref(null)
    const showEditTaskModal = ref(false)

    // Delete modal state
    const showDeleteModal = ref(false)
    const deleteConfirmText = ref('')
    const isDeletingProject = ref(false)

    // Team members modal state
    const showTeamMembersModal = ref(false)

    // Create task modal state
    const showCreateTaskModal = ref(false)

    // Report preview modal state
    const showReportPreviewModal = ref(false)
    const reportPreviewData = ref(null)

    // Search state
    const myTasksSearchQuery = ref('')
    const otherTasksSearchQuery = ref('')

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
      return formatDate(dateString)
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
      const priorityNum = parseInt(priority)
      if (!isNaN(priorityNum)) {
        if (priorityNum >= 8) return 'priority-high'        // 8-10: High priority
        if (priorityNum >= 5) return 'priority-medium'      // 5-7: Medium priority
        if (priorityNum >= 3) return 'priority-low'         // 3-4: Low priority
        return 'priority-lowest'                             // 1-2: Lowest priority
      }
      // Fallback for legacy text values
      const priorityStr = String(priority).toLowerCase()
      if (priorityStr === 'high') return 'priority-high'
      if (priorityStr === 'medium') return 'priority-medium'
      if (priorityStr === 'low') return 'priority-low'
      if (priorityStr === 'lowest') return 'priority-lowest'
      return 'priority-medium'
    }

    const getPriorityText = (priority) => {
      const priorityNum = parseInt(priority)
      if (!isNaN(priorityNum) && priorityNum >= 1 && priorityNum <= 10) {
        return `Priority: ${priorityNum}`
      }
      // Fallback for legacy text values
      const priorityStr = String(priority).toLowerCase()
      if (priorityStr === 'high') return 'Priority: 9'
      if (priorityStr === 'medium') return 'Priority: 5'
      if (priorityStr === 'low') return 'Priority: 3'
      if (priorityStr === 'lowest') return 'Priority: 1'
      return 'Priority: 5'
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

    const getTaskTimeTaken = (task) => {
      if (!task.created_at) return 'N/A'

      // If task is completed, calculate time from created_at to completedDate
      if (task.status === 'Completed' && task.completedDate) {
        return calculateTimeTaken(task.created_at, task.completedDate)
      }

      // If task is still in progress, calculate time from created_at to now
      return calculateTimeTaken(task.created_at)
    }

    const isUserCollaborator = (task) => {
      const userId = authStore.user?.user_id
      if (!userId || !task.collaborators) return false

      // Check if user is a collaborator but NOT the owner
      if (task.owner_id === userId) return false

      return Array.isArray(task.collaborators) && task.collaborators.includes(userId)
    }

    const isParentTask = (task) => {
      // A task is a parent if it has subtasks
      // Check if any task in the list has this task as its parent
      return projectTasks.value.some(t => t.parent_task_id === task.id)
    }

    const isTaskOverdue = (task) => {
      // A task is overdue if it's not completed and the due date has passed
      if (task.status === 'Completed' || !task.dueDate) return false

      const today = new Date()
      today.setHours(0, 0, 0, 0)

      const dueDate = new Date(task.dueDate)
      dueDate.setHours(0, 0, 0, 0)

      return dueDate < today
    }

    const formatAssigneeNames = (assigneeName) => {
      // Format assignee names to show max 2 names + count
      if (!assigneeName || assigneeName === 'Unassigned') return 'Unassigned'

      const names = assigneeName.split(', ').map(name => name.trim())

      if (names.length <= 2) {
        return assigneeName
      }

      const firstTwoNames = names.slice(0, 2).join(', ')
      const remainingCount = names.length - 2
      return `${firstTwoNames} +${remainingCount} more`
    }

    // Table columns definition
    const taskColumns = [
      {
        title: 'Task Name',
        dataIndex: 'title',
        key: 'title',
        width: '18%',
        ellipsis: true,
        sorter: (a, b) => a.title.localeCompare(b.title),
        sortDirections: ['ascend', 'descend']
      },
      {
        title: 'Description',
        dataIndex: 'description',
        key: 'description',
        width: '25%',
        ellipsis: true
      },
      {
        title: 'Status',
        dataIndex: 'status',
        key: 'status',
        width: '10%',
        align: 'center',
        sorter: (a, b) => {
          // Custom sorter: Completed should be last
          const statusOrder = { 'Ongoing': 1, 'Under Review': 2, 'Completed': 3 }
          const orderA = statusOrder[a.status] || 1
          const orderB = statusOrder[b.status] || 1
          return orderA - orderB
        },
        sortDirections: ['ascend', 'descend'],
        defaultSortOrder: 'ascend' // Completed will be last with this order
      },
      {
        title: 'Priority',
        dataIndex: 'priority',
        key: 'priority',
        width: '10%',
        align: 'center',
        sorter: (a, b) => {
          // Priority is stored as a number (1-10), higher number = higher priority
          const priorityA = parseInt(a.priority) || 5
          const priorityB = parseInt(b.priority) || 5
          return priorityB - priorityA  // Descending by default (10 first, then 9, 8, etc.)
        },
        sortDirections: ['ascend', 'descend']
      },
      {
        title: 'Due Date',
        dataIndex: 'dueDate',
        key: 'dueDate',
        width: '10%',
        align: 'center',
        sorter: (a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(a.dueDate) - new Date(b.dueDate)
        },
        sortDirections: ['ascend', 'descend']
      },
      {
        title: 'Time Taken',
        dataIndex: 'timeTaken',
        key: 'timeTaken',
        width: '12%',
        align: 'center',
        sorter: (a, b) => {
          // Sort by total milliseconds for accurate sorting
          const getTimeDiff = (task) => {
            if (!task.created_at) return 0
            const start = new Date(task.created_at)
            const end = task.status === 'Completed' && task.completedDate
              ? new Date(task.completedDate)
              : new Date()
            return end - start
          }
          return getTimeDiff(a) - getTimeDiff(b)
        },
        sortDirections: ['ascend', 'descend']
      },
      {
        title: 'Department',
        dataIndex: 'department',
        key: 'department',
        width: '10%',
        align: 'center',
        sorter: (a, b) => (a.department || 'N/A').localeCompare(b.department || 'N/A'),
        sortDirections: ['ascend', 'descend']
      },
      {
        title: 'Assignee',
        dataIndex: 'assignee_name',
        key: 'assignee',
        width: '13%',
        align: 'center',
        sorter: (a, b) => (a.assignee_name || 'Unassigned').localeCompare(b.assignee_name || 'Unassigned'),
        sortDirections: ['ascend', 'descend']
      }
    ]

    const getMyTasks = () => {
      const userId = authStore.user?.user_id
      if (!userId) return []

      return projectTasks.value.filter(task => {
        // User is the owner
        if (task.owner_id === userId) return true

        // User is a collaborator (works for both parent tasks and subtasks)
        if (task.collaborators && Array.isArray(task.collaborators)) {
          if (task.collaborators.includes(userId)) return true
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

    const getFilteredMyTasks = () => {
      const myTasks = getMyTasks()
      if (!myTasksSearchQuery.value) return myTasks

      const query = myTasksSearchQuery.value.toLowerCase().trim()
      return myTasks.filter(task =>
        task.title.toLowerCase().includes(query)
      )
    }

    const getFilteredOtherTasks = () => {
      const otherTasks = getOtherTasks()
      if (!otherTasksSearchQuery.value) return otherTasks

      const query = otherTasksSearchQuery.value.toLowerCase().trim()
      return otherTasks.filter(task =>
        task.title.toLowerCase().includes(query)
      )
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

        // Get all unique owner_ids
        const ownerIds = [...new Set(filteredTasks.map(t => t.owner_id).filter(Boolean))]

        // Get all unique collaborator IDs from all tasks
        const collaboratorIds = new Set()
        filteredTasks.forEach(t => {
          let collaborators = t.collaborators || []
          if (typeof collaborators === 'string') {
            try {
              collaborators = JSON.parse(collaborators)
            } catch (e) {
              collaborators = []
            }
          }
          if (Array.isArray(collaborators)) {
            collaborators.forEach(collabId => collaboratorIds.add(collabId))
          }
        })

        // Combine all unique user IDs (owners + collaborators)
        const allUserIds = [...new Set([...ownerIds, ...collaboratorIds])]

        // Fetch user names and departments for all user IDs
        const userNameMap = {}
        const userDepartmentMap = {}
        for (const userId of allUserIds) {
          try {
            const userResponse = await fetch(`${baseUrl}/users/${userId}`)
            if (userResponse.ok) {
              const userData = await userResponse.json()
              userNameMap[userId] = userData.user?.name || 'Unknown'
              userDepartmentMap[userId] = userData.user?.department || 'N/A'
            }
          } catch (err) {
            console.error(`Failed to fetch user name for ${userId}:`, err)
            userNameMap[userId] = 'Unknown'
            userDepartmentMap[userId] = 'N/A'
          }
        }

        projectTasks.value = filteredTasks.map(t => {
          // Parse collaborators if it's a JSON string
          let collaborators = t.collaborators || []
          if (typeof collaborators === 'string') {
            try {
              collaborators = JSON.parse(collaborators)
            } catch (e) {
              console.error('Failed to parse collaborators:', e)
              collaborators = []
            }
          }

          // Build assignee_name: owner + collaborators (comma-separated)
          const assigneeNames = []

          // Add owner name first
          if (t.owner_id && userNameMap[t.owner_id]) {
            assigneeNames.push(userNameMap[t.owner_id])
          }

          // Add collaborator names (excluding owner if they're also in collaborators)
          if (Array.isArray(collaborators)) {
            collaborators.forEach(collabId => {
              if (collabId !== t.owner_id && userNameMap[collabId]) {
                assigneeNames.push(userNameMap[collabId])
              }
            })
          }

          const assignee_name = assigneeNames.length > 0 ? assigneeNames.join(', ') : 'Unassigned'

          return {
            id: t.id,
            title: t.title,
            dueDate: t.dueDate || null,
            completedDate: t.completedDate || null,
            created_at: t.created_at || null,
            status: t.status,
            description: t.description || 'No description available',
            priority: t.priority || 'Medium',
            owner_id: t.owner_id,
            owner_name: userNameMap[t.owner_id] || 'Unassigned',
            assignee_name: assignee_name,
            department: userDepartmentMap[t.owner_id] || 'N/A',
            collaborators: Array.isArray(collaborators) ? collaborators : [],
            project: t.project || project.value.project_name,
            parent_task_id: t.parent_task_id || null,
            isSubtask: t.isSubtask || !!t.parent_task_id
          }
        })
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
          status: foundProject.status || 'Active',
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

    const handleGenerateReport = async () => {
      try {
        // Show loading notification
        notification.info({
          message: 'Loading Report Preview',
          description: 'Please wait while we prepare your project report...',
          placement: 'topRight',
          duration: 2
        })

        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'

        // Fetch report preview data
        const response = await fetch(`${reportServiceUrl}/preview-project-report`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_id: project.value.project_id,
            user_id: authStore.user?.user_id
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to load report preview')
        }

        const data = await response.json()
        reportPreviewData.value = data
        showReportPreviewModal.value = true

      } catch (error) {
        console.error('Error loading report preview:', error)
        notification.error({
          message: 'Failed to Load Preview',
          description: error.message || 'Unable to load report preview. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      }
    }

    const closeReportPreview = () => {
      showReportPreviewModal.value = false
      reportPreviewData.value = null
    }

    const handleExportPDF = async () => {
      try {
        notification.info({
          message: 'Generating PDF',
          description: 'Please wait while we generate your PDF report...',
          placement: 'topRight',
          duration: 2
        })

        const reportServiceUrl = import.meta.env.VITE_REPORT_SERVICE_URL || 'http://localhost:8090'

        const response = await fetch(`${reportServiceUrl}/generate-project-report`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_id: project.value.project_id,
            user_id: authStore.user?.user_id
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to generate PDF')
        }

        // Get the blob from response
        const blob = await response.blob()

        // Create a download link
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url

        // Extract filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition')
        let filename = `project_report_${project.value.project_name.replace(/\s+/g, '_')}_${new Date().getTime()}.pdf`

        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1].replace(/['"]/g, '')
          }
        }

        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        notification.success({
          message: 'PDF Generated Successfully',
          description: 'Your project report has been downloaded.',
          placement: 'topRight',
          duration: 3
        })

        closeReportPreview()

      } catch (error) {
        console.error('Error exporting PDF:', error)
        notification.error({
          message: 'Failed to Export PDF',
          description: error.message || 'Unable to generate PDF. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      }
    }

    const closeTaskDetailModal = () => {
      showTaskDetailModal.value = false
      selectedTask.value = null
    }

    const handleTaskEdit = (task) => {
      // Close the detail modal
      closeTaskDetailModal()

      // Open edit task modal
      editingTask.value = task
      showEditTaskModal.value = true
    }

    const closeEditTaskModal = () => {
      showEditTaskModal.value = false
      editingTask.value = null
    }

    const handleTaskUpdated = async (updatedTask) => {
      // Update the task in the local tasks list
      const index = projectTasks.value.findIndex(t => t.id === updatedTask.id)
      if (index !== -1) {
        projectTasks.value[index] = {
          ...projectTasks.value[index],
          ...updatedTask
        }
      }

      // Show success notification
      notification.success({
        message: 'Task Updated',
        description: `"${updatedTask.title}" has been updated.`,
        placement: 'topRight',
        duration: 3
      })

      // Close modals
      closeEditTaskModal()

      // Reload tasks to ensure we have the latest data
      await loadProjectTasks()
    }

    const handleTaskDelete = async (deletedTask) => {
      // Close the detail modal
      closeTaskDetailModal()

      // Show success notification
      notification.success({
        message: 'Task Deleted',
        description: `"${deletedTask.title}" has been deleted.`,
        placement: 'topRight',
        duration: 3
      })

      // Reload tasks to update the list
      await loadProjectTasks()
    }

    const handleOpenTask = async (task) => {
      console.log('=== HANDLEOPENTASK CALLED IN PROJECTDETAILS ===')
      console.log('Received task:', task)
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${task.id}`)

        if (response.ok) {
          const data = await response.json()
          const rawTask = data.task || data
          
          // Transform the task data to match expected format
          const transformedTask = {
            ...rawTask,
            project: rawTask.project || rawTask.project_id || 'No Project',
            assignee: rawTask.assignee || rawTask.owner_id || 'Unassigned',
            description: rawTask.description || 'No description available',
            priority: rawTask.priority || 5,
            collaborators: typeof rawTask.collaborators === 'string' 
              ? JSON.parse(rawTask.collaborators || '[]') 
              : (rawTask.collaborators || []),
          }
          
          selectedTask.value = transformedTask
          // Keep the modal open and update with new task
          showTaskDetailModal.value = true
          console.log('Task details loaded and transformed:', selectedTask.value)
        } else {
          console.error('Failed to fetch task details')
          notification.error({
            message: 'Failed to load task',
            description: 'Unable to fetch task details. Please try again.',
            placement: 'topRight',
            duration: 3
          })
        }
      } catch (error) {
        console.error('Error fetching task:', error)
        notification.error({
          message: 'Error loading task',
          description: error.message || 'An unexpected error occurred.',
          placement: 'topRight',
          duration: 3
        })
      }
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

    const handleMarkAsCompleted = async () => {
      if (project.value.status === 'Completed') {
        notification.info({
          message: 'Project Already Completed',
          description: 'This project is already marked as completed.',
          placement: 'topRight',
          duration: 3
        })
        return
      }

      try {
        const userId = authStore.user?.user_id

        if (!userId) {
          throw new Error('User not authenticated')
        }

        // Step 1: Mark all tasks in the project as completed
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        let completedTasksCount = 0
        let failedTasksCount = 0

        for (const task of projectTasks.value) {
          // Only update tasks that are not already completed
          if (task.status !== 'Completed') {
            try {
              const taskResponse = await fetch(`${taskServiceUrl}/tasks/${task.id}`, {
                method: 'PUT',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  status: 'Completed'
                })
              })

              if (taskResponse.ok) {
                completedTasksCount++
              } else {
                failedTasksCount++
              }
            } catch (taskError) {
              console.error(`Failed to complete task ${task.id}:`, taskError)
              failedTasksCount++
            }
          }
        }

        // Step 2: Mark the project as completed
        const projectServiceUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const response = await fetch(`${projectServiceUrl}/projects/${project.value.project_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            project_name: project.value.project_name,
            project_description: project.value.project_description,
            due_date: project.value.due_date,
            created_by: project.value.created_by_id,
            user_id: userId,
            collaborators: project.value.collaborators || [],
            status: 'Completed'
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        // Update local project status
        project.value.status = 'Completed'

        // Build notification message
        let description = `"${project.value.project_name}" has been marked as completed.`
        if (completedTasksCount > 0) {
          description += ` ${completedTasksCount} task(s) were also completed.`
        }
        if (failedTasksCount > 0) {
          description += ` Note: ${failedTasksCount} task(s) could not be updated.`
        }

        notification.success({
          message: 'Project Completed',
          description: description,
          placement: 'topRight',
          duration: 4
        })

        // Emit event to update sidebar
        emitProjectUpdated({
          ...project.value,
          status: 'Completed'
        })

        // Reload project and tasks to show updated status
        await loadProject()
        await loadProjectTasks()
      } catch (error) {
        console.error('Failed to mark project as completed:', error)
        notification.error({
          message: 'Failed to Complete Project',
          description: error.message || 'Unable to mark project as completed. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      }
    }

    const handleMarkAsActive = async () => {
      if (project.value.status !== 'Completed') {
        notification.info({
          message: 'Project Not Completed',
          description: 'This project is not marked as completed.',
          placement: 'topRight',
          duration: 3
        })
        return
      }

      try {
        const userId = authStore.user?.user_id

        if (!userId) {
          throw new Error('User not authenticated')
        }

        // Mark the project as Active
        const projectServiceUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const response = await fetch(`${projectServiceUrl}/projects/${project.value.project_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            project_name: project.value.project_name,
            project_description: project.value.project_description,
            due_date: project.value.due_date,
            created_by: project.value.created_by_id,
            user_id: userId,
            collaborators: project.value.collaborators || [],
            status: 'Active'
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        // Update local project status
        project.value.status = 'Active'

        notification.success({
          message: 'Project Reactivated',
          description: `"${project.value.project_name}" has been marked as active.`,
          placement: 'topRight',
          duration: 4
        })

        // Emit event to update sidebar
        emitProjectUpdated({
          ...project.value,
          status: 'Active'
        })

        // Reload project and tasks to show updated status
        await loadProject()
        await loadProjectTasks()
      } catch (error) {
        console.error('Failed to mark project as active:', error)
        notification.error({
          message: 'Failed to Reactivate Project',
          description: error.message || 'Unable to mark project as active. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      }
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
      myTasksSearchQuery,
      otherTasksSearchQuery,
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
      getFilteredMyTasks,
      getFilteredOtherTasks,
      getTaskTimeTaken,
      isUserCollaborator,
      isParentTask,
      isTaskOverdue,
      formatAssigneeNames,
      taskColumns,
      handleEdit,
      handleDelete,
      closeDeleteModal,
      confirmDelete,
      handleProjectUpdated,
      handleTaskClick,
      closeTaskDetailModal,
      handleTaskEdit,
      handleTaskDelete,
      closeEditTaskModal,
      handleTaskUpdated,
      editingTask,
      showEditTaskModal,
      handleOpenTask,
      handleGenerateReport,
      closeReportPreview,
      handleExportPDF,
      showReportPreviewModal,
      reportPreviewData,
      handleMarkAsCompleted,
      handleMarkAsActive
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.action-btn :deep(.anticon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

.action-menu-btn {
  border: 1px solid #d9d9d9;
  color: #6b7280;
}

.action-menu-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

/* Dropdown Menu Icon Colors */
.menu-icon-edit {
  color: #1890ff !important;
}

.menu-icon-complete {
  color: #10b981 !important;
}

.menu-item-complete[disabled] .menu-icon-complete {
  color: #d9d9d9 !important;
}

.menu-icon-active {
  color: #1890ff !important;
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
  flex-wrap: wrap;
}

.stat-item-inline {
  text-align: center;
  min-width: 60px;
  flex-shrink: 0;
}

.stat-number-inline {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  line-height: 1;
  margin-bottom: 4px;
  white-space: nowrap;
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
  white-space: nowrap;
}

.progress-inline {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 140px;
  padding-left: 24px;
  border-left: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.progress-percentage-inline {
  font-size: 24px;
  font-weight: 700;
  color: #667eea;
  text-align: right;
  white-space: nowrap;
}

.progress-bar-inline {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill-inline {
  height: 100%;
  background: linear-gradient(90deg, #10B981, #059669);
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
  gap: 24px;
}

.section-title-group {
  display: flex;
  align-items: center;
  gap: 16px;
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

/* Search Input */
.search-input {
  width: 300px;
  height: 40px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.search-input:hover {
  border-color: #667eea;
}

.search-input:focus,
.search-input:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.search-icon {
  color: #9ca3af;
  font-size: 16px;
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
  background: linear-gradient(90deg, #10B981, #059669);
  border-radius: 6px;
  transition: width 0.6s ease;
}

/* Tasks Table */
.tasks-table-container {
  margin-top: 16px;
}

.tasks-table :deep(.ant-table) {
  background: white;
  border-radius: 8px;
}

.tasks-table :deep(.ant-table-thead > tr > th) {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

.tasks-table :deep(.ant-table-tbody > tr) {
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.tasks-table :deep(.ant-table-tbody > tr:hover) {
  background-color: #f9fafb;
}

/* Overdue task styling - red border and background */
.tasks-table :deep(.ant-table-tbody > tr.overdue-task-row) {
  border: 2px solid #ef4444 !important;
  border-left: 4px solid #dc2626 !important;
  background-color: #fecaca !important;
}

.tasks-table :deep(.ant-table-tbody > tr.overdue-task-row:hover) {
  background-color: #fca5a5 !important;
  border-color: #dc2626 !important;
}

/* Override ALL cell backgrounds in overdue row to red (including sorted column) */
.tasks-table :deep(.ant-table-tbody > tr.overdue-task-row > td) {
  background-color: #fecaca !important;
}

.tasks-table :deep(.ant-table-tbody > tr.overdue-task-row:hover > td) {
  background-color: #fca5a5 !important;
}

/* Override sorted column greyish background for overdue rows */
.tasks-table :deep(.ant-table-tbody > tr.overdue-task-row > td.ant-table-column-sort) {
  background-color: #fecaca !important;
}

.tasks-table :deep(.ant-table-tbody > tr.overdue-task-row:hover > td.ant-table-column-sort) {
  background-color: #fca5a5 !important;
}

.task-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #111827;
  cursor: pointer;
}

.task-title-cell:hover .task-title-text {
  color: #667eea;
}

.task-title-text {
  transition: color 0.2s ease;
}

/* Badge Icons */
.badge-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  flex-shrink: 0;
}

.badge-icon svg {
  width: 14px;
  height: 14px;
}

.badge-icon.subtask {
  background: rgba(88, 86, 214, 0.1);
  color: #5856d6;
}

.badge-icon.subtask:hover {
  background: rgba(88, 86, 214, 0.2);
  transform: scale(1.1);
}

.badge-icon.collaborator {
  background: rgba(175, 82, 222, 0.1);
  color: #af52de;
}

.badge-icon.collaborator:hover {
  background: rgba(175, 82, 222, 0.2);
  transform: scale(1.1);
}

.badge-icon.parent-task {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.badge-icon.parent-task:hover {
  background: rgba(249, 115, 22, 0.2);
  transform: scale(1.1);
}

.task-description-cell {
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-status {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.task-priority-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
}

.overdue-text {
  color: #ef4444;
  font-weight: 600;
}

.completed-text {
  color: #10b981;
  font-weight: 600;
}

.time-taken-cell {
  color: #667eea;
  font-weight: 500;
  font-size: 13px;
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

.task-priority.priority-high,
.task-priority-cell.priority-high {
  color: #ef4444;
}

.task-priority.priority-medium,
.task-priority-cell.priority-medium {
  color: #f59e0b;
}

.task-priority.priority-low,
.task-priority-cell.priority-low {
  color: #06b6d4;
}

.task-priority.priority-lowest,
.task-priority-cell.priority-lowest {
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
    min-width: 55px;
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

@media (max-width: 900px) {
  .progress-stats-inline {
    gap: 12px;
  }

  .stat-item-inline {
    min-width: 45px;
  }

  .stat-number-inline {
    font-size: 20px;
  }

  .stat-label-inline {
    font-size: 10px;
  }

  .progress-inline {
    min-width: 100px;
  }

  .progress-percentage-inline {
    font-size: 18px;
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

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .search-input {
    width: 100%;
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
