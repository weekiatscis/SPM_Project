import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import router from '../router'

const API_BASE_URL = 'http://localhost:8086'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const sessionToken = ref(localStorage.getItem('sessionToken'))
  const sessionId = ref(localStorage.getItem('sessionId'))
  const sessionTimeout = ref(null)
  const warningTimeout = ref(null)
  const showWarning = ref(false)

  const isAuthenticated = computed(() => !!user.value && !!sessionToken.value)

  // Session timeout management (15 minutes)
  const SESSION_DURATION = 3 * 60 * 1000 // 15 minutes in milliseconds
  const WARNING_TIME = 1 * 60 * 1000 // 13 minutes (2 minutes before expiration)
  
  // Singapore timezone helper
  const getSingaporeTime = () => {
    return new Date().toLocaleString('en-SG', {
      timeZone: 'Asia/Singapore',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  // Generate a unique session ID
  const generateSessionId = () => {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }
  
  // Audit logging helper
  const logAuditEvent = async (eventType, eventDescription, metadata = {}) => {
    if (!sessionToken.value) return

    try {
      await fetch(`${API_BASE_URL}/auth/audit-log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionToken.value}`,
        },
        body: JSON.stringify({
          event_type: eventType,
          event_description: eventDescription,
          session_id: sessionId.value,
          timestamp: getSingaporeTime(),
          metadata: {
            ...metadata,
            timezone: 'Asia/Singapore',
            client_time: getSingaporeTime()
          }
        }),
      })
    } catch (error) {
      console.error('Failed to log audit event:', error)
    }
  }

  const showSessionWarning = () => {
    // Only show warning if session is still valid
    if (!isAuthenticated.value) {
      return
    }
    
    showWarning.value = true
    logAuditEvent(
      'session_warning_shown',
      'Session warning displayed to user - 2 minutes remaining',
      { remaining_seconds: 120 }
    )
  }

  const startSessionTimer = () => {
    // Clear any existing timers
    if (sessionTimeout.value) {
      clearTimeout(sessionTimeout.value)
    }
    if (warningTimeout.value) {
      clearTimeout(warningTimeout.value)
    }

    // Hide warning modal if it's showing
    showWarning.value = false

    // Set warning timer (13 minutes)
    warningTimeout.value = setTimeout(() => {
      showSessionWarning()
    }, WARNING_TIME)

    // Set logout timer (15 minutes)
    sessionTimeout.value = setTimeout(() => {
      handleAutoLogout()
    }, SESSION_DURATION)
  }

  const handleAutoLogout = async () => {
    const wasWarningIgnored = showWarning.value

    // Clear all timers immediately to prevent race conditions
    if (sessionTimeout.value) {
      clearTimeout(sessionTimeout.value)
      sessionTimeout.value = null
    }
    if (warningTimeout.value) {
      clearTimeout(warningTimeout.value)
      warningTimeout.value = null
    }

    // Log audit event before logout (while session is still valid)
    await logAuditEvent(
      wasWarningIgnored ? 'session_expired_ignored_warning' : 'session_expired_auto',
      wasWarningIgnored
        ? 'Session expired after warning was ignored'
        : 'Session expired due to inactivity',
      { warning_shown: wasWarningIgnored }
    )

    // Call logout with isManual=false to prevent duplicate audit logging
    await logout(false)
  }

  const extendSession = async () => {
    await logAuditEvent(
      'session_extended',
      'User extended session by clicking "Stay Logged In"',
      { extended_from: 'warning_modal' }
    )

    showWarning.value = false
    resetSessionTimer()
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
      
      // Store user, session token, and session ID
      user.value = data.user
      sessionToken.value = data.session_token
      // Generate session ID if backend doesn't provide one
      sessionId.value = data.session_id || data.sessionId || generateSessionId()
      localStorage.setItem('sessionToken', data.session_token)
      localStorage.setItem('sessionId', sessionId.value)
      
      // Start session timer
      startSessionTimer()
      
      return data
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }
  
  const logout = async (isManual = true) => {
    try {
      // Log manual logout only if we have a valid session
      if (isManual && sessionToken.value && user.value) {
        await logAuditEvent(
          'session_logout_manual',
          'User manually logged out',
          { warning_was_showing: showWarning.value }
        )
      }

      // Only attempt server logout if we have a valid session token
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
      // Clear all timers first to prevent race conditions
      if (sessionTimeout.value) {
        clearTimeout(sessionTimeout.value)
        sessionTimeout.value = null
      }
      if (warningTimeout.value) {
        clearTimeout(warningTimeout.value)
        warningTimeout.value = null
      }

      // Clear local state
      user.value = null
      sessionToken.value = null
      sessionId.value = null
      localStorage.removeItem('sessionToken')
      localStorage.removeItem('sessionId')

      // Hide warning modal
      showWarning.value = false

      // Redirect to login page
      if (router.currentRoute.value.name !== 'Login') {
        router.push({ name: 'Login' })
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
        if (data.session_id || data.sessionId) {
          sessionId.value = data.session_id || data.sessionId
          localStorage.setItem('sessionId', sessionId.value)
        }
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
      // Generate session ID if we don't have one
      if (!sessionId.value) {
        sessionId.value = generateSessionId()
        localStorage.setItem('sessionId', sessionId.value)
      }
      
      const isValid = await validateSession()
      if (isValid) {
        startSessionTimer()
      }
    }
  }

  const updateProfile = async (profileData) => {
    if (!sessionToken.value) {
      throw new Error('Not authenticated')
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionToken.value}`,
        },
        body: JSON.stringify(profileData),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Profile update failed')
      }

      // Update local user data
      user.value = { ...user.value, ...data.user }

      // Reset session timer on activity
      resetSessionTimer()

      return data
    } catch (error) {
      console.error('Profile update error:', error)
      throw error
    }
  }

  return {
    user,
    sessionToken,
    sessionId,
    isAuthenticated,
    showWarning,
    login,
    logout,
    validateSession,
    initializeAuth,
    resetSessionTimer,
    updateProfile,
    extendSession,
    handleAutoLogout
  }
})