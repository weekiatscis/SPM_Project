import { ref, watch, onMounted } from 'vue'

const THEME_KEY = 'smart-task-manager-theme'
const DARK_CLASS = 'dark'

// Theme state
const isDarkMode = ref(false)

export function useTheme() {
  // Initialize theme from localStorage or system preference
  const initializeTheme = () => {
    const savedTheme = localStorage.getItem(THEME_KEY)
    
    if (savedTheme) {
      isDarkMode.value = savedTheme === 'dark'
    } else {
      // Check system preference
      isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    
    applyTheme()
  }

  // Apply theme to document
  const applyTheme = () => {
    if (isDarkMode.value) {
      document.documentElement.classList.add(DARK_CLASS)
    } else {
      document.documentElement.classList.remove(DARK_CLASS)
    }
  }

  // Toggle theme
  const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value
    localStorage.setItem(THEME_KEY, isDarkMode.value ? 'dark' : 'light')
    applyTheme()
  }

  // Set specific theme
  const setTheme = (theme) => {
    isDarkMode.value = theme === 'dark'
    localStorage.setItem(THEME_KEY, theme)
    applyTheme()
  }

  // Watch for system theme changes
  const watchSystemTheme = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    const handleChange = (e) => {
      // Only update if user hasn't manually set a preference
      if (!localStorage.getItem(THEME_KEY)) {
        isDarkMode.value = e.matches
        applyTheme()
      }
    }
    
    mediaQuery.addEventListener('change', handleChange)
    
    // Return cleanup function
    return () => mediaQuery.removeEventListener('change', handleChange)
  }

  // Initialize on mount
  onMounted(() => {
    initializeTheme()
    return watchSystemTheme()
  })

  // Watch for theme changes and apply them
  watch(isDarkMode, applyTheme)

  return {
    isDarkMode,
    toggleTheme,
    setTheme,
    initializeTheme
  }
}
