<template>
  <transition name="slide-panel">
    <div v-if="isNotificationPanelOpen" class="notification-panel-overlay">
      <div class="notification-panel">
        <!-- Panel Header -->
        <div class="panel-header">
          <div class="header-left">
            <button
              @click="refreshNotifications"
              :disabled="isRefreshing"
              class="refresh-button"
              title="Refresh notifications"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                :class="{ 'spinning': isRefreshing }"
              >
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
              </svg>
            </button>
            <div class="header-title">
              <h3>Notifications</h3>
              <span class="notification-count">{{ unreadCount || 0 }} unread</span>
            </div>
          </div>
          <button @click="closePanel" class="close-button" title="Close panel">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <!-- Action Buttons -->
        <div class="panel-actions">
          <a-button
            v-if="unreadCount > 0"
            type="text"
            size="small"
            @click="markAllAsRead"
            :loading="isMarkingAllRead"
            class="action-btn mark-read-btn"
          >
            Mark all read
          </a-button>
        </div>

        <!-- Notifications List -->
        <div class="notifications-list-container">
          <a-spin :spinning="isLoading">
            <div v-if="displayedNotifications?.length === 0" class="empty-state">
              <div class="empty-icon">
                <img src="/Notificationgif.gif" alt="No notifications" class="notification-empty-gif" />
              </div>
              <p v-if="!showAllNotifications">No unread notifications</p>
              <p v-else>No notifications</p>
              <a-button type="link" size="small" @click="refreshNotifications">
                Click to refresh
              </a-button>
            </div>

            <div
              v-for="notification in displayedNotifications"
              :key="notification.id"
              class="notification-item"
              :class="{ 'unread': !notification.is_read }"
            >
              <div class="notification-content">
                <div class="notification-item-header">
                  <div class="notification-title">
                    {{ notification.title }}
                  </div>
                  <span
                    v-if="notification.priority"
                    class="priority-badge"
                    :class="`priority-${notification.priority?.toLowerCase()}`"
                  >
                    {{ notification.priority }}
                  </span>
                </div>
                <div class="notification-message">
                  {{ notification.message }}
                </div>
                <div class="notification-footer-content">
                  <div class="notification-time">
                    {{ formatNotificationTime(notification.created_at) }}
                  </div>
                  <div class="notification-actions">
                    <button
                      v-if="notification.task_id"
                      @click="handleViewTask(notification)"
                      class="view-task-btn"
                    >
                      View Task →
                    </button>
                    <button
                      v-if="notification.project_id"
                      @click="handleViewProject(notification)"
                      class="view-project-btn"
                    >
                      View Project →
                    </button>
                  </div>
                </div>
              </div>
              <div v-if="!notification.is_read" class="unread-indicator"></div>
            </div>
          </a-spin>
        </div>

        <!-- Panel Footer -->
        <div class="panel-footer">
          <a-button type="text" size="small" @click="toggleNotificationView" block>
            {{ showAllNotifications ? 'View unread notifications' : 'View all notifications' }}
          </a-button>
        </div>
      </div>
    </div>
  </transition>

  <!-- Task Detail Modal -->
  <TaskDetailModal
    v-if="selectedTask"
    :task="selectedTask"
    :isOpen="isTaskDetailModalOpen"
    @close="closeTaskDetailModal"
    @edit="handleEditTask"
  />
</template>

<script>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '../../stores/notifications'
import { useAuthStore } from '../../stores/auth'
import { useRealtimeNotifications } from '../../composables/useRealtimeNotifications'
import { useNotificationPanel } from '../../composables/useNotificationPanel'
import { BellIcon } from '../icons/index.js'
import TaskDetailModal from '../tasks/TaskDetailModal.vue'

