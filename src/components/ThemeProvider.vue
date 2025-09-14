<template>
  <a-config-provider :theme="antdTheme">
    <slot />
  </a-config-provider>
</template>

<script>
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme'
import { theme } from 'ant-design-vue'

export default {
  name: 'ThemeProvider',
  setup() {
    const { isDarkMode } = useTheme()
    
    const antdTheme = computed(() => ({
      algorithm: isDarkMode.value ? theme.darkAlgorithm : theme.defaultAlgorithm,
      token: {
        // Customize colors for better dark mode experience
        colorPrimary: '#1890ff',
        colorSuccess: '#52c41a',
        colorWarning: '#faad14',
        colorError: '#ff4d4f',
        colorInfo: '#1890ff',
        // Dark mode specific tokens
        ...(isDarkMode.value && {
          colorBgBase: '#141414',
          colorBgContainer: '#1f1f1f',
          colorBgElevated: '#262626',
          colorBorder: '#424242',
          colorText: '#ffffff',
          colorTextSecondary: '#a6a6a6',
          colorTextTertiary: '#737373',
          colorTextQuaternary: '#595959',
        })
      }
    }))
    
    return {
      antdTheme
    }
  }
}
</script>
