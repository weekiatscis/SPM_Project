<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal panel -->
      <div
        class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:w-full"
        style="max-width: 600px;">
        <!-- Header -->
        <div class="bg-white px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900">
              Add Task to {{ project?.project_name }}
            </h3>
            <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
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
            <input id="title" v-model="form.title" type="text" required class="input-field"
              :class="{ 'border-red-500': errors.title }"
              placeholder="Enter task title" />
            <div v-if="errors.title" class="mt-1 text-sm text-red-600">
              {{ errors.title }}
            </div>
          </div>

          <!-- Description -->
          <div>
            <label for="description" class="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea id="description" v-model="form.description" rows="3" class="input-field"
              placeholder="Enter task description"></textarea>
          </div>

          <!-- Due Date -->
          <div>
            <label for="dueDate" class="block text-sm font-medium text-gray-700 mb-1">
              Due Date *
            </label>
            <input id="dueDate" v-model="form.dueDate" type="date" required class="input-field"
              :class="{ 'border-red-500': errors.dueDate }" :min="minDate" />
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
            <select id="status" v-model="form.status" class="input-field">
              <!-- Staff users cannot create unassigned tasks -->
              <option v-if="!isStaffRole" value="Unassigned">Unassigned</option>
              <option value="Ongoing">Ongoing</option>
              <option value="Under Review">Under Review</option>
              <option value="Completed">Completed</option>
            </select>
          </div>

          <!-- Priority -->
          <div>
            <label for="priority" class="block text-sm font-medium text-gray-700 mb-1">
              Priority (1-10)
            </label>
            <div class="space-y-2">
              <input
                id="priority"
                v-model.number="form.priority"
                type="range"
                min="1"
                max="10"
                step="1"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div class="flex justify-between text-xs text-gray-500">
                <span>1 (Lowest)</span>
                <span class="font-semibold text-blue-600">{{ form.priority }}</span>
                <span>10 (Highest)</span>
              </div>
            </div>
          </div>

          <!-- Assignee - Must select from project members -->
          <div>
            <label for="assignee" class="block text-sm font-medium text-gray-700 mb-1">
              Assign to Project Member *
            </label>

            <!-- If user is Staff, show read-only field with their name -->
            <div v-if="isStaffRole" class="input-field bg-gray-50 cursor-not-allowed">
              {{ authStore.user?.name || 'Current User' }} (You)
            </div>

            <!-- If user can assign to others, show dropdown -->
            <select v-else id="assignee" v-model="form.assigneeId" required class="input-field"
              :class="{ 'border-red-500': errors.assigneeId }"
              :disabled="isLoadingMembers">
              <option value="">Select team member...</option>
              <option v-for="member in projectMembers" :key="member.user_id" :value="member.user_id">
                {{ member.name }}{{ member.isOwner ? ' (Owner)' : '' }}
              </option>
            </select>

            <div v-if="errors.assigneeId" class="mt-1 text-sm text-red-600">
              {{ errors.assigneeId }}
            </div>
            <div v-if="isLoadingMembers && !isStaffRole" class="mt-1 text-sm text-gray-600">
              Loading team members...
            </div>
            <div v-if="isStaffRole" class="mt-1 text-xs text-gray-600">
              Tasks are automatically assigned to you as a Staff member
            </div>
            <div v-else class="mt-1 text-sm text-blue-600">
              Task will be automatically added to this project
            </div>
          </div>

          <!-- Collaborators (Optional - other project members) -->
          <div>
            <label for="collaborators" class="block text-sm font-medium text-gray-700 mb-1">
              Additional Collaborators
            </label>
            <div class="relative">
              <select id="collaborators" v-model="selectedCollaborator" @change="addCollaborator" class="input-field"
                :disabled="isLoadingMembers">
                <option value="">Add a collaborator...</option>
                <option v-for="member in availableCollaborators" :key="member.user_id" :value="member.user_id">
                  {{ member.name }}{{ member.isOwner ? ' (Owner)' : '' }}
                </option>
              </select>
            </div>

            <!-- Selected Collaborators -->
            <div v-if="form.collaborators.length > 0" class="mt-2 space-y-1">
              <div v-for="collaborator in selectedCollaborators" :key="collaborator.user_id"
                class="flex items-center justify-between bg-blue-50 px-3 py-2 rounded-md">
                <span class="text-sm font-medium text-blue-700">
                  {{ collaborator.name }}
                </span>
                <button type="button" @click="removeCollaborator(collaborator.user_id)"
                  class="text-blue-400 hover:text-blue-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Reminder Customization -->
            <div v-if="form.dueDate" class="border-t pt-4 mt-4">
              <!-- Notification Channels -->
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Send notifications via:
                </label>
                <div class="flex gap-4">
                  <label class="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      v-model="form.inAppEnabled"
                      class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span class="text-sm text-gray-700">In-App Notifications</span>
                  </label>
                  <label class="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      v-model="form.emailEnabled"
                      class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span class="text-sm text-gray-700">Email Notifications</span>
                  </label>
                </div>
                <div v-if="!form.inAppEnabled && !form.emailEnabled" class="mt-2 text-xs text-red-600">
                  ⚠️ You won't receive any notifications for this task
                </div>
              </div>

              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-gray-700">
                  Reminder Schedule
                </label>
                <button type="button" @click="toggleReminderCustomization"
                  class="text-sm text-blue-600 hover:text-blue-800">
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
                  <button v-for="day in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]" :key="day" type="button"
                    @click="toggleReminderDay(day)"
                    :disabled="!canAddMoreReminders && !form.reminderDays.includes(day)"
                    class="px-3 py-2 text-sm rounded border transition-colors"
                    :class="form.reminderDays.includes(day)
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed'">
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
          </div>
        </form>

        <!-- Footer -->
        <div class="bg-gray-50 px-6 py-3 flex justify-end space-x-3">
          <button type="button" @click="$emit('close')" class="btn-secondary">
            Cancel
          </button>
          <button @click="saveTask" :disabled="isLoading"
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
            {{ isLoading ? 'Creating...' : 'Create Task' }}
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
  name: 'CreateProjectTaskModal',
  props: {
    project: {
      type: Object,
      required: true
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
      status: 'Ongoing',
      priority: 5,
      assigneeId: '',
      collaborators: [],
      reminderDays: [7, 3, 1],
      emailEnabled: true,
      inAppEnabled: true
    })

    const errors = ref({
      title: '',
      dueDate: '',
      assigneeId: ''
    })

    const isLoading = ref(false)
    const isLoadingMembers = ref(false)
    const projectMembers = ref([])
    const selectedCollaborator = ref('')
    const showReminderCustomization = ref(false)

    // Check if current user is Staff role
    const isStaffRole = computed(() => {
      return authStore.user?.role === 'Staff'
    })

    // Check if user can assign tasks to others (Manager, Director, or HR)
    const canAssignToOthers = computed(() => {
      const role = authStore.user?.role
      return role === 'Manager' || role === 'Director' || role === 'HR'
    })

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

    // Available collaborators (excluding assignee)
    const availableCollaborators = computed(() => {
      return projectMembers.value.filter(member => {
        if (member.user_id === form.value.assigneeId) return false
        if (form.value.collaborators.includes(member.user_id)) return false
        return true
      })
    })

    // Get details of selected collaborators
    const selectedCollaborators = computed(() => {
      return form.value.collaborators.map(collaboratorId => {
        return projectMembers.value.find(member => member.user_id === collaboratorId)
      }).filter(Boolean)
    })

    const canAddMoreReminders = computed(() => {
      return form.value.reminderDays.length < 5
    })

    // Fetch user details by ID
    const fetchUserDetails = async (userId) => {
      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users/${userId}`)

        if (!response.ok) {
          console.error(`Failed to fetch user ${userId}: HTTP ${response.status}`)
          return null
        }

        const payload = await response.json()
        return payload.user || null
      } catch (error) {
        console.error(`Failed to fetch user ${userId}:`, error)
        return null
      }
    }

    // Load project members (owner + collaborators)
    const loadProjectMembers = async () => {
      if (!props.project) return

      isLoadingMembers.value = true
      try {
        const members = []

        // Add project owner
        if (props.project.created_by_id) {
          const ownerInfo = await fetchUserDetails(props.project.created_by_id)
          if (ownerInfo) {
            members.push({
              ...ownerInfo,
              isOwner: true
            })
          }
        }

        // Add collaborators
        if (props.project.collaborators && Array.isArray(props.project.collaborators)) {
          const collaboratorPromises = props.project.collaborators.map(userId =>
            fetchUserDetails(userId)
          )
          const collaboratorResults = await Promise.all(collaboratorPromises)
          collaboratorResults.forEach(collaborator => {
            if (collaborator) {
              members.push({
                ...collaborator,
                isOwner: false
              })
            }
          })
        }

        projectMembers.value = members
        console.log('Loaded project members:', members)
      } catch (error) {
        console.error('Failed to load project members:', error)
        projectMembers.value = []
      } finally {
        isLoadingMembers.value = false
      }
    }

    // Add collaborator
    const addCollaborator = () => {
      if (selectedCollaborator.value && !form.value.collaborators.includes(selectedCollaborator.value)) {
        form.value.collaborators.push(selectedCollaborator.value)
        selectedCollaborator.value = ''
      }
    }

    // Remove collaborator
    const removeCollaborator = (collaboratorId) => {
      const index = form.value.collaborators.indexOf(collaboratorId)
      if (index > -1) {
        form.value.collaborators.splice(index, 1)
      }
    }

    const toggleReminderCustomization = () => {
      showReminderCustomization.value = !showReminderCustomization.value
      if (!showReminderCustomization.value) {
        form.value.reminderDays = [7, 3, 1]
      }
    }

    const toggleReminderDay = (day) => {
      const index = form.value.reminderDays.indexOf(day)
      if (index > -1) {
        form.value.reminderDays.splice(index, 1)
      } else {
        if (form.value.reminderDays.length < 5) {
          form.value.reminderDays.push(day)
        }
      }
    }

    // Watch for modal opening to fetch project members
    watch(() => props.isOpen, (isOpen) => {
      if (isOpen) {
        loadProjectMembers()

        // Reset form - if Staff, auto-assign to themselves
        const defaultAssigneeId = isStaffRole.value ? (authStore.user?.user_id || '') : ''
        const defaultStatus = isStaffRole.value ? 'Ongoing' : 'Ongoing'

        form.value = {
          title: '',
          description: '',
          dueDate: '',
          status: defaultStatus,
          priority: 5,
          assigneeId: defaultAssigneeId,
          collaborators: [],
          reminderDays: [7, 3, 1],
          emailEnabled: true,
          inAppEnabled: true
        }
        errors.value = {
          title: '',
          dueDate: '',
          assigneeId: ''
        }
        showReminderCustomization.value = false
      }
    })

    const saveTask = async () => {
      // Reset errors
      errors.value = {
        title: '',
        dueDate: '',
        assigneeId: ''
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
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        const selectedDate = new Date(form.value.dueDate)

        if (selectedDate < today) {
          errors.value.dueDate = 'Please select a valid due date'
          hasErrors = true
        }
      }

      // Determine final assignee based on role
      let finalAssigneeId = form.value.assigneeId

      if (isStaffRole.value) {
        // Staff always assigns to themselves
        finalAssigneeId = authStore.user?.user_id || ''
      } else if (!form.value.assigneeId) {
        errors.value.assigneeId = 'Please select a team member to assign this task'
        hasErrors = true
      }

      if (hasErrors) {
        return
      }

      isLoading.value = true

      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const payload = {
          title: form.value.title,
          description: form.value.description,
          due_date: form.value.dueDate,
          status: form.value.status,
          priority: form.value.priority,
          owner_id: finalAssigneeId,
          collaborators: JSON.stringify(form.value.collaborators),
          project_id: props.project.project_id, // Automatically link to this project
          project: props.project.project_name, // Include project name
          reminder_days: form.value.reminderDays,
          email_enabled: form.value.emailEnabled,
          in_app_enabled: form.value.inAppEnabled,
          created_by: authStore.user?.user_id
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

        // Refresh notifications
        if (authStore.user?.user_id) {
          setTimeout(async () => {
            await notificationStore.fetchNotifications(authStore.user.user_id)
            console.log('Notifications refreshed after task creation')
          }, 500)
        }

        // Emit success
        emit('save', result.task)
        console.log('Task created successfully and added to project:', result.task)

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
      isLoadingMembers,
      isStaffRole,
      canAssignToOthers,
      projectMembers,
      selectedCollaborator,
      availableCollaborators,
      selectedCollaborators,
      authStore,
      minDate,
      daysUntilDue,
      dueDateMessage,
      dueDateColorClass,
      showReminderCustomization,
      canAddMoreReminders,
      addCollaborator,
      removeCollaborator,
      toggleReminderCustomization,
      toggleReminderDay,
      saveTask
    }
  }
}
</script>

<style scoped>
.input-field {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
  transition: all 0.15s ease;
}

.input-field:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-field.border-red-500 {
  border-color: #ef4444;
}

.btn-primary {
  padding: 0.5rem 1rem;
  background-color: #667eea;
  color: white;
  font-weight: 500;
  border-radius: 0.375rem;
  transition: all 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background-color: #5568d3;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background-color: white;
  color: #374151;
  font-weight: 500;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  background-color: #f9fafb;
}
</style>
