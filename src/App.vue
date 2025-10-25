<template>
    <a-config-provider>
      <!-- Session Warning Modal - Global -->
      <SessionWarningModal />

      <!-- Show auth pages (login/signup) without any layout -->
      <div v-if="isLoginPage">
        <router-view />
      </div>

      <!-- Show main app layout for all other pages -->
      <a-layout v-else style="min-height: 100vh;">
        <!-- Custom Sidebar -->
        <CustomSidebar 
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
          <CustomSidebar 
            :is-collapsed="false"
          />
        </a-drawer>
        
        <!-- Main Layout -->
        <a-layout
          :style="{
            marginLeft: isSidebarCollapsed ? '64px' : '256px',
            marginRight: isNotificationPanelOpen ? '420px' : '0',
            transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1), margin-right 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
          }"
          class="hidden md:flex"
        >
          <!-- Header -->
          <a-layout-header :style="{
            padding: '0 24px',
            background: 'rgba(255, 255, 255, 0.7)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            borderBottom: '1px solid rgba(240, 240, 240, 0.3)',
            height: '64px',
            position: 'fixed',
            top: 0,
            left: isSidebarCollapsed ? '64px' : '256px',
            right: 0,
            zIndex: 999,
            transition: 'left 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
          }">
            <Topbar
              :is-sidebar-collapsed="isSidebarCollapsed"
              @toggle-sidebar="toggleSidebar"
              @toggle-mobile-sidebar="toggleMobileSidebar"
            />
          </a-layout-header>

          <!-- Content -->
          <a-layout-content class="gradient-content" :style="{
            margin: '64px 0 0 0',
            overflow: 'auto',
            borderRadius: '8px',
            minHeight: 'calc(100vh - 112px)',
            padding: '0px',
            transition: 'margin-right 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
          }">
            <!-- Breadcrumb -->
            <!-- <a-breadcrumb :style="{ margin: '16px 24px' }">
              <a-breadcrumb-item>Home</a-breadcrumb-item>
              <a-breadcrumb-item>{{ currentPageTitle }}</a-breadcrumb-item>
            </a-breadcrumb> -->

            <!-- Page Content -->
            <div :style="{
              background: 'transparent',
              padding: '8px',
              minHeight: '280px',
            }">
              <router-view />
            </div>
          </a-layout-content>

          <!-- Footer -->
          <a-layout-footer :style="{ textAlign: 'center', background: 'transparent', padding: '12px 24px' }">
          </a-layout-footer>
        </a-layout>

        <!-- Notification Panel (slides in from right) -->
        <NotificationPanel />

        <!-- Mobile Layout -->
        <a-layout class="md:hidden" style="min-height: 100vh;">
          <!-- Mobile Header -->
          <a-layout-header :style="{
            padding: '0 16px',
            background: 'rgba(255, 255, 255, 0.7)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            borderBottom: '1px solid rgba(240, 240, 240, 0.3)',
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
            background: 'transparent'
          }">
            <div :style="{
              background: 'transparent',
              padding: '24px',
              borderRadius: '8px',
              minHeight: 'calc(100vh - 96px)'
            }">
              <router-view />
            </div>
          </a-layout-content>
        </a-layout>

        <!-- Notification Panel for Mobile (full-width) -->
        <NotificationPanel />
      </a-layout>
    </a-config-provider>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import CustomSidebar from './layout/CustomSidebar.vue'
import Topbar from './layout/Topbar.vue'
import NotificationPanel from './components/notifications/NotificationPanel.vue'
import { useNotificationPanel } from './composables/useNotificationPanel.js'
import SessionWarningModal from './components/session/SessionWarningModal.vue'

export default {
  name: 'App',
  components: {
    CustomSidebar,
    Topbar,
    NotificationPanel,
    SessionWarningModal
  },
  setup() {
    const route = useRoute()
    const { isNotificationPanelOpen } = useNotificationPanel()

    const isSidebarCollapsed = ref(false)
    const isMobileSidebarOpen = ref(false)

    // Check if current route is an auth page (login/signup/forgot-password/reset-password) that doesn't need main layout
    const isLoginPage = computed(() => 
      route.name === 'Login' || 
      route.name === 'Signup' || 
      route.name === 'ForgotPassword' || 
      route.name === 'ResetPassword'
    )

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
      isLoginPage,
      currentPageTitle,
      isNotificationPanelOpen,
      toggleSidebar,
      toggleMobileSidebar,
      closeMobileSidebar,
    }
  }
}
</script>

<style>
/* No transitions for auth pages */
</style>
