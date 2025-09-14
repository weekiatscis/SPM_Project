// Icon components for the Smart Task Manager
import BaseIcon from './BaseIcon.vue'
import ImageIcon from './ImageIcon.vue'
import HybridIcon from './HybridIcon.vue'
import ViteImageIcon from './ViteImageIcon.vue'

// Navigation Icons
export const HomeIcon = {
  name: 'HomeIcon',
  props: ['size', 'color', 'alt', 'spin'],
  template: `
    <div class="flex items-center">
      <img 
        src="/public/home.png" 
        :alt="alt || 'Home'"
        class="w-8 h-8 inline-block object-contain"
        @error="console.error('Failed to load home icon')"
        @load="console.log('Home icon loaded successfully')"
      />
    </div>
  `
}

export const TaskIcon = {
  name: 'TaskIcon',
  props: ['size', 'color', 'alt', 'spin'],
  template: `
    <div class="flex items-center">
      <img 
        src="/public/task.png" 
        :alt="alt || 'Task'"
        class="w-8 h-8 inline-block object-contain"
        @error="console.error('Failed to load task icon')"
        @load="console.log('Task icon loaded successfully')"
      />
    </div>
  `
}

export const DashboardIcon = {
  name: 'DashboardIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <rect x="3" y="3" width="7" height="7"/>
      <rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/>
      <rect x="3" y="14" width="7" height="7"/>
    </BaseIcon>
  `
}

export const ProjectIcon = {
  name: 'ProjectIcon',
  props: ['size', 'color', 'alt', 'spin'],
  template: `
    <div class="flex items-center">
      <img 
        src="/public/project.png" 
        :alt="alt || 'Project'"
        class="w-8 h-8 inline-block object-contain"
        @error="console.error('Failed to load project icon')"
        @load="console.log('Project icon loaded successfully')"
      />
    </div>
  `
}

export const SettingsIcon = {
  name: 'SettingsIcon',
  props: ['size', 'color', 'alt', 'spin'],
  template: `
    <div class="flex items-center">
      <img 
        src="/public/settings.png" 
        :alt="alt || 'Settings'"
        class="w-8 h-8 inline-block object-contain"
        @error="console.error('Failed to load settings icon')"
        @load="console.log('Settings icon loaded successfully')"
      />
    </div>
  `
}

// Action Icons
export const PlusIcon = {
  name: 'PlusIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <line x1="12" y1="5" x2="12" y2="19"/>
      <line x1="5" y1="12" x2="19" y2="12"/>
    </BaseIcon>
  `
}

export const EditIcon = {
  name: 'EditIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
    </BaseIcon>
  `
}

export const DeleteIcon = {
  name: 'DeleteIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polyline points="3,6 5,6 21,6"/>
      <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
      <line x1="10" y1="11" x2="10" y2="17"/>
      <line x1="14" y1="11" x2="14" y2="17"/>
    </BaseIcon>
  `
}

export const SearchIcon = {
  name: 'SearchIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <circle cx="11" cy="11" r="8"/>
      <path d="m21 21-4.35-4.35"/>
    </BaseIcon>
  `
}

export const FilterIcon = {
  name: 'FilterIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46"/>
    </BaseIcon>
  `
}

export const CloseIcon = {
  name: 'CloseIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <line x1="18" y1="6" x2="6" y2="18"/>
      <line x1="6" y1="6" x2="18" y2="18"/>
    </BaseIcon>
  `
}

// Status Icons
export const CheckIcon = {
  name: 'CheckIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polyline points="20,6 9,17 4,12"/>
    </BaseIcon>
  `
}

export const CheckCircleIcon = {
  name: 'CheckCircleIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
      <polyline points="22,4 12,14.01 9,11.01"/>
    </BaseIcon>
  `
}

export const ClockIcon = {
  name: 'ClockIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12,6 12,12 16,14"/>
    </BaseIcon>
  `
}

export const AlertIcon = {
  name: 'AlertIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </BaseIcon>
  `
}

export const ExclamationIcon = {
  name: 'ExclamationIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </BaseIcon>
  `
}

// User & Profile Icons
export const UserIcon = {
  name: 'UserIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </BaseIcon>
  `
}

export const UsersIcon = {
  name: 'UsersIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 00-3-3.87"/>
      <path d="M16 3.13a4 4 0 010 7.75"/>
    </BaseIcon>
  `
}

