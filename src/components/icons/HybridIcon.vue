<template>
  <!-- Use ImageIcon for PNG files -->
  <ImageIcon 
    v-if="iconType === 'image'"
    :name="name"
    :size="size"
    :color="color"
    :alt="alt"
    :spin="spin"
  />
  
  <!-- Use BaseIcon for SVG paths -->
  <BaseIcon 
    v-else
    :size="size"
    :color="color"
    :fill="fill"
    :stroke="stroke"
    :stroke-width="strokeWidth"
    :spin="spin"
  >
    <slot />
  </BaseIcon>
</template>

<script>
import BaseIcon from './BaseIcon.vue'
import ImageIcon from './ImageIcon.vue'

export default {
  name: 'HybridIcon',
  components: {
    BaseIcon,
    ImageIcon
  },
  props: {
    name: {
      type: String,
      default: ''
    },
    iconType: {
      type: String,
      default: 'svg',
      validator: (value) => ['svg', 'image'].includes(value)
    },
    size: {
      type: String,
      default: 'md'
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
    alt: {
      type: String,
      default: ''
    },
    spin: {
      type: Boolean,
      default: false
    }
  }
}
</script>
