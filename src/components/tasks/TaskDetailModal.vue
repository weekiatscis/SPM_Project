
<template>
  <teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 overflow-y-auto" style="z-index: 10000;">
      <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <!-- Background overlay -->
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" style="z-index: 10000;" @click="$emit('close')"></div>

        <!-- Modal panel -->
        <div
          class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full relative" style="z-index: 10001;">
        <!-- Header -->
        <div class="bg-white px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between min-h-[2.5rem]">
            <div class="flex items-center space-x-3">
              <h2 class="text-2xl font-semibold text-gray-900 leading-6 m-0">{{ task.title }}</h2>
              <a-tag :color="getStatusColor(task.status)">
                {{ getStatusText(task.status) }}
              </a-tag>
            </div>
            <button @click="$emit('close')"
              class="text-gray-400 hover:text-gray-600 p-1 flex items-center justify-center">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="bg-white px-6 py-4">
          <!-- Task header -->
          <div class="mb-6">
            <p class="text-gray-600">{{ task.description }}</p>
          </div>

          <!-- Task details grid -->
          <div class="grid grid-cols-2 gap-6 mb-6">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Assignee</label>
              <p class="text-gray-900 text-xs">{{ assigneeName }}</p>
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Project</label>
              <p class="text-gray-900 text-xs">{{ task.project }}</p>
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Due Date</label>
              <p class="text-gray-900 text-xs">{{ formatDate(task.dueDate) }}</p>
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Priority</label>
              <p class="text-gray-900 text-xs">{{ task.priority || 5 }}/10</p>
            </div>
            <div v-if="task.recurrence" class="col-span-2">
              <label class="block text-sm font-semibold text-gray-700 mb-1">Recurrence</label>
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <p class="text-gray-900 text-xs capitalize">
                  Repeats {{ task.recurrence }}
                </p>
              </div>
              <p class="text-xs text-gray-500 mt-1">
                A new task will be created automatically when this task is completed
              </p>
            </div>
          </div>

          <!-- Collaborators Section -->
          <div v-if="collaborators.length > 0" class="mb-6">
            <label class="block text-sm font-semibold text-gray-700 mb-3">Collaborators</label>
            <div class="space-y-2">
              <div v-if="isLoadingCollaborators" class="text-center py-2">
                <div class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                <p class="text-xs text-gray-500 mt-1">Loading collaborators...</p>
              </div>
              <div v-else-if="collaborators.length === 0" class="text-center py-2">
                <p class="text-xs text-gray-500">No collaborators assigned to this task.</p>
              </div>
              <div v-else class="grid grid-cols-2 gap-2">
                <div 
                  v-for="collaborator in collaborators" 
                  :key="collaborator.user_id"
                  class="flex items-center space-x-2 bg-blue-50 px-3 py-2 rounded-md border border-blue-200"
                >
                  <div class="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                    <span class="text-xs font-medium text-white">
                      {{ getInitials(collaborator.name) }}
                    </span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-blue-700 truncate">{{ collaborator.name }}</p>
                    <p class="text-xs text-blue-600">{{ collaborator.role }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Subtasks Section -->
          <div v-if="task.isSubtask || subtasks.length > 0" class="mb-6">
            <!-- Show parent task if this is a subtask -->
            <div v-if="task.isSubtask && parentTask" class="mb-4">
              <label class="block text-sm font-semibold text-gray-700 mb-2">Parent Task</label>
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <h4 class="text-sm font-medium text-gray-900">{{ parentTask.title }}</h4>
                    <p class="text-xs text-gray-600 mt-1">{{ parentTask.description || 'No description' }}</p>
                  </div>
                  <div class="ml-4">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                          :class="getStatusBadgeClass(parentTask.status)">
                      {{ parentTask.status }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Show subtasks if this task has any -->
            <div v-if="!task.isSubtask">
              <label class="block text-sm font-semibold text-gray-700 mb-3">Subtasks</label>
              <div class="space-y-2">
                <div v-if="isLoadingSubtasks" class="text-center py-2">
                  <div class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                  <p class="text-xs text-gray-500 mt-1">Loading subtasks...</p>
                </div>
                <div v-else-if="subtasks.length === 0" class="text-center py-2">
                  <p class="text-xs text-gray-500">No subtasks created for this task.</p>
                </div>
                <div v-else class="space-y-2">
                  <div 
                    v-for="subtask in subtasks" 
                    :key="subtask.id"
                    class="bg-gray-50 border border-gray-200 rounded-lg p-3 hover:bg-gray-100 transition-colors"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex-1">
                        <h4 class="text-sm font-medium text-gray-900">{{ subtask.title }}</h4>
                        <p class="text-xs text-gray-600 mt-1">{{ subtask.description || 'No description' }}</p>
                        <div class="flex items-center space-x-4 mt-2">
                          <span class="text-xs text-gray-500">
                            Due: {{ formatDate(subtask.dueDate) }}
                          </span>
                          <span class="text-xs text-gray-500">
                            Priority: {{ subtask.priority || 5 }}/10
                          </span>
                        </div>
                      </div>
                      <div class="ml-4">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                              :class="getStatusBadgeClass(subtask.status)">
                          {{ subtask.status }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Comments Section -->
          <div class="mb-6">
            <TaskComments 
              :task-id="task.id" 
              :task="task"
              @comments-updated="handleCommentsUpdated"
            />
          </div>

          <!-- Audit Log Section -->
          <div class="border-t border-gray-200 pt-6">
            <div class="bg-gray-100 rounded-lg p-4">
              <h3 class="text-sm font-medium text-gray-700 mb-4">Audit Log</h3>
              <div class="h-24 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 hover:scrollbar-thumb-gray-400 pr-2">
                <div v-if="isLoadingLogs" class="text-center py-4">
                  <div class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                  <p class="text-xs text-gray-500 mt-1">Loading audit logs...</p>
                </div>
                
                <div v-else-if="auditLogs.length === 0" class="text-center py-4">
                  <p class="text-xs text-gray-500">No audit logs found.</p>
                </div>
                
                <div v-else class="space-y-0.5">
                  <div 
                    v-for="log in auditLogs" 
                    :key="log.log_id"
                    class="flex items-start space-x-2 py-0.5 px-1 hover:bg-gray-50 rounded transition-colors duration-150"
                  >
                    <div class="flex-shrink-0">
                      <div class="w-1.5 h-1.5 rounded-full mt-1" :class="{
                        'bg-green-400': log.action === 'create',
                        'bg-blue-400': log.action === 'update',
                        'bg-red-400': log.action === 'delete'
                      }"></div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-xs text-gray-700 leading-tight">
                        <span class="font-medium text-gray-500">{{ formatLogDate(log.created_at) }}</span>: 
                        <span class="font-medium text-indigo-600">{{ getUserName(log.user_id, log.user_name) }}</span>
                        {{ formatLogMessage(log) }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer with action buttons -->
        <div class="bg-gray-50 px-6 py-3 flex justify-between">
          <div class="flex space-x-3" v-if="isCurrentUserAssignee">
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
              :title="!task.isSubtask && subtasks.length > 0 ? `This will also delete ${subtasks.length} subtask(s)` : 'Delete this task'"
            >
              <svg v-if="!isDeleting" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              <svg v-else class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ isDeleting ? 'Deleting...' : getDeleteButtonText() }}
            </button>
          </div>
          <div v-else class="flex items-center text-sm text-gray-500">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Only the assignee can edit or delete this task
          </div>
          <button
            @click="$emit('close')"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Close
          </button>
        </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import TaskComments from './TaskComments.vue'
import { useAuthStore } from '../../stores/auth'
// Icons will be inline SVG instead of components

export default {
  name: 'TaskDetailModal',
  components: {
    TaskComments
  },
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
    const authStore = useAuthStore()
    const isDeleting = ref(false)
    const auditLogs = ref([])
    
    // Check if the current user is the assignee
    const isCurrentUserAssignee = computed(() => {
      return authStore.user?.user_id === props.task?.owner_id
    })
    const isLoadingLogs = ref(false)
    const userCache = ref({})
    const collaborators = ref([])
    const isLoadingCollaborators = ref(false)
    const subtasks = ref([])
    const isLoadingSubtasks = ref(false)
    const parentTask = ref(null)
    const isLoadingParentTask = ref(false)
    const assigneeName = ref('Unassigned')

    const USER_ID_FIELDS = new Set([
      'owner_id',
      'ownerid',
      'assignee',
      'assignee_id',
      'created_by',
      'updated_by',
      'actor_id',
      'user_id'
    ])

    const USER_ID_ARRAY_FIELDS = new Set(['collaborators'])

    const normalizeFieldName = (field) => {
      if (!field || typeof field !== 'string') return ''
      return field.replace(/\s+/g, '_').toLowerCase()
    }

    const tryParseJson = (value) => {
      if (value === null || value === undefined) return null
      if (typeof value !== 'string') return value
      const trimmed = value.trim()
      if (!trimmed) return ''
      try {
        return JSON.parse(trimmed)
      } catch (error) {
        return value
      }
    }

    const extractFieldValue = (source, field, normalizedField) => {
      const data = tryParseJson(source)
      if (data === null || data === undefined) return null

      if (typeof data === 'object' && !Array.isArray(data)) {
        if (field && Object.prototype.hasOwnProperty.call(data, field)) {
          return data[field]
        }

        const normalizedKey = Object.keys(data).find(
          (key) => normalizeFieldName(key) === normalizedField
        )
        if (normalizedKey) {
          return data[normalizedKey]
        }

        const values = Object.values(data)
        if (values.length === 1) {
          return values[0]
        }
      }

      return data
    }

    const ensureArray = (value) => {
      if (Array.isArray(value)) {
        return value
      }

      const parsed = tryParseJson(value)
      if (Array.isArray(parsed)) {
        return parsed
      }

      if (parsed === null || parsed === undefined || parsed === '') {
        return []
      }

      return [parsed]
    }

    const looksLikeUuid = (value) => {
      if (typeof value !== 'string') return false
      return /^[0-9a-fA-F-]{8,}$/.test(value)
    }

    const formatUserIdValue = (rawValue) => {
      if (rawValue === null || rawValue === undefined || rawValue === '') {
        return 'None'
      }

      if (Array.isArray(rawValue)) {
        const resolved = rawValue.map((item) => formatUserIdValue(item)).filter(Boolean)
        return resolved.length > 0 ? resolved.join(', ') : 'None'
      }

      const stringValue = String(rawValue)
      if (!looksLikeUuid(stringValue)) {
        return stringValue
      }

      return getUserName(stringValue)
    }

    const formatPrimitiveValue = (value) => {
      if (value === null || value === undefined || value === '') return 'None'
      if (typeof value === 'boolean') return value ? 'Yes' : 'No'
      if (value instanceof Date) return value.toLocaleString('en-US')
      if (typeof value === 'object') return JSON.stringify(value)
      return String(value)
    }

    const formatFieldLabel = (field) => {
      const normalized = normalizeFieldName(field)
      const overrides = {
        owner_id: 'Owner',
        ownerid: 'Owner',
        assignee: 'Assignee',
        assignee_id: 'Assignee',
        due_date: 'Due Date',
        created_by: 'Created By',
        updated_by: 'Updated By',
        actor_id: 'Actor'
      }

      if (normalized && overrides[normalized]) {
        return overrides[normalized]
      }

      const safeField = field || 'field'
      return safeField
        .replace(/[_-]+/g, ' ')
        .replace(/\s+/g, ' ')
        .replace(/\b\w/g, (char) => char.toUpperCase())
        .trim()
    }

    const formatValueByField = (field, container) => {
      const normalizedField = normalizeFieldName(field)
      const value = extractFieldValue(container, field, normalizedField)

      if (USER_ID_FIELDS.has(normalizedField)) {
        return formatUserIdValue(value)
      }

      if (USER_ID_ARRAY_FIELDS.has(normalizedField)) {
        const arrayValues = ensureArray(value)
        if (arrayValues.length === 0) return 'None'
        return arrayValues.map((item) => formatUserIdValue(item)).join(', ')
      }

      if (Array.isArray(value)) {
        const formatted = value.map((item) => formatPrimitiveValue(item)).filter(Boolean)
        return formatted.length > 0 ? formatted.join(', ') : 'None'
      }

      return formatPrimitiveValue(value)
    }

    const collectUserIdsFromLog = (log) => {
      const ids = new Set()
      if (!log || !log.field) return ids

      const normalizedField = normalizeFieldName(log.field)

      const addId = (value) => {
        if (!value) return
        if (Array.isArray(value)) {
          value.forEach((item) => addId(item))
        } else if (looksLikeUuid(String(value))) {
          ids.add(String(value))
        }
      }

      if (USER_ID_FIELDS.has(normalizedField) || USER_ID_ARRAY_FIELDS.has(normalizedField)) {
        const oldValue = extractFieldValue(log.old_value, log.field, normalizedField)
        const newValue = extractFieldValue(log.new_value, log.field, normalizedField)
        addId(oldValue)
        addId(newValue)
      }

      return ids
    }

    // Fetch audit logs when modal opens or task changes
    const fetchAuditLogs = async () => {
      if (!props.task?.id) return
      
      isLoadingLogs.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${props.task.id}/logs`)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        const result = await response.json()
        
        // Logs are already sorted by the backend (latest first)
        auditLogs.value = result.logs || []

        const userIdsToFetch = new Set()

        auditLogs.value.forEach((log) => {
          if (log.user_id && log.user_name) {
            userCache.value[log.user_id] = log.user_name
          }

          if (log.user_id && looksLikeUuid(String(log.user_id))) {
            userIdsToFetch.add(String(log.user_id))
          }

          const relatedIds = collectUserIdsFromLog(log)
          relatedIds.forEach((id) => userIdsToFetch.add(id))
        })
        
        // Fetch user names for all unique user_ids (actors and referenced users)
        await fetchUserNames([...userIdsToFetch])
        
      } catch (error) {
        console.error('Failed to fetch audit logs:', error)
        auditLogs.value = []
      } finally {
        isLoadingLogs.value = false
      }
    }

    // Fetch assignee details
    const fetchAssignee = async () => {
      if (!props.task?.owner_id) {
        assigneeName.value = 'Unassigned'
        return
      }

      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users`)

        if (response.ok) {
          const result = await response.json()
          const user = result.users.find(u => u.user_id === props.task.owner_id)
          assigneeName.value = user?.name || `User ${props.task.owner_id.slice(0, 8)}`
        } else {
          assigneeName.value = `User ${props.task.owner_id.slice(0, 8)}`
        }
      } catch (error) {
        console.error('Error fetching assignee:', error)
        assigneeName.value = `User ${props.task.owner_id.slice(0, 8)}`
      }
    }

    // Fetch collaborators details
    const fetchCollaborators = async () => {
      console.log('🔍 [TaskDetailModal] fetchCollaborators called')
      console.log('   props.task:', props.task)
      console.log('   props.task.collaborators:', props.task?.collaborators)
      console.log('   Type of collaborators:', typeof props.task?.collaborators)
      console.log('   Is Array:', Array.isArray(props.task?.collaborators))

      if (!props.task?.collaborators || props.task.collaborators.length === 0) {
        console.log('   ⚠️ No collaborators or empty array, skipping fetch')
        collaborators.value = []
        return
      }

      // Filter out the assignee from collaborators
      const collaboratorIds = props.task.collaborators.filter(id => id !== props.task.owner_id)

      if (collaboratorIds.length === 0) {
        console.log('   ⚠️ All collaborators are the assignee, no additional collaborators to show')
        collaborators.value = []
        return
      }

      console.log(`   ✅ Found ${collaboratorIds.length} collaborator(s) (excluding assignee), fetching details...`)
      isLoadingCollaborators.value = true
      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const collaboratorPromises = collaboratorIds.map(async (userId) => {
          try {
            // Try to get user details from the users service
            const response = await fetch(`${userServiceUrl}/users`)
            if (response.ok) {
              const result = await response.json()
              const user = result.users.find(u => u.user_id === userId)
              return user || { user_id: userId, name: `User ${userId.slice(0, 8)}`, role: 'Unknown' }
            }
            return { user_id: userId, name: `User ${userId.slice(0, 8)}`, role: 'Unknown' }
          } catch (error) {
            console.error(`Failed to fetch collaborator ${userId}:`, error)
            return { user_id: userId, name: `User ${userId.slice(0, 8)}`, role: 'Unknown' }
          }
        })

        const results = await Promise.all(collaboratorPromises)
        collaborators.value = results.filter(Boolean) // Remove null values

      } catch (error) {
        console.error('Failed to fetch collaborators:', error)
        collaborators.value = []
      } finally {
        isLoadingCollaborators.value = false
      }
    }

    // Fetch subtasks
    const fetchSubtasks = async () => {
      if (!props.task?.id || props.task.isSubtask) {
        subtasks.value = []
        return
      }
      
      isLoadingSubtasks.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${props.task.id}/subtasks`)
        
        if (response.ok) {
          const result = await response.json()
          subtasks.value = result.subtasks || []
        } else {
          subtasks.value = []
        }
        
      } catch (error) {
        console.error('Failed to fetch subtasks:', error)
        subtasks.value = []
      } finally {
        isLoadingSubtasks.value = false
      }
    }

    // Fetch parent task if this is a subtask
    const fetchParentTask = async () => {
      if (!props.task?.parent_task_id) {
        parentTask.value = null
        return
      }

      isLoadingParentTask.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${props.task.parent_task_id}`)

        if (response.ok) {
          const result = await response.json()
          parentTask.value = result.task
        } else {
          parentTask.value = null
        }

      } catch (error) {
        console.error('Failed to fetch parent task:', error)
        parentTask.value = null
      } finally {
        isLoadingParentTask.value = false
      }
    }

    // Fetch assignee name from owner_id
    const fetchAssigneeName = async () => {
      if (!props.task?.owner_id) {
        assigneeName.value = 'Unassigned'
        return
      }

      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/users/${props.task.owner_id}`)

        if (response.ok) {
          const result = await response.json()
          if (result.user && result.user.name) {
            assigneeName.value = result.user.name
          } else {
            assigneeName.value = 'Unknown User'
          }
        } else {
          assigneeName.value = 'Unknown User'
        }

      } catch (error) {
        console.error('Failed to fetch assignee:', error)
        assigneeName.value = 'Unknown User'
      }
    }

    // Fetch all related data
    const fetchAllData = async () => {
      await Promise.all([
        fetchAuditLogs(),
        fetchCollaborators(),
        fetchSubtasks(),
        fetchParentTask(),
        fetchAssigneeName()
      ])
    }

    // Fetch logs when component mounts and modal is open
    onMounted(() => {
      if (props.isOpen && props.task?.id) {
        nextTick(() => fetchAllData())
      }
    })

    // Watch for modal opening to fetch data
    watch(() => props.isOpen, (isOpen) => {
      if (isOpen && props.task?.id) {
        nextTick(() => fetchAllData())
      }
    })

    // Watch for task changes to refetch data
    watch(() => props.task?.id, (taskId) => {
      if (props.isOpen && taskId) {
        nextTick(() => fetchAllData())
      }
    })

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const formatLogDate = (dateString) => {
      return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // Fetch user names from Supabase user table
    const fetchUserNames = async (userIds) => {
      for (const userId of userIds) {
        if (!userId || userCache.value[userId]) continue
        
        try {
          // Fetch user data directly from task service (it has Supabase access)
          const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
          const url = `${taskServiceUrl}/users/${userId}`
          
          const response = await fetch(url)
          
          if (response.ok) {
            const result = await response.json()
            
            if (result.user && result.user.name) {
              userCache.value[userId] = result.user.name
            } else {
              // Fallback to short ID if no name found
              const shortId = userId.slice(0, 8)
              userCache.value[userId] = `User ${shortId}`
            }
          } else {
            // Fallback for failed requests
            const shortId = userId.slice(0, 8)
            userCache.value[userId] = `User ${shortId}`
          }
        } catch (error) {
          // Set a fallback name so we don't keep trying
          const shortId = userId.slice(0, 8)
          userCache.value[userId] = `User ${shortId}`
        }
      }
    }

    const getUserName = (userId, preferredName) => {
      if (preferredName && userId) {
        userCache.value[userId] = preferredName
        return preferredName
      }

      if (!userId) {
        return preferredName || 'Unknown User'
      }
      
      if (userCache.value[userId]) {
        return userCache.value[userId]
      }
      
      const shortId = userId.slice(0, 8)
      const friendlyName = `User-${shortId}`
      userCache.value[userId] = friendlyName
      
      return friendlyName
    }

    const formatLogMessage = (log) => {
      if (log.action === 'create') {
        return 'created task.'
      }

      if (log.action === 'assign_task') {
        const assigneeId =
          extractFieldValue(log.new_value, 'assignee', 'assignee') ?? log.new_value?.assignee
        if (assigneeId) {
          const assigneeName = formatUserIdValue(assigneeId)
          return `assigned task to ${assigneeName}.`
        }
        return 'assigned task.'
      }

      if (log.action === 'auto_add_collaborator') {
        return 'is added as collaborator automatically.'
      }

      if (log.action === 'update') {
        const fieldName = log.field || 'field'
        const readableFieldName = formatFieldLabel(fieldName)
        const oldValue = formatValueByField(fieldName, log.old_value)
        const newValue = formatValueByField(fieldName, log.new_value)
        return `updated ${readableFieldName} from ${oldValue} to ${newValue}.`
      }

      if (log.action === 'delete') {
        return 'deleted task.'
      }

      return `performed ${log.action} action.`
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

    const getStatusBadgeClass = (status) => {
      const classes = {
        'Unassigned': 'bg-gray-100 text-gray-800',
        'Ongoing': 'bg-blue-100 text-blue-800',
        'Under Review': 'bg-yellow-100 text-yellow-800',
        'Completed': 'bg-green-100 text-green-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getInitials = (name) => {
      if (!name) return '??'
      return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
    }

    const getDeleteButtonText = () => {
      if (!props.task.isSubtask && subtasks.value.length > 0) {
        return `Delete Task + ${subtasks.value.length} Subtask${subtasks.value.length > 1 ? 's' : ''}`
      }
      return 'Delete Task'
    }

    const getPriorityColor = (priority) => {
      // Convert priority to number if it's a string (for backwards compatibility)
      const priorityNum = typeof priority === 'string' ? parseInt(priority) : priority
      
      // Map 1-10 scale to colors
      if (priorityNum >= 8) return 'bg-red-400'       // 8-10: High priority (red)
      if (priorityNum >= 5) return 'bg-yellow-400'    // 5-7: Medium priority (yellow)
      return 'bg-green-400'                            // 1-4: Low priority (green)
    }

    const editTask = () => {
      emit('edit', props.task)
    }

    const deleteTask = async () => {
      try {
        // First, get the delete preview to show what will be deleted
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const previewResponse = await fetch(`${taskServiceUrl}/tasks/${props.task.id}/delete-preview`)
        
        if (previewResponse.ok) {
          const previewData = await previewResponse.json()
          
          // Create confirmation message based on what will be deleted
          let confirmMessage = `Are you sure you want to delete "${props.task.title}"?`
          
          if (previewData.has_subtasks) {
            confirmMessage += `\n\nThis will also delete ${previewData.subtasks_count} subtask(s):`
            previewData.tasks_to_delete.forEach(task => {
              if (task.type === 'subtask') {
                confirmMessage += `\n• ${task.title}`
              }
            })
            confirmMessage += '\n\nThis action cannot be undone.'
          } else {
            confirmMessage += '\n\nThis action cannot be undone.'
          }
          
          if (!confirm(confirmMessage)) {
            return
          }
        } else {
          // Fallback if preview fails
          if (!confirm(`Are you sure you want to delete "${props.task.title}"? This action cannot be undone.`)) {
            return
          }
        }
      } catch (error) {
        console.error('Failed to get delete preview:', error)
        // Fallback confirmation
        if (!confirm(`Are you sure you want to delete "${props.task.title}"? This action cannot be undone.`)) {
          return
        }
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

        const result = await response.json()
        
        // Show success message with details of what was deleted
        if (result.total_deleted > 1) {
          console.log(`Successfully deleted ${result.total_deleted} tasks (1 main task + ${result.total_deleted - 1} subtasks)`)
        } else {
          console.log('Task deleted successfully')
        }

        emit('delete', props.task)
      } catch (error) {
        console.error('Failed to delete task:', error)
        alert(`Failed to delete task: ${error.message}`)
      } finally {
        isDeleting.value = false
      }
    }

    const handleCommentsUpdated = (commentCount) => {
      // This method can be used to update comment count in the UI if needed
      console.log(`Task ${props.task.id} now has ${commentCount} comments`)
    }

    return {
      isDeleting,
      auditLogs,
      isLoadingLogs,
      collaborators,
      isLoadingCollaborators,
      subtasks,
      isLoadingSubtasks,
      parentTask,
      isLoadingParentTask,
      assigneeName,
      isCurrentUserAssignee,
      formatDate,
      formatLogDate,
      formatActivityDate,
      getStatusColor,
      getStatusText,
      getStatusBadgeClass,
      getPriorityColor,
      getUserName,
      getInitials,
      getDeleteButtonText,
      formatLogMessage,
      editTask,
      deleteTask,
      handleCommentsUpdated
    }
  }
}
</script>
