<template>
  <div class="channels-page" v-loading="loading">
    <div class="page-header">
      <el-button v-if="userStore.isAdmin" type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        {{ $t('channel.add') }}
      </el-button>
    </div>

    <!-- Channel List -->
    <div class="channels-grid" v-if="channels.length > 0">
      <el-card v-for="channel in channels" :key="channel.channel_id" class="channel-card">
        <template #header>
          <div class="card-header">
            <div class="channel-info">
              <el-icon class="channel-icon" :class="channel.channel_type">
                <component :is="getChannelIcon(channel.channel_type)" />
              </el-icon>
              <div>
                <div class="channel-name">{{ channel.name }}</div>
                <el-tag size="small" :type="getStatusType(channel.status)">
                  {{ getStatusText(channel.status) }}
                </el-tag>
              </div>
            </div>
            <el-dropdown v-if="userStore.isAdmin" trigger="click">
              <el-button size="small" text>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="startChannel(channel.channel_id)" :disabled="channel.status === 'connected'">
                    <el-icon><VideoPlay /></el-icon> {{ $t('channel.start') }}
                  </el-dropdown-item>
                  <el-dropdown-item @click="stopChannel(channel.channel_id)" :disabled="channel.status !== 'connected'">
                    <el-icon><VideoPause /></el-icon> {{ $t('channel.stop') }}
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="deleteChannel(channel.channel_id)">
                    <el-icon><Delete /></el-icon> {{ $t('common.delete') }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>

        <div class="channel-details">
          <div class="detail-item">
            <span class="label">{{ $t('channel.type') }}:</span>
            <span class="value">{{ getChannelTypeName(channel.channel_type) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('channel.id') }}:</span>
            <span class="value code">{{ channel.channel_id }}</span>
          </div>
          <div class="detail-item" v-if="channel.reconnect_count > 0">
            <span class="label">{{ $t('channel.reconnects') }}:</span>
            <span class="value warning">{{ channel.reconnect_count }}</span>
          </div>
        </div>

        <div v-if="userStore.isAdmin" class="channel-actions">
          <el-button size="small" @click="openSendDialog(channel)" :disabled="channel.status !== 'connected'">
            {{ $t('channel.sendMessage') }}
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- Empty State - Centered -->
    <div v-else class="empty-state">
      <el-empty :description="$t('channel.noChannels')">
        <template #image>
          <el-icon :size="64" color="var(--pc-text-muted)"><Connection /></el-icon>
        </template>
      </el-empty>
    </div>

    <!-- Create Channel Dialog -->
    <el-dialog v-model="showCreateDialog" :title="$t('channel.add')" width="500px">
      <el-form :model="createForm" label-width="120px">
        <el-form-item :label="$t('channel.type')" required>
          <el-select v-model="createForm.channel_type" :placeholder="$t('channel.selectType')" style="width: 100%">
            <el-option
              v-for="type in availableTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('channel.name')" required>
          <el-input v-model="createForm.name" :placeholder="$t('channel.channelName')" />
        </el-form-item>

        <!-- Feishu Config -->
        <template v-if="createForm.channel_type === 'feishu'">
          <el-form-item :label="$t('channel.feishuAppId')" required>
            <el-input v-model="createForm.app_id" :placeholder="$t('channel.feishuAppId')" />
          </el-form-item>
          <el-form-item :label="$t('channel.feishuAppSecret')" required>
            <el-input v-model="createForm.app_secret" type="password" :placeholder="$t('channel.feishuAppSecret')" show-password />
          </el-form-item>
        </template>

        <el-form-item :label="$t('channel.autoReconnect')">
          <el-switch v-model="createForm.auto_reconnect" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createChannel" :loading="creating">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>

    <!-- Send Message Dialog -->
    <el-dialog v-model="showSendDialog" :title="$t('channel.sendMessage')" width="400px">
      <el-form :model="sendForm" label-width="80px">
        <el-form-item :label="$t('channel.chatId')">
          <el-input v-model="sendForm.chat_id" :placeholder="$t('channel.targetChatId')" />
        </el-form-item>
        <el-form-item :label="$t('channel.message')">
          <el-input v-model="sendForm.content" type="textarea" :rows="3" :placeholder="$t('channel.enterMessage')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSendDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="sendMessage" :loading="sending">{{ $t('channel.send') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, VideoPlay, VideoPause, Delete, ChatDotRound, Message, Connection } from '@element-plus/icons-vue'
import { api } from '../api'

const { t: $t } = useI18n()
const userStore = useUserStore()

interface ChannelInfo {
  channel_id: string
  channel_type: string
  name: string
  status: string
  enabled: boolean
  reconnect_count: number
}

const channels = ref<ChannelInfo[]>([])
const availableTypes = ref<{ value: string; label: string }[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showSendDialog = ref(false)
const creating = ref(false)
const sending = ref(false)
const currentChannel = ref<ChannelInfo | null>(null)

const createForm = ref({
  channel_type: 'feishu',
  name: '',
  app_id: '',
  app_secret: '',
  auto_reconnect: true,
})

const sendForm = ref({
  chat_id: '',
  content: '',
})

async function fetchChannels() {
  loading.value = true
  try {
    const res = await api.get('/channels')
    channels.value = res.data?.channels ? Object.values(res.data.channels) : []
  } catch (e: any) {
    ElMessage.error($t('channel.loadFailed') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

async function fetchAvailableTypes() {
  try {
    const res = await api.get('/channels/types/available')
    availableTypes.value = res.data?.types || []
  } catch (e: any) {
    console.error($t('channel.loadTypesFailed'), e)
  }
}

async function createChannel() {
  if (!createForm.value.name) {
    ElMessage.warning($t('channel.enterName'))
    return
  }

  creating.value = true
  try {
    const payload: any = {
      channel_type: createForm.value.channel_type,
      name: createForm.value.name,
      auto_reconnect: createForm.value.auto_reconnect,
    }

    if (createForm.value.channel_type === 'feishu') {
      if (!createForm.value.app_id || !createForm.value.app_secret) {
        ElMessage.warning($t('channel.enterAppCredentials'))
        creating.value = false
        return
      }
      payload.app_id = createForm.value.app_id
      payload.app_secret = createForm.value.app_secret
    }

    await api.post('/channels', payload)
    ElMessage.success($t('channel.createdSuccess'))
    showCreateDialog.value = false
    resetCreateForm()
    fetchChannels()
  } catch (e: any) {
    ElMessage.error($t('channel.createFailed') + ': ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

async function startChannel(channelId: string) {
  try {
    await api.post(`/channels/${channelId}/start`)
    ElMessage.success($t('channel.started'))
    fetchChannels()
  } catch (e: any) {
    ElMessage.error($t('channel.startFailed') + ': ' + (e.response?.data?.detail || e.message))
  }
}

async function stopChannel(channelId: string) {
  try {
    await api.post(`/channels/${channelId}/stop`)
    ElMessage.success($t('channel.stopped'))
    fetchChannels()
  } catch (e: any) {
    ElMessage.error($t('channel.stopFailed') + ': ' + (e.response?.data?.detail || e.message))
  }
}

async function deleteChannel(channelId: string) {
  try {
    await ElMessageBox.confirm($t('channel.confirmDelete'), $t('channel.confirmDeleteTitle'), { type: 'warning' })
    await api.delete(`/channels/${channelId}`)
    ElMessage.success($t('channel.deleted'))
    fetchChannels()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error($t('channel.deleteFailed') + ': ' + (e.response?.data?.detail || e.message))
    }
  }
}

function openSendDialog(channel: ChannelInfo) {
  currentChannel.value = channel
  sendForm.value = { chat_id: '', content: '' }
  showSendDialog.value = true
}

async function sendMessage() {
  if (!currentChannel.value || !sendForm.value.chat_id || !sendForm.value.content) {
    ElMessage.warning($t('channel.fillAllFields'))
    return
  }

  sending.value = true
  try {
    await api.post(`/channels/${currentChannel.value.channel_id}/send`, sendForm.value)
    ElMessage.success($t('channel.sent'))
    showSendDialog.value = false
  } catch (e: any) {
    ElMessage.error($t('channel.sendFailed') + ': ' + (e.response?.data?.detail || e.message))
  } finally {
    sending.value = false
  }
}

function resetCreateForm() {
  createForm.value = {
    channel_type: 'feishu',
    name: '',
    app_id: '',
    app_secret: '',
    auto_reconnect: true,
  }
}

function getChannelIcon(type: string) {
  const icons: Record<string, any> = {
    feishu: ChatDotRound,
    dingtalk: Message,
    wecom: Message,
  }
  return icons[type] || ChatDotRound
}

function getChannelTypeName(type: string) {
  const key = `channel.${type}`
  const fallback = type
  // Check if the translation key exists; if not, return the raw type
  const translated = $t(key)
  return translated === key ? fallback : translated
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    connected: 'success',
    connecting: 'warning',
    disconnected: 'info',
    reconnecting: 'warning',
    error: 'danger',
  }
  return types[status] || 'info'
}

function getStatusText(status: string) {
  const key = `channel.${status === 'error' ? 'errorStatus' : status}`
  const translated = $t(key)
  return translated === key ? status : translated
}

onMounted(() => {
  fetchChannels()
  fetchAvailableTypes()
})
</script>

<style scoped lang="scss">
.channels-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  backdrop-filter: var(--pc-glass-blur);
}

.channel-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .channel-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .channel-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    background: rgba(var(--pc-primary-rgb), 0.08);
    color: var(--pc-primary);

    &.feishu {
      background: rgba(var(--pc-accent-orange-rgb), 0.08);
      color: var(--pc-accent-orange);
    }
  }

  .channel-name {
    font-weight: 500;
    margin-bottom: 4px;
  }

  .channel-details {
    margin-top: 12px;

    .detail-item {
      display: flex;
      margin-bottom: 8px;
      font-size: 13px;

      .label {
        color: var(--pc-text-muted);
        width: 80px;
      }

      .value {
        color: var(--pc-text-primary);

        &.code {
          font-family: monospace;
          background: var(--pc-bg-deep);
          padding: 2px 6px;
          border-radius: 4px;
        }

        &.warning {
          color: var(--pc-accent-orange);
        }
      }
    }
  }

  .channel-actions {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--pc-border);
  }
}
</style>
