<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal panel - Increased width with max-w-4xl -->
      <div
        class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
        <!-- Header - With close button (X) in top right -->
        <div class="bg-white px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between min-h-[2.5rem]">
            <div class="flex items-center space-x-3">
              <h2 class="text-2xl font-semibold text-gray-900 leading-6 m-0">{{ task.title }}</h2>
            </div>
            <button
              @click="$emit('close')"
              class="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
              aria-label="Close"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content - Enhanced with all fields from TaskFormModal -->
        <div class="bg-white px-6 py-4">
          <!-- Description -->
          <div class="mb-6">
            <label class="block text-sm font-semibold text-gray-700 mb-1">Description</label>
            <p class="text-gray-600">{{ task.description || 'No description available' }}</p>
          </div>

          <!-- Task details grid - Updated with all fields from TaskFormModal -->
          <div class="grid grid-cols-2 gap-6 mb-6">
            <!-- Status -->
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Status</label>
              <p class="text-gray-900">
                <a-tag :color="getStatusColor(task.status)">
                  {{ getStatusText(task.status) }}
                </a-tag>
              </p>
            </div>

            <!-- Priority -->
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Priority</label>
              <p class="text-gray-900 capitalize">{{ task.priority || 'Not set' }}</p>
            </div>

            <!-- Due Date -->
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Due Date</label>
              <p class="text-gray-900">{{ task.dueDate ? formatDate(task.dueDate) : 'No due date' }}</p>
            </div>

            <!-- Owner / Assignee -->
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Owner / Assignee</label>
              <p class="text-gray-900">
                <span v-if="isLoadingUsers">Loading user data...</span>
                <span v-else>{{ task.owner_id ? (userLookup[task.owner_id] || task.owner_id) : (task.assignee || 'Unassigned') }}</span>
              </p>
            </div>

            <!-- Parent Project / Group -->
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Parent Project / Group</label>
              <p class="text-gray-900">{{ task.project_id || task.project || 'No parent project' }}</p>
            </div>

            <!-- Created At -->
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Created</label>
              <p class="text-gray-900">{{ task.created_at ? formatDate(task.created_at) : 'Unknown' }}</p>
            </div>
          </div>

          <!-- Collaborators / Invited Members -->
          <div class="mb-6">
            <label class="block text-sm font-semibold text-gray-700 mb-1">Collaborators / Invited Members</label>
            <div class="flex flex-wrap gap-2">
              <p v-if="!parsedCollaborators || parsedCollaborators.length === 0" class="text-gray-500">No collaborators</p>
              <template v-else>
                <a-tag v-for="(collaborator, idx) in parsedCollaborators" :key="idx" color="blue">
                  {{ userLookup[collaborator] || collaborator }}
                </a-tag>
              </template>
              <p v-if="isLoadingUsers" class="text-xs text-gray-500 mt-2">Loading user data...</p>
            </div>
          </div>

          <!-- Subtasks -->
          <div class="mb-6">
            <label class="block text-sm font-semibold text-gray-700 mb-1">Subtasks</label>
            <div class="mt-2">
              <p v-if="!parsedSubtasks || parsedSubtasks.length === 0" class="text-gray-500">No subtasks</p>
              <template v-else>
                <ul class="list-disc pl-5 space-y-1">
                  <li v-for="(subtask, idx) in parsedSubtasks" :key="idx" class="text-gray-900">
                    {{ subtask.title }}
                    <span v-if="subtask.completed" class="text-green-500 ml-2">(Completed)</span>
                  </li>
                </ul>
              </template>
            </div>
          </div>
        </div>

        <!-- Footer with action buttons - Moved edit and delete buttons to the right, removed close button -->
        <div class="bg-gray-50 px-6 py-3 flex justify-end space-x-3">
          <button
            @click="editTask"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            Edit Task
          </button>
          <button
            @click="deleteTask"
            :disabled="isDeleting"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="!isDeleting" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
            <svg v-else class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isDeleting ? 'Deleting...' : 'Delete Task' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
// Icons will be inline SVG instead of components

