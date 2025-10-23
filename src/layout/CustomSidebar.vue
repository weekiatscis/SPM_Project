<template>
  <aside 
    :class="['custom-sidebar', { 'collapsed': isCollapsed }]"
    @mouseenter="handleSidebarEnter"
    @mouseleave="handleSidebarLeave"
  >
    <!-- Logo Section -->
    <div class="logo-section">
      <img 
        v-if="isCollapsed"
        src="/public/Taskio_collapsed.svg" 
        alt="Taskio" 
        class="logo-collapsed"
      />
      <img 
        v-else
        src="/taskio-logo.svg" 
        alt="Taskio" 
        class="logo-expanded"
      />
    </div>

    <!-- Navigation Menu -->
    <nav class="nav-menu">
      <!-- Home -->
      <router-link to="/home" class="nav-item" :class="{ 'active': isActive('/home') }">
        <div class="nav-icon">
          <HomeIcon />
        </div>
        <span v-if="!isCollapsed" class="nav-label">Home</span>
      </router-link>

      <!-- Dashboard -->
      <router-link to="/dashboard" class="nav-item" :class="{ 'active': isActive('/dashboard') }">
        <div class="nav-icon">
          <DashboardIcon />
        </div>
        <span v-if="!isCollapsed" class="nav-label">Dashboard</span>
      </router-link>

      <!-- Projects -->
      <div class="nav-group">
        <div
          class="nav-item nav-group-header"
          :class="{ 'active': isActive('/projects') }"
          @click="navigateToProjects"
        >
          <div class="nav-icon">
            <ProjectIcon />
          </div>
          <span v-if="!isCollapsed" class="nav-label">Projects</span>
          <svg
            v-if="!isCollapsed"
            class="expand-arrow"
            :class="{ 'expanded': projectsExpanded }"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            @click.stop="toggleProjects"
          >
            <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>

        <!-- Project List -->
        <div v-if="!isCollapsed && projectsExpanded" class="nav-submenu">
          <div v-if="projectsLoading" class="submenu-item loading">
            <div class="loading-spinner"></div>
            <span>Loading...</span>
          </div>
          <router-link 
            v-for="project in userProjects" 
            :key="project.project_id"
            :to="`/projects/${project.project_id}`"
            class="submenu-item"
            :class="{ 'active': isActive(`/projects/${project.project_id}`) }"
          >
            <div class="project-dot"></div>
            <span class="submenu-label">{{ project.project_name }}</span>
          </router-link>
          <div v-if="!projectsLoading && userProjects.length === 0" class="submenu-item empty">
            <span>No projects yet</span>
          </div>
        </div>
      </div>
    </nav>

    <!-- User Section -->
    <div class="user-section" @click="toggleUserMenu">
      <div class="user-avatar">
        <UserIcon />
      </div>
      <div v-if="!isCollapsed" class="user-info">
        <div class="user-name">{{ user?.name || 'Loading...' }}</div>
        <div class="user-role">{{ user?.role || 'Role' }}</div>
      </div>
      
      <!-- User Dropdown Menu -->
      <transition name="fade">
        <div v-if="userMenuOpen" class="user-menu" @click.stop>
          <button @click="logout" class="user-menu-item logout">
            <LogoutIcon />
            <span>Logout</span>
          </button>
        </div>
      </transition>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useProjectEvents } from '../composables/useProjectEvents.js'
import { HomeIcon, DashboardIcon, ProjectIcon, UserIcon, LogoutIcon } from '../components/icons/index.js'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:isCollapsed'])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { onProjectCreated, onProjectUpdated, onProjectDeleted } = useProjectEvents()

const user = computed(() => authStore.user)
const projectsExpanded = ref(true)
const projectsLoading = ref(false)
const userProjects = ref([])
const userMenuOpen = ref(false)
const leaveTimeout = ref(null)

const isActive = (path) => {
  if (path === '/home') {
    return route.path === '/' || route.path === '/home'
  }
  return route.path.startsWith(path)
}

const toggleCollapse = () => {
  emit('update:isCollapsed', !props.isCollapsed)
}

// Auto-expand sidebar on hover
const handleSidebarEnter = () => {
  // Clear any pending collapse
  if (leaveTimeout.value) {
    clearTimeout(leaveTimeout.value)
    leaveTimeout.value = null
  }
  
  // Expand sidebar immediately on hover
  emit('update:isCollapsed', false)
}

const handleSidebarLeave = () => {
  // Collapse sidebar after user leaves (with delay for smooth UX)
  leaveTimeout.value = setTimeout(() => {
    emit('update:isCollapsed', true)
  }, 300)
}

const navigateToProjects = () => {
  // Navigate to projects page when clicking anywhere on the header except arrow
  router.push('/projects')
}

const toggleProjects = () => {
  // Only toggle the dropdown, don't navigate
  if (!props.isCollapsed) {
    projectsExpanded.value = !projectsExpanded.value
  }
}

const toggleUserMenu = () => {
  userMenuOpen.value = !userMenuOpen.value
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

// Close user menu when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.user-section')) {
    userMenuOpen.value = false
  }
}

// Watch for user changes
watch(() => user.value?.user_id, (newUserId) => {
  if (newUserId && userProjects.value.length === 0 && !projectsLoading.value) {
    loadUserProjects()
  }
}, { immediate: true })

