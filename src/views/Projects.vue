<template>
  <div class="projects-page">
    <!-- Project Overview Header -->
    <div class="project-overview-wrapper">
      <div class="project-overview-header">
        <h1 class="page-title">Projects Overview</h1>
      </div>
    </div>

    <!-- Main Content Row -->
    <div class="projects-content">
      <ProjectList
        ref="projectListRef"
        :stats="stats"
        @create-project="showCreateModal = true"
        @open-modal="showCreateModal = true"
      />
    </div>

    <!-- Create Project Modal -->
    <ProjectFormModal
      :isOpen="showCreateModal"
      @close="showCreateModal = false"
      @save="handleProjectSaved"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import ProjectList from '../components/projects/ProjectList.vue'
import ProjectFormModal from '../components/projects/ProjectFormModal.vue'
import { useProjectEvents } from '../composables/useProjectEvents'

export default {
  name: 'Projects',
  components: {
    PlusOutlined,
    ProjectList,
    ProjectFormModal
  },  
  setup() {
    const projects = ref([])
    const showCreateModal = ref(false)
    const authStore = useAuthStore()
    const projectListRef = ref(null)
    const { emitProjectCreated, onProjectUpdated, onProjectDeleted } = useProjectEvents()

    const currentUser = computed(() => {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user) : null
    })

    const stats = computed(() => {
      const total = projects.value.length
      const active = projects.value.filter(project => project.status === 'Active').length
      const completed = projects.value.filter(project => project.status === 'Completed').length
      return { total, active, completed }
    })

    // Handle project saved from modal
    const handleProjectSaved = async (projectData) => {
      console.log('Projects.vue received new project:', projectData)

      // Add to local stats array with status
      projects.value.unshift({
        ...projectData,
        status: projectData.status || 'Active' // Use status from projectData, default to Active
      })

      // Also notify ProjectList component to add the project
      if (projectListRef.value && projectListRef.value.addNewProject) {
        await projectListRef.value.addNewProject(projectData)
      }

      // Emit event to notify other components (like Sidebar) to refresh
      emitProjectCreated(projectData)

      showCreateModal.value = false
    }

    // Function to load projects
    const loadProjects = async () => {
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
        console.error('Failed to load projects for stats:', error)
        projects.value = []
      }
    }

    // Load projects on mount for stats
    onMounted(async () => {
      await loadProjects()
    })

    // Listen for project updates and reload
    const cleanupUpdated = onProjectUpdated(() => {
      loadProjects()
    })

    const cleanupDeleted = onProjectDeleted(() => {
      loadProjects()
    })

    // Cleanup listeners on unmount
    onUnmounted(() => {
      cleanupUpdated()
      cleanupDeleted()
    })

    return {
      currentUser,
      stats,
      showCreateModal,
      handleProjectSaved,
      projectListRef
    }
  }
}
</script>

<style scoped>
.projects-page {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

/* Project Overview Wrapper - Simple wrapper */
.project-overview-wrapper {
  margin-bottom: 12px;
}

/* Project Overview Header - Text on the left */
.project-overview-header {
  margin-bottom: 12px;
  padding: 24px 32px 24px 24px;
}

.page-title {
  margin: 0;
  font-size: 36px;
  font-weight: 800;
  color: #000000;
  text-align: left;
}

.projects-content {
  /* ProjectList handles its own styling */
}

/* Responsive Design */
@media (max-width: 768px) {
  .projects-page {
    padding: 20px 16px;
  }

  .project-overview-header {
    padding: 16px 20px 12px 16px;
  }

  .page-title {
    font-size: 24px !important;
  }
}

@media (max-width: 480px) {
  .project-overview-header {
    padding: 12px 16px 8px 12px;
  }

  .page-title {
    font-size: 20px !important;
  }
}
</style>