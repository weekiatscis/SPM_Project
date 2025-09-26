import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import { useAuthStore } from './stores/auth'
import { createActivityTracker } from './plugins/activityTracker'
import './style.css'

// Import Ant Design Vue
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import { ConfigProvider } from 'ant-design-vue'

// Router and views will be added later during development

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(Antd)
app.use(router)

app.mount('#app')

const authStore = useAuthStore()
const activityTracker = createActivityTracker(authStore)
activityTracker.startTracking()
