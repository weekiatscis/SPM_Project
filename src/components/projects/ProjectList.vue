<template>
  <!-- Project Form Modal -->
  <ProjectFormModal
    :isOpen="showProjectModal"
    @close="showProjectModal = false"
    @save="handleProjectSaved"
  />


  <div>
    <!-- Tabs Container with Background Illustration -->
    <div class="tabs-container-wrapper">
      <!-- Section Toggle Tabs with Stats and Button -->
      <div class="tabs-header-row">
        <div class="tabs-section">
          <!-- GIF Behind Tabs -->
          <div class="tabs-background-illustration">
            <img
              src="/ProjectIllustration.gif"
              alt="Project illustration"
              class="project-illustration-gif"
            />
          </div>

          <a-tabs v-model:activeKey="activeTab">
          <a-tab-pane key="all" tab="Ongoing Projects" />
          <a-tab-pane key="owned" tab="My Projects" />
          <a-tab-pane key="collaborating" tab="Collaborating" />
          <a-tab-pane key="completed" tab="Completed" />
          </a-tabs>
        </div>

        <div class="header-actions">
        <div class="stats-container">
          <div class="stat-card stat-total">
            <div class="stat-icon">📊</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">Total</div>
            </div>
          </div>

          <div class="stat-card stat-active">
            <div class="stat-icon">🚀</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">Active</div>
            </div>
          </div>

          <div class="stat-card stat-completed">
            <div class="stat-icon">✓</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completed }}</div>
              <div class="stat-label">Completed</div>
            </div>
          </div>
        </div>

        <button class="new-project-btn" @click="handleOpenModal">
          <PlusOutlined class="btn-icon" />
          <span>New Project</span>
        </button>
        </div>
      </div>
    </div>

    <!-- Ongoing Projects Section -->
    <a-card
      v-if="activeTab === 'all'"
      style="min-height: 500px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span>Ongoing Projects</span>
            <a-input
              v-model:value="ongoingSearchQuery"
              placeholder="Search projects..."
              size="small"
              style="width: 200px;"
              allow-clear
            >
              <template #prefix>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 14px; height: 14px; opacity: 0.5;">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </template>
            </a-input>
            <!-- Sortable Headers -->
            <div class="sortable-headers">
              <button
                class="sort-header"
                :class="{ active: sortBy.startsWith('name') }"
                @click="toggleSort('name')"
              >
                Name
                <span class="sort-arrow">{{ sortBy === 'name-asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'due_date' }"
                @click="toggleSort('due_date')"
              >
                Due Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'created_at' }"
                @click="toggleSort('created_at')"
              >
                Created Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
            </div>
          </div>
          <a-button type="primary" @click="activeTab = 'assign'" class="assign-task-btn">
            Assign Task
          </a-button>
        </div>
      </template>

      <div v-if="isLoading" style="text-align: center; padding: 50px;">
        <a-spin size="large" />
        <p style="margin-top: 16px;">Loading projects...</p>
      </div>

      <div v-else-if="allProjects.length === 0" style="text-align: center; padding: 50px;">
        <a-empty description="No projects found">
          <a-button type="primary" @click="showProjectModal = true">
            Create Your First Project
          </a-button>
        </a-empty>
      </div>

      <a-row v-else :gutter="[16, 16]">
        <a-col
          v-for="project in allProjects"
          :key="project.project_id"
          :xs="24"
          :sm="12"
          :lg="8"
          :xl="6"
        >
          <ProjectCard
            :project="project"
            :current-user-id="currentUserId"
            @view-details="handleProjectClick"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- My Projects Section -->
    <a-card
      v-if="activeTab === 'owned'"
      style="min-height: 500px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span>My Projects</span>
            <a-input
              v-model:value="myProjectsSearchQuery"
              placeholder="Search projects..."
              size="small"
              style="width: 200px;"
              allow-clear
            >
              <template #prefix>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 14px; height: 14px; opacity: 0.5;">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </template>
            </a-input>
            <!-- Sortable Headers -->
            <div class="sortable-headers">
              <button
                class="sort-header"
                :class="{ active: sortBy.startsWith('name') }"
                @click="toggleSort('name')"
              >
                Name
                <span class="sort-arrow">{{ sortBy === 'name-asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'due_date' }"
                @click="toggleSort('due_date')"
              >
                Due Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'created_at' }"
                @click="toggleSort('created_at')"
              >
                Created Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
            </div>
          </div>
          <a-button type="primary" @click="activeTab = 'assign'" class="assign-task-btn">
            Assign Task
          </a-button>
        </div>
      </template>

      <div v-if="isLoading" style="text-align: center; padding: 50px;">
        <a-spin size="large" />
        <p style="margin-top: 16px;">Loading projects...</p>
      </div>

      <div v-else-if="ownedProjects.length === 0" style="text-align: center; padding: 50px;">
        <a-empty description="You haven't created any projects yet">
          <a-button type="primary" @click="showProjectModal = true">
            Create Your First Project
          </a-button>
        </a-empty>
      </div>

      <a-row v-else :gutter="[16, 16]">
        <a-col
          v-for="project in ownedProjects"
          :key="project.project_id"
          :xs="24"
          :sm="12"
          :lg="8"
          :xl="6"
        >
          <ProjectCard
            :project="project"
            :current-user-id="currentUserId"
            @view-details="handleProjectClick"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- Collaborating Projects Section -->
    <a-card
      v-if="activeTab === 'collaborating'"
      style="min-height: 500px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span>Collaborating</span>
            <a-input
              v-model:value="collaboratingSearchQuery"
              placeholder="Search projects..."
              size="small"
              style="width: 200px;"
              allow-clear
            >
              <template #prefix>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 14px; height: 14px; opacity: 0.5;">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </template>
            </a-input>
            <!-- Sortable Headers -->
            <div class="sortable-headers">
              <button
                class="sort-header"
                :class="{ active: sortBy.startsWith('name') }"
                @click="toggleSort('name')"
              >
                Name
                <span class="sort-arrow">{{ sortBy === 'name-asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'due_date' }"
                @click="toggleSort('due_date')"
              >
                Due Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'created_at' }"
                @click="toggleSort('created_at')"
              >
                Created Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
            </div>
          </div>
          <a-button type="primary" @click="activeTab = 'assign'" class="assign-task-btn">
            Assign Task
          </a-button>
        </div>
      </template>

      <div v-if="isLoading" style="text-align: center; padding: 50px;">
        <a-spin size="large" />
        <p style="margin-top: 16px;">Loading projects...</p>
      </div>

      <div v-else-if="collaboratingProjects.length === 0" style="text-align: center; padding: 50px;">
        <a-empty description="You are not collaborating on any projects yet" />
      </div>

      <a-row v-else :gutter="[16, 16]">
        <a-col
          v-for="project in collaboratingProjects"
          :key="project.project_id"
          :xs="24"
          :sm="12"
          :lg="8"
          :xl="6"
        >
          <ProjectCard
            :project="project"
            :current-user-id="currentUserId"
            @view-details="handleProjectClick"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- Completed Projects Section -->
    <a-card
      v-if="activeTab === 'completed'"
      style="min-height: 500px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span>Completed Projects</span>
            <a-input
              v-model:value="completedSearchQuery"
              placeholder="Search projects..."
              size="small"
              style="width: 200px;"
              allow-clear
            >
              <template #prefix>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 14px; height: 14px; opacity: 0.5;">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </template>
            </a-input>
            <!-- Sortable Headers -->
            <div class="sortable-headers">
              <button
                class="sort-header"
                :class="{ active: sortBy.startsWith('name') }"
                @click="toggleSort('name')"
              >
                Name
                <span class="sort-arrow">{{ sortBy === 'name-asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'due_date' }"
                @click="toggleSort('due_date')"
              >
                Due Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
              <button
                class="sort-header"
                :class="{ active: sortBy === 'created_at' }"
                @click="toggleSort('created_at')"
              >
                Created Date
                <span class="sort-arrow">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
              </button>
            </div>
          </div>
          <a-button type="primary" @click="activeTab = 'assign'" class="assign-task-btn">
            Assign Task
          </a-button>
        </div>
      </template>

      <div v-if="isLoading" style="text-align: center; padding: 50px;">
        <a-spin size="large" />
        <p style="margin-top: 16px;">Loading projects...</p>
      </div>

      <div v-else-if="completedProjects.length === 0" style="text-align: center; padding: 50px;">
        <a-empty description="No completed projects yet" />
      </div>

      <a-row v-else :gutter="[16, 16]">
        <a-col
          v-for="project in completedProjects"
          :key="project.project_id"
          :xs="24"
          :sm="12"
          :lg="8"
          :xl="6"
        >
          <ProjectCard
            :project="project"
            :current-user-id="currentUserId"
            @view-details="handleProjectClick"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- Assign Task Section -->
    <a-card
      v-if="activeTab === 'assign'"
      style="min-height: 500px;"
    >


      <!-- Two Column Layout -->
      <a-row :gutter="16" style="height: 450px;">
        <!-- Left Side - Tasks List (30%) -->
        <a-col :span="7">
          <div style="border-right: 1px solid #f0f0f0; padding-right: 16px; height: 100%;">
            <div style="margin-bottom: 16px;">
              <h4 style="margin: 0 0 12px 0;">Available Tasks</h4>
              <div style="display: flex; gap: 8px;">
                <a-button
                  size="small"
                  :type="taskSortBy.startsWith('dueDate') ? 'primary' : 'default'"
                  @click="toggleTaskDueDateSort"
                  style="flex: 1;"
                >
                  Due Date {{ taskSortBy === 'dueDate-asc' ? '↑' : taskSortBy === 'dueDate-desc' ? '↓' : '↑' }}
                </a-button>
                <a-select
                  v-model:value="taskStatusFilter"
                  size="small"
                  placeholder="Status"
                  style="flex: 1;"
                  allow-clear
                >
                  <a-select-option value="">All</a-select-option>
                  <a-select-option value="Unassigned">Unassigned</a-select-option>
                  <a-select-option value="Ongoing">Ongoing</a-select-option>
                  <a-select-option value="Under Review">Under Review</a-select-option>
                </a-select>
              </div>
            </div>

            <div v-if="isLoadingTasks" style="text-align: center; padding: 50px;">
              <a-spin size="large" />
              <p style="margin-top: 16px;">Loading tasks...</p>
            </div>

            <div v-else-if="allAvailableTasks.length === 0" style="text-align: center; padding: 50px;">
              <a-empty description="No tasks found" />
            </div>

            <a-list
              v-else
              :data-source="allAvailableTasks"
              style="height: 350px; overflow-y: auto;"
            >
              <template #renderItem="{ item }">
                <a-list-item
                  style="cursor: pointer; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #f0f0f0;"
                  :style="isTaskSelected(item) ? { background: '#e6f7ff', border: '1px solid #1890ff' } : { background: 'white' }"
                  @click="selectTaskForAssign(item)"
                >
                  <div style="width: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;">
                      <strong style="flex: 1; font-size: 14px; line-height: 1.5; word-break: break-word;">{{ item.title }}</strong>
                      <a-tag :color="getTaskStatusColor(item.status)" size="small" style="flex-shrink: 0; margin-top: 2px;">
                        {{ item.status }}
                      </a-tag>
                    </div>
                    <div style="font-size: 12px; color: #666;">
                      Due: {{ item.dueDate ? formatDate(item.dueDate) : 'No due date' }}
                    </div>
                  </div>
                </a-list-item>
              </template>
            </a-list>
          </div>
        </a-col>

        <!-- Right Side - Project Assignment (70%) -->
        <a-col :span="17">
          <div style="padding-left: 16px; height: 100%;">
            <div v-if="selectedTasksForAssign.length > 0" style="margin-bottom: 16px;">
              <div style="font-size: 14px; color: #666; margin-bottom: 8px;">
                Selected Tasks ({{ selectedTasksForAssign.length }}):
              </div>
              <div style="max-height: 60px; overflow-y: auto;">
                <a-tag
                  v-for="task in selectedTasksForAssign"
                  :key="task.id"
                  closable
                  @close="selectTaskForAssign(task)"
                  style="margin-bottom: 4px;"
                >
                  {{ task.title }}
                </a-tag>
              </div>
            </div>

            <div v-if="selectedTasksForAssign.length === 0" style="text-align: center; padding: 50px;">
              <a-empty description="Select tasks from the left to assign them to a project" />
            </div>

            <div v-else>
              <!-- Search Projects -->
              <div style="margin-bottom: 16px;">
                <a-input-search
                  v-model:value="projectSearchQuery"
                  placeholder="Search projects..."
                  style="width: 100%;"
                  @search="searchProjects"
                  allow-clear
                />
              </div>

              <div v-if="isLoading" style="text-align: center; padding: 50px;">
                <a-spin size="large" />
                <p style="margin-top: 16px;">Loading projects...</p>
              </div>

              <div v-else-if="filteredProjectsForAssign.length === 0" style="text-align: center; padding: 50px;">
                <a-empty description="No projects found" />
              </div>

              <div v-else>
                <div style="margin-bottom: 8px; font-size: 12px; color: #666;">
                  {{ filteredProjectsForAssign.length }} project(s) available
                </div>
                <a-list
                  :data-source="filteredProjectsForAssign"
                  style="height: 300px; overflow-y: auto; border: 1px solid #f0f0f0; border-radius: 4px;"
                >
                  <template #renderItem="{ item }">
                    <a-list-item
                      style="cursor: pointer; padding: 12px 16px; border-bottom: 1px solid #f5f5f5;"
                      :style="selectedProjectForAssign?.project_id === item.project_id ? { background: '#f0f9ff', border: '1px solid #1890ff' } : { background: 'white' }"
                      @click="selectProjectForAssign(item)"
                    >
                      <div style="width: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                          <div style="display: flex; align-items: center; gap: 8px;">
                            <strong style="font-size: 14px;">{{ item.project_name }}</strong>
                            <a-tag :color="getProjectStatusColor(item.status)" size="small">
                              {{ item.status }}
                            </a-tag>
                            <a-tag v-if="isUserCollaborator(item)" class="collaborator-badge" size="small">
                              Collaborator
                            </a-tag>
                          </div>
                          <div v-if="selectedProjectForAssign?.project_id === item.project_id">
                            <a-button
                              type="primary"
                              size="small"
                              @click.stop="assignTaskToProject"
                              :loading="isAssigning"
                            >
                              Assign {{ selectedTasksForAssign.length > 1 ? 'Tasks' : 'Task' }}
                            </a-button>
                          </div>
                        </div>
                        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
                          {{ item.project_description || 'No description' }}
                        </div>
                        <div style="font-size: 11px; color: #999;">
                          Created: {{ formatDate(item.created_at) }} • By: {{ item.created_by }}
                        </div>
                        <div style="font-size: 11px; color: #999;">
                          Due: {{ formatProjectDueDate(item.due_date) }}
                        </div>
                      </div>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, UpOutlined, DownOutlined } from '@ant-design/icons-vue'
import { notification } from 'ant-design-vue'
import { useAuthStore } from '../../stores/auth'
import ProjectFormModal from './ProjectFormModal.vue'
import ProjectCard from './ProjectCard.vue'

export default {
  name: 'ProjectList',
  components: {
    PlusOutlined,
    ProjectFormModal,
    ProjectCard
  },
  props: {
    stats: {
      type: Object,
      default: () => ({ total: 0, active: 0, completed: 0 })
    }
  },
  emits: ['create-project', 'open-modal'],
  setup(props, { emit }) {
    const router = useRouter()
    const projects = ref([])
    const isLoading = ref(false)
    const sortBy = ref('due_date')
    const sortDirection = ref('asc') // Track sort direction for due_date and created_at
    const authStore = useAuthStore()

    // Search queries for each tab
    const ongoingSearchQuery = ref('')
    const myProjectsSearchQuery = ref('')
    const collaboratingSearchQuery = ref('')
    const completedSearchQuery = ref('')

    // Tab state for switching between sections
    const activeTab = ref('all')

    // Modal state for creating project
    const showProjectModal = ref(false)

    // Task assignment state
    const tasks = ref([])
    const isLoadingTasks = ref(false)
    const taskSortBy = ref('dueDate-asc')
    const taskStatusFilter = ref('')
    const selectedTasksForAssign = ref([])

    // Project assignment state
    const projectSearchQuery = ref('')
    const selectedProjectForAssign = ref(null)
    const isAssigning = ref(false)

    // Method to add new project (can be called from parent component)
    const addNewProject = async (projectData) => {
      console.log('ProjectList.addNewProject called with:', projectData)

      // Fetch the user name for the created_by user_id
      const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
      let createdByName = projectData.created_by

      try {
        const userResponse = await fetch(`${taskServiceUrl}/users/${projectData.created_by}`)
        if (userResponse.ok) {
          const userData = await userResponse.json()
          createdByName = userData.user?.name || projectData.created_by
        }
      } catch (err) {
        console.error(`Failed to fetch user name for ${projectData.created_by}:`, err)
      }

      // Transform the API response to match frontend format
      const mappedProject = {
        project_id: projectData.project_id || projectData.id,
        project_name: projectData.project_name,
        project_description: projectData.project_description,
        created_at: projectData.created_at,
        created_by: createdByName, // Use the fetched user name
        created_by_id: projectData.created_by,
        due_date: projectData.due_date,
        collaborators: projectData.collaborators || [],
        status: projectData.status || 'Active'
      }

      // Add the new project to the projects list
      projects.value.unshift(mappedProject)
      console.log('Project added to ProjectList, total:', projects.value.length)
    }

    // Handle project saved from ProjectFormModal (for internal modal)
    const handleProjectSaved = async (projectData) => {
      await addNewProject(projectData)

      // Show success notification
      notification.success({
        message: 'Project created successfully',
        description: `"${projectData.project_name}" has been added to your projects.`,
        placement: 'topRight',
        duration: 3
      })

      // Close the modal
      showProjectModal.value = false
    }

    // Handle project click - navigate to project details page
    const handleProjectClick = async (project) => {
      router.push(`/projects/${project.project_id}`)
    }

    // Handle opening modal from button
    const handleOpenModal = () => {
      emit('open-modal')
    }


    // Helper function to apply sorting
    const applySorting = (projectList) => {
      const sorted = [...projectList]

      if (sortBy.value === 'name-asc') {
        return sorted.sort((a, b) => a.project_name.localeCompare(b.project_name))
      } else if (sortBy.value === 'name-desc') {
        return sorted.sort((a, b) => b.project_name.localeCompare(a.project_name))
      } else if (sortBy.value === 'created_at') {
        return sorted.sort((a, b) => {
          if (sortDirection.value === 'asc') {
            // Oldest first
            return new Date(a.created_at) - new Date(b.created_at)
          } else {
            // Newest first (default)
            return new Date(b.created_at) - new Date(a.created_at)
          }
        })
      } else if (sortBy.value === 'due_date') {
        return sorted.sort((a, b) => {
          // Handle null/undefined due dates - push them to the end
          if (!a.due_date) return 1
          if (!b.due_date) return -1

          if (sortDirection.value === 'asc') {
            // Earliest first (closest due date first)
            return new Date(a.due_date) - new Date(b.due_date)
          } else {
            // Latest first (furthest due date first)
            return new Date(b.due_date) - new Date(a.due_date)
          }
        })
      }

      return sorted
    }

    // Toggle sort function
    const toggleSort = (field) => {
      if (field === 'name') {
        // Toggle between asc and desc for name
        if (sortBy.value === 'name-asc') {
          sortBy.value = 'name-desc'
        } else {
          sortBy.value = 'name-asc'
        }
      } else {
        // For due_date and created_at, toggle direction
        if (sortBy.value === field) {
          // Same field, toggle direction
          sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
        } else {
          // Different field, set it and default to desc for created_at, asc for due_date
          sortBy.value = field
          sortDirection.value = field === 'created_at' ? 'desc' : 'asc'
        }
      }
    }

    // Ongoing projects (exclude completed projects)
    const allProjects = computed(() => {
      let ongoing = projects.value.filter(p => p.status !== 'Completed')

      // Apply search filter
      if (ongoingSearchQuery.value) {
        const query = ongoingSearchQuery.value.toLowerCase().trim()
        ongoing = ongoing.filter(p =>
          p.project_name.toLowerCase().includes(query) ||
          (p.project_description && p.project_description.toLowerCase().includes(query))
        )
      }

      return applySorting(ongoing)
    })

    // Owned projects (where user is the creator, excluding completed)
    const ownedProjects = computed(() => {
      const currentUserId = authStore.user?.user_id
      let owned = projects.value.filter(p =>
        p.created_by_id === currentUserId &&
        p.status !== 'Completed'
      )

      // Apply search filter
      if (myProjectsSearchQuery.value) {
        const query = myProjectsSearchQuery.value.toLowerCase().trim()
        owned = owned.filter(p =>
          p.project_name.toLowerCase().includes(query) ||
          (p.project_description && p.project_description.toLowerCase().includes(query))
        )
      }

      return applySorting(owned)
    })

    // Collaborating projects (where user is in collaborators array but not the creator, excluding completed)
    const collaboratingProjects = computed(() => {
      const currentUserId = authStore.user?.user_id
      let collaborating = projects.value.filter(p =>
        p.created_by_id !== currentUserId &&
        p.collaborators &&
        p.collaborators.includes(currentUserId) &&
        p.status !== 'Completed'
      )

      // Apply search filter
      if (collaboratingSearchQuery.value) {
        const query = collaboratingSearchQuery.value.toLowerCase().trim()
        collaborating = collaborating.filter(p =>
          p.project_name.toLowerCase().includes(query) ||
          (p.project_description && p.project_description.toLowerCase().includes(query))
        )
      }

      return applySorting(collaborating)
    })

    // Completed projects (where user is the creator OR collaborator, and status is Completed)
    const completedProjects = computed(() => {
      const currentUserId = authStore.user?.user_id
      let completed = projects.value.filter(p => {
        const isOwner = p.created_by_id === currentUserId
        const isCollaborator = p.collaborators && p.collaborators.includes(currentUserId)
        return (isOwner || isCollaborator) && p.status === 'Completed'
      })

      // Apply search filter
      if (completedSearchQuery.value) {
        const query = completedSearchQuery.value.toLowerCase().trim()
        completed = completed.filter(p =>
          p.project_name.toLowerCase().includes(query) ||
          (p.project_description && p.project_description.toLowerCase().includes(query))
        )
      }

      return applySorting(completed)
    })

    // Function to handle sort change

    // Computed property for current user ID (safely handles undefined authStore)
    const currentUserId = computed(() => {
      return authStore?.user?.user_id || null
    })

    // Task-related functions
    const loadTasks = async () => {
      isLoadingTasks.value = true
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const ownerId = authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID || ''
        const url = ownerId
          ? `${baseUrl}/tasks?owner_id=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/tasks`
        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
        tasks.value = apiTasks.map(t => ({
          id: t.id,
          title: t.title,
          dueDate: t.dueDate || null,
          status: t.status,
          project_id: t.project_id || null
        }))
      } catch (error) {
        console.error('Failed to load tasks:', error)
        tasks.value = []
        notification.error({
          message: 'Failed to load tasks',
          description: error.message || 'Unable to fetch tasks. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      } finally {
        isLoadingTasks.value = false
      }
    }

    // All available tasks computed property with sorting and filtering - only unassigned tasks, excluding completed
    const allAvailableTasks = computed(() => {
      // Filter tasks that are not assigned to any project (project_id is null/undefined)
      // and exclude completed tasks
      let filteredTasks = tasks.value.filter(task =>
        (!task.project_id || task.project_id === null) &&
        task.status !== 'Completed'
      )

      // Apply status filter if selected
      if (taskStatusFilter.value) {
        filteredTasks = filteredTasks.filter(task => task.status === taskStatusFilter.value)
      }

      let sortedTasks = [...filteredTasks]

      // Apply sorting
      if (taskSortBy.value === 'dueDate-asc') {
        return sortedTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(a.dueDate) - new Date(b.dueDate)
        })
      } else if (taskSortBy.value === 'dueDate-desc') {
        return sortedTasks.sort((a, b) => {
          if (!a.dueDate) return 1
          if (!b.dueDate) return -1
          return new Date(b.dueDate) - new Date(a.dueDate)
        })
      }

      return sortedTasks
    })

    // Task sort functions
    const toggleTaskDueDateSort = () => {
      if (taskSortBy.value === 'dueDate-asc') {
        taskSortBy.value = 'dueDate-desc'
      } else {
        taskSortBy.value = 'dueDate-asc'
      }
    }

    // Task selection - toggle behavior for multiple selection
    const selectTaskForAssign = (task) => {
      const index = selectedTasksForAssign.value.findIndex(t => t.id === task.id)

      if (index > -1) {
        // Task is already selected, remove it (unselect)
        selectedTasksForAssign.value.splice(index, 1)
      } else {
        // Task is not selected, add it (select)
        selectedTasksForAssign.value.push(task)
      }
    }

    // Helper function to check if a task is selected
    const isTaskSelected = (task) => {
      return selectedTasksForAssign.value.some(t => t.id === task.id)
    }

    // Helper functions
    const formatDate = (dateString) => {
      if (!dateString) return 'No due date'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    }

    const formatProjectDueDate = (dateString) => {
      if (!dateString) return 'No due date'

      const date = new Date(dateString)
      const now = new Date()
      const timeDiff = date.getTime() - now.getTime()
      const daysDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24))

      if (daysDiff < 0) {
        return `Overdue by ${Math.abs(daysDiff)} day(s)`
      } else if (daysDiff === 0) {
        return 'Due today'
      } else if (daysDiff === 1) {
        return 'Due tomorrow'
      } else if (daysDiff <= 7) {
        return `Due in ${daysDiff} day(s)`
      } else {
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        })
      }
    }

    const getTaskStatusColor = (status) => {
      const colors = {
        'Unassigned': 'default',
        'Ongoing': 'blue',
        'Under Review': 'gold',
        'Completed': 'green'
      }
      return colors[status] || 'default'
    }

    // Project assignment functions
    const filteredProjectsForAssign = computed(() => {
      // Exclude completed projects from assignment
      const activeProjects = projects.value.filter(p => p.status !== 'Completed')

      if (!projectSearchQuery.value) {
        return activeProjects
      }

      const query = projectSearchQuery.value.toLowerCase()
      return activeProjects.filter(project =>
        project.project_name.toLowerCase().includes(query) ||
        (project.project_description || '').toLowerCase().includes(query) ||
        project.created_by.toLowerCase().includes(query)
      )
    })

    const searchProjects = () => {
      // Search is reactive through computed property
      // This function can be used for additional search logic if needed
    }

    const selectProjectForAssign = (project) => {
      selectedProjectForAssign.value = project
    }

    const getProjectStatusColor = (status) => {
      const colors = {
        'Active': 'blue',
        'Planning': 'cyan',
        'On Hold': 'orange',
        'Completed': 'green',
        'Cancelled': 'red'
      }
      return colors[status] || 'default'
    }

    const isUserCollaborator = (project) => {
      if (!currentUserId || !project.collaborators) return false
      return Array.isArray(project.collaborators) && project.collaborators.includes(currentUserId)
    }

    const assignTaskToProject = async () => {
      if (selectedTasksForAssign.value.length === 0 || !selectedProjectForAssign.value) return

      isAssigning.value = true
      let successCount = 0
      let failureCount = 0

      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const projectId = selectedProjectForAssign.value.project_id

        // Process each selected task
        for (const task of selectedTasksForAssign.value) {
          try {
            const response = await fetch(`${baseUrl}/tasks/${task.id}`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                project_id: projectId
              })
            })

            if (!response.ok) {
              const errorData = await response.json()
              throw new Error(errorData.error || `HTTP ${response.status}`)
            }

            // Update the task in the local tasks array to reflect the assignment
            const taskIndex = tasks.value.findIndex(t => t.id === task.id)
            if (taskIndex !== -1) {
              tasks.value[taskIndex] = {
                ...tasks.value[taskIndex],
                project_id: projectId,
                project: selectedProjectForAssign.value.project_name
              }
            }

            successCount++
          } catch (taskError) {
            console.error(`Failed to assign task "${task.title}":`, taskError)
            failureCount++
          }
        }

        // Show appropriate notification based on results
        if (successCount > 0 && failureCount === 0) {
          notification.success({
            message: 'Tasks assigned successfully',
            description: `${successCount} task(s) have been assigned to project "${selectedProjectForAssign.value.project_name}".`,
            placement: 'topRight',
            duration: 3
          })
        } else if (successCount > 0 && failureCount > 0) {
          notification.warning({
            message: 'Partial assignment completed',
            description: `${successCount} task(s) assigned successfully, ${failureCount} failed.`,
            placement: 'topRight',
            duration: 4
          })
        } else if (failureCount > 0) {
          notification.error({
            message: 'Assignment failed',
            description: `Failed to assign ${failureCount} task(s) to the project.`,
            placement: 'topRight',
            duration: 4
          })
        }

        // Reset selections
        selectedTasksForAssign.value = []
        selectedProjectForAssign.value = null
        projectSearchQuery.value = ''

      } catch (error) {
        console.error('Failed to assign tasks:', error)
        notification.error({
          message: 'Failed to assign tasks',
          description: error.message || 'Unable to assign tasks to project. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      } finally {
        isAssigning.value = false
      }
    }

    onMounted(async () => {
      // Load projects
      isLoading.value = true
      try {
        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const ownerId = authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID || ''
        const url = ownerId
          ? `${baseUrl}/projects?created_by=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/projects`

        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const payload = await response.json()
        const apiProjects = Array.isArray(payload?.projects) ? payload.projects : []

        // Map projects and fetch user names
        const projectsWithUserIds = apiProjects.map(p => ({
          project_id: p.project_id,
          project_name: p.project_name,
          project_description: p.project_description,
          created_at: p.created_at,
          created_by: p.created_by, // This is still user_id
          created_by_id: p.created_by, // Store the original user_id
          due_date: p.due_date,
          collaborators: p.collaborators || [], // Store collaborators array
          status: p.status || 'Active' // Use status from API, default to Active if not present
        }))

        // Fetch user names for all unique created_by user IDs
        const uniqueUserIds = [...new Set(projectsWithUserIds.map(p => p.created_by).filter(Boolean))]
        const userNameMap = {}

        // Fetch user names from task service
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        for (const userId of uniqueUserIds) {
          try {
            const userResponse = await fetch(`${taskServiceUrl}/users/${userId}`)
            if (userResponse.ok) {
              const userData = await userResponse.json()
              userNameMap[userId] = userData.user?.name || userId
            } else {
              userNameMap[userId] = userId // Fallback to user_id if fetch fails
            }
          } catch (err) {
            console.error(`Failed to fetch user name for ${userId}:`, err)
            userNameMap[userId] = userId // Fallback to user_id
          }
        }

        // Replace user_id with user name
        projects.value = projectsWithUserIds.map(p => ({
          ...p,
          created_by: userNameMap[p.created_by_id] || p.created_by_id || 'Unknown'
        }))
      } catch (error) {
        console.error('Failed to load projects:', error)
        projects.value = []
        notification.error({
          message: 'Failed to load projects',
          description: error.message || 'Unable to fetch projects. Please try again.',
          placement: 'topRight',
          duration: 4
        })
      } finally {
        isLoading.value = false
      }

      // Load tasks for assignment
      await loadTasks()
    })

    return {
      h,
      allProjects,
      ownedProjects,
      collaboratingProjects,
      completedProjects,
      isLoading,
      activeTab,
      showProjectModal,
      sortBy,
      sortDirection,
      toggleSort,
      handleProjectSaved,
      addNewProject, // Expose this method to parent
      handleProjectClick,
      handleOpenModal, // Expose to handle button click
      currentUserId, // Expose current user ID
      // Search queries for each tab
      ongoingSearchQuery,
      myProjectsSearchQuery,
      collaboratingSearchQuery,
      completedSearchQuery,
      // Task assignment related
      allAvailableTasks,
      isLoadingTasks,
      taskSortBy,
      taskStatusFilter,
      selectedTasksForAssign,
      toggleTaskDueDateSort,
      selectTaskForAssign,
      isTaskSelected,
      formatDate,
      formatProjectDueDate,
      getTaskStatusColor,
      // Project assignment related
      filteredProjectsForAssign,
      projectSearchQuery,
      selectedProjectForAssign,
      isAssigning,
      searchProjects,
      selectProjectForAssign,
      getProjectStatusColor,
      isUserCollaborator,
      assignTaskToProject
    }
  }
}
</script>

