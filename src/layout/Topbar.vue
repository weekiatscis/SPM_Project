<template>
  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
    <!-- Left side: Mobile menu + Search -->
    <div style="display: flex; align-items: center; gap: 16px;">
      <!-- Mobile menu button -->
      <a-button
        v-if="isMobile"
        type="text"
        @click="$emit('toggle-mobile-sidebar')"
        style="font-size: 16px; width: 40px; height: 40px;"
      >
        <template #icon>
          <MenuIcon />
        </template>
      </a-button>

      <!-- Search bar -->
      <a-input-search
        v-model:value="searchQuery"
        placeholder="Search tasks, projects..."
        :style="{ width: isMobile ? '200px' : '300px' }"
        @search="handleSearch"
      >
        <template #prefix>
          <SearchIcon />
        </template>
      </a-input-search>
    </div>

    <!-- Right side: Notifications + Profile -->
    <div style="display: flex; align-items: center; gap: 8px;">
      <!-- Notifications -->
      <a-badge :count="3" size="small">
        <a-button type="text" shape="circle" size="large">
          <template #icon>
            <BellIcon />
          </template>
        </a-button>
      </a-badge>

      <!-- Theme Toggle -->
      <a-button type="text" shape="circle" size="large" @click="toggleTheme">
        <template #icon>
          <component :is="isDark ? 'SunIcon' : 'MoonIcon'" />
        </template>
      </a-button>

      <!-- User Profile Dropdown -->
      <a-dropdown :trigger="['click']" placement="bottomRight">
        <a-button type="text" style="height: 40px; padding: 4px 8px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <a-avatar :size="32" style="background-color: #1890ff;">
              {{ user?.name?.charAt(0).toUpperCase() || 'U' }}
            </a-avatar>
            <span v-if="!isMobile" style="font-size: 14px; font-weight: 500;">
              {{ user?.name || 'Loading...' }}
            </span>
            <DownOutlined style="font-size: 12px;" />
          </div>
        </a-button>
        <template #overlay>
          <a-menu @click="handleMenuClick">
            <a-menu-item key="profile">
              <UserOutlined style="margin-right: 8px;" />
              Profile Settings
            </a-menu-item>
            <a-menu-item key="preferences">
              <SettingOutlined style="margin-right: 8px;" />
              Preferences
            </a-menu-item>
            <a-menu-divider />
            <a-menu-item key="logout">
              <LogoutOutlined style="margin-right: 8px;" />
              Sign out
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined, 
  UserOutlined, 
  SettingOutlined, 
  LogoutOutlined,
  DownOutlined 
} from '@ant-design/icons-vue'
import { MenuIcon, SearchIcon, BellIcon } from '../components/icons/index.js'
import { useTheme } from '../composables/useTheme.js'
import { useAuthStore } from '../stores/auth.js'

export default {
  name: 'Topbar',
  props: {
    isSidebarCollapsed: {
      type: Boolean,
      default: false
    }
  },
  components: {
    MenuIcon,
    SearchIcon,
    BellIcon,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    UserOutlined,
    SettingOutlined,
    LogoutOutlined,
    DownOutlined
  },
  emits: ['toggle-mobile-sidebar', 'toggle-sidebar'],
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const searchQuery = ref('')
    
    // Get user data directly from auth store and use theme composable
    const user = computed(() => authStore.user)
    const { isDark, toggleTheme } = useTheme()

    // Responsive check
    const isMobile = ref(window.innerWidth < 768)

    const handleSearch = (value) => {
      console.log('Searching for:', value)
      // Implement search functionality here
    }

    const handleMenuClick = async ({ key }) => {
      if (key === 'logout') {
        await logout()
      } else if (key === 'profile') {
        // TODO: Navigate to profile settings page
        console.log('Navigate to profile settings')
      } else if (key === 'preferences') {
        // TODO: Navigate to preferences page
        console.log('Navigate to preferences')
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

    // Handle window resize for responsive behavior
    const handleResize = () => {
      isMobile.value = window.innerWidth < 768
    }

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })

    // Create icons for theme toggle
    const SunIcon = () => h('svg', {
      viewBox: '0 0 24 24',
      width: '16',
      height: '16',
      fill: 'currentColor'
    }, [
      h('path', {
        d: 'M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z'
      })
    ])

    const MoonIcon = () => h('svg', {
      viewBox: '0 0 24 24',
      width: '16',
      height: '16',
      fill: 'currentColor'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z',
        'clip-rule': 'evenodd'
      })
    ])

    return {
      searchQuery,
      user,
      isDark,
      isMobile,
      handleSearch,
      handleMenuClick,
      logout,
      toggleTheme,
      h,
      MenuFoldOutlined,
      MenuUnfoldOutlined,
      SunIcon,
      MoonIcon
    }
  }
}
</script>
