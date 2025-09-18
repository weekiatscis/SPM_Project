<template>
  <aside :class="[
    'bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen relative transition-colors duration-300',
    isCollapsed ? 'w-16' : 'w-64'
  ]"
  >
    <!-- Logo/Brand -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center">
        <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        <h1 v-if="!isCollapsed" class="ml-3 text-lg font-semibold text-gray-900 dark:text-gray-100">
          TaskManager
        </h1>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="p-4 space-y-2 flex-1 overflow-y-auto pb-20">
      <button
        v-for="item in navigationItems"
        :key="item.path"
        :class="[
          'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
          'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700',
          isCollapsed ? 'justify-center' : ''
        ]"
        @click="handleNavigation(item.path)"
      >
        <component :is="item.icon" class="w-5 h-5" />
        <span v-if="!isCollapsed" class="ml-3">{{ item.name }}</span>
      </button>
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
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ currentUser?.name }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 capitalize">{{ currentUser?.role }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { HomeIcon, TaskIcon, DashboardIcon, ProjectIcon, SettingsIcon, UserIcon, LogoutIcon } from '../components/icons/index.js'

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

    const currentUser = computed(() => {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user) : null
    })

    const navigationItems = computed(() => {
      return [
        { name: 'Home', path: '/home', icon: 'HomeIcon' }
      ]
    })

    const handleNavigation = (path) => {
      router.push(path)
    }

    const logout = () => {
      localStorage.removeItem('user')
      // Router navigation will be implemented later
      console.log('User logged out')
    }

    return {
      currentUser,
      navigationItems,
      handleNavigation,
      logout
    }
  }
}
</script>
