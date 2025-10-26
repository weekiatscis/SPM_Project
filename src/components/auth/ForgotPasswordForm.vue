<template>
  <div>
    <!-- Logo Section -->
    <div class="logo-section">
      <img src="/taskio-logo.svg" alt="Taskio" class="taskio-logo" />
      <h1 class="welcome-title">Reset Password</h1>
      <p class="welcome-subtitle">Enter your email to receive a password reset link</p>
    </div>

    <!-- Success Message (shown after email sent) -->
    <div v-if="emailSent" class="success-message">
      <svg class="success-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div>
        <p class="success-title">Check your email</p>
        <p class="success-text">
          We've sent a password reset link to <strong>{{ form.email }}</strong>.
          The link will expire in 15 minutes.
        </p>
      </div>
    </div>

    <!-- Forgot Password Form -->
    <form v-if="!emailSent" @submit.prevent="handleSubmit" class="forgot-password-form">
      <!-- Email Input -->
      <div class="form-group">
        <label class="form-label">Email Address</label>
        <div class="input-wrapper">
          <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <input
            v-model="form.email"
            type="email"
            placeholder="you@example.com"
            class="form-input"
            :class="{ 'input-error': errorMessage }"
            :disabled="isLoading"
            autocomplete="email"
          />
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
          Sending...
        </span>
      </button>
    </form>

    <!-- Back to Login Button -->
    <div class="footer">
      <button @click="$emit('back-to-login')" class="back-button">
        <svg class="back-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Login
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { validateEmail } from '../../utils/passwordValidation'

const API_BASE_URL = 'http://localhost:8086'

export default {
  name: 'ForgotPasswordForm',
  emits: ['back-to-login'],
  setup() {
    const form = reactive({
      email: ''
    })

    const isLoading = ref(false)
    const errorMessage = ref('')
    const emailSent = ref(false)

    const handleSubmit = async () => {
      // Reset error
      errorMessage.value = ''

      // Validate email
      if (!form.email) {
        errorMessage.value = 'Please enter your email address'
        return
      }

      if (!validateEmail(form.email)) {
        errorMessage.value = 'Please enter a valid email address'
        return
      }

      isLoading.value = true

      try {
        const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: form.email.toLowerCase().trim()
          }),
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.error || 'Failed to send reset email')
        }

        // Show success message
        emailSent.value = true

      } catch (error) {
        errorMessage.value = error.message || 'Failed to send reset email. Please try again.'
      } finally {
        isLoading.value = false
      }
    }

    return {
      form,
      isLoading,
      errorMessage,
      emailSent,
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
  margin-bottom: 40px;
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
.forgot-password-form {
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

/* Success Message */
.success-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px;
  background: rgba(52, 199, 89, 0.08);
  border: 1px solid rgba(52, 199, 89, 0.2);
  border-radius: 12px;
  margin-bottom: 24px;
  animation: successSlide 0.5s ease;
}

@keyframes successSlide {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  color: #34c759;
  margin-top: 2px;
}

.success-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0 0 6px 0;
}

.success-text {
  font-size: 13px;
  color: #515154;
  margin: 0;
  line-height: 1.5;
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

/* Footer */
.footer {
  text-align: center;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #007aff;
  font-size: 14px;
  font-weight: 550;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.back-button:hover {
  background: rgba(0, 122, 255, 0.08);
  color: #0051d5;
}

.back-icon {
  width: 18px;
  height: 18px;
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

  .success-title {
    color: #f5f5f7;
  }

  .success-text {
    color: #aeaeb2;
  }
}
</style>
