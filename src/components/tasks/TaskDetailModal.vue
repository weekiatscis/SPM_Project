<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal panel -->
      <div
        class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
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
              <p class="text-gray-900 text-xs">{{ task.assignee }}</p>
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
              <p class="text-gray-900 text-xs capitalize">{{ task.priority }}</p>
            </div>
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
  emits: ['close'],
  setup(props, { emit }) {

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

    return {
      formatDate,
      formatActivityDate,
      getStatusColor,
      getStatusText,
      getPriorityColor
    }
  }
}
</script>
