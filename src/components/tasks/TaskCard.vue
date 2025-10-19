<template>
  <a-card
    :hoverable="true"
    size="small"
    :style="{ 
      width: '100%',
      marginLeft: task.isSubtask ? '32px' : '0',
      borderLeft: task.isSubtask ? '3px solid #1890ff' : 'none'
    }"
    :class="[
      'cursor-pointer',
      'task-card',
      { 'urgent-task': isDueWithin24Hours(task.dueDate) && task.status !== 'Completed' },
      { 'subtask-card': task.isSubtask },
      { 'parent-task-card': task.isParent }
    ]"
  >
    <a-row justify="space-between" align="middle">
      <a-col :span="16">
        <div class="flex items-center space-x-2">
          <!-- Expand/Collapse button for parent tasks with subtasks -->
          <button 
            v-if="hasSubtasks && !task.isSubtask"
            @click.stop="$emit('toggle-expand', task.id)"
            class="expand-button"
          >
            <svg 
              class="w-4 h-4 text-gray-500" 
              :class="{ 'rotate-90': isExpanded }"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          
          <div @click="$emit('view-details', task)" class="flex-1">
            <a-typography-text :strong="!task.isSubtask" :class="{ 'subtask-title': task.isSubtask }">
              {{ task.title }}
            </a-typography-text>
            
            <!-- Subtask badge -->
            <a-tag v-if="task.isSubtask" color="blue" size="small" style="font-size: 10px; margin-left: 8px;">
              Subtask
            </a-tag>
            
            <a-tooltip v-if="task.recurrence" :title="getRecurrenceTooltip(task.recurrence)">
              <svg 
                 class="w-5 h-5 text-blue-500 flex-shrink-0 inline-block ml-2" 
                 fill="none" 
                 stroke="currentColor" 
                 viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </a-tooltip>
          </div>
        </div>
        <br>
        <div @click="$emit('view-details', task)">
          <a-typography-text type="secondary" :style="{ fontSize: task.isSubtask ? '11px' : '12px' }">
            Due: {{ formatDate(task.dueDate) }}
          </a-typography-text>
          <div v-if="task.assignee" style="margin-top: 4px;">
            <a-typography-text type="secondary" :style="{ fontSize: task.isSubtask ? '10px' : '11px' }">
              Assignee: {{ task.assignee }}
            </a-typography-text>
          </div>
          <div v-if="task.collaborators && task.collaborators.length > 0" style="margin-top: 2px;">
            <a-typography-text type="secondary" :style="{ fontSize: task.isSubtask ? '10px' : '11px' }">
              Collaborators: {{ task.collaborators.length }}
            </a-typography-text>
          </div>
        </div>
      </a-col>
      <a-col :span="8" style="text-align: right;">
        <a-tag :color="getStatusColor(task.status)" :size="task.isSubtask ? 'small' : 'default'">
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
    },
    isExpanded: {
      type: Boolean,
      default: false
    },
    hasSubtasks: {
      type: Boolean,
      default: false
    }
  },
  emits: ['view-details', 'toggle-expand'],
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

/* Expand button */
.expand-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.expand-button:hover {
  background-color: #f0f0f0;
}

.expand-button svg {
  transition: transform 0.2s ease;
}

.expand-button svg.rotate-90 {
  transform: rotate(90deg);
}

/* Subtask styling */
.subtask-card {
  background-color: #f0f5ff;
  border-left-width: 3px !important;
  position: relative;
}

.subtask-title {
  font-size: 14px;
  color: #595959;
}

/* Parent task styling */
.parent-task-card {
  font-weight: 500;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

/* Add hover effect for recurring icon */
.w-5.h-5.text-blue-500 {
  transition: transform 0.2s ease;
}

.w-5.h-5.text-blue-500:hover {
  transform: rotate(180deg);
}

/* Enhanced card transitions */
.task-card {
  transition: all 0.2s ease-in-out;
}

.task-card:hover {
  transform: translateY(-2px);
}

.subtask-card:hover {
  transform: translateX(2px) translateY(-1px);
  background-color: #e6f7ff;
}
</style>
