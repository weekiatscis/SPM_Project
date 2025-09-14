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
              placeholder="Enter task title"
            />
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

          <!-- Project and Assignee -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="project" class="block text-sm font-medium text-gray-700 mb-1">
                Project *
              </label>
              <select
                id="project"
                v-model="form.project"
                required
                class="input-field"
              >
                <option value="">Select project</option>
                <option value="Website Redesign">Website Redesign</option>
                <option value="Mobile App">Mobile App</option>
                <option value="Marketing Campaign">Marketing Campaign</option>
                <option value="Product Launch">Product Launch</option>
              </select>
            </div>

            <div>
              <label for="assignee" class="block text-sm font-medium text-gray-700 mb-1">
                Assignee *
              </label>
              <select
                id="assignee"
                v-model="form.assignee"
                required
                class="input-field"
              >
                <option value="">Select assignee</option>
                <option value="John Doe">John Doe</option>
                <option value="Jane Smith">Jane Smith</option>
                <option value="Mike Johnson">Mike Johnson</option>
                <option value="Sarah Wilson">Sarah Wilson</option>
              </select>
            </div>
          </div>

          <!-- Due Date and Priority -->
          <div class="grid grid-cols-2 gap-4">
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
              />
            </div>

            <div>
              <label for="priority" class="block text-sm font-medium text-gray-700 mb-1">
                Priority *
              </label>
              <select
                id="priority"
                v-model="form.priority"
                required
                class="input-field"
              >
                <option value="">Select priority</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
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
              <option value="pending">Pending</option>
              <option value="in-progress">In Progress</option>
              <option value="completed">Completed</option>
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
            class="btn-primary"
          >
            {{ task?.id ? 'Update Task' : 'Create Task' }}
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
      project: '',
      assignee: '',
      dueDate: '',
      priority: '',
      status: 'pending'
    })

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
          project: '',
          assignee: '',
          dueDate: '',
          priority: '',
          status: 'pending'
        }
      }
    }, { immediate: true })

    const saveTask = () => {
      // Validate required fields
      if (!form.value.title || !form.value.project || !form.value.assignee || !form.value.dueDate || !form.value.priority) {
        alert('Please fill in all required fields')
        return
      }

      const taskData = {
        ...form.value,
        id: props.task?.id || null,
        dueDate: new Date(form.value.dueDate).toISOString(),
        activities: props.task?.activities || [],
        comments: props.task?.comments || []
      }

      emit('save', taskData)
    }

    return {
      form,
      saveTask
    }
  }
}
</script>
