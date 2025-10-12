/**
 * Profile validation utility
 * Handles validation for profile update fields
 */

export const PROFILE_CONSTRAINTS = {
  DISPLAY_NAME_MAX_LENGTH: 20,
  DISPLAY_NAME_MIN_LENGTH: 1,
}

/**
 * Validates display name field
 * @param {string} displayName - The display name to validate
 * @returns {Object} - { valid: boolean, error: string|null }
 */
export function validateDisplayName(displayName) {
  // Check if empty (null, undefined, or empty string)
  if (displayName === null || displayName === undefined || displayName === '') {
    return {
      valid: false,
      error: 'Display name is required',
    }
  }

  // Convert to string if not already
  const name = String(displayName)

  // Check if only whitespace
  if (name.trim().length === 0) {
    return {
      valid: false,
      error: 'Display name cannot contain only whitespace',
    }
  }

  // Get the trimmed length for validation
  const trimmedName = name.trim()

  // Check minimum length (after trimming)
  if (trimmedName.length < PROFILE_CONSTRAINTS.DISPLAY_NAME_MIN_LENGTH) {
    return {
      valid: false,
      error: `Display name must be at least ${PROFILE_CONSTRAINTS.DISPLAY_NAME_MIN_LENGTH} character`,
    }
  }

  // Check maximum length (after trimming)
  if (trimmedName.length > PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH) {
    return {
      valid: false,
      error: `Display name must not exceed ${PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH} characters`,
    }
  }

  return {
    valid: true,
    error: null,
  }
}

/**
 * Sanitizes display name by trimming whitespace
 * @param {string} displayName - The display name to sanitize
 * @returns {string} - Sanitized display name
 */
export function sanitizeDisplayName(displayName) {
  if (!displayName) return ''
  return String(displayName).trim()
}

/**
 * Validates email field (optional - for future use)
 * @param {string} email - The email to validate
 * @returns {Object} - { valid: boolean, error: string|null }
 */
export function validateEmail(email) {
  if (!email || email.trim() === '') {
    return {
      valid: false,
      error: 'Email is required',
    }
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.trim())) {
    return {
      valid: false,
      error: 'Please enter a valid email address',
    }
  }

  return {
    valid: true,
    error: null,
  }
}

/**
 * Validates entire profile data
 * @param {Object} profileData - The profile data to validate
 * @returns {Object} - { valid: boolean, errors: Object }
 */
export function validateProfileData(profileData) {
  const errors = {}

  // Validate display name
  const nameValidation = validateDisplayName(profileData.displayName)
  if (!nameValidation.valid) {
    errors.displayName = nameValidation.error
  }

  // Add more field validations here as needed
  // Example: email, bio, etc.

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  }
}

/**
 * Sanitizes entire profile data
 * @param {Object} profileData - The profile data to sanitize
 * @returns {Object} - Sanitized profile data
 */
export function sanitizeProfileData(profileData) {
  return {
    ...profileData,
    displayName: sanitizeDisplayName(profileData.displayName),
    // Add more sanitization as needed
  }
}
