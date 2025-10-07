<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal panel -->
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
        <!-- Header -->
        <div class="bg-white px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900">
              {{ task?.id ? 'Edit Task' : 'Add New Task' }}
            </h3>
            <button
              @click="$emit('close')"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="saveTask" class="bg-white px-6 py-4 space-y-4">
          <!-- Title -->
          <div>
            <label for="title" class="block text-sm font-medium text-gray-700 mb-1">
              Title *
            </label>
            <input
              id="title"
              v-model="form.title"
              type="text"
              required
              class="input-field"
              :class="{ 'border-red-500': errors.title }"
              placeholder="Enter task title"
            />
            <div v-if="errors.title" class="mt-1 text-sm text-red-600">
              {{ errors.title }}
            </div>
          </div>

          <!-- Description -->
          <div>
            <label for="description" class="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              v-model="form.description"
              rows="3"
              class="input-field"
              placeholder="Enter task description"
            ></textarea>
          </div>

          <!-- Due Date -->
          <div>
            <label for="dueDate" class="block text-sm font-medium text-gray-700 mb-1">
              Due Date *
            </label>
            <input
              id="dueDate"
              v-model="form.dueDate"
              type="date"
              required
              class="input-field"
              :class="{ 'border-red-500': errors.dueDate }"
              :min="minDate"
            />
            <div v-if="errors.dueDate" class="mt-1 text-sm text-red-600">
              {{ errors.dueDate }}
            </div>
            <div v-if="daysUntilDue !== null" class="mt-1 text-sm" :class="dueDateColorClass">
              {{ dueDateMessage }}
            </div>
          </div>

          <!-- Status -->
          <div>
            <label for="status" class="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              id="status"
              v-model="form.status"
              class="input-field"
            >
              <option value="Unassigned">Unassigned</option>
              <option value="Ongoing">Ongoing</option>
              <option value="Under Review">Under Review</option>
              <option value="Completed">Completed</option>
            </select>
          </div>

          <!-- Priority -->
          <div>
            <label for="priority" class="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              id="priority"
              v-model="form.priority"
              class="input-field"
            >
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
              <option value="Lowest">Lowest</option>
            </select>
          </div>

          <!-- Reminder Customization -->
          <div v-if="form.dueDate" class="border-t pt-4 mt-4">
            <div class="flex items-center justify-between mb-2">
              <label class="block text-sm font-medium text-gray-700">
                Reminder Schedule
              </label>
              <button
                type="button"
                @click="toggleReminderCustomization"
                class="text-sm text-blue-600 hover:text-blue-800"
              >
                {{ showReminderCustomization ? 'Use Default' : 'Customize' }}
              </button>
            </div>

            <div v-if="!showReminderCustomization" class="text-sm text-gray-600">
              You'll be reminded 7, 3, and 1 day(s) before the due date
            </div>

            <div v-else class="space-y-3">
              <div class="text-sm text-gray-600 mb-2">
                Select when you want to receive reminders (up to 5, max 10 days before):
              </div>

              <div class="grid grid-cols-5 gap-2">
                <button
                  v-for="day in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
                  :key="day"
                  type="button"
                  @click="toggleReminderDay(day)"
                  :disabled="!canAddMoreReminders && !form.reminderDays.includes(day)"
                  class="px-3 py-2 text-sm rounded border transition-colors"
                  :class="form.reminderDays.includes(day)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed'"
                >
                  {{ day }}d
                </button>
              </div>

              <div class="text-xs text-gray-500">
                Selected: {{ form.reminderDays.length > 0 ? form.reminderDays.sort((a, b) => b - a).join(', ') + ' day(s) before' : 'None' }}
              </div>

              <div v-if="form.reminderDays.length === 0" class="text-xs text-red-600">
                ⚠️ No reminders selected. You won't receive any notifications.
              </div>
            </div>
          </div>
        </form>

        <!-- Footer -->
        <div class="bg-gray-50 px-6 py-3 flex justify-end space-x-3">
          <button
            type="button"
            @click="$emit('close')"
            class="btn-secondary"
          >
            Cancel
          </button>
          <button
            @click="saveTask"
            :disabled="isLoading"
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLoading ? 'Creating...' : (task?.id ? 'Update Task' : 'Create Task') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useNotificationStore } from '../../stores/notifications'

