<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>Company Login</h1>
        <p>Sign in to access your tasks and projects</p>
      </div>
      
      <a-form @submit="handleLogin" class="login-form" layout="vertical">
        <a-form-item 
          label="Email Address"
          :validate-status="errorMessage ? 'error' : ''"
          :help="errorMessage"
        >
          <a-input
            v-model:value="form.email"
            type="email"
            placeholder="Enter your email"
            size="large"
            :disabled="isLoading"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>
        
        <a-form-item label="Password">
          <a-input-password
            v-model:value="form.password"
            placeholder="Enter your password"
            size="large"
            :disabled="isLoading"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="isLoading"
            @click="handleLogin"
          >
            {{ isLoading ? 'Signing in...' : 'Sign In' }}
          </a-button>
        </a-form-item>
      </a-form>
      
      <div class="login-footer">
        <a-typography-text type="secondary">
          Don't have an account? 
          <router-link to="/signup" class="signup-link">Create one here</router-link>
        </a-typography-text>
        <div style="margin-top: 12px;">
          <a-typography-text type="secondary">
            Contact your administrator if you need assistance
          </a-typography-text>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '../stores/auth'

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
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.login-header p {
  color: #6b7280;
  font-size: 0.875rem;
}

.login-form {
  margin-bottom: 1.5rem;
}

.login-footer {
  text-align: center;
}

.signup-link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.signup-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

/* Mobile responsive */
@media (max-width: 480px) {
  .login-container {
    padding: 0.5rem;
  }
  
  .login-card {
    padding: 1.5rem;
  }
  
  .login-header h1 {
    font-size: 1.5rem;
  }
}

/* Dark mode support */
.dark .login-card {
  background: #1f2937;
}

.dark .login-header h1 {
  color: #f9fafb;
}

.dark .login-header p {
  color: #9ca3af;
}
</style>