export default {
  name: 'NotificationPanel',
  components: {
    BellIcon,
    TaskDetailModal
  },
  setup() {
    const router = useRouter()
    const notificationStore = useNotificationStore()
    const authStore = useAuthStore()
    const { connect, disconnect, requestNotificationPermission } = useRealtimeNotifications()
    const { isNotificationPanelOpen, closePanel } = useNotificationPanel()

    const isMarkingAllRead = ref(false)
    const isRefreshing = ref(false)
    const isTaskDetailModalOpen = ref(false)
    const selectedTask = ref(null)
    const isLoadingTask = ref(false)
    const showAllNotifications = ref(false) // Toggle between unread-only and all notifications

    const user = computed(() => authStore.user)

    // Use storeToRefs to maintain reactivity when destructuring
    const {
      notifications,
      isLoading,
      unreadCount,
      recentNotifications
    } = storeToRefs(notificationStore)

    // Actions don't need storeToRefs
    const {
      fetchNotifications,
      markAsRead,
      markAllAsRead: storeMarkAllAsRead,
      refreshNotifications: storeRefreshNotifications
    } = notificationStore

    // Debug the store values
    console.log('NotificationPanel setup complete:', {
      notificationsValue: notifications.value,
      notificationsLength: notifications.value?.length,
      unreadCountValue: unreadCount.value,
      recentNotificationsValue: recentNotifications.value,
      recentNotificationsLength: recentNotifications.value?.length
    })

    const hasUnread = computed(() => unreadCount.value > 0)

    // Filtered notifications based on toggle state
    const displayedNotifications = computed(() => {
      if (showAllNotifications.value) {
        // Show all notifications (max 50 from backend)
        return notifications.value
      } else {
        // Show only unread notifications
        return recentNotifications.value.filter(notif => !notif.is_read)
      }
    })

    // Debug watchers
    watch(notifications, (newNotifications) => {
      console.log('Notifications changed:', newNotifications.length, newNotifications)
    }, { immediate: true })

    watch(unreadCount, (newCount) => {
      console.log('Unread count changed:', newCount)
    }, { immediate: true })

    watch(recentNotifications, (newRecent) => {
      console.log('Recent notifications changed:', newRecent.length, newRecent)
    }, { immediate: true })

    const formatNotificationTime = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = now.getTime() - date.getTime()
      const diffMinutes = Math.floor(diffTime / (1000 * 60))
      const diffHours = Math.floor(diffTime / (1000 * 60 * 60))
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

      if (diffMinutes < 1) return 'Just now'
      if (diffMinutes < 60) return `${diffMinutes}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`

      return date.toLocaleDateString()
    }

    const handleNotificationClick = async (notification) => {
      console.log('Notification clicked:', notification)

      // Mark as read if unread
      if (!notification.is_read && user.value?.user_id) {
        await markAsRead(notification.id, user.value.user_id)
      }
    }

    const handleViewTask = async (notification) => {
      console.log('View task clicked:', notification.task_id)

      // Mark as read if unread
      if (!notification.is_read && user.value?.user_id) {
        await markAsRead(notification.id, user.value.user_id)
      }

      // Fetch task details and open modal
      isLoadingTask.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${notification.task_id}`)

        if (response.ok) {
          const data = await response.json()
          selectedTask.value = data.task
          isTaskDetailModalOpen.value = true
          console.log('Task details loaded:', data.task)
        } else {
          console.error('Failed to fetch task details')
          alert('Failed to load task details')
        }
      } catch (error) {
        console.error('Error fetching task:', error)
        alert('Error loading task details')
      } finally {
        isLoadingTask.value = false
      }
    }

    const handleViewProject = async (notification) => {
      console.log('View project clicked:', notification.project_id)

      // Mark as read if unread
      if (!notification.is_read && user.value?.user_id) {
        await markAsRead(notification.id, user.value.user_id)
      }

      // Navigate to project details page
      try {
        router.push(`/projects/${notification.project_id}`)
        // Close panel after navigation
        closePanel()
        console.log('Navigating to project:', notification.project_id)
      } catch (error) {
        console.error('Error navigating to project:', error)
        alert('Error navigating to project')
      }
    }

    const closeTaskDetailModal = () => {
      isTaskDetailModalOpen.value = false
      selectedTask.value = null
    }

    const handleEditTask = (task) => {
      console.log('Edit task requested:', task)
      // Close the detail modal
      closeTaskDetailModal()
      // Dispatch custom event for parent to handle
      window.dispatchEvent(new CustomEvent('open-task-edit', { detail: task }))
    }

    const markAllAsRead = async () => {
      if (!user.value?.user_id) return

      isMarkingAllRead.value = true
      try {
        await storeMarkAllAsRead(user.value.user_id)
      } finally {
        isMarkingAllRead.value = false
      }
    }

    const refreshNotifications = async () => {
      const userId = user.value?.user_id || authStore.user?.user_id

      if (!userId) {
        console.error('Cannot refresh notifications: user_id is undefined')
        console.log('Auth store user:', authStore.user)
        console.log('Computed user:', user.value)
        return
      }

      console.log('Refreshing notifications for user:', userId)
      isRefreshing.value = true
      try {
        await storeRefreshNotifications(userId)
        console.log('Notifications refreshed! Store state:', {
          total: notifications.value?.length || 0,
          unread: unreadCount.value || 0,
          recent: recentNotifications.value?.length || 0,
          notificationsValue: notifications.value
        })
      } catch (error) {
        console.error('Failed to refresh notifications:', error)
      } finally {
        isRefreshing.value = false
      }
    }

    const toggleNotificationView = () => {
      showAllNotifications.value = !showAllNotifications.value
    }

    // Watch for panel opening and refresh notifications
    watch(isNotificationPanelOpen, async (isOpen) => {
      if (isOpen) {
        const userId = user.value?.user_id || authStore.user?.user_id
        if (userId) {
          console.log('Notification panel opened, refreshing notifications...')
          await refreshNotifications()
        }
      }
    })

    // Initialize notifications
    onMounted(async () => {
      console.log('NotificationPanel mounted, user:', user.value)
      const userId = user.value?.user_id || authStore.user?.user_id
      if (userId) {
        await requestNotificationPermission()
        await fetchNotifications(userId)
        connect()
      }
    })

    onUnmounted(() => {
      disconnect()
    })

    return {
      isNotificationPanelOpen,
      notifications,
      isLoading,
      unreadCount,
      recentNotifications,
      displayedNotifications,
      showAllNotifications,
      hasUnread,
      isMarkingAllRead,
      isRefreshing,
      isTaskDetailModalOpen,
      selectedTask,
      isLoadingTask,
      closePanel,
      formatNotificationTime,
      handleNotificationClick,
      handleViewTask,
      handleViewProject,
      closeTaskDetailModal,
      handleEditTask,
      markAllAsRead,
      refreshNotifications,
      toggleNotificationView
    }
  }
}
</script>

<style scoped>
/* Panel Overlay - covers the right side below topbar */
.notification-panel-overlay {
  position: fixed;
  top: 64px;
  right: 0;
  bottom: 0;
  width: 420px;
  z-index: 1000;
  pointer-events: all;
}

/* Panel Container */
.notification-panel {
  width: 100%;
  height: 100%;
  background: white;
  box-shadow: -8px 0 16px -4px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  border-left: 1px solid #e5e7eb;
  border-top: none;
}

/* Panel Header */
.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  color: #3b82f6;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.refresh-button:hover {
  background-color: #dbeafe;
  color: #2563eb;
}

.refresh-button:active {
  transform: scale(0.95);
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-button svg.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.header-title h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.notification-count {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  color: #6b7280;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  background-color: #f3f4f6;
  color: #111827;
}

.close-button:active {
  transform: scale(0.95);
}

/* Action Buttons */
.panel-actions {
  padding: 12px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  background: #fafbfc;
}

.action-btn {
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f3f4f6;
  color: #1890ff;
}

.mark-read-btn {
  margin-left: auto;
}

/* Notifications List Container */
.notifications-list-container {
  flex: 1;
  overflow-y: auto;
  background: #f9fafb;
  padding: 4px 0;
}

/* Custom Scrollbar */
.notifications-list-container::-webkit-scrollbar {
  width: 6px;
}

.notifications-list-container::-webkit-scrollbar-track {
  background: #f9fafb;
}

.notifications-list-container::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.notifications-list-container::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Empty State */
.empty-state {
  padding: 60px 24px;
  text-align: center;
  color: #6b7280;
}

.empty-icon {
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.notification-empty-gif {
  width: 120px;
  height: 120px;
  object-fit: contain;
  opacity: 0.7;
}

.empty-state p {
  margin: 8px 0;
  font-size: 14px;
  font-weight: 500;
}

.empty-subtext {
  font-size: 12px;
  color: #9ca3af;
}

/* Notification Item */
.notification-item {
  padding: 14px 16px;
  margin: 8px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
  background: white;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.notification-item:hover {
  background-color: #f9fafb;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.notification-item.unread {
  background-color: #f0f9ff;
  border-left: 4px solid #1890ff;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
}

.notification-item.unread:hover {
  background-color: #e6f4ff;
  box-shadow: 0 3px 8px rgba(24, 144, 255, 0.15);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  color: #111827;
  line-height: 1.4;
}

.notification-message {
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 8px;
  line-height: 1.5;
}

.notification-footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.notification-time {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

.notification-actions {
  display: flex;
  gap: 8px;
}

.unread-indicator {
  width: 8px;
  height: 8px;
  background-color: #1890ff;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

/* Priority Badges */
.priority-badge {
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  flex-shrink: 0;
}

.priority-high {
  background-color: #fee2e2;
  color: #dc2626;
}

.priority-medium {
  background-color: #fef3c7;
  color: #d97706;
}

.priority-low {
  background-color: #dcfce7;
  color: #16a34a;
}

.priority-lowest {
  background-color: #dbeafe;
  color: #2563eb;
}

/* View Task/Project Buttons */
.view-task-btn,
.view-project-btn {
  background: none;
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  white-space: nowrap;
}

.view-task-btn {
  color: #1890ff;
}

.view-task-btn:hover {
  background-color: #e6f7ff;
  color: #0958d9;
}

.view-project-btn {
  color: #10b981;
}

.view-project-btn:hover {
  background-color: #d1fae5;
  color: #059669;
}

.view-task-btn:active,
.view-project-btn:active {
  transform: scale(0.95);
}

/* Panel Footer */
.panel-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #fafbfc;
  flex-shrink: 0;
}

.panel-footer :deep(.ant-btn) {
  font-size: 13px;
  font-weight: 600;
  color: #1890ff;
}

.panel-footer :deep(.ant-btn:hover) {
  color: #0958d9;
  background: #f0f9ff;
}

/* Slide Panel Animation */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateX(100%);
}

.slide-panel-enter-to,
.slide-panel-leave-from {
  transform: translateX(0);
}

/* Responsive */
@media (max-width: 768px) {
  .notification-panel-overlay {
    width: 100%;
  }
}

/* Dark Mode Support */
:global(.dark) .notification-panel {
  background: #1f2937;
  border-left-color: #374151;
}

:global(.dark) .panel-header {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  border-bottom-color: #374151;
}

:global(.dark) .header-title h3 {
  color: #f9fafb;
}

:global(.dark) .notification-count {
  color: #9ca3af;
}

:global(.dark) .close-button {
  color: #9ca3af;
}

:global(.dark) .close-button:hover {
  background-color: #374151;
  color: #f9fafb;
}

:global(.dark) .panel-actions {
  background: #111827;
  border-bottom-color: #374151;
}

:global(.dark) .notifications-list-container {
  background: #1f2937;
}

:global(.dark) .notification-item {
  border-bottom-color: #374151;
}

:global(.dark) .notification-item:hover {
  background-color: #374151;
}

:global(.dark) .notification-item.unread {
  background-color: #1e3a5f;
  border-left-color: #60a5fa;
}

:global(.dark) .notification-title {
  color: #f9fafb;
}

:global(.dark) .notification-message {
  color: #d1d5db;
}

:global(.dark) .notification-time {
  color: #6b7280;
}

:global(.dark) .unread-indicator {
  background-color: #60a5fa;
}

:global(.dark) .panel-footer {
  background: #111827;
  border-top-color: #374151;
}
</style>
