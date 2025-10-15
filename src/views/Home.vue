<template>

  <div style="max-width: 1600px; margin: 0 auto; padding: 20px;">
    <!-- Welcome Header -->
    <div class="welcome-section">
      <a-typography-title :level="1" :style="titleStyle">
        {{ getGreeting() }}, <span class="gradient-name">{{ currentUser?.name || 'User' }}!</span>
      </a-typography-title>
    </div>

    <!-- Timeline Section with Background GIF -->
    <div class="timeline-container-wrapper">
      <!-- GIF Behind Timeline -->
      <div class="background-illustration">
        <img 
          src="/illustration.gif" 
          alt="Background illustration"
          class="hidden-illustration"
        />
      </div>
      
      <!-- Timeline Content -->
      <a-row style="margin-bottom: 24px; position: relative; z-index: 2;">
        <a-col :span="24">
          <a-card :bordered="false">
            <!-- Timeline Header -->
            <div class="timeline-header">
              <h3 class="timeline-title">Weekly Task Timeline</h3>
            </div>

            <TaskTimelineChart
              :timeline-data="timelineData"
              :week-range-text="weekRangeText"
              :day-labels="dayLabels"
              :week-summary="weekSummary"
              :is-current-week="isCurrentWeek"
              :is-loading="isLoadingTasks"
              @chart-click="handleTimelineClick"
              @previous-week="goToPreviousWeek"
              @next-week="goToNextWeek"
              @current-week="goToCurrentWeek"
            />

          <!-- Timeline Navigation - Bottom -->
          <div class="timeline-navigation-bottom">
            <div class="compact-navigation">
              <!-- Left Navigation -->
              <a-button 
                @click="goToPreviousWeek" 
                :disabled="isLoadingTasks"
                type="text"
                size="large"
                class="nav-button"
              >
                <template #icon>
                  <LeftOutlined />
                </template>
              </a-button>
              
              <!-- Center - Week Range -->
              <div class="week-range-section">
                <div class="week-range-text">{{ weekRangeText }}</div>
              </div>
              
              <!-- Right Navigation -->
              <a-button 
                @click="goToNextWeek" 
                :disabled="isLoadingTasks"
                type="text"
                size="large"
                class="nav-button"
              >
                <template #icon>
                  <RightOutlined />
                </template>
              </a-button>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
    </div> <!-- Close timeline-container-wrapper -->

    <!-- Main Content Row -->
    <a-row :gutter="24" style="margin-bottom: 24px;">
      <!-- Tasks Section -->
      <a-col :span="12">
        <TaskList ref="taskListRef" />
      </a-col>

      <!-- Report Generator Section -->
      <a-col :span="12">
        <ReportGenerator />
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useTaskTimeline } from '../composables/useTaskTimeline.js'
import TaskList from '../components/tasks/TaskList.vue'
import ReportGenerator from '../components/reports/ReportGenerator.vue'
import NotificationTester from '../components/NotificationTester.vue' // Add this import
import TaskTimelineChart from '../components/charts/TaskTimelineChart.vue'
import { LeftOutlined, RightOutlined } from '@ant-design/icons-vue'

export default {
  name: 'Home',
  components: {
    TaskList,
    ReportGenerator,
    NotificationTester, // Add this component
    TaskTimelineChart,
    LeftOutlined,
    RightOutlined
  },
  setup() {
    const tasks = ref([])
    const isLoadingTasks = ref(false)
    const taskListRef = ref(null)
    const authStore = useAuthStore()
    
    // Get user data directly from auth store
    const currentUser = computed(() => authStore.user)

    // Timeline functionality
    const {
      timelineData,
      weekRangeText,
      dayLabels,
      weekSummary,
      isCurrentWeek,
      goToPreviousWeek,
      goToNextWeek,
      goToCurrentWeek,
      getTasksForDate
    } = useTaskTimeline(tasks)



    // Helper functions for welcome section
    const getGreeting = () => {
      const hour = new Date().getHours()
      if (hour < 12) return 'Good morning'
      if (hour < 17) return 'Good afternoon'
      return 'Good evening'
    }

    // Welcome section styling (no background)
    const welcomeSectionStyle = computed(() => ({
      marginBottom: '24px',
      padding: '0'
    }))

    // font style for welcome title
    const titleStyle = computed(() => ({
      color: '#000000',
      marginBottom: '0',
      fontSize: '36px',
      fontWeight: '800',
      textAlign: 'left'
    }))
    
    // Timeline interaction handlers
    const handleTimelineClick = (clickData) => {
      const { date, dayLabel, taskCount } = clickData
      const tasksForDate = getTasksForDate(date)
      
      if (tasksForDate.length > 0) {
        // Show notification with task details
        const taskTitles = tasksForDate.slice(0, 3).map(t => t.title).join(', ')
        const moreText = tasksForDate.length > 3 ? ` and ${tasksForDate.length - 3} more` : ''
        
        // You can extend this to show a modal or filter the task list
        console.log('Tasks for', dayLabel, ':', tasksForDate)
        
        // Optional: scroll to task list or highlight specific tasks
        if (taskListRef.value) {
          // You can add methods to TaskList component to highlight specific tasks
        }
      }
    }

    // Load tasks for stats and timeline
    const loadTasks = async () => {
      isLoadingTasks.value = true
      try {
        const baseUrl = import.meta.env.VITE_TASK_SERVICE_URL || 'http://localhost:8080'
        const ownerId = authStore.user?.user_id || import.meta.env.VITE_TASK_OWNER_ID || ''
        const url = ownerId
          ? `${baseUrl}/tasks?owner_id=${encodeURIComponent(ownerId)}`
          : `${baseUrl}/tasks`
        const response = await fetch(url)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const payload = await response.json()
        const apiTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
        tasks.value = apiTasks.map(t => ({
          id: t.id,
          title: t.title,
          dueDate: t.dueDate || null,
          status: t.status
        }))
      } catch (e) {
        console.error('Failed to load tasks:', e)
        tasks.value = []
      } finally {
        isLoadingTasks.value = false
      }
    }

    // Load tasks on mount
    onMounted(() => {
      loadTasks()
    })

    return {
      // User data
      currentUser,
      getGreeting,
      
      // Timeline data and functionality
      timelineData,
      weekRangeText,
      dayLabels,
      weekSummary,
      isCurrentWeek,
      isLoadingTasks,
      taskListRef,
      handleTimelineClick,
      goToPreviousWeek,
      goToNextWeek,
      goToCurrentWeek,
      
      // Styling
      welcomeSectionStyle,
      titleStyle
    }
  }
}
</script>

