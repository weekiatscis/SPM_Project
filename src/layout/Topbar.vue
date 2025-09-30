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
      <NotificationDropdown />

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
import { useAuthStore } from '../stores/auth.js'
import NotificationDropdown from '../components/notifications/NotificationDropdown.vue'


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
    DownOutlined,
    NotificationDropdown
  },
  emits: ['toggle-mobile-sidebar', 'toggle-sidebar'],
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const searchQuery = ref('')
    
    // Get user data directly from auth store
    const user = computed(() => authStore.user)

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



    return {
      searchQuery,
      user,
      isMobile,
      handleSearch,
      handleMenuClick,
      logout,
      h,
      MenuFoldOutlined,
      MenuUnfoldOutlined
    }
  }
}
</script>
