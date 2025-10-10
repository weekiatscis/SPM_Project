import { ref } from 'vue'

// Simple event bus for project-related events
const projectCreatedListeners = []

export function useProjectEvents() {
  const onProjectCreated = (callback) => {
    projectCreatedListeners.push(callback)

    // Return cleanup function
    return () => {
      const index = projectCreatedListeners.indexOf(callback)
      if (index > -1) {
        projectCreatedListeners.splice(index, 1)
      }
    }
  }

  const emitProjectCreated = (project) => {
    projectCreatedListeners.forEach(callback => callback(project))
  }

  return {
    onProjectCreated,
    emitProjectCreated
  }
}
