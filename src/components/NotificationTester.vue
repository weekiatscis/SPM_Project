<template>
  <div style="padding: 20px; border: 1px solid #ccc; border-radius: 8px; margin: 20px; background-color: #f9f9f9;">
    <h3>🔧 Notification System Tester</h3>
    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
      <a-button 
        @click="testNotification"
        :loading="isLoading"
        type="primary"
      >
        Create Test Notification
      </a-button>
      
      <a-button 
        @click="checkNotifications"
        :loading="isLoading"
        type="default"
        style="background-color: #52c41a; border-color: #52c41a; color: white;"
      >
        Check My Notifications
      </a-button>
    </div>
    
    <div 
      v-if="result" 
      :style="{
        padding: '10px',
        backgroundColor: result.startsWith('✅') ? '#f6ffed' : '#fff2f0',
        border: `1px solid ${result.startsWith('✅') ? '#b7eb8f' : '#ffccc7'}`,
        borderRadius: '4px',
        fontSize: '14px'
      }"
    >
      {{ result }}
    </div>
    
    <div style="font-size: 12px; color: #666; margin-top: 10px;">
      💡 <strong>Instructions:</strong>
      <ol style="font-size: 12px; margin-top: 5px;">
        <li>Click "Create Test Notification" to create a test notification</li>
        <li>Click "Check My Notifications" to see all your notifications</li>
        <li>Check the browser console for detailed results</li>
        <li>Try clicking the bell icon to see if notifications appear</li>
      </ol>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'NotificationTester',
  setup() {
    const authStore = useAuthStore()
    const isLoading = ref(false)
    const result = ref('')

    const testNotification = async () => {
      isLoading.value = true
      result.value = ''
      
      try {
        const userId = authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID
        if (!userId) {
          result.value = '❌ Error: No user ID found. Please log in.'
          return
        }

        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        
        const response = await fetch(`${taskServiceUrl}/test-notifications/${userId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        })
        
        if (response.ok) {
          const data = await response.json()
          result.value = '✅ Test notification created successfully!'
          console.log('Test notification result:', data)
        } else {
          const error = await response.json()
          result.value = `❌ Failed: ${error.error}`
        }
      } catch (error) {
        result.value = `❌ Error: ${error.message}`
      } finally {
        isLoading.value = false
      }
    }

    const checkNotifications = async () => {
      isLoading.value = true
      result.value = ''
      
      try {
        const userId = authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID
        if (!userId) {
          result.value = '❌ Error: No user ID found. Please log in.'
          return
        }

        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        
        const response = await fetch(`${taskServiceUrl}/notifications/debug/${userId}`)
        
        if (response.ok) {
          const data = await response.json()
          result.value = `📊 Found ${data.total_notifications} notifications. Check console for details.`
          console.log('User notifications:', data)
        } else {
          const error = await response.json()
          result.value = `❌ Failed: ${error.error}`
        }
      } catch (error) {
        result.value = `❌ Error: ${error.message}`
      } finally {
        isLoading.value = false
      }
    }

    return {
      isLoading,
      result,
      testNotification,
      checkNotifications
    }
  }
}
</script>