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
              {{ project?.project_id ? 'Edit Project' : 'Create New Project' }}
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
        <form @submit.prevent="saveProject" class="bg-white px-6 py-4 space-y-4">
          <!-- Project Name -->
          <div>
            <label for="project_name" class="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              id="project_name"
              v-model="form.project_name"
              type="text"
              required
              class="input-field"
              :class="{ 'border-red-500': errors.project_name }"
              placeholder="Enter project name"
            />
            <div v-if="errors.project_name" class="mt-1 text-sm text-red-600">
              {{ errors.project_name }}
            </div>
          </div>

          <!-- Project Description -->
          <div>
            <label for="project_description" class="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="project_description"
              v-model="form.project_description"
              rows="3"
              class="input-field"
              placeholder="Enter project description"
            ></textarea>
          </div>

          <!-- Created By -->
          <div>
            <label for="created_by" class="block text-sm font-medium text-gray-700 mb-1">
              Created By
            </label>
            <input
              id="created_by"
              v-model="form.created_by"
              type="text"
              class="input-field"
              placeholder="Enter creator name"
            />
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
            @click="saveProject"
            :disabled="isLoading"
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLoading ? 'Creating...' : (project?.project_id ? 'Update Project' : 'Create Project') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'ProjectFormModal',
  props: {
    project: {
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
      project_name: '',
      project_description: '',
      created_by: ''
    })

    const errors = ref({
      project_name: ''
    })

    const isLoading = ref(false)

    // Watch for project changes to populate form
    watch(() => props.project, (newProject) => {
      if (newProject) {
        form.value = {
          project_name: newProject.project_name || '',
          project_description: newProject.project_description || '',
          created_by: newProject.created_by || ''
        }
      } else {
        // Reset form for new project
        form.value = {
          project_name: '',
          project_description: '',
          created_by: ''
        }
        // Reset errors
        errors.value = {
          project_name: ''
        }
      }
    }, { immediate: true })

    const saveProject = async () => {
      // Reset errors
      errors.value = {
        project_name: ''
      }

      // Validate required fields
      let hasErrors = false

      if (!form.value.project_name?.trim()) {
        errors.value.project_name = 'Project name is required'
        hasErrors = true
      }

      if (hasErrors) {
        return
      }

      isLoading.value = true

      try {
        // If editing existing project, emit to parent (update functionality to be implemented)
        if (props.project?.project_id) {
          const projectData = {
            ...form.value,
            project_id: props.project.project_id
          }
          emit('save', projectData)
          return
        }

        // For new project, call createProject microservice
        const createProjectUrl = import.meta.env.VITE_CREATE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const payload = {
          project_name: form.value.project_name.trim(),
          project_description: form.value.project_description?.trim() || '',
          created_by: form.value.created_by?.trim() || 'Unknown',
          owner_id: import.meta.env.VITE_TASK_OWNER_ID
        }

        const response = await fetch(`${createProjectUrl}/projects`, {
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
          project_name: '',
          project_description: '',
          created_by: ''
        }

        // Reset errors
        errors.value = {
          project_name: ''
        }

        // Emit success with the created project data
        emit('save', result.project)

        // Show success message
        console.log('Project created successfully:', result.project)

      } catch (error) {
        console.error('Failed to create project:', error)
        alert(`Failed to create project: ${error.message}`)
      } finally {
        isLoading.value = false
      }
    }

    return {
      form,
      errors,
      isLoading,
      saveProject
    }
  }
}
</script>

<style scoped>
.input-field {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
}

.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors;
}
</style>