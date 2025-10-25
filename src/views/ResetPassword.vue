<template>
  <div class="auth-container">
    <!-- Animated Background -->
    <div class="background-wrapper">
      <div class="gradient-bg"></div>
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <!-- Main Content -->
    <div class="auth-content">
      <div class="auth-card">
        <!-- Show error if token is invalid -->
        <div v-if="tokenError" class="token-error-container">
          <div class="error-icon-large">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 class="error-title">Invalid Reset Link</h1>
          <p class="error-message">{{ tokenError }}</p>
          <button @click="goToLogin" class="back-button-large">
            Return to Login
          </button>
        </div>

        <!-- Show reset form if token is valid -->
        <ResetPasswordForm v-else />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ResetPasswordForm from '../components/auth/ResetPasswordForm.vue'

const API_BASE_URL = 'http://localhost:8086'

export default {
  name: 'ResetPassword',
  components: {
    ResetPasswordForm
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const tokenError = ref('')

    const goToLogin = () => {
      router.push({ name: 'Login' })
    }

    // Validate token on mount
    onMounted(async () => {
      const token = route.query.token

      if (!token) {
        tokenError.value = 'No reset token provided. Please request a new password reset.'
        return
      }

      try {
        const response = await fetch(`${API_BASE_URL}/auth/validate-reset-token?token=${encodeURIComponent(token)}`)
        const data = await response.json()

        if (!data.valid) {
          tokenError.value = data.error || 'This reset link is invalid or has expired. Please request a new password reset.'
        }
      } catch (error) {
        tokenError.value = 'Unable to validate reset link. Please try again or request a new password reset.'
      }
    })

    return {
      tokenError,
      goToLogin
    }
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 20px;
}

/* Background */
.background-wrapper {
  position: fixed;
  inset: 0;
  z-index: 0;
}

.gradient-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  opacity: 0.9;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #667eea 0%, transparent 70%);
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, #f093fb 0%, transparent 70%);
  bottom: -100px;
  right: -100px;
  animation-delay: 5s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #764ba2 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-30px, 30px) scale(0.9);
  }
}

/* Content */
.auth-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
}

.auth-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Token Error Container */
.token-error-container {
  text-align: center;
  padding: 20px;
}

.error-icon-large {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  color: #ff3b30;
}

.error-icon-large svg {
  width: 100%;
  height: 100%;
}

.error-title {
  font-size: 28px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 12px 0;
  letter-spacing: -0.03em;
}

.error-message {
  font-size: 15px;
  color: #86868b;
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.back-button-large {
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
}

.back-button-large:hover {
  background: #0051d5;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.4);
}

.back-button-large:active {
  transform: translateY(0);
}

/* Responsive */
@media (max-width: 600px) {
  .auth-card {
    padding: 36px 28px;
    border-radius: 20px;
  }

  .orb {
    filter: blur(60px);
  }

  .error-icon-large {
    width: 64px;
    height: 64px;
    margin-bottom: 20px;
  }

  .error-title {
    font-size: 24px;
  }

  .error-message {
    font-size: 14px;
  }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .auth-card {
    background: rgba(28, 28, 30, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .gradient-bg {
    opacity: 0.7;
  }

  .error-title {
    color: #f5f5f7;
  }

  .error-message {
    color: #98989d;
  }
}
</style>
