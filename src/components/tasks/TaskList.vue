<template>
  <div style="max-width: 1600px; margin: 0 auto; padding: 24px;">
    <!-- Header with filters and add button -->
    <a-card :bordered="false" :style="headerStyle">
      <a-row :gutter="24" align="middle">
        <a-col :span="16">
          <div style="display: flex; align-items: center; gap: 24px;">
            <div style="position: relative;">
              <img 
                src="/illustrations/task_illustration.png" 
                alt="Task Illustration" 
                :style="illustrationStyle"
              />
              <!-- Decorative circle behind illustration -->
              <div style="position: absolute; inset: 0; background: rgba(255,255,255,0.2); border-radius: 50%; transform: scale(1.1); z-index: -1;"></div>
            </div>
            <div style="flex: 1;">
              <a-typography-title :level="2" :style="titleStyle">
                Tasks
              </a-typography-title>
              <a-typography-paragraph :style="subtitleStyle">
                Manage your tasks and projects
              </a-typography-paragraph>
              <!-- Additional integration elements -->
              <a-space>
                <a-space>
                  <div :style="dotStyle"></div>
                  <a-typography-text :style="workspaceTextStyle">
                    Active workspace
                  </a-typography-text>
                </a-space>
                <a-typography-text :style="dateTextStyle">
                  {{ new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}
                </a-typography-text>
              </a-space>
            </div>
          </div>
        </a-col>
        <a-col :span="8" style="text-align: right;">
          <a-space>
            <!-- Filter dropdown -->
            <a-select
              v-model:value="selectedFilter"
              style="width: 120px"
              placeholder="Filter"
            >
              <a-select-option value="all">All Tasks</a-select-option>
              <a-select-option value="unassigned">Unassigned</a-select-option>
              <a-select-option value="ongoing">Ongoing</a-select-option>
              <a-select-option value="under-review">Under Review</a-select-option>
              <a-select-option value="completed">Completed</a-select-option>
            </a-select>

            <!-- Add task button -->
            <a-button
              type="primary"
              @click="showAddTaskModal = true"
              :icon="h(PlusOutlined)"
              style="background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.3); color: white;"
            >
              Add Task
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- Project tabs -->
    <a-tabs v-model:activeKey="selectedProject" @change="selectedProject = $event" style="margin-bottom: 24px;">
      <a-tab-pane
        v-for="project in projects"
        :key="project"
        :tab="`${project} (${getProjectTaskCount(project)})`"
      />
    </a-tabs>

    <!-- Task grid -->
    <div v-if="filteredTasks.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" style="margin-bottom: 24px;">
      <TaskCard
        v-for="task in filteredTasks"
        :key="task.id"
        :task="task"
        @view-details="viewTaskDetails"
        @edit-task="editTask"
        @delete-task="deleteTask"
        @toggle-complete="toggleTaskComplete"
        class="group"
      />
    </div>

    <!-- Empty state -->
    <a-empty v-else description="No tasks found">
      <a-button
        type="primary"
        @click="showAddTaskModal = true"
        :icon="h(PlusOutlined)"
      >
        Add your first task
      </a-button>
    </a-empty>

    <!-- Task Detail Modal -->
    <TaskDetailModal
      v-if="selectedTask"
      :task="selectedTask"
      :is-open="showDetailModal"
      @close="closeDetailModal"
      @save="saveTask"
      @delete="deleteTask"
    />

    <!-- Add/Edit Task Modal -->
    <TaskFormModal
      :task="editingTask"
      :is-open="showAddTaskModal || showEditTaskModal"
      @close="closeTaskModal"
      @save="saveTask"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, h } from 'vue'
import TaskCard from './TaskCard.vue'
import TaskDetailModal from './TaskDetailModal.vue'
import TaskFormModal from './TaskFormModal.vue'
import { sampleTasks } from '../../data/sampleData.js'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useNotifications } from '../../composables/useNotifications.js'
import { useTheme } from '../../composables/useTheme.js'

