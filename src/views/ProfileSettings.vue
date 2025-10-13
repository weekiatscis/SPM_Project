<template>
  <div class="profile-settings-container">
    <a-card title="Profile Settings" :bordered="false">
      <!-- Edit Button -->
      <template #extra>
        <a-button
          v-if="!isEditing"
          type="primary"
          @click="startEditing"
          :icon="h(EditOutlined)"
        >
          Edit
        </a-button>
      </template>

      <a-form
        :model="formState"
        :rules="rules"
        layout="vertical"
        @finish="handleSubmit"
        ref="formRef"
      >
        <!-- Display Name Field -->
        <a-form-item
          label="Full Name"
          name="displayName"
          :validate-status="validationStatus.displayName"
          :help="validationHelp.displayName"
        >
          <a-input
            v-model:value="formState.displayName"
            placeholder="Enter your full name"
            :maxlength="PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH + 10"
            @blur="handleDisplayNameBlur"
            @input="handleDisplayNameInput"
            size="large"
            :disabled="!isEditing"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
          <div v-if="isEditing" class="character-count">
            {{ trimmedDisplayNameLength }} / {{ PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH }} characters
          </div>
        </a-form-item>

        <!-- Email Field (Read-only) -->
        <a-form-item label="Email Address">
          <a-input
            :value="user?.email"
            disabled
            placeholder="Email address"
            size="large"
          >
            <template #prefix>
              <MailOutlined />
            </template>
          </a-input>
          <div class="field-hint">Email cannot be changed</div>
        </a-form-item>

        <!-- Role Field (Read-only) -->
        <a-form-item label="Role">
          <a-input
            :value="user?.role"
            disabled
            placeholder="Role"
            size="large"
          >
            <template #prefix>
              <IdcardOutlined />
            </template>
          </a-input>
          <div class="field-hint">Role cannot be changed</div>
        </a-form-item>

        <!-- Department Field (Read-only) -->
        <a-form-item label="Department">
          <a-input
            :value="user?.department"
            disabled
            placeholder="Department"
            size="large"
          >
            <template #prefix>
              <BankOutlined />
            </template>
          </a-input>
          <div class="field-hint">Department cannot be changed</div>
        </a-form-item>

        <!-- Superior Field (Read-only) -->
        <a-form-item label="Reporting To">
          <a-input
            :value="superiorName"
            disabled
            placeholder="No superior assigned"
            size="large"
          >
            <template #prefix>
              <TeamOutlined />
            </template>
          </a-input>
          <div class="field-hint">
            <span v-if="loading">Loading superior information...</span>
            <span v-else>Superior cannot be changed</span>
          </div>
        </a-form-item>

        <!-- Action Buttons - Only show when editing -->
        <a-form-item v-if="isEditing">
          <a-space>
            <a-button
              type="primary"
              html-type="submit"
              :loading="loading"
              :disabled="!hasChanges || loading"
            >
              Save Changes
            </a-button>
            <a-button
              @click="handleCancel"
              :disabled="loading"
            >
              Cancel
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- Unsaved Changes Modal -->
    <a-modal
      v-model:open="showCancelModal"
      title="Unsaved Changes"
      @ok="confirmCancel"
      @cancel="showCancelModal = false"
      okText="Discard Changes"
      cancelText="Keep Editing"
    >
      <p>You have unsaved changes. Are you sure you want to discard them?</p>
    </a-modal>
  </div>
</template>

<script>
import { ref, computed, reactive, watch, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import {
  UserOutlined,
  MailOutlined,
  IdcardOutlined,
  BankOutlined,
  TeamOutlined,
  EditOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'
import {
  validateDisplayName,
  sanitizeDisplayName,
  PROFILE_CONSTRAINTS,
} from '../utils/profileValidation.js'

export default {
  name: 'ProfileSettings',
  components: {
    UserOutlined,
    MailOutlined,
    IdcardOutlined,
    BankOutlined,
    TeamOutlined,
    EditOutlined,
  },
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()
    const formRef = ref()
    const loading = ref(false)
    const showCancelModal = ref(false)
    const superiorInfo = ref(null)
    const isEditing = ref(false)

    // Get user from auth store
    const user = computed(() => authStore.user)

    // Form state
    const formState = reactive({
      displayName: '',
    })

    // Original values for change detection
    const originalValues = reactive({
      displayName: '',
    })

    // Fetch superior information
    const fetchSuperiorInfo = async (superiorId) => {
      if (!superiorId) {
        superiorInfo.value = null
        return
      }

      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users/${superiorId}`)

        if (response.ok) {
          const data = await response.json()
          superiorInfo.value = data.user
        } else if (response.status === 404) {
          // Superior user not found - this is okay, just show as not assigned
          console.warn(`Superior user ${superiorId} not found`)
          superiorInfo.value = { name: 'Not found', role: '' }
        } else {
          console.error('Failed to fetch superior info')
          superiorInfo.value = null
        }
      } catch (error) {
        console.error('Error fetching superior info:', error)
        superiorInfo.value = null
      }
    }

    // Computed: Superior name
    const superiorName = computed(() => {
      if (!user.value?.superior) {
        return 'No superior assigned'
      }
      if (superiorInfo.value) {
        return `${superiorInfo.value.name} (${superiorInfo.value.role})`
      }
      return 'Loading...'
    })

    // Initialize form with user data
    onMounted(() => {
      if (user.value) {
        formState.displayName = user.value.name || ''
        originalValues.displayName = user.value.name || ''

        // Fetch superior info if exists
        if (user.value.superior) {
          fetchSuperiorInfo(user.value.superior)
        }
      }
    })

    // Watch for user changes (in case it loads after mount)
    watch(user, (newUser) => {
      if (newUser) {
        if (!formState.displayName) {
          formState.displayName = newUser.name || ''
          originalValues.displayName = newUser.name || ''
        }

        // Fetch superior info if exists
        if (newUser.superior) {
          fetchSuperiorInfo(newUser.superior)
        }
      }
    })

    // Computed: Trimmed display name length
    const trimmedDisplayNameLength = computed(() => {
      return formState.displayName ? formState.displayName.trim().length : 0
    })

    // Computed: Check if there are unsaved changes
    const hasChanges = computed(() => {
      return formState.displayName !== originalValues.displayName
    })

    // Validation status
    const validationStatus = reactive({
      displayName: '',
    })

    const validationHelp = reactive({
      displayName: '',
    })

    // Form validation rules
    const rules = {
      displayName: [
        {
          required: true,
          validator: async (rule, value) => {
            const validation = validateDisplayName(value)
            if (!validation.valid) {
              throw new Error(validation.error)
            }
          },
          trigger: 'change',
        },
      ],
    }

    // Handle display name input (real-time validation)
    const handleDisplayNameInput = () => {
      // Clear previous validation on input
      validationStatus.displayName = ''
      validationHelp.displayName = ''

      // Check length in real-time
      const trimmedLength = trimmedDisplayNameLength.value
      if (trimmedLength > PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH) {
        validationStatus.displayName = 'error'
        validationHelp.displayName = `Display name must not exceed ${PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH} characters`
      }
    }

    // Handle display name blur (validate on blur)
    const handleDisplayNameBlur = () => {
      if (!isEditing.value) return

      const validation = validateDisplayName(formState.displayName)
      if (!validation.valid) {
        validationStatus.displayName = 'error'
        validationHelp.displayName = validation.error
      } else {
        validationStatus.displayName = 'success'
        validationHelp.displayName = ''
      }
    }

    // Start editing mode
    const startEditing = () => {
      isEditing.value = true
    }

    // Handle form submission
    const handleSubmit = async () => {
      try {
        loading.value = true

        // Validate form
        await formRef.value.validate()

        // Sanitize data (trim whitespace)
        const sanitizedDisplayName = sanitizeDisplayName(formState.displayName)

        // Call API to update profile - use user service endpoint
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users/${user.value.user_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.sessionToken}`,
          },
          body: JSON.stringify({
            name: sanitizedDisplayName,
          }),
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to update profile')
        }

        const data = await response.json()

        // Update local user data in auth store
        authStore.user = { ...authStore.user, name: sanitizedDisplayName }

        // Update original values to new values
        originalValues.displayName = sanitizedDisplayName
        formState.displayName = sanitizedDisplayName

        // Exit editing mode
        isEditing.value = false

        // Clear validation
        validationStatus.displayName = ''
        validationHelp.displayName = ''

        // Show success message
        message.success('Profile updated successfully')
      } catch (error) {
        console.error('Profile update error:', error)

        // Handle validation errors
        if (error.errorFields) {
          message.error('Please fix the errors in the form')
        } else {
          message.error(error.message || 'Failed to update profile')
        }
      } finally {
        loading.value = false
      }
    }

    // Handle cancel button
    const handleCancel = () => {
      if (hasChanges.value) {
        // Show confirmation modal if there are unsaved changes
        showCancelModal.value = true
      } else {
        // Exit editing mode without changes
        isEditing.value = false
        validationStatus.displayName = ''
        validationHelp.displayName = ''
      }
    }

    // Confirm cancel and discard changes
    const confirmCancel = () => {
      // Reset form to original values
      formState.displayName = originalValues.displayName

      // Clear validation
      validationStatus.displayName = ''
      validationHelp.displayName = ''

      // Exit editing mode
      isEditing.value = false

      // Close modal
      showCancelModal.value = false
    }

    return {
      formRef,
      formState,
      user,
      loading,
      showCancelModal,
      hasChanges,
      trimmedDisplayNameLength,
      validationStatus,
      validationHelp,
      rules,
      PROFILE_CONSTRAINTS,
      superiorName,
      isEditing,
      startEditing,
      handleSubmit,
      handleCancel,
      confirmCancel,
      handleDisplayNameBlur,
      handleDisplayNameInput,
      h,
    }
  },
}
</script>

<style scoped>
.profile-settings-container {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
}

.character-count {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
  text-align: right;
}

.field-hint {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}
</style>
