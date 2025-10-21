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
          <a-select-option value="Ongoing">
            <a-badge status="processing" text="Ongoing" />
          </a-select-option>
          <a-select-option value="Under Review">
            <a-badge status="warning" text="Under Review" />
          </a-select-option>
          <a-select-option value="Completed">
            <a-badge status="success" text="Completed" />
          </a-select-option>
        </a-select>
      </a-form-item>

      <!-- HR-specific filters -->
      <template v-if="isHRUser">
        <!-- Department Filter -->
        <a-form-item label="Department">
          <a-select
            v-model:value="localFilters.departments"
            mode="multiple"
            placeholder="All departments"
            :options="departmentOptions"
            :max-tag-count="2"
            allow-clear
            show-search
            :disabled="isLoading"
            @change="emitFilterChange"
          >
            <template #maxTagPlaceholder="omittedValues">
              <span>+{{ omittedValues.length }} more</span>
            </template>
          </a-select>
          <div v-if="departmentOptions.length > 0" class="filter-hint">
            {{ departmentOptions.length }} department{{ departmentOptions.length !== 1 ? 's' : '' }}
          </div>
        </a-form-item>

        <!-- Role Filter -->
        <a-form-item label="Role">
          <a-select
            v-model:value="localFilters.roles"
            mode="multiple"
            placeholder="All roles"
            :options="roleOptions"
            :max-tag-count="2"
            allow-clear
            show-search
            :disabled="isLoading"
            @change="emitFilterChange"
          >
            <template #maxTagPlaceholder="omittedValues">
              <span>+{{ omittedValues.length }} more</span>
            </template>
          </a-select>
          <div v-if="roleOptions.length > 0" class="filter-hint">
            {{ roleOptions.length }} role{{ roleOptions.length !== 1 ? 's' : '' }}
          </div>
        </a-form-item>

        <!-- Employee Name Filter -->
        <a-form-item label="Employee Name">
          <a-select
            v-model:value="localFilters.assignees"
            mode="multiple"
            placeholder="All employees"
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
            {{ subordinates.length }} employee{{ subordinates.length !== 1 ? 's' : '' }}
          </div>
        </a-form-item>
      </template>

      <!-- Director-specific filters -->
      <template v-else-if="isDirector">
        <!-- Manager Filter (Directors only see their Managers) -->
        <a-form-item label="Manager Name">
          <a-select
            v-model:value="localFilters.assignees"
            mode="multiple"
            placeholder="All managers"
            :options="managerOptions"
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
          <div v-if="managerOptions.length > 0" class="filter-hint">
            {{ managerOptions.length }} manager{{ managerOptions.length !== 1 ? 's' : '' }} in your department
          </div>
        </a-form-item>
      </template>

      <!-- Manager: Team Members Filter -->
      <a-form-item v-else-if="isManager" label="Team Members">
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

      <!-- Due Date Range (Hidden for Directors) -->
      <a-form-item v-if="!isDirector" label="Due Date Range">
        <a-range-picker
          v-model:value="localFilters.dateRange"
          format="MMM DD, YYYY"
          :disabled="isLoading"
          style="width: 100%"
          @change="emitFilterChange"
        />
      </a-form-item>

      <!-- Priority Filter -->
      <a-form-item label="Priority (1-10)">
        <a-select
          v-model:value="localFilters.priority"
          placeholder="All Priorities"
          allow-clear
          :disabled="isLoading"
          @change="emitFilterChange"
        >
          <a-select-option :value="10">
            <a-tag color="red">10 - Highest</a-tag>
          </a-select-option>
          <a-select-option :value="9">
            <a-tag color="red">9 - Very High</a-tag>
          </a-select-option>
          <a-select-option :value="8">
            <a-tag color="orange">8 - High</a-tag>
          </a-select-option>
          <a-select-option :value="7">
            <a-tag color="orange">7</a-tag>
          </a-select-option>
          <a-select-option :value="6">
            <a-tag color="gold">6</a-tag>
          </a-select-option>
          <a-select-option :value="5">
            <a-tag color="gold">5 - Medium</a-tag>
          </a-select-option>
          <a-select-option :value="4">
            <a-tag color="blue">4</a-tag>
          </a-select-option>
          <a-select-option :value="3">
            <a-tag color="blue">3</a-tag>
          </a-select-option>
          <a-select-option :value="2">
            <a-tag color="cyan">2 - Low</a-tag>
          </a-select-option>
          <a-select-option :value="1">
            <a-tag color="cyan">1 - Lowest</a-tag>
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
            <span style="margin-left: 8px;">Highest Priority (10)</span>
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
  },
  userRole: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:filters', 'apply', 'reset'])

const localFilters = ref({ ...props.filters })

// Watch for external filter changes
watch(() => props.filters, (newFilters) => {
  localFilters.value = { ...newFilters }
}, { deep: true })

// Check if user is HR
const isHRUser = computed(() => props.userRole === 'HR')

// Check if user is Director
const isDirector = computed(() => props.userRole === 'Director')

// Check if user is Manager
const isManager = computed(() => props.userRole === 'Manager')

const subordinateOptions = computed(() => {
  return props.subordinates.map(sub => ({
    label: `${sub.name} (${sub.role})`,
    value: sub.user_id,
    role: sub.role,
    department: sub.department
  }))
})

// For Directors: Show only Managers in the same department
const managerOptions = computed(() => {
  if (!isDirector.value) return []
  
  return props.subordinates
    .filter(sub => sub.role === 'Manager')
    .map(sub => ({
      label: `${sub.name} (${sub.role})`,
      value: sub.user_id,
      role: sub.role,
      department: sub.department
    }))
})

// Get unique departments for HR filter
const departmentOptions = computed(() => {
  const departments = [...new Set(props.subordinates.map(sub => sub.department).filter(Boolean))]
  return departments.sort().map(dept => ({
    label: dept,
    value: dept
  }))
})

// Get unique roles for HR filter
const roleOptions = computed(() => {
  const roles = [...new Set(props.subordinates.map(sub => sub.role).filter(Boolean))]
  return roles.sort().map(role => ({
    label: role,
    value: role
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
    searchText: '',
    departments: [],
    roles: []
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
    searchText: '',
    departments: [],
    roles: []
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
      // Set to priority 10 (highest priority)
      localFilters.value.priority = 10
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
