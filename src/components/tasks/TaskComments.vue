<template>
  <div class="task-comments">
    <!-- Comments Header -->
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-semibold text-gray-900">Comments</h3>
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
    <div v-if="canComment" class="mt-6 pt-4 border-t border-gray-200">
      <div class="flex space-x-3">
        <div class="flex-shrink-0">
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <span class="text-white text-xs font-medium">{{ getInitials(currentUserName) }}</span>
          </div>
        </div>
        <div class="flex-1">
          <textarea
            v-model="newComment"
            :disabled="isAddingComment"
            placeholder="Add a comment..."
            rows="3"
            class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            @keydown.ctrl.enter="addComment"
            @keydown.meta.enter="addComment"
          ></textarea>
          <div class="flex justify-end items-center mt-2">
            <button
              @click="addComment"
              :disabled="!newComment.trim() || isAddingComment"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isAddingComment ? 'Posting...' : 'Post Comment' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Message for users who can't comment -->
    <div v-else class="mt-4 pt-3 border-t border-gray-200">
      <div class="text-center py-2 text-gray-500">
        <svg class="mx-auto h-5 w-5 text-gray-400 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <p class="text-xs">Only task owners and collaborators can add comments</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '../../stores/auth'

export default {
  name: 'TaskComments',
  props: {
    taskId: {
      type: String,
      required: true
    },
    task: {
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

    // Check if current user can comment (owner or collaborator, including creators/managers)
    const canComment = computed(() => {
      // If access_info is available, use it
      if (props.task.access_info) {
        return props.task.access_info.can_comment
      }
      
      // Fallback to original logic (owner or collaborator)
      return props.task.owner_id === currentUserId.value || 
             (props.task.collaborators && props.task.collaborators.includes(currentUserId.value))
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

    // Fetch user names from Supabase user table
    const fetchUserNames = async (userIds) => {
      for (const userId of userIds) {
        if (!userId || userCache.value[userId]) continue
        
        try {
          // Fetch user data directly from task service (it has Supabase access)
          const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
          const url = `${taskServiceUrl}/users/${userId}`
          
          const response = await fetch(url)
          
          if (response.ok) {
            const result = await response.json()
            
            if (result.user && result.user.name) {
              userCache.value[userId] = result.user.name
            } else {
              // Fallback to short ID if no name found
              const shortId = userId.slice(0, 8)
              userCache.value[userId] = `User ${shortId}`
            }
          } else {
            // Fallback for failed requests
            const shortId = userId.slice(0, 8)
            userCache.value[userId] = `User ${shortId}`
          }
        } catch (error) {
          // Set a fallback name so we don't keep trying
          const shortId = userId.slice(0, 8)
          userCache.value[userId] = `User ${shortId}`
        }
      }
    }

    const getUserName = (userId) => {
      if (!userId) return 'Unknown User'
      
      // Check if we have a cached name
      if (userCache.value[userId]) {
        return userCache.value[userId]
      }
      
      // Create a user-friendly fallback name from the UUID
      const shortId = userId.slice(0, 8)
      const friendlyName = `User-${shortId}`
      userCache.value[userId] = friendlyName
      
      return friendlyName
    }

    const fetchComments = async () => {
      if (!props.taskId) return

      isLoadingComments.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${props.taskId}/comments`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch comments: ${response.statusText}`)
        }
        
        const result = await response.json()
        comments.value = result.comments || []
        emit('comments-updated', comments.value.length)
        
        // Fetch user names for all unique user_ids in comments
        const userIds = [...new Set(comments.value.map(comment => comment.user_id))]
        await fetchUserNames(userIds)
        
      } catch (error) {
        console.error('Failed to fetch comments:', error)
        comments.value = []
      } finally {
        isLoadingComments.value = false
      }
    }

    const addComment = async () => {
      if (!newComment.value.trim() || !canComment.value || isAddingComment.value) return

      isAddingComment.value = true
      try {
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${props.taskId}/comments`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            comment_text: newComment.value.trim(),
            user_id: currentUserId.value
          })
        })

        const result = await response.json()

        if (!response.ok) {
          throw new Error(result.error || `Failed to add comment: ${response.statusText}`)
        }
        
        if (result.success && result.comment) {
          // Cache the user name for the new comment
          if (result.comment.user_name) {
            userCache.value[result.comment.user_id] = result.comment.user_name
          }
          
          // Add the new comment to the beginning of the list (since backend returns latest first)
          comments.value.unshift(result.comment)
          newComment.value = ''
          emit('comments-updated', comments.value.length)
        } else {
          throw new Error('Server returned invalid response')
        }

      } catch (error) {
        console.error('Failed to add comment:', error)
        
        // Even if there was an error in the response, the comment might have been added
        // Let's refetch comments to make sure we show the latest state
        try {
          await fetchComments()
          // If the comment count changed, the comment was probably added successfully
          if (comments.value.length > 0) {
            newComment.value = '' // Clear the input if comments were updated
            return // Don't show error if the refetch shows the comment was added
          }
        } catch (refetchError) {
          console.error('Failed to refetch comments:', refetchError)
        }
        
        alert('Failed to add comment. Please try again.')
      } finally {
        isAddingComment.value = false
      }
    }

    // Watch for task changes to refetch comments
    watch(() => props.taskId, (newTaskId) => {
      if (newTaskId) {
        fetchComments()
      }
    })

    onMounted(() => {
      if (props.taskId) {
        fetchComments()
      }
    })

    return {
      comments,
      isLoadingComments,
      isAddingComment,
      newComment,
      currentUserName,
      canComment,
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
.task-comments .max-h-64::-webkit-scrollbar {
  width: 8px;
}

.task-comments .max-h-64::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.task-comments .max-h-64::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.task-comments .max-h-64::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Firefox scrollbar */
.task-comments .max-h-64 {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

/* Animation for comment entries */
.task-comments .space-y-3 > div {
  transition: all 0.2s ease-in-out;
}

.task-comments .space-y-3 > div:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>