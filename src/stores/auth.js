import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE_URL = 'http://localhost:8086'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const sessionToken = ref(localStorage.getItem('sessionToken'))
  const sessionTimeout = ref(null)
  
  const isAuthenticated = computed(() => !!user.value && !!sessionToken.value)
  
  // Session timeout management (15 minutes)
  const SESSION_DURATION = 15 * 60 * 1000 // 15 minutes in milliseconds
  
  const startSessionTimer = () => {
    if (sessionTimeout.value) {
      clearTimeout(sessionTimeout.value)
    }
    
    sessionTimeout.value = setTimeout(() => {
      logout()
      alert('Your session has expired due to inactivity. Please log in again.')
    }, SESSION_DURATION)
  }
  
  const resetSessionTimer = () => {
    if (isAuthenticated.value) {
      startSessionTimer()
    }
  }
  
  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Login failed')
      }
      
      // Store user and session token
      user.value = data.user
      sessionToken.value = data.session_token
      localStorage.setItem('sessionToken', data.session_token)
      
      // Start session timer
      startSessionTimer()
      
      return data
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }
  
  const logout = async () => {
    try {
      if (sessionToken.value) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${sessionToken.value}`,
          },
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear local state
      user.value = null
      sessionToken.value = null
      localStorage.removeItem('sessionToken')
      
      if (sessionTimeout.value) {
        clearTimeout(sessionTimeout.value)
        sessionTimeout.value = null
      }
    }
  }
  
  const validateSession = async () => {
    if (!sessionToken.value) {
      return false
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/validate`, {
        headers: {
          'Authorization': `Bearer ${sessionToken.value}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        user.value = data.user
        resetSessionTimer()
        return true
      } else {
        // Session invalid
        await logout()
        return false
      }
    } catch (error) {
      console.error('Session validation error:', error)
      await logout()
      return false
    }
  }
  
  const initializeAuth = async () => {
    if (sessionToken.value) {
      const isValid = await validateSession()
      if (isValid) {
        startSessionTimer()
      }
    }
  }
  
  return {
    user,
    isAuthenticated,
    login,
    logout,
    validateSession,
    initializeAuth,
    resetSessionTimer
  }
})