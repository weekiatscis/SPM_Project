<template>
  <!-- Project Form Modal -->
  <ProjectFormModal
    :isOpen="showProjectModal"
    @close="showProjectModal = false"
    @save="handleProjectSaved"
  />


  <div>
    <!-- Section Toggle Tabs -->
    <a-tabs v-model:activeKey="activeTab" style="margin-bottom: 16px;">
      <a-tab-pane key="projects" tab="All Projects" />
      <a-tab-pane key="assign" tab="Assign Task" />
    </a-tabs>

    <!-- Projects Section -->
    <a-card
      v-if="activeTab === 'projects'"
      style="min-height: 500px;"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 12px;">
          <span>All Projects</span>
          <a-space size="small">
            <a-button
              size="small"
              :type="sortBy.startsWith('created_at') ? 'primary' : 'default'"
              @click="toggleDateSort"
            >
              Date {{ sortBy === 'created_at-asc' ? '↑' : sortBy === 'created_at-desc' ? '↓' : '↑' }}
            </a-button>
            <a-button
              size="small"
              :type="sortBy.startsWith('status') ? 'primary' : 'default'"
              @click="toggleStatusSort"
            >
              Status {{ sortBy === 'status-asc' ? '↑' : sortBy === 'status-desc' ? '↓' : '↑' }}
            </a-button>
          </a-space>
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
            <div style="display: flex; align-items: center; justify-between; margin-bottom: 16px;">
              <h4 style="margin: 0;">Available Tasks</h4>
              <a-space size="small">
                <a-button
                  size="small"
                  :type="taskSortBy.startsWith('dueDate') ? 'primary' : 'default'"
                  @click="toggleTaskDueDateSort"
                >
                  Due Date {{ taskSortBy === 'dueDate-asc' ? '↑' : taskSortBy === 'dueDate-desc' ? '↓' : '↑' }}
                </a-button>
                <a-button
                  size="small"
                  :type="taskSortBy.startsWith('status') ? 'primary' : 'default'"
                  @click="toggleTaskStatusSort"
                >
                  Status {{ taskSortBy === 'status-asc' ? '↑' : taskSortBy === 'status-desc' ? '↓' : '↑' }}
                </a-button>
              </a-space>
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
                  style="cursor: pointer; padding: 8px; border-radius: 4px; margin-bottom: 4px;"
                  :style="isTaskSelected(item) ? { background: '#e6f7ff', border: '1px solid #1890ff' } : {}"
                  @click="selectTaskForAssign(item)"
                >
                  <div style="width: 100%;">
                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 4px;">
                      <strong>{{ item.title }}</strong>
                      <a-tag :color="getTaskStatusColor(item.status)" size="small">
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
                          <div>
                            <strong style="font-size: 14px;">{{ item.project_name }}</strong>
                            <a-tag :color="getProjectStatusColor(item.status)" size="small" style="margin-left: 8px;">
                              {{ item.status }}
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
import { PlusOutlined } from '@ant-design/icons-vue'
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
  emits: ['create-project'],
  setup(props, { emit }) {
    const router = useRouter()
    const projects = ref([])
    const isLoading = ref(false)
    const sortBy = ref('created_at-desc')
    const authStore = useAuthStore()

    // Tab state for switching between sections
    const activeTab = ref('projects')

    // Modal state for creating project
    const showProjectModal = ref(false)

    // Task assignment state
    const tasks = ref([])
    const isLoadingTasks = ref(false)
    const taskSortBy = ref('dueDate-asc')
    const selectedTasksForAssign = ref([])

    // Project assignment state
    const projectSearchQuery = ref('')
    const selectedProjectForAssign = ref(null)
    const isAssigning = ref(false)

    // Handle project saved from ProjectFormModal
    const handleProjectSaved = (projectData) => {
      // Transform the API response to match frontend format
      const mappedProject = {
        project_id: projectData.project_id || projectData.id,
        project_name: projectData.project_name,
        project_description: projectData.project_description,
        created_at: projectData.created_at,
        created_by: projectData.created_by,
        due_date: projectData.due_date,
        status: 'Active' // Default status
      }

      // Add the new project to the projects list
      projects.value.unshift(mappedProject)

      // Show success notification
      notification.success({
        message: 'Project created successfully',
        description: `"${mappedProject.project_name}" has been added to your projects.`,
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


    // All projects computed property with sorting
    const allProjects = computed(() => {
      const sortedProjects = [...projects.value]

      if (sortBy.value === 'created_at-asc') {
        return sortedProjects.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      } else if (sortBy.value === 'created_at-desc') {
        return sortedProjects.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      } else if (sortBy.value === 'status-asc') {
        return sortedProjects.sort((a, b) => (a.status || 'Active').localeCompare(b.status || 'Active'))
      } else if (sortBy.value === 'status-desc') {
        return sortedProjects.sort((a, b) => (b.status || 'Active').localeCompare(a.status || 'Active'))
      }

      return sortedProjects
    })

    // Function to toggle date sort between ascending and descending
    const toggleDateSort = () => {
      if (sortBy.value === 'created_at-asc') {
        sortBy.value = 'created_at-desc'
      } else {
        sortBy.value = 'created_at-asc'
      }
    }

    // Function to toggle status sort between ascending and descending
    const toggleStatusSort = () => {
      if (sortBy.value === 'status-asc') {
        sortBy.value = 'status-desc'
      } else {
        sortBy.value = 'status-asc'
      }
    }

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

    // All available tasks computed property with sorting - only unassigned tasks
    const allAvailableTasks = computed(() => {
      // Filter tasks that are not assigned to any project (project_id is null/undefined)
      const unassignedTasks = tasks.value.filter(task =>
        !task.project_id || task.project_id === null
      )

      let sortedTasks = [...unassignedTasks]

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
      } else if (taskSortBy.value === 'status-asc') {
        return sortedTasks.sort((a, b) => a.status.localeCompare(b.status))
      } else if (taskSortBy.value === 'status-desc') {
        return sortedTasks.sort((a, b) => b.status.localeCompare(a.status))
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

    const toggleTaskStatusSort = () => {
      if (taskSortBy.value === 'status-asc') {
        taskSortBy.value = 'status-desc'
      } else {
        taskSortBy.value = 'status-asc'
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
        'Completed': 'green',
        'In Progress': 'blue',
        'Pending': 'orange',
        'On Hold': 'red',
        'Unassigned': 'default'
      }
      return colors[status] || 'default'
    }

    // Project assignment functions
    const filteredProjectsForAssign = computed(() => {
      if (!projectSearchQuery.value) {
        return projects.value
      }

      const query = projectSearchQuery.value.toLowerCase()
      return projects.value.filter(project =>
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
          status: 'Active' // Default status since not in DB yet
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
      isLoading,
      activeTab,
      showProjectModal,
      sortBy,
      toggleDateSort,
      toggleStatusSort,
      handleProjectSaved,
      handleProjectClick,
      // Task assignment related
      allAvailableTasks,
      isLoadingTasks,
      taskSortBy,
      selectedTasksForAssign,
      toggleTaskDueDateSort,
      toggleTaskStatusSort,
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
      assignTaskToProject
    }
  }
}
</script>

<style scoped>
/* Custom card grid spacing */
:deep(.ant-col) {
  margin-bottom: 16px;
}

/* Enhanced card hover effects */
:deep(.ant-card) {
  transition: all 0.2s ease;
  height: 100%;
}

:deep(.ant-card:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
</style>