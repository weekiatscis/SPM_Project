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
        'Active': '#1890ff',
        'Planning': '#13c2c2',
        'On Hold': '#fa8c16',
        'Completed': '#52c41a',
        'Cancelled': '#ff4d4f'
      }
      return colors[status] || '#1890ff'
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
  transition: all 0.2s ease;
}

.urgent-project {
  border: 1px solid #ff4d4f !important;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.1);
}

:deep(.ant-card-head) {
  padding: 12px 16px;
  min-height: auto;
}

:deep(.ant-card-body) {
  padding: 12px 16px;
}

:deep(.ant-card-head-title) {
  padding: 0;
}
</style>