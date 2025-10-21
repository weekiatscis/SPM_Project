
<template>
  <teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 overflow-y-auto" style="z-index: 10000;">
      <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <!-- Background overlay -->
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" style="z-index: 10000;" @click="$emit('close')"></div>

        <!-- Modal panel -->
        <div
          class="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full relative" style="z-index: 10001;">
        <!-- Header -->
        <div class="modal-header">
          <div class="flex items-start justify-between">
            <div class="flex-1 pr-8">
              <div class="flex items-center gap-3 mb-3">
                <h2 class="modal-title">{{ task.title }}</h2>
                <a-tag :color="getStatusColor(task.status)" class="status-tag-large">
                  {{ getStatusText(task.status) }}
                </a-tag>
              </div>
              <button @click="editTask" class="edit-button" v-if="isCurrentUserAssignee">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span>Edit Task</span>
              </button>
            </div>
            <button @click="$emit('close')" class="close-button">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="modal-content">
          <!-- Task Description -->
          <div class="description-section">
            <p class="description-text">{{ task.description }}</p>
          </div>

          <!-- Task details grid -->
          <div class="details-grid">
            <div class="detail-item">
              <label class="detail-label">Assignee</label>
              <p class="detail-value">{{ assigneeName }}</p>
            </div>
            <div class="detail-item">
              <label class="detail-label">Project</label>
              <p class="detail-value">{{ projectName }}</p>
            </div>
            <div class="detail-item">
              <label class="detail-label">Due Date</label>
              <p class="detail-value">{{ formatDate(task.dueDate) }}</p>
            </div>
            <div class="detail-item">
              <label class="detail-label">Priority</label>
              <p class="detail-value">{{ task.priority || 5 }}/10</p>
            </div>
            <div v-if="task.status === 'Completed' && task.completedDate" class="detail-item">
              <label class="detail-label">Completed Date</label>
              <p class="detail-value">{{ formatDate(task.completedDate) }}</p>
            </div>
            <div v-if="(task.status === 'Ongoing' || task.status === 'Under Review') && task.created_at" class="detail-item">
              <label class="detail-label">Time Taken</label>
              <div class="flex items-center gap-2 detail-value">
                <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{{ timeTaken }}</span>
              </div>
            </div>
            <div v-if="task.recurrence" class="detail-item col-span-2">
              <label class="detail-label">Recurrence</label>
              <div class="flex items-center gap-3 detail-value">
                <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span class="capitalize">Repeats {{ task.recurrence }}</span>
              </div>
              <p class="detail-hint">
                A new task will be created automatically when this task is completed
              </p>
            </div>
          </div>

          <!-- Collaborators Section -->
          <div v-if="collaborators.length > 0" class="section-block">
            <h3 class="section-title">Collaborators</h3>
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
          <div v-if="subtasks.length > 0" class="section-block">
            <!-- Show subtasks if this task has any -->
            <div v-if="!task.isSubtask">
              <h3 class="section-title">Subtasks ({{ subtasks.length }})</h3>
              <div class="space-y-2">
                <div v-if="isLoadingSubtasks" class="text-center py-2">
                  <div class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                  <p class="text-xs text-gray-500 mt-1">Loading subtasks...</p>
                </div>
                <div v-else-if="subtasks.length === 0" class="text-center py-2">
                  <p class="text-xs text-gray-500">No subtasks created for this task.</p>
                </div>
                <div v-else class="space-y-3">
                  <div 
                    v-for="subtask in subtasks" 
                    :key="subtask.id"
                    @click="handleSubtaskClick(subtask)"
                    class="subtask-card"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex-1">
                        <div class="flex items-center space-x-2">
                          <h4 class="text-sm font-medium text-gray-900 group-hover:text-blue-700">{{ subtask.title }}</h4>
                          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                                :class="getStatusBadgeClass(subtask.status)">
                            {{ subtask.status }}
                          </span>
                        </div>
                        <div class="flex items-center space-x-4 mt-1">
                          <span class="text-xs text-gray-500 flex items-center">
                            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                            </svg>
                            {{ formatDate(subtask.dueDate) }}
                          </span>
                          <span class="text-xs text-gray-500 flex items-center">
                            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11"></path>
                            </svg>
                            Priority: {{ subtask.priority || 5 }}/10
                          </span>
                        </div>
                      </div>
                      <div class="ml-4">
                        <svg class="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Comments Section -->
          <div class="section-block">
            <TaskComments 
              :task-id="task.id" 
              :task="task"
              @comments-updated="handleCommentsUpdated"
            />
          </div>

          <!-- Audit Log Section -->
          <div class="audit-log-section">
            <div class="audit-log-container">
              <h3 class="section-title">Audit Log</h3>
              <div class="audit-log-scroll">
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
                        <span class="font-medium text-indigo-600">{{ getUserName(log.user_id) }}</span>
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
        <div class="modal-footer">
          <div class="flex space-x-3" v-if="isCurrentUserAssignee">
            <!-- Mark as Completed Button (only show if not already completed) -->
            <button
              v-if="task.status !== 'Completed'"
              @click="markAsCompleted"
              :disabled="isMarkingComplete"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="!isMarkingComplete" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <svg v-else class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ isMarkingComplete ? 'Completing...' : 'Mark as Completed' }}
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
import { calculateTimeTaken } from '../../utils/dateUtils'
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
  emits: ['close', 'edit', 'delete', 'open-task'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    const isDeleting = ref(false)
    const isMarkingComplete = ref(false)
    const auditLogs = ref([])
    
    // Check if the current user is the assignee
    const isCurrentUserAssignee = computed(() => {
      return authStore.user?.user_id === props.task?.owner_id
    })
    
    // Calculate time taken for ongoing or under review tasks
    const timeTaken = computed(() => {
      if (!props.task?.created_at) return 'N/A'
      if (props.task.status !== 'Ongoing' && props.task.status !== 'Under Review') return 'N/A'
      return calculateTimeTaken(props.task.created_at)
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
    const projectName = ref('No Project')

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
        
        // Fetch user names for all unique user_ids
        const userIds = [...new Set(auditLogs.value.map(log => log.user_id))]
        await fetchUserNames(userIds)
        
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

    // Fetch project name from project_id
    const fetchProjectName = async () => {
      console.log('🔍 [TaskDetailModal] fetchProjectName called');
      console.log('   props.task:', props.task);
      console.log('   All task keys:', Object.keys(props.task));
      console.log('   props.task.project:', props.task.project);
      console.log('   typeof props.task.project:', typeof props.task.project);
      if (typeof props.task.project === 'object' && props.task.project !== null) {
        console.log('   props.task.project object:', JSON.stringify(props.task.project));
      }
      if (!props.task.project) {
        console.warn('   ⚠️ No project found, setting to "No Project"');
        projectName.value = 'No Project';
        return;
      }
      // If project is an object, use its name directly
      if (typeof props.task.project === 'object' && props.task.project !== null) {
        projectName.value = props.task.project.name || 'No Project';
        return;
      }
      // If project is a string, check if it's a likely ID (UUID or number)
      if (typeof props.task.project === 'string') {
        // Simple check: if it looks like a UUID, fetch from API; otherwise, use as name
        const uuidRegex = /^[0-9a-fA-F-]{36}$/;
        if (uuidRegex.test(props.task.project)) {
          const projectId = props.task.project;
          try {
            const response = await fetch(`/api/projects?project_id=${projectId}`);
            console.log('   Response status:', response.status);
            if (response.ok) {
              const result = await response.json();
              console.log('   Full API response:', JSON.stringify(result));
              if (result.projects && result.projects.length > 0) {
                projectName.value = result.projects[0].project_name;
                console.log('   ✅ Project name set to:', projectName.value);
              } else {
                projectName.value = 'No Project';
                console.log('   ⚠️ No projects in response, setting to "No Project"');
              }
            } else {
              projectName.value = 'No Project';
              console.log('   ❌ Response not OK, setting to "No Project"');
            }
          } catch (error) {
            console.error('Failed to fetch project name:', error);
            projectName.value = 'No Project';
          }
        } else {
          // Use the string directly as the project name
          projectName.value = props.task.project;
          console.log('   ✅ Project name set directly from string:', projectName.value);
        }
        return;
      }
    }

    // Fetch all related data
    const fetchAllData = async () => {
      await Promise.all([
        fetchAuditLogs(),
        fetchCollaborators(),
        fetchSubtasks(),
        fetchParentTask(),
        fetchAssigneeName(),
        fetchProjectName()
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
        console.log('🔍 [TaskDetailModal] Modal opened with task:', props.task)
        console.log('🔍 [TaskDetailModal] Task status:', props.task.status)
        console.log('🔍 [TaskDetailModal] Task completedDate:', props.task.completedDate)
        console.log('🔍 [TaskDetailModal] Task completed_date:', props.task.completed_date)
        console.log('🔍 [TaskDetailModal] All task keys:', Object.keys(props.task))
        nextTick(() => fetchAllData())
      }
    })

    // Watch for task changes to refetch data
    watch(() => props.task?.id, (taskId) => {
      if (props.isOpen && taskId) {
        console.log('🔍 [TaskDetailModal] Task changed:', props.task)
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

    const getUserName = (userId) => {
      if (!userId) return 'Unknown User'
      
      // Check if we have a cached name
      if (userCache.value[userId]) {
        return userCache.value[userId]
      }
      
      // Create a user-friendly fallback name from the UUID
      const shortId = userId.slice(0, 8)
      const friendlyName = `User-${shortId}`
      userCache.value[userId] = friendlyName
      
      return friendlyName
    }

    const formatLogMessage = (log) => {
      if (log.action === 'create') {
        return 'created task.'
      } else if (log.action === 'assign_task') {
        // Handle task assignment: "assigned task to [User Name]"
        const assigneeId = log.new_value?.assignee
        if (assigneeId) {
          const assigneeName = getUserName(assigneeId)
          return `assigned task to ${assigneeName}.`
        }
        return 'assigned task.'
      } else if (log.action === 'auto_add_collaborator') {
        // Handle auto-collaboration: "is added as collaborator automatically"
        return 'is added as collaborator automatically.'
      } else if (log.action === 'update') {
        const fieldName = log.field
        
        // Handle JSONB structure for old and new values
        let oldValue = 'null'
        let newValue = 'null'
        
        if (log.old_value && typeof log.old_value === 'object' && log.old_value[fieldName] !== undefined) {
          oldValue = log.old_value[fieldName] === null ? 'null' : String(log.old_value[fieldName])
        }
        
        if (log.new_value && typeof log.new_value === 'object' && log.new_value[fieldName] !== undefined) {
          newValue = log.new_value[fieldName] === null ? 'null' : String(log.new_value[fieldName])
        }
        
        // Format field names to be more readable
        const readableFieldName = fieldName.replace(/_/g, ' ')
        
        return `updated ${readableFieldName} from "${oldValue}" to "${newValue}".`
      } else if (log.action === 'delete') {
        return 'deleted task.'
      }
      return `performed ${log.action} action.`
    }

    const formatValue = (field, valueObj) => {
      if (!valueObj) return 'null'
      
      // Handle JSONB objects from the database
      if (typeof valueObj === 'object') {
        // For single field updates, the structure is: { "field_name": "value" }
        if (valueObj[field] !== undefined) {
          const value = valueObj[field]
          return value === null ? 'null' : String(value)
        }
        
        // For create actions, the structure contains all created fields
        if (field === 'task' && typeof valueObj === 'object') {
          // For create actions, show a summary of created fields
          const fields = Object.keys(valueObj).filter(key => valueObj[key] !== null)
          return `with ${fields.join(', ')}`
        }
        
        // Fallback: try to extract any non-null value from the object
        const nonNullValues = Object.entries(valueObj).filter(([_, value]) => value !== null)
        if (nonNullValues.length > 0) {
          return nonNullValues.map(([_, value]) => String(value)).join(', ')
        }
      }
      
      return valueObj === null ? 'null' : String(valueObj)
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

    const markAsCompleted = async () => {
      // Check if this is a parent task with subtasks
      const hasSubtasks = subtasks.value && subtasks.value.length > 0
      const confirmMessage = hasSubtasks 
        ? `Mark "${props.task.title}" as completed?\n\nThis will also mark ${subtasks.value.length} subtask${subtasks.value.length > 1 ? 's' : ''} as completed.`
        : `Mark "${props.task.title}" as completed?`
      
      if (!confirm(confirmMessage)) {
        return
      }

      isMarkingComplete.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        
        // Mark the parent task as completed
        const response = await fetch(`${taskServiceUrl}/tasks/${props.task.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            status: 'Completed'
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `Failed to update task status`)
        }

        const result = await response.json()
        
        // If this is a parent task with subtasks, mark all subtasks as completed too
        if (hasSubtasks) {
          const subtaskPromises = subtasks.value.map(async (subtask) => {
            if (subtask.status !== 'Completed') {
              try {
                const subtaskResponse = await fetch(`${taskServiceUrl}/tasks/${subtask.id}`, {
                  method: 'PUT',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    status: 'Completed'
                  })
                })
                
                if (!subtaskResponse.ok) {
                  console.error(`Failed to complete subtask: ${subtask.title}`)
                }
              } catch (error) {
                console.error(`Error completing subtask ${subtask.title}:`, error)
              }
            }
          })
          
          // Wait for all subtasks to be updated
          await Promise.all(subtaskPromises)
        }
        
        // Show success message
        let successMessage = 'Task marked as completed successfully!'
        if (hasSubtasks) {
          successMessage += `\n\nAll ${subtasks.value.length} subtask${subtasks.value.length > 1 ? 's have' : ' has'} also been marked as completed.`
        }
        if (props.task.recurrence) {
          successMessage += '\n\nA new recurring task has been created.'
        }
        alert(successMessage)
        
        // Update local task object
        props.task.status = 'Completed'
        
        // Close the modal and emit event
        emit('close')
        
        // Optionally emit a refresh event or update event
        window.location.reload() // Simple approach to refresh the list
        
      } catch (error) {
        console.error('Failed to mark task as completed:', error)
        alert(`Failed to mark task as completed: ${error.message}`)
      } finally {
        isMarkingComplete.value = false
      }
    }

    const handleCommentsUpdated = (commentCount) => {
      // This method can be used to update comment count in the UI if needed
      console.log(`Task ${props.task.id} now has ${commentCount} comments`)
    }

    const handleSubtaskClick = (subtask) => {
      console.log('=== SUBTASK CLICKED IN TASKDETAILMODAL ===')
      console.log('Subtask data:', subtask)
      console.log('About to emit open-task event')
      emit('open-task', subtask)
      console.log('open-task event emitted successfully')
    }

    return {
      isDeleting,
      isMarkingComplete,
      auditLogs,
      isLoadingLogs,
      collaborators,
      isLoadingCollaborators,
      subtasks,
      isLoadingSubtasks,
      parentTask,
      isLoadingParentTask,
      assigneeName,
      projectName,
      isCurrentUserAssignee,
      timeTaken,
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
      markAsCompleted,
      handleCommentsUpdated,
      handleSubtaskClick
    }
  }
}
</script>

<style scoped>
/* Modal Header */
.modal-header {
  background: linear-gradient(to bottom, #ffffff, #f9fafb);
  padding: 28px 32px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 26px;
  font-weight: 700;
  color: #111827;
  letter-spacing: -0.02em;
  line-height: 1.3;
  margin: 0;
}

.status-tag-large {
  font-size: 14px !important;
  font-weight: 600 !important;
  padding: 6px 16px !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

.edit-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.edit-button:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
  color: #111827;
  transform: translateY(-1px);
}

.close-button {
  padding: 8px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  color: #6b7280;
  transition: all 0.2s ease;
  cursor: pointer;
  flex-shrink: 0;
}

.close-button:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

/* Modal Content */
.modal-content {
  padding: 32px;
  max-height: 70vh;
  overflow-y: auto;
}

/* Custom Scrollbar */
.modal-content::-webkit-scrollbar {
  width: 8px;
}

.modal-content::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

.modal-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Description Section */
.description-section {
  margin-bottom: 32px;
  padding: 20px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.description-text {
  font-size: 15px;
  line-height: 1.6;
  color: #374151;
  margin: 0;
}

/* Details Grid */
.details-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
  padding: 24px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  line-height: 1.5;
}

.detail-hint {
  font-size: 13px;
  color: #6b7280;
  margin-top: 8px;
  line-height: 1.5;
}

/* Section Blocks */
.section-block {
  margin-bottom: 32px;
  padding: 24px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.section-title {
  font-size: 17px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 20px 0;
  letter-spacing: -0.01em;
}

/* Subtask Cards */
.subtask-card {
  background: #ffffff;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.subtask-card:hover {
  background: #eff6ff;
  border-color: #60a5fa;
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(96, 165, 250, 0.15);
}

/* Audit Log Section */
.audit-log-section {
  border-top: 1px solid #e5e7eb;
  padding-top: 32px;
  margin-top: 32px;
}

.audit-log-container {
  background: #f9fafb;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.audit-log-scroll {
  height: 200px;
  overflow-y: auto;
  padding-right: 8px;
}

.audit-log-scroll::-webkit-scrollbar {
  width: 6px;
}

.audit-log-scroll::-webkit-scrollbar-track {
  background: #e5e7eb;
  border-radius: 3px;
}

.audit-log-scroll::-webkit-scrollbar-thumb {
  background: #9ca3af;
  border-radius: 3px;
}

.audit-log-scroll::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}

/* Modal Footer */
.modal-footer {
  background: #f9fafb;
  padding: 20px 32px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-header {
    padding: 20px 24px;
  }
  
  .modal-title {
    font-size: 22px;
  }
  
  .modal-content {
    padding: 24px;
  }
  
  .details-grid {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 20px;
  }
  
  .section-block {
    padding: 20px;
  }
  
  .audit-log-scroll {
    height: 150px;
  }
  
  .modal-footer {
    padding: 16px 24px;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
