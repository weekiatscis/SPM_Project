<template>
    <a-config-provider>
      <!-- Show auth pages (login/signup) without any layout -->
      <div v-if="isLoginPage">
        <router-view v-slot="{ Component }">
          <transition name="auth-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import CustomSidebar from './layout/CustomSidebar.vue'
import Topbar from './layout/Topbar.vue'
import NotificationPanel from './components/notifications/NotificationPanel.vue'
import { useNotificationPanel } from './composables/useNotificationPanel.js'

export default {
  name: 'App',
  components: {
    CustomSidebar,
    Topbar,
    NotificationPanel
  },
  setup() {
    const route = useRoute()
    const { isNotificationPanelOpen } = useNotificationPanel()

    const isSidebarCollapsed = ref(false)
    const isMobileSidebarOpen = ref(false)

    // Check if current route is an auth page (login/signup) that doesn't need main layout
    const isLoginPage = computed(() => route.name === 'Login' || route.name === 'Signup')

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
/* Auth Page 360° Flip Transitions */
.auth-fade-enter-active,
.auth-fade-leave-active {
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
  backface-visibility: hidden;
}

/* Login → Signup (flip forward) */
.auth-fade-leave-active {
  position: absolute;
  width: 100%;
  animation: flipOut 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.auth-fade-enter-active {
  animation: flipIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes flipOut {
  0% {
    transform: perspective(1200px) rotateY(0deg) scale(1);
    opacity: 1;
  }
  49% {
    opacity: 1;
  }
  50% {
    transform: perspective(1200px) rotateY(180deg) scale(0.9);
    opacity: 0;
  }
  100% {
    transform: perspective(1200px) rotateY(180deg) scale(0.9);
    opacity: 0;
  }
}

@keyframes flipIn {
  0% {
    transform: perspective(1200px) rotateY(-180deg) scale(0.9);
    opacity: 0;
  }
  50% {
    transform: perspective(1200px) rotateY(-180deg) scale(0.9);
    opacity: 0;
  }
  51% {
    opacity: 1;
  }
  100% {
    transform: perspective(1200px) rotateY(0deg) scale(1);
    opacity: 1;
  }
}

/* Ensure smooth rendering */
.auth-fade-enter-from,
.auth-fade-leave-to {
  opacity: 0;
}

.auth-fade-enter-to,
.auth-fade-leave-from {
  opacity: 1;
}
</style>
