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
          :validate-status="errors.project_name ? 'error' : ''"
          :help="errors.project_name"
          required
        >
          <a-input
            v-model:value="form.project_name"
            size="large"
            placeholder="e.g., Website Redesign, Q1 Marketing Campaign"
            :prefix="h(EditOutlined)"
            class="custom-input"
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
            format="YYYY-MM-DD"
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

        <!-- Created By (Read-only for new projects) -->
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
          :disabled="isLoading"
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
  CheckOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'

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
    CheckOutlined
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
    const form = ref({
      project_name: '',
      project_description: '',
      due_date: '',
      created_by: ''
    })

    const errors = ref({
      project_name: '',
      due_date: ''
    })

    const isLoading = ref(false)
    const modalVisible = ref(false)

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

    // Handle close modal
    const handleClose = () => {
      modalVisible.value = false
      emit('close')
    }

    // Watch for project changes to populate form
    watch(() => props.project, (newProject) => {
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
          due_date: ''
        }
      }
    }, { immediate: true })

    const saveProject = async () => {
      // Reset errors
      errors.value = {
        project_name: '',
        due_date: ''
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

      if (hasErrors) {
        return
      }

      isLoading.value = true

      try {
        // If editing existing project, call update API
        if (props.project?.project_id) {
          const updateProjectUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
          const payload = {
            project_name: form.value.project_name.trim(),
            project_description: form.value.project_description?.trim() || '',
            due_date: form.value.due_date,
            created_by: form.value.created_by?.trim() || 'Unknown'
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
          emit('save', updatedProjectData)
          return
        }

        // For new project, call createProject microservice
        const createProjectUrl = import.meta.env.VITE_CREATE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const payload = {
          project_name: form.value.project_name.trim(),
          project_description: form.value.project_description?.trim() || '',
          due_date: form.value.due_date,
          created_by: currentUserId.value, // Use current user's ID
          owner_id: currentUserId.value // Also set owner_id to current user
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
          due_date: '',
          created_by: ''
        }

        // Reset errors
        errors.value = {
          project_name: '',
          due_date: ''
        }

        // Emit success with the created project data
        emit('save', result.project)

        // Show success notification
        notification.success({
          message: 'Project Created',
          description: `${result.project.project_name} has been created successfully.`,
          placement: 'topRight',
          duration: 3
        })

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
      handleClose
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
</style>