import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Home from '../views/Home.vue'
import Projects from '../views/Projects.vue'
import ProjectDetails from '../views/ProjectDetails.vue'
import Login from '../views/Login.vue'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/login', name: 'Login', component: Login, meta: { requiresGuest: true } },
  { path: '/home', name: 'Home', component: Home },
  { path: '/projects', name: 'Projects', component: Projects },
  { path: '/projects/:id', name: 'ProjectDetails', component: ProjectDetails }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  if (!authStore.isAuthenticated && localStorage.getItem('sessionToken')) {
    await authStore.initializeAuth()
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'Home' }) 
  } else {

    if (authStore.isAuthenticated) {
      authStore.resetSessionTimer()
    }
    next()
  }
})

export default router