<template>
  <a-row :gutter="16" style="margin-bottom: 24px;">
    <!-- Total Tasks -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" hoverable class="metric-card total-card">
        <div class="card-content-wrapper">
          <div class="card-content-left">
            <a-statistic
              title="Total Tasks"
              :value="metrics.total"
              :value-style="{ color: '#1890ff', fontSize: '28px', fontWeight: 'bold' }"
            >
              <template #prefix>
                <CheckCircleOutlined style="font-size: 24px;" />
              </template>
            </a-statistic>
            <div class="metric-subtitle">
              &nbsp;
            </div>
          </div>
        </div>
      </a-card>
    </a-col>

    <!-- In Progress -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" hoverable class="metric-card progress-card">
        <div class="card-content-wrapper">
          <div class="card-content-left">
            <a-statistic
              title="In Progress"
              :value="metrics.inProgress"
              :value-style="{ color: '#52c41a', fontSize: '28px', fontWeight: 'bold' }"
            >
              <template #prefix>
                <SyncOutlined :spin="true" style="font-size: 24px;" />
              </template>
            </a-statistic>
            <div class="metric-subtitle">
              {{ calculatePercentage(metrics.inProgress, metrics.total) }}% of total
            </div>
          </div>
          <div class="card-illustration-bottom">
            <img 
              src="/inprogressIllustration.png" 
              alt="In Progress"
              class="metric-illustration-large"
            />
          </div>
        </div>
      </a-card>
    </a-col>

    <!-- Under Review -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" hoverable class="metric-card review-card">
        <div class="card-content-wrapper">
          <div class="card-content-left">
            <a-statistic
              title="Under Review"
              :value="metrics.underReview"
              :value-style="{ color: '#faad14', fontSize: '28px', fontWeight: 'bold' }"
            >
              <template #prefix>
                <EyeOutlined style="font-size: 24px;" />
              </template>
            </a-statistic>
            <div class="metric-subtitle">
              {{ calculatePercentage(metrics.underReview, metrics.total) }}% of total
            </div>
          </div>
          <div class="card-illustration-bottom">
            <img 
              src="/underreviewIllustration.png" 
              alt="Under Review"
              class="metric-illustration-large"
            />
          </div>
        </div>
      </a-card>
    </a-col>

    <!-- Overdue -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" hoverable class="metric-card overdue-card">
        <div class="card-content-wrapper">
          <div class="card-content-left">
            <a-statistic
              title="Overdue"
              :value="metrics.overdue"
              :value-style="{ color: '#ff4d4f', fontSize: '28px', fontWeight: 'bold' }"
            >
              <template #prefix>
                <ExclamationCircleOutlined style="font-size: 24px;" />
              </template>
            </a-statistic>
            <div class="metric-subtitle overdue-subtitle">
              <a-badge :count="metrics.overdue" :overflow-count="999" />
              <span style="margin-left: 8px;">Needs attention</span>
            </div>
          </div>
          <div class="card-illustration-bottom">
            <img 
              src="/overdueIllustration.png" 
              alt="Overdue"
              class="metric-illustration-large"
            />
          </div>
        </div>
      </a-card>
    </a-col>
  </a-row>

  <!-- Additional Metrics Row (Optional - can be toggled) -->
  <a-row v-if="showExtendedMetrics" :gutter="16" style="margin-bottom: 24px;">
    <!-- Completed -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" class="metric-card-small">
        <a-statistic
          title="Completed"
          :value="metrics.completed"
          :value-style="{ color: '#52c41a' }"
        >
          <template #suffix>
            <span style="font-size: 14px; color: #666;">
              / {{ metrics.total }}
            </span>
          </template>
        </a-statistic>
      </a-card>
    </a-col>

    <!-- Unassigned -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" class="metric-card-small">
        <a-statistic
          title="Unassigned"
          :value="metrics.unassigned"
          :value-style="{ color: '#8c8c8c' }"
        />
      </a-card>
    </a-col>

    <!-- High Priority -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" class="metric-card-small">
        <a-statistic
          title="High Priority"
          :value="metrics.highPriority"
          :value-style="{ color: '#ff4d4f' }"
        />
      </a-card>
    </a-col>

    <!-- Due This Week -->
    <a-col :xs="24" :sm="12" :md="6">
      <a-card :bordered="false" class="metric-card-small">
        <a-statistic
          title="Due This Week"
          :value="metrics.dueThisWeek"
          :value-style="{ color: '#1890ff' }"
        />
      </a-card>
    </a-col>
  </a-row>
