import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref([])
  const isLoading = ref(false)

  // Computed properties
  const unreadCount = computed(() => 
    notifications.value.filter(n => !n.is_read).length
  )

  const recentNotifications = computed(() => 
    notifications.value.slice(0, 10)
  )

  // Actions
  const fetchNotifications = async (userId) => {
    if (!userId) return

    isLoading.value = true
    try {
      // Fetch from notification service first, fallback to task service
      const notificationServiceUrl = import.meta.env.VITE_NOTIFICATION_SERVICE_URL || 'http://localhost:8084'
      const response = await fetch(`${notificationServiceUrl}/notifications?user_id=${userId}&limit=50`)

      if (response.ok) {
        const data = await response.json()
        // Sort by created_at DESC (latest first)
        const sortedNotifications = (data.notifications || []).sort((a, b) => {
          return new Date(b.created_at) - new Date(a.created_at)
        })
        notifications.value = sortedNotifications
        console.log('Fetched notifications from notification service:', sortedNotifications.length, 'notifications')
      } else {
        console.error('Failed to fetch notifications:', response.status)
        // Fallback to task service
        try {
          const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
          const fallbackResponse = await fetch(`${taskServiceUrl}/notifications/debug/${userId}`)
          if (fallbackResponse.ok) {
            const fallbackData = await fallbackResponse.json()
            const sortedNotifications = (fallbackData.notifications || []).sort((a, b) => {
              return new Date(b.created_at) - new Date(a.created_at)
            })
            notifications.value = sortedNotifications
            console.log('Fetched notifications from task service (fallback):', sortedNotifications.length)
          }
        } catch (fallbackError) {
          console.error('Fallback fetch also failed:', fallbackError)
          notifications.value = []
        }
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
      notifications.value = []
    } finally {
      isLoading.value = false
    }
  }

  const markAsRead = async (notificationId, userId) => {
    try {
      // Try to mark as read via notification service first (if available)
      const notificationServiceUrl = 'http://localhost:8084'
      const response = await fetch(`${notificationServiceUrl}/notifications/${notificationId}/read`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      })

      if (response.ok) {
        // Update local state
        const notification = notifications.value.find(n => n.id === notificationId)
        if (notification) {
          notification.is_read = true
        }
        console.log('Marked notification as read via notification service')
      } else {
        // Fallback: update directly in database via task service
        // Note: You might need to add this endpoint to your task service
        console.log('Failed to mark as read via notification service, trying direct database update')
        
        // For now, just update local state
        const notification = notifications.value.find(n => n.id === notificationId)
        if (notification) {
          notification.is_read = true
        }
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
      
      // Fallback: update local state anyway
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.is_read = true
      }
    }
  }

  const markAllAsRead = async (userId) => {
    try {
      // Try notification service first
      const notificationServiceUrl = 'http://localhost:8084'
      const response = await fetch(`${notificationServiceUrl}/notifications/mark-all-read`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      })

      if (response.ok) {
        // Update local state
        notifications.value.forEach(n => n.is_read = true)
        console.log('Marked all notifications as read via notification service')
      } else {
        console.log('Failed to mark all as read via notification service')
        
        // Fallback: update local state
        notifications.value.forEach(n => n.is_read = true)
      }
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error)
      
      // Fallback: update local state
      notifications.value.forEach(n => n.is_read = true)
    }
  }

  const addNotification = (notification) => {
    // Add new notification to the beginning and re-sort to ensure correct order
    notifications.value.unshift(notification)
    notifications.value.sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at)
    })
    console.log('Added new notification:', notification.title, 'Total:', notifications.value.length)
  }

  // Method to refresh notifications (useful for testing)
  const refreshNotifications = async (userId) => {
    await fetchNotifications(userId)
  }

  return {
    notifications,
    isLoading,
    unreadCount,
    recentNotifications,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    addNotification,
    refreshNotifications
  }
})