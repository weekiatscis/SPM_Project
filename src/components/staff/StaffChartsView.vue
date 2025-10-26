<template>
  <div class="staff-charts-view">
    <a-card :loading="isLoading" class="charts-card">
      <a-row :gutter="[24, 24]">
        <!-- My Task Status Distribution -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">My Task Status</h3>
            <div ref="statusChartRef" class="chart"></div>
          </div>
        </a-col>

        <!-- My Priority Distribution -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">My Task Priorities</h3>
            <div ref="priorityChartRef" class="chart"></div>
          </div>
        </a-col>

        <!-- My Task Timeline -->
        <a-col :xs="24">
          <div class="chart-container">
            <h3 class="chart-title">My Upcoming Deadlines (Next 30 Days)</h3>
            <div ref="timelineChartRef" class="chart" style="height: 350px;"></div>
          </div>
        </a-col>

        <!-- My Completion Rate -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">My Completion Rate</h3>
            <div ref="completionChartRef" class="chart"></div>
          </div>
        </a-col>

        <!-- My Productivity Trend -->
        <a-col :xs="24" :lg="12">
          <div class="chart-container">
            <h3 class="chart-title">My Productivity Trend (Last 7 Days)</h3>
            <div ref="productivityChartRef" class="chart"></div>
          </div>
        </a-col>

        <!-- My Task Categories -->
        <a-col :xs="24">
          <div class="chart-container">
            <h3 class="chart-title">My Tasks by Project</h3>
            <div ref="projectChartRef" class="chart" style="height: 300px;"></div>
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

// Chart refs
const statusChartRef = ref(null)
const priorityChartRef = ref(null)
const timelineChartRef = ref(null)
const completionChartRef = ref(null)
const productivityChartRef = ref(null)
const projectChartRef = ref(null)

// Chart instances
let statusChart = null
let priorityChart = null
let timelineChart = null
let completionChart = null
let productivityChart = null
let projectChart = null

// Initialize charts
const initCharts = async () => {
  nextTick(async () => {
    if (statusChartRef.value) {
      statusChart = echarts.init(statusChartRef.value)
    }
    if (priorityChartRef.value) {
      priorityChart = echarts.init(priorityChartRef.value)
    }
    if (timelineChartRef.value) {
      timelineChart = echarts.init(timelineChartRef.value)
    }
    if (completionChartRef.value) {
      completionChart = echarts.init(completionChartRef.value)
    }
    if (productivityChartRef.value) {
      productivityChart = echarts.init(productivityChartRef.value)
    }
    if (projectChartRef.value) {
      projectChart = echarts.init(projectChartRef.value)
    }
    await updateAllCharts()
  })
}

// Update Status Chart
const updateStatusChart = () => {
  if (!statusChart) return

  const statusCounts = {}
  props.tasks.forEach(task => {
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
  
  props.tasks.forEach(task => {
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

// Update Timeline Chart
const updateTimelineChart = () => {
  if (!timelineChart) return

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const next30Days = new Date(today)
  next30Days.setDate(next30Days.getDate() + 30)

  // Group tasks by date
  const dateMap = {}
  props.tasks.forEach(task => {
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

// Update Completion Chart
const updateCompletionChart = () => {
  if (!completionChart) return

  const total = props.tasks.length
  const completed = props.tasks.filter(t => t.status === 'Completed').length
  const inProgress = props.tasks.filter(t => t.status === 'On Going').length
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

// Update Productivity Chart
const updateProductivityChart = () => {
  if (!productivityChart) return

  // Generate productivity data for the last 7 days
  const today = new Date()
  const last7Days = []
  const productivityData = []

  for (let i = 6; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    
    // Count tasks completed on this date
    const completedOnDate = props.tasks.filter(task => {
      if (!task.completedDate) return false
      const completedDate = new Date(task.completedDate)
      const completedDateStr = completedDate.toISOString().split('T')[0]
      return completedDateStr === dateStr
    }).length

    last7Days.push(dateStr)
    productivityData.push(completedOnDate)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = new Date(params[0].axisValue)
        return `${date.toLocaleDateString()}<br/>Tasks Completed: ${params[0].value}`
      }
    },
    xAxis: {
      type: 'category',
      data: last7Days,
      axisLabel: {
        formatter: (value) => {
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
      }
    },
    yAxis: {
      type: 'value',
      minInterval: 1
    },
    series: [
      {
        data: productivityData,
        type: 'bar',
        itemStyle: { 
          color: '#52c41a',
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: '#389e0d'
          }
        }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }

  productivityChart.setOption(option)
}

// Update Project Chart
const updateProjectChart = async () => {
  if (!projectChart) return

  // Get unique project IDs from tasks
  const projectIds = [...new Set(props.tasks.map(task => task.project_id).filter(Boolean))]
  
  // Fetch project names
  const projectNameMap = {}
  const PROJECT_SERVICE_URL = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'
  
  for (const projectId of projectIds) {
    try {
      const response = await fetch(`${PROJECT_SERVICE_URL}/projects?project_id=${projectId}`)
      if (response.ok) {
        const data = await response.json()
        const project = data.projects?.[0]
        projectNameMap[projectId] = project?.project_name || `Project ${projectId}`
      } else {
        projectNameMap[projectId] = `Project ${projectId}`
      }
    } catch (error) {
      console.warn(`Failed to fetch project name for ${projectId}:`, error)
      projectNameMap[projectId] = `Project ${projectId}`
    }
  }

  const projectCounts = {}
  props.tasks.forEach(task => {
    const projectId = task.project_id
    if (projectId) {
      const projectName = projectNameMap[projectId] || `Project ${projectId}`
      projectCounts[projectName] = (projectCounts[projectName] || 0) + 1
    } else {
      projectCounts['No Project'] = (projectCounts['No Project'] || 0) + 1
    }
  })

  const data = Object.entries(projectCounts)
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
    ],
    color: ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2', '#eb2f96']
  }

  projectChart.setOption(option)
}

// Update all charts
const updateAllCharts = async () => {
  updateStatusChart()
  updatePriorityChart()
  updateTimelineChart()
  updateCompletionChart()
  updateProductivityChart()
  await updateProjectChart()
}

// Handle window resize
const handleResize = () => {
  statusChart?.resize()
  priorityChart?.resize()
  timelineChart?.resize()
  completionChart?.resize()
  productivityChart?.resize()
  projectChart?.resize()
}

// Watch for task changes
watch(() => props.tasks, async () => {
  await updateAllCharts()
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
  timelineChart?.dispose()
  completionChart?.dispose()
  productivityChart?.dispose()
  projectChart?.dispose()
})
</script>

<style scoped>
.staff-charts-view {
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
