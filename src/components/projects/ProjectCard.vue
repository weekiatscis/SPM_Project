<template>
  <a-card
    :hoverable="true"
    size="small"
    :style="{ width: '100%', minHeight: '200px' }"
    @click="$emit('view-details', project)"
    :class="[
      'cursor-pointer project-card',
      { 'urgent-project': isUrgent(project.end_date) && project.status !== 'Completed' }
    ]"
  >
    <!-- Project Header -->
    <template #title>
      <div style="display: flex; align-items: center; gap: 8px;">
        <div
          :style="{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: getProjectColor(project.status),
            flexShrink: 0
          }"
        ></div>
        <a-typography-text
          strong
          style="font-size: 14px;"
          :ellipsis="true"
          :content="project.project_name"
        />
      </div>
    </template>

    <!-- Project Content -->
    <div style="height: 120px; display: flex; flex-direction: column; justify-content: space-between;">
      <!-- Description -->
      <div style="flex: 1; margin-bottom: 12px;">
        <a-typography-paragraph
          :ellipsis="{ rows: 2, expandable: false }"
          style="margin: 0; font-size: 12px; color: #666;"
        >
          {{ project.project_description || 'No description available' }}
        </a-typography-paragraph>
      </div>

      <!-- Project Info -->
      <div>
        <!-- Status and Due Date -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
          <a-tag :color="getStatusColor(project.status)" size="small">
            {{ getStatusText(project.status) }}
          </a-tag>
          <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px;">
            <a-typography-text
              type="secondary"
              style="font-size: 11px; line-height: 1.4;"
              :class="{ 'urgent-due-date': isUrgent(project.due_date) && project.status !== 'Completed' }"
            >
              {{ formatDueDateWithDays(project.due_date) }}
            </a-typography-text>
            <a-typography-text
              v-if="getDaysUntilDue(project.due_date) !== null"
              type="secondary"
              style="font-size: 10px; line-height: 1.2;"
              :class="{ 'urgent-due-date': isUrgent(project.due_date) && project.status !== 'Completed' }"
            >
              {{ getDaysUntilDue(project.due_date) < 0 ? `Overdue by ${Math.abs(getDaysUntilDue(project.due_date))} day(s)` : getDaysUntilDue(project.due_date) === 0 ? 'Due today' : getDaysUntilDue(project.due_date) === 1 ? 'Due tomorrow' : `Due in ${getDaysUntilDue(project.due_date)} day(s)` }}
            </a-typography-text>
          </div>
        </div>

        <!-- Created by -->
        <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 4px;">
          <UserOutlined style="font-size: 11px; color: #999;" />
          <a-typography-text type="secondary" style="font-size: 11px;">
            {{ project.created_by || 'Unknown' }}
          </a-typography-text>
        </div>

        <!-- Created date and Collaborator badge -->
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 4px;">
          <div style="display: flex; align-items: center; gap: 4px;">
            <CalendarOutlined style="font-size: 11px; color: #999;" />
            <a-typography-text type="secondary" style="font-size: 11px;">
              Created: {{ formatDate(project.created_at) }}
            </a-typography-text>
          </div>
          <a-tag v-if="isCollaborator()" class="collaborator-badge" size="small">
            Collaborator
          </a-tag>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script>
import { UserOutlined, CalendarOutlined } from '@ant-design/icons-vue'

export default {
  name: 'ProjectCard',
  components: {
    UserOutlined,
    CalendarOutlined
  },
  props: {
    project: {
      type: Object,
      required: true
    },
    currentUserId: {
      type: String,
      default: null
    }
  },
  emits: ['view-details'],
  setup(props) {
    const formatDate = (dateString) => {
      if (!dateString) return 'No date'

      const date = new Date(dateString)
      const now = new Date()

      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      })
    }

    const getStatusColor = (status) => {
      const colors = {
        'Active': 'blue',
        'Planning': 'cyan',
        'On Hold': 'orange',
        'Completed': 'green',
        'Cancelled': 'red'
      }
      return colors[status] || 'default'
    }

    const getStatusText = (status) => {
      return status || 'Active'
    }

    const getProjectColor = (status) => {
      const colors = {
        'Active': '#8B5CF6',
        'Planning': '#06B6D4',
        'On Hold': '#F59E0B',
        'Completed': '#10B981',
        'Cancelled': '#EF4444'
      }
      return colors[status] || '#8B5CF6'
    }

    const formatDueDate = (dateString) => {
      if (!dateString) return 'No due date'

      const date = new Date(dateString)
      const now = new Date()
      const timeDiff = date.getTime() - now.getTime()
      const daysDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24))

      if (daysDiff < 0) {
        return `Overdue by ${Math.abs(daysDiff)} day(s)`
      } else if (daysDiff === 0) {
        return 'Due today'
      } else if (daysDiff === 1) {
        return 'Due tomorrow'
      } else if (daysDiff <= 7) {
        return `Due in ${daysDiff} day(s)`
      } else {
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        })
      }
    }

    const isUrgent = (endDateString) => {
      if (!endDateString) return false

      const endDate = new Date(endDateString)
      const now = new Date()
      const timeDiff = endDate.getTime() - now.getTime()
      const daysDiff = timeDiff / (1000 * 60 * 60 * 24)

      // Return true if deadline is within next 7 days (and not overdue)
      return daysDiff >= 0 && daysDiff <= 7
    }

    const getDaysUntilDue = (dateString) => {
      if (!dateString) return null

      const date = new Date(dateString)
      const now = new Date()
      const timeDiff = date.getTime() - now.getTime()
      const daysDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24))

      return daysDiff
    }

    const formatDueDateWithDays = (dateString) => {
      if (!dateString) return 'No due date'

      const date = new Date(dateString)
      const now = new Date()
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      })
    }

    const isCollaborator = () => {
      if (!props.currentUserId || !props.project) return false
      const isOwner = props.project.created_by_id === props.currentUserId
      const isCollab = props.project.collaborators && props.project.collaborators.includes(props.currentUserId)
      return !isOwner && isCollab
    }

    return {
      formatDate,
      formatDueDate,
      formatDueDateWithDays,
      getDaysUntilDue,
      getStatusColor,
      getStatusText,
      getProjectColor,
      isUrgent,
      isCollaborator
    }
  }
}
</script>

<style scoped>
.project-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px !important;
  overflow: hidden;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1) !important;
}

.urgent-project {
  border: 1px solid #EF4444 !important;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15) !important;
}

:deep(.ant-card) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(229, 231, 235, 0.6);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

:deep(.ant-card-head) {
  padding: 16px 20px;
  min-height: auto;
  border-bottom: 1px solid rgba(229, 231, 235, 0.6);
  background: transparent;
}

:deep(.ant-card-body) {
  padding: 16px 20px;
}

:deep(.ant-card-head-title) {
  padding: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1F2937;
}

:deep(.ant-tag) {
  border-radius: 12px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 600;
  border: none;
}

:deep(.ant-typography) {
  color: #6B7280;
}

.urgent-due-date {
  color: #EF4444 !important;
  font-weight: 600 !important;
}

.collaborator-badge {
  background: #FEF3C7 !important;
  color: #D97706 !important;
  border: 1px solid #FDE68A !important;
  border-radius: 12px !important;
  padding: 2px 10px !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  margin: 0 !important;
}
</style>