import { ref } from 'vue'

// Global state for notification panel
const isNotificationPanelOpen = ref(false)

export function useNotificationPanel() {
  const openPanel = () => {
    isNotificationPanelOpen.value = true
  }

  const closePanel = () => {
    isNotificationPanelOpen.value = false
  }

  const togglePanel = () => {
    isNotificationPanelOpen.value = !isNotificationPanelOpen.value
  }

  return {
    isNotificationPanelOpen,
    openPanel,
    closePanel,
    togglePanel
  }
}
