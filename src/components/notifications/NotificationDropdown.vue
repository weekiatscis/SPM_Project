<template>
  <div>
    <a-dropdown
      :trigger="['click']"
      placement="bottomRight"
      :overlay-style="{ width: '350px', maxHeight: '400px' }"
    >
      <!-- Bell Icon with Badge -->
      <a-badge :count="unreadCount" size="small" :offset="[-2, 2]">
        <a-button
          type="text"
          shape="circle"
          size="large"
          :style="{ position: 'relative' }"
        >
          <template #icon>
            <BellIcon :class="{ 'animate-pulse': hasUnread }" />
          </template>
        </a-button>
      </a-badge>
  
      <!-- Dropdown Content -->
      <template #overlay>
        <div class="notification-dropdown">
          <!-- Header -->
          <div class="notification-header">
            <div class="header-title">
              <h4>Notifications</h4>
              <span class="notification-count">{{ unreadCount || 0 }} unread (Total: {{ notifications?.length || 0 }})</span>
            </div>
            <div class="header-actions">
              <a-button 
                type="text" 
                size="small"
                @click="refreshNotifications"
                :loading="isRefreshing"
                style="margin-right: 8px;"
              >
                🔄 Refresh
              </a-button>
              <a-button 
                v-if="unreadCount > 0"
                type="text" 
                size="small"
                @click="markAllAsRead"
                :loading="isMarkingAllRead"
              >
                Mark all read
              </a-button>
            </div>
          </div>
  
          <!-- Debug Info -->
          <div style="padding: 8px; background: #f0f0f0; font-size: 11px; border-bottom: 1px solid #ccc;">
            <div>Total notifications: {{ notifications?.length || 0 }}</div>
            <div>Recent notifications: {{ recentNotifications?.length || 0 }}</div>
            <div>Unread count: {{ unreadCount || 0 }}</div>
            <div>Has unread: {{ hasUnread }}</div>
            <div>Is loading: {{ isLoading }}</div>
          </div>
  
          <!-- Notifications List -->
          <div class="notification-list">
            <a-spin :spinning="isLoading">
              <div v-if="recentNotifications?.length === 0" class="empty-state">
                <div class="empty-icon">
                  <BellIcon size="lg" color="gray" />
                </div>
                <p>No recent notifications (but {{ notifications?.length || 0 }} total found)</p>
                <a-button type="link" size="small" @click="refreshNotifications">
                  Click to refresh
                </a-button>
              </div>
  
              <div
                v-for="notification in recentNotifications"
                :key="notification.id"
                class="notification-item"
                :class="{ 'unread': !notification.is_read }"
              >
                <div class="notification-content">
                  <div class="notification-header">
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
                <div v-if="!notification.is_read" class="unread-indicator"></div>
              </div>
            </a-spin>
          </div>
  
          <!-- Footer -->
          <div class="notification-footer">
            <a-button type="text" size="small" @click="viewAllNotifications">
              View all notifications
            </a-button>
          </div>
        </div>
      </template>
    </a-dropdown>

    <!-- Task Detail Modal -->
    <TaskDetailModal
      :task="selectedTask"
      :isOpen="isTaskDetailModalOpen"
      @close="closeTaskDetailModal"
      @edit="handleEditTask"
    />
  </div>
