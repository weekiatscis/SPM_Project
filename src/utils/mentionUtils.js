/**
 * Utility functions for @mention functionality in comments
 */

/**
 * Extract @mentions from text
 * @param {string} text - The text to search for mentions
 * @returns {Array} Array of mentioned usernames (without @)
 */
export function extractMentions(text) {
  if (!text) return []
  
  const mentionRegex = /@(\w+)/g
  const mentions = []
  let match
  
  while ((match = mentionRegex.exec(text)) !== null) {
    mentions.push(match[1])
  }
  
  return [...new Set(mentions)] // Remove duplicates
}

/**
 * Parse comment text and replace @mentions with styled spans
 * @param {string} text - The comment text
 * @param {Object} userCache - Cache of user names
 * @returns {string} HTML string with styled mentions
 */
export function parseMentions(text, userCache = {}) {
  if (!text) return ''
  
  return text.replace(/@(\w+)/g, (match, username) => {
    // Check if this is a valid user
    const userId = findUserIdByUsername(username, userCache)
    if (userId) {
      return `<span class="mention" data-user-id="${userId}" data-username="${username}">@${username}</span>`
    }
    return match // Return original if not a valid user
  })
}

/**
 * Find user ID by username in the user cache
 * @param {string} username - The username to search for
 * @param {Object} userCache - Cache of user data
 * @returns {string|null} User ID if found, null otherwise
 */
function findUserIdByUsername(username, userCache) {
  // This would need to be implemented based on your user cache structure
  // For now, return null as we'll handle user lookup in the backend
  return null
}

/**
 * Get mention suggestions based on query
 * @param {Array} allUsers - All available users
 * @param {string} query - The search query
 * @param {string} currentUserId - Current user's ID to exclude
 * @returns {Array} Filtered users
 */
export function getMentionSuggestions(allUsers, query, currentUserId) {
  if (!query || query.length < 1) return []
  
  const lowerQuery = query.toLowerCase()
  return allUsers
    .filter(user => 
      user.user_id !== currentUserId &&
      (user.name?.toLowerCase().includes(lowerQuery) ||
       user.email?.toLowerCase().includes(lowerQuery) ||
       user.username?.toLowerCase().includes(lowerQuery))
    )
    .slice(0, 5) // Limit to 5 suggestions
}

/**
 * Handle keydown events for mention functionality
 * @param {Event} event - The keyboard event
 * @param {Array} suggestions - Current suggestions
 * @param {number} selectedIndex - Currently selected index
 * @param {Function} onSelect - Callback when a suggestion is selected
 * @returns {boolean} Whether the event was handled
 */
export function handleMentionKeydown(event, suggestions, selectedIndex, onSelect) {
  if (!suggestions || suggestions.length === 0) return false
  
  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      onSelect(Math.max(0, selectedIndex - 1))
      return true
    case 'ArrowDown':
      event.preventDefault()
      onSelect(Math.min(suggestions.length - 1, selectedIndex + 1))
      return true
    case 'Enter':
      event.preventDefault()
      if (suggestions[selectedIndex]) {
        onSelect(suggestions[selectedIndex])
      }
      return true
    case 'Escape':
      event.preventDefault()
      return true
  }
  
  return false
}

/**
 * Insert mention into textarea at cursor position
 * @param {HTMLTextAreaElement} textarea - The textarea element
 * @param {string} username - The username to insert
 */
export function insertMention(textarea, username) {
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = textarea.value
  const before = text.substring(0, start)
  const after = text.substring(end)
  
  // Find the last @ in the text before cursor
  const lastAtIndex = before.lastIndexOf('@')
  if (lastAtIndex !== -1) {
    // Replace from @ to cursor with @username
    const newText = text.substring(0, lastAtIndex) + `@${username} ` + after
    textarea.value = newText
    
    // Set cursor position after the mention
    const newCursorPos = lastAtIndex + username.length + 2
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  } else {
    // Insert at cursor position
    const newText = before + `@${username} ` + after
    textarea.value = newText
    
    // Set cursor position after the mention
    const newCursorPos = start + username.length + 2
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  }
  
  // Trigger input event to update v-model
  textarea.dispatchEvent(new Event('input', { bubbles: true }))
}
