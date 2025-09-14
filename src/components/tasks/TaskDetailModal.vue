<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal panel -->
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
        <!-- Header -->
        <div class="bg-white px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900">
              Task Details
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

        <!-- Content -->
        <div class="bg-white px-6 py-4">
          <!-- Task header -->
          <div class="mb-6">
            <div class="flex items-start justify-between mb-2">
              <h2 class="text-xl font-semibold text-gray-900">{{ task.title }}</h2>
              <div class="flex items-center space-x-2">
                <span 
                  :class="[
                    'px-2 py-1 text-xs font-medium rounded-full',
                    getStatusColor(task.status)
                  ]"
                >
                  {{ getStatusText(task.status) }}
                </span>
                <div 
                  :class="[
                    'w-3 h-3 rounded-full',
                    getPriorityColor(task.priority)
                  ]"
                  :title="`${task.priority} priority`"
                ></div>
              </div>
            </div>
            <p class="text-gray-600">{{ task.description }}</p>
          </div>

          <!-- Task details grid -->
          <div class="grid grid-cols-2 gap-6 mb-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Assignee</label>
              <p class="text-gray-900">{{ task.assignee }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Project</label>
              <p class="text-gray-900">{{ task.project }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
              <p class="text-gray-900">{{ formatDate(task.dueDate) }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <p class="text-gray-900 capitalize">{{ task.priority }}</p>
            </div>
          </div>

          <!-- Activity timeline -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Activity Timeline</h4>
            <div class="space-y-3">
              <div v-for="activity in task.activities" :key="activity.id" class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                  <div class="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <svg class="w-4 h-4 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-gray-900">
                    <span class="font-medium">{{ activity.user }}</span>
                    {{ activity.action }}
                  </p>
                  <p class="text-xs text-gray-500">{{ formatActivityDate(activity.timestamp) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Comments section -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Comments</h4>
            <div class="space-y-3 mb-4">
              <div v-for="comment in task.comments" :key="comment.id" class="bg-gray-50 rounded-lg p-3">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm font-medium text-gray-900">{{ comment.user }}</span>
                  <span class="text-xs text-gray-500">{{ formatActivityDate(comment.timestamp) }}</span>
                </div>
                <p class="text-sm text-gray-700">{{ comment.text }}</p>
              </div>
            </div>
            
            <!-- Add comment -->
            <div class="flex space-x-3">
              <input
                v-model="newComment"
                type="text"
                placeholder="Add a comment..."
                class="flex-1 input-field"
                @keyup.enter="addComment"
              />
              <button
                @click="addComment"
                :disabled="!newComment.trim()"
                class="btn-primary"
              >
                Add
              </button>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 px-6 py-3 flex justify-between">
          <button
            @click="$emit('delete', task)"
            class="btn-secondary text-red-600 hover:bg-red-50"
          >
            Delete Task
          </button>
          <div class="flex space-x-3">
            <button
              @click="$emit('close')"
              class="btn-secondary"
            >
              Close
            </button>
            <button
              @click="editTask"
              class="btn-primary"
            >
              Edit Task
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { CloseIcon, CheckCircleIcon } from '../icons/index.js'

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
  emits: ['close', 'save', 'delete'],
  setup(props, { emit }) {
    const newComment = ref('')

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
        pending: 'bg-yellow-100 text-yellow-800',
        'in-progress': 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        overdue: 'bg-red-100 text-red-800'
      }
      return colors[status] || colors.pending
    }

    const getStatusText = (status) => {
      const texts = {
        pending: 'Pending',
        'in-progress': 'In Progress',
        completed: 'Completed',
        overdue: 'Overdue'
      }
      return texts[status] || 'Pending'
    }

    const getPriorityColor = (priority) => {
      const colors = {
        low: 'bg-green-400',
        medium: 'bg-yellow-400',
        high: 'bg-red-400'
      }
      return colors[priority] || colors.medium
    }

    const addComment = () => {
      if (!newComment.value.trim()) return

      const comment = {
        id: Date.now(),
        user: 'Current User',
        text: newComment.value.trim(),
        timestamp: new Date().toISOString()
      }

      const updatedTask = {
        ...props.task,
        comments: [...(props.task.comments || []), comment]
      }

      emit('save', updatedTask)
      newComment.value = ''
    }

    const editTask = () => {
      // This would typically open an edit modal
      // For now, we'll emit a close event and let the parent handle editing
      emit('close')
    }

    return {
      newComment,
      formatDate,
      formatActivityDate,
      getStatusColor,
      getStatusText,
      getPriorityColor,
      addComment,
      editTask
    }
  }
}
</script>
