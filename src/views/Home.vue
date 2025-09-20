<template>
  <div style="max-width: 1600px; margin: 0 auto; padding: 24px;">
    <!-- Welcome Header -->
    <a-card :bordered="false" :style="headerStyle">
      <a-row :gutter="24" align="middle">
        <a-col :span="16">
          <a-typography-title :level="2" :style="titleStyle">
            {{ getGreeting() }}, {{ currentUser?.name }}! 👋
          </a-typography-title>
          <a-typography-paragraph :style="subtitleStyle">
            {{ getMotivationalMessage() }}
          </a-typography-paragraph>
        </a-col>
        <a-col :span="8" style="text-align: right;">
          <a-space direction="vertical" align="end">
            <a-statistic
              title="Today's Progress"
              :value="`${stats.completed}/${stats.total}`"
              :value-style="statisticValueStyle"
              :title-style="statisticTitleStyle"
            />
            <a-avatar :size="64" :style="avatarStyle">
              {{ getUserInitials() }}
            </a-avatar>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- Main Content Row -->
    <a-row :gutter="24" style="margin-bottom: 24px;">
      <!-- Tasks Section -->
      <a-col :span="12">
        <TaskList />
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useTheme } from '../composables/useTheme.js'
import TaskList from '../components/tasks/TaskList.vue'

export default {
  name: 'Home',
  components: {
    TaskList
  },
  setup() {
    const tasks = ref([])
    const { isDarkMode } = useTheme()

    const currentUser = computed(() => {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user) : null
    })

    const stats = computed(() => {
      const total = tasks.value.length
      const completed = tasks.value.filter(task => task.status === 'Completed').length
      const unassigned = tasks.value.filter(task => task.status === 'Unassigned').length
      return { total, completed, unassigned }
    })

    // Helper functions for welcome section
    const getGreeting = () => {
      const hour = new Date().getHours()
      if (hour < 12) return 'Good morning'
      if (hour < 17) return 'Good afternoon'
      return 'Good evening'
    }

    const getMotivationalMessage = () => {
      return "Manage your tasks and stay productive!"
    }

    const getUserInitials = () => {
      if (!currentUser.value?.name) return 'U'
      return currentUser.value.name
        .split(' ')
        .map(name => name.charAt(0))
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }

    // Theme-aware header style
    const headerStyle = computed(() => {
      const lightGradient = 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)'
      const darkGradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      
      return {
        marginBottom: '24px',
        background: isDarkMode.value ? darkGradient : lightGradient
      }
    })

    // Theme-aware text styles
    const titleStyle = computed(() => ({
      color: isDarkMode.value ? 'white' : '#1976d2',
      marginBottom: '8px'
    }))

    const subtitleStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.9)' : 'rgba(25,118,210,0.8)',
      fontSize: '16px',
      marginBottom: '0'
    }))

    const statisticValueStyle = computed(() => ({
      color: isDarkMode.value ? 'white' : '#1976d2',
      fontSize: '24px'
    }))

    const statisticTitleStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.8)' : 'rgba(25,118,210,0.7)'
    }))

    const avatarStyle = computed(() => ({
      background: isDarkMode.value ? 'rgba(255,255,255,0.2)' : 'rgba(25,118,210,0.2)',
      color: isDarkMode.value ? 'white' : '#1976d2',
      fontSize: '20px',
      fontWeight: 'bold'
    }))

    // Load tasks for stats (could be moved to TaskList if needed)
    onMounted(async () => {
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const ownerId = import.meta.env.VITE_TASK_OWNER_ID || ''
        const url = ownerId
          ? `${baseUrl}/tasks?owner_id=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/tasks`
        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
        tasks.value = apiTasks.map(t => ({
          id: t.id,
          title: t.title,
          dueDate: t.dueDate || null,
          status: t.status
        }))
      } catch (e) {
        console.error('Failed to load tasks for stats:', e)
        tasks.value = []
      }
    })

    return {
      currentUser,
      stats,
      getGreeting,
      getMotivationalMessage,
      getUserInitials,
      headerStyle,
      titleStyle,
      subtitleStyle,
      statisticValueStyle,
      statisticTitleStyle,
      avatarStyle
    }
  }
}
</script>


