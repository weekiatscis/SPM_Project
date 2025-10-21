<template>
  <div class="team-charts-view">
    <!-- Chart Filters (HR Only) -->
    <a-card v-if="isHRUser && departmentOptions.length > 0" :bordered="false" style="margin-bottom: 16px;">
      <a-row :gutter="16" align="middle">
        <a-col :span="4">
          <strong>Filter Charts:</strong>
        </a-col>
        <a-col :span="10">
          <a-select
            v-model:value="selectedDepartments"
            mode="multiple"
            placeholder="All Departments"
            :options="departmentOptions"
            :max-tag-count="2"
            allow-clear
            show-search
            style="width: 100%"
            @change="updateAllCharts"
          >
            <template #maxTagPlaceholder="omittedValues">
              <span>+{{ omittedValues.length }} more</span>
            </template>
          </a-select>
        </a-col>
        <a-col :span="10">
          <a-space>
            <a-badge :count="filteredTasksCount" :number-style="{ backgroundColor: '#1890ff' }" />
            <span style="color: #666;">
              {{ filteredTasksCount }} of {{ tasks.length }} tasks
            </span>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <a-card :loading="isLoading" class="charts-card">
      <a-row :gutter="[24, 24]">
        <!-- Task Status Distribution -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">Task Status Distribution</h3>
            <div ref="statusChartRef" class="chart"></div>
          </div>
        </a-col>

        <!-- Priority Distribution -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">Priority Distribution</h3>
            <div ref="priorityChartRef" class="chart"></div>
          </div>
        </a-col>

        <!-- Tasks by Team Member -->
        <a-col :xs="24">
          <div class="chart-container">
            <h3 class="chart-title">Tasks by Team Member</h3>
            <div ref="teamMemberChartRef" class="chart" style="height: 400px;"></div>
          </div>
        </a-col>

        <!-- Task Timeline -->
        <a-col :xs="24">
          <div class="chart-container">
            <h3 class="chart-title">Tasks Due Timeline (Next 30 Days)</h3>
            <div ref="timelineChartRef" class="chart" style="height: 350px;"></div>
          </div>
        </a-col>

        <!-- Workload by Department -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">Workload by Department</h3>
            <div ref="departmentChartRef" class="chart"></div>
          </div>
        </a-col>

        <!-- Completion Rate -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">Task Completion Rate</h3>
            <div ref="completionChartRef" class="chart"></div>
          </div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  tasks: {
    type: Array,
    required: true
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  subordinates: {
    type: Array,
    default: () => []
  },
  userRole: {
    type: String,
    default: ''
  }
})

// Local department filter
const selectedDepartments = ref([])

// Check if user is HR
const isHRUser = computed(() => props.userRole === 'HR')

// Get department options from subordinates
const departmentOptions = computed(() => {
  if (!isHRUser.value) return []
  const departments = [...new Set(props.subordinates.map(sub => sub.department).filter(Boolean))]
  return departments.sort().map(dept => ({
    label: dept,
    value: dept
  }))
})

// Filter tasks by selected departments
const filteredTasks = computed(() => {
  if (!isHRUser.value || selectedDepartments.value.length === 0) {
    return props.tasks
  }
  return props.tasks.filter(task => 
    selectedDepartments.value.includes(task.assigneeDepartment)
  )
})

// Count of filtered tasks
const filteredTasksCount = computed(() => filteredTasks.value.length)

// Chart refs
const statusChartRef = ref(null)
const priorityChartRef = ref(null)
const teamMemberChartRef = ref(null)
const timelineChartRef = ref(null)
const departmentChartRef = ref(null)
const completionChartRef = ref(null)

// Chart instances
let statusChart = null
let priorityChart = null
let teamMemberChart = null
let timelineChart = null
let departmentChart = null
let completionChart = null

// Initialize charts
const initCharts = () => {
  nextTick(() => {
    if (statusChartRef.value) {
      statusChart = echarts.init(statusChartRef.value)
    }
    if (priorityChartRef.value) {
      priorityChart = echarts.init(priorityChartRef.value)
    }
    if (teamMemberChartRef.value) {
      teamMemberChart = echarts.init(teamMemberChartRef.value)
    }
    if (timelineChartRef.value) {
      timelineChart = echarts.init(timelineChartRef.value)
    }
    if (departmentChartRef.value) {
      departmentChart = echarts.init(departmentChartRef.value)
    }
    if (completionChartRef.value) {
      completionChart = echarts.init(completionChartRef.value)
    }
    updateAllCharts()
  })
}

// Update Status Chart
const updateStatusChart = () => {
  if (!statusChart) return

  const statusCounts = {}
  filteredTasks.value.forEach(task => {
    const status = task.status || 'Unknown'
    statusCounts[status] = (statusCounts[status] || 0) + 1
  })

  const data = Object.entries(statusCounts).map(([name, value]) => ({ name, value }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: '60%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          formatter: '{b}: {d}%'
        }
      }
    ],
    color: ['#52c41a', '#1890ff', '#faad14', '#ff4d4f', '#722ed1']
  }

  statusChart.setOption(option)
}

// Update Priority Chart
const updatePriorityChart = () => {
  if (!priorityChart) return

  // Priority is now 1-10, group into ranges for visualization
  const priorityRanges = {
    'Critical (9-10)': 0,
    'High (7-8)': 0,
    'Medium (4-6)': 0,
    'Low (1-3)': 0
  }
  
  filteredTasks.value.forEach(task => {
    const priority = Number(task.priority) || 5
    if (priority >= 9) priorityRanges['Critical (9-10)']++
    else if (priority >= 7) priorityRanges['High (7-8)']++
    else if (priority >= 4) priorityRanges['Medium (4-6)']++
    else priorityRanges['Low (1-3)']++
  })

  const data = Object.entries(priorityRanges).map(([name, value]) => ({ name, value }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          formatter: '{b}: {d}%'
        }
      }
    ],
    color: ['#ff4d4f', '#fa8c16', '#faad14', '#52c41a']
  }

  priorityChart.setOption(option)
}

