<template>
  <a-layout-sider
    v-model:collapsed="collapsed"
    :trigger="null"
    collapsible
    :style="{ height: '100vh', position: 'fixed', left: 0, top: 0, zIndex: 100 }"
    theme="light"
    :width="256"
    :collapsed-width="64"
    class="modern-sidebar"
  >
    <!-- Logo/Brand -->
    <div class="logo-container">
      <!-- Collapsed Logo -->
      <img 
        v-if="collapsed"
        src="/public/Taskio_collapsed.svg" 
        alt="Taskio Logo" 
        :style="{ 
          height: '32px', 
          width: '32px', 
          objectFit: 'contain'
        }"
      />
      <!-- Expanded Logo -->
      <img 
        v-else
        src="/taskio-logo.svg" 
        alt="Taskio Logo" 
        :style="{ 
          height: '24px', 
          width: 'auto', 
          objectFit: 'contain',
          marginRight: '8px'
        }"
      />
    </div>

    <!-- Navigation Menu -->
    <a-menu
      v-model:selectedKeys="selectedKeys"
      v-model:openKeys="openKeys"
      mode="inline"
      class="sidebar-menu"
      @click="handleMenuClick"
    >
      <!-- Home -->
      <a-menu-item key="home">
        <template #icon>
          <HomeIcon />
        </template>
        Home
      </a-menu-item>

      <!-- Dashboard (Visible to all authenticated users) -->
      <a-menu-item key="dashboard">
        <template #icon>
          <DashboardIcon />
        </template>
        Dashboard
      </a-menu-item>

      <!-- Projects with submenu -->
      <a-sub-menu key="projects" @titleClick="handleProjectsTitleClick">
        <template #icon>
          <ProjectIcon />
        </template>
        <template #title>Projects</template>

        <!-- Loading state -->
        <a-menu-item v-if="projectsLoading" key="projects-loading" disabled>
          <template #icon>
            <a-spin size="small" />
          </template>
          Loading...
        </a-menu-item>

        <!-- Individual user projects -->
        <a-menu-item
          v-for="project in userProjects"
          :key="`project-${project.project_id}`"
          :title="project.project_name"
        >
          <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            {{ project.project_name }}
          </span>
        </a-menu-item>

        <!-- No projects message -->
        <a-menu-item v-if="!projectsLoading && userProjects.length === 0" key="no-projects" disabled>
          <template #icon>
            <div style="width: 6px; height: 6px; background-color: #d9d9d9; border-radius: 50%; margin-left: 2px;"></div>
          </template>
          No projects yet
        </a-menu-item>
      </a-sub-menu>
    </a-menu>

    <!-- Collapse Button -->
    <div class="collapse-button-container">
      <a-button
        type="text"
        :icon="collapsed ? h(MenuUnfoldOutlined) : h(MenuFoldOutlined)"
        @click="toggleCollapse"
        class="collapse-button"
      >
      </a-button>
    </div>

    <!-- User section at bottom -->
    <div class="user-section">
      <a-dropdown :trigger="['click']" placement="topLeft">
        <div class="user-info">
          <a-avatar :size="36" class="user-avatar">
            <template #icon>
              <UserIcon />
            </template>
          </a-avatar>
          <div v-if="!collapsed" class="user-details">
            <div class="user-name">
              {{ user?.name || 'Loading...' }}
            </div>
            <div class="user-role">
              {{ user?.role || 'Role' }}
            </div>
          </div>
        </div>
        <template #overlay>
          <a-menu>
            <a-menu-item key="logout" @click="logout">
              <template #icon>
                <LogoutIcon />
              </template>
              Logout
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </a-layout-sider>
</template>

<style scoped>
/* Modern Sidebar */
.modern-sidebar {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.06) !important;
  border-right: 1px solid #e5e7eb !important;
}

:deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
  background: linear-gradient(to bottom, #ffffff, #fafbfc) !important;
}

/* Logo Container */
.logo-container {
  padding: 24px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  min-height: 72px;
}

/* Sidebar Menu */
.sidebar-menu {
  height: calc(100vh - 170px);
  border-right: 0 !important;
  padding: 20px 12px !important;
  background: transparent !important;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Custom Scrollbar */
.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Menu Items */
:deep(.ant-menu-item) {
  margin-bottom: 4px !important;
  margin-top: 0 !important;
  border-radius: 10px !important;
  height: 44px !important;
  line-height: 44px !important;
  padding: 0 16px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  font-weight: 500 !important;
  font-size: 14px !important;
}

:deep(.ant-menu-item:hover) {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08), rgba(64, 169, 255, 0.08)) !important;
  color: #1890ff !important;
  transform: translateX(2px);
}

:deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, #1890ff, #40a9ff) !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.25) !important;
}

:deep(.ant-menu-item-selected:hover) {
  background: linear-gradient(135deg, #1890ff, #40a9ff) !important;
  transform: translateX(0);
}

:deep(.ant-menu-item-selected .anticon) {
  color: #ffffff !important;
}

/* Submenu */
:deep(.ant-menu-submenu) {
  margin-bottom: 4px !important;
}

:deep(.ant-menu-submenu-title) {
  border-radius: 10px !important;
  height: 44px !important;
  line-height: 44px !important;
  padding: 0 16px !important;
  margin: 0 !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  font-weight: 500 !important;
  font-size: 14px !important;
}

:deep(.ant-menu-submenu-title:hover) {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08), rgba(64, 169, 255, 0.08)) !important;
  color: #1890ff !important;
}

:deep(.ant-menu-submenu-open > .ant-menu-submenu-title) {
  color: #1890ff !important;
  font-weight: 600 !important;
}

/* Submenu Items */
:deep(.ant-menu-sub .ant-menu-item) {
  height: 40px !important;
  line-height: 40px !important;
  font-size: 13px !important;
  padding-left: 48px !important;
}

/* Icons - Expanded State */
:deep(.ant-menu-item-icon),
:deep(.ant-menu-submenu-title .ant-menu-item-icon) {
  font-size: 20px !important;
  margin-right: 12px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

:deep(.ant-menu-item-icon img),
:deep(.ant-menu-submenu-title .ant-menu-item-icon img) {
  width: 20px !important;
  height: 20px !important;
  object-fit: contain !important;
}

/* Icons - Collapsed State */
:deep(.ant-menu-inline-collapsed .ant-menu-item),
:deep(.ant-menu-inline-collapsed .ant-menu-submenu-title) {
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

:deep(.ant-menu-inline-collapsed .ant-menu-item-icon),
:deep(.ant-menu-inline-collapsed .ant-menu-submenu-title .ant-menu-item-icon) {
  font-size: 24px !important;
  margin: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
}

:deep(.ant-menu-inline-collapsed .ant-menu-item-icon img),
:deep(.ant-menu-inline-collapsed .ant-menu-submenu-title .ant-menu-item-icon img) {
  width: 24px !important;
  height: 24px !important;
  object-fit: contain !important;
}

/* Collapse Button Container */
.collapse-button-container {
  position: absolute;
  bottom: 72px;
  left: 0;
  right: 0;
  padding: 8px 12px;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
}

.collapse-button {
  height: 36px !important;
  width: 100% !important;
  border-radius: 8px !important;
  font-size: 16px !important;
  transition: all 0.3s ease !important;
  border: 1px solid #e5e7eb !important;
}

.collapse-button:hover {
  background: #f3f4f6 !important;
  border-color: #1890ff !important;
  color: #1890ff !important;
}

/* User Section */
.user-section {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  background: #ffffff;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: #f3f4f6;
}

.user-avatar {
  background: linear-gradient(135deg, #1890ff, #40a9ff) !important;
  flex-shrink: 0;
}

.user-details {
  margin-left: 12px;
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.user-role {
  font-size: 12px;
  color: #6b7280;
  text-transform: capitalize;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  margin-top: 2px;
}

/* Collapsed State */
:deep(.ant-layout-sider-collapsed) .user-info {
  justify-content: center;
  padding: 4px;
}

:deep(.ant-layout-sider-collapsed) .collapse-button-container {
  padding: 8px;
}

/* Dark Mode Support */
:global(.dark) .modern-sidebar {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3) !important;
  border-right-color: #374151 !important;
}

:global(.dark) :deep(.ant-layout-sider-children) {
  background: linear-gradient(to bottom, #1f2937, #111827) !important;
}

:global(.dark) .logo-container,
:global(.dark) .collapse-button-container,
:global(.dark) .user-section {
  background: #1f2937;
  border-color: #374151;
}

:global(.dark) :deep(.ant-menu-item:hover) {
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.15), rgba(59, 130, 246, 0.15)) !important;
  color: #60a5fa !important;
}

:global(.dark) :deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
}

:global(.dark) .user-name {
  color: #f9fafb;
}

:global(.dark) .user-role {
  color: #d1d5db;
}
</style>

<script>
import { computed, ref, onMounted, onUnmounted, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'
import { HomeIcon, TaskIcon, DashboardIcon, ProjectIcon, SettingsIcon, UserIcon, LogoutIcon } from '../components/icons/index.js'
import { useAuthStore } from '../stores/auth.js'
import { useProjectEvents } from '../composables/useProjectEvents.js'

export default {
  name: 'Sidebar',
  props: {
    isCollapsed: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:isCollapsed'],
  components: {
    HomeIcon,
    TaskIcon,
    DashboardIcon,
    ProjectIcon,
    SettingsIcon,
    UserIcon,
    LogoutIcon,
    MenuFoldOutlined,
    MenuUnfoldOutlined
  },
  setup(props, { emit }) {
    const router = useRouter()
    const route = useRoute()
    const authStore = useAuthStore()
    const { onProjectCreated, onProjectUpdated, onProjectDeleted } = useProjectEvents()

    // Get user data directly from auth store
    const user = computed(() => authStore.user)

    // Ant Design menu state
    const selectedKeys = ref(['home'])
    const openKeys = ref([])
    const collapsed = computed({
      get: () => props.isCollapsed,
      set: (value) => emit('update:isCollapsed', value)
    })

    // Projects state
    const userProjects = ref([])
    const projectsLoading = ref(false)

    const handleNavigation = (path) => {
      router.push(path)
    }

    const handleMenuClick = ({ key }) => {
      if (key === 'home') {
        handleNavigation('/home')
      } else if (key === 'dashboard') {
        handleNavigation('/dashboard')
      } else if (key.startsWith('project-')) {
        const projectId = key.replace('project-', '')
        handleNavigation(`/projects/${projectId}`)
      }
    }

    const handleProjectsTitleClick = () => {
      handleNavigation('/projects')
    }

    const toggleCollapse = () => {
      collapsed.value = !collapsed.value
    }

    const loadUserProjects = async () => {
      if (!user.value?.user_id) return

      projectsLoading.value = true
      try {
        const baseUrl = 'http://localhost:8082'
        const response = await fetch(`${baseUrl}/projects?created_by=${encodeURIComponent(user.value.user_id)}`)

        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const payload = await response.json()
        const allProjects = Array.isArray(payload?.projects) ? payload.projects : []

        // Filter to only show Active projects (exclude Completed)
        userProjects.value = allProjects.filter(project => project.status !== 'Completed')
      } catch (error) {
        console.error('Failed to load user projects:', error)
        userProjects.value = []
      } finally {
        projectsLoading.value = false
      }
    }

    const logout = async () => {
      try {
        await authStore.logout()
        await router.push('/login')
      } catch (error) {
        console.error('Logout error:', error)
      }
    }

    // Update selected keys based on current route
    const updateSelectedKeys = () => {
      const path = route.path
      if (path === '/home' || path === '/') {
        selectedKeys.value = ['home']
        openKeys.value = []
      } else if (path === '/dashboard') {
        selectedKeys.value = ['dashboard']
        openKeys.value = []
      } else if (path === '/projects') {
        selectedKeys.value = []
        openKeys.value = ['projects']
      } else if (path.startsWith('/projects/')) {
        const projectId = path.split('/projects/')[1]
        selectedKeys.value = [`project-${projectId}`]
        openKeys.value = ['projects']
      }
    }

    // Watch for route changes
    watch(() => route.path, updateSelectedKeys, { immediate: true })

    // Load projects when user becomes available
    watch(() => user.value?.user_id, (newUserId) => {
      if (newUserId && userProjects.value.length === 0 && !projectsLoading.value) {
        loadUserProjects()
      }
    }, { immediate: true })

    // Auto-open projects submenu when there are projects and not collapsed
    watch([() => userProjects.value.length, collapsed], ([projectsLength, isCollapsed]) => {
      if (projectsLength > 0 && !isCollapsed && !openKeys.value.includes('projects')) {
        openKeys.value = ['projects']
      }
    })

    // Listen for project events and reload
    const cleanupCreated = onProjectCreated(() => {
      loadUserProjects()
    })

    const cleanupUpdated = onProjectUpdated(() => {
      loadUserProjects()
    })

    const cleanupDeleted = onProjectDeleted(() => {
      loadUserProjects()
    })

    // Cleanup listeners on unmount
    onUnmounted(() => {
      cleanupCreated()
      cleanupUpdated()
      cleanupDeleted()
    })

    return {
      user,
      selectedKeys,
      openKeys,
      collapsed,
      userProjects,
      projectsLoading,
      handleNavigation,
      handleMenuClick,
      handleProjectsTitleClick,
      toggleCollapse,
      logout,
      loadUserProjects, // Expose for external refresh
      h,
      MenuFoldOutlined,
      MenuUnfoldOutlined
    }
  }
}
</script>
