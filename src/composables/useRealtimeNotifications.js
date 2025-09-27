import { ref, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { useNotificationStore } from '../stores/notifications'
import { useAuthStore } from '../stores/auth'

export function useRealtimeNotifications() {
  const socket = ref(null)
  const isConnected = ref(false)
  const notificationStore = useNotificationStore()
  const authStore = useAuthStore()

  const connect = () => {
    if (!authStore.user?.user_id) return

    // Connect to notification service
    socket.value = io('http://localhost:8084', {
      transports: ['websocket', 'polling']
    })

    socket.value.on('connect', () => {
      isConnected.value = true
      console.log('Connected to notification service')
      
      // Join user's notification room
      socket.value.emit('join_notifications', {
        user_id: authStore.user.user_id
      })
    })

    socket.value.on('disconnect', () => {
      isConnected.value = false
      console.log('Disconnected from notification service')
    })

    socket.value.on('new_notification', (notification) => {
      console.log('Received new notification:', notification)
      
      // Add to store
      notificationStore.addNotification(notification)
      
      // Show browser notification if permission granted
      if (Notification.permission === 'granted') {
        const browserNotification = new Notification(notification.title, {
          body: notification.message,
          icon: '/icons/task.png',
          badge: '/icons/task.png',
          tag: notification.id
        })

        // Auto-close after 5 seconds
        setTimeout(() => {
          browserNotification.close()
        }, 5000)

        // Handle click to focus window
        browserNotification.onclick = () => {
          window.focus()
          browserNotification.close()
        }
      }
    })

    socket.value.on('connect_error', (error) => {
      console.error('Socket connection error:', error)
    })
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
      isConnected.value = false
    }
  }

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      if (Notification.permission === 'default') {
        const permission = await Notification.requestPermission()
        return permission === 'granted'
      }
      return Notification.permission === 'granted'
    }
    return false
  }

  return {
    socket,
    isConnected,
    connect,
    disconnect,
    requestNotificationPermission
  }
}