export const LogoutIcon = {
  name: 'LogoutIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
      <polyline points="16,17 21,12 16,7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </BaseIcon>
  `
}

// Date & Time Icons
export const CalendarIcon = {
  name: 'CalendarIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </BaseIcon>
  `
}

// Communication Icons
export const BellIcon = {
  name: 'BellIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 01-3.46 0"/>
    </BaseIcon>
  `
}

export const MessageIcon = {
  name: 'MessageIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
    </BaseIcon>
  `
}

// Menu & Navigation Icons
export const MenuIcon = {
  name: 'MenuIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <line x1="3" y1="6" x2="21" y2="6"/>
      <line x1="3" y1="12" x2="21" y2="12"/>
      <line x1="3" y1="18" x2="21" y2="18"/>
    </BaseIcon>
  `
}

export const ChevronDownIcon = {
  name: 'ChevronDownIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polyline points="6,9 12,15 18,9"/>
    </BaseIcon>
  `
}

export const ChevronRightIcon = {
  name: 'ChevronRightIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polyline points="9,18 15,12 9,6"/>
    </BaseIcon>
  `
}

export const ChevronLeftIcon = {
  name: 'ChevronLeftIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polyline points="15,18 9,12 15,6"/>
    </BaseIcon>
  `
}

// Priority & Status Indicators
export const FlagIcon = {
  name: 'FlagIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
      <line x1="4" y1="22" x2="4" y2="15"/>
    </BaseIcon>
  `
}

export const StarIcon = {
  name: 'StarIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
    </BaseIcon>
  `
}

// File & Document Icons
export const FileIcon = {
  name: 'FileIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
      <polyline points="14,2 14,8 20,8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10,9 9,9 8,9"/>
    </BaseIcon>
  `
}

export const DownloadIcon = {
  name: 'DownloadIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
      <polyline points="7,10 12,15 17,10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </BaseIcon>
  `
}

// Loading Icon
export const LoadingIcon = {
  name: 'LoadingIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth'],
  template: `
    <BaseIcon v-bind="$props" :spin="true">
      <circle cx="12" cy="12" r="10" opacity="0.25"/>
      <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" opacity="0.75"/>
    </BaseIcon>
  `
}

// Chart & Analytics Icons
export const BarChartIcon = {
  name: 'BarChartIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <line x1="12" y1="20" x2="12" y2="10"/>
      <line x1="18" y1="20" x2="18" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="16"/>
    </BaseIcon>
  `
}

export const PieChartIcon = {
  name: 'PieChartIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <path d="M21.21 15.89A10 10 0 118 2.83"/>
      <path d="M22 12A10 10 0 0012 2v10z"/>
    </BaseIcon>
  `
}

export const TrendingUpIcon = {
  name: 'TrendingUpIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polyline points="23,6 13.5,15.5 8.5,10.5 1,18"/>
      <polyline points="17,6 23,6 23,12"/>
    </BaseIcon>
  `
}

export const TrendingDownIcon = {
  name: 'TrendingDownIcon',
  components: { BaseIcon },
  props: ['size', 'color', 'fill', 'stroke', 'strokeWidth', 'spin'],
  template: `
    <BaseIcon v-bind="$props">
      <polyline points="23,18 13.5,8.5 8.5,13.5 1,6"/>
      <polyline points="17,18 23,18 23,12"/>
    </BaseIcon>
  `
}

// Helper function to create PNG-based icons
export const createImageIcon = (iconName, displayName, altText) => ({
  name: displayName || `${iconName}Icon`,
  components: { ImageIcon },
  props: ['size', 'color', 'alt', 'spin'],
  template: `
    <ImageIcon 
      name="${iconName}" 
      v-bind="$props"
      :alt="alt || '${altText || iconName}'"
    />
  `
})

// Export all icons
export default {
  BaseIcon,
  ImageIcon,
  HybridIcon,
  HomeIcon,
  TaskIcon,
  DashboardIcon,
  ProjectIcon,
  SettingsIcon,
  PlusIcon,
  EditIcon,
  DeleteIcon,
  SearchIcon,
  FilterIcon,
  CloseIcon,
  CheckIcon,
  CheckCircleIcon,
  ClockIcon,
  AlertIcon,
  ExclamationIcon,
  UserIcon,
  UsersIcon,
  LogoutIcon,
  CalendarIcon,
  BellIcon,
  MessageIcon,
  MenuIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
  FlagIcon,
  StarIcon,
  FileIcon,
  DownloadIcon,
  LoadingIcon,
  BarChartIcon,
  PieChartIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  createImageIcon
}
