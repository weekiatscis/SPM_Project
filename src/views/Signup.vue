<template>
  <div class="signup-container">
    <div class="signup-card">
      <div class="signup-header">
        <h1>Create Account</h1>
        <p>Sign up to start managing your tasks and projects</p>
      </div>
      
      <a-form @submit="handleSignup" class="signup-form" layout="vertical">
        <a-form-item 
          label="Full Name"
          :validate-status="errorFields.name ? 'error' : ''"
          :help="errorFields.name"
        >
          <a-input
            v-model:value="form.name"
            type="text"
            placeholder="Enter your full name"
            size="large"
            :disabled="isLoading"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item 
          label="Email Address"
          :validate-status="errorFields.email ? 'error' : ''"
          :help="errorFields.email"
        >
          <a-input
            v-model:value="form.email"
            type="email"
            placeholder="Enter your email address"
            size="large"
            :disabled="isLoading"
          >
            <template #prefix>
              <MailOutlined />
            </template>
          </a-input>
        </a-form-item>
        
        <a-form-item 
          label="Password"
          :validate-status="errorFields.password ? 'error' : ''"
          :help="errorFields.password"
        >
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

        <a-form-item 
          label="Confirm Password"
          :validate-status="errorFields.confirmPassword ? 'error' : ''"
          :help="errorFields.confirmPassword"
        >
          <a-input-password
            v-model:value="form.confirmPassword"
            placeholder="Confirm your password"
            size="large"
            :disabled="isLoading"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item 
          label="Role"
          :validate-status="errorFields.role ? 'error' : ''"
          :help="errorFields.role"
        >
          <a-select
            v-model:value="form.role"
            placeholder="Select your role"
            size="large"
            :disabled="isLoading"
          >
            <a-select-option value="Staff">Staff</a-select-option>
            <a-select-option value="Manager">Manager</a-select-option>
            <a-select-option value="Director">Director</a-select-option>
            <a-select-option value="Hr">HR</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item 
          label="Department (Optional)"
          :validate-status="errorFields.department ? 'error' : ''"
          :help="errorFields.department"
        >
          <a-input
            v-model:value="form.department"
            type="text"
            placeholder="Enter your department"
            size="large"
            :disabled="isLoading"
          >
            <template #prefix>
              <BankOutlined />
            </template>
          </a-input>
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="isLoading"
            @click="handleSignup"
          >
            {{ isLoading ? 'Creating Account...' : 'Create Account' }}
          </a-button>
        </a-form-item>
      </a-form>
      
      <div class="signup-footer">
        <a-typography-text type="secondary">
          Already have an account? 
          <router-link to="/login" class="login-link">Sign in here</router-link>
        </a-typography-text>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { UserOutlined, LockOutlined, MailOutlined, BankOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

export default {
  name: 'Signup',
  components: {
    UserOutlined,
    LockOutlined,
    MailOutlined,
    BankOutlined
  },
  setup() {
    const router = useRouter()
    
    const form = reactive({
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: '',
      department: ''
    })
    
    const isLoading = ref(false)
    const errorFields = ref({
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: '',
      department: ''
    })
    
    const validateForm = () => {
      // Reset errors
      errorFields.value = {
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: '',
        department: ''
      }
      
      let isValid = true
      
      // Name validation
      if (!form.name.trim()) {
        errorFields.value.name = 'Full name is required'
        isValid = false
      } else if (form.name.trim().length < 2) {
        errorFields.value.name = 'Name must be at least 2 characters long'
        isValid = false
      }
      
      // Email validation
      if (!form.email.trim()) {
        errorFields.value.email = 'Email address is required'
        isValid = false
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
        errorFields.value.email = 'Please enter a valid email address'
        isValid = false
      }
      
      // Password validation
      if (!form.password) {
        errorFields.value.password = 'Password is required'
        isValid = false
      } else if (form.password.length < 8) {
        errorFields.value.password = 'Password must be at least 8 characters long'
        isValid = false
      } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(form.password)) {
        errorFields.value.password = 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
        isValid = false
      }
      
      // Confirm password validation
      if (!form.confirmPassword) {
        errorFields.value.confirmPassword = 'Please confirm your password'
        isValid = false
      } else if (form.password !== form.confirmPassword) {
        errorFields.value.confirmPassword = 'Passwords do not match'
        isValid = false
      }
      
      // Role validation
      if (!form.role) {
        errorFields.value.role = 'Please select your role'
        isValid = false
      }
      
      return isValid
    }
    
    const handleSignup = async (e) => {
      e.preventDefault()
      
      if (!validateForm()) {
        return
      }
      
      isLoading.value = true
      
      try {
        const response = await fetch('http://localhost:8086/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: form.name.trim(),
            email: form.email.trim().toLowerCase(),
            password: form.password,
            role: form.role,
            department: form.department.trim() || undefined
          }),
        })
        
        const data = await response.json()
        
        if (!response.ok) {
          throw new Error(data.error || 'Signup failed')
        }
        
        message.success('Account created successfully! Please sign in.')
        
        // Redirect to login page
        router.push('/login')
        
      } catch (error) {
        console.error('Signup error:', error)
        
        // Handle specific error cases
        if (error.message.includes('User already exists')) {
          errorFields.value.email = 'An account with this email already exists'
        } else {
          message.error(error.message || 'Signup failed. Please try again.')
        }
      } finally {
        isLoading.value = false
      }
    }
    
    return {
      form,
      isLoading,
      errorFields,
      handleSignup
    }
  }
}
</script>

<style scoped>
.signup-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.signup-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  padding: 2rem;
  width: 100%;
  max-width: 480px;
}

.signup-header {
  text-align: center;
  margin-bottom: 2rem;
}

.signup-header h1 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.signup-header p {
  color: #6b7280;
  font-size: 0.875rem;
}

.signup-form {
  margin-bottom: 1.5rem;
}

.signup-footer {
  text-align: center;
}

.login-link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.login-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

/* Mobile responsive */
@media (max-width: 480px) {
  .signup-container {
    padding: 0.5rem;
  }
  
  .signup-card {
    padding: 1.5rem;
  }
  
  .signup-header h1 {
    font-size: 1.5rem;
  }
}

/* Dark mode support */
.dark .signup-card {
  background: #1f2937;
}

.dark .signup-header h1 {
  color: #f9fafb;
}

.dark .signup-header p {
  color: #9ca3af;
}
</style>