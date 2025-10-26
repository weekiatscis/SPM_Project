<template>

  <div class="home-container">
    <!-- Welcome Header -->
    <div class="welcome-section">
      <a-typography-title :level="1" :style="titleStyle">
        {{ getGreeting() }}, <span class="gradient-name">{{ currentUser?.name || 'User' }}!</span>
      </a-typography-title>
    </div>

    <!-- Top Section: Timeline + Report Generator -->
    <a-row :gutter="24" class="top-section-row">
      <!-- Timeline Section with Background GIF -->
      <a-col :xs="24" :lg="24" :xl="15">
        <div class="timeline-container-wrapper">
          <!-- GIF Behind Timeline -->
          <div class="background-illustration">
            <img 
              src="/illustration.gif" 
              alt="Background illustration"
              class="hidden-illustration"
            />
          </div>
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
        </div>
      </a-col>
      
      <!-- Report Generator Section -->
      <a-col :xs="24" :lg="24" :xl="9">
        <ReportGenerator />
      </a-col>
    </a-row>

    <!-- Main Content Row - Full Width Tasks -->
    <a-row class="main-content-row">
      <a-col :span="24">
        <TaskList ref="taskListRef" />
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
/* Home Container */
.home-container {
  max-width: 1800px;
  margin: 0 auto;
  padding: 32px 40px;
}

@media (max-width: 1400px) {
  .home-container {
    padding: 28px 32px;
  }
}

@media (max-width: 768px) {
  .home-container {
    padding: 20px 16px;
  }
}

/* Welcome section styles */
.welcome-section {
  margin-bottom: 32px;
  padding: 0;
}

/* Top Section Row */
.top-section-row {
  margin-bottom: 40px;
}

/* Timeline container with background GIF */
.timeline-container-wrapper {
  position: relative;
  height: 100%;
}

/* Main Content Row */
.main-content-row {
  margin-bottom: 40px;
}

/* Responsive: Stack on smaller screens */
@media (max-width: 1199px) {
  .top-section-row {
    margin-bottom: 24px;
  }
  
  .top-section-row .ant-col:first-child {
    margin-bottom: 24px;
  }
}

/* Background illustration positioned behind timeline */
.background-illustration {
  display: block;
  position: absolute;
  right: 5%;
  top: -30px;
  transform: translateY(-50%);
  z-index: 1;
  opacity: 1;
  pointer-events: none; /* Do not block interactions */
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

/* Timeline card with modern design */
.timeline-container-wrapper :deep(.ant-card) {
  background-color: rgba(255, 255, 255, 1) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: 1px solid rgba(229, 231, 235, 0.8) !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden !important;
}

.timeline-container-wrapper :deep(.ant-card):hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04) !important;
  border-color: rgba(24, 144, 255, 0.2) !important;
}


/* Ensure proper spacing for timeline section */
.timeline-section {
  margin-bottom: 24px;
}

/* Timeline Header Styles */
.timeline-header {
  padding: 0 0 20px 0;
  margin-bottom: 12px;
  position: relative;
}

.timeline-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #1890ff, #40a9ff);
  border-radius: 2px;
}

.timeline-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-color, #111827);
  text-align: left;
  letter-spacing: -0.02em;
}

.timeline-navigation-bottom {
  display: flex;
  justify-content: center;
  width: 100%;
  padding: 20px 0 4px 0;
  border-top: 1px solid var(--border-color, #f3f4f6);
  margin-top: 20px;
  background: linear-gradient(to bottom, transparent, rgba(249, 250, 251, 0.5));
}

.compact-navigation {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-color, #6b7280);
  flex-shrink: 0;
  background: var(--nav-bg, #f9fafb);
  border: 1px solid var(--border-color, #e5e7eb) !important;
}

.nav-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #1890ff, #40a9ff) !important;
  color: #ffffff !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
  border-color: transparent !important;
}

.nav-button:active:not(:disabled) {
  transform: translateY(0);
}

.nav-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: var(--nav-bg, #f9fafb) !important;
}

.week-range-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 220px;
  padding: 8px 20px;
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08), rgba(64, 169, 255, 0.08));
  border-radius: 12px;
  border: 1px solid rgba(24, 144, 255, 0.15);
}

.week-range-text {
  font-size: 15px;
  font-weight: 700;
  background: linear-gradient(135deg, #1890ff, #40a9ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.3px;
  text-align: center;
  white-space: nowrap;
}

/* Dark mode timeline */
:global(.dark) .timeline-header,
:global(.dark) .timeline-navigation-bottom {
  --border-color: #374151;
  --text-color: #f9fafb;
  --text-color-secondary: #d1d5db;
  --nav-bg: #1f2937;
  --primary-color: #1890ff;
}

:global(.dark) .timeline-container-wrapper :deep(.ant-card) {
  background-color: rgba(31, 41, 55, 1) !important;
  border-color: rgba(55, 65, 81, 0.8) !important;
}

:global(.dark) .timeline-container-wrapper :deep(.ant-card):hover {
  border-color: rgba(24, 144, 255, 0.3) !important;
}

/* Light mode timeline */
:global(.light) .timeline-header,
:global(.light) .timeline-navigation-bottom,
.timeline-header,
.timeline-navigation-bottom {
  --border-color: #e5e7eb;
  --text-color: #111827;
  --text-color-secondary: #6b7280;
  --nav-bg: #f9fafb;
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
