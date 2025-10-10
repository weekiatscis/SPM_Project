<template>
  <div class="project-comments">
    <!-- Comments Header -->
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-semibold text-gray-900">Project Comments</h3>
      <span class="text-sm text-gray-500">{{ comments.length }} comment{{ comments.length !== 1 ? 's' : '' }}</span>
    </div>

    <!-- Comments List -->
    <div class="space-y-4">
      <div v-if="isLoadingComments" class="text-center py-4">
        <div class="inline-flex items-center">
          <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Loading comments...
        </div>
      </div>

      <div v-else-if="comments.length === 0" class="text-center py-8 text-gray-500">
        <svg class="mx-auto h-12 w-12 text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p>No comments yet</p>
        <p class="text-sm">Be the first to add a comment!</p>
      </div>

      <div v-else class="max-h-64 overflow-y-auto space-y-3">
        <div
          v-for="comment in comments"
          :key="comment.comment_id"
          class="flex space-x-3 p-3 bg-gray-50 rounded-lg"
        >
          <!-- User Avatar -->
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
              <span class="text-white text-sm font-medium">{{ getInitials(getUserName(comment.user_id)) }}</span>
            </div>
          </div>

          <!-- Comment Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <h4 class="text-sm font-medium text-gray-900">{{ getUserName(comment.user_id) }}</h4>
              <span class="text-xs text-gray-500">{{ formatCommentDate(comment.created_at) }}</span>
            </div>
            
            <!-- Comment Text (read-only) -->
            <div class="mt-1">
              <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ comment.comment_text }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Comment Form -->
    <div class="mt-6 pt-4 border-t border-gray-200">
      <div class="flex space-x-3">
        <div class="flex-shrink-0">
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <span class="text-white text-sm font-medium">{{ getInitials(currentUserName) }}</span>
          </div>
        </div>
        <div class="flex-1">
          <textarea
            v-model="newComment"
            placeholder="Add a comment..."
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            :disabled="isAddingComment"
          ></textarea>
          <div class="mt-2 flex justify-end">
            <button
              @click="addComment"
              :disabled="!newComment.trim() || isAddingComment"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isAddingComment ? 'Adding...' : 'Add Comment' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '../../stores/auth'