export default {
  name: 'TaskFormModal',
  props: {
    task: {
      type: Object,
      default: null
    },
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    const notificationStore = useNotificationStore()
    const form = ref({
      title: '',
      description: '',
      dueDate: '',
      status: 'Unassigned',
      priority: 'Medium',
      reminderDays: [7, 3, 1]  // Default reminder days
    })

    const errors = ref({
      title: '',
      dueDate: ''
    })

    const isLoading = ref(false)
    const showReminderCustomization = ref(false)
    
    const minDate = computed(() => {
      return new Date().toISOString().split('T')[0]
    })

    const daysUntilDue = computed(() => {
      if (!form.value.dueDate) return null
      
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const dueDate = new Date(form.value.dueDate)
      dueDate.setHours(0, 0, 0, 0)
      
      return Math.ceil((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
    })

    const dueDateMessage = computed(() => {
      if (daysUntilDue.value === null) return ''
      
      if (daysUntilDue.value === 0) return 'Due today'
      if (daysUntilDue.value === 1) return 'Due tomorrow'
      if (daysUntilDue.value <= 7) return `Due in ${daysUntilDue.value} days (you'll get reminders)`
      return `Due in ${daysUntilDue.value} days`
    })

    const dueDateColorClass = computed(() => {
      if (daysUntilDue.value === null) return 'text-gray-600'

      if (daysUntilDue.value <= 1) return 'text-red-600'
      if (daysUntilDue.value <= 3) return 'text-orange-600'
      if (daysUntilDue.value <= 7) return 'text-yellow-600'
      return 'text-green-600'
    })

    const canAddMoreReminders = computed(() => {
      return form.value.reminderDays.length < 5
    })

    const toggleReminderCustomization = () => {
      showReminderCustomization.value = !showReminderCustomization.value
      if (!showReminderCustomization.value) {
        // Reset to default when switching back
        form.value.reminderDays = [7, 3, 1]
      }
    }

    const toggleReminderDay = (day) => {
      const index = form.value.reminderDays.indexOf(day)
      if (index > -1) {
        // Remove the day
        form.value.reminderDays.splice(index, 1)
      } else {
        // Add the day if under limit
        if (form.value.reminderDays.length < 5) {
          form.value.reminderDays.push(day)
        }
      }
    }

    // Watch for task changes to populate form
    watch(() => props.task, (newTask) => {
      if (newTask) {
        form.value = {
          title: newTask.title || '',
          description: newTask.description || '',
          dueDate: newTask.dueDate ? new Date(newTask.dueDate).toISOString().split('T')[0] : '',
          status: newTask.status || 'Unassigned',
          priority: newTask.priority || 'Medium',
          reminderDays: newTask.reminderDays || [7, 3, 1]
        }
      } else {
        // Reset form for new task
        form.value = {
          title: '',
          description: '',
          dueDate: '',
          status: 'Unassigned',
          priority: 'Medium',
          reminderDays: [7, 3, 1]
        }
        // Reset errors
        errors.value = {
          title: '',
          dueDate: ''
        }
        showReminderCustomization.value = false
      }
    }, { immediate: true })

    const saveTask = async () => {
      // Reset errors
      errors.value = {
        title: '',
        dueDate: ''
      }

      // Validate required fields
      let hasErrors = false
      
      if (!form.value.title?.trim()) {
        errors.value.title = 'Title is required'
        hasErrors = true
      }
      
      if (!form.value.dueDate) {
        errors.value.dueDate = 'Due Date is required'
        hasErrors = true
      } else {
        // Check if due date is in the past
        const today = new Date()
        today.setHours(0, 0, 0, 0) // Reset time to start of day for comparison
        const selectedDate = new Date(form.value.dueDate)
        
        if (selectedDate < today) {
          errors.value.dueDate = 'Please select a valid due date'
          hasErrors = true
        }
      }

      if (hasErrors) {
        return
      }

      isLoading.value = true

      try {
        // If editing existing task, call update endpoint
        if (props.task?.id) {
          const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
          const updatePayload = {
            title: form.value.title,
            description: form.value.description,
            due_date: form.value.dueDate,
            status: form.value.status,
            priority: form.value.priority,
            reminder_days: form.value.reminderDays
          }

          const response = await fetch(`${taskServiceUrl}/tasks/${props.task.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatePayload)
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.error || `HTTP ${response.status}`)
          }

          const result = await response.json()

          // Refresh notifications after updating task (in case due date changed)
          if (authStore.user?.user_id) {
            await notificationStore.fetchNotifications(authStore.user.user_id)
            console.log('Notifications refreshed after task update')
          }

          // Emit success with the updated task data
          emit('save', result.task)
          console.log('Task updated successfully:', result.task)
          return
        }

        // For new task, call unified task service
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const payload = {
          title: form.value.title,
          description: form.value.description,
          due_date: form.value.dueDate,
          status: form.value.status,
          priority: form.value.priority,
          owner_id: authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID,
          reminder_days: form.value.reminderDays
        }

        const response = await fetch(`${taskServiceUrl}/tasks`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload)
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        const result = await response.json()
        
        // Reset form after successful creation
        form.value = {
          title: '',
          description: '',
          dueDate: '',
          status: 'Unassigned',
          priority: 'Medium',
          reminderDays: [7, 3, 1]
        }
        showReminderCustomization.value = false
        
        // Reset errors
        errors.value = {
          title: '',
          dueDate: ''
        }
        
        // Refresh notifications immediately after creating task
        if (authStore.user?.user_id) {
          // Wait a moment for backend to process notifications
          setTimeout(async () => {
            await notificationStore.fetchNotifications(authStore.user.user_id)
            console.log('Notifications refreshed after task creation')
          }, 500)
        }

        // Emit success with the created task data
        emit('save', result.task)

        // Show success message
        console.log('Task created successfully:', result.task)
        
      } catch (error) {
        console.error('Failed to create task:', error)
        alert(`Failed to create task: ${error.message}`)
      } finally {
        isLoading.value = false
      }
    }

    return {
      form,
      errors,
      isLoading,
      minDate,
      daysUntilDue,
      dueDateMessage,
      dueDateColorClass,
      showReminderCustomization,
      canAddMoreReminders,
      toggleReminderCustomization,
      toggleReminderDay,
      saveTask
    }
  }
}
</script>