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
        <div class="flex-1 relative">
          <!-- Contenteditable div for rich text with inline mentions -->
          <div
            ref="commentTextarea"
            contenteditable="true"
            :class="[
              'comment-input-field',
              'w-full min-h-[76px] p-3 border border-gray-300 rounded-lg',
              'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none',
              { 'opacity-50 cursor-not-allowed': isAddingComment }
            ]"
            @input="handleInput"
            @keydown="handleKeydown"
            @paste="handlePaste"
            data-placeholder="Add a comment... (Type @ to mention someone)"
          ></div>
          
          <!-- Mention Dropdown -->
          <div
            v-if="showMentionDropdown"
            class="absolute z-50 mt-1 w-64 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto"
            :style="dropdownStyle"
          >
            <div v-if="isLoadingDepartmentMembers" class="p-3 text-center text-sm text-gray-500">
              <div class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              Loading task members...
            </div>
            <div v-else-if="filteredMentionUsers.length === 0" class="p-3 text-center text-sm text-gray-500">
              No task members found
              <div class="text-xs mt-1 text-gray-400">Only task owners and collaborators can be mentioned</div>
            </div>
            <div v-else>
              <button
                v-for="(user, index) in filteredMentionUsers"
                :key="user.user_id"
                @click="selectMention(user)"
                @mouseenter="selectedMentionIndex = index"
                :class="[
                  'w-full text-left px-3 py-2 hover:bg-blue-50 transition-colors flex items-center gap-2',
                  { 'bg-blue-100': selectedMentionIndex === index }
                ]"
              >
                <div class="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center flex-shrink-0">
                  <span class="text-white text-xs font-medium">{{ getInitials(user.name) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-gray-900 truncate">{{ user.name }}</div>
                  <div class="text-xs text-gray-500 truncate">{{ user.role }}</div>
                </div>
              </button>
            </div>
          </div>
          <div class="flex justify-end items-center mt-2">
            <button
              @click="addComment"
              :disabled="isButtonDisabled"
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
import { ref, computed, onMounted, watch, nextTick } from 'vue'
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
    const commentTextarea = ref(null)
    
    // Mention functionality
    const departmentMembers = ref([])
    const isLoadingDepartmentMembers = ref(false)
    const showMentionDropdown = ref(false)
    const mentionSearchQuery = ref('')
    const mentionStartPos = ref(0)
    const selectedMentionIndex = ref(0)
    const dropdownStyle = ref({})
    const mentionedUsers = ref([])

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

    // Computed property for button disabled state
    const isButtonDisabled = computed(() => {
      const hasContent = newComment.value.trim() || mentionedUsers.value.length > 0
      const disabled = !hasContent || isAddingComment.value
      return disabled
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

    // Fetch task-related members for mentions (owner + collaborators only)
    const fetchTaskRelatedMembers = async () => {
      if (!props.task) return
      
      isLoadingDepartmentMembers.value = true
      try {
        const taskRelatedUserIds = new Set()
        
        // Add task owner
        if (props.task.owner_id) {
          taskRelatedUserIds.add(props.task.owner_id)
        }
        
        // Add collaborators
        if (props.task.collaborators && Array.isArray(props.task.collaborators)) {
          props.task.collaborators.forEach(collaboratorId => {
            if (collaboratorId) {
              taskRelatedUserIds.add(collaboratorId)
            }
          })
        }
        
        // Remove current user from mention list
        taskRelatedUserIds.delete(currentUserId.value)
        
        // Convert to array and fetch user details
        const userIds = Array.from(taskRelatedUserIds)
        
        if (userIds.length === 0) {
          departmentMembers.value = []
          return
        }
        
        // Fetch user details for each task-related user
        const taskRelatedUsers = []
        
        for (const userId of userIds) {
          try {
            const userServiceUrl = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8081'
            const response = await fetch(`${userServiceUrl}/users/${userId}`)
            
            if (response.ok) {
              const data = await response.json()
              if (data.user) {
                taskRelatedUsers.push({
                  user_id: data.user.user_id,
                  name: data.user.name || `User ${userId.slice(0, 8)}`,
                  role: data.user.role || 'Member'
                })
              }
            }
          } catch (error) {
            console.error(`Failed to fetch user ${userId}:`, error)
            // Add fallback user data
            taskRelatedUsers.push({
              user_id: userId,
              name: `User ${userId.slice(0, 8)}`,
              role: 'Member'
            })
          }
        }
        
        departmentMembers.value = taskRelatedUsers
        
      } catch (error) {
        console.error('Failed to fetch task-related members:', error)
        departmentMembers.value = []
      } finally {
        isLoadingDepartmentMembers.value = false
      }
    }
    
    // Filtered mention users based on search query
    const filteredMentionUsers = computed(() => {
      if (!mentionSearchQuery.value) {
        return departmentMembers.value
      }
      
      const query = mentionSearchQuery.value.toLowerCase()
      return departmentMembers.value.filter(user => 
        user.name.toLowerCase().includes(query) ||
        user.role.toLowerCase().includes(query)
      )
    })
    
    // Handle contenteditable input for mention detection
    const handleInput = () => {
      if (!commentTextarea.value) return
      
      // Get the text content
      const text = getTextContent()
      newComment.value = text
      
      // Update mentions array based on current mention spans
      updateMentionsFromDOM()
      
      // Detect @ mentions for dropdown
      const lastAtIndex = text.lastIndexOf('@')
      
      if (lastAtIndex !== -1) {
        const textAfterAt = text.substring(lastAtIndex + 1)
        
        // Check if we're still typing a mention (no space or newline after @)
        if (!textAfterAt.includes(' ') && !textAfterAt.includes('\n')) {
          mentionStartPos.value = lastAtIndex
          
          // Only reset selected index if the search query actually changed
          const previousQuery = mentionSearchQuery.value
          mentionSearchQuery.value = textAfterAt
          
          if (previousQuery !== textAfterAt) {
            selectedMentionIndex.value = 0
          }
          
          showMentionDropdown.value = true
          
          calculateDropdownPosition()
          
          if (departmentMembers.value.length === 0 && !isLoadingDepartmentMembers.value) {
            fetchTaskRelatedMembers()
          }
        } else {
          showMentionDropdown.value = false
          mentionSearchQuery.value = ''
        }
      } else {
        showMentionDropdown.value = false
        mentionSearchQuery.value = ''
        mentionStartPos.value = 0
      }
    }
    
    // Get text content from contenteditable, preserving spaces
    const getTextContent = () => {
      if (!commentTextarea.value) return ''
      
      let text = ''
      const traverse = (node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          text += node.textContent
        } else if (node.nodeType === Node.ELEMENT_NODE) {
          if (node.classList && node.classList.contains('mention-tag')) {
            // For mention spans, get the data-name attribute
            text += '@' + (node.getAttribute('data-name') || node.textContent.replace('@', ''))
          } else {
            // Traverse child nodes
            node.childNodes.forEach(traverse)
          }
        }
      }
      
      commentTextarea.value.childNodes.forEach(traverse)
      return text
    }
    
    // Update mentionedUsers array based on mention spans in DOM
    const updateMentionsFromDOM = () => {
      if (!commentTextarea.value) return
      
      const mentionSpans = commentTextarea.value.querySelectorAll('.mention-tag')
      const currentMentions = []
      
      mentionSpans.forEach(span => {
        const userId = span.getAttribute('data-user-id')
        const userName = span.getAttribute('data-name')
        if (userId && userName) {
          currentMentions.push({ user_id: userId, name: userName })
        }
      })
      
      mentionedUsers.value = currentMentions
    }
    
    // Handle paste to strip formatting
    const handlePaste = (event) => {
      event.preventDefault()
      const text = event.clipboardData.getData('text/plain')
      document.execCommand('insertText', false, text)
    }
    
    // Calculate dropdown position relative to cursor
    const calculateDropdownPosition = () => {
      if (!commentTextarea.value) return
      
      // Simple positioning below the textarea
      dropdownStyle.value = {
        bottom: 'auto',
        left: '0px'
      }
    }
    
    // Handle keyboard navigation in mention dropdown
    const handleKeydown = (event) => {
      // Handle Ctrl/Cmd + Enter to submit
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault()
        addComment()
        return
      }
      
      if (!showMentionDropdown.value) return
      
      if (event.key === 'ArrowDown') {
        event.preventDefault()
        event.stopPropagation()
        selectedMentionIndex.value = Math.min(
          selectedMentionIndex.value + 1,
          filteredMentionUsers.value.length - 1
        )
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        event.stopPropagation()
        selectedMentionIndex.value = Math.max(selectedMentionIndex.value - 1, 0)
      } else if (event.key === 'Enter' && !event.ctrlKey && !event.metaKey) {
        if (filteredMentionUsers.value.length > 0) {
          event.preventDefault()
          event.stopPropagation()
          selectMention(filteredMentionUsers.value[selectedMentionIndex.value])
        }
      } else if (event.key === 'Escape') {
        event.preventDefault()
        event.stopPropagation()
        showMentionDropdown.value = false
      }
    }
    
    // Select a mention from dropdown
    const selectMention = (user) => {
      if (!commentTextarea.value) return
      
      // Check if user is already mentioned
      if (mentionedUsers.value.find(u => u.user_id === user.user_id)) {
        showMentionDropdown.value = false
        mentionSearchQuery.value = ''
        return
      }
      
      // Save the current selection/cursor position
      const selection = window.getSelection()
      const range = selection.getRangeAt(0)
      
      // Find the @ character and the text after it to replace
      const textNode = range.startContainer
      let container = textNode.nodeType === Node.TEXT_NODE ? textNode : commentTextarea.value
      
      // Get all text up to cursor
      const textBeforeCursor = container.nodeType === Node.TEXT_NODE 
        ? container.textContent.substring(0, range.startOffset)
        : getTextContent()
      
      const atIndex = textBeforeCursor.lastIndexOf('@')
      
      if (atIndex !== -1) {
        // Calculate how many characters to delete (@ + search query)
        const charsToDelete = textBeforeCursor.length - atIndex
        
        // Delete the @ and search text
        for (let i = 0; i < charsToDelete; i++) {
          document.execCommand('delete', false)
        }
        
        // Create a mention span element
        const mentionSpan = document.createElement('span')
        mentionSpan.className = 'mention-tag'
        mentionSpan.contentEditable = 'false'
        mentionSpan.setAttribute('data-user-id', user.user_id)
        mentionSpan.setAttribute('data-name', user.name)
        mentionSpan.textContent = '@' + user.name
        
        // Insert the mention span
        const newRange = selection.getRangeAt(0)
        newRange.insertNode(mentionSpan)
        
        // Add a space after the mention
        const spaceNode = document.createTextNode(' ')
        mentionSpan.parentNode.insertBefore(spaceNode, mentionSpan.nextSibling)
        
        // Move cursor after the space
        newRange.setStartAfter(spaceNode)
        newRange.setEndAfter(spaceNode)
        selection.removeAllRanges()
        selection.addRange(newRange)
        
        // Update the mentions array
        mentionedUsers.value.push({
          user_id: user.user_id,
          name: user.name
        })
      }
      
      // Close dropdown
      showMentionDropdown.value = false
      mentionSearchQuery.value = ''
      mentionStartPos.value = 0
      
      // Focus back to contenteditable
      commentTextarea.value.focus()
      
      // Trigger input event to update state
      handleInput()
    }
    
    const addComment = async () => {
      // Allow comment if there's text OR mentions
      const hasContent = newComment.value.trim() || mentionedUsers.value.length > 0
      if (!hasContent || !canComment.value || isAddingComment.value) return

      console.log('Starting to add comment...')
      isAddingComment.value = true
      
      // Store the initial comment count to compare later
      const initialCommentCount = comments.value.length
      
      try {
        // The final comment text already includes inline mentions from getTextContent()
        // No need to prepend mentions again as they're already in the text
        const finalCommentText = newComment.value.trim()
        
        console.log('Sending comment with text:', finalCommentText)
        console.log('Mentioned users:', mentionedUsers.value.map(u => u.name))
        
        const taskServiceUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const response = await fetch(`${taskServiceUrl}/tasks/${props.taskId}/comments`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            comment_text: finalCommentText,
            user_id: currentUserId.value
          })
        })

        console.log('Response status:', response.status, response.statusText)
        
        // Parse the response JSON
        let result
        try {
          result = await response.json()
          console.log('Response data:', result)
        } catch (parseError) {
          console.error('Failed to parse response JSON:', parseError)
          throw new Error('Invalid response from server')
        }

        // Check if response is not OK (status >= 400)
        if (!response.ok) {
          console.error('Response not OK:', result)
          throw new Error(result.error || `Failed to add comment: ${response.statusText}`)
        }
        
        // Verify the response has the expected structure
        if (!result.success || !result.comment) {
          console.error('Invalid response structure:', result)
          throw new Error('Server returned invalid response structure')
        }
        
        console.log('Comment created successfully:', result.comment)
        
        // Cache the user name for the new comment
        if (result.comment.user_name) {
          userCache.value[result.comment.user_id] = result.comment.user_name
        }
        
        // IMPORTANT: Clear input BEFORE adding comment to list
        // This prevents Vue from trying to render tags that are being removed
        clearCommentInputSync()
        
        // Wait for Vue to finish clearing the input area
        await nextTick()
        
        // NOW add the new comment to the beginning of the list
        comments.value.unshift(result.comment)
        
        console.log('Comment added successfully, state cleared')
        emit('comments-updated', comments.value.length)

      } catch (error) {
        console.error('Error in addComment:', error.message, error)
        
        // The comment might have been created despite the error
        // Refetch to check and update the UI accordingly
        try {
          console.log('Refetching comments to verify...')
          await fetchComments()
          
          // Check if a NEW comment was added by comparing counts
          if (comments.value.length > initialCommentCount) {
            console.log('Comment was actually created successfully! Clearing input...')
            // The comment was added successfully, clear the input
            clearCommentInputSync()
            await nextTick()
            // Don't show error since the comment was actually added
            return
          } else {
            console.log('No new comment found after refetch')
          }
        } catch (refetchError) {
          console.error('Failed to refetch comments:', refetchError)
        }
        
        // Show error only if comment was not actually added
        alert('Failed to add comment. Please try again.')
      } finally {
        isAddingComment.value = false
        console.log('Finally block: isAddingComment set to false')
      }
    }
    
    // Helper function to clear comment input state
    const clearCommentInputSync = () => {
      // Clear all reactive state
      newComment.value = ''
      mentionedUsers.value = []
      showMentionDropdown.value = false
      mentionSearchQuery.value = ''
      mentionStartPos.value = 0
      
      // Clear the contenteditable div
      if (commentTextarea.value) {
        commentTextarea.value.innerHTML = ''
      }
    }

    // Watch for task changes to refetch comments and task-related members
    watch(() => props.taskId, (newTaskId) => {
      if (newTaskId) {
        fetchComments()
      }
    })

    // Watch for task object changes (including collaborators) to refetch task-related members
    watch(() => props.task, (newTask) => {
      if (newTask) {
        // Clear existing members to force refetch when dropdown is opened
        departmentMembers.value = []
      }
    }, { deep: true })

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
      isButtonDisabled,
      getInitials,
      formatCommentDate,
      getUserName,
      addComment,
      fetchComments,
      commentTextarea,
      showMentionDropdown,
      filteredMentionUsers,
      isLoadingDepartmentMembers,
      selectedMentionIndex,
      dropdownStyle,
      handleInput,
      handleKeydown,
      handlePaste,
      selectMention,
      mentionedUsers
    }
  }
}
</script>

<style>
/* Global styles for dynamically created mention tags (unscoped) */
.mention-tag {
  display: inline-flex !important;
  align-items: center;
  padding: 2px 8px !important;
  margin: 0 2px;
  background-color: #dbeafe !important;
  color: #2563eb !important;
  border-radius: 4px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  user-select: none;
  cursor: default;
  vertical-align: middle;
}

.mention-tag:hover {
  background-color: #bfdbfe !important;
}
</style>

<style scoped>
/* Comment input field (contenteditable) */
.comment-input-field {
  font-size: 14px;
  line-height: 1.5;
  color: #374151;
  font-family: inherit;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Placeholder for empty contenteditable */
.comment-input-field:empty:before {
  content: attr(data-placeholder);
  color: #9ca3af;
  pointer-events: none;
}

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