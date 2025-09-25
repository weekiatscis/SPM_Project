<template>
  <a-layout-sider
    v-model:collapsed="collapsed"
    :trigger="null"
    collapsible
    :style="{ height: '100vh', position: 'fixed', left: 0, top: 0, zIndex: 100 }"
    theme="light"
    :width="256"
    :collapsed-width="64"
  >
    <!-- Logo/Brand -->
    <div class="logo-container" :style="{ 
      padding: '16px', 
      borderBottom: '1px solid #f0f0f0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: collapsed ? 'center' : 'flex-start'
    }">
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
      :style="{ height: 'calc(100vh - 170px)', borderRight: 0 }"
      @click="handleMenuClick"
    >
      <!-- Home -->
      <a-menu-item key="home">
        <template #icon>
          <HomeIcon />
        </template>
        Home
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
    <div :style="{ 
      position: 'absolute', 
      bottom: '72px', 
      left: 0, 
      right: 0, 
      padding: '4px 16px',
      backgroundColor: '#fff',
      display: 'flex',
      justifyContent: collapsed ? 'center' : 'flex-end'
    }">
      <a-button
        type="text"
        :icon="collapsed ? h(MenuUnfoldOutlined) : h(MenuFoldOutlined)"
        @click="toggleCollapse"
        :style="{ 
          height: '32px',
          width: collapsed ? '100%' : 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px' // Adjust this value to change collapse button icon size
        }"
      >
      </a-button>
    </div>

    <!-- User section at bottom -->
    <div :style="{ 
      position: 'absolute', 
      bottom: 0, 
      left: 0, 
      right: 0, 
      padding: '16px', 
      borderTop: '1px solid #f0f0f0',
      backgroundColor: '#fff'
    }">
      <a-dropdown :trigger="['hover']" placement="topLeft">
        <div :style="{ 
          display: 'flex', 
          alignItems: 'center', 
          cursor: 'pointer',
          justifyContent: collapsed ? 'center' : 'flex-start'
        }">
          <a-avatar :size="collapsed ? 28 : 32" style="background-color: #f56a00;">
            <template #icon>
              <UserIcon />
            </template>
          </a-avatar>
          <div v-if="!collapsed" style="margin-left: 12px; flex: 1; min-width: 0;">
            <div style="font-weight: 500; font-size: 14px; color: #262626; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              {{ user?.name || 'Loading...' }}
            </div>
            <div style="font-size: 12px; color: #8c8c8c; text-transform: capitalize; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
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


/* If you want to specifically target your custom icons */
:deep(.ant-menu-inline-collapsed .ant-menu-item-icon),
:deep(.ant-menu-inline-collapsed .ant-menu-submenu-title .ant-menu-item-icon) {
  width: 32px !important; /* Adjust width */
  height: 32px !important; /* Adjust height */
}

</style>

<script>
import { computed, ref, onMounted, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'
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

    // Use the user composable to get user data
    const { user, loading, error } = useUser()

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

    // Update selected keys based on current route
    const updateSelectedKeys = () => {
      const path = route.path
      if (path === '/home' || path === '/') {
        selectedKeys.value = ['home']
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

    return {
      user,
      loading,
      error,
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
      h,
      MenuFoldOutlined,
      MenuUnfoldOutlined
    }
  }
}
</script>