<style scoped>
/* Custom card grid spacing */
:deep(.ant-col) {
  margin-bottom: 24px;
}

/* Enhanced card hover effects */
:deep(.ant-card) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(229, 231, 235, 0.6);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

:deep(.ant-card:hover) {
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
  border-color: rgba(209, 213, 219, 0.8);
}

:deep(.ant-card-head) {
  border-bottom: 1px solid rgba(229, 231, 235, 0.6);
  background: transparent;
  font-weight: 600;
}

:deep(.ant-card-head-title) {
  font-size: 18px;
  font-weight: 600;
  color: #1F2937;
}

:deep(.ant-tabs) {
  background: #ffffff;
  border-radius: 12px;
  padding: 4px;
  border: 1px solid rgba(16, 185, 129, 0.1);
}

:deep(.ant-tabs-nav) {
  margin: 0 !important;
  background-color: #ffffff;
}

:deep(.ant-tabs-tab) {
  padding: 10px 24px;
  border-radius: 8px;
  margin: 0 4px !important;
  color: #6B7280;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.ant-tabs-tab:hover) {
  color: #10B981;
  background: rgba(16, 185, 129, 0.05);
}

:deep(.ant-tabs-tab-active) {
  background: #10B981 !important;
  color: white !important;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

:deep(.ant-tabs-tab-active .ant-tabs-tab-btn) {
  color: white !important;
}

:deep(.ant-tabs-ink-bar) {
  display: none;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #10B981, #059669);
  border: none;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

:deep(.ant-btn-default) {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  color: #6B7280;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.ant-btn-default:hover) {
  border-color: #10B981;
  color: #10B981;
  background: rgba(16, 185, 129, 0.05);
}

:deep(.ant-empty) {
  padding: 40px 20px;
}

:deep(.ant-empty-description) {
  color: #6B7280;
  font-size: 14px;
}

/* Tabs Container Wrapper - Like Home's timeline wrapper */
.tabs-container-wrapper {
  position: relative;
  margin-bottom: 16px;
}

/* Tabs Header Row */
.tabs-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  position: relative;
  z-index: 2;
}

.tabs-section {
  flex: 1;
  min-width: 0;
  position: relative;
}

/* Background Illustration - Positioned behind tabs at right edge of ant-tabs */
.tabs-section {
  position: relative;
}

.tabs-background-illustration {
  position: absolute;
  top: -100%;
  right: 0;
  transform: translateY(-50%);
  z-index: 0;
  pointer-events: none;
}

.project-illustration-gif {
  width: 180px;
  height: 150px;
  border-radius: 8px;
  display: block;
  opacity: 0.9;
}

/* Ensure tabs content stays above illustration */
:deep(.ant-tabs) {
  position: relative;
  z-index: 1;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.stats-container {
  display: flex;
  gap: 8px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(229, 231, 235, 0.6);
  border-radius: 10px;
  min-width: 90px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.stat-total {
  border-color: rgba(229, 231, 235, 0.6);
}

.stat-active {
  border-color: rgba(229, 231, 235, 0.6);
  background: rgba(255, 255, 255, 0.9);
}

.stat-completed {
  border-color: rgba(229, 231, 235, 0.6);
  background: rgba(255, 255, 255, 0.9);
}

.stat-icon {
  font-size: 20px;
  line-height: 1;
  filter: grayscale(0.2);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 0px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
  color: #1F2937;
}

.stat-active .stat-value {
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-completed .stat-value {
  background: linear-gradient(135deg, #10B981, #059669);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 10px;
  font-weight: 600;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-top: 2px;
}

.new-project-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  background: linear-gradient(135deg, #10B981, #059669);
  color: white;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
  white-space: nowrap;
}

.new-project-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
}

.new-project-btn:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 16px;
  font-weight: bold;
}

:deep(.assign-task-btn) {
  height: 36px;
  padding: 0 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #1890ff, #096dd9) !important;
  border-color: #1890ff !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2) !important;
}

:deep(.assign-task-btn:hover) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #40a9ff, #1890ff) !important;
  border-color: #40a9ff !important;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3) !important;
}

:deep(.assign-task-btn:active) {
  background: linear-gradient(135deg, #096dd9, #0050b3) !important;
  border-color: #096dd9 !important;
}

.collaborator-badge {
  background: #FEF3C7 !important;
  color: #D97706 !important;
  border: 1px solid #FDE68A !important;
  border-radius: 12px !important;
  padding: 2px 10px !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  margin: 0 !important;
}

/* Responsive Design */
@media (max-width: 1400px) {
  .tabs-header-row {
    flex-wrap: wrap;
  }

  .tabs-section {
    flex-basis: 100%;
  }

  .project-illustration-gif {
    width: 100px;
  }

  .header-actions {
    flex-basis: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 1024px) {
  .project-illustration-gif {
    width: 90px;
  }

  .tabs-background-illustration {
    right: -20px;
  }
}

@media (max-width: 768px) {
  .tabs-background-illustration {
    display: none; /* Hide illustration on mobile */
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .stats-container {
    justify-content: space-between;
  }

  .stat-card {
    flex: 1;
    min-width: 80px;
  }

  .stat-value {
    font-size: 16px;
  }

  .stat-icon {
    font-size: 18px;
  }

  .new-project-btn {
    width: 100%;
    justify-content: center;
  }
}

/* Sortable Headers */
.sortable-headers {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sort-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.sort-header:hover {
  background: #f3f4f6;
  color: #1890ff;
}

.sort-header.active {
  background: #e6f7ff;
  color: #1890ff;
  font-weight: 600;
}

.sort-arrow {
  margin-left: 6px;
  font-size: 16px;
  color: #000000;
  font-weight: bold;
  line-height: 1;
}
</style>