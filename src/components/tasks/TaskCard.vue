<template>
  <a-card 
    hoverable 
    class="task-card cursor-pointer dark:bg-gray-800 dark:border-gray-700" 
    @click="$emit('view-details', task)"
    :body-style="{ padding: '16px' }"
  >
    <div class="flex items-start justify-between">
      <!-- Task content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center space-x-3 mb-2">
          <a-checkbox
            :checked="task.status === 'completed'"
            @click.stop="toggleComplete"
          />
          <h3 
            :class="[
              'text-lg font-medium truncate',
              task.status === 'completed' ? 'line-through text-gray-500 dark:text-gray-400' : 'text-gray-900 dark:text-gray-100'
            ]"
          >
            {{ task.title }}
          </h3>
        </div>
        
        <p class="text-gray-600 dark:text-gray-300 text-sm mb-3 line-clamp-2">
          {{ task.description }}
        </p>

        <!-- Task meta info -->
        <a-space class="text-xs text-gray-500 dark:text-gray-400">
          <span class="flex items-center">
            <CalendarOutlined class="mr-1" />
            {{ formatDate(task.dueDate) }}
          </span>
          
          <span class="flex items-center">
            <UserOutlined class="mr-1" />
            {{ task.assignee }}
          </span>
        </a-space>
      </div>

      <!-- Task actions and status -->
      <div class="flex flex-col items-end space-y-2 ml-4">
        <!-- Status badge -->
        <a-tag :color="getStatusColor(task.status)">
          {{ getStatusText(task.status) }}
        </a-tag>

        <!-- Priority indicator -->
        <a-tag 
          :color="getPriorityColor(task.priority)"
          size="small"
        >
          {{ task.priority }}
        </a-tag>

        <!-- Action buttons -->
        <div class="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <a-button
            @click.stop="$emit('edit-task', task)"
            type="text"
            size="small"
            :icon="h(EditOutlined)"
            title="Edit task"
          />
          
          <a-button
            @click.stop="$emit('delete-task', task)"
            type="text"
            size="small"
            danger
            :icon="h(DeleteOutlined)"
            title="Delete task"
          />
        </div>
      </div>
    </div>

    <!-- Project tag -->
    <a-divider style="margin: 12px 0" />
    <a-tag color="default">
      {{ task.project }}
    </a-tag>
  </a-card>
</template>

<script>
import { h } from 'vue'
import { CalendarOutlined, UserOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'

export default {
  name: 'TaskCard',
  components: {
    CalendarOutlined,
    UserOutlined,
    EditOutlined,
    DeleteOutlined
  },
  props: {
    task: {
      type: Object,
      required: true
    }
  },
  emits: ['view-details', 'edit-task', 'delete-task', 'toggle-complete'],
  setup(props, { emit }) {
    const toggleComplete = () => {
      const newStatus = props.task.status === 'completed' ? 'pending' : 'completed'
      emit('toggle-complete', { ...props.task, status: newStatus })
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = date.getTime() - now.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) {
        return `${Math.abs(diffDays)} days overdue`
      } else if (diffDays === 0) {
        return 'Due today'
      } else if (diffDays === 1) {
        return 'Due tomorrow'
      } else {
        return `Due in ${diffDays} days`
      }
    }

    const getStatusColor = (status) => {
      const colors = {
        pending: 'orange',
        'in-progress': 'blue',
        completed: 'green',
        overdue: 'red'
      }
      return colors[status] || colors.pending
    }

    const getStatusText = (status) => {
      const texts = {
        pending: 'Pending',
        'in-progress': 'In Progress',
        completed: 'Completed',
        overdue: 'Overdue'
      }
      return texts[status] || 'Pending'
    }

    const getPriorityColor = (priority) => {
      const colors = {
        low: 'green',
        medium: 'orange',
        high: 'red'
      }
      return colors[priority] || colors.medium
    }

    return {
      h,
      toggleComplete,
      formatDate,
      getStatusColor,
      getStatusText,
      getPriorityColor
    }
  }
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card:hover .group-hover\:opacity-100 {
  opacity: 1;
}

.task-card {
  transition: all 0.3s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dark .task-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
</style>
