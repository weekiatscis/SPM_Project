<template>
  <ThemeProvider>
    <a-config-provider>
      <a-layout style="min-height: 100vh;">
        <!-- Sidebar -->
        <Sidebar 
          v-model:is-collapsed="isSidebarCollapsed"
          class="hidden md:block"
        />
        
        <!-- Mobile sidebar drawer -->
        <a-drawer
          v-model:open="isMobileSidebarOpen"
          placement="left"
          :closable="false"
          :width="256"
          :body-style="{ padding: 0 }"
          class="md:hidden"
        >
          <Sidebar 
            :is-collapsed="false"
            @menu-click="closeMobileSidebar"
          />
        </a-drawer>
        
        <!-- Main Layout -->
        <a-layout :style="{ marginLeft: isSidebarCollapsed ? '64px' : '256px', transition: 'margin-left 0.2s' }" class="hidden md:flex">
          <!-- Header -->
          <a-layout-header :style="{ 
            padding: '0 24px', 
            background: '#fff', 
            display: 'flex', 
            alignItems: 'center',
            borderBottom: '1px solid #f0f0f0',
            height: '64px'
          }">
            <Topbar 
              :is-sidebar-collapsed="isSidebarCollapsed"
              @toggle-sidebar="toggleSidebar"
              @toggle-mobile-sidebar="toggleMobileSidebar" 
            />
          </a-layout-header>
          
          <!-- Content -->
          <a-layout-content :style="{ 
            margin: '24px 24px 0', 
            overflow: 'auto',
            background: '#fff',
            borderRadius: '8px',
            minHeight: 'calc(100vh - 112px)'
          }">
            <!-- Breadcrumb -->
            <a-breadcrumb :style="{ margin: '16px 24px' }">
              <a-breadcrumb-item>Home</a-breadcrumb-item>
              <a-breadcrumb-item>{{ currentPageTitle }}</a-breadcrumb-item>
            </a-breadcrumb>
            
            <!-- Page Content -->
            <div :style="{ 
              background: '#fff', 
              padding: '24px', 
              minHeight: '280px'
            }">
              <router-view />
            </div>
          </a-layout-content>
          
          <!-- Footer -->
          <a-layout-footer :style="{ textAlign: 'center', background: '#fff', padding: '12px 24px' }">
            Taskio ©{{ new Date().getFullYear() }} - Smart Task Management
          </a-layout-footer>
        </a-layout>

        <!-- Mobile Layout -->
        <a-layout class="md:hidden" style="min-height: 100vh;">
          <!-- Mobile Header -->
          <a-layout-header :style="{ 
            padding: '0 16px', 
            background: '#fff', 
            display: 'flex', 
            alignItems: 'center',
            borderBottom: '1px solid #f0f0f0',
            height: '64px'
          }">
            <Topbar 
              :is-sidebar-collapsed="false"
              @toggle-sidebar="toggleSidebar"
              @toggle-mobile-sidebar="toggleMobileSidebar" 
            />
          </a-layout-header>
          
          <!-- Mobile Content -->
          <a-layout-content :style="{ 
            padding: '16px',
            overflow: 'auto',
            background: '#f5f5f5'
          }">
            <div :style="{ 
              background: '#fff', 
              padding: '24px', 
              borderRadius: '8px',
              minHeight: 'calc(100vh - 96px)'
            }">
              <router-view />
            </div>
          </a-layout-content>
        </a-layout>
      </a-layout>
    </a-config-provider>
  </ThemeProvider>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
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
    const route = useRoute()
    
    // Initialize theme on app mount
    onMounted(() => {
      initializeTheme()
    })
    
    const isSidebarCollapsed = ref(false)
    const isMobileSidebarOpen = ref(false)

    // Generate page title from route
    const currentPageTitle = computed(() => {
      const path = route.path
      if (path === '/' || path === '/home') return 'Dashboard'
      if (path === '/projects') return 'Projects'
      if (path.startsWith('/projects/')) return 'Project Details'
      
      // Capitalize first letter and remove leading slash
      return path.slice(1).charAt(0).toUpperCase() + path.slice(2)
    })

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
      currentPageTitle,
      toggleSidebar,
      toggleMobileSidebar,
      closeMobileSidebar
    }
  }
}
</script>
