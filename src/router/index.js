import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Home from '../views/Home.vue'
import Projects from '../views/Projects.vue'
import ProjectDetails from '../views/ProjectDetails.vue'
import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'
import ProfileSettings from '../views/ProfileSettings.vue'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/login', name: 'Login', component: Login, meta: { requiresGuest: true } },
  { path: '/signup', name: 'Signup', component: Signup, meta: { requiresGuest: true } },
  { path: '/home', name: 'Home', component: Home, meta: { requiresAuth: true } },
  { path: '/projects', name: 'Projects', component: Projects, meta: { requiresAuth: true } },
  { path: '/projects/:id', name: 'ProjectDetails', component: ProjectDetails, meta: { requiresAuth: true } },
  { path: '/profile', name: 'ProfileSettings', component: ProfileSettings, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Try to initialize auth if we have a session token but aren't authenticated
  if (!authStore.isAuthenticated && localStorage.getItem('sessionToken')) {
    await authStore.initializeAuth()
  }
  
  // Handle root path redirect based on authentication status
  if (to.path === '/') {
    if (authStore.isAuthenticated) {
      next({ name: 'Home' })
    } else {
      next({ name: 'Login' })
    }
    return
  }
  
  // Protect routes that require authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'Home' }) 
  } else {
    // Reset session timer for authenticated users
    if (authStore.isAuthenticated) {
      authStore.resetSessionTimer()
    }
    next()
  }
})

export default router