</template>

<script setup>
import { computed } from 'vue'
import {
  CheckCircleOutlined,
  SyncOutlined,
  EyeOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  tasks: {
    type: Array,
    required: true,
    default: () => []
  },
  showExtendedMetrics: {
    type: Boolean,
    default: false
  }
})

const metrics = computed(() => {
  const now = new Date()
  // Set to start of today for accurate comparison
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const oneWeekFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000)
  
  return {
    total: props.tasks.length,
    inProgress: props.tasks.filter(t => t.status === 'On Going').length,
    underReview: props.tasks.filter(t => t.status === 'Under Review').length,
    completed: props.tasks.filter(t => t.status === 'Completed').length,
    unassigned: props.tasks.filter(t => t.status === 'Unassigned').length,
    overdue: props.tasks.filter(t => {
      // Task is overdue if:
      // 1. Not completed
      // 2. Has a due date
      // 3. Due date is before today (start of day)
      if (t.status === 'Completed' || !t.dueDate) {
        return false
      }
      
      try {
        const dueDate = new Date(t.dueDate)
        // Set to start of day for comparison
        const dueDateStartOfDay = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate())
        return dueDateStartOfDay < today
      } catch (e) {
        console.error('Error parsing due date:', t.dueDate, e)
        return false
      }
    }).length,
    highPriority: props.tasks.filter(t => t.priority === 'High').length,
    dueThisWeek: props.tasks.filter(t => {
      if (!t.dueDate || t.status === 'Completed') return false
      try {
        const dueDate = new Date(t.dueDate)
        const dueDateStartOfDay = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate())
        return dueDateStartOfDay >= today && dueDateStartOfDay <= oneWeekFromNow
      } catch (e) {
        console.error('Error parsing due date:', t.dueDate, e)
        return false
      }
    }).length
  }
})

const calculatePercentage = (value, total) => {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}
</script>

<style scoped>
.metric-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  min-height: 140px;
  display: flex;
  flex-direction: column;
}

.metric-card :deep(.ant-card-body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

/* Subtle background colors for each metric card */
.total-card {
  background: linear-gradient(135deg, #ffffff 0%, #e6f7ff 100%) !important;
}

.progress-card {
  background: linear-gradient(135deg, #ffffff 0%, #f6ffed 100%) !important;
}

.review-card {
  background: linear-gradient(135deg, #ffffff 0%, #fffbe6 100%) !important;
}

.overdue-card {
  background: linear-gradient(135deg, #ffffff 0%, #fff1f0 100%) !important;
}

.metric-card-small {
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.metric-subtitle {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
  min-height: 20px;
}

.overdue-subtitle {
  color: #ff4d4f;
  font-weight: 500;
}

/* Card content wrapper for illustration layout */
.card-content-wrapper {
  position: relative;
  min-height: 120px;
}

.card-content-left {
  position: relative;
  z-index: 2;
}

.card-illustration-bottom {
  position: absolute;
  bottom: -24px;
  right: -40px;
  width: 160px;
  height: 160px;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  pointer-events: none;
  overflow: hidden;
  padding: 8px;
}

.metric-illustration-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: bottom right;
  opacity: 0.7;
  transition: opacity 0.3s, transform 0.3s;
}

.progress-card:hover .metric-illustration-large {
  opacity: 0.9;
  transform: scale(1.05);
}

.review-card:hover .metric-illustration-large {
  opacity: 0.9;
  transform: scale(1.05);
}

.overdue-card:hover .metric-illustration-large {
  opacity: 0.9;
  transform: scale(1.05);
}

@media (max-width: 768px) {
  .metric-card,
  .metric-card-small {
    margin-bottom: 12px;
  }
}
</style>
