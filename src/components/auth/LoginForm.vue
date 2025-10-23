<template>
  <div>
      <!-- Logo Section -->
      <div class="logo-section">
        <img src="/taskio-logo.svg" alt="Taskio" class="taskio-logo" />
        <h1 class="welcome-title">Welcome back</h1>
        <p class="welcome-subtitle">Sign in to continue to Taskio</p>
      </div>
      
      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="login-form">
        <!-- Email Input -->
        <div class="form-group">
          <label class="form-label">Email</label>
          <div class="input-wrapper">
            <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
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
        
        <!-- Password Input -->
        <div class="form-group">
          <label class="form-label">Password</label>
          <div class="input-wrapper">
            <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Enter your password"
              class="form-input"
              :class="{ 'input-error': errorMessage }"
              :disabled="isLoading"
              autocomplete="current-password"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="password-toggle"
              :disabled="isLoading"
            >
              <svg v-if="!showPassword" class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          <span v-if="!isLoading">Sign In</span>
          <span v-else class="loading-content">
            <svg class="spinner" viewBox="0 0 24 24">
              <circle class="spinner-circle" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
            </svg>
            Signing in...
          </span>
        </button>
      </form>
      
    <!-- Footer -->
    <div class="login-footer">
      <p class="footer-text">
        Don't have an account?
        <a href="#" @click.prevent="$emit('switch-to-signup')" class="footer-link">Create one</a>
      </p>
      <p class="footer-help">Contact your administrator for assistance</p>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '../../stores/auth'

export default {
  name: 'Login',
  components: {
    UserOutlined,
    LockOutlined
  },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const form = reactive({
      email: '',
      password: ''
    })
    
    const isLoading = ref(false)
    const errorMessage = ref('')
    const showPassword = ref(false)
    
    const handleLogin = async (e) => {
      e.preventDefault()
      
      if (!form.email || !form.password) {
        errorMessage.value = 'Please enter both email and password'
        return
      }
      
      isLoading.value = true
      errorMessage.value = ''
      
      try {
        await authStore.login(form.email, form.password)
        
        message.success('Login successful!')
        
        // Redirect to intended route or home
        const redirectTo = router.currentRoute.value.query.redirect || '/home'
        router.push(redirectTo)
        
      } catch (error) {
        errorMessage.value = error.message || 'Login failed. Please try again.'
        message.error(errorMessage.value)
      } finally {
        isLoading.value = false
      }
    }
    
    return {
      form,
      isLoading,
      errorMessage,
      showPassword,
      handleLogin
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
.login-form {
  margin-bottom: 32px;
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

/* Footer */
.login-footer {
  text-align: center;
}

.footer-text {
  font-size: 14px;
  color: #515154;
  margin: 0 0 12px 0;
  font-weight: 450;
}

.footer-link {
  color: #007aff;
  text-decoration: none;
  font-weight: 550;
  margin-left: 4px;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: #0051d5;
  text-decoration: underline;
}

.footer-help {
  font-size: 12px;
  color: #86868b;
  margin: 0;
  font-weight: 450;
}

/* Responsive */
@media (max-width: 480px) {
  .login-glass-card {
    padding: 36px 28px;
    border-radius: 24px;
  }
  
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
  
  .orb {
    filter: blur(60px);
  }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .login-glass-card {
    background: rgba(28, 28, 30, 0.85);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
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
  
  .footer-text {
    color: #aeaeb2;
  }
  
  .footer-help {
    color: #98989d;
  }
}
</style>