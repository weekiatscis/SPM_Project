<template>
  <a-modal
    v-model:open="modalVisible"
    title="Project Team Members"
    width="700px"
    :footer="null"
    @cancel="handleClose"
  >
    <div class="team-members-content">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <a-spin size="large" />
        <p>Loading team members...</p>
      </div>

      <!-- Team Members List -->
      <div v-else class="members-list">
        <!-- Project Owner -->
        <div class="member-section">
          <h3 class="section-title">
            <CrownOutlined class="crown-icon" />
            Project Owner
          </h3>
          <div class="member-card owner-card">
            <a-avatar :size="48" style="background-color: #667eea;">
              <template #icon>
                <UserOutlined />
              </template>
            </a-avatar>
            <div class="member-info">
              <div class="member-name">
                {{ ownerInfo?.name || 'Loading...' }}
                <a-tag color="gold" class="owner-badge">Owner</a-tag>
              </div>
              <div class="member-department">
                <TeamOutlined class="dept-icon" />
                {{ ownerInfo?.department || 'N/A' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Collaborators -->
        <div class="member-section">
          <h3 class="section-title">
            <TeamOutlined class="team-icon" />
            Collaborators ({{ collaboratorsList.length }})
          </h3>

          <div v-if="collaboratorsList.length === 0" class="empty-state">
            <a-empty description="No collaborators in this project" />
          </div>

          <div v-else class="collaborators-grid">
            <div
              v-for="collaborator in collaboratorsList"
              :key="collaborator.user_id"
              class="member-card"
            >
              <a-avatar :size="48" style="background-color: #9ca3af;">
                <template #icon>
                  <UserOutlined />
                </template>
              </a-avatar>
              <div class="member-info">
                <div class="member-name">{{ collaborator.name }}</div>
                <div class="member-department">
                  <TeamOutlined class="dept-icon" />
                  {{ collaborator.department || 'N/A' }}
                </div>
              </div>

              <!-- Actions (Only visible if current user is owner) -->
              <div v-if="isCurrentUserOwner" class="member-actions">
                <a-button
                  type="text"
                  size="small"
                  danger
                  @click="showRemoveCollaboratorModal(collaborator)"
                  :disabled="collaboratorsList.length === 1"
                >
                  <UserDeleteOutlined />
                  Remove
                </a-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </a-modal>

  <!-- Remove Collaborator Confirmation Modal -->
  <a-modal
    v-model:open="showRemoveModal"
    title="Remove Collaborator"
    width="500px"
    :maskClosable="false"
    @ok="confirmRemoveCollaborator"
    @cancel="cancelRemove"
  >
    <div class="confirmation-content">
      <ExclamationCircleOutlined class="warning-icon" />
      <p class="confirm-title">
        Are you sure you want to remove <strong>{{ selectedCollaborator?.name }}</strong> from this project?
      </p>
      <p class="confirm-description">
        This collaborator will lose access to all tasks and project information. This action cannot be undone.
      </p>
    </div>
    <template #footer>
      <a-button @click="cancelRemove">Cancel</a-button>
      <a-button type="primary" danger @click="confirmRemoveCollaborator" :loading="isRemoving">
        Remove Collaborator
      </a-button>
    </template>
  </a-modal>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { notification } from 'ant-design-vue'
import {
  UserOutlined,
  TeamOutlined,
  CrownOutlined,
  UserDeleteOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { useProjectEvents } from '../../composables/useProjectEvents'

export default {
  name: 'TeamMembersModal',
  components: {
    UserOutlined,
    TeamOutlined,
    CrownOutlined,
    UserDeleteOutlined,
    ExclamationCircleOutlined
  },
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    project: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'update'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    const { emitProjectUpdated } = useProjectEvents()

    const modalVisible = ref(false)
    const isLoading = ref(false)
    const ownerInfo = ref(null)
    const collaboratorsList = ref([])

    // Remove collaborator state
    const showRemoveModal = ref(false)
    const selectedCollaborator = ref(null)
    const isRemoving = ref(false)

    // Check if current user is the project owner
    const isCurrentUserOwner = computed(() => {
      return authStore.user?.user_id === props.project?.created_by_id
    })

    // Sync modal visibility
    watch(() => props.isOpen, (newVal) => {
      modalVisible.value = newVal
      if (newVal) {
        loadTeamMembers()
      }
    }, { immediate: true })

    // Fetch user details by ID
    const fetchUserDetails = async (userId) => {
      try {
        // User service runs on port 8081
        const response = await fetch(`http://localhost:8081/users/${userId}`)

        if (!response.ok) {
          console.error(`Failed to fetch user ${userId}: HTTP ${response.status}`)
          throw new Error(`HTTP ${response.status}`)
        }

        const payload = await response.json()
        console.log(`Fetched user ${userId}:`, payload.user) // Debug log
        return payload.user || null
      } catch (error) {
        console.error(`Failed to fetch user ${userId}:`, error)
        return null
      }
    }

    // Load all team members with their details
    const loadTeamMembers = async () => {
      isLoading.value = true

      try {
        // Fetch owner info
        if (props.project?.created_by_id) {
          ownerInfo.value = await fetchUserDetails(props.project.created_by_id)
        }

        // Fetch collaborators info
        if (props.project?.collaborators && Array.isArray(props.project.collaborators)) {
          const collaboratorPromises = props.project.collaborators.map(userId =>
            fetchUserDetails(userId)
          )
          const collaboratorResults = await Promise.all(collaboratorPromises)
          collaboratorsList.value = collaboratorResults.filter(Boolean)
        } else {
          collaboratorsList.value = []
        }
      } catch (error) {
        console.error('Failed to load team members:', error)
        notification.error({
          message: 'Failed to load team members',
          description: 'Unable to fetch team member information.',
          placement: 'topRight',
          duration: 3
        })
      } finally {
        isLoading.value = false
      }
    }

    // Show remove collaborator modal
    const showRemoveCollaboratorModal = (collaborator) => {
      selectedCollaborator.value = collaborator
      showRemoveModal.value = true
    }

    // Cancel remove
    const cancelRemove = () => {
      showRemoveModal.value = false
      selectedCollaborator.value = null
    }

    // Confirm remove collaborator
    const confirmRemoveCollaborator = async () => {
      if (!selectedCollaborator.value) return

      isRemoving.value = true

      try {
        const projectServiceUrl = import.meta.env.VITE_PROJECT_SERVICE_URL || 'http://localhost:8082'

        // Remove collaborator from the list
        const updatedCollaborators = props.project.collaborators.filter(
          id => id !== selectedCollaborator.value.user_id
        )

        // Call API to update project - include all required fields
        const response = await fetch(`${projectServiceUrl}/projects/${props.project.project_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            project_name: props.project.project_name,
            project_description: props.project.project_description || '',
            due_date: props.project.due_date,
            created_by: props.project.created_by_id,
            user_id: authStore.user?.user_id,
            collaborators: updatedCollaborators
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        notification.success({
          message: 'Collaborator Removed',
          description: `${selectedCollaborator.value.name} has been removed from the project.`,
          placement: 'topRight',
          duration: 3
        })

        // Emit update event
        const updatedProject = {
          ...props.project,
          collaborators: updatedCollaborators
        }
        emitProjectUpdated(updatedProject)
        emit('update', updatedProject)

        // Reload team members
        await loadTeamMembers()

        // Close modal
        showRemoveModal.value = false
        selectedCollaborator.value = null
      } catch (error) {
        console.error('Failed to remove collaborator:', error)
        notification.error({
          message: 'Failed to Remove Collaborator',
          description: error.message || 'An error occurred while removing the collaborator.',
          placement: 'topRight',
          duration: 4
        })
      } finally {
        isRemoving.value = false
      }
    }

    const handleClose = () => {
      modalVisible.value = false
      emit('close')
    }

    return {
      modalVisible,
      isLoading,
      ownerInfo,
      collaboratorsList,
      isCurrentUserOwner,
      showRemoveModal,
      selectedCollaborator,
      isRemoving,
      showRemoveCollaboratorModal,
      cancelRemove,
      confirmRemoveCollaborator,
      handleClose
    }
  }
}
</script>

<style scoped>
.team-members-content {
  min-height: 300px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
}

.loading-state p {
  margin-top: 16px;
  font-size: 14px;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.member-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.crown-icon {
  color: #f59e0b;
  font-size: 18px;
}

.team-icon {
  color: #667eea;
  font-size: 18px;
}

.member-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  transition: all 0.2s ease;
  position: relative;
}

.member-card:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.owner-card {
  border-color: #fbbf24;
  background: linear-gradient(to right, #fffbeb, #ffffff);
}

.owner-card:hover {
  border-color: #f59e0b;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.owner-badge {
  margin: 0;
}

.member-department {
  font-size: 14px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dept-icon {
  font-size: 12px;
}

.member-actions {
  flex-shrink: 0;
}

.collaborators-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

/* Confirmation Modals */
.confirmation-content {
  padding: 20px 0;
  text-align: center;
}

.warning-icon {
  font-size: 48px;
  color: #f59e0b;
  margin-bottom: 16px;
}

.warning-icon.transfer {
  color: #667eea;
}

.confirm-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.confirm-description {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .member-card {
    padding: 12px;
  }

  .member-name {
    font-size: 14px;
  }

  .member-department {
    font-size: 12px;
  }
}
</style>