export default {
  name: 'TaskList',
  components: {
    TaskCard,
    TaskDetailModal,
    TaskFormModal,
    PlusOutlined
  },
  setup() {
    const tasks = ref([])
    const selectedProject = ref('All Projects')
    const selectedFilter = ref('all')
    const selectedTask = ref(null)
    const editingTask = ref(null)
    const showDetailModal = ref(false)
    const showAddTaskModal = ref(false)
    const showEditTaskModal = ref(false)
    const { showSuccess, showError, showWarning } = useNotifications()
    const { isDarkMode } = useTheme()

    // Load sample data
    onMounted(() => {
      tasks.value = [...sampleTasks]
    })

    const projects = computed(() => {
      const projectSet = new Set(['All Projects'])
      tasks.value.forEach(task => projectSet.add(task.project))
      return Array.from(projectSet)
    })

    const filteredTasks = computed(() => {
      let filtered = tasks.value

      // Filter by project
      if (selectedProject.value !== 'All Projects') {
        filtered = filtered.filter(task => task.project === selectedProject.value)
      }

      // Filter by status
      if (selectedFilter.value !== 'all') {
        filtered = filtered.filter(task => {
          if (selectedFilter.value === 'overdue') {
            const dueDate = new Date(task.dueDate)
            const now = new Date()
            return dueDate < now && task.status !== 'completed'
          }
          return task.status === selectedFilter.value
        })
      }

      return filtered
    })

    const getProjectTaskCount = (project) => {
      if (project === 'All Projects') {
        return tasks.value.length
      }
      return tasks.value.filter(task => task.project === project).length
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

    // Theme-aware illustration style
    const illustrationStyle = computed(() => {
      const baseStyle = {
        width: '100px',
        height: '100px',
        objectFit: 'contain',
        filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.1))'
      }
      
      // Invert colors in dark mode to make black illustration white
      if (isDarkMode.value) {
        baseStyle.filter += ' invert(1) brightness(1.2)'
      }
      
      return baseStyle
    })

    // Theme-aware text styles
    const titleStyle = computed(() => ({
      color: isDarkMode.value ? 'white' : '#1976d2',
      marginBottom: '8px'
    }))

    const subtitleStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.9)' : 'rgba(25,118,210,0.8)',
      fontSize: '16px',
      marginBottom: '12px'
    }))

    const dotStyle = computed(() => ({
      width: '8px',
      height: '8px',
      background: isDarkMode.value ? 'rgba(255,255,255,0.8)' : 'rgba(25,118,210,0.8)',
      borderRadius: '50%'
    }))

    const workspaceTextStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.8)' : 'rgba(25,118,210,0.8)',
      fontSize: '14px'
    }))

    const dateTextStyle = computed(() => ({
      color: isDarkMode.value ? 'rgba(255,255,255,0.7)' : 'rgba(25,118,210,0.7)',
      fontSize: '14px'
    }))

    const viewTaskDetails = (task) => {
      selectedTask.value = task
      showDetailModal.value = true
    }

    const editTask = (task) => {
      editingTask.value = { ...task }
      showEditTaskModal.value = true
    }

    const deleteTask = (task) => {
      if (confirm('Are you sure you want to delete this task?')) {
        tasks.value = tasks.value.filter(t => t.id !== task.id)
        showSuccess('Task deleted', `"${task.title}" has been deleted successfully`)
        closeDetailModal()
      }
    }

    const toggleTaskComplete = (updatedTask) => {
      const index = tasks.value.findIndex(t => t.id === updatedTask.id)
      if (index !== -1) {
        tasks.value[index] = updatedTask
        if (updatedTask.status === 'completed') {
          showSuccess('Task completed', `"${updatedTask.title}" has been marked as completed! 🎉`)
        } else {
          showInfo('Task status updated', `"${updatedTask.title}" status changed to ${updatedTask.status}`)
        }
      }
    }

    const saveTask = (taskData) => {
      if (taskData.id) {
        // Update existing task
        const index = tasks.value.findIndex(t => t.id === taskData.id)
        if (index !== -1) {
          tasks.value[index] = taskData
          showSuccess('Task updated', `"${taskData.title}" has been updated successfully`)
        }
      } else {
        // Add new task
        const newTask = {
          ...taskData,
          id: Date.now(),
          createdAt: new Date().toISOString()
        }
        tasks.value.push(newTask)
        showSuccess('Task created', `"${taskData.title}" has been added successfully`)
      }
      closeTaskModal()
      closeDetailModal()
    }

    const closeDetailModal = () => {
      showDetailModal.value = false
      selectedTask.value = null
    }

    const closeTaskModal = () => {
      showAddTaskModal.value = false
      showEditTaskModal.value = false
      editingTask.value = null
    }

    return {
      h,
      tasks,
      selectedProject,
      selectedFilter,
      selectedTask,
      editingTask,
      showDetailModal,
      showAddTaskModal,
      showEditTaskModal,
      projects,
      filteredTasks,
      getProjectTaskCount,
      headerStyle,
      illustrationStyle,
      titleStyle,
      subtitleStyle,
      dotStyle,
      workspaceTextStyle,
      dateTextStyle,
      viewTaskDetails,
      editTask,
      deleteTask,
      toggleTaskComplete,
      saveTask,
      closeDetailModal,
      closeTaskModal
    }
  }
}
</script>
