<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal panel - widened -->
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
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

          <!-- Status and Priority in a single row -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Status -->
            <div>
              <label for="status" class="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                v-model="form.status"
                class="input-field w-full"
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
                class="input-field w-full"
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
                <option value="Lowest">Lowest</option>
              </select>
            </div>
          </div>

            <!-- Priority -->
            <div>
              <label for="priority" class="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                id="priority"
                v-model="form.priority"
                class="input-field w-full"
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
                <option value="Lowest">Lowest</option>
              </select>
            </div>
          </div>

          <!-- Owner -->
          <div>
            <label for="owner" class="block text-sm font-medium text-gray-700 mb-1">
              Owner
            </label>
            <select
              id="owner"
              v-model="form.owner_id"
              class="input-field"
              :disabled="isLoadingUsers"
            >
              <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select an owner' }}</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ user.name }}
              </option>
            </select>
            <div v-if="isLoadingUsers" class="mt-1 text-xs text-gray-500">Loading users from database...</div>
          </div>

          <!-- Collaborators / Invited Members -->
          <div>
            <label for="collaborators" class="block text-sm font-medium text-gray-700 mb-1">
              Collaborators / Invited Members
            </label>
            <select
              id="collaborators"
              v-model="form.collaborators"
              multiple
              class="input-field"
              :disabled="isLoadingUsers"
            >
              <option v-if="isLoadingUsers" value="" disabled>Loading users...</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ user.name }}
              </option>
            </select>
            <div class="mt-1 text-xs text-gray-500">
              {{ isLoadingUsers ? 'Loading users from database...' : 'Hold Ctrl/Cmd to select multiple' }}
            </div>
          </div>

          <!-- Parent Project / Group -->
          <div>
            <label for="project" class="block text-sm font-medium text-gray-700 mb-1">
              Parent Project / Group
            </label>
            <select
              id="project"
              v-model="form.project_id"
              class="input-field"
            >
              <option value="">No parent project</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.title }}
              </option>
            </select>
          </div>

          <!-- Subtasks -->
          <div>
            <div class="flex justify-between items-center">
              <label class="block text-sm font-medium text-gray-700">
                Subtasks
              </label>
              <button 
                type="button" 
                @click="addSubtask" 
                class="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                + Add subtask
              </button>
            </div>
            
            <div v-for="(subtask, index) in form.subtasks" :key="index" class="mt-2 flex items-center">
              <input
                v-model="subtask.title"
                type="text"
                class="input-field flex-grow"
                placeholder="Enter subtask"
              />
              <button 
                type="button" 
                @click="removeSubtask(index)" 
                class="ml-2 text-red-600 hover:text-red-800"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            <div v-if="form.subtasks.length === 0" class="mt-2 text-sm text-gray-500">
              No subtasks added
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