// Listen for project events
const cleanupCreated = onProjectCreated(() => loadUserProjects())
const cleanupUpdated = onProjectUpdated(() => loadUserProjects())
const cleanupDeleted = onProjectDeleted(() => loadUserProjects())

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // Start with sidebar collapsed for auto-hide behavior
  emit('update:isCollapsed', true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  // Clear any pending timeout
  if (leaveTimeout.value) clearTimeout(leaveTimeout.value)
  cleanupCreated()
  cleanupUpdated()
  cleanupDeleted()
})
</script>

<style scoped>
/* Custom Sidebar */
.custom-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 256px;
  background: linear-gradient(to bottom, #ffffff, #fafbfc);
  border-right: 1px solid #e5e7eb;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
}

.custom-sidebar.collapsed {
  width: 64px;
}

/* Logo Section */
.logo-section {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
  flex-shrink: 0;
}

.logo-collapsed {
  height: 32px;
  width: 32px;
  object-fit: contain;
}

.logo-expanded {
  height: 24px;
  width: auto;
  object-fit: contain;
}

/* Navigation Menu */
.nav-menu {
  flex: 1;
  padding: 20px 12px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Custom Scrollbar */
.nav-menu::-webkit-scrollbar {
  width: 4px;
}

.nav-menu::-webkit-scrollbar-track {
  background: transparent;
}

.nav-menu::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.nav-menu::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Nav Item */
.nav-item {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 16px;
  margin-bottom: 4px;
  border-radius: 10px;
  color: #374151;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
}

.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.nav-item:hover {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08), rgba(64, 169, 255, 0.08));
  color: #1890ff;
  transform: translateX(2px);
}

.collapsed .nav-item:hover {
  transform: translateX(0);
}

.nav-item.active {
  background: linear-gradient(135deg, #1890ff, #40a9ff);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.25);
}

.nav-item.active:hover {
  transform: translateX(0);
}

/* Nav Icon */
.nav-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-icon :deep(img) {
  width: 32px !important;
  height: 32px !important;
  object-fit: contain;
}

.nav-label {
  margin-left: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Nav Group */
.nav-group {
  margin-bottom: 4px;
}

.nav-group-header {
  position: relative;
}

.expand-arrow {
  position: absolute;
  right: 12px;
  transition: transform 0.3s ease;
  color: currentColor;
  cursor: pointer;
  padding: 4px;
}

.expand-arrow.expanded {
  transform: rotate(180deg);
}

/* Submenu */
.nav-submenu {
  margin-top: 4px;
  margin-left: 12px;
  padding-left: 12px;
  border-left: 2px solid #e5e7eb;
}

.submenu-item {
  display: flex;
  align-items: center;
  height: 36px;
  padding: 0 12px;
  margin-bottom: 2px;
  border-radius: 8px;
  color: #6b7280;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.submenu-item:hover {
  background: #f3f4f6;
  color: #1890ff;
}

.submenu-item.active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.1), rgba(64, 169, 255, 0.1));
  color: #1890ff;
  font-weight: 600;
}

.submenu-item.loading,
.submenu-item.empty {
  cursor: default;
  color: #9ca3af;
}

.submenu-item.loading:hover,
.submenu-item.empty:hover {
  background: transparent;
  color: #9ca3af;
}

.project-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  margin-right: 10px;
  flex-shrink: 0;
}

.submenu-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.loading-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #e5e7eb;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* User Section */
.user-section {
  position: relative;
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  background: #ffffff;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.collapsed .user-section {
  justify-content: center;
}

.user-section:hover {
  background: #f3f4f6;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #40a9ff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar :deep(img) {
  width: 20px !important;
  height: 20px !important;
  filter: brightness(0) invert(1);
}

.user-info {
  margin-left: 12px;
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.user-role {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  text-transform: capitalize;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* User Menu Dropdown */
.user-menu {
  position: absolute;
  bottom: 100%;
  left: 16px;
  right: 16px;
  margin-bottom: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
  padding: 8px;
  z-index: 1000;
}

.collapsed .user-menu {
  left: 72px;
  right: auto;
  min-width: 200px;
}

.user-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  background: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.user-menu-item:hover {
  background: #fef2f2;
  color: #dc2626;
}

.user-menu-item :deep(img) {
  width: 16px !important;
  height: 16px !important;
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Dark Mode */
:global(.dark) .custom-sidebar {
  background: linear-gradient(to bottom, #1f2937, #111827);
  border-right-color: #374151;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
}

:global(.dark) .logo-section,
:global(.dark) .user-section {
  background: #1f2937;
  border-color: #374151;
}

:global(.dark) .nav-item {
  color: #d1d5db;
}

:global(.dark) .nav-item:hover {
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.15), rgba(59, 130, 246, 0.15));
  color: #60a5fa;
}

:global(.dark) .nav-item.active {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
}

:global(.dark) .user-name {
  color: #f9fafb;
}

:global(.dark) .user-role {
  color: #d1d5db;
}

:global(.dark) .user-menu {
  background: #1f2937;
  border-color: #374151;
}

:global(.dark) .user-menu-item {
  color: #f9fafb;
}
</style>
