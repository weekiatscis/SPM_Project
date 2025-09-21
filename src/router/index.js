import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Projects from '../views/Projects.vue'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', name: 'Home', component: Home },
  { path: '/projects', name: 'Projects', component: Projects }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router


