<template>
  <div>
      <!-- Logo Section -->
      <div class="logo-section">
        <img src="/taskio-logo.svg" alt="Taskio" class="taskio-logo" />
        <h1 class="welcome-title">Create your account</h1>
        <p class="welcome-subtitle">Join Taskio and start managing your projects</p>
      </div>
      
      <!-- Signup Form -->
      <form @submit.prevent="handleSignup" class="signup-form">
        <!-- Step 1: Personal Info -->
        <div v-show="currentStep === 1" class="form-step">
          <!-- Full Name -->
          <div class="form-group">
            <label class="form-label">Full Name</label>
            <div class="input-wrapper">
              <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <input
                v-model="form.name"
                type="text"
                placeholder="John Doe"
                class="form-input"
                :class="{ 'input-error': errorFields.name }"
                :disabled="isLoading"
                autocomplete="name"
              />
            </div>
            <span v-if="errorFields.name" class="field-error">{{ errorFields.name }}</span>
          </div>

          <!-- Email -->
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
                :class="{ 'input-error': errorFields.email }"
                :disabled="isLoading"
                autocomplete="email"
              />
            </div>
            <span v-if="errorFields.email" class="field-error">{{ errorFields.email }}</span>
          </div>

          <!-- Password -->
          <div class="form-group">
            <label class="form-label">Password</label>
            <div class="input-wrapper">
              <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="At least 8 characters"
                class="form-input"
                :class="{ 'input-error': errorFields.password }"
                :disabled="isLoading"
                autocomplete="new-password"
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
            <span v-if="errorFields.password" class="field-error">{{ errorFields.password }}</span>
          </div>

          <!-- Confirm Password -->
          <div class="form-group">
            <label class="form-label">Confirm Password</label>
            <div class="input-wrapper">
              <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <input
                v-model="form.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="Re-enter your password"
                class="form-input"
                :class="{ 'input-error': errorFields.confirmPassword }"
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
            <span v-if="errorFields.confirmPassword" class="field-error">{{ errorFields.confirmPassword }}</span>
          </div>

          <button type="button" @click="nextStep" class="submit-button" :disabled="isLoading">
            Continue
            <svg class="button-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>

        <!-- Step 2: Work Info -->
        <div v-show="currentStep === 2" class="form-step">
          <!-- Role -->
          <div class="form-group">
            <label class="form-label">Role</label>
            <div class="select-wrapper">
              <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <select
                v-model="form.role"
                class="form-select"
                :class="{ 'input-error': errorFields.role }"
                :disabled="isLoading"
                @change="onRoleChange"
              >
                <option value="" disabled>Select your role</option>
                <option value="Staff">Staff</option>
                <option value="Manager">Manager</option>
                <option value="Director">Director</option>
                <option value="Hr">HR</option>
              </select>
            </div>
            <span v-if="errorFields.role" class="field-error">{{ errorFields.role }}</span>
          </div>

          <!-- Department -->
          <div class="form-group">
            <label class="form-label">Department</label>
            <div class="select-wrapper">
              <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <select
                v-model="form.department"
                class="form-select"
                :class="{ 'input-error': errorFields.department }"
                :disabled="isLoading"
                @change="onDepartmentChange"
              >
                <option value="" disabled>Select your department</option>
                <option value="Sales">Sales</option>
                <option value="Consultancy">Consultancy</option>
                <option value="Systems solutioning">Systems Solutioning</option>
                <option value="Engineering operations">Engineering Operations</option>
                <option value="HR and admin">HR and Admin</option>
                <option value="Finance">Finance</option>
                <option value="IT">IT</option>
              </select>
            </div>
            <span v-if="errorFields.department" class="field-error">{{ errorFields.department }}</span>
          </div>

          <!-- Superior -->
          <div class="form-group">
            <label class="form-label">Superior (Optional)</label>
            <div class="select-wrapper">
              <svg class="input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <select
                v-model="form.superior"
                class="form-select"
                :disabled="isLoading || !form.department || isLoadingSuperiors"
              >
                <option value="">No superior</option>
                <option 
                  v-for="superior in availableSuperiors" 
                  :key="superior.user_id" 
                  :value="superior.user_id"
                >
                  {{ superior.name }} ({{ superior.role }})
                </option>
              </select>
              <div v-if="isLoadingSuperiors" class="loading-spinner-small"></div>
            </div>
            <span v-if="!form.department" class="field-hint">Please select a department first</span>
            <span v-else-if="form.department && availableSuperiors.length === 0 && !isLoadingSuperiors" class="field-hint">
              No managers found in {{ form.department }} department
            </span>
          </div>

          <div class="button-group">
            <button type="button" @click="prevStep" class="back-button" :disabled="isLoading">
              <svg class="button-arrow-left" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
              </svg>
              Back
            </button>
            <button
              type="submit"
              class="submit-button"
              :class="{ 'button-loading': isLoading }"
              :disabled="isLoading"
            >
              <span v-if="!isLoading">Create Account</span>
              <span v-else class="loading-content">
                <svg class="spinner" viewBox="0 0 24 24">
                  <circle class="spinner-circle" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                </svg>
                Creating...
              </span>
            </button>
          </div>
        </div>

        <!-- Progress Indicator -->
        <div class="progress-indicator">
          <div class="progress-dot" :class="{ active: currentStep >= 1, completed: currentStep > 1 }"></div>
          <div class="progress-line" :class="{ active: currentStep > 1 }"></div>
          <div class="progress-dot" :class="{ active: currentStep >= 2 }"></div>
        </div>
      </form>
      
    <!-- Footer -->
    <div class="signup-footer">
      <p class="footer-text">
        Already have an account?
        <a href="#" @click.prevent="$emit('switch-to-login')" class="footer-link">Sign in</a>
      </p>
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
      department: '',
      superior: ''
    })
    
    const isLoading = ref(false)
    const isLoadingSuperiors = ref(false)
    const availableSuperiors = ref([])
    const showPassword = ref(false)
    const showConfirmPassword = ref(false)
    const currentStep = ref(1)
    const errorFields = ref({
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: '',
      department: '',
      superior: ''
    })
    
    const validateForm = () => {
      // Reset errors
      errorFields.value = {
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: '',
        department: '',
        superior: ''
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
      
      // Department validation
      if (!form.department) {
        errorFields.value.department = 'Please select your department'
        isValid = false
      }
      
      // Superior validation (optional but should make sense if provided)
      if (form.superior) {
        const selectedSuperior = availableSuperiors.value.find(s => s.user_id === form.superior)
        if (selectedSuperior) {
          // Check role hierarchy logic
          if (form.role === 'Director' && selectedSuperior.role !== 'Director') {
            errorFields.value.superior = 'Directors typically report to other Directors or have no superior'
            isValid = false
          } else if (form.role === 'Manager' && selectedSuperior.role === 'Staff') {
            errorFields.value.superior = 'Managers cannot report to Staff members'
            isValid = false
          } else if (form.role === 'Staff' && selectedSuperior.role === 'Staff') {
            errorFields.value.superior = 'Staff members cannot report to other Staff members'
            isValid = false
          }
        }
      }
      
      return isValid
    }
    
    // Fetch managers from the selected department
    const fetchDepartmentSuperiors = async (department) => {
      if (!department) {
        availableSuperiors.value = []
        return
      }

      isLoadingSuperiors.value = true
      try {
        const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
        const response = await fetch(`${userServiceUrl}/users/departments/${encodeURIComponent(department)}`)
        
        if (response.ok) {
          const data = await response.json()
          let potentialSuperiors = data.users || []
          
          // Filter based on role hierarchy
          if (form.role === 'Staff') {
            // Staff can report to Managers or Directors
            potentialSuperiors = potentialSuperiors.filter(user => 
              user.role === 'Manager' || user.role === 'Director'
            )
          } else if (form.role === 'Manager') {
            // Managers can report to Directors
            potentialSuperiors = potentialSuperiors.filter(user => 
              user.role === 'Director'
            )
          } else if (form.role === 'Hr') {
            // HR can report to Directors
            potentialSuperiors = potentialSuperiors.filter(user => 
              user.role === 'Director'
            )
          } else if (form.role === 'Director') {
            // Directors can report to other Directors (rare) or no one
            potentialSuperiors = potentialSuperiors.filter(user => 
              user.role === 'Director'
            )
          }
          
          availableSuperiors.value = potentialSuperiors
        } else {
          console.error('Failed to fetch department users:', response.status)
          availableSuperiors.value = []
        }
      } catch (error) {
        console.error('Error fetching department users:', error)
        availableSuperiors.value = []
      } finally {
        isLoadingSuperiors.value = false
      }
    }

    // Handle department change
    const onDepartmentChange = (department) => {
      // Reset superior when department changes
      form.superior = ''
      // Fetch new superiors for the selected department
      fetchDepartmentSuperiors(department)
    }

    // Handle role change
    const onRoleChange = (role) => {
      // Reset superior when role changes as the available superiors might change
      form.superior = ''
      // Re-fetch superiors if department is already selected
      if (form.department) {
        fetchDepartmentSuperiors(form.department)
      }
    }
    
    // Step navigation
    const nextStep = () => {
      // Validate step 1 fields
      errorFields.value.name = ''
      errorFields.value.email = ''
      errorFields.value.password = ''
      errorFields.value.confirmPassword = ''
      
      let isValid = true
      
      if (!form.name.trim()) {
        errorFields.value.name = 'Full name is required'
        isValid = false
      } else if (form.name.trim().length < 2) {
        errorFields.value.name = 'Name must be at least 2 characters long'
        isValid = false
      }
      
      if (!form.email.trim()) {
        errorFields.value.email = 'Email address is required'
        isValid = false
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
        errorFields.value.email = 'Please enter a valid email address'
        isValid = false
      }
      
      if (!form.password) {
        errorFields.value.password = 'Password is required'
        isValid = false
      } else if (form.password.length < 8) {
        errorFields.value.password = 'Password must be at least 8 characters long'
        isValid = false
      } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(form.password)) {
        errorFields.value.password = 'Password must contain uppercase, lowercase, and number'
        isValid = false
      }
      
      if (!form.confirmPassword) {
        errorFields.value.confirmPassword = 'Please confirm your password'
        isValid = false
      } else if (form.password !== form.confirmPassword) {
        errorFields.value.confirmPassword = 'Passwords do not match'
        isValid = false
      }
      
      if (isValid) {
        currentStep.value = 2
      }
    }
    
    const prevStep = () => {
      currentStep.value = 1
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
            department: form.department.trim() || undefined,
            superior: form.superior || null
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
      isLoadingSuperiors,
      availableSuperiors,
      errorFields,
      showPassword,
      showConfirmPassword,
      currentStep,
      handleSignup,
      onDepartmentChange,
      onRoleChange,
      nextStep,
      prevStep
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
  height: 38px;
  width: auto;
  margin: 0 auto 20px auto;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
  animation: logoFloat 3s ease-in-out infinite;
  display: block;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 6px 0;
  letter-spacing: -0.03em;
}

.welcome-subtitle {
  font-size: 14px;
  color: #86868b;
  margin: 0;
  font-weight: 450;
}

/* Form */
.signup-form {
  margin-bottom: 24px;
}

.form-step {
  animation: stepFadeIn 0.4s ease;
}

@keyframes stepFadeIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.form-group {
  margin-bottom: 18px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 550;
  color: #1d1d1f;
  margin-bottom: 7px;
  letter-spacing: -0.01em;
}

/* Input Wrapper */
.input-wrapper,
.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  width: 19px;
  height: 19px;
  color: #86868b;
  pointer-events: none;
  z-index: 1;
}

.form-input,
.form-select {
  width: 100%;
  height: 48px;
  padding: 0 48px;
  font-size: 14px;
  color: #1d1d1f;
  background: rgba(255, 255, 255, 0.6);
  border: 1.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 13px;
  outline: none;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  font-weight: 450;
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2386868b'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 20px;
  padding-right: 48px;
}

.form-input::placeholder {
  color: #a1a1a6;
}

.form-input:hover,
.form-select:hover {
  border-color: rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.75);
}

.form-input:focus,
.form-select:focus {
  border-color: #007aff;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
}

.form-input:disabled,
.form-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-error {
  border-color: #ff3b30 !important;
}

.input-error:focus {
  box-shadow: 0 0 0 4px rgba(255, 59, 48, 0.1) !important;
}

/* Field Error & Hint */
.field-error {
  display: block;
  font-size: 12px;
  color: #ff3b30;
  margin-top: 6px;
  font-weight: 500;
}

.field-hint {
  display: block;
  font-size: 11px;
  color: #86868b;
  margin-top: 6px;
  font-weight: 450;
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
  width: 19px;
  height: 19px;
  color: #86868b;
}

/* Loading Spinner Small */
.loading-spinner-small {
  position: absolute;
  right: 16px;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 122, 255, 0.2);
  border-top-color: #007aff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Buttons */
.submit-button {
  width: 100%;
  height: 48px;
  background: #007aff;
  color: #ffffff;
  border: none;
  border-radius: 13px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
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

.button-arrow,
.button-arrow-left {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.spinner {
  width: 18px;
  height: 18px;
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

/* Button Group */
.button-group {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.back-button {
  flex: 1;
  height: 48px;
  background: rgba(0, 0, 0, 0.05);
  color: #1d1d1f;
  border: none;
  border-radius: 13px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.back-button:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.back-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-group .submit-button {
  flex: 2;
  margin-top: 0;
}

/* Progress Indicator */
.progress-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.progress-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.progress-dot.active {
  background: #007aff;
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
}

.progress-dot.completed {
  background: #34c759;
  box-shadow: 0 0 0 4px rgba(52, 199, 89, 0.15);
}

.progress-line {
  width: 40px;
  height: 2px;
  background: rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.progress-line.active {
  background: #007aff;
}

/* Footer */
.signup-footer {
  text-align: center;
  margin-top: 20px;
}

.footer-text {
  font-size: 13px;
  color: #515154;
  margin: 0;
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

/* Responsive */
@media (max-width: 480px) {
  .signup-glass-card {
    padding: 32px 24px;
    border-radius: 24px;
    max-height: 95vh;
  }
  
  .taskio-logo {
    height: 34px;
    margin-bottom: 16px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-subtitle {
    font-size: 13px;
  }
  
  .form-input,
  .form-select,
  .submit-button,
  .back-button {
    height: 44px;
  }
  
  .form-group {
    margin-bottom: 16px;
  }
  
  .orb {
    filter: blur(60px);
  }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .signup-glass-card {
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
  
  .form-input,
  .form-select {
    color: #f5f5f7;
    background: rgba(58, 58, 60, 0.6);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .form-input:hover,
  .form-select:hover {
    background: rgba(58, 58, 60, 0.75);
    border-color: rgba(255, 255, 255, 0.15);
  }
  
  .form-input:focus,
  .form-select:focus {
    background: rgba(58, 58, 60, 0.9);
  }
  
  .form-input::placeholder {
    color: #636366;
  }
  
  .back-button {
    background: rgba(255, 255, 255, 0.1);
    color: #f5f5f7;
  }
  
  .back-button:hover {
    background: rgba(255, 255, 255, 0.15);
  }
  
  .footer-text {
    color: #aeaeb2;
  }
  
  .field-hint {
    color: #98989d;
  }
  
  .progress-indicator {
    border-top-color: rgba(255, 255, 255, 0.1);
  }
}
</style>