export default {
  name: 'TaskDetailModal',
  props: {
    task: {
      type: Object,
      required: true
    },
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'edit', 'delete'],
  setup(props, { emit }) {
    const isDeleting = ref(false)
    
    // Parse collaborators and subtasks if they're JSON strings
    const parsedCollaborators = ref([])
    const parsedSubtasks = ref([])
    
    // User lookup to translate IDs to names
    const userLookup = ref({})
    const isLoadingUsers = ref(false)
    
    // Watch for task changes to parse JSON data
    watch(() => props.task, (newTask) => {
      if (newTask) {
        // Parse collaborators
        if (newTask.collaborators) {
          try {
            if (typeof newTask.collaborators === 'string') {
              parsedCollaborators.value = JSON.parse(newTask.collaborators);
            } else {
              parsedCollaborators.value = newTask.collaborators;
            }
          } catch (e) {
            console.error("Failed to parse collaborators:", e);
            parsedCollaborators.value = [];
          }
        } else {
          parsedCollaborators.value = [];
        }
        
        // Parse subtasks
        if (newTask.subtasks) {
          try {
            if (typeof newTask.subtasks === 'string') {
              parsedSubtasks.value = JSON.parse(newTask.subtasks);
            } else {
              parsedSubtasks.value = newTask.subtasks;
            }
          } catch (e) {
            console.error("Failed to parse subtasks:", e);
            parsedSubtasks.value = [];
          }
        } else {
          parsedSubtasks.value = [];
        }
      }
    }, { immediate: true })

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const formatActivityDate = (dateString) => {
      return new Date(dateString).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const getStatusColor = (status) => {
      const colors = {
        'Unassigned': 'default',
        'Ongoing': 'blue',
        'Under Review': 'gold',
        'Completed': 'green'
      }
      return colors[status] || 'default'
    }

    const getStatusText = (status) => {
      const texts = {
        'Unassigned': 'Unassigned',
        'Ongoing': 'Ongoing',
        'Under Review': 'Under Review',
        'Completed': 'Completed'
      }
      return texts[status] || 'Unassigned'
    }

    const getPriorityColor = (priority) => {
      const colors = {
        low: 'bg-green-400',
        medium: 'bg-yellow-400',
        high: 'bg-red-400'
      }
      return colors[priority] || colors.medium
    }

    const editTask = () => {
      emit('edit', props.task)
    }

    const deleteTask = async () => {
      if (!confirm(`Are you sure you want to delete "${props.task.title}"? This action cannot be undone.`)) {
        return
      }

      isDeleting.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${props.task.id}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          }
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        emit('delete', props.task)
      } catch (error) {
        console.error('Failed to delete task:', error)
        alert(`Failed to delete task: ${error.message}`)
      } finally {
        isDeleting.value = false
      }
    }
    
    // Fetch users from the database
    const fetchUsers = async () => {
      isLoadingUsers.value = true
      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`)
        }
        
        const data = await response.json()
        if (Array.isArray(data.users)) {
          const lookup = {}
          data.users.forEach(user => {
            lookup[user.user_id] = user.name || user.email || user.user_id
          })
          userLookup.value = lookup
          console.log('User lookup populated:', userLookup.value)
        } else {
          console.error('Expected users array in response, got:', data)
          fallbackToDefaultUserLookup()
        }
      } catch (error) {
        console.error('Failed to fetch users for lookup:', error)
        fallbackToDefaultUserLookup()
      } finally {
        isLoadingUsers.value = false
      }
    }
    
    // Fallback to default user lookup if API fails
    const fallbackToDefaultUserLookup = () => {
      console.warn('Using fallback user lookup data')
      userLookup.value = {
        '3fa85f64-5717-4562-b3fc-2c963f66afa6': 'John Doe',
        '5dc8784a-f695-4060-9a9a-0a375661a6e1': 'Jane Smith',
        '2abf3fc3-3b5a-49c5-88f5-85dbd5a3f2cd': 'Mike Johnson',
        '612c8e02-9d1d-4a11-9f4f-49f8ae5aba97': 'Wee Kiat'
      }
    }
    
    // Fetch users when component is mounted
    onMounted(() => {
      fetchUsers()
    })

    return {
      isDeleting,
      formatDate,
      formatActivityDate,
      getStatusColor,
      getStatusText,
      getPriorityColor,
      parsedCollaborators,
      parsedSubtasks,
      userLookup,
      editTask,
      deleteTask
    }
  }
}
</script>
