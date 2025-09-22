import { ref, onMounted } from 'vue'

export function useUser() {
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const fetchUser = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch('http://localhost:8081/user')
      
      if (!response.ok) {
        throw new Error(`Failed to fetch user: ${response.status}`)
      }
      
      const data = await response.json()
      user.value = data.user
    } catch (err) {
      error.value = err.message
      console.error('Error fetching user:', err)
    } finally {
      loading.value = false
    }
  }

  // Fetch user data when composable is used
  onMounted(() => {
    fetchUser()
  })

  return {
    user,
    loading,
    error,
    fetchUser
  }
}