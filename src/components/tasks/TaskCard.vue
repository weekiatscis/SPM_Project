<template>
  <a-card
    :hoverable="true"
    :style="{ 
      width: '100%'
    }"
    :class="[
      'cursor-pointer',
      'task-card',
      { 'urgent-task': (isDueWithin24Hours(task.dueDate) || isOverdue(task.dueDate)) && task.status !== 'Completed' },
      { 'parent-task-card': task.isParent }
    ]"
    @click="$emit('view-details', task)"
  >
    <!-- Subtle Priority Indicator -->
    <div class="priority-indicator" :class="getPriorityClass(task.priority)"></div>

    <a-row justify="space-between" align="top" :gutter="[16, 0]">
      <a-col :span="17">
        <div class="task-content">
          <div class="task-title-section">
            <div class="title-with-badge">
              <a-typography-text 
                strong
                class="main-title"
              >
                {{ task.title }}
              </a-typography-text>
              
              <!-- Subtask Label - Inline after title -->
              <span v-if="task.isSubtask" class="subtask-label">
                <svg class="subtask-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <span class="subtask-text">Subtask</span>
              </span>
              
              <!-- Due Soon Badge - Inline -->
              <span v-if="isDueWithin24Hours(task.dueDate) && !isOverdue(task.dueDate) && task.status !== 'Completed'" class="urgent-badge">
                <ClockCircleOutlined class="urgent-icon" />
                <span class="urgent-text">Due Soon</span>
              </span>
              
              <!-- Overdue Badge - Inline -->
              <span v-if="isOverdue(task.dueDate) && task.status !== 'Completed'" class="urgent-badge">
                <ClockCircleOutlined class="urgent-icon" />
                <span class="urgent-text">Overdue</span>
              </span>
            </div>
            
            
            <div class="task-badges">
              <!-- Collaborator badge -->
              <a-tag v-if="isCollaborator()" color="purple" class="task-badge">
                Collaborator
              </a-tag>
            
              <a-tooltip v-if="task.recurrence" :title="getRecurrenceTooltip(task.recurrence)">
                <svg 
                   class="recurrence-icon" 
                   fill="none" 
                   stroke="currentColor" 
                   viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </a-tooltip>
            </div>
          </div>
          
          <div class="task-meta">
            <div class="meta-item due-date">
              <a-typography-text type="secondary" class="meta-text">
                Due: {{ formatDate(task.dueDate) }}
              </a-typography-text>
            </div>
            
            <div v-if="(task.status === 'Ongoing' || task.status === 'Under Review') && task.created_at" class="meta-item">
              <a-typography-text type="secondary" class="meta-text">
                <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Time Taken: {{ timeTaken }}
              </a-typography-text>
            </div>
            
            <div v-if="task.assignee" class="meta-item">
              <a-typography-text type="secondary" class="meta-text">
                Assignee: {{ task.assignee }}
              </a-typography-text>
            </div>
            
            <div v-if="task.collaborators && task.collaborators.length > 0" class="meta-item">
              <a-typography-text type="secondary" class="meta-text">
                Collaborators: {{ task.collaborators.length }}
              </a-typography-text>
            </div>
          </div>
        </div>
      </a-col>
      
      <a-col :span="7" class="status-column">
        <a-tag :color="getStatusColor(task.status)" class="status-tag">
          {{ getStatusText(task.status) }}
        </a-tag>
      </a-col>
    </a-row>
  </a-card>
</template>

<script>
import { ClockCircleOutlined } from '@ant-design/icons-vue'
import { calculateTimeTaken } from '../../utils/dateUtils'
import { computed } from 'vue'

