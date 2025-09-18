<template>
  <!-- Create Group Modal -->
  <a-modal 
    v-model:visible="showGroupModal" 
    title="Create Group" 
    @ok="addGroup" 
    @cancel="onCancelGroupModal"
    :width="400"
  >
    <a-input v-model:value="newGroupName" placeholder="Enter group name" size="large" />
  </a-modal>

  <!-- Task Form Modal -->
  <TaskFormModal 
    :isOpen="showTaskModal" 
    @close="showTaskModal = false" 
    @save="handleTaskSaved"
  />

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
        <a-card 
          title="All Tasks" 
          style="height: 500px;"
        >
          <template #extra>
            <a-button type="primary" size="small" :icon="h(PlusOutlined)" @click="showTaskModal = true">
              Create Task
            </a-button>
          </template>
          <a-list
            :data-source="allTasks"
            :locale="{ emptyText: 'No tasks found' }"
            style="height: 400px; overflow-y: auto;"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card
                  :hoverable="true"
                  size="small"
                  :style="{ width: '100%' }"
                >
                  <a-row justify="space-between" align="middle">
                    <a-col :span="16">
                      <a-typography-text strong>{{ item.title }}</a-typography-text>
                      <br>
                      <a-typography-text type="secondary" style="font-size: 12px;">
                        Due: {{ formatDate(item.dueDate) }}
                      </a-typography-text>
                    </a-col>
                    <a-col :span="8" style="text-align: right;">
                      <a-tag :color="getStatusColor(item.status)">
                        {{ getStatusText(item.status) }}
                      </a-tag>
                    </a-col>
                  </a-row>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>

    
  </div>
</template>

<script>

import { ref, computed, onMounted, h } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useTheme } from '../composables/useTheme.js'
import TaskFormModal from '../components/tasks/TaskFormModal.vue'

export default {
  name: 'Home',
  components: {
    PlusOutlined,
    TaskFormModal
  },
  setup() {
    const tasks = ref([])
    const { isDarkMode } = useTheme()

    // Groups/drag-and-drop removed

    // Modal state for creating group
    const showGroupModal = ref(false)
    const newGroupName = ref('')
    const showTaskModal = ref(false)

    // Add group
    const addGroup = () => {
      if (!newGroupName.value.trim()) return
      groups.value.push({
        id: Date.now(),
        name: newGroupName.value.trim(),
        tasks: []
      })
      newGroupName.value = ''
      showGroupModal.value = false
    }

    // Helpers: DB <-> UI mapping
    const normalizeStatus = (value) => value

    const mapFromDb = (row) => ({
      id: row.task_id ?? row.id,
      title: row.title,
      dueDate: row.due_date || null,
      status: normalizeStatus(row.status)
    })

    // Handle task saved from TaskFormModal
    const handleTaskSaved = (taskData) => {
      // Transform the API response to match frontend format
      const mappedTask = {
        id: taskData.task_id || taskData.id,
        title: taskData.title,
        dueDate: taskData.due_date || taskData.dueDate,
        status: taskData.status
      }
      
      // Add the new task to the tasks list
      tasks.value.unshift(mappedTask)
      // Close the modal
      showTaskModal.value = false
    }

  // Card titles with + icon (now handled in template slots)
    // Modal cancel handlers
    const onCancelGroupModal = () => {
      showGroupModal.value = false
      newGroupName.value = ''
    }

    // All tasks (renamed from unassignedTasks)
    const allTasks = computed(() => tasks.value)

    // Drag-and-drop removed

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

    // recentTasks removed

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = date.getTime() - now.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) {
        return `${Math.abs(diffDays)} days overdue`
      } else if (diffDays === 0) {
        return 'today'
      } else if (diffDays === 1) {
        return 'tomorrow'
      } else {
        return `in ${diffDays} days`
      }
    }

    const getStatusColor = (status) => {
      const colors = {
        'Unassigned': 'default',
        'Ongoing': 'blue',
        'Under Review': 'gold',
        'Completed': 'green'
      }
      return colors[status] || 'default'
    }

    const getStatusText = (status) => {
      const texts = {
        'Unassigned': 'Unassigned',
        'Ongoing': 'Ongoing',
        'Under Review': 'Under Review',
        'Completed': 'Completed'
      }
      return texts[status] || 'Unassigned'
    }

    // Navigation to other screens is disabled until those screens exist

    // Helper functions for welcome section
    const getGreeting = () => {
      const hour = new Date().getHours()
      if (hour < 12) return 'Good morning'
      if (hour < 17) return 'Good afternoon'
      return 'Good evening'
    }

    const getMotivationalMessage = () => {
      const hour = new Date().getHours()
      const completedToday = tasks.value.filter(task => 
        task.status === 'Completed' && 
        new Date(task.dueDate).toDateString() === new Date().toDateString()
      ).length
      
      if (hour < 12) {
        return completedToday > 0 
          ? `Great start! You've completed ${completedToday} task${completedToday > 1 ? 's' : ''} today.`
          : "Ready to tackle today's tasks? Let's make it productive!"
      } else if (hour < 17) {
        return completedToday > 0
          ? `Keep up the momentum! ${completedToday} task${completedToday > 1 ? 's' : ''} completed so far.`
          : "Afternoon productivity time! What's your next priority?"
      } else {
        return completedToday > 0
          ? `Well done today! You completed ${completedToday} task${completedToday > 1 ? 's' : ''}.`
          : "Evening wind-down time. Any final tasks to wrap up?"
      }
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
          status: normalizeStatus(t.status)
        }))
      } catch (e) {
        console.error('Failed to load tasks via service:', e)
        tasks.value = []
      }
    })

    return {
      h,
      currentUser,
      stats,
      formatDate,
      getStatusColor,
      getStatusText,
      getGreeting,
      getMotivationalMessage,
      getUserInitials,
      headerStyle,
      titleStyle,
      subtitleStyle,
      statisticValueStyle,
      statisticTitleStyle,
      avatarStyle,
      allTasks,
      showGroupModal,
      newGroupName,
      addGroup,
      showTaskModal,
      handleTaskSaved,
      onCancelGroupModal
    }
  }
}
</script>

<style scoped>
.draggable-task-card {
  transition: all 0.2s ease;
}

.draggable-task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.draggable-task-card.dragging {
  opacity: 0.6;
  transform: scale(1.02);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  cursor: grabbing;
}

.droppable-group-card {
  transition: all 0.2s ease;
  border: 2px dashed transparent;
}

.droppable-group-card.drag-over {
  border-color: #1890ff !important;
  border-style: solid !important;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  background-color: rgba(24, 144, 255, 0.05);
  transform: scale(1.02);
}

/* Custom scrollbar for better UX */
:deep(.ant-list) {
  scrollbar-width: thin;
  scrollbar-color: #d9d9d9 transparent;
}

:deep(.ant-list::-webkit-scrollbar) {
  width: 6px;
}

:deep(.ant-list::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.ant-list::-webkit-scrollbar-thumb) {
  background-color: #d9d9d9;
  border-radius: 3px;
}

:deep(.ant-list::-webkit-scrollbar-thumb:hover) {
  background-color: #bfbfbf;
}

/* Enhanced card hover effects */
:deep(.ant-card) {
  transition: all 0.2s ease;
}

:deep(.ant-card:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Better spacing for nested cards */
:deep(.ant-card .ant-card) {
  margin-bottom: 8px;
}

:deep(.ant-card .ant-card:last-child) {
  margin-bottom: 0;
}
</style>
