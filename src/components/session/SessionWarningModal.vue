<template>
  <a-modal
    :open="visible"
    :closable="false"
    :maskClosable="false"
    :footer="null"
    :width="480"
    centered
    wrapClassName="session-warning-modal-wrap"
  >
    <div class="session-warning-container">
      <!-- Warning Icon -->
      <div class="warning-icon-container">
        <svg class="warning-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>

      <!-- Title -->
      <h2 class="warning-title">Session Expiring Soon</h2>

      <!-- Message -->
      <p class="warning-message">
        Your session will expire in <strong class="countdown-text">{{ formatTime(countdown) }}</strong> due to inactivity.
      </p>

      <p class="warning-submessage">
        Would you like to stay logged in?
      </p>

      <!-- Progress Bar -->
      <div class="progress-container">
        <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
      </div>

      <!-- Action Buttons -->
      <div class="button-group">
        <button @click="handleExtend" class="btn-primary">
          Stay Logged In
        </button>
        <button @click="handleLogout" class="btn-link">
          Log Out
        </button>
      </div>
    </div>
  </a-modal>
</template>

<script>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useAuthStore } from '../../stores/auth'

export default {
  name: 'SessionWarningModal',
  setup() {
    const authStore = useAuthStore()
    const countdown = ref(120) // 2 minutes in seconds
    const countdownInterval = ref(null)
    const TOTAL_WARNING_TIME = 120 // 2 minutes

    const visible = computed(() => authStore.showWarning)

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const progressPercentage = computed(() => {
      return (countdown.value / TOTAL_WARNING_TIME) * 100
    })

    const startCountdown = () => {
      // Reset countdown to 2 minutes
      countdown.value = TOTAL_WARNING_TIME

      // Clear any existing interval
      if (countdownInterval.value) {
        clearInterval(countdownInterval.value)
      }

      // Start countdown
      countdownInterval.value = setInterval(() => {
        countdown.value--

        if (countdown.value <= 0) {
          clearInterval(countdownInterval.value)
          // Auto-logout when countdown reaches 0
          authStore.handleAutoLogout()
        }
      }, 1000)
    }

    const stopCountdown = () => {
      if (countdownInterval.value) {
        clearInterval(countdownInterval.value)
        countdownInterval.value = null
      }
    }

    const handleExtend = () => {
      stopCountdown()
      authStore.extendSession()
    }

    const handleLogout = () => {
      stopCountdown()
      authStore.logout()
    }

    // Watch for modal visibility changes
    watch(visible, (newVal) => {
      if (newVal) {
        startCountdown()
      } else {
        stopCountdown()
      }
    })

    // Cleanup on component unmount
    onUnmounted(() => {
      stopCountdown()
    })

    return {
      visible,
      countdown,
      formatTime,
      progressPercentage,
      handleExtend,
      handleLogout
    }
  }
}
</script>

<style scoped>
.session-warning-container {
  padding: 8px;
  text-align: center;
}

/* Warning Icon */
.warning-icon-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.warning-icon {
  width: 64px;
  height: 64px;
  color: #ff9500;
  filter: drop-shadow(0 4px 12px rgba(255, 149, 0, 0.3));
}

/* Title */
.warning-title {
  font-size: 24px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 16px 0;
  letter-spacing: -0.03em;
}

/* Message */
.warning-message {
  font-size: 16px;
  color: #515154;
  margin: 0 0 8px 0;
  font-weight: 450;
  line-height: 1.5;
}

.warning-submessage {
  font-size: 15px;
  color: #86868b;
  margin: 0 0 24px 0;
  font-weight: 450;
}

.countdown-text {
  color: #ff9500;
  font-weight: 600;
  font-size: 18px;
  font-variant-numeric: tabular-nums;
}

/* Progress Bar */
.progress-container {
  width: 100%;
  height: 6px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 28px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #ff9500 0%, #ff3b30 100%);
  border-radius: 3px;
  transition: width 1s linear;
}

/* Button Group */
.button-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

/* Primary Button - Stay Logged In */
.btn-primary {
  width: 100%;
  max-width: 300px;
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

.btn-primary:hover {
  background: #0051d5;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.4);
}

.btn-primary:active {
  transform: translateY(0);
}

/* Link-styled Button - Log Out */
.btn-link {
  background: none;
  border: none;
  color: #007aff;
  text-decoration: none;
  font-weight: 550;
  font-size: 15px;
  cursor: pointer;
  transition: color 0.2s ease;
  padding: 8px 16px;
}

.btn-link:hover {
  color: #0051d5;
  text-decoration: underline;
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .warning-title {
    color: #f5f5f7;
  }

  .warning-message {
    color: #aeaeb2;
  }

  .warning-submessage {
    color: #98989d;
  }

  .progress-container {
    background: rgba(255, 255, 255, 0.1);
  }
}
</style>

<style>
/* Global Modal Styling - Glass Effect */
.session-warning-modal-wrap .ant-modal-content {
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  border: 1.5px solid rgba(0, 0, 0, 0.1) !important;
  border-radius: 20px !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15) !important;
  padding: 32px !important;
}

.session-warning-modal-wrap .ant-modal-body {
  padding: 0 !important;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .session-warning-modal-wrap .ant-modal-content {
    background: rgba(28, 28, 30, 0.85) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
  }
}
</style>
