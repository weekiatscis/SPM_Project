/**
 * Date utility functions for calculating time differences and formatting
 */

/**
 * Calculate the time elapsed since a given date
 * @param {string|Date} startDate - The start date (task created_at)
 * @param {string|Date} endDate - The end date (defaults to now)
 * @returns {string} Human-readable time difference (e.g., "2 days 5 hours", "3 hours 30 minutes")
 */
export function calculateTimeTaken(startDate, endDate = new Date()) {
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  // Calculate total milliseconds difference
  const diffMs = end - start
  
  // If negative or zero, return "Just started"
  if (diffMs <= 0) {
    return 'Just started'
  }
  
  // Convert to different units
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  // Format based on duration
  if (diffDays > 0) {
    const remainingHours = diffHours % 24
    if (diffDays === 1) {
      return remainingHours > 0 ? `1 day ${remainingHours}h` : '1 day'
    }
    return remainingHours > 0 ? `${diffDays} days ${remainingHours}h` : `${diffDays} days`
  } else if (diffHours > 0) {
    const remainingMinutes = diffMinutes % 60
    if (diffHours === 1) {
      return remainingMinutes > 0 ? `1 hour ${remainingMinutes}m` : '1 hour'
    }
    return remainingMinutes > 0 ? `${diffHours} hours ${remainingMinutes}m` : `${diffHours} hours`
  } else if (diffMinutes > 0) {
    return diffMinutes === 1 ? '1 minute' : `${diffMinutes} minutes`
  } else {
    return 'Just started'
  }
}

/**
 * Get detailed time breakdown
 * @param {string|Date} startDate - The start date
 * @param {string|Date} endDate - The end date (defaults to now)
 * @returns {Object} Object with days, hours, minutes breakdown
 */
export function getTimeBreakdown(startDate, endDate = new Date()) {
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  const diffMs = end - start
  
  if (diffMs <= 0) {
    return { days: 0, hours: 0, minutes: 0, total: 0 }
  }
  
  const totalMinutes = Math.floor(diffMs / (1000 * 60))
  const totalHours = Math.floor(diffMs / (1000 * 60 * 60))
  const totalDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  const days = totalDays
  const hours = totalHours % 24
  const minutes = totalMinutes % 60
  
  return {
    days,
    hours,
    minutes,
    totalDays,
    totalHours,
    totalMinutes,
    total: diffMs
  }
}
