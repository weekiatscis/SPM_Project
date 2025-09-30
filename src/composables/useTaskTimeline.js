import { ref, computed, watch } from 'vue'

// Singapore timezone constant
const SINGAPORE_TIMEZONE = 'Asia/Singapore'

/**
 * Utility function to get current date in Singapore timezone
 */
const getSingaporeDate = () => {
  return new Date(new Date().toLocaleString("en-US", { timeZone: SINGAPORE_TIMEZONE }))
}

/**
 * Utility function to format date in Singapore timezone
 */
const formatDateInSingapore = (date, options = {}) => {
  return date.toLocaleDateString('en-US', { 
    ...options, 
    timeZone: SINGAPORE_TIMEZONE 
  })
}

/**
 * Composable for handling task timeline data processing
 * Generates weekly timeline data for chart visualization
 */
export function useTaskTimeline(tasks) {
  const selectedWeekOffset = ref(0) // 0 = current week, -1 = previous week, 1 = next week
  
  /**
   * Get the start of week (Sunday) for a given date
   */
  const getWeekStart = (date) => {
    const d = new Date(date)
    const day = d.getDay() // 0 = Sunday, 1 = Monday, etc.
    const diff = d.getDate() - day
    return new Date(d.setDate(diff))
  }

  /**
   * Get current week date range based on selected offset (Singapore timezone)
   */
  const currentWeekRange = computed(() => {
    const now = getSingaporeDate()
    const currentWeekStart = getWeekStart(now)
    
    // Apply week offset
    const weekStart = new Date(currentWeekStart)
    weekStart.setDate(weekStart.getDate() + (selectedWeekOffset.value * 7))
    
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 6)
    
    return {
      start: weekStart,
      end: weekEnd,
      dates: Array.from({ length: 7 }, (_, i) => {
        const date = new Date(weekStart)
        date.setDate(date.getDate() + i)
        return date
      })
    }
  })

  /**
   * Format date to YYYY-MM-DD string (Singapore timezone)
   */
  const formatDateKey = (date) => {
    // Convert to Singapore timezone and format as YYYY-MM-DD
    const singaporeDate = new Date(date.toLocaleString("en-US", { timeZone: SINGAPORE_TIMEZONE }))
    const year = singaporeDate.getFullYear()
    const month = String(singaporeDate.getMonth() + 1).padStart(2, '0')
    const day = String(singaporeDate.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  /**
   * Filter tasks that are due within the current week and not completed
   */
  const weeklyTasks = computed(() => {
    if (!tasks.value || !Array.isArray(tasks.value)) return []
    
    const { start, end } = currentWeekRange.value
    
    return tasks.value.filter(task => {
      // Skip completed tasks
      if (task.status === 'Completed') return false
      
      // Skip tasks without due dates
      if (!task.dueDate) return false
      
      // Convert task date to Singapore timezone for comparison
      const taskDate = new Date(task.dueDate)
      const taskDateInSingapore = new Date(taskDate.toLocaleString("en-US", { timeZone: SINGAPORE_TIMEZONE }))
      
      // Normalize dates to start of day for proper comparison
      const taskDayStart = new Date(taskDateInSingapore.getFullYear(), taskDateInSingapore.getMonth(), taskDateInSingapore.getDate())
      const weekStartDay = new Date(start.getFullYear(), start.getMonth(), start.getDate())
      const weekEndDay = new Date(end.getFullYear(), end.getMonth(), end.getDate())
      
      return taskDayStart >= weekStartDay && taskDayStart <= weekEndDay
    })
  })

  /**
   * Group tasks by date and count them
   */
  const timelineData = computed(() => {
    const { dates } = currentWeekRange.value
    
    // Initialize data structure
    const tasksByDate = {}
    const dateCounts = []
    const dateLabels = []
    
    dates.forEach(date => {
      const dateKey = formatDateKey(date)
      tasksByDate[dateKey] = []
      dateLabels.push(dateKey)
    })
    
    // Group tasks by date
    weeklyTasks.value.forEach(task => {
      // Convert task date to Singapore timezone and format consistently
      const taskDate = new Date(task.dueDate)
      const taskDateKey = formatDateKey(taskDate)
      
      if (tasksByDate.hasOwnProperty(taskDateKey)) {
        tasksByDate[taskDateKey].push(task)
      }
    })
    
    // Count tasks per date
    dateLabels.forEach(dateKey => {
      dateCounts.push(tasksByDate[dateKey].length)
    })
    
    return {
      dates: dateLabels,
      taskCounts: dateCounts,
      tasksByDate,
      maxCount: Math.max(...dateCounts, 1) // Ensure at least 1 for chart scaling
    }
  })

  /**
   * Get formatted week range string for display (Singapore timezone)
   */
  const weekRangeText = computed(() => {
    const { start, end } = currentWeekRange.value
    const startStr = formatDateInSingapore(start, { 
      month: 'short', 
      day: 'numeric'
    })
    const endStr = formatDateInSingapore(end, { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
    return `${startStr} - ${endStr}`
  })

  /**
   * Get day labels for chart (e.g., ['Sun', 'Mon', 'Tue', ...]) (Singapore timezone)
   */
  const dayLabels = computed(() => {
    const { dates } = currentWeekRange.value
    return dates.map(date => 
      formatDateInSingapore(date, { weekday: 'short' })
    )
  })

  /**
   * Navigation functions
   */
  const goToPreviousWeek = () => {
    selectedWeekOffset.value -= 1
  }

  const goToNextWeek = () => {
    selectedWeekOffset.value += 1
  }

  const goToCurrentWeek = () => {
    selectedWeekOffset.value = 0
  }

  /**
   * Check if current week is selected
   */
  const isCurrentWeek = computed(() => selectedWeekOffset.value === 0)

  /**
   * Get tasks for a specific date
   */
  const getTasksForDate = (dateKey) => {
    return timelineData.value.tasksByDate[dateKey] || []
  }

  /**
   * Get summary statistics
   */
  const weekSummary = computed(() => {
    const total = weeklyTasks.value.length
    const statusCounts = weeklyTasks.value.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1
      return acc
    }, {})

    return {
      total,
      byStatus: statusCounts,
      peakDay: timelineData.value.maxCount,
      daysWithTasks: timelineData.value.taskCounts.filter(count => count > 0).length
    }
  })

  return {
    // Data
    timelineData,
    weeklyTasks,
    currentWeekRange,
    weekRangeText,
    dayLabels,
    weekSummary,
    
    // State
    selectedWeekOffset,
    isCurrentWeek,
    
    // Actions
    goToPreviousWeek,
    goToNextWeek,
    goToCurrentWeek,
    getTasksForDate,
    
    // Utilities
    formatDateKey,
    getSingaporeDate,
    formatDateInSingapore
  }
}

// Export timezone utilities for use in other components
export { getSingaporeDate, formatDateInSingapore, SINGAPORE_TIMEZONE }