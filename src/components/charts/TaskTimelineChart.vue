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
      height: '350px',
      width: '100%',
      position: 'relative'
    }))

    // Chart configuration
    const chartOption = computed(() => {
      const { taskCounts, maxCount } = props.timelineData
      
      // Modern blue gradient colors
      const primaryColor = '#1890ff'
      const secondaryColor = '#40a9ff'
      const textColor = '#1f2937'
      const gridColor = '#e5e7eb'
      const tooltipBg = '#ffffff'
      const tooltipBorder = '#e5e7eb'
      
      return {
        tooltip: {
          trigger: 'axis',
          backgroundColor: tooltipBg,
          borderColor: tooltipBorder,
          borderWidth: 1,
          padding: [12, 16],
          textStyle: {
            color: textColor,
            fontSize: 13
          },
          shadowBlur: 20,
          shadowColor: 'rgba(0, 0, 0, 0.08)',
          shadowOffsetY: 4,
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
              <div style="padding: 4px;">
                <div style="font-weight: 600; margin-bottom: 8px; color: #111827; font-size: 14px;">
                  ${dayLabel}, ${dateFormatted}
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <div style="width: 8px; height: 8px; border-radius: 50%; background: linear-gradient(135deg, ${primaryColor}, ${secondaryColor});"></div>
                  <span style="font-weight: 600; color: ${primaryColor}; font-size: 15px;">
                    ${taskCount} task${taskCount !== 1 ? 's' : ''}
                  </span>
                </div>
                ${taskCount > 0 ? '<div style="font-size: 11px; color: #9ca3af; margin-top: 8px; font-weight: 500;">💡 Click to view details</div>' : ''}
              </div>
            `
          }
        },
        grid: {
          left: '2%',
          right: '2%',
          bottom: '10%',
          top: '12%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: props.dayLabels,
          axisLine: {
            lineStyle: {
              color: gridColor,
              width: 2
            }
          },
          axisTick: {
            show: false
          },
          axisLabel: {
            color: textColor,
            fontSize: 13,
            fontWeight: 500,
            margin: 12
          }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: Math.max(maxCount + 2, 5),
          interval: Math.max(1, Math.ceil(maxCount / 4)),
          axisLine: {
            show: false
          },
          axisTick: {
            show: false
          },
          axisLabel: {
            color: '#9ca3af',
            fontSize: 12,
            fontWeight: 500,
            margin: 12
          },
          splitLine: {
            lineStyle: {
              color: '#f3f4f6',
              width: 1.5
            }
          }
        },
        series: [
          {
            name: 'Tasks Due',
            type: 'line',
            data: taskCounts,
            smooth: 0.4,
            symbol: 'circle',
            symbolSize: 10,
            lineStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 1,
                y2: 0,
                colorStops: [
                  { offset: 0, color: primaryColor },
                  { offset: 1, color: secondaryColor }
                ]
              },
              width: 3.5,
              shadowColor: 'rgba(24, 144, 255, 0.3)',
              shadowBlur: 8,
              shadowOffsetY: 2
            },
            itemStyle: {
              color: '#ffffff',
              borderColor: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 1,
                y2: 0,
                colorStops: [
                  { offset: 0, color: primaryColor },
                  { offset: 1, color: secondaryColor }
                ]
              },
              borderWidth: 3,
              shadowColor: 'rgba(24, 144, 255, 0.4)',
              shadowBlur: 6,
              shadowOffsetY: 2
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(24, 144, 255, 0.25)' },
                  { offset: 0.5, color: 'rgba(64, 169, 255, 0.15)' },
                  { offset: 1, color: 'rgba(64, 169, 255, 0.02)' }
                ]
              }
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                symbolSize: 14,
                borderWidth: 4,
                shadowBlur: 10,
                shadowColor: 'rgba(24, 144, 255, 0.5)'
              },
              lineStyle: {
                width: 4
              }
            }
          }
        ],
        animation: true,
        animationDuration: 1200,
        animationEasing: 'cubicInOut',
        animationDelay: (idx) => idx * 50
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
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-wrapper {
  padding: 20px 16px 12px;
}

.timeline-chart {
  width: 100%;
  height: 100%;
  cursor: pointer;
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
  --text-color: #1f2937;
  --text-color-secondary: #6b7280;
  --primary-color: #1890ff;
}

/* Responsive design */
@media (max-width: 768px) {
  .chart-wrapper {
    padding: 16px 12px 10px;
  }
}
</style>