<style scoped>
/* Welcome section styles */
.welcome-section {
  margin-bottom: 12px;
  padding: 24px 32px 24px 24px;
}

/* Timeline container with background GIF */
.timeline-container-wrapper {
  position: relative;
  margin-bottom: 24px;
}

/* Background illustration positioned behind timeline */
.background-illustration {
  position: absolute;
  right: 5%;
  top: -30px; /* Half of the GIF is outside the container */
  transform: translateY(-50%);
  z-index: 1;
  opacity: 1; /* Slightly transparent for subtle effect */
}

.hidden-illustration {
  width: 250px;  /* Even larger */
  height: auto;
  border-radius: 12px;
  /* Removed hover transition effects */
}

/* Ensure timeline content is above the background */
.timeline-container-wrapper .ant-row {
  position: relative;
  z-index: 2;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .background-illustration {
    right: -80px;
  }
  
  .hidden-illustration {
    width: 160px;
  }
}

@media (max-width: 768px) {
  .background-illustration {
    display: none; /* Hide on mobile to avoid overlap issues */
  }
}

/* Gradient name styling */
.gradient-name {
  background: linear-gradient(135deg, #87ceeb 0%, #5dade2 25%, #3498db 50%, #2980b9 75%, #1f4e79 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 800;
  position: relative;
}

/* Dark mode gradient variation */
:global(.dark) .gradient-name {
  background: linear-gradient(135deg, #e6f3ff 0%, #b3d9ff 25%, #87ceeb 50%, #5dade2 75%, #3498db 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Timeline card*/
.timeline-container-wrapper :deep(.ant-card) {
  background-color: rgba(255, 255, 255, 1) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: 1px solid rgba(229, 231, 235, 1) !important;
}


/* Ensure proper spacing for timeline section */
.timeline-section {
  margin-bottom: 24px;
}

/* Timeline Header Styles */
.timeline-header {
  padding: 0 0 16px 0;
  margin-bottom: 8px;
}

.timeline-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color, #000000);
  text-align: left;
}

.timeline-navigation-bottom {
  display: flex;
  justify-content: center;
  width: 100%;
  padding: 16px 0 0 0;
  border-top: 1px solid var(--border-color, #f0f0f0);
  margin-top: 16px;
}

.compact-navigation {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  transition: all 0.3s ease;
  color: var(--text-color, #000000);
  flex-shrink: 0;
}

.nav-button:hover:not(:disabled) {
  background-color: var(--nav-button-hover, rgba(24, 144, 255, 0.1));
  color: var(--primary-color, #1890ff);
  transform: scale(1.1);
}

.nav-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.week-range-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 200px;
}

.week-range-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color, #000000);
  letter-spacing: 0.5px;
  text-align: center;
  white-space: nowrap;
}

/* Dark mode timeline */
:global(.dark) .timeline-header,
:global(.dark) .timeline-navigation-bottom {
  --border-color: #434343;
  --text-color: #ffffff;
  --text-color-secondary: #bfbfbf;
  --nav-button-hover: rgba(255, 255, 255, 0.1);
  --primary-color: #1890ff;
}

/* Light mode timeline */
:global(.light) .timeline-header,
:global(.light) .timeline-navigation-bottom,
.timeline-header,
.timeline-navigation-bottom {
  --border-color: #f0f0f0;
  --text-color: #000000;
  --text-color-secondary: #666666;
  --nav-button-hover: rgba(24, 144, 255, 0.1);
  --primary-color: #1890ff;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .timeline-section {
    margin-bottom: 16px;
  }
  
  .timeline-title {
    font-size: 16px;
  }
  
  .timeline-navigation-bottom {
    padding: 12px 0 0 0;
    margin-top: 12px;
  }
  
  .compact-navigation {
    gap: 12px;
  }
  
  .week-range-text {
    font-size: 14px;
  }
  
  .week-range-section {
    min-width: 160px;
  }
  
  .nav-button {
    width: 32px;
    height: 32px;
  }
}

@media (max-width: 480px) {
  .timeline-header {
    padding: 0 0 12px 0;
    margin-bottom: 6px;
  }
  
  .timeline-title {
    font-size: 15px;
  }
  
  .timeline-navigation-bottom {
    padding: 10px 0 0 0;
    margin-top: 10px;
  }
  
  .compact-navigation {
    gap: 8px;
  }
  
  .week-range-text {
    font-size: 13px;
  }
  
  .week-range-section {
    min-width: 140px;
  }
  
  .nav-button {
    width: 28px;
    height: 28px;
  }
  
  /* Welcome section responsive */
  .welcome-section {
    margin-bottom: 24px;
    padding: 16px 20px 12px 16px;
  }
  
  .welcome-section :deep(.ant-typography-h1) {
    font-size: 24px !important;
  }
}
</style>