export default {
  name: 'TaskCard',
  components: {
    ClockCircleOutlined
  },
  props: {
    task: {
      type: Object,
      required: true
    },
    currentUserId: {
      type: String,
      default: null
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

    const isOverdue = (dueDateString) => {
      if (!dueDateString) return false
      
      const dueDate = new Date(dueDateString + 'T00:00:00')
      const today = new Date()
      
      // Reset both dates to midnight for accurate comparison
      today.setHours(0, 0, 0, 0)
      dueDate.setHours(0, 0, 0, 0)
      
      // Return true if due date is before today
      return dueDate.getTime() < today.getTime()
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

    // Check if current user is a collaborator (not the assignee)
    const isCollaborator = () => {
      try {
        if (!props.currentUserId || !props.task) return false
        
        // User is NOT the assignee
        const isNotAssignee = props.task.owner_id !== props.currentUserId
        
        // User IS in the collaborators list
        const isInCollaborators = props.task.collaborators && 
          Array.isArray(props.task.collaborators) &&
          props.task.collaborators.some(collab => {
            // Handle both string IDs and object collaborators
            if (typeof collab === 'string') {
              return collab === props.currentUserId
            }
            return collab.user_id === props.currentUserId || collab.id === props.currentUserId
          })
        
        return isNotAssignee && isInCollaborators
      } catch (error) {
        console.error('Error in isCollaborator:', error)
        return false
      }
    }
    
    // Calculate time taken for ongoing or under review tasks
    const timeTaken = computed(() => {
      if (!props.task?.created_at) return 'N/A'
      if (props.task.status !== 'Ongoing' && props.task.status !== 'Under Review') return 'N/A'
      return calculateTimeTaken(props.task.created_at)
    })

    const getPriorityClass = (priority) => {
      const priorityNum = typeof priority === 'string' ? parseInt(priority) : (priority || 5)
      
      if (priorityNum >= 8) return 'priority-high'      // 8-10: High (red)
      if (priorityNum >= 5) return 'priority-medium'    // 5-7: Medium (yellow)
      return 'priority-low'                              // 1-4: Low (green)
    }

    return {
      formatDate,
      getStatusColor,
      getStatusText,
      isDueWithin24Hours,
      isOverdue,
      getRecurrenceTooltip,
      isCollaborator,
      timeTaken,
      getPriorityClass
    }
  }
}
</script>

<style scoped>
/* Base Card Styling */
:deep(.ant-card) {
  border-radius: 12px !important;
  border: 1px solid #e5e7eb !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative !important;
}

:deep(.ant-card-body) {
  padding: 20px !important;
}

/* Subtle Priority Indicator */
.priority-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 40%;
  border-radius: 0 4px 4px 0;
  opacity: 0.6;
  transition: all 0.3s ease;
}

.task-card:hover .priority-indicator {
  opacity: 1;
  width: 5px;
}

.priority-high {
  background: linear-gradient(180deg, #ff4d4f 0%, #ff7875 100%);
  box-shadow: 0 0 8px rgba(255, 77, 79, 0.3);
}

.priority-medium {
  background: linear-gradient(180deg, #faad14 0%, #ffc53d 100%);
  box-shadow: 0 0 8px rgba(250, 173, 20, 0.3);
}

.priority-low {
  background: linear-gradient(180deg, #52c41a 0%, #73d13d 100%);
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.3);
}

/* Task Content Layout */
.task-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title-with-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* Title Styling */
.main-title {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #111827 !important;
  line-height: 1.5 !important;
  letter-spacing: -0.01em !important;
}

/* Badges */
.task-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.task-badge {
  font-size: 11px !important;
  font-weight: 600 !important;
  padding: 2px 10px !important;
  border-radius: 6px !important;
  border: none !important;
}

.recurrence-icon {
  width: 18px;
  height: 18px;
  color: #1890ff;
  transition: transform 0.3s ease;
  cursor: pointer;
}

.recurrence-icon:hover {
  transform: rotate(180deg);
}

/* Meta Information */
.task-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
}

.meta-text {
  font-size: 13px !important;
  color: #6b7280 !important;
  font-weight: 500 !important;
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-icon {
  width: 14px;
  height: 14px;
  color: #9ca3af;
  flex-shrink: 0;
}

.due-date .meta-text {
  font-weight: 600 !important;
  color: #374151 !important;
}

/* Status Column */
.status-column {
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  padding-top: 2px;
}

.status-tag {
  font-size: 13px !important;
  font-weight: 600 !important;
  padding: 6px 14px !important;
  border-radius: 8px !important;
  border: none !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

/* Card Hover Effect */
.task-card:hover :deep(.ant-card) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04) !important;
  border-color: #1890ff !important;
}

/* Urgent Task Styling - Design Principles Compliant */
.urgent-task :deep(.ant-card) {
  border: 1.5px solid #ffa39e !important;
  border-left: 4px solid #ff4d4f !important;
  background: #ffffff !important;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.08) !important;
  position: relative;
  overflow: visible !important;
}

/* Subtle top accent - visual hierarchy */
.urgent-task::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #ff4d4f;
  opacity: 0.3;
  border-radius: 12px 12px 0 0;
}

/* Subtask Label - Prominent Design */
.subtask-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #e6f7ff;
  color: #0958d9;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid #91caff;
  letter-spacing: 0.2px;
  margin-left: 8px;
  flex-shrink: 0;
}

.subtask-icon {
  width: 14px;
  height: 14px;
  color: #1890ff;
  flex-shrink: 0;
}

.subtask-text {
  text-transform: uppercase;
  font-size: 10px;
  font-weight: 700;
}

.subtask-label:hover {
  background: #bae0ff;
  border-color: #69b1ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.15);
  transition: all 0.2s ease;
}

/* Clean Badge - Integrated Design */
.urgent-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #fff1f0;
  color: #cf1322;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid #ffccc7;
  letter-spacing: 0.2px;
  margin-left: 8px;
}

.urgent-icon {
  font-size: 12px;
  color: #ff4d4f;
}

.urgent-text {
  text-transform: uppercase;
  font-size: 10px;
  font-weight: 700;
}

/* Hover effect - subtle enhancement */
.urgent-task:hover :deep(.ant-card) {
  border-left-color: #cf1322 !important;
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.12) !important;
}

.urgent-task:hover .urgent-badge {
  background: #ff4d4f;
  color: #ffffff;
  border-color: #ff4d4f;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(255, 77, 79, 0.2);
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

</style>
