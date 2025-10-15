<template>
  <a-card title="Filters" :bordered="false" class="filter-card">
    <a-form layout="vertical">
      <!-- Status Filter -->
      <a-form-item label="Status">
        <a-select
          v-model:value="localFilters.status"
          placeholder="All Statuses"
          allow-clear
          :disabled="isLoading"
          @change="emitFilterChange"
        >
          <a-select-option value="Unassigned">
            <a-badge status="default" text="Unassigned" />
          </a-select-option>
          <a-select-option value="On Going">
            <a-badge status="processing" text="On Going" />
          </a-select-option>
          <a-select-option value="Under Review">
            <a-badge status="warning" text="Under Review" />
          </a-select-option>
          <a-select-option value="Completed">
            <a-badge status="success" text="Completed" />
          </a-select-option>
        </a-select>
      </a-form-item>

      <!-- Team Members Filter -->
      <a-form-item label="Team Members">
        <a-select
          v-model:value="localFilters.assignees"
          mode="multiple"
          placeholder="All team members"
          :options="subordinateOptions"
          :max-tag-count="2"
          allow-clear
          show-search
          :filter-option="filterOption"
          :disabled="isLoading"
          @change="emitFilterChange"
        >
          <template #maxTagPlaceholder="omittedValues">
            <span>+{{ omittedValues.length }} more</span>
          </template>
        </a-select>
        <div v-if="subordinates.length > 0" class="filter-hint">
          {{ subordinates.length }} team member{{ subordinates.length !== 1 ? 's' : '' }}
        </div>
      </a-form-item>

      <!-- Due Date Range -->
      <a-form-item label="Due Date Range">
        <a-range-picker
          v-model:value="localFilters.dateRange"
          format="MMM DD, YYYY"
          :disabled="isLoading"
          style="width: 100%"
          @change="emitFilterChange"
        />
      </a-form-item>

      <!-- Priority Filter -->
      <a-form-item label="Priority">
        <a-select
          v-model:value="localFilters.priority"
          placeholder="All Priorities"
          allow-clear
          :disabled="isLoading"
          @change="emitFilterChange"
        >
          <a-select-option value="High">
            <a-tag color="red">High</a-tag>
          </a-select-option>
          <a-select-option value="Medium">
            <a-tag color="orange">Medium</a-tag>
          </a-select-option>
          <a-select-option value="Low">
            <a-tag color="blue">Low</a-tag>
          </a-select-option>
        </a-select>
      </a-form-item>

      <!-- Search -->
      <a-form-item label="Search Tasks">
        <a-input
          v-model:value="localFilters.searchText"
          placeholder="Search by title or assignee..."
          allow-clear
          :disabled="isLoading"
          @change="emitFilterChange"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input>
      </a-form-item>

      <!-- Quick Filter Buttons -->
      <a-form-item label="Quick Filters">
        <a-space direction="vertical" style="width: 100%">
          <a-button 
            type="text" 
            block 
            @click="applyQuickFilter('overdue')"
            :disabled="isLoading"
            style="text-align: left; padding-left: 8px;"
          >
            <ExclamationCircleOutlined style="color: #ff4d4f;" />
            <span style="margin-left: 8px;">Overdue Tasks</span>
          </a-button>
          <a-button 
            type="text" 
            block 
            @click="applyQuickFilter('thisWeek')"
            :disabled="isLoading"
            style="text-align: left; padding-left: 8px;"
          >
            <ClockCircleOutlined style="color: #1890ff;" />
            <span style="margin-left: 8px;">Due This Week</span>
          </a-button>
          <a-button 
            type="text" 
            block 
            @click="applyQuickFilter('highPriority')"
            :disabled="isLoading"
            style="text-align: left; padding-left: 8px;"
          >
            <FireOutlined style="color: #ff4d4f;" />
            <span style="margin-left: 8px;">High Priority</span>
          </a-button>
        </a-space>
      </a-form-item>

      <!-- Action Buttons -->
      <a-space direction="vertical" style="width: 100%; margin-top: 16px;">
        <a-button 
          type="primary" 
          block 
          @click="applyFilters"
          :disabled="isLoading"
        >
          Apply Filters
        </a-button>
        <a-button 
          block 
          @click="resetFilters"
          :disabled="isLoading"
        >
          Reset All Filters
        </a-button>
      </a-space>
    </a-form>
  </a-card>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { 
  SearchOutlined, 
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  FireOutlined
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'

const props = defineProps({
  filters: {
    type: Object,
    required: true
  },
  subordinates: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:filters', 'apply', 'reset'])

const localFilters = ref({ ...props.filters })

// Watch for external filter changes
watch(() => props.filters, (newFilters) => {
  localFilters.value = { ...newFilters }
}, { deep: true })

const subordinateOptions = computed(() => {
  return props.subordinates.map(sub => ({
    label: `${sub.name} (${sub.role})`,
    value: sub.user_id,
    role: sub.role,
    department: sub.department
  }))
})

const filterOption = (input, option) => {
  const label = option.label.toLowerCase()
  const searchTerm = input.toLowerCase()
  return label.includes(searchTerm)
}

const emitFilterChange = () => {
  emit('update:filters', localFilters.value)
}

const applyFilters = () => {
  emit('apply', localFilters.value)
}

const resetFilters = () => {
  localFilters.value = {
    status: null,
    assignees: [],
    dateRange: null,
    priority: null,
    searchText: ''
  }
  emit('update:filters', localFilters.value)
  emit('reset')
}

const applyQuickFilter = async (filterType) => {
  // Reset filters first
  localFilters.value = {
    status: null,
    assignees: [],
    dateRange: null,
    priority: null,
    searchText: ''
  }
  
  switch (filterType) {
    case 'overdue':
      {
        // For overdue: tasks due before today AND not completed
        // Set date range from far past to yesterday (end of day)
        const today = dayjs().startOf('day')
        const yesterday = dayjs().subtract(1, 'day').endOf('day')
        
        localFilters.value.dateRange = [
          dayjs('2020-01-01'), // Far past date
          yesterday
        ]
      }
      break
      
    case 'thisWeek':
      {
        // Set date range to next 7 days from today
        const today = dayjs().startOf('day')
        const oneWeekFromNow = dayjs().add(7, 'day').endOf('day')
        
        localFilters.value.dateRange = [
          today,
          oneWeekFromNow
        ]
      }
      break
      
    case 'highPriority':
      localFilters.value.priority = 'High'
      break
  }
  
  // Emit the update first
  emit('update:filters', localFilters.value)
  
  // Wait for Vue to process the reactivity update
  await nextTick()
  
  // Then emit the apply action
  emit('apply', localFilters.value)
}
</script>

<style scoped>
.filter-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 24px;
}

.filter-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}

:deep(.ant-form-item-label) {
  padding-bottom: 4px;
}

:deep(.ant-form-item-label > label) {
  font-weight: 500;
  font-size: 13px;
}

@media (max-width: 768px) {
  .filter-card {
    position: static;
    margin-bottom: 24px;
  }
}
</style>
