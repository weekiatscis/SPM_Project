/**
 * Unit tests for profile validation
 * Tests cover all the specified test cases
 */

import { describe, it, expect } from 'vitest'
import {
  validateDisplayName,
  sanitizeDisplayName,
  validateProfileData,
  sanitizeProfileData,
  PROFILE_CONSTRAINTS,
} from '../profileValidation.js'

describe('profileValidation', () => {
  describe('validateDisplayName', () => {
    // Test Case 1: Successfully update profile with all valid fields
    it('should accept valid display name', () => {
      const result = validateDisplayName('John Doe')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    // Test Case 3: Submit empty required name field
    it('should reject empty display name', () => {
      const result = validateDisplayName('')
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Display name is required')
    })

    it('should reject null display name', () => {
      const result = validateDisplayName(null)
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Display name is required')
    })

    it('should reject undefined display name', () => {
      const result = validateDisplayName(undefined)
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Display name is required')
    })

    // Test Case 4: Submit name field with only white spaces
    it('should reject display name with only whitespace', () => {
      const result = validateDisplayName('   ')
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Display name cannot contain only whitespace')
    })

    it('should reject display name with tabs only', () => {
      const result = validateDisplayName('\t\t\t')
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Display name cannot contain only whitespace')
    })

    it('should reject display name with mixed whitespace', () => {
      const result = validateDisplayName('  \t  \n  ')
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Display name cannot contain only whitespace')
    })

    // Test Case 5: Maximum length display name (20 characters)
    it('should accept display name with exactly 20 characters', () => {
      const maxLengthName = 'A'.repeat(PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH)
      const result = validateDisplayName(maxLengthName)
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
      expect(maxLengthName.length).toBe(20)
    })

    // Test Case 6: Exceed maximum length display name (21 characters)
    it('should reject display name with 21 characters', () => {
      const tooLongName = 'A'.repeat(PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH + 1)
      const result = validateDisplayName(tooLongName)
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Display name must not exceed 20 characters')
      expect(tooLongName.length).toBe(21)
    })

    it('should reject display name exceeding maximum length', () => {
      const tooLongName = 'A'.repeat(50)
      const result = validateDisplayName(tooLongName)
      expect(result.valid).toBe(false)
      expect(result.error).toContain('must not exceed')
    })

    // Test Case 7: Minimum length name (1 character)
    it('should accept display name with 1 character', () => {
      const result = validateDisplayName('A')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    // Test Case 8: Name with unicode/emoji characters
    it('should accept display name with emoji', () => {
      const result = validateDisplayName('John 😀')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with various emojis', () => {
      const result = validateDisplayName('🎉 Party 🎊')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with unicode characters', () => {
      const result = validateDisplayName('José María')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with Chinese characters', () => {
      const result = validateDisplayName('李明')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with Japanese characters', () => {
      const result = validateDisplayName('田中太郎')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with Arabic characters', () => {
      const result = validateDisplayName('محمد')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    // Test Case 9: Name with special characters
    it('should accept display name with special characters', () => {
      const result = validateDisplayName("O'Brien")
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with hyphens', () => {
      const result = validateDisplayName('Mary-Jane')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with dots', () => {
      const result = validateDisplayName('Dr. Smith')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with underscores', () => {
      const result = validateDisplayName('user_name_123')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    // Test Case 10: Leading whitespace in display name
    it('should accept display name with leading whitespace (will be trimmed)', () => {
      const result = validateDisplayName('  John')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    // Test Case 11: Trailing whitespace in display name
    it('should accept display name with trailing whitespace (will be trimmed)', () => {
      const result = validateDisplayName('John  ')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('should accept display name with both leading and trailing whitespace', () => {
      const result = validateDisplayName('  John  ')
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    // Edge case: Whitespace that results in valid length after trim
    it('should validate based on trimmed length', () => {
      // 22 characters total, but only 20 after trim
      const nameWithWhitespace = '  ' + 'A'.repeat(20) + '  '
      const result = validateDisplayName(nameWithWhitespace)
      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    // Edge case: Whitespace that results in exceeding max length after trim
    it('should reject when trimmed length exceeds maximum', () => {
      const nameWithWhitespace = '  ' + 'A'.repeat(21) + '  '
      const result = validateDisplayName(nameWithWhitespace)
      expect(result.valid).toBe(false)
      expect(result.error).toContain('must not exceed')
    })
  })

  describe('sanitizeDisplayName', () => {
    it('should trim leading whitespace', () => {
      const result = sanitizeDisplayName('  John')
      expect(result).toBe('John')
    })

    it('should trim trailing whitespace', () => {
      const result = sanitizeDisplayName('John  ')
      expect(result).toBe('John')
    })

    it('should trim both leading and trailing whitespace', () => {
      const result = sanitizeDisplayName('  John  ')
      expect(result).toBe('John')
    })

    it('should preserve internal whitespace', () => {
      const result = sanitizeDisplayName('  John   Doe  ')
      expect(result).toBe('John   Doe')
    })

    it('should return empty string for null', () => {
      const result = sanitizeDisplayName(null)
      expect(result).toBe('')
    })

    it('should return empty string for undefined', () => {
      const result = sanitizeDisplayName(undefined)
      expect(result).toBe('')
    })

    it('should return empty string for empty string', () => {
      const result = sanitizeDisplayName('')
      expect(result).toBe('')
    })
  })

  describe('validateProfileData', () => {
    it('should validate complete profile data successfully', () => {
      const profileData = {
        displayName: 'John Doe',
      }
      const result = validateProfileData(profileData)
      expect(result.valid).toBe(true)
      expect(result.errors).toEqual({})
    })

    it('should return errors for invalid display name', () => {
      const profileData = {
        displayName: '',
      }
      const result = validateProfileData(profileData)
      expect(result.valid).toBe(false)
      expect(result.errors.displayName).toBeTruthy()
    })

    it('should return errors for display name exceeding max length', () => {
      const profileData = {
        displayName: 'A'.repeat(25),
      }
      const result = validateProfileData(profileData)
      expect(result.valid).toBe(false)
      expect(result.errors.displayName).toContain('must not exceed')
    })
  })

  describe('sanitizeProfileData', () => {
    it('should sanitize all profile fields', () => {
      const profileData = {
        displayName: '  John Doe  ',
      }
      const result = sanitizeProfileData(profileData)
      expect(result.displayName).toBe('John Doe')
    })

    it('should preserve other fields', () => {
      const profileData = {
        displayName: '  John  ',
        email: 'test@example.com',
      }
      const result = sanitizeProfileData(profileData)
      expect(result.displayName).toBe('John')
      expect(result.email).toBe('test@example.com')
    })
  })

  describe('PROFILE_CONSTRAINTS', () => {
    it('should have correct constraint values', () => {
      expect(PROFILE_CONSTRAINTS.DISPLAY_NAME_MAX_LENGTH).toBe(20)
      expect(PROFILE_CONSTRAINTS.DISPLAY_NAME_MIN_LENGTH).toBe(1)
    })
  })
})
