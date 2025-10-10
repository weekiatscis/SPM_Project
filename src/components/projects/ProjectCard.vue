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
        <!-- Status and Date -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <a-tag :color="getStatusColor(project.status)" size="small">
            {{ getStatusText(project.status) }}
          </a-tag>
          <a-typography-text type="secondary" style="font-size: 11px;">
            {{ formatDate(project.created_at) }}
          </a-typography-text>
        </div>

        <!-- Created by -->
        <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 4px;">
          <UserOutlined style="font-size: 11px; color: #999;" />
          <a-typography-text type="secondary" style="font-size: 11px;">
            {{ project.created_by || 'Unknown' }}
          </a-typography-text>
        </div>

        <!-- Due date -->
        <div style="display: flex; align-items: center; gap: 4px;">
          <CalendarOutlined style="font-size: 11px; color: #999;" />
          <a-typography-text type="secondary" style="font-size: 11px;">
            Due: {{ formatDueDate(project.due_date) }}
          </a-typography-text>
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
    }
  },
  emits: ['view-details'],
  setup(props) {
    const formatDate = (dateString) => {
      if (!dateString) return 'No date'

      const date = new Date(dateString)
      const now = new Date()
      const diffTime = now.getTime() - date.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays === 0) {
        return 'Today'
      } else if (diffDays === 1) {
        return 'Yesterday'
      } else if (diffDays < 7) {
        return `${diffDays} days ago`
      } else {
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        })
      }
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

    return {
      formatDate,
      formatDueDate,
      getStatusColor,
      getStatusText,
      getProjectColor,
      isUrgent
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
  box-shadow: 0 12px 24px rgba(139, 92, 246, 0.15) !important;
}

.urgent-project {
  border: 1px solid #EF4444 !important;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15) !important;
}

:deep(.ant-card) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.1);
  box-shadow: 0 4px 6px rgba(139, 92, 246, 0.05);
}

:deep(.ant-card-head) {
  padding: 16px 20px;
  min-height: auto;
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
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
</style>