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
        <ForgotPasswordForm @back-to-login="goToLogin" />
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import ForgotPasswordForm from '../components/auth/ForgotPasswordForm.vue'

export default {
  name: 'ForgotPassword',
  components: {
    ForgotPasswordForm
  },
  setup() {
    const router = useRouter()

    const goToLogin = () => {
      router.push({ name: 'Login' })
    }

    return {
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

/* Responsive */
@media (max-width: 600px) {
  .auth-card {
    padding: 36px 28px;
    border-radius: 20px;
  }

  .orb {
    filter: blur(60px);
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
}
</style>
