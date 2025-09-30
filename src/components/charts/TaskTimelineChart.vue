<template>
  <div class="timeline-chart-container">
    <!-- Chart Container -->
    <div class="chart-wrapper" :style="chartContainerStyle">
      <v-chart
        ref="chartRef"
        class="timeline-chart"
        :option="chartOption"
        :loading="isLoading"
        @click="handleChartClick"
        autoresize
      />
    </div>

  </div>
</template>

<script>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'



// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
])

export default {
  name: 'TaskTimelineChart',
  components: {
    VChart
  },
  props: {
    timelineData: {
      type: Object,
      required: true
    },
    weekRangeText: {
      type: String,
      required: true
    },
    dayLabels: {
      type: Array,
      required: true
    },
    weekSummary: {
      type: Object,
      required: true
    },
    isCurrentWeek: {
      type: Boolean,
      default: false
    },
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['chart-click', 'previous-week', 'next-week', 'current-week'],
  setup(props, { emit }) {
    const chartRef = ref(null)

    // Chart container styling
    const chartContainerStyle = computed(() => ({
      height: '300px',
      width: '100%',
      position: 'relative'
    }))

    // Chart configuration
    const chartOption = computed(() => {
      const { taskCounts, maxCount } = props.timelineData
      
      // Light theme colors
      const primaryColor = '#1890ff'
      const areaColor = 'rgba(24, 144, 255, 0.1)'
      const textColor = '#000000'
      const gridColor = '#e0e0e0'
      
      return {
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#ffffff',
          borderColor: '#d9d9d9',
          textStyle: {
            color: textColor
          },
          formatter: (params) => {
            const dataIndex = params[0].dataIndex
            const dayLabel = props.dayLabels[dataIndex]
            const date = props.timelineData.dates[dataIndex]
            const taskCount = params[0].value
            const dateFormatted = new Date(date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              timeZone: 'Asia/Singapore'
            })
            
            return `
              <div style="padding: 8px;">
                <div style="font-weight: bold; margin-bottom: 4px;">
                  ${dayLabel}, ${dateFormatted}
                </div>
                <div style="color: ${primaryColor};">
                  ${taskCount} task${taskCount !== 1 ? 's' : ''} due
                </div>
                ${taskCount > 0 ? '<div style="font-size: 12px; color: #999; margin-top: 4px;">Click to view details</div>' : ''}
              </div>
            `
          }
        },
        grid: {
          left: '3%',
          right: '3%',
          bottom: '8%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: props.dayLabels,
          axisLine: {
            lineStyle: {
              color: gridColor
            }
          },
          axisTick: {
            lineStyle: {
              color: gridColor
            }
          },
          axisLabel: {
            color: textColor,
            fontSize: 12
          }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: Math.max(maxCount + 1, 5), // Ensure some headroom
          interval: Math.max(1, Math.ceil(maxCount / 4)),
          axisLine: {
            show: false
          },
          axisTick: {
            show: false
          },
          axisLabel: {
            color: textColor,
            fontSize: 12
          },
          splitLine: {
            lineStyle: {
              color: gridColor,
              type: 'dashed'
            }
          }
        },
        series: [
          {
            name: 'Tasks Due',
            type: 'line',
            data: taskCounts,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: {
              color: primaryColor,
              width: 3
            },
            itemStyle: {
              color: primaryColor,
              borderColor: '#ffffff',
              borderWidth: 2
            },
            areaStyle: {
              color: areaColor
            },
            emphasis: {
              itemStyle: {
                symbolSize: 12,
                borderWidth: 3
              }
            }
          }
        ],
        animation: true,
        animationDuration: 1000,
        animationEasing: 'cubicOut'
      }
    })

    // Chart click handler
    const handleChartClick = (params) => {
      if (params.componentType === 'series') {
        const dateIndex = params.dataIndex
        const date = props.timelineData.dates[dateIndex]
        const taskCount = params.value
        
        if (taskCount > 0) {
          emit('chart-click', {
            date,
            dateIndex,
            taskCount,
            dayLabel: props.dayLabels[dateIndex]
          })
        }
      }
    }

    // Navigation handlers
    const goToPreviousWeek = () => {
      emit('previous-week')
    }

    const goToNextWeek = () => {
      emit('next-week')
    }

    const goToCurrentWeek = () => {
      emit('current-week')
    }



    // Resize chart on mount
    onMounted(async () => {
      await nextTick()
      if (chartRef.value) {
        chartRef.value.resize()
      }
    })

    return {
      chartRef,
      chartOption,
      chartContainerStyle,
      handleChartClick,
      goToPreviousWeek,
      goToNextWeek,
      goToCurrentWeek
    }
  }
}
</script>

<style scoped>
.timeline-chart-container {
  width: 100%;
  background: var(--chart-bg, #ffffff);
  border-radius: 8px;
  overflow: hidden;
}

.chart-wrapper {
  padding: 16px 8px 8px;
}

.timeline-chart {
  width: 100%;
  height: 100%;
}

/* Dark mode styles */
:global(.dark) .timeline-chart-container {
  --chart-bg: #1f1f1f;
  --border-color: #434343;
  --text-color: #ffffff;
  --text-color-secondary: #bfbfbf;
  --primary-color: #1890ff;
}

/* Light mode styles */
:global(.light) .timeline-chart-container,
.timeline-chart-container {
  --chart-bg: #ffffff;
  --border-color: #f0f0f0;
  --text-color: #000000;
  --text-color-secondary: #666666;
  --primary-color: #1890ff;
}

/* Responsive design */
@media (max-width: 768px) {

}
</style>