// Update Team Member Chart
const updateTeamMemberChart = () => {
  if (!teamMemberChart) return

  const memberTasks = {}
  filteredTasks.value.forEach(task => {
    const name = task.assigneeName || 'Unknown'
    if (!memberTasks[name]) {
      memberTasks[name] = { total: 0, completed: 0, inProgress: 0, overdue: 0 }
    }
    memberTasks[name].total++
    
    if (task.status === 'Completed') {
      memberTasks[name].completed++
    } else if (task.status === 'On Going') {
      memberTasks[name].inProgress++
    }
    
    // Check if overdue
    if (task.dueDate && task.status !== 'Completed') {
      const dueDate = new Date(task.dueDate)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      if (dueDate < today) {
        memberTasks[name].overdue++
      }
    }
  })

  const members = Object.keys(memberTasks)
  const completedData = members.map(m => memberTasks[m].completed)
  const inProgressData = members.map(m => memberTasks[m].inProgress)
  const overdueData = members.map(m => memberTasks[m].overdue)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['Completed', 'In Progress', 'Overdue']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: members
    },
    series: [
      {
        name: 'Completed',
        type: 'bar',
        stack: 'total',
        data: completedData,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: 'In Progress',
        type: 'bar',
        stack: 'total',
        data: inProgressData,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: 'Overdue',
        type: 'bar',
        stack: 'total',
        data: overdueData,
        itemStyle: { color: '#ff4d4f' }
      }
    ]
  }

  teamMemberChart.setOption(option)
}

// Update Timeline Chart
const updateTimelineChart = () => {
  if (!timelineChart) return

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const next30Days = new Date(today)
  next30Days.setDate(next30Days.getDate() + 30)

  // Group tasks by date
  const dateMap = {}
  filteredTasks.value.forEach(task => {
    if (!task.dueDate) return
    const dueDate = new Date(task.dueDate)
    if (dueDate >= today && dueDate <= next30Days) {
      const dateStr = dueDate.toISOString().split('T')[0]
      dateMap[dateStr] = (dateMap[dateStr] || 0) + 1
    }
  })

  // Create array of all dates in range
  const dates = []
  const counts = []
  for (let d = new Date(today); d <= next30Days; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split('T')[0]
    dates.push(dateStr)
    counts.push(dateMap[dateStr] || 0)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = new Date(params[0].axisValue)
        return `${date.toLocaleDateString()}<br/>Tasks Due: ${params[0].value}`
      }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value) => {
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        },
        interval: 4
      }
    },
    yAxis: {
      type: 'value',
      minInterval: 1
    },
    series: [
      {
        data: counts,
        type: 'line',
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ]
          }
        },
        itemStyle: { color: '#1890ff' }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }

  timelineChart.setOption(option)
}

// Update Department Chart
const updateDepartmentChart = () => {
  if (!departmentChart) return

  const departmentCounts = {}
  filteredTasks.value.forEach(task => {
    const dept = task.assigneeDepartment || 'Unknown'
    departmentCounts[dept] = (departmentCounts[dept] || 0) + 1
  })

  const data = Object.entries(departmentCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} tasks ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: '60%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          formatter: '{b}: {c} tasks'
        }
      }
    ]
  }

  departmentChart.setOption(option)
}

// Update Completion Chart
const updateCompletionChart = () => {
  if (!completionChart) return

  const total = filteredTasks.value.length
  const completed = filteredTasks.value.filter(t => t.status === 'Completed').length
  const inProgress = filteredTasks.value.filter(t => t.status === 'On Going').length
  const notStarted = total - completed - inProgress

  const completionRate = total > 0 ? ((completed / total) * 100).toFixed(1) : 0

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} tasks ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 'bottom'
    },
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: 'center',
          formatter: `${completionRate}%\nCompleted`,
          fontSize: 20,
          fontWeight: 'bold'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 24,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: completed, name: 'Completed', itemStyle: { color: '#52c41a' } },
          { value: inProgress, name: 'In Progress', itemStyle: { color: '#1890ff' } },
          { value: notStarted, name: 'Not Started', itemStyle: { color: '#d9d9d9' } }
        ]
      }
    ]
  }

  completionChart.setOption(option)
}

// Update all charts
const updateAllCharts = () => {
  updateStatusChart()
  updatePriorityChart()
  updateTeamMemberChart()
  updateTimelineChart()
  updateDepartmentChart()
  updateCompletionChart()
}

// Handle window resize
const handleResize = () => {
  statusChart?.resize()
  priorityChart?.resize()
  teamMemberChart?.resize()
  timelineChart?.resize()
  departmentChart?.resize()
  completionChart?.resize()
}

// Watch for task changes
watch(() => props.tasks, () => {
  updateAllCharts()
}, { deep: true })

// Lifecycle
onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  statusChart?.dispose()
  priorityChart?.dispose()
  teamMemberChart?.dispose()
  timelineChart?.dispose()
  departmentChart?.dispose()
  completionChart?.dispose()
})
</script>

<style scoped>
.team-charts-view {
  width: 100%;
}

.charts-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-container {
  background: white;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #262626;
}

.chart {
  width: 100%;
  height: 300px;
}

@media (max-width: 768px) {
  .chart {
    height: 250px;
  }
  
  .chart-title {
    font-size: 14px;
  }
}
</style>
