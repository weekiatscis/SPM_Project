import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// Import Ant Design Vue
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import { ConfigProvider } from 'ant-design-vue'

// Router and views will be added later during development

const app = createApp(App)
app.use(Antd)
app.mount('#app')
