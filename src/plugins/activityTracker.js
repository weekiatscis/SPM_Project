export function createActivityTracker(authStore) {
  const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
  
  const trackActivity = () => {
    if (authStore.isAuthenticated) {
      authStore.resetSessionTimer()
    }
  }
  
  const startTracking = () => {
    events.forEach(event => {
      document.addEventListener(event, trackActivity, true)
    })
  }
  
  const stopTracking = () => {
    events.forEach(event => {
      document.removeEventListener(event, trackActivity, true)
    })
  }
  
  return {
    startTracking,
    stopTracking
  }
}