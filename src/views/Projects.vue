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
        <ProjectList @create-project="showCreateModal = true" />
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
import { useTheme } from '../composables/useTheme.js'
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
    const { isDarkMode } = useTheme()

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

    // Theme-aware header style
    const headerStyle = computed(() => {
      const lightGradient = 'linear-gradient(135deg, #f3e8ff 0%, #e0e7ff 100%)'
      const darkGradient = 'linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)'

      return {
        marginBottom: '24px',
        background: isDarkMode.value ? darkGradient : lightGradient
      }
    })

    // Theme-aware text styles
    const titleStyle = computed(() => ({
      color: isDarkMode.value ? 'white' : '#7c3aed',
      marginBottom: '8px'
    }))

    const subtitleStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.9)' : 'rgba(124,58,237,0.8)',
      fontSize: '16px',
      marginBottom: '0'
    }))

    const statisticValueStyle = computed(() => ({
      color: isDarkMode.value ? 'white' : '#7c3aed',
      fontSize: '24px'
    }))

    const statisticTitleStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.8)' : 'rgba(124,58,237,0.7)'
    }))

    // Handle project saved from modal
    const handleProjectSaved = (projectData) => {
      // Add the new project to the projects list
      projects.value.unshift(projectData)
      showCreateModal.value = false
    }

    // Load projects on mount for stats
    onMounted(async () => {
      try {
        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const ownerId = import.meta.env.VITE_TASK_OWNER_ID || ''
        const url = ownerId
          ? `${baseUrl}/projects?created_by=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/projects`

        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const payload = await response.json()
        const apiProjects = Array.isArray(payload?.projects) ? payload.projects : []

        projects.value = apiProjects.map(p => ({
          project_id: p.project_id,
          project_name: p.project_name,
          project_description: p.project_description,
          created_at: p.created_at,
          created_by: p.created_by,
          status: 'Active' // Default status since not in DB yet
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
      headerStyle,
      titleStyle,
      subtitleStyle,
      statisticValueStyle,
      statisticTitleStyle
    }
  }
}
</script>