<template>
  <div>
    <!-- Logo Section -->
    <div class="logo-section">
      <img src="/taskio-logo.svg" alt="Taskio" class="taskio-logo" />
      <h1 class="welcome-title">Create New Password</h1>
      <p class="welcome-subtitle">Enter your new password below</p>
    </div>

    <!-- Reset Password Form -->
    <form @submit.prevent="handleSubmit" class="reset-password-form">
      <!-- New Password Input -->
      <div class="form-group">
        <label class="form-label">New Password</label>
        <div class="input-wrapper">
          <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <input
            v-model="form.newPassword"
            :type="showNewPassword ? 'text' : 'password'"
            placeholder="Enter new password"
            class="form-input"
            :class="{ 'input-error': errorMessage }"
            :disabled="isLoading"
            autocomplete="new-password"
            @input="handlePasswordInput"
          />
          <button
            type="button"
            @click="showNewPassword = !showNewPassword"
            class="password-toggle"
            :disabled="isLoading"
          >
            <svg v-if="!showNewPassword" class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <svg v-else class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Password Strength Indicator -->
      <div v-if="form.newPassword" class="password-strength">
        <div class="strength-bar">
          <div
            class="strength-fill"
            :style="{
              width: `${passwordStrength}%`,
              backgroundColor: strengthColor
            }"
          ></div>
        </div>
        <p class="strength-label" :style="{ color: strengthColor }">
          {{ strengthLabel }}
        </p>
      </div>

      <!-- Password Requirements -->
      <div class="requirements-section">
        <p class="requirements-title">Password must contain:</p>
        <ul class="requirements-list">
          <li
            v-for="(req, index) in passwordRequirements"
            :key="index"
            :class="{ 'requirement-met': req.met }"
          >
            <svg class="requirement-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                v-if="req.met"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
              <circle
                v-else
                cx="12"
                cy="12"
                r="9"
                stroke-width="2"
              />
            </svg>
            {{ req.text }}
          </li>
        </ul>
      </div>

      <!-- Confirm Password Input -->
      <div class="form-group">
        <label class="form-label">Confirm Password</label>
        <div class="input-wrapper">
          <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <input
            v-model="form.confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            placeholder="Confirm new password"
            class="form-input"
            :class="{ 'input-error': errorMessage }"
            :disabled="isLoading"
            autocomplete="new-password"
          />
          <button
            type="button"
            @click="showConfirmPassword = !showConfirmPassword"
            class="password-toggle"
            :disabled="isLoading"
          >
            <svg v-if="!showConfirmPassword" class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <svg v-else class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="error-message">
        <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ errorMessage }}</span>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        class="submit-button"
        :class="{ 'button-loading': isLoading }"
        :disabled="isLoading"
      >
        <span v-if="!isLoading">Reset Password</span>
        <span v-else class="loading-content">
          <svg class="spinner" viewBox="0 0 24 24">
            <circle class="spinner-circle" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
          </svg>
          Resetting...
        </span>
      </button>
    </form>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  validatePasswordStrength,
  validatePasswordMatch,
  getPasswordStrength,
  getPasswordStrengthLabel,
  checkPasswordRequirements
} from '../../utils/passwordValidation'

const API_BASE_URL = 'http://localhost:8086'

export default {
  name: 'ResetPasswordForm',
  setup() {
    const router = useRouter()
    const route = useRoute()

    const form = reactive({
      newPassword: '',
      confirmPassword: ''
    })

    const isLoading = ref(false)
    const errorMessage = ref('')
    const showNewPassword = ref(false)
    const showConfirmPassword = ref(false)

    // Get reset token from URL
    const resetToken = computed(() => route.query.token || '')

    // Password strength
    const passwordStrength = computed(() => getPasswordStrength(form.newPassword))
    const strengthInfo = computed(() => getPasswordStrengthLabel(passwordStrength.value))
    const strengthLabel = computed(() => strengthInfo.value.label)
    const strengthColor = computed(() => strengthInfo.value.color)

    // Password requirements
    const passwordRequirements = computed(() => checkPasswordRequirements(form.newPassword))

    const handlePasswordInput = () => {
      // Clear error when user starts typing
      errorMessage.value = ''
    }

    const handleSubmit = async () => {
      // Reset error
      errorMessage.value = ''

      // Validate inputs
      if (!form.newPassword || !form.confirmPassword) {
        errorMessage.value = 'Please fill in all fields'
        return
      }

      // Validate password strength
      const strengthValidation = validatePasswordStrength(form.newPassword)
      if (!strengthValidation.isValid) {
        errorMessage.value = strengthValidation.errors[0]
        return
      }

      // Validate password match
      const matchValidation = validatePasswordMatch(form.newPassword, form.confirmPassword)
      if (!matchValidation.isValid) {
        errorMessage.value = matchValidation.error
        return
      }

      // Validate reset token
      if (!resetToken.value) {
        errorMessage.value = 'Invalid reset link. Please request a new password reset.'
        return
      }

      isLoading.value = true

      try {
        const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            token: resetToken.value,
            new_password: form.newPassword
          }),
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.error || 'Failed to reset password')
        }

        // Show success message
        message.success('Password reset successful! You can now log in with your new password.')

        // Redirect to login after 2 seconds
        setTimeout(() => {
          router.push({ name: 'Login' })
        }, 2000)

      } catch (error) {
        errorMessage.value = error.message || 'Failed to reset password. Please try again.'
        message.error(errorMessage.value)
      } finally {
        isLoading.value = false
      }
    }

    return {
      form,
      isLoading,
      errorMessage,
      showNewPassword,
      showConfirmPassword,
      passwordStrength,
      strengthLabel,
      strengthColor,
      passwordRequirements,
      handlePasswordInput,
      handleSubmit
    }
  }
}
</script>

<style scoped>
/* Logo Section */
.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 32px;
  width: 100%;
}

.taskio-logo {
  height: 42px;
  width: auto;
  margin: 0 auto 24px auto;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
  animation: logoFloat 3s ease-in-out infinite;
  display: block;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 8px 0;
  letter-spacing: -0.03em;
}

.welcome-subtitle {
  font-size: 15px;
  color: #86868b;
  margin: 0;
  font-weight: 450;
}

/* Form */
.reset-password-form {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 550;
  color: #1d1d1f;
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}

/* Input Wrapper */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  width: 20px;
  height: 20px;
  color: #86868b;
  pointer-events: none;
  z-index: 1;
}

.form-input {
  width: 100%;
  height: 52px;
  padding: 0 48px;
  font-size: 15px;
  color: #1d1d1f;
  background: rgba(255, 255, 255, 0.6);
  border: 1.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 14px;
  outline: none;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  font-weight: 450;
}

.form-input::placeholder {
  color: #a1a1a6;
}

.form-input:hover {
  border-color: rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.75);
}

.form-input:focus {
  border-color: #007aff;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-error {
  border-color: #ff3b30 !important;
}

.input-error:focus {
  box-shadow: 0 0 0 4px rgba(255, 59, 48, 0.1) !important;
}

/* Password Toggle */
.password-toggle {
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.password-toggle:hover {
  background: rgba(0, 0, 0, 0.05);
}

.password-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-icon {
  width: 20px;
  height: 20px;
  color: #86868b;
}

/* Password Strength */
.password-strength {
  margin-bottom: 20px;
}

.strength-bar {
  width: 100%;
  height: 6px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
  border-radius: 3px;
}

.strength-label {
  font-size: 12px;
  font-weight: 600;
  margin: 0;
  text-align: right;
}

/* Requirements Section */
.requirements-section {
  background: rgba(0, 0, 0, 0.03);
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 20px;
}

.requirements-title {
  font-size: 12px;
  font-weight: 600;
  color: #86868b;
  margin: 0 0 10px 0;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.requirements-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.requirements-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #86868b;
  margin-bottom: 8px;
  transition: color 0.3s ease;
}

.requirements-list li:last-child {
  margin-bottom: 0;
}

.requirements-list li.requirement-met {
  color: #34c759;
}

.requirement-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.2);
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #ff3b30;
  font-weight: 500;
  animation: errorShake 0.4s ease;
}

@keyframes errorShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
}

.error-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* Submit Button */
.submit-button {
  width: 100%;
  height: 52px;
  background: #007aff;
  color: #ffffff;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.submit-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.submit-button:hover {
  background: #0051d5;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.4);
}

.submit-button:hover::before {
  opacity: 1;
}

.submit-button:active {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.button-loading {
  pointer-events: none;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.spinner {
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

.spinner-circle {
  stroke-dasharray: 60;
  stroke-dashoffset: 45;
  animation: spinCircle 1.5s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes spinCircle {
  0% { stroke-dashoffset: 60; }
  50% { stroke-dashoffset: 15; }
  100% { stroke-dashoffset: 60; }
}

/* Responsive */
@media (max-width: 480px) {
  .taskio-logo {
    height: 36px;
    margin-bottom: 20px;
  }

  .welcome-title {
    font-size: 28px;
  }

  .welcome-subtitle {
    font-size: 14px;
  }

  .form-input,
  .submit-button {
    height: 48px;
  }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .welcome-title {
    color: #f5f5f7;
  }

  .welcome-subtitle {
    color: #98989d;
  }

  .form-label {
    color: #f5f5f7;
  }

  .form-input {
    color: #f5f5f7;
    background: rgba(58, 58, 60, 0.6);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .form-input:hover {
    background: rgba(58, 58, 60, 0.75);
    border-color: rgba(255, 255, 255, 0.15);
  }

  .form-input:focus {
    background: rgba(58, 58, 60, 0.9);
  }

  .form-input::placeholder {
    color: #636366;
  }

  .requirements-section {
    background: rgba(255, 255, 255, 0.05);
  }
}
</style>