export default {
  name: 'ProjectComments',
  props: {
    projectId: {
      type: String,
      required: true
    },
    project: {
      type: Object,
      required: true
    }
  },
  emits: ['comments-updated'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    const comments = ref([])
    const isLoadingComments = ref(false)
    const isAddingComment = ref(false)
    const newComment = ref('')
    const userCache = ref({})

    const currentUserId = computed(() => authStore.user?.user_id)
    const currentUserName = computed(() => {
      const user = authStore.user
      if (!user) return 'Me'
      
      // Try different possible name field combinations
      const firstName = user.first_name || user.firstName || ''
      const lastName = user.last_name || user.lastName || ''
      const fullName = `${firstName} ${lastName}`.trim()
      
      // If we have a full name, use it
      if (fullName) return fullName
      
      // Fallback to other possible name fields
      if (user.name) return user.name
      if (user.username) return user.username
      if (user.email) return user.email.split('@')[0]
      
      // Last resort fallback
      return 'Me'
    })

    const getInitials = (name) => {
      if (!name || name === 'Me') return 'ME'
      if (name.length === 1) return name.toUpperCase()
      
      const words = name.split(' ').filter(word => word.length > 0)
      if (words.length === 0) return '??'
      if (words.length === 1) return words[0].substring(0, 2).toUpperCase()
      
      return words.slice(0, 2).map(word => word[0]).join('').toUpperCase()
    }

    const formatCommentDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = now.getTime() - date.getTime()
      const diffMinutes = Math.floor(diffTime / (1000 * 60))
      const diffHours = Math.floor(diffMinutes / 60)
      const diffDays = Math.floor(diffHours / 24)

      if (diffMinutes < 1) return 'just now'
      if (diffMinutes < 60) return `${diffMinutes}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      })
    }

    // Fetch user names from user service
    const fetchUserNames = async (userIds) => {
      for (const userId of userIds) {
        if (!userId || userCache.value[userId]) continue
        
        try {
          // Try to get user details from the user service first
          const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
          
          try {
            const response = await fetch(`${userServiceUrl}/users`)
            if (response.ok) {
              const result = await response.json()
              const user = result.users?.find(u => u.user_id === userId)
              
              if (user) {
                // Try different name field combinations
                const firstName = user.first_name || user.firstName || ''
                const lastName = user.last_name || user.lastName || ''
                const fullName = `${firstName} ${lastName}`.trim()
                
                if (fullName) {
                  userCache.value[userId] = fullName
                  continue
                }
                
                // Fallback to other possible name fields
                if (user.name) {
                  userCache.value[userId] = user.name
                  continue
                }
                
                if (user.username) {
                  userCache.value[userId] = user.username
                  continue
                }
                
                if (user.email) {
                  userCache.value[userId] = user.email.split('@')[0]
                  continue
                }
              }
            }
          } catch (userServiceError) {
            console.warn('User service not available, trying task service fallback')
          }
          
          // Fallback: Try to get user details from task service
          try {
            const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
            const response = await fetch(`${taskServiceUrl}/users/${userId}`)
            
            if (response.ok) {
              const result = await response.json()
              
              if (result.user && result.user.name) {
                userCache.value[userId] = result.user.name
                continue
              }
            }
          } catch (taskServiceError) {
            console.warn('Task service user lookup failed')
          }
          
          // Final fallback: Create a user-friendly fallback name
          const shortId = userId.slice(0, 8)
          const friendlyName = `User-${shortId}`
          userCache.value[userId] = friendlyName
          
        } catch (error) {
          console.error('Failed to fetch user name for', userId, error)
          // Create fallback name even if there's an error
          const shortId = userId.slice(0, 8)
          const friendlyName = `User-${shortId}`
          userCache.value[userId] = friendlyName
        }
      }
    }

    const getUserName = (userId) => {
      if (!userId) return 'Unknown User'
      
      // Check if we have a cached name
      if (userCache.value[userId]) {
        return userCache.value[userId]
      }
      
      // If it's the current user, return their name
      if (userId === currentUserId.value) {
        return currentUserName.value
      }
      
      // Create a user-friendly fallback name from the UUID
      const shortId = userId.slice(0, 8)
      const friendlyName = `User-${shortId}`
      
      // Cache this fallback name
      userCache.value[userId] = friendlyName
      
      // Try to fetch the real name in the background
      fetchUserNames([userId])
      
      return friendlyName
    }

    const fetchComments = async () => {
      if (!props.projectId) return

      isLoadingComments.value = true
      try {
        const projectServiceUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        const response = await fetch(`${projectServiceUrl}/projects/${props.projectId}/comments`)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        const result = await response.json()
        comments.value = result.comments || []
        emit('comments-updated', comments.value.length)
        
        // Fetch user names for all unique user_ids in comments
        const userIds = [...new Set(comments.value.map(comment => comment.user_id))]
        await fetchUserNames(userIds)
        
      } catch (error) {
        console.error('Failed to fetch project comments:', error)
        comments.value = []
      } finally {
        isLoadingComments.value = false
      }
    }

    const addComment = async () => {
      if (!newComment.value.trim() || isAddingComment.value) return

      isAddingComment.value = true
      try {
        const projectServiceUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
        
        const response = await fetch(`${projectServiceUrl}/projects/${props.projectId}/comments`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            comment_text: newComment.value.trim(),
            user_id: currentUserId.value
          })
        })

        const result = await response.json()

        if (!response.ok) {
          throw new Error(result.error || `HTTP ${response.status}`)
        }
        
        if (result.success && result.comment) {
          // Cache the user name for the new comment (use current user's name)
          if (result.comment.user_id === currentUserId.value) {
            userCache.value[result.comment.user_id] = currentUserName.value
          }
          
          // Add the new comment to the list
          comments.value.push(result.comment)
          
          // Clear the input
          newComment.value = ''
          
          // Update parent component
          emit('comments-updated', comments.value.length)
        } else {
          throw new Error(result.error || 'Failed to add comment')
        }

      } catch (error) {
        console.error('Failed to add comment:', error)
        
        // Even if there was an error in the response, the comment might have been added
        // Let's refetch comments to make sure we show the latest state
        try {
          await fetchComments()
        } catch (refetchError) {
          console.error('Failed to refetch comments:', refetchError)
        }
        
        alert(`Failed to add comment: ${error.message}`)
      } finally {
        isAddingComment.value = false
      }
    }

    // Watch for project changes to refetch comments
    watch(() => props.projectId, (newProjectId) => {
      if (newProjectId) {
        fetchComments()
      }
    })

    onMounted(() => {
      if (props.projectId) {
        fetchComments()
      }
    })

    return {
      comments,
      isLoadingComments,
      isAddingComment,
      newComment,
      currentUserName,
      getInitials,
      formatCommentDate,
      getUserName,
      addComment,
      fetchComments
    }
  }
}
</script>

<style scoped>
/* Custom scrollbar for comments list */
.project-comments .max-h-64::-webkit-scrollbar {
  width: 8px;
}

.project-comments .max-h-64::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.project-comments .max-h-64::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.project-comments .max-h-64::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Firefox scrollbar */
.project-comments .max-h-64 {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

/* Animation for comment entries */
.project-comments .space-y-3 > div {
  transition: all 0.2s ease-in-out;
}

.project-comments .space-y-3 > div:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>