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
      // Parse the date string and set to midnight local time to avoid timezone issues
      const dueDate = new Date(dateString + 'T00:00:00')
      const today = new Date()
      
      // Reset both dates to midnight for accurate day comparison
      today.setHours(0, 0, 0, 0)
      dueDate.setHours(0, 0, 0, 0)
      
      const diffTime = dueDate.getTime() - today.getTime()
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24))

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
      
      // Reset time to compare dates only
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000)
      const taskDate = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate())
      
      // Return true if due today or tomorrow
      return taskDate.getTime() === today.getTime() || taskDate.getTime() === tomorrow.getTime()
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
