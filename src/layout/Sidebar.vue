<template>
  <aside :class="[
    'bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen relative transition-colors duration-300',
    isCollapsed ? 'w-16' : 'w-64'
  ]"
  >
    <!-- Logo/Brand -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center">
        <div class="flex items-center justify-center">
          <img 
            src="/taskio-logo.svg" 
            alt="Taskio Logo" 
            class="h-6 w-auto object-contain"
          />
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="p-4 space-y-2 flex-1 overflow-y-auto pb-20">
      <!-- Home button -->
      <button
        :class="[
          'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
          'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700',
          isCollapsed ? 'justify-center' : ''
        ]"
        @click="handleNavigation('/home')"
      >
        <HomeIcon class="w-5 h-5" />
        <span v-if="!isCollapsed" class="ml-3">Home</span>
      </button>

      <!-- Projects collapsible section -->
      <div class="space-y-1">
        <!-- Projects main button -->
        <button
          :class="[
            'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
            'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700',
            isCollapsed ? 'justify-center' : 'justify-between'
          ]"
          @click="handleNavigation('/projects')"
        >
          <div class="flex items-center">
            <ProjectIcon class="w-5 h-5" />
            <span v-if="!isCollapsed" class="ml-3">Projects</span>
          </div>
          <svg
            v-if="!isCollapsed"
            :class="[
              'w-4 h-4 transition-transform duration-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded p-0.5',
              isProjectsExpanded ? 'rotate-180' : ''
            ]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            @click.stop="toggleProjectsCollapse()"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Projects dropdown list -->
        <div
          v-if="!isCollapsed"
          :class="[
            'overflow-hidden transition-all duration-200 ease-in-out',
            isProjectsExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
          ]"
        >
          <div class="pl-8 space-y-1">
            <!-- Loading state -->
            <div v-if="projectsLoading" class="px-2 py-1.5">
              <span class="text-xs text-gray-500 dark:text-gray-400">Loading...</span>
            </div>

            <!-- Individual projects -->
            <button
              v-for="project in userProjects"
              :key="project.project_id"
              :class="[
                'w-full flex items-center px-2 py-1.5 text-sm rounded-md transition-colors duration-200',
                'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 text-left'
              ]"
              @click="handleNavigation(`/projects/${project.project_id}`)"
              :title="project.project_name"
            >
              <span class="text-xs truncate">{{ project.project_name }}</span>
            </button>

            <!-- No projects message -->
            <div v-if="!projectsLoading && userProjects.length === 0" class="px-2 py-1.5">
              <span class="text-xs text-gray-500 dark:text-gray-400">No projects yet</span>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- User section -->
    <div class="px-4 pt-4 pb-0 absolute bottom-0 left-0 right-0 bg-white dark:bg-gray-800 group overflow-hidden transition-colors duration-300">
      <div class="overflow-hidden transition-all duration-200 ease-out max-h-0 opacity-0 transform translate-y-2 group-hover:max-h-24 group-hover:opacity-100 group-hover:translate-y-0 mb-6">
        <button
          @click="logout"
          :class="[
            'w-full flex items-center px-2 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200',
            isCollapsed ? 'justify-center' : ''
          ]"
        >
          <LogoutIcon size="sm" />
          <span v-if="!isCollapsed" class="ml-2">Logout</span>
        </button>
      </div>

      <div class="flex items-center cursor-default">
        <div class="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
          <UserIcon size="sm" color="gray" />
        </div>
        <div v-if="!isCollapsed" class="ml-3">
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ user?.name || 'Loading...' }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 capitalize">{{ user?.role || 'Role' }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { HomeIcon, TaskIcon, DashboardIcon, ProjectIcon, SettingsIcon, UserIcon, LogoutIcon } from '../components/icons/index.js'
import { useUser } from '../composables/useUser.js'

export default {
  name: 'Sidebar',
  props: {
    isCollapsed: {
      type: Boolean,
      default: false
    }
  },
  components: {
    HomeIcon,
    TaskIcon,
    DashboardIcon,
    ProjectIcon,
    SettingsIcon,
    UserIcon,
    LogoutIcon
  },
  setup() {
    const router = useRouter()

    // Use the user composable to get user data
    const { user, loading, error } = useUser()

    // Projects collapsible state
    const isProjectsExpanded = ref(false)
    const userProjects = ref([])
    const projectsLoading = ref(false)

    const handleNavigation = (path) => {
      router.push(path)
    }

    const toggleProjectsCollapse = async () => {
      isProjectsExpanded.value = !isProjectsExpanded.value

      // Load projects when expanding for the first time
      if (isProjectsExpanded.value && userProjects.value.length === 0) {
        await loadUserProjects()
      }
    }

    const loadUserProjects = async () => {
      if (!user.value?.user_id) return

      projectsLoading.value = true
      try {
        const baseUrl = 'http://localhost:8083'
        const response = await fetch(`${baseUrl}/projects?created_by=${encodeURIComponent(user.value.user_id)}`)

        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const payload = await response.json()
        userProjects.value = Array.isArray(payload?.projects) ? payload.projects : []
      } catch (error) {
        console.error('Failed to load user projects:', error)
        userProjects.value = []
      } finally {
        projectsLoading.value = false
      }
    }

    const logout = () => {
      localStorage.removeItem('user')
      // Router navigation will be implemented later
      console.log('User logged out')
    }

    // Load projects when user becomes available
    watch(() => user.value?.user_id, (newUserId) => {
      if (newUserId && userProjects.value.length === 0 && !projectsLoading.value) {
        loadUserProjects()
      }
    }, { immediate: true })

    return {
      user,
      loading,
      error,
      isProjectsExpanded,
      userProjects,
      projectsLoading,
      handleNavigation,
      toggleProjectsCollapse,
      logout
    }
  }
}
</script>
