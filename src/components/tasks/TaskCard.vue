<template>
  <a-card
    :hoverable="true"
    size="small"
    :style="{ width: '100%' }"
    @click="$emit('view-details', task)"
    :class="[
      'cursor-pointer',
      { 'urgent-task': isDueWithin24Hours(task.dueDate) && task.status !== 'Completed' }
    ]"
  >
    <a-row justify="space-between" align="middle">
      <a-col :span="16">
        <a-typography-text strong>{{ task.title }}</a-typography-text>
        <br>
        <a-typography-text type="secondary" style="font-size: 12px;">
          Due: {{ formatDate(task.dueDate) }}
        </a-typography-text>
      </a-col>
      <a-col :span="8" style="text-align: right;">
        <a-tag :color="getStatusColor(task.status)">
          {{ getStatusText(task.status) }}
        </a-tag>
      </a-col>
    </a-row>
  </a-card>
</template>

<script>
export default {
  name: 'TaskCard',
  props: {
    task: {
      type: Object,
      required: true
    }
  },
  emits: ['view-details'],
  setup(props, { emit }) {
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = date.getTime() - now.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) {
        return `${Math.abs(diffDays)} days overdue`
      } else if (diffDays === 0) {
        return 'today'
      } else if (diffDays === 1) {
        return 'tomorrow'
      } else {
        return `in ${diffDays} days`
      }
    }

    const getStatusColor = (status) => {
      const colors = {
        'Unassigned': 'default',
        'Ongoing': 'blue',
        'Under Review': 'gold',
        'Completed': 'green'
      }
      return colors[status] || 'default'
    }

    const getStatusText = (status) => {
      const texts = {
        'Unassigned': 'Unassigned',
        'Ongoing': 'Ongoing',
        'Under Review': 'Under Review',
        'Completed': 'Completed'
      }
      return texts[status] || 'Unassigned'
    }

    const isDueWithin24Hours = (dueDateString) => {
      if (!dueDateString) return false
      
      const dueDate = new Date(dueDateString)
      const now = new Date()
      const timeDiff = dueDate.getTime() - now.getTime()
      const hoursDiff = timeDiff / (1000 * 60 * 60) // Convert to hours
      
      // Return true if due within next 24 hours (and not overdue)
      return hoursDiff >= 0 && hoursDiff <= 24
    }

    return {
      formatDate,
      getStatusColor,
      getStatusText,
      isDueWithin24Hours
    }
  }
}
</script>

<style scoped>
.urgent-task {
  border: 1px solid #ff4d4f !important;
}
</style>
