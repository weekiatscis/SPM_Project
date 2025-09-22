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
            />
            <div v-if="errors.dueDate" class="mt-1 text-sm text-red-600">
              {{ errors.dueDate }}
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
import { ref, watch } from 'vue'

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
    const form = ref({
      title: '',
      description: '',
      dueDate: '',
      status: 'Unassigned',
      priority: 'Medium'
    })

    const errors = ref({
      title: '',
      dueDate: ''
    })

    const isLoading = ref(false)

    // Watch for task changes to populate form
    watch(() => props.task, (newTask) => {
      if (newTask) {
        form.value = {
          ...newTask,
          dueDate: newTask.dueDate ? new Date(newTask.dueDate).toISOString().split('T')[0] : ''
        }
      } else {
        // Reset form for new task
        form.value = {
          title: '',
          description: '',
          dueDate: '',
          status: 'Unassigned',
          priority: 'Medium'
        }
        // Reset errors
        errors.value = {
          title: '',
          dueDate: ''
        }
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
            priority: form.value.priority
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
          owner_id: import.meta.env.VITE_TASK_OWNER_ID
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
          priority: 'Medium'
        }
        
        // Reset errors
        errors.value = {
          title: '',
          dueDate: ''
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
      saveTask
    }
  }
}
</script>
