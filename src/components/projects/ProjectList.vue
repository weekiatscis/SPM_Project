<template>
  <!-- Project Form Modal -->
  <ProjectFormModal
    :isOpen="showProjectModal"
    @close="showProjectModal = false"
    @save="handleProjectSaved"
  />

  <!-- Project Detail Modal -->
  <ProjectDetailModal
    v-if="selectedProject"
    :project="selectedProject"
    :isOpen="showDetailModal"
    @close="closeDetailModal"
    @save="handleProjectUpdated"
    @delete="handleProjectDeleted"
  />

  <div>
    <!-- Projects Section -->
    <a-card
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
  </div>
</template>

<script>
import { ref, computed, onMounted, h } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { notification } from 'ant-design-vue'
import { useTheme } from '../../composables/useTheme.js'
import ProjectFormModal from './ProjectFormModal.vue'
import ProjectDetailModal from './ProjectDetailModal.vue'
import ProjectCard from './ProjectCard.vue'

export default {
  name: 'ProjectList',
  components: {
    PlusOutlined,
    ProjectFormModal,
    ProjectDetailModal,
    ProjectCard
  },
  emits: ['create-project'],
  setup(props, { emit }) {
    const projects = ref([])
    const isLoading = ref(false)
    const selectedProject = ref(null)
    const showDetailModal = ref(false)
    const isLoadingProjectDetails = ref(false)
    const sortBy = ref('created_at-desc')
    const { isDarkMode } = useTheme()

    // Modal state for creating project
    const showProjectModal = ref(false)

    // Handle project saved from ProjectFormModal
    const handleProjectSaved = (projectData) => {
      // Transform the API response to match frontend format
      const mappedProject = {
        project_id: projectData.project_id || projectData.id,
        project_name: projectData.project_name,
        project_description: projectData.project_description,
        created_at: projectData.created_at,
        created_by: projectData.created_by,
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

    // Handle project click
    const handleProjectClick = async (project) => {
      selectedProject.value = project
      showDetailModal.value = true
    }

    // Handle modal close
    const closeDetailModal = () => {
      showDetailModal.value = false
      selectedProject.value = null
    }

    // Handle project updated from modal
    const handleProjectUpdated = (updatedProject) => {
      const index = projects.value.findIndex(p => p.project_id === updatedProject.project_id)
      if (index !== -1) {
        projects.value[index] = {
          ...projects.value[index],
          ...updatedProject
        }
        notification.success({
          message: 'Project updated successfully',
          description: `"${updatedProject.project_name}" has been updated.`,
          placement: 'topRight',
          duration: 3
        })
      }
      closeDetailModal()
    }

    // Handle project deleted from modal
    const handleProjectDeleted = (deletedProject) => {
      projects.value = projects.value.filter(p => p.project_id !== deletedProject.project_id)
      notification.success({
        message: 'Project deleted successfully',
        description: `"${deletedProject.project_name}" has been deleted.`,
        placement: 'topRight',
        duration: 3
      })
      closeDetailModal()
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

    onMounted(async () => {
      isLoading.value = true
      try {
        const baseUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8083'
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
    })

    return {
      h,
      allProjects,
      isLoading,
      selectedProject,
      showDetailModal,
      isLoadingProjectDetails,
      showProjectModal,
      sortBy,
      toggleDateSort,
      toggleStatusSort,
      handleProjectSaved,
      handleProjectClick,
      closeDetailModal,
      handleProjectUpdated,
      handleProjectDeleted
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