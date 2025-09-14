<template>
  <svg
    :class="[
      'inline-block',
      sizeClass,
      colorClass,
      { 'animate-spin': spin }
    ]"
    :fill="fill"
    :stroke="stroke"
    :viewBox="viewBox"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <slot />
  </svg>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'BaseIcon',
  props: {
    size: {
      type: String,
      default: 'md',
      validator: (value) => ['xs', 'sm', 'md', 'lg', 'xl', '2xl'].includes(value)
    },
    color: {
      type: String,
      default: 'current'
    },
    fill: {
      type: String,
      default: 'none'
    },
    stroke: {
      type: String,
      default: 'currentColor'
    },
    strokeWidth: {
      type: [String, Number],
      default: 2
    },
    viewBox: {
      type: String,
      default: '0 0 24 24'
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

    const colorClass = computed(() => {
      if (props.color === 'current') return 'text-current'
      
      const colors = {
        primary: 'text-primary-600',
        secondary: 'text-gray-600',
        success: 'text-green-600',
        warning: 'text-yellow-600',
        danger: 'text-red-600',
        info: 'text-blue-600',
        white: 'text-white',
        gray: 'text-gray-500'
      }
      return colors[props.color] || `text-${props.color}`
    })

    return {
      sizeClass,
      colorClass
    }
  }
}
</script>
