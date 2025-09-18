<template>
  <ThemeProvider>
    <div id="app" class="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      <div class="flex h-screen">
        <!-- Sidebar -->
        <Sidebar 
          :is-collapsed="isSidebarCollapsed" 
          @toggle="toggleSidebar"
          class="hidden md:block"
        />
        
        <!-- Mobile sidebar overlay -->
        <div 
          v-if="isMobileSidebarOpen" 
          class="fixed inset-0 z-50 md:hidden"
          @click="closeMobileSidebar"
        >
          <div class="absolute inset-0 bg-gray-600 opacity-75"></div>
          <Sidebar 
            :is-collapsed="false" 
            @toggle="closeMobileSidebar"
            class="relative z-10"
          />
        </div>
        
        <!-- Main content area -->
        <div class="flex-1 flex flex-col overflow-hidden">
          <!-- Top bar -->
          <Topbar @toggle-mobile-sidebar="toggleMobileSidebar" />
          
          <!-- Page content -->
          <main class="flex-1 overflow-auto p-6">
            <router-view />
          </main>
        </div>
      </div>
    </div>
  </ThemeProvider>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './layout/Sidebar.vue'
import Topbar from './layout/Topbar.vue'
import ThemeProvider from './components/ThemeProvider.vue'
import { useTheme } from './composables/useTheme'

export default {
  name: 'App',
  components: {
    Sidebar,
    Topbar,
    ThemeProvider
  },
  setup() {
    // Initialize theme
    const { initializeTheme } = useTheme()
    
    // Initialize theme on app mount
    onMounted(() => {
      initializeTheme()
    })
    
    const isSidebarCollapsed = ref(false)
    const isMobileSidebarOpen = ref(false)

    const toggleSidebar = () => {
      isSidebarCollapsed.value = !isSidebarCollapsed.value
    }

    const toggleMobileSidebar = () => {
      isMobileSidebarOpen.value = !isMobileSidebarOpen.value
    }

    const closeMobileSidebar = () => {
      isMobileSidebarOpen.value = false
    }

    // Handle window resize
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        isMobileSidebarOpen.value = false
      }
    }

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })

    return {
      isSidebarCollapsed,
      isMobileSidebarOpen,
      toggleSidebar,
      toggleMobileSidebar,
      closeMobileSidebar
    }
  }
}
</script>
