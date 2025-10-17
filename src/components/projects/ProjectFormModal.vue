<template>
  <!-- Ant Design Modal -->
  <a-modal
    v-model:open="modalVisible"
    :title="null"
    :footer="null"
    :width="600"
    :closable="false"
    :maskClosable="false"
    @cancel="handleClose"
    class="project-modal"
  >
    <!-- Custom Header with Icon -->
    <div class="modal-header">
      <div class="header-content">
        <div class="icon-wrapper">
          <FolderOpenOutlined class="header-icon" />
        </div>
        <div class="header-text">
          <h3 class="modal-title">
            {{ project?.project_id ? 'Edit Project' : 'Create New Project' }}
          </h3>
          <p class="modal-subtitle">
            {{ project?.project_id ? 'Update project details and settings' : 'Set up a new project to organize your tasks' }}
          </p>
        </div>
      </div>
      <a-button
        type="text"
        @click="handleClose"
        class="close-button"
        :icon="h(CloseOutlined)"
      />
    </div>

    <!-- Form Content -->
    <div class="modal-body">
      <a-form
        :model="form"
        layout="vertical"
        @submit.prevent="saveProject"
        class="project-form"
      >
        <!-- Project Name -->
        <a-form-item
          label="Project Name"
          :validate-status="errors.project_name || isDuplicateName ? 'error' : isCheckingDuplicate ? 'validating' : ''"
          :help="errors.project_name || (isDuplicateName ? 'A project with this name already exists' : '')"
          required
        >
          <a-input
            v-model:value="form.project_name"
            size="large"
            placeholder="e.g., Website Redesign, Q1 Marketing Campaign"
            :prefix="h(EditOutlined)"
            class="custom-input"
            @input="onProjectNameInput"
          />
        </a-form-item>

        <!-- Project Description -->
        <a-form-item label="Description">
          <a-textarea
            v-model:value="form.project_description"
            :rows="4"
            placeholder="Describe the project objectives, scope, and key deliverables..."
            size="large"
            :maxlength="500"
            show-count
            class="custom-textarea"
          />
        </a-form-item>

        <!-- Due Date -->
        <a-form-item
          label="Project Completion Date"
          :validate-status="errors.due_date ? 'error' : ''"
          :help="errors.due_date"
          required
        >
          <a-date-picker
            v-model:value="dueDateValue"
            size="large"
            format="DD/MM/YYYY"
            :style="{ width: '100%' }"
            placeholder="Select target date"
            :disabled-date="disabledDate"
            class="custom-date-picker"
          >
            <template #suffixIcon>
              <CalendarOutlined />
            </template>
          </a-date-picker>
          <div class="date-hint">
            <ClockCircleOutlined class="hint-icon" />
            <span>Set a realistic deadline for project completion</span>
          </div>
        </a-form-item>

        <!-- Project Owner for New Projects (Read-only) -->
        <a-form-item
          v-if="!project?.project_id"
          label="Project Owner"
        >
          <a-input
            v-model:value="currentUserName"
            size="large"
            disabled
            :prefix="h(UserOutlined)"
            class="custom-input-disabled"
          />
          <div class="owner-info">
            <InfoCircleOutlined class="info-icon" />
            <span>You will be assigned as the project owner</span>
          </div>
        </a-form-item>

        <!-- Project Owner for Editing (Changeable) -->
        <a-form-item
          v-if="project?.project_id"
          label="Project Owner"
        >
          <a-select
            v-model:value="selectedOwnerId"
            size="large"
            placeholder="Select project owner"
            :prefix="h(UserOutlined)"
            class="custom-select"
          >
            <a-select-option
              v-for="user in allUsersIncludingOwner"
              :key="user.user_id"
              :value="user.user_id"
            >
              <div class="owner-option">
                <span>{{ user.name }}</span>
                <span class="owner-dept">{{ user.department }}</span>
              </div>
            </a-select-option>
          </a-select>
          <div class="owner-warning">
            <ExclamationCircleOutlined class="warning-icon" />
            <span>Changing the owner will transfer full control of this project</span>
          </div>
        </a-form-item>

        <!-- Collaborators Section -->
        <a-form-item
          label="Add Collaborators"
          :validate-status="errors.collaborators ? 'error' : ''"
          :help="errors.collaborators"
          required
        >
          <div class="collaborators-section">
            <!-- Filter and Search Controls -->
            <div class="filter-controls">
              <a-select
                v-model:value="departmentFilter"
                placeholder="Filter by Department"
                size="large"
                allow-clear
                style="width: 48%;"
                @change="filterUsers"
              >
                <a-select-option value="">All Departments</a-select-option>
                <a-select-option v-for="dept in departments" :key="dept" :value="dept">
                  {{ dept }}
                </a-select-option>
              </a-select>

              <a-input
                v-model:value="userSearchQuery"
                placeholder="Search by name..."
                size="large"
                allow-clear
                style="width: 48%;"
                @input="filterUsers"
              >
                <template #prefix>
                  <SearchOutlined />
                </template>
              </a-input>
            </div>

            <!-- Selected Collaborators -->
            <div v-if="selectedCollaborators.length > 0" class="selected-collaborators">
              <div class="selected-label">Selected ({{ selectedCollaborators.length }}):</div>
              <div class="selected-tags">
                <a-tag
                  v-for="user in selectedCollaborators"
                  :key="user.user_id"
                  closable
                  @close="removeCollaborator(user)"
                  color="purple"
                >
                  {{ user.name }} - {{ user.department }}
                </a-tag>
              </div>
            </div>

            <!-- Available Users List -->
            <div class="users-list">
              <a-spin v-if="isLoadingUsers" />
              <div v-else-if="filteredUsers.length === 0" class="no-users">
                No users found
              </div>
              <div v-else class="user-items">
                <div
                  v-for="user in filteredUsers"
                  :key="user.user_id"
                  class="user-item"
                  :class="{ selected: isUserSelected(user) }"
                  @click="toggleCollaborator(user)"
                >
                  <a-checkbox :checked="isUserSelected(user)" />
                  <div class="user-info">
                    <div class="user-name">{{ user.name }}</div>
                    <div class="user-department">{{ user.department }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-form-item>
      </a-form>
    </div>

    <!-- Modal Footer -->
    <div class="modal-footer">
      <a-space :size="12">
        <a-button
          size="large"
          @click="handleClose"
          class="cancel-btn"
        >
          Cancel
        </a-button>
        <a-button
          type="primary"
          size="large"
          @click="saveProject"
          :loading="isLoading"
          :disabled="isLoading || isDuplicateName || isCheckingDuplicate"
          class="submit-btn"
        >
          <template #icon>
            <CheckOutlined v-if="!isLoading" />
          </template>
          {{ project?.project_id ? 'Update Project' : 'Create Project' }}
        </a-button>
      </a-space>
    </div>
  </a-modal>
</template>

<script>
import { ref, watch, computed, h } from 'vue'
import { notification } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  FolderOpenOutlined,
  CloseOutlined,
  EditOutlined,
  CalendarOutlined,
  UserOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined,
  CheckOutlined,
  SearchOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { useProjectEvents } from '../../composables/useProjectEvents'

export default {
  name: 'ProjectFormModal',
  components: {
    FolderOpenOutlined,
    CloseOutlined,
    EditOutlined,
    CalendarOutlined,
    UserOutlined,
    InfoCircleOutlined,
    ClockCircleOutlined,
    CheckOutlined,
    SearchOutlined,
    ExclamationCircleOutlined
  },
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
    const authStore = useAuthStore()
    const { emitProjectCreated, emitProjectUpdated } = useProjectEvents()
    const form = ref({
      project_name: '',
      project_description: '',
      due_date: '',
      created_by: '',
      collaborators: []
    })

    const errors = ref({
      project_name: '',
      due_date: '',
      collaborators: ''
    })

    const isLoading = ref(false)
    const modalVisible = ref(false)

    // Collaborators state
    const allUsers = ref([])
    const filteredUsers = ref([])
    const selectedCollaborators = ref([])
    const departmentFilter = ref('')
    const userSearchQuery = ref('')
    const isLoadingUsers = ref(false)
    const departments = ref([])

    // Owner selection state
    const selectedOwnerId = ref('')
    const currentOwnerInfo = ref(null)

    // Duplicate name checking state
    const isDuplicateName = ref(false)
    const isCheckingDuplicate = ref(false)
    let duplicateCheckTimeout = null

    // Sync modalVisible with isOpen prop
    watch(() => props.isOpen, (newVal) => {
      modalVisible.value = newVal
    }, { immediate: true })

    // Get current user's name from auth store
    const currentUserName = computed(() => {
      return authStore.user?.name || 'Current User'
    })

    // Get current user's ID
    const currentUserId = computed(() => {
      return authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID
    })

    // All users including current owner for owner selection dropdown
    const allUsersIncludingOwner = computed(() => {
      const users = [...allUsers.value]

      // If editing and current owner info is loaded, add them if not already in list
      if (currentOwnerInfo.value && !users.some(u => u.user_id === currentOwnerInfo.value.user_id)) {
        users.unshift(currentOwnerInfo.value)
      }

      // Also add current user if not in list
      if (authStore.user && !users.some(u => u.user_id === currentUserId.value)) {
        users.unshift({
          user_id: currentUserId.value,
          name: authStore.user.name,
          department: authStore.user.department
        })
      }

      return users.sort((a, b) => a.name.localeCompare(b.name))
    })

    // Date picker value (using dayjs for Ant Design)
    const dueDateValue = computed({
      get: () => form.value.due_date ? dayjs(form.value.due_date) : null,
      set: (val) => {
        form.value.due_date = val ? val.format('YYYY-MM-DD') : ''
      }
    })

    // Disable dates before today
    const disabledDate = (current) => {
      return current && current < dayjs().startOf('day')
    }

    // Fetch all users from the user table
    const fetchUsers = async () => {
      isLoadingUsers.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/users`)

        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const payload = await response.json()
        const users = Array.isArray(payload?.users) ? payload.users : []

        // Filter out current user from the list
        allUsers.value = users.filter(u => u.user_id !== currentUserId.value)

        // Extract unique departments
        const deptSet = new Set(users.map(u => u.department).filter(Boolean))
        departments.value = Array.from(deptSet).sort()

        // Initialize filtered users and apply filters to exclude already selected collaborators
        filterUsers()
      } catch (error) {
        console.error('Failed to fetch users:', error)
        notification.error({
          message: 'Failed to load users',
          description: 'Unable to fetch users. Please try again.',
          placement: 'topRight',
          duration: 3
        })
      } finally {
        isLoadingUsers.value = false
      }
    }

    // Filter users based on department and search query
    const filterUsers = () => {
      let filtered = [...allUsers.value]

      // Filter by department
      if (departmentFilter.value) {
        filtered = filtered.filter(u => u.department === departmentFilter.value)
      }

      // Filter by search query
      if (userSearchQuery.value) {
        const query = userSearchQuery.value.toLowerCase()
        filtered = filtered.filter(u =>
          u.name.toLowerCase().includes(query)
        )
      }

      // Exclude already selected collaborators
      filtered = filtered.filter(u =>
        !selectedCollaborators.value.some(sc => sc.user_id === u.user_id)
      )

      filteredUsers.value = filtered
    }

    // Check if user is selected
    const isUserSelected = (user) => {
      return selectedCollaborators.value.some(u => u.user_id === user.user_id)
    }

    // Toggle collaborator selection
    const toggleCollaborator = (user) => {
      const index = selectedCollaborators.value.findIndex(u => u.user_id === user.user_id)

      if (index > -1) {
        selectedCollaborators.value.splice(index, 1)
      } else {
        selectedCollaborators.value.push(user)
      }

      filterUsers()
    }

    // Remove collaborator
    const removeCollaborator = (user) => {
      const index = selectedCollaborators.value.findIndex(u => u.user_id === user.user_id)
      if (index > -1) {
        selectedCollaborators.value.splice(index, 1)
        filterUsers()
      }
    }

    // Check for duplicate project names
    const checkDuplicateProjectName = async (projectName) => {
      if (!projectName || !projectName.trim()) {
        isDuplicateName.value = false
        return
      }

      // Skip check if editing existing project with same name
      if (props.project?.project_id && props.project?.project_name === projectName.trim()) {
        isDuplicateName.value = false
        return
      }

      isCheckingDuplicate.value = true

      try {
        const projectServiceUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const response = await fetch(`${projectServiceUrl}/projects`)

        if (!response.ok) {
          console.error('Failed to fetch projects for duplicate check')
          isDuplicateName.value = false
          return
        }

        const data = await response.json()
        const projects = data.projects || []

        // Check if project name already exists (case-insensitive)
        const duplicate = projects.some(p =>
          p.project_name.toLowerCase() === projectName.trim().toLowerCase() &&
          p.project_id !== props.project?.project_id
        )

        isDuplicateName.value = duplicate
      } catch (error) {
        console.error('Error checking duplicate project name:', error)
        isDuplicateName.value = false
      } finally {
        isCheckingDuplicate.value = false
      }
    }

    // Handle project name input with debounce
    const onProjectNameInput = () => {
      // Clear existing timeout
      if (duplicateCheckTimeout) {
        clearTimeout(duplicateCheckTimeout)
      }

      // Set new timeout for debounced check
      duplicateCheckTimeout = setTimeout(() => {
        checkDuplicateProjectName(form.value.project_name)
      }, 500) // Wait 500ms after user stops typing
    }

    // Handle close modal
    const handleClose = () => {
      modalVisible.value = false
      // Reset collaborator state
      selectedCollaborators.value = []
      departmentFilter.value = ''
      userSearchQuery.value = ''
      // Reset duplicate check state
      isDuplicateName.value = false
      isCheckingDuplicate.value = false
      if (duplicateCheckTimeout) {
        clearTimeout(duplicateCheckTimeout)
      }
      emit('close')
    }

    // Watch for modal open to fetch users
    watch(() => props.isOpen, async (newVal) => {
      if (newVal) {
        // If editing, load current owner info
        if (props.project?.project_id && props.project?.created_by_id) {
          selectedOwnerId.value = props.project.created_by_id

          try {
            const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
            const response = await fetch(`${taskServiceUrl}/users/${props.project.created_by_id}`)
            if (response.ok) {
              const data = await response.json()
              if (data.user) {
                currentOwnerInfo.value = data.user
              }
            }
          } catch (error) {
            console.error(`Failed to fetch owner info:`, error)
          }
        }

        // If editing a project with collaborators, load them first
        if (props.project?.collaborators && Array.isArray(props.project.collaborators)) {
          try {
            const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
            const collaboratorDetails = []

            // Fetch details for each collaborator
            for (const userId of props.project.collaborators) {
              try {
                const response = await fetch(`${taskServiceUrl}/users/${userId}`)
                if (response.ok) {
                  const data = await response.json()
                  if (data.user) {
                    collaboratorDetails.push(data.user)
                  }
                }
              } catch (error) {
                console.error(`Failed to fetch user ${userId}:`, error)
              }
            }

            selectedCollaborators.value = collaboratorDetails
          } catch (error) {
            console.error('Failed to load existing collaborators:', error)
          }
        } else {
          selectedCollaborators.value = []
        }

        // Now fetch all users, which will automatically exclude selected collaborators
        await fetchUsers()
      }
    })

    // Watch for project changes to populate form
    watch(() => props.project, async (newProject) => {
      if (newProject) {
        form.value = {
          project_name: newProject.project_name || '',
          project_description: newProject.project_description || '',
          due_date: newProject.due_date || '',
          created_by: newProject.created_by || ''
        }
      } else {
        // Reset form for new project
        form.value = {
          project_name: '',
          project_description: '',
          due_date: '',
          created_by: ''
        }
        // Reset errors
        errors.value = {
          project_name: '',
          due_date: '',
          collaborators: ''
        }
      }
    }, { immediate: true })

    const saveProject = async () => {
      // Reset errors
      errors.value = {
        project_name: '',
        due_date: '',
        collaborators: ''
      }

      // Validate required fields
      let hasErrors = false

      if (!form.value.project_name?.trim()) {
        errors.value.project_name = 'Project name is required'
        hasErrors = true
      }

      if (!form.value.due_date) {
        errors.value.due_date = 'Due date is required'
        hasErrors = true
      }

      if (selectedCollaborators.value.length === 0) {
        errors.value.collaborators = 'At least one collaborator is required'
        hasErrors = true
      }

      if (hasErrors) {
        return
      }

      isLoading.value = true

      try {
        // If editing existing project, call update API
        if (props.project?.project_id) {
          const updateProjectUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'

          // Handle ownership transfer
          let updatedCollaborators = selectedCollaborators.value.map(u => u.user_id)
          let newOwnerId = selectedOwnerId.value

          // If owner changed, manage collaborators list
          if (newOwnerId !== props.project.created_by_id) {
            // Remove new owner from collaborators if they're in the list
            updatedCollaborators = updatedCollaborators.filter(id => id !== newOwnerId)

            // Add old owner to collaborators if they're not already there
            if (!updatedCollaborators.includes(props.project.created_by_id)) {
              updatedCollaborators.push(props.project.created_by_id)
            }
          }

          const payload = {
            project_name: form.value.project_name.trim(),
            project_description: form.value.project_description?.trim() || '',
            due_date: form.value.due_date,
            created_by: newOwnerId, // Use selected owner
            user_id: currentUserId.value, // Add user_id for authorization
            collaborators: updatedCollaborators // Include updated collaborators
          }

          const response = await fetch(`${updateProjectUrl}/projects/${props.project.project_id}`, {
            method: 'PUT',
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

          // Emit success with the updated project data
          const updatedProjectData = {
            ...form.value,
            project_id: props.project.project_id
          }

          // Emit event to update sidebar
          emitProjectUpdated(updatedProjectData)

          emit('save', updatedProjectData)

          // Show success notification for update
          notification.success({
            message: 'Project Updated',
            description: `${result.project.project_name} has been updated successfully.`,
            placement: 'topRight',
            duration: 3
          })

          // Close modal
          handleClose()
          return
        }

        // For new project, call createProject microservice
        const createProjectUrl = import.meta.env.VITE_CREATE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const payload = {
          project_name: form.value.project_name.trim(),
          project_description: form.value.project_description?.trim() || '',
          due_date: form.value.due_date,
          created_by: currentUserId.value, // Use current user's ID
          owner_id: currentUserId.value, // Also set owner_id to current user
          collaborators: selectedCollaborators.value.map(u => u.user_id) // Add collaborator user IDs
        }

        console.log('DEBUG: Sending request to:', `${createProjectUrl}/projects`)
        console.log('DEBUG: Payload:', JSON.stringify(payload, null, 2))

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
          due_date: '',
          created_by: '',
          collaborators: []
        }

        // Reset collaborators
        selectedCollaborators.value = []
        departmentFilter.value = ''
        userSearchQuery.value = ''

        // Reset errors
        errors.value = {
          project_name: '',
          due_date: '',
          collaborators: ''
        }

        // Emit event to update sidebar
        emitProjectCreated(result.project)

        // Emit success with the created project data
        emit('save', result.project)

        // Show success notification
        notification.success({
          message: 'Project Created',
          description: `${result.project.project_name} has been created successfully.`,
          placement: 'topRight',
          duration: 3
        })

        // Close modal
        handleClose()

      } catch (error) {
        console.error('Failed to create project:', error)
        notification.error({
          message: 'Failed to Create Project',
          description: error.message || 'An error occurred while creating the project.',
          placement: 'topRight',
          duration: 4
        })
      } finally {
        isLoading.value = false
      }
    }

    return {
      h,
      form,
      errors,
      isLoading,
      saveProject,
      currentUserName,
      currentUserId,
      modalVisible,
      dueDateValue,
      disabledDate,
      handleClose,
      // Owner-related
      selectedOwnerId,
      allUsersIncludingOwner,
      // Collaborator-related
      filteredUsers,
      selectedCollaborators,
      departmentFilter,
      userSearchQuery,
      isLoadingUsers,
      departments,
      filterUsers,
      isUserSelected,
      toggleCollaborator,
      removeCollaborator,
      // Duplicate check-related
      isDuplicateName,
      isCheckingDuplicate,
      onProjectNameInput
    }
  }
}
</script>

<style scoped>
/* Modal Header */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 24px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex: 1;
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.header-icon {
  font-size: 24px;
  color: white;
}

.header-text {
  flex: 1;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: white;
  line-height: 1.3;
}

.modal-subtitle {
  margin: 4px 0 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
}

.close-button {
  color: white !important;
  margin-top: -4px;
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.2) !important;
}

/* Modal Body */
.modal-body {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.project-form {
  margin: 0;
}

/* Form Labels */
:deep(.ant-form-item-label > label) {
  font-weight: 600;
  color: #262626;
  font-size: 14px;
}

:deep(.ant-form-item-label > label.ant-form-item-required:not(.ant-form-item-required-mark-optional)::before) {
  color: #ff4d4f;
}

/* Custom Inputs */
:deep(.custom-input) {
  border-radius: 8px;
  border: 1.5px solid #d9d9d9;
  transition: all 0.3s ease;
}

:deep(.custom-input:hover) {
  border-color: #667eea;
}

:deep(.custom-input:focus),
:deep(.custom-input.ant-input-affix-wrapper-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

:deep(.custom-input .ant-input) {
  border: none;
  box-shadow: none;
}

:deep(.custom-input .ant-input:focus) {
  border: none;
  box-shadow: none;
}

.custom-textarea :deep(.ant-input) {
  border-radius: 8px;
  border: 1.5px solid #d9d9d9;
  transition: all 0.3s ease;
}

.custom-textarea :deep(.ant-input:hover) {
  border-color: #667eea;
}

.custom-textarea :deep(.ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

/* Date Picker */
.custom-date-picker :deep(.ant-picker) {
  border-radius: 8px;
  border: 1.5px solid #d9d9d9;
  transition: all 0.3s ease;
}

.custom-date-picker :deep(.ant-picker:hover) {
  border-color: #667eea;
}

.custom-date-picker :deep(.ant-picker-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.date-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: #8c8c8c;
}

.hint-icon {
  font-size: 14px;
  color: #1890ff;
}

/* Disabled Input (Owner) */
:deep(.custom-input-disabled) {
  background: #f5f5f5;
  border: 1.5px solid #e8e8e8;
  border-radius: 8px;
  cursor: not-allowed;
}

:deep(.custom-input-disabled .ant-input[disabled]) {
  background: transparent;
  border: none;
  color: #595959;
  cursor: not-allowed;
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  border-radius: 6px;
  font-size: 12px;
  color: #0958d9;
}

.info-icon {
  font-size: 14px;
  color: #1890ff;
}

/* Owner Select Dropdown */
:deep(.custom-select .ant-select-selector) {
  border-radius: 8px !important;
  border: 1.5px solid #d9d9d9 !important;
  transition: all 0.3s ease !important;
  height: 40px !important;
  padding: 4px 11px !important;
}

:deep(.custom-select .ant-select-selector:hover) {
  border-color: #667eea !important;
}

:deep(.custom-select.ant-select-focused .ant-select-selector) {
  border-color: #667eea !important;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
}

.owner-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.owner-dept {
  font-size: 12px;
  color: #8c8c8c;
  margin-left: 8px;
}

.owner-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fff7e6;
  border-radius: 6px;
  font-size: 12px;
  color: #d46b08;
}

.owner-warning .warning-icon {
  font-size: 14px;
  color: #fa8c16;
}

/* Modal Footer */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
  display: flex;
  justify-content: flex-end;
}

.cancel-btn {
  border-radius: 8px;
  font-weight: 500;
  border: 1.5px solid #d9d9d9;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.submit-btn {
  border-radius: 8px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.submit-btn:hover {
  background: linear-gradient(135deg, #5568d3 0%, #63408a 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  background: #d9d9d9;
  box-shadow: none;
}

/* Scrollbar Styling */
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-header {
    padding: 20px 16px 16px;
  }

  .icon-wrapper {
    width: 40px;
    height: 40px;
  }

  .header-icon {
    font-size: 20px;
  }

  .modal-title {
    font-size: 18px;
  }

  .modal-subtitle {
    font-size: 13px;
  }

  .modal-body {
    padding: 20px 16px;
  }

  .modal-footer {
    padding: 12px 16px;
  }
}

/* Collaborators Section */
.collaborators-section {
  border: 1px solid rgba(215, 143, 238, 0.2);
  border-radius: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.5);
}

.filter-controls {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.selected-collaborators {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(215, 143, 238, 0.08);
  border-radius: 8px;
  border: 1px solid rgba(215, 143, 238, 0.15);
}

.selected-label {
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.users-list {
  max-height: 250px;
  overflow-y: auto;
  border: 1px solid rgba(215, 143, 238, 0.15);
  border-radius: 8px;
  padding: 8px;
  background: white;
}

.no-users {
  text-align: center;
  padding: 32px;
  color: #9CA3AF;
  font-size: 14px;
}

.user-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.user-item:hover {
  background: rgba(215, 143, 238, 0.08);
  border-color: rgba(215, 143, 238, 0.2);
}

.user-item.selected {
  background: rgba(215, 143, 238, 0.12);
  border-color: rgba(215, 143, 238, 0.3);
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #1F2937;
  margin-bottom: 2px;
}

.user-department {
  font-size: 12px;
  color: #6B7280;
}

.users-list::-webkit-scrollbar {
  width: 6px;
}

.users-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.users-list::-webkit-scrollbar-thumb {
  background: #D78FEE;
  border-radius: 3px;
}

.users-list::-webkit-scrollbar-thumb:hover {
  background: #C77FDE;
}
</style>