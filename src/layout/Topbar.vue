<template>
  <header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 transition-colors duration-300">
    <div class="flex items-center justify-between">
      <!-- Left side: Mobile menu button + Search -->
      <div class="flex items-center space-x-4">
        <!-- Mobile menu button -->
        <button
          @click="$emit('toggle-mobile-sidebar')"
          class="md:hidden p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
        >
          <MenuIcon size="lg" />
        </button>

        <!-- Search bar -->
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <SearchIcon size="sm" color="gray" />
          </div>
          <input
            type="text"
            placeholder="Search tasks, projects..."
            class="pl-10 pr-4 py-2 w-64 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200"
            v-model="searchQuery"
            @input="handleSearch"
          />
        </div>
      </div>

      <!-- Right side: Theme Toggle + Notifications + Profile -->
      <div class="flex items-center space-x-4">
        <!-- Notifications -->
        <button class="relative p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200">
          <BellIcon size="lg" />
          <!-- Notification badge -->
          <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        <!-- Profile dropdown -->
        <div class="relative" ref="profileDropdown">
          <button
            @click="toggleProfileMenu"
            class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
          >
            <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <span class="text-white text-sm font-medium">
                {{ currentUser?.name?.charAt(0).toUpperCase() }}
              </span>
            </div>
            <span class="hidden sm:block text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ currentUser?.name }}
            </span>
            <ChevronDownIcon size="sm" color="gray" />
          </button>

          <!-- Dropdown menu -->
          <div
            v-if="isProfileMenuOpen"
            class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50 transition-colors duration-200"
          >
            <a href="#" class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200">
              Profile Settings
            </a>
            <a href="#" class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200">
              Preferences
            </a>
            <hr class="my-1 border-gray-200 dark:border-gray-700">
            <button
              @click="logout"
              class="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { MenuIcon, SearchIcon, BellIcon, ChevronDownIcon } from '../components/icons/index.js'

export default {
  name: 'Topbar',
  components: {
    MenuIcon,
    SearchIcon,
    BellIcon,
    ChevronDownIcon,
  },
  emits: ['toggle-mobile-sidebar'],
  setup() {
    const searchQuery = ref('')
    const isProfileMenuOpen = ref(false)
    const profileDropdown = ref(null)

    const currentUser = computed(() => {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user) : null
    })

    const toggleProfileMenu = () => {
      isProfileMenuOpen.value = !isProfileMenuOpen.value
    }

    const handleSearch = () => {
      // Implement search functionality
      console.log('Searching for:', searchQuery.value)
    }

    const logout = () => {
      localStorage.removeItem('user')
      // Router navigation will be implemented later
      console.log('User logged out')
    }

    // Close profile menu when clicking outside
    const handleClickOutside = (event) => {
      if (profileDropdown.value && !profileDropdown.value.contains(event.target)) {
        isProfileMenuOpen.value = false
      }
    }

    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })

    return {
      searchQuery,
      isProfileMenuOpen,
      profileDropdown,
      currentUser,
      toggleProfileMenu,
      handleSearch,
      logout
    }
  }
}
</script>
