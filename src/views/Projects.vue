<template>
  <div style="max-width: 1600px; margin: 0 auto; padding: 0px;">
    <!-- Welcome Header -->
    <a-card :bordered="false" :style="headerStyle">
      <a-row :gutter="24" align="middle">
        <a-col :span="16">
          <a-typography-title :level="2" :style="titleStyle">
            Projects Overview 📁
          </a-typography-title>
          <a-typography-paragraph :style="subtitleStyle">
            Manage and organize your projects efficiently
          </a-typography-paragraph>
        </a-col>
        <a-col :span="8" style="text-align: right;">
          <a-space direction="vertical" align="end">
            <a-statistic
              title="Active Projects"
              :value="`${stats.active}/${stats.total}`"
              :value-style="statisticValueStyle"
              :title-style="statisticTitleStyle"
            />
            <a-button type="primary" size="large" @click="showCreateModal = true">
              <template #icon>
                <PlusOutlined />
              </template>
              New Project
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- Main Content Row -->
    <a-row :gutter="24" style="margin-bottom: 24px;">
      <!-- Projects Section -->
      <a-col :span="24">
        <ProjectList
          ref="projectListRef"
          @create-project="showCreateModal = true"
        />
      </a-col>
    </a-row>

    <!-- Create Project Modal -->
    <ProjectFormModal
      :isOpen="showCreateModal"
      @close="showCreateModal = false"
      @save="handleProjectSaved"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import ProjectList from '../components/projects/ProjectList.vue'
import ProjectFormModal from '../components/projects/ProjectFormModal.vue'

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

    // Light theme header style
    const headerStyle = computed(() => {
      const lightGradient = 'linear-gradient(135deg, #f3e8ff 0%, #e0e7ff 100%)'

      return {
        marginBottom: '24px',
        background: lightGradient
      }
    })

    // Light theme text styles
    const titleStyle = computed(() => ({
      color: '#7c3aed',
      marginBottom: '8px'
    }))

    const subtitleStyle = computed(() => ({
      color: 'rgba(124,58,237,0.8)',
      fontSize: '16px',
      marginBottom: '0'
    }))

    const statisticValueStyle = computed(() => ({
      color: '#7c3aed',
      fontSize: '24px'
    }))

    const statisticTitleStyle = computed(() => ({
      color: 'rgba(124,58,237,0.7)'
    }))

    // Handle project saved from modal
    const handleProjectSaved = async (projectData) => {
      console.log('Projects.vue received new project:', projectData)

      // Add to local stats array
      projects.value.unshift(projectData)

      // Also notify ProjectList component to add the project
      if (projectListRef.value && projectListRef.value.addNewProject) {
        await projectListRef.value.addNewProject(projectData)
      }

      showCreateModal.value = false
    }

    // Load projects on mount for stats
    onMounted(async () => {
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
        console.error('Failed to load projects for stats:', error)
        projects.value = []
      }
    })

    return {
      currentUser,
      stats,
      showCreateModal,
      handleProjectSaved,
      projectListRef,
      headerStyle,
      titleStyle,
      subtitleStyle,
      statisticValueStyle,
      statisticTitleStyle
    }
  }
}
</script>