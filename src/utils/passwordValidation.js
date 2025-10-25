/**
 * Password Validation Utility
 * Validates passwords according to security requirements:
 * - Minimum 15 characters
 * - Contains uppercase and lowercase letters
 * - Contains at least one number
 * - Contains at least one special character
 */

/**
 * Validates password strength according to requirements
 * @param {string} password - Password to validate
 * @returns {Object} - { isValid: boolean, errors: string[] }
 */
export function validatePasswordStrength(password) {
  const errors = []

  if (!password) {
    return {
      isValid: false,
      errors: ['Password is required']
    }
  }

  // Check minimum length (15 characters)
  if (password.length < 15) {
    errors.push('Password must be at least 15 characters long')
  }

  // Check for uppercase letter
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter')
  }

  // Check for lowercase letter
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter')
  }

  // Check for number
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number')
  }

  // Check for special character
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character (!@#$%^&*()_+-=[]{};\':"|,.<>/?)')
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Validates that password and confirm password match
 * @param {string} password - Password
 * @param {string} confirmPassword - Confirm password
 * @returns {Object} - { isValid: boolean, error: string }
 */
export function validatePasswordMatch(password, confirmPassword) {
  if (!password || !confirmPassword) {
    return {
      isValid: false,
      error: 'Both password fields are required'
    }
  }

  if (password !== confirmPassword) {
    return {
      isValid: false,
      error: 'Passwords do not match'
    }
  }

  return {
    isValid: true,
    error: null
  }
}

/**
 * Gets password strength score (0-100)
 * @param {string} password - Password to evaluate
 * @returns {number} - Strength score from 0 to 100
 */
export function getPasswordStrength(password) {
  if (!password) return 0

  let score = 0

  // Length score (up to 40 points)
  if (password.length >= 15) score += 20
  if (password.length >= 20) score += 10
  if (password.length >= 25) score += 10

  // Character variety (up to 60 points)
  if (/[a-z]/.test(password)) score += 15
  if (/[A-Z]/.test(password)) score += 15
  if (/[0-9]/.test(password)) score += 15
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 15

  return Math.min(score, 100)
}

/**
 * Gets password strength label and color
 * @param {number} score - Password strength score (0-100)
 * @returns {Object} - { label: string, color: string }
 */
export function getPasswordStrengthLabel(score) {
  if (score >= 80) {
    return { label: 'Strong', color: '#34c759' }
  } else if (score >= 60) {
    return { label: 'Good', color: '#ff9500' }
  } else if (score >= 40) {
    return { label: 'Fair', color: '#ff9500' }
  } else if (score > 0) {
    return { label: 'Weak', color: '#ff3b30' }
  }
  return { label: 'Very Weak', color: '#ff3b30' }
}

/**
 * Format password requirements as a list
 * @returns {Array} - Array of requirement objects
 */
export function getPasswordRequirements() {
  return [
    { text: 'At least 15 characters long', regex: /.{15,}/ },
    { text: 'Contains uppercase letter (A-Z)', regex: /[A-Z]/ },
    { text: 'Contains lowercase letter (a-z)', regex: /[a-z]/ },
    { text: 'Contains number (0-9)', regex: /[0-9]/ },
    { text: 'Contains special character (!@#$%...)', regex: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/ }
  ]
}

/**
 * Check which requirements a password meets
 * @param {string} password - Password to check
 * @returns {Array} - Array of requirement objects with 'met' boolean
 */
export function checkPasswordRequirements(password) {
  const requirements = getPasswordRequirements()
  return requirements.map(req => ({
    ...req,
    met: password ? req.regex.test(password) : false
  }))
}

/**
 * Validates email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid email format
 */
export function validateEmail(email) {
  if (!email) return false
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email.trim())
}
