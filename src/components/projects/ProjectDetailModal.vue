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
            <div class="flex items-center gap-3">
              <h3 class="text-lg font-medium text-gray-900">
                Project Details
              </h3>
              <a-tag :color="getStatusColor(project.status)" size="small">
                {{ getStatusText(project.status) }}
              </a-tag>
            </div>
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
        <div class="bg-white px-6 py-4 max-h-96 overflow-y-auto">
          <!-- Project Information -->
          <div class="space-y-4">
            <!-- Project Name -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Project Name
              </label>
              <p class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {{ project.project_name }}
              </p>
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <p class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md min-h-[60px]">
                {{ project.project_description || 'No description available' }}
              </p>
            </div>

            <!-- Project Metadata -->
            <div class="grid grid-cols-2 gap-4">
              <!-- Created By -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Created By
                </label>
                <p class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                  {{ project.created_by || 'Unknown' }}
                </p>
              </div>

              <!-- Created Date -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Created Date
                </label>
                <p class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                  {{ formatFullDate(project.created_at) }}
                </p>
              </div>
            </div>

            <!-- Project ID -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Project ID
              </label>
              <p class="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-md font-mono">
                {{ project.project_id }}
              </p>
            </div>

            <!-- Actions Section -->
            <div class="border-t pt-4 mt-6">
              <h4 class="text-sm font-medium text-gray-700 mb-3">Project Actions</h4>
              <div class="space-y-2">
                <div class="flex items-center justify-between p-3 bg-blue-50 rounded-md">
                  <div>
                    <p class="text-sm font-medium text-blue-900">View Tasks</p>
                    <p class="text-xs text-blue-700">See all tasks in this project</p>
                  </div>
                  <button class="text-xs bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700">
                    View Tasks
                  </button>
                </div>
                <div class="flex items-center justify-between p-3 bg-green-50 rounded-md">
                  <div>
                    <p class="text-sm font-medium text-green-900">Generate Report</p>
                    <p class="text-xs text-green-700">Export project progress report</p>
                  </div>
                  <button class="text-xs bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700">
                    Export
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 px-6 py-3 flex justify-between">
          <button
            @click="handleDelete"
            class="btn-danger"
          >
            Delete Project
          </button>
          <div class="flex space-x-3">
            <button
              type="button"
              @click="$emit('close')"
              class="btn-secondary"
            >
              Close
            </button>
            <button
              @click="handleEdit"
              class="btn-primary"
            >
              Edit Project
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProjectDetailModal',
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
  emits: ['close', 'save', 'delete'],
  setup(props, { emit }) {
    const formatFullDate = (dateString) => {
      if (!dateString) return 'Unknown'

      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const getStatusColor = (status) => {
      const colors = {
        'Active': 'blue',
        'Planning': 'cyan',
        'On Hold': 'orange',
        'Completed': 'green',
        'Cancelled': 'red'
      }
      return colors[status] || 'default'
    }

    const getStatusText = (status) => {
      return status || 'Active'
    }

    const handleEdit = () => {
      // Emit edit event - parent component can handle opening edit modal
      emit('save', props.project)
    }

    const handleDelete = () => {
      if (confirm(`Are you sure you want to delete "${props.project.project_name}"? This action cannot be undone.`)) {
        // Emit delete event
        emit('delete', props.project)
      }
    }

    return {
      formatFullDate,
      getStatusColor,
      getStatusText,
      handleEdit,
      handleDelete
    }
  }
}
</script>

<style scoped>
.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors;
}

.btn-danger {
  @apply px-4 py-2 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors;
}
</style>