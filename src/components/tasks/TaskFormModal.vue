<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal panel -->
      <div
        class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
        <!-- Header -->
        <div class="bg-white px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900">
              {{ task?.id ? 'Edit Task' : (form.isSubtask ? 'Add New Subtask' : 'Add New Task') }}
            </h3>
            <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="saveTask" class="bg-white px-6 py-4 space-y-5">
          
          <!-- ========== SECTION 1: TASK BASICS ========== -->
          <!-- Task Type Toggle -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Task Type
            </label>
            <div class="flex items-center space-x-6">
              <label class="flex items-center">
                <input type="radio" v-model="form.isSubtask" :value="false"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
                <span class="ml-2 text-sm text-gray-700">Regular Task</span>
              </label>
              <label class="flex items-center">
                <input type="radio" v-model="form.isSubtask" :value="true"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
                <span class="ml-2 text-sm text-gray-700">Subtask</span>
              </label>
            </div>
          </div>

          <!-- Parent Task Selection (only for subtasks) -->
          <div v-if="form.isSubtask">
            <label for="parentTask" class="block text-sm font-medium text-gray-700 mb-1">
              Parent Task *
            </label>
            <select id="parentTask" v-model="form.parentTaskId" required class="input-field"
              :class="{ 'border-red-500': errors.parentTaskId }" :disabled="isLoadingUserTasks">
              <option value="">Select parent task...</option>
              <option v-for="task in userTasks" :key="task.id" :value="task.id">
                {{ task.title }} ({{ task.status }})
              </option>
            </select>
            <div v-if="errors.parentTaskId" class="mt-1 text-sm text-red-600">
              {{ errors.parentTaskId }}
            </div>
            <div v-if="isLoadingUserTasks" class="mt-1 text-sm text-gray-600">
              Loading your tasks...
            </div>
            <div v-if="userTasks.length === 0 && !isLoadingUserTasks" class="mt-1 text-sm text-gray-600">
              No tasks available to use as parent. Create a regular task first.
            </div>
          </div>

          <!-- Title -->
          <div>
            <label for="title" class="block text-sm font-medium text-gray-700 mb-1">
              Title *
            </label>
            <input id="title" v-model="form.title" type="text" required class="input-field"
              :class="{ 'border-red-500': errors.title }"
              :placeholder="form.isSubtask ? 'Enter subtask title' : 'Enter task title'" />
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

          <!-- ========== SECTION 2: SCHEDULING (2-column layout) ========== -->
          <div class="border-t pt-5">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            </div>

            <!-- Priority -->
            <div class="mt-4">
              <div class="flex items-center justify-between mb-3">
                <label for="priority" class="block text-sm font-medium text-gray-700">
                  Priority
                </label>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-medium text-gray-500">{{ getPriorityLabel(form.priority) }}</span>
                  <span 
                    class="inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold text-white"
                    :class="getPriorityBadgeColor(form.priority)">
                    {{ form.priority }}
                  </span>
                </div>
              </div>
              <div class="relative">
                <input 
                  id="priority" 
                  v-model.number="form.priority" 
                  type="range" 
                  min="1" 
                  max="10" 
                  step="1"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-priority"
                  :style="getSliderStyle(form.priority)"
                />
                <div class="flex justify-between mt-1 text-xs text-gray-400">
                  <span>Low</span>
                  <span>Medium</span>
                  <span>High</span>
                  <span>Critical</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ========== SECTION 3: ASSIGNMENT & COLLABORATION ========== -->
          <div class="border-t pt-5 space-y-4">
            <h4 class="text-sm font-semibold text-gray-900">Assignment & Collaboration</h4>
            
            <!-- Assignee -->
            <div>
              <label for="assignee" class="block text-sm font-medium text-gray-700 mb-1">
                Assignee *
              </label>

              <!-- If user is Staff, show read-only field with their name -->
              <div v-if="isStaffRole" class="input-field bg-gray-50 cursor-not-allowed">
                {{ authStore.user?.name || 'Current User' }} (You)
              </div>

              <!-- If user is Manager/Director, show dropdown with subordinates -->
              <select v-else-if="canAssignToOthers" id="assignee" v-model="form.assigneeId" class="input-field"
                :class="{ 'border-red-500': errors.assigneeId }">
                <option v-for="subordinate in subordinates" :key="subordinate.user_id" :value="subordinate.user_id">
                  {{ subordinate.name }}{{ subordinate.isSelf ? ' (You)' : '' }} - {{ subordinate.role }}
                </option>
              </select>

              <!-- If no subordinates available, fallback to current user -->
              <div v-else class="input-field bg-gray-50 cursor-not-allowed">
                {{ authStore.user?.name || 'Current User' }} (You)
              </div>

              <div v-if="errors.assigneeId" class="mt-1 text-sm text-red-600">
                {{ errors.assigneeId }}
              </div>

              <div v-if="isStaffRole" class="mt-1 text-xs text-gray-600">
                Tasks are automatically assigned to you as a Staff member
              </div>

              <div v-if="isLoadingSubordinates" class="mt-1 text-sm text-gray-600">
                Loading team members...
              </div>

              <div v-if="canAssignToOthers && subordinates.length === 0 && !isLoadingSubordinates"
                class="mt-1 text-sm text-gray-600">
                No team members found. Task will be assigned to you.
              </div>
            </div>

            <!-- Collaborators -->
            <div>
              <label for="collaborators" class="block text-sm font-medium text-gray-700 mb-1">
                Collaborators
                <span v-if="form.collaborators.length > 0" class="ml-2 text-xs text-blue-600 font-normal">
                  ({{ form.collaborators.length }} selected)
                </span>
              </label>
              <div class="relative">
                <select id="collaborators" v-model="selectedCollaborator" @change="addCollaborator" class="input-field"
                  :disabled="isLoadingDepartmentMembers">
                  <option value="">Add a collaborator...</option>
                  <option v-for="member in availableDepartmentMembers" :key="member.user_id" :value="member.user_id">
                    {{ member.name }} ({{ member.role }})
                  </option>
                </select>
              </div>

              <!-- Selected Collaborators -->
              <div v-if="form.collaborators.length > 0" class="mt-2 space-y-1">
                <div v-for="collaborator in selectedCollaborators" :key="collaborator.user_id"
                  class="flex items-center justify-between bg-blue-50 px-3 py-2 rounded-md">
                  <span class="text-sm font-medium text-blue-700">
                    {{ collaborator.name }} ({{ collaborator.role }})
                  </span>
                  <button type="button" @click="removeCollaborator(collaborator.user_id)"
                    class="text-blue-400 hover:text-blue-600">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <div v-if="isLoadingDepartmentMembers" class="mt-1 text-sm text-gray-600">
                Loading department members...
              </div>

              <div v-else class="mt-1 text-xs text-gray-500">
                Add members from your department to collaborate on this task
              </div>
            </div>
          </div>

          <!-- ========== SECTION 4: RECURRING TASK (for non-subtasks) ========== -->
          <div v-if="!form.isSubtask" class="border-t pt-5">
            <h4 class="text-sm font-semibold text-gray-900 mb-3">Recurring Task</h4>
            
            <!-- Show read-only info when editing an existing task -->
            <div v-if="task?.id">
              <div class="input-field bg-gray-50 cursor-not-allowed">
                {{ form.recurrence ? getRecurrenceLabel(form.recurrence) : 'Not a recurring task' }}
              </div>
              <div v-if="form.recurrence" class="mt-2 text-xs text-gray-600 bg-blue-50 p-2 rounded">
                <svg class="w-4 h-4 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                </svg>
                This is a recurring task. When completed, a new instance will be automatically created with the next due date.
              </div>
              <div v-else class="mt-2 text-xs text-gray-500">
                Recurrence cannot be changed after task creation.
              </div>
            </div>
            
            <!-- Show editable controls when creating a new task -->
            <div v-else>
              <div class="flex items-center mb-3">
                <input 
                  type="checkbox" 
                  id="isRecurring" 
                  v-model="isRecurringEnabled"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label for="isRecurring" class="ml-2 text-sm text-gray-700">
                  Make this a recurring task
                </label>
              </div>
              
              <div v-if="isRecurringEnabled" class="mt-3">
                <label for="recurrence" class="block text-sm font-medium text-gray-700 mb-1">
                  Repeat Frequency *
                </label>
                <select 
                  id="recurrence" 
                  v-model="form.recurrence" 
                  required
                  class="input-field"
                >
                  <option value="">Select frequency...</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Biweekly (Every 2 weeks)</option>
                  <option value="monthly">Monthly</option>
                </select>
                
                <div class="mt-2 text-xs text-gray-600 bg-blue-50 p-2 rounded">
                  <svg class="w-4 h-4 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                  </svg>
                  When this task is completed, a new instance will be automatically created with the next due date based on the selected frequency.
                </div>
              </div>
            </div>
          </div>

          <!-- ========== SECTION 5: NOTIFICATIONS & REMINDERS ========== -->
          <div v-if="form.dueDate" class="border-t pt-5">
            <h4 class="text-sm font-semibold text-gray-900 mb-3">Notifications & Reminders</h4>
            
            <!-- Notification Channels -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Notification Channels
              </label>
              <div class="flex gap-4">
                <label class="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="form.inAppEnabled"
                    class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span class="text-sm text-gray-700">In-App</span>
                </label>
                <label class="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="form.emailEnabled"
                    class="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span class="text-sm text-gray-700">Email</span>
                </label>
              </div>
              <div v-if="!form.inAppEnabled && !form.emailEnabled" class="mt-2 text-xs text-red-600">
                ⚠️ You won't receive any notifications for this task
              </div>
            </div>

            <!-- Reminder Schedule -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-gray-700">
                  Reminder Schedule
                </label>
                <button type="button" @click="toggleReminderCustomization"
                  class="text-xs text-blue-600 hover:text-blue-800 font-medium">
                  {{ showReminderCustomization ? '↓ Use Default' : '↑ Customize' }}
                </button>
              </div>

              <div v-if="!showReminderCustomization" class="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                Default: 7, 3, and 1 day(s) before due date
              </div>

              <div v-else class="space-y-3">
                <div class="text-xs text-gray-600">
                  Select reminder days (up to 5, max 10 days before):
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
                  Selected: {{form.reminderDays.length > 0 ? form.reminderDays.sort((a, b) => b - a).join(', ') + ' day(s) before' : 'None' }}
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
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed submittaskcreate">
            {{ isLoading ? 'Creating...' : (task?.id ? 'Update Task' : (form.isSubtask ? 'Create Subtask' : 'Create Task')) }}
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
      priority: 5,
      assigneeId: '',
      collaborators: [],
      isSubtask: false,
      parentTaskId: '',
      reminderDays: [7, 3, 1],  // Default reminder days
      emailEnabled: true,  // Default: email notifications enabled
      inAppEnabled: true,  // Default: in-app notifications enabled
      recurrence: ''  // Recurrence pattern: daily, weekly, biweekly, monthly, quarterly, yearly
    })

    const errors = ref({
      title: '',
      dueDate: '',
      assigneeId: '',
      parentTaskId: ''
    })

    const isLoading = ref(false)
    const isLoadingSubordinates = ref(false)
    const isLoadingDepartmentMembers = ref(false)
    const isLoadingUserTasks = ref(false)
    const subordinates = ref([])
    const departmentMembers = ref([])
    const userTasks = ref([])
    const selectedCollaborator = ref('')
    const isRecurringEnabled = ref(false)

    // Check if current user is Staff role
    const isStaffRole = computed(() => {
      return authStore.user?.role === 'Staff'
    })

    // Check if user can assign tasks to others (Manager or Director)
    const canAssignToOthers = computed(() => {
      const role = authStore.user?.role
      return role === 'Manager' || role === 'Director'
    })
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

    // Available department members for collaborators (excluding already selected ones and assignee)
    const availableDepartmentMembers = computed(() => {
      return departmentMembers.value.filter(member => {
        // Exclude current user
        if (member.user_id === authStore.user?.user_id) return false
        // Exclude already selected collaborators
        if (form.value.collaborators.includes(member.user_id)) return false
        // Exclude the assignee (if different from current user)
        if (form.value.assigneeId && member.user_id === form.value.assigneeId) return false
        return true
      })
    })

    // Get details of selected collaborators
    const selectedCollaborators = computed(() => {
      return form.value.collaborators.map(collaboratorId => {
        return departmentMembers.value.find(member => member.user_id === collaboratorId)
      }).filter(Boolean)
    })

    // Fetch subordinates for Manager/Director users
    const fetchSubordinates = async () => {
      if (!canAssignToOthers.value || !authStore.user?.user_id) {
        return
      }

      isLoadingSubordinates.value = true
      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users/${authStore.user.user_id}/subordinates`)

        if (response.ok) {
          const data = await response.json()
          const subordinatesList = data.subordinates || []

          // Add current user (Manager/Director/HR) to the list so they can assign to themselves
          const currentUser = {
            user_id: authStore.user.user_id,
            name: authStore.user.name,
            role: authStore.user.role,
            department: authStore.user.department,
            isSelf: true  // Flag to identify it's the current user
          }

          // Put current user at the top of the list
          subordinates.value = [currentUser, ...subordinatesList]
        } else {
          console.error('Failed to fetch subordinates:', response.status)
          subordinates.value = []
        }
      } catch (error) {
        console.error('Error fetching subordinates:', error)
        subordinates.value = []
      } finally {
        isLoadingSubordinates.value = false
      }
    }

    // Fetch department members for collaborators
    const fetchDepartmentMembers = async () => {
      if (!authStore.user?.department) {
        return
      }

      isLoadingDepartmentMembers.value = true
      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users/departments/${authStore.user.department}`)

        if (response.ok) {
          const data = await response.json()
          departmentMembers.value = data.users || []
        } else {
          console.error('Failed to fetch department members:', response.status)
          departmentMembers.value = []
        }
      } catch (error) {
        console.error('Error fetching department members:', error)
        departmentMembers.value = []
      } finally {
        isLoadingDepartmentMembers.value = false
      }
    }

    // Fetch user's tasks for parent task selection
    const fetchUserTasks = async () => {
      if (!authStore.user?.user_id) {
        return
      }

      isLoadingUserTasks.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/user/${authStore.user.user_id}`)

        if (response.ok) {
          const data = await response.json()
          // Only include tasks that are not completed and are not subtasks themselves
          userTasks.value = (data.tasks || []).filter(task =>
            task.status !== 'Completed' && !task.isSubtask
          )
        } else {
          console.error('Failed to fetch user tasks:', response.status)
          userTasks.value = []
        }
      } catch (error) {
        console.error('Error fetching user tasks:', error)
        userTasks.value = []
      } finally {
        isLoadingUserTasks.value = false
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

    // Fetch notification preferences for existing task
    const fetchNotificationPreferences = async (taskId) => {
      if (!taskId || !authStore.user?.user_id) return

      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${taskId}/notification-preferences?user_id=${authStore.user.user_id}`)

        if (response.ok) {
          const data = await response.json()
          form.value.emailEnabled = data.email_enabled ?? true
          form.value.inAppEnabled = data.in_app_enabled ?? true
          console.log('Loaded notification preferences:', data)
        }
      } catch (error) {
        console.error('Failed to fetch notification preferences:', error)
        // Keep defaults
      }
    }

    // Fetch reminder days for existing task
    const fetchReminderDays = async (taskId) => {
      if (!taskId) return

      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${taskId}/reminder-preferences`)

        if (response.ok) {
          const data = await response.json()
          form.value.reminderDays = data.reminder_days || [7, 3, 1]
          console.log('Loaded reminder days:', data.reminder_days)
        }
      } catch (error) {
        console.error('Failed to fetch reminder days:', error)
        // Keep defaults
      }
    }

    // Watch for task changes to populate form
    watch(() => props.task, async (newTask) => {
      if (newTask) {
        // Set recurring checkbox state FIRST before setting form values
        // This prevents the watcher from clearing the recurrence value
        isRecurringEnabled.value = !!newTask.recurrence

        form.value = {
          title: newTask.title || '',
          description: newTask.description || '',
          dueDate: newTask.dueDate ? new Date(newTask.dueDate).toISOString().split('T')[0] : '',
          status: newTask.status || (isStaffRole.value ? 'Ongoing' : 'Unassigned'),
          priority: newTask.priority || 5,
          assigneeId: newTask.owner_id || '',
          collaborators: newTask.collaborators || [],
          isSubtask: !!newTask.parent_task_id,
          parentTaskId: newTask.parent_task_id || '',
          reminderDays: [7, 3, 1],  // Will be updated by fetchReminderDays
          emailEnabled: true,  // Will be updated by fetchNotificationPreferences
          inAppEnabled: true,  // Will be updated by fetchNotificationPreferences
          recurrence: newTask.recurrence || ''
        }

        console.log('Loaded task for editing - recurrence:', newTask.recurrence, 'isRecurringEnabled:', isRecurringEnabled.value)

        // Fetch notification preferences and reminder days for existing task
        if (newTask.id) {
          await fetchNotificationPreferences(newTask.id)
          await fetchReminderDays(newTask.id)
        }
      } else {
        // Reset form for new task
        // Default assignee: always set to current user (Staff, Manager, Director, HR)
        const defaultAssigneeId = authStore.user?.user_id || ''

        form.value = {
          title: '',
          description: '',
          dueDate: '',
          status: isStaffRole.value ? 'Ongoing' : 'Unassigned',
          priority: 5,
          assigneeId: defaultAssigneeId,
          collaborators: [],
          isSubtask: false,
          parentTaskId: '',
          reminderDays: [7, 3, 1],
          emailEnabled: true,
          inAppEnabled: true,
          recurrence: ''
        }
        // Reset errors
        errors.value = {
          title: '',
          dueDate: '',
          assigneeId: '',
          parentTaskId: ''
        }
        showReminderCustomization.value = false
        isRecurringEnabled.value = false
      }
    }, { immediate: true })

    // Watch for modal opening to fetch subordinates and department members
    watch(() => props.isOpen, (isOpen) => {
      if (isOpen) {
        if (canAssignToOthers.value) {
          fetchSubordinates()
        }
        fetchDepartmentMembers()
        fetchUserTasks()
      }
    })

    // Watch for subtask toggle to clear parent task selection
    watch(() => form.value.isSubtask, (isSubtask) => {
      if (!isSubtask) {
        form.value.parentTaskId = ''
        errors.value.parentTaskId = ''
      }
    })

    // Watch for recurring toggle to clear recurrence
    watch(isRecurringEnabled, (enabled) => {
      if (!enabled) {
        form.value.recurrence = ''
      }
    })

    const saveTask = async () => {
      // Reset errors
      errors.value = {
        title: '',
        dueDate: '',
        assigneeId: '',
        parentTaskId: ''
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

      // Validate parent task for subtasks
      if (form.value.isSubtask && !form.value.parentTaskId) {
        errors.value.parentTaskId = 'Please select a parent task'
        hasErrors = true
      }

      // Validate assignee
      let finalAssigneeId = form.value.assigneeId

      if (isStaffRole.value) {
        // Staff always assigns to themselves
        finalAssigneeId = authStore.user?.user_id || ''
      } else if (canAssignToOthers.value) {
        // Manager/Director: if no assignee selected, auto-assign to themselves
        if (!form.value.assigneeId) {
          finalAssigneeId = authStore.user?.user_id || ''
          console.log('No assignee selected - auto-assigning to current user:', finalAssigneeId)
        } else {
          finalAssigneeId = form.value.assigneeId
        }
      } else {
        // Fallback to current user if no subordinates
        finalAssigneeId = authStore.user?.user_id || ''
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
            owner_id: finalAssigneeId,
            isSubtask: form.value.isSubtask,
            parent_task_id: form.value.isSubtask ? form.value.parentTaskId : null,
            reminder_days: form.value.reminderDays,
            email_enabled: form.value.emailEnabled,
            in_app_enabled: form.value.inAppEnabled
            // Note: recurrence is NOT included - it cannot be changed after task creation
          }

          // Only include collaborators if user has permission to manage them (Manager/Director)
          if (canAssignToOthers.value) {
            updatePayload.collaborators = JSON.stringify(form.value.collaborators)
          }
          // Staff members should not be able to modify collaborators, so we don't send this field

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
          owner_id: finalAssigneeId, // The assignee becomes the owner of the task
          collaborators: JSON.stringify(form.value.collaborators),
          isSubtask: form.value.isSubtask,
          parent_task_id: form.value.isSubtask ? form.value.parentTaskId : null,
          reminder_days: form.value.reminderDays,
          email_enabled: form.value.emailEnabled,
          in_app_enabled: form.value.inAppEnabled,
          created_by: authStore.user?.user_id, // Add who is creating the task
          recurrence: isRecurringEnabled.value ? form.value.recurrence : null
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
        // Default assignee: always set to current user (Staff, Manager, Director, HR)
        const defaultAssigneeId = authStore.user?.user_id || ''

        form.value = {
          title: '',
          description: '',
          dueDate: '',
          status: isStaffRole.value ? 'Ongoing' : 'Unassigned',
          priority: 5,
          assigneeId: defaultAssigneeId,
          collaborators: [],
          isSubtask: false,
          parentTaskId: '',
          reminderDays: [7, 3, 1],
          emailEnabled: true,
          inAppEnabled: true,
          recurrence: ''
        }
        showReminderCustomization.value = false
        isRecurringEnabled.value = false

        // Reset errors
        errors.value = {
          title: '',
          dueDate: '',
          assigneeId: '',
          parentTaskId: ''
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

        // Show appropriate success message
        if (form.value.isSubtask) {
          console.log('Subtask created and linked to parent task:', form.value.parentTaskId)
        }

      } catch (error) {
        console.error('Failed to create task:', error)
        alert(`Failed to create task: ${error.message}`)
      } finally {
        isLoading.value = false
      }
    }

    // Helper function to get readable recurrence label
    const getRecurrenceLabel = (recurrence) => {
      const labels = {
        'daily': 'Daily',
        'weekly': 'Weekly',
        'biweekly': 'Biweekly (Every 2 weeks)',
        'monthly': 'Monthly'
      }
      return labels[recurrence] || recurrence
    }

    // Helper function to get priority label
    const getPriorityLabel = (priority) => {
      if (priority <= 3) return 'Low Priority'
      if (priority <= 6) return 'Medium Priority'
      if (priority <= 8) return 'High Priority'
      return 'Critical Priority'
    }

    // Helper function to get priority badge color
    const getPriorityBadgeColor = (priority) => {
      if (priority <= 3) return 'bg-gray-500'
      if (priority <= 6) return 'bg-blue-500'
      if (priority <= 8) return 'bg-orange-500'
      return 'bg-red-500'
    }

    // Helper function to get slider gradient style
    const getSliderStyle = (priority) => {
      const percentage = ((priority - 1) / 9) * 100
      let color = '#6B7280' // gray
      if (priority <= 3) color = '#6B7280' // gray
      else if (priority <= 6) color = '#3B82F6' // blue
      else if (priority <= 8) color = '#F97316' // orange
      else color = '#EF4444' // red
      
      return {
        background: `linear-gradient(to right, ${color} 0%, ${color} ${percentage}%, #E5E7EB ${percentage}%, #E5E7EB 100%)`
      }
    }

    return {
      form,
      errors,
      isLoading,
      isStaffRole,
      canAssignToOthers,
      isLoadingSubordinates,
      isLoadingDepartmentMembers,
      isLoadingUserTasks,
      subordinates,
      departmentMembers,
      userTasks,
      selectedCollaborator,
      availableDepartmentMembers,
      selectedCollaborators,
      authStore,
      minDate,
      daysUntilDue,
      dueDateMessage,
      dueDateColorClass,
      addCollaborator,
      removeCollaborator,
      showReminderCustomization,
      canAddMoreReminders,
      toggleReminderCustomization,
      toggleReminderDay,
      isRecurringEnabled,
      getRecurrenceLabel,
      getPriorityLabel,
      getPriorityBadgeColor,
      getSliderStyle,
      saveTask
    }
  }
}
</script>

<style scoped>
/* Custom slider styling */
.slider-priority {
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  border-radius: 4px;
  outline: none;
  transition: all 0.2s ease;
}

.slider-priority::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  border: 3px solid currentColor;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider-priority::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.slider-priority::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  border: 3px solid currentColor;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider-priority::-moz-range-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

/* Color the thumb based on priority value */
.slider-priority {
  color: #3B82F6; /* Default blue */
}
</style>