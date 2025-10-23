<template>
  <div class="auth-container">
    <!-- Animated Background -->
    <div class="background-gradient"></div>
    <div class="background-orbs">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>
    
    <!-- 3D Flip Card Container -->
    <div class="card-scene">
      <div class="flip-card" :class="{ 'is-flipped': isSignupMode }">
        <!-- Front Side - Login -->
        <div class="card-face card-face-front">
          <div class="glass-card">
            <LoginForm @switch-to-signup="flipToSignup" />
          </div>
        </div>
        
        <!-- Back Side - Signup -->
        <div class="card-face card-face-back">
          <div class="glass-card">
            <SignupForm @switch-to-login="flipToLogin" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoginForm from '../components/auth/LoginForm.vue'
import SignupForm from '../components/auth/SignupForm.vue'

export default {
  name: 'Auth',
  components: {
    LoginForm,
    SignupForm
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const isSignupMode = ref(false)
    
    // Initialize based on route
    onMounted(() => {
      isSignupMode.value = route.name === 'Signup'
    })
    
    // Watch for route changes
    watch(() => route.name, (newRoute) => {
      isSignupMode.value = newRoute === 'Signup'
    })
    
    const flipToSignup = () => {
      isSignupMode.value = true
      router.push({ name: 'Signup' })
    }
    
    const flipToLogin = () => {
      isSignupMode.value = false
      router.push({ name: 'Login' })
    }
    
    return {
      isSignupMode,
      flipToSignup,
      flipToLogin
    }
  }
}
</script>

<style scoped>
/* Container & Background */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.background-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, 
    #667eea 0%, 
    #764ba2 25%,
    #f093fb 50%,
    #4facfe 75%,
    #00f2fe 100%
  );
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.background-orbs {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(129, 179, 255, 0.8) 0%, transparent 70%);
  top: -10%;
  left: -10%;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.6) 0%, transparent 70%);
  bottom: -10%;
  right: -10%;
  animation-delay: 7s;
}

.orb-3 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(175, 82, 222, 0.5) 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}

/* 3D Card Scene */
.card-scene {
  perspective: 1200px;
  width: 100%;
  max-width: 500px;
}

.flip-card {
  position: relative;
  width: 100%;
  min-height: 600px;
  transform-style: preserve-3d;
  transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.flip-card.is-flipped {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.card-face-front {
  transform: rotateY(0deg);
}

.card-face-back {
  transform: rotateY(180deg);
}

.glass-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  padding: 48px 40px;
  max-height: 90vh;
  overflow-y: auto;
}

/* Scrollbar */
.glass-card::-webkit-scrollbar {
  width: 8px;
}

.glass-card::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
}

.glass-card::-webkit-scrollbar-thumb {
  background: rgba(0, 122, 255, 0.3);
  border-radius: 10px;
}

.glass-card::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 122, 255, 0.5);
}

/* Responsive */
@media (max-width: 480px) {
  .glass-card {
    padding: 32px 24px;
    border-radius: 24px;
    max-height: 95vh;
  }
  
  .orb {
    filter: blur(60px);
  }
}

/* Dark Mode */
@media (prefers-color-scheme: dark) {
  .glass-card {
    background: rgba(28, 28, 30, 0.85);
    border-color: rgba(255, 255, 255, 0.1);
  }
}
</style>