</template>
  
  <script>
  import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
  import { storeToRefs } from 'pinia'
  import { useRouter } from 'vue-router'
  import { useNotificationStore } from '../../stores/notifications'
  import { useAuthStore } from '../../stores/auth'
  import { useRealtimeNotifications } from '../../composables/useRealtimeNotifications'
  import { BellIcon } from '../icons/index.js'
  import TaskDetailModal from '../tasks/TaskDetailModal.vue'

  export default {
    name: 'NotificationDropdown',
    components: {
      BellIcon,
      TaskDetailModal
    },
    setup() {
      const router = useRouter()
      const notificationStore = useNotificationStore()
      const authStore = useAuthStore()
      const { connect, disconnect, requestNotificationPermission } = useRealtimeNotifications()
      
      const isMarkingAllRead = ref(false)
      const isRefreshing = ref(false)
      const isTaskDetailModalOpen = ref(false)
      const selectedTask = ref(null)
      const isLoadingTask = ref(false)

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
      console.log('Store setup complete:', {
        notificationsValue: notifications.value,
        notificationsLength: notifications.value?.length,
        unreadCountValue: unreadCount.value,
        recentNotificationsValue: recentNotifications.value,
        recentNotificationsLength: recentNotifications.value?.length
      })
  
      const hasUnread = computed(() => unreadCount.value > 0)

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
          router.push(`/projects?projectId=${notification.project_id}`)
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
        // Emit event to parent or open edit modal
        // You can either:
        // 1. Navigate to edit page
        // 2. Open TaskFormModal in edit mode
        // 3. Emit to parent component

        // For now, let's emit to parent so it can handle the edit
        // The parent component (Home or wherever NotificationDropdown is used)
        // should have a TaskFormModal and open it in edit mode

        // Since we're in a dropdown, let's dispatch a custom event
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
        if (!user.value?.user_id) return
        
        console.log('Refreshing notifications for user:', user.value.user_id)
        isRefreshing.value = true
        try {
          await storeRefreshNotifications(user.value.user_id)
          console.log('Notifications refreshed! Store state:', {
            total: notifications.value?.length || 0,
            unread: unreadCount.value || 0,
            recent: recentNotifications.value?.length || 0,
            notificationsValue: notifications.value
          })
        } finally {
          isRefreshing.value = false
        }
      }
  
      const viewAllNotifications = () => {
        console.log('Navigate to all notifications')
      }
  
      // Initialize notifications
      onMounted(async () => {
        console.log('NotificationDropdown mounted, user:', user.value)
        if (user.value?.user_id) {
          await requestNotificationPermission()
          await fetchNotifications(user.value.user_id)
          connect()
        }
      })
  
      onUnmounted(() => {
        disconnect()
      })
  
      return {
        notifications,
        isLoading,
        unreadCount,
        recentNotifications,
        hasUnread,
        isMarkingAllRead,
        isRefreshing,
        isTaskDetailModalOpen,
        selectedTask,
        isLoadingTask,
        formatNotificationTime,
        handleNotificationClick,
        handleViewTask,
        handleViewProject,
        closeTaskDetailModal,
        handleEditTask,
        markAllAsRead,
        refreshNotifications,
        viewAllNotifications
      }
    }
  }
  </script>
  
  <style scoped>
  .notification-dropdown {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }
  
  .notification-header {
    padding: 16px;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .header-title h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
  
  .notification-count {
    font-size: 12px;
    color: #8c8c8c;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
  }
  
  .notification-list {
    max-height: 300px;
    overflow-y: auto;
  }
  
  .notification-item {
    padding: 12px 16px;
    border-bottom: 1px solid #f5f5f5;
    cursor: pointer;
    position: relative;
    display: flex;
    align-items: flex-start;
    gap: 8px;
    transition: background-color 0.2s;
  }
  
  .notification-item:hover {
    background-color: #f9f9f9;
  }
  
  .notification-item.unread {
    background-color: #f6ffed;
  }
  
  .notification-item:last-child {
    border-bottom: none;
  }
  
  .notification-content {
    flex: 1;
  }
  
  .notification-title {
    font-weight: 500;
    font-size: 14px;
    margin-bottom: 4px;
    color: #262626;
  }
  
  .notification-message {
    font-size: 13px;
    color: #595959;
    margin-bottom: 4px;
    line-height: 1.4;
  }
  
  .notification-time {
    font-size: 11px;
    color: #8c8c8c;
  }
  
  .unread-indicator {
    width: 8px;
    height: 8px;
    background-color: #1890ff;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
  }
  
  .notification-footer {
    padding: 8px 16px;
    border-top: 1px solid #f0f0f0;
    text-align: center;
  }
  
  .empty-state {
    padding: 40px 20px;
    text-align: center;
    color: #8c8c8c;
  }
  
  .empty-icon {
    margin-bottom: 12px;
    opacity: 0.5;
  }
  
  /* Custom scrollbar */
  .notification-list::-webkit-scrollbar {
    width: 4px;
  }
  
  .notification-list::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  .notification-list::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 2px;
  }
  
  .notification-list::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
  }

  /* Notification header with priority */
  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }

  /* Priority badges */
  .priority-badge {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .priority-high {
    background-color: #fff2f0;
    color: #cf1322;
  }

  .priority-medium {
    background-color: #fff7e6;
    color: #d46b08;
  }

  .priority-low {
    background-color: #f6ffed;
    color: #389e0d;
  }

  .priority-lowest {
    background-color: #f0f5ff;
    color: #1d39c4;
  }

  /* Notification footer with time and button */
  .notification-footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
  }

  /* View Task button */
  .view-task-btn {
    background: none;
    border: none;
    color: #1890ff;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .view-task-btn:hover {
    background-color: #e6f7ff;
    color: #096dd9;
  }

  .view-task-btn:active {
    transform: scale(0.95);
  }

  .view-project-btn {
    background: none;
    border: none;
    color: #52c41a;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .view-project-btn:hover {
    background-color: #f6ffed;
    color: #389e0d;
  }

  .view-project-btn:active {
    transform: scale(0.95);
  }
  </style>