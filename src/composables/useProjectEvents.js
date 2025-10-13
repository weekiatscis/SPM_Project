import { ref } from 'vue'

// Simple event bus for project-related events
const projectCreatedListeners = []
const projectUpdatedListeners = []
const projectDeletedListeners = []

export function useProjectEvents() {
  // Project Created
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

  // Project Updated
  const onProjectUpdated = (callback) => {
    projectUpdatedListeners.push(callback)

    // Return cleanup function
    return () => {
      const index = projectUpdatedListeners.indexOf(callback)
      if (index > -1) {
        projectUpdatedListeners.splice(index, 1)
      }
    }
  }

  const emitProjectUpdated = (project) => {
    projectUpdatedListeners.forEach(callback => callback(project))
  }

  // Project Deleted
  const onProjectDeleted = (callback) => {
    projectDeletedListeners.push(callback)

    // Return cleanup function
    return () => {
      const index = projectDeletedListeners.indexOf(callback)
      if (index > -1) {
        projectDeletedListeners.splice(index, 1)
      }
    }
  }

  const emitProjectDeleted = (projectId) => {
    projectDeletedListeners.forEach(callback => callback(projectId))
  }

  return {
    onProjectCreated,
    emitProjectCreated,
    onProjectUpdated,
    emitProjectUpdated,
    onProjectDeleted,
    emitProjectDeleted
  }
}
