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
        <div class="flex items-center space-x-2">
          <a-typography-text strong>{{ task.title }}</a-typography-text>
          <a-tooltip v-if="task.recurrence" :title="getRecurrenceTooltip(task.recurrence)">
            <svg 
               class="w-5 h-5 text-blue-500 flex-shrink-0" 
               fill="none" 
               stroke="currentColor" 
               viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </a-tooltip>
        </div>
        <br>
        <a-typography-text type="secondary" style="font-size: 12px;">
          Due: {{ formatDate(task.dueDate) }}
        </a-typography-text>
        <div v-if="task.assignee" style="margin-top: 4px;">
          <a-typography-text type="secondary" style="font-size: 11px;">
            Assignee: {{ task.assignee }}
          </a-typography-text>
        </div>
        <div v-if="task.collaborators && task.collaborators.length > 0" style="margin-top: 2px;">
          <a-typography-text type="secondary" style="font-size: 11px;">
            Collaborators: {{ task.collaborators.length }}
          </a-typography-text>
        </div>
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

    const getRecurrenceTooltip = (recurrence) => {
      const tooltips = {
        'daily': 'Recurring Daily - A new task will be created when completed',
        'weekly': 'Recurring Weekly - A new task will be created when completed',
        'biweekly': 'Recurring Biweekly - A new task will be created when completed',
        'monthly': 'Recurring Monthly - A new task will be created when completed'
      }
      return tooltips[recurrence] || 'Recurring Task'
    }

    return {
      formatDate,
      getStatusColor,
      getStatusText,
      isDueWithin24Hours,
      getRecurrenceTooltip
    }
  }
}
</script>

<style scoped>
.urgent-task {
  border: 1px solid #ff4d4f !important;
}

/* Add hover effect for recurring icon */
.w-5.h-5.text-blue-500 {
  transition: transform 0.2s ease;
}

.w-5.h-5.text-blue-500:hover {
  transform: rotate(180deg);
}
</style>
