import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const TASK_SERVICE_URL = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
const USER_SERVICE_URL = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'

/**
 * Composable for managing team tasks in the Manager Dashboard
 * Handles fetching subordinates and their tasks with auto-refresh
 */
export function useTeamTasks() {
  const authStore = useAuthStore()
  
  const tasks = ref([])
  const subordinates = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const lastFetchTime = ref(null)
  const refreshInterval = ref(null)

  /**
   * Fetch all subordinates for the current manager/director
   */
  const fetchSubordinates = async () => {
    const userId = authStore.user?.user_id
    if (!userId) {
      throw new Error('User ID not available')
    }

    const response = await fetch(`${USER_SERVICE_URL}/users/${userId}/subordinates`)
    if (!response.ok) {
      throw new Error('Failed to fetch subordinates')
    }

    const data = await response.json()
    return data.subordinates || []
  }

  /**
   * Fetch tasks for a specific user
   */
  const fetchUserTasks = async (userId) => {
    const response = await fetch(`${TASK_SERVICE_URL}/tasks?owner_id=${userId}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch tasks for user ${userId}`)
    }
    return response.json()
  }

  /**
   * Fetch all team tasks (tasks for all subordinates)
   */
  const fetchTeamTasks = async () => {
    isLoading.value = true
    error.value = null

    try {
      // 1. Get subordinates
      const subs = await fetchSubordinates()
      subordinates.value = subs

      if (subs.length === 0) {
        tasks.value = []
        return
      }

      // 2. Fetch tasks for each subordinate
      const taskPromises = subs.map(async (sub) => {
        try {
          const data = await fetchUserTasks(sub.user_id)
          return (data.tasks || []).map(task => ({
            ...task,
            assigneeName: sub.name,
            assigneeRole: sub.role,
            assigneeId: sub.user_id,
            assigneeDepartment: sub.department
          }))
        } catch (err) {
          console.error(`Error fetching tasks for ${sub.name}:`, err)
          return []
        }
      })

      const results = await Promise.all(taskPromises)
      tasks.value = results.flat()
      lastFetchTime.value = new Date()

    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Start auto-refresh interval (every 5 minutes)
   */
  const startAutoRefresh = () => {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
    }
    
    refreshInterval.value = setInterval(() => {
      console.log('Auto-refreshing team tasks...')
      fetchTeamTasks()
    }, 5 * 60 * 1000) // 5 minutes
  }

  /**
   * Stop auto-refresh interval
   */
  const stopAutoRefresh = () => {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  }

  /**
   * Initialize: fetch tasks and start auto-refresh
   */
  const initialize = () => {
    fetchTeamTasks()
    startAutoRefresh()
  }

  /**
   * Cleanup on unmount
   */
  onUnmounted(() => {
    stopAutoRefresh()
  })

  return {
    tasks,
    subordinates,
    isLoading,
    error,
    lastFetchTime,
    fetchTeamTasks,
    initialize,
    startAutoRefresh,
    stopAutoRefresh
  }
}
