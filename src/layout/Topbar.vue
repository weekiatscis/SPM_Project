<template>
  <div class="topbar-container">
    <!-- Left side: Mobile menu + Search -->
    <div class="topbar-left">
      <!-- Mobile menu button -->
      <a-button
        v-if="isMobile"
        type="text"
        @click="$emit('toggle-mobile-sidebar')"
        class="mobile-menu-button"
      >
        <template #icon>
          <MenuIcon />
        </template>
      </a-button>

      <!-- Search bar -->
      <a-input-search
        v-model:value="searchQuery"
        placeholder="Search tasks, projects..."
        class="search-input"
        @search="handleSearch"
        size="large"
      >
        <template #prefix>
          <SearchIcon />
        </template>
      </a-input-search>
    </div>

    <!-- Right side: Notifications + Profile -->
    <div class="topbar-right">
      <!-- Notifications -->
      <NotificationDropdown />

      <!-- User Profile Dropdown -->
      <a-dropdown :trigger="['click']" placement="bottomRight" class="profile-dropdown">
        <a-button type="text" class="profile-button">
          <div class="profile-content">
            <a-avatar :size="36" class="profile-avatar">
              {{ user?.name?.charAt(0).toUpperCase() || 'U' }}
            </a-avatar>
            <span v-if="!isMobile" class="profile-name">
              {{ user?.name || 'Loading...' }}
            </span>
            <DownOutlined class="profile-arrow" />
          </div>
        </a-button>
        <template #overlay>
          <a-menu @click="handleMenuClick" class="profile-menu">
            <a-menu-item key="profile" class="menu-item">
              <UserOutlined class="menu-icon" />
              Profile Settings
            </a-menu-item>
            <a-menu-item key="preferences" class="menu-item">
              <SettingOutlined class="menu-icon" />
              Preferences
            </a-menu-item>
            <a-menu-divider />
            <a-menu-item key="logout" class="menu-item logout-item">
              <LogoutOutlined class="menu-icon" />
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
        router.push('/profile')
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

<style scoped>
/* Topbar Container */
.topbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 24px;
}

/* Left Side */
.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  max-width: 600px;
}

/* Mobile Menu Button */
.mobile-menu-button {
  width: 44px !important;
  height: 44px !important;
  border-radius: 10px !important;
  font-size: 18px !important;
  transition: all 0.3s ease !important;
  border: 1px solid #e5e7eb !important;
}

.mobile-menu-button:hover {
  background: #f3f4f6 !important;
  border-color: #1890ff !important;
  color: #1890ff !important;
}

/* Search Input */
.search-input {
  flex: 1;
  max-width: 500px;
}

:deep(.search-input .ant-input-affix-wrapper) {
  border-radius: 12px !important;
  border: 1.5px solid #e5e7eb !important;
  padding: 8px 16px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}

:deep(.search-input .ant-input-affix-wrapper:hover) {
  border-color: #1890ff !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1) !important;
}

:deep(.search-input .ant-input-affix-wrapper-focused) {
  border-color: #1890ff !important;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1), 0 2px 8px rgba(24, 144, 255, 0.15) !important;
}

:deep(.search-input .ant-input) {
  font-size: 14px !important;
  font-weight: 500 !important;
}

:deep(.search-input .ant-input::placeholder) {
  color: #9ca3af !important;
}

:deep(.search-input .ant-input-prefix) {
  margin-right: 12px !important;
  color: #6b7280 !important;
}

:deep(.search-input .ant-input-search-button) {
  border-radius: 8px !important;
  background: linear-gradient(135deg, #1890ff, #40a9ff) !important;
  border: none !important;
  height: 36px !important;
  transition: all 0.3s ease !important;
}

:deep(.search-input .ant-input-search-button:hover) {
  background: linear-gradient(135deg, #096dd9, #1890ff) !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3) !important;
}

/* Right Side */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Profile Button */
.profile-button {
  height: 48px !important;
  padding: 4px 12px !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
  border: 1px solid transparent !important;
}

.profile-button:hover {
  background: #f3f4f6 !important;
  border-color: #e5e7eb !important;
}

.profile-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.profile-avatar {
  background: linear-gradient(135deg, #1890ff, #40a9ff) !important;
  font-weight: 600 !important;
  flex-shrink: 0;
}

.profile-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-arrow {
  font-size: 12px;
  color: #6b7280;
  transition: transform 0.3s ease;
}

.profile-dropdown:hover .profile-arrow {
  transform: rotate(180deg);
}

/* Profile Menu */
:deep(.profile-menu) {
  border-radius: 12px !important;
  padding: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06) !important;
  border: 1px solid #e5e7eb !important;
  min-width: 200px !important;
}

:deep(.profile-menu .ant-dropdown-menu-item) {
  border-radius: 8px !important;
  padding: 10px 12px !important;
  margin-bottom: 4px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
}

:deep(.profile-menu .ant-dropdown-menu-item:hover) {
  background: #f3f4f6 !important;
  color: #1890ff !important;
}

:deep(.profile-menu .ant-dropdown-menu-item:last-child) {
  margin-bottom: 0 !important;
}

.menu-icon {
  margin-right: 10px !important;
  font-size: 16px !important;
}

:deep(.profile-menu .logout-item:hover) {
  background: #fef2f2 !important;
  color: #dc2626 !important;
}

:deep(.profile-menu .ant-dropdown-menu-item-divider) {
  margin: 8px 0 !important;
  background: #e5e7eb !important;
}

/* Dark Mode */
:global(.dark) .mobile-menu-button {
  border-color: #374151 !important;
}

:global(.dark) .mobile-menu-button:hover {
  background: #374151 !important;
  border-color: #60a5fa !important;
  color: #60a5fa !important;
}

:global(.dark) :deep(.search-input .ant-input-affix-wrapper) {
  background: #1f2937 !important;
  border-color: #374151 !important;
}

:global(.dark) :deep(.search-input .ant-input) {
  background: transparent !important;
  color: #f9fafb !important;
}

:global(.dark) :deep(.search-input .ant-input::placeholder) {
  color: #6b7280 !important;
}

:global(.dark) .profile-button:hover {
  background: #374151 !important;
  border-color: #4b5563 !important;
}

:global(.dark) .profile-name {
  color: #f9fafb;
}

:global(.dark) :deep(.profile-menu) {
  background: #1f2937 !important;
  border-color: #374151 !important;
}

:global(.dark) :deep(.profile-menu .ant-dropdown-menu-item) {
  color: #f9fafb !important;
}

:global(.dark) :deep(.profile-menu .ant-dropdown-menu-item:hover) {
  background: #374151 !important;
  color: #60a5fa !important;
}

/* Responsive */
@media (max-width: 768px) {
  .topbar-container {
    gap: 12px;
  }
  
  .topbar-left {
    gap: 8px;
    max-width: none;
  }
  
  .search-input {
    max-width: 200px;
  }
  
  :deep(.search-input .ant-input-affix-wrapper) {
    padding: 6px 12px !important;
  }
  
  .profile-button {
    padding: 4px 8px !important;
  }
}
</style>
