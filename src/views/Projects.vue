<template>
  <div class="projects-page">
    <!-- Welcome Header -->
    <div class="project-overview-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">Projects Overview</h1>
          <p class="page-subtitle">Manage and organize your projects efficiently</p>
        </div>
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
  padding: 32px 24px;
}

/* Project Overview Header */
.project-overview-header {
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, rgba(215, 143, 238, 0.12) 0%, rgba(167, 139, 250, 0.08) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(215, 143, 238, 0.2);
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(215, 143, 238, 0.15);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 32px;
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #D78FEE, #A78BFA);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.page-subtitle {
  margin: 0;
  font-size: 16px;
  color: #6B7280;
  font-weight: 400;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 16px;
}

.stats-container {
  display: flex;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(215, 143, 238, 0.2);
  border-radius: 14px;
  min-width: 140px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(215, 143, 238, 0.1);
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(215, 143, 238, 0.2);
}

.stat-total {
  border-color: rgba(107, 114, 128, 0.2);
}

.stat-active {
  border-color: rgba(215, 143, 238, 0.4);
  background: linear-gradient(135deg, rgba(215, 143, 238, 0.08), rgba(167, 139, 250, 0.04));
}

.stat-completed {
  border-color: rgba(16, 185, 129, 0.3);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(5, 150, 105, 0.02));
}

.stat-icon {
  font-size: 28px;
  line-height: 1;
  filter: grayscale(0.2);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  color: #1F2937;
}

.stat-active .stat-value {
  background: linear-gradient(135deg, #D78FEE, #A78BFA);
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
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.new-project-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border: none;
  background: linear-gradient(135deg, #D78FEE, #A78BFA);
  color: white;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(215, 143, 238, 0.4);
}

.new-project-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(215, 143, 238, 0.5);
}

.new-project-btn:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 18px;
  font-weight: bold;
}

.projects-content {
  /* ProjectList handles its own styling */
}

/* Responsive Design */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .header-right {
    align-items: stretch;
  }

  .stats-container {
    justify-content: space-between;
  }

  .new-project-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .projects-page {
    padding: 20px 16px;
  }

  .project-overview-header {
    padding: 24px 20px;
  }

  .page-title {
    font-size: 24px;
  }

  .page-subtitle {
    font-size: 14px;
  }

  .stats-container {
    flex-direction: column;
    gap: 12px;
  }

  .stat-card {
    width: 100%;
  }
}
</style>