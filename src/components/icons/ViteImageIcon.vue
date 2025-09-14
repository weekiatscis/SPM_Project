<template>
  <img
    :src="iconUrl"
    :alt="alt"
    :class="[
      'inline-block object-contain',
      sizeClass,
      { 'animate-spin': spin }
    ]"
    :style="{ filter: colorFilter }"
    @error="onImageError"
    @load="onImageLoad"
  />
</template>

<script>
import { computed, ref } from 'vue'

export default {
  name: 'ViteImageIcon',
  props: {
    name: {
      type: String,
      required: true
    },
    size: {
      type: String,
      default: 'md'
    },
    color: {
      type: String,
      default: 'current'
    },
    alt: {
      type: String,
      default: ''
    },
    spin: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const sizeClass = computed(() => {
      const sizes = {
        xs: 'w-3 h-3',
        sm: 'w-4 h-4',
        md: 'w-5 h-5',
        lg: 'w-6 h-6',
        xl: 'w-8 h-8',
        '2xl': 'w-10 h-10'
      }
      return sizes[props.size]
    })

    const iconUrl = computed(() => {
      // Use public icons path for all icons
      return `/icons/${props.name}.png`
    })

    const colorFilter = computed(() => {
      if (props.color === 'current' || props.color === 'inherit') {
        return 'none'
      }
      
      const colorFilters = {
        primary: 'hue-rotate(210deg) saturate(1.5) brightness(0.9)',
        secondary: 'grayscale(0.5) brightness(0.7)',
        success: 'hue-rotate(120deg) saturate(1.2)',
        warning: 'hue-rotate(45deg) saturate(1.3)',
        danger: 'hue-rotate(0deg) saturate(1.5) brightness(0.8)',
        info: 'hue-rotate(200deg) saturate(1.2)',
        white: 'brightness(0) invert(1)',
        gray: 'grayscale(1) brightness(0.6)'
      }
      
      return colorFilters[props.color] || 'none'
    })

    const onImageError = (event) => {
      console.error(`Failed to load icon: ${props.name} from ${event.target.src}`)
    }

    const onImageLoad = () => {
      console.log(`Successfully loaded icon: ${props.name}`)
    }

    return {
      sizeClass,
      iconUrl,
      colorFilter,
      onImageError,
      onImageLoad
    }
  }
}
</script>
