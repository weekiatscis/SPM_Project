<template>
  <div 
    class="task-card-wrapper"
    :class="[
      'cursor-pointer',
      getPriorityClass(task.priority),
      { 'urgent-task': (isDueWithin24Hours(task.dueDate) || isOverdue(task.dueDate)) && task.status !== 'Completed' },
      { 'completed-task': task.status === 'Completed' }
    ]"
    @click="$emit('view-details', task)"
  >
    <!-- Glassmorphic Card -->
    <div class="task-card-inner">
      <!-- Left: Priority Accent -->
      <div class="priority-accent" :class="getPriorityClass(task.priority)"></div>
      
      <!-- Main Content -->
      <div class="task-main-content">
        <!-- Top Row: Title + Quick Badges -->
        <div class="task-header">
          <div class="task-title-row">
            <h4 class="task-title">{{ task.title }}</h4>
            
            <!-- Compact Inline Badges -->
            <div class="quick-badges">
              <a-tooltip v-if="task.recurrence" :title="getRecurrenceTooltip(task.recurrence)">
                <span class="badge-icon recurrence">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </span>
              </a-tooltip>
              
              <a-tooltip v-if="task.isSubtask" title="This is a subtask">
                <span class="badge-icon subtask">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </span>
              </a-tooltip>
              
              <a-tooltip v-if="isCollaborator()" title="You are a collaborator">
                <span class="badge-icon collaborator">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </span>
              </a-tooltip>
            </div>
          </div>
          
          <!-- Status Badge -->
          <div class="status-badge" :class="getStatusClass(task.status)">
            <span class="status-dot"></span>
            <span class="status-text">{{ getStatusText(task.status) }}</span>
          </div>
        </div>
        
        <!-- Bottom Row: Compact Metadata -->
        <div class="task-footer">
          <div class="task-metadata">
            <!-- Due Date -->
            <div class="meta-chip due-date" :class="{ 'overdue': isOverdue(task.dueDate) && task.status !== 'Completed', 'due-soon': isDueWithin24Hours(task.dueDate) && !isOverdue(task.dueDate) && task.status !== 'Completed' }">
              <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{{ formatDate(task.dueDate) }}</span>
            </div>
            
            <!-- Time Taken (for ongoing tasks) -->
            <div v-if="(task.status === 'Ongoing' || task.status === 'Under Review') && task.created_at" class="meta-chip">
              <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{{ timeTaken }}</span>
            </div>
            
            <!-- Assignee -->
            <a-tooltip v-if="task.assignee" :title="'Assigned to: ' + task.assignee">
              <div class="meta-chip assignee">
                <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span class="truncate">{{ task.assignee }}</span>
              </div>
            </a-tooltip>
            
            <!-- Collaborators Count -->
            <a-tooltip v-if="task.collaborators && task.collaborators.length > 0" :title="task.collaborators.length + ' collaborator(s)'">
              <div class="meta-chip">
                <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <span>{{ task.collaborators.length }}</span>
              </div>
            </a-tooltip>
          </div>
          
          <!-- Priority Indicator -->
          <div class="priority-badge" :class="getPriorityClass(task.priority)">
            <span class="priority-text">P{{ task.priority || 5 }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Hover Glow Effect -->
    <div class="card-glow" :class="getPriorityClass(task.priority)"></div>
  </div>
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
        'Under Review': 'Review',
        'Completed': 'Done'
      }
      return texts[status] || 'Unassigned'
    }
    
    const getStatusClass = (status) => {
      const classes = {
        'Unassigned': 'status-unassigned',
        'Ongoing': 'status-ongoing',
        'Under Review': 'status-review',
        'Completed': 'status-completed'
      }
      return classes[status] || 'status-unassigned'
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
      getStatusClass,
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
/* ===== GLASSMORPHIC IMMERSIVE DESIGN ===== */

/* Main Card Wrapper */
.task-card-wrapper {
  position: relative;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Inner Card - Glassmorphism Effect */
.task-card-inner {
  position: relative;
  display: flex;
  gap: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.04),
    0 1px 3px rgba(0, 0, 0, 0.02),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Priority Accent Bar */
.priority-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 16px 0 0 16px;
  opacity: 0.7;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.priority-accent.priority-high {
  background: linear-gradient(180deg, #ff3b30 0%, #ff6b6b 100%);
}

.priority-accent.priority-medium {
  background: linear-gradient(180deg, #ff9500 0%, #ffb84d 100%);
}

.priority-accent.priority-low {
  background: linear-gradient(180deg, #34c759 0%, #5dd879 100%);
}

/* Main Content Area */
.task-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 12px;
}

/* ===== HEADER SECTION ===== */
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.task-title-row {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.task-title {
  margin: 0;
  font-size: 14.5px;
  font-weight: 600;
  color: #1d1d1f;
  line-height: 1.35;
  letter-spacing: -0.02em;
  flex: 1;
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Quick Badge Icons */
.quick-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.badge-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
}

.badge-icon svg {
  width: 14px;
  height: 14px;
}

.badge-icon.recurrence {
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
}

.badge-icon.recurrence:hover {
  background: rgba(0, 122, 255, 0.2);
  transform: rotate(180deg) scale(1.1);
}

.badge-icon.subtask {
  background: rgba(88, 86, 214, 0.1);
  color: #5856d6;
}

.badge-icon.subtask:hover {
  background: rgba(88, 86, 214, 0.2);
  transform: scale(1.1);
}

.badge-icon.collaborator {
  background: rgba(175, 82, 222, 0.1);
  color: #af52de;
}

.badge-icon.collaborator:hover {
  background: rgba(175, 82, 222, 0.2);
  transform: scale(1.1);
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-badge.status-unassigned {
  background: rgba(142, 142, 147, 0.12);
  color: #8e8e93;
}

.status-badge.status-unassigned .status-dot {
  background: #8e8e93;
}

.status-badge.status-ongoing {
  background: rgba(0, 122, 255, 0.12);
  color: #007aff;
}

.status-badge.status-ongoing .status-dot {
  background: #007aff;
}

.status-badge.status-review {
  background: rgba(255, 149, 0, 0.12);
  color: #ff9500;
}

.status-badge.status-review .status-dot {
  background: #ff9500;
}

.status-badge.status-completed {
  background: rgba(52, 199, 89, 0.12);
  color: #34c759;
}

.status-badge.status-completed .status-dot {
  background: #34c759;
}

/* ===== FOOTER SECTION ===== */
.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.task-metadata {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

/* Meta Chips */
.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: #6e6e73;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.meta-chip:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.meta-chip .meta-icon {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  opacity: 0.7;
}

.meta-chip.due-date {
  font-weight: 600;
  color: #1d1d1f;
}

.meta-chip.due-date.overdue {
  background: rgba(255, 59, 48, 0.12);
  color: #ff3b30;
}

.meta-chip.due-date.overdue .meta-icon {
  color: #ff3b30;
  opacity: 1;
}

.meta-chip.due-date.due-soon {
  background: rgba(255, 149, 0, 0.12);
  color: #ff9500;
}

.meta-chip.due-date.due-soon .meta-icon {
  color: #ff9500;
  opacity: 1;
}

.meta-chip.assignee {
  max-width: 150px;
}

.meta-chip .truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Priority Badge */
.priority-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.03em;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.priority-badge.priority-high {
  background: rgba(255, 59, 48, 0.15);
  color: #ff3b30;
}

.priority-badge.priority-medium {
  background: rgba(255, 149, 0, 0.15);
  color: #ff9500;
}

.priority-badge.priority-low {
  background: rgba(52, 199, 89, 0.15);
  color: #34c759;
}

/* ===== HOVER EFFECTS ===== */

/* Hover Glow Effect */
.card-glow {
  position: absolute;
  inset: -2px;
  border-radius: 18px;
  opacity: 0;
  transition: opacity 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: none;
  z-index: -1;
}

.card-glow.priority-high {
  background: radial-gradient(circle at 50% 50%, rgba(255, 59, 48, 0.15), transparent 70%);
}

.card-glow.priority-medium {
  background: radial-gradient(circle at 50% 50%, rgba(255, 149, 0, 0.15), transparent 70%);
}

.card-glow.priority-low {
  background: radial-gradient(circle at 50% 50%, rgba(52, 199, 89, 0.15), transparent 70%);
}

.task-card-wrapper:hover .card-glow {
  opacity: 1;
}

.task-card-wrapper:hover .task-card-inner {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 
    0 12px 32px rgba(0, 0, 0, 0.08),
    0 6px 16px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  border-color: rgba(255, 255, 255, 0.5);
}

.task-card-wrapper:hover .priority-accent {
  width: 5px;
  opacity: 1;
}

.task-card-wrapper:active .task-card-inner {
  transform: translateY(-1px) scale(0.99);
}

/* ===== SPECIAL STATES ===== */

/* Urgent Task */
.task-card-wrapper.urgent-task .task-card-inner {
  border: 1px solid rgba(255, 59, 48, 0.2);
  background: linear-gradient(135deg, rgba(255, 59, 48, 0.03) 0%, rgba(255, 255, 255, 0.85) 100%);
}

.task-card-wrapper.urgent-task .priority-accent {
  width: 5px;
  opacity: 1;
  box-shadow: 0 0 12px rgba(255, 59, 48, 0.4);
}

/* Completed Task */
.task-card-wrapper.completed-task .task-card-inner {
  opacity: 0.7;
  background: rgba(248, 248, 248, 0.85);
}

.task-card-wrapper.completed-task .task-title {
  text-decoration: line-through;
  color: #8e8e93;
}

.task-card-wrapper.completed-task:hover .task-card-inner {
  opacity: 0.85;
}

/* ===== RESPONSIVE DESIGN ===== */
@media (max-width: 768px) {
  .task-card-inner {
    padding: 14px 16px;
  }
  
  .task-title {
    font-size: 14px;
  }
  
  .task-header {
    gap: 8px;
  }
  
  .task-footer {
    gap: 8px;
  }
  
  .meta-chip {
    font-size: 10.5px;
    padding: 4px 8px;
  }
  
  .status-badge {
    font-size: 9.5px;
    padding: 4px 8px;
  }
  
  .priority-badge {
    font-size: 10px;
    padding: 4px 7px;
  }
}

/* ===== DARK MODE SUPPORT ===== */
:global(.dark) .task-card-inner {
  background: rgba(28, 28, 30, 0.85);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.3),
    0 1px 3px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

:global(.dark) .task-title {
  color: #f5f5f7;
}

:global(.dark) .meta-chip {
  background: rgba(255, 255, 255, 0.08);
  color: #a1a1a6;
}

:global(.dark) .meta-chip:hover {
  background: rgba(255, 255, 255, 0.12);
}

:global(.dark) .task-card-wrapper.completed-task .task-card-inner {
  background: rgba(20, 20, 22, 0.85);
}
</style>
