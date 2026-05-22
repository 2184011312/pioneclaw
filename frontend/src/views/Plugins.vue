<template>
  <div class="plugins-page">
    <div class="page-header">
      <div class="header-actions">
        <el-button type="primary" @click="discoverPlugins" :loading="discovering">
          <el-icon><Search /></el-icon>
          {{ $t('plugin.discover') }}
        </el-button>
        <el-button @click="loadData">
          <el-icon><Refresh /></el-icon>
          {{ $t('common.refresh') }}
        </el-button>
        <el-button @click="runHealthCheck" :loading="healthChecking">
          <el-icon><FirstAidKit /></el-icon>
          {{ $t('plugin.healthCheck') }}
        </el-button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="plugin-stats">
      <div class="stat-card">
        <div class="stat-icon total">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">{{ $t('plugin.total') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon loaded">
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.by_state?.loaded || 0 }}</div>
          <div class="stat-label">{{ $t('plugin.loaded') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon unloaded">
          <el-icon><Close /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.by_state?.unloaded || 0 }}</div>
          <div class="stat-label">{{ $t('plugin.unloaded') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon error">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ (stats.by_state?.error || 0) + (stats.by_state?.retrying || 0) }}</div>
          <div class="stat-label">{{ $t('plugin.loadError') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon healthy">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ healthyCount }}/{{ pluginHealthTotal }}</div>
          <div class="stat-label">{{ $t('plugin.healthy') }}</div>
        </div>
      </div>
    </div>

    <!-- Tabs for Plugins and Events -->
    <el-tabs v-model="activeTab" class="plugin-tabs">
      <el-tab-pane :label="$t('plugin.loadedPlugins')" name="plugins">
        <!-- Plugin List -->
        <el-table :data="plugins" v-loading="loading" style="width: 100%" class="pc-data-table plugins-table">
          <template #empty>
            <el-empty :description="$t('plugin.noPlugins')" />
          </template>
          <el-table-column prop="name" :label="$t('common.name')" width="200">
            <template #default="{ row }">
              <div class="plugin-name-cell">
                <span class="plugin-name">{{ row.name }}</span>
                <el-tag v-if="row.version" size="small" type="info">v{{ row.version }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" :label="$t('common.description')" min-width="200" show-overflow-tooltip />
          <el-table-column :label="$t('common.status')" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getStateType(row.state)" size="small" :class="{ 'retrying-tag': row.state === 'retrying' }">
                {{ getStateText(row.state) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('plugin.health')" width="70" align="center">
            <template #default="{ row }">
              <el-tooltip v-if="row.health_status !== undefined && row.health_status !== null"
                :content="$t(row.health_status ? 'plugin.healthy' : 'plugin.unhealthy')"
                placement="top"
              >
                <el-icon :size="18" :color="row.health_status ? 'var(--pc-accent-green)' : 'var(--pc-accent-red)'">
                  <CircleCheck v-if="row.health_status" />
                  <CircleClose v-else />
                </el-icon>
              </el-tooltip>
              <span v-else class="text-muted">—</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('plugin.dependencies')" width="120" align="center">
            <template #default="{ row }">
              <el-popover
                v-if="row.dependencies && row.dependencies.length > 0"
                placement="left"
                :title="$t('plugin.dependencies')"
                :width="300"
                trigger="hover"
              >
                <template #reference>
                  <el-tag type="info" size="small">
                    {{ row.dependencies.length }} {{ $t('plugin.dependencies') }}
                  </el-tag>
                </template>
                <ul class="deps-list">
                  <li v-for="dep in row.dependencies" :key="dep">{{ dep }}</li>
                </ul>
              </el-popover>
              <span v-else class="text-muted">{{ $t('plugin.noDependencies') }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('plugin.subscriptions')" width="120" align="center">
            <template #default="{ row }">
              <el-popover
                v-if="row.subscriptions && row.subscriptions.length > 0"
                placement="left"
                :title="$t('plugin.subscriptions')"
                :width="300"
                trigger="hover"
              >
                <template #reference>
                  <el-tag type="success" size="small">
                    {{ row.subscriptions.length }} {{ $t('plugin.subscriptions') }}
                  </el-tag>
                </template>
                <ul class="subs-list">
                  <li v-for="sub in row.subscriptions" :key="sub">{{ sub }}</li>
                </ul>
              </el-popover>
              <span v-else class="text-muted">{{ $t('plugin.noSubscriptions') }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.actions')" width="260" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <!-- LOADED: ACTIVE state -->
                <template v-if="row.state === 'loaded'">
                  <el-button size="small" text type="primary" @click="pausePlugin(row)">
                    {{ $t('plugin.pause') }}
                  </el-button>
                  <el-button size="small" text type="warning" @click="stopPlugin(row)">
                    {{ $t('plugin.stop') }}
                  </el-button>
                  <el-button size="small" text type="primary" @click="reloadPlugin(row)">
                    {{ $t('plugin.reload') }}
                  </el-button>
                </template>
                <!-- PAUSED -->
                <template v-else-if="row.state === 'paused'">
                  <el-button size="small" text type="success" @click="resumePlugin(row)">
                    {{ $t('plugin.resume') }}
                  </el-button>
                  <el-button size="small" text type="warning" @click="stopPlugin(row)">
                    {{ $t('plugin.stop') }}
                  </el-button>
                </template>
                <!-- ERROR -->
                <template v-else-if="row.state === 'error'">
                  <el-tooltip :content="row.error" placement="top">
                    <el-button size="small" text type="warning" @click="restartPlugin(row)">
                      {{ $t('plugin.restart') }}
                    </el-button>
                  </el-tooltip>
                  <el-button size="small" text type="danger" @click="stopPlugin(row)">
                    {{ $t('plugin.stop') }}
                  </el-button>
                </template>
                <!-- RETRYING -->
                <template v-else-if="row.state === 'retrying'">
                  <el-button size="small" text type="warning" disabled>
                    <el-icon class="is-loading"><Loading /></el-icon>
                    {{ $t('plugin.retrying') }}
                  </el-button>
                </template>
                <!-- STOPPED -->
                <template v-else-if="row.state === 'stopped'">
                  <el-button size="small" text type="primary" @click="restartPlugin(row)">
                    {{ $t('plugin.restart') }}
                  </el-button>
                  <el-button size="small" text type="success" @click="enablePlugin(row)">
                    {{ $t('plugin.enable') }}
                  </el-button>
                </template>
                <!-- DISABLED -->
                <template v-else-if="row.state === 'disabled'">
                  <el-button size="small" text type="success" @click="enablePlugin(row)">
                    {{ $t('plugin.enable') }}
                  </el-button>
                </template>
                <!-- UNLOADED -->
                <template v-else-if="row.state === 'unloaded'">
                  <el-button size="small" text type="primary" @click="loadPlugin(row)">
                    {{ $t('plugin.load') }}
                  </el-button>
                </template>
                <!-- LOADING / UNLOADING / STOPPING -->
                <template v-else>
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span class="text-muted" style="margin-left:4px">{{ row.state }}</span>
                </template>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="$t('plugin.eventBus')" name="events">
        <!-- Event Subscriptions -->
        <el-table :data="subscriptions" v-loading="loadingEvents" style="width: 100%" class="pc-data-table events-table">
          <template #empty>
            <el-empty :description="$t('plugin.noSubscriptions')" />
          </template>
          <el-table-column prop="sub_id" :label="$t('plugin.pluginId')" width="280" show-overflow-tooltip />
          <el-table-column prop="topic" :label="$t('plugin.topic')" width="200" />
          <el-table-column prop="handler" :label="$t('plugin.handler')" min-width="200" show-overflow-tooltip />
          <el-table-column prop="priority" :label="$t('plugin.priority')" width="100" align="center" />
          <el-table-column :label="$t('plugin.wildcard')" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.wildcard ? 'success' : 'info'" size="small">
                {{ row.wildcard ? 'Yes' : 'No' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Discover Dialog -->
    <el-dialog v-model="discoverDialogVisible" :title="$t('plugin.availablePlugins')" width="600px">
      <el-table :data="discoveredPlugins" v-loading="discovering">
        <el-table-column prop="name" :label="$t('common.name')" />
        <el-table-column :label="$t('common.actions')" width="150" align="center">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              :disabled="isPluginLoaded(row)"
              @click="loadDiscoveredPlugin(row)"
            >
              {{ isPluginLoaded(row) ? $t('plugin.loaded') : $t('plugin.load') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, Check, Close, Warning, Search, Refresh, CircleCheck, CircleClose, FirstAidKit, Loading } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { pluginsApi, type PluginResponse, type PluginStats, type SubscriptionInfo, type LifecycleResponse } from '@/api/plugins'

const { t: $t } = useI18n()

const loading = ref(false)
const discovering = ref(false)
const loadingEvents = ref(false)
const activeTab = ref('plugins')
const plugins = ref<PluginResponse[]>([])
const stats = ref<PluginStats>({
  total: 0,
  by_state: {},
  plugin_dir: null,
})
const subscriptions = ref<SubscriptionInfo[]>([])
const discoveredPlugins = ref<{ name: string }[]>([])
const discoverDialogVisible = ref(false)
const healthChecking = ref(false)
const healthStatuses = ref<Record<string, boolean | null>>({})
const healthyCount = ref(0)
const pluginHealthTotal = ref(0)

async function loadData() {
  loading.value = true
  try {
    const [pluginsRes, statsRes, healthRes] = await Promise.all([
      pluginsApi.list(),
      pluginsApi.stats(),
      pluginsApi.healthAll().catch(() => ({ data: [] as LifecycleResponse[] })),
    ])
    plugins.value = pluginsRes.data
    stats.value = statsRes.data

    // Merge health status into plugin rows
    const healthMap: Record<string, boolean | null> = {}
    let hCount = 0
    let hTotal = 0
    for (const h of healthRes.data) {
      healthMap[h.plugin_id] = h.health_status
      if (h.state === 'loaded' || h.state === 'paused') {
        hTotal++
        if (h.health_status) hCount++
      }
    }
    healthStatuses.value = healthMap
    healthyCount.value = hCount
    pluginHealthTotal.value = hTotal

    // Augment plugin rows with health status
    for (const p of plugins.value) {
      ;(p as any).health_status = healthMap[p.plugin_id] ?? undefined
    }
  } catch (error) {
    ElMessage.error($t('common.failed'))
  } finally {
    loading.value = false
  }
}

async function loadSubscriptions() {
  loadingEvents.value = true
  try {
    const res = await pluginsApi.listSubscriptions()
    subscriptions.value = res.data
  } catch (error) {
    ElMessage.error($t('common.failed'))
  } finally {
    loadingEvents.value = false
  }
}

async function loadPlugin(plugin: PluginResponse) {
  try {
    await pluginsApi.load(plugin.plugin_id)
    ElMessage.success($t('plugin.loadSuccess'))
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.loadFailed'))
  }
}

async function reloadPlugin(plugin: PluginResponse) {
  try {
    await pluginsApi.reload(plugin.plugin_id)
    ElMessage.success($t('plugin.reloadSuccess'))
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.reloadFailed'))
  }
}

async function pausePlugin(plugin: PluginResponse) {
  try {
    await pluginsApi.pause(plugin.plugin_id)
    ElMessage.success($t('plugin.pauseSuccess'))
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.pauseFailed'))
  }
}

async function resumePlugin(plugin: PluginResponse) {
  try {
    await pluginsApi.resume(plugin.plugin_id)
    ElMessage.success($t('plugin.resumeSuccess'))
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.resumeFailed'))
  }
}

async function stopPlugin(plugin: PluginResponse) {
  try {
    await pluginsApi.stop(plugin.plugin_id)
    ElMessage.success($t('plugin.stopSuccess'))
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.stopFailed'))
  }
}

async function restartPlugin(plugin: PluginResponse) {
  try {
    await pluginsApi.restart(plugin.plugin_id)
    ElMessage.success($t('plugin.restartSuccess'))
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.restartFailed'))
  }
}

async function enablePlugin(plugin: PluginResponse) {
  try {
    await pluginsApi.enable(plugin.plugin_id)
    ElMessage.success($t('plugin.enableSuccess'))
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.enableFailed'))
  }
}

async function runHealthCheck() {
  healthChecking.value = true
  try {
    const res = await pluginsApi.healthAll()
    const healthMap: Record<string, boolean | null> = {}
    let hCount = 0
    let hTotal = 0
    for (const h of res.data) {
      healthMap[h.plugin_id] = h.health_status
      if (h.state === 'loaded' || h.state === 'paused') {
        hTotal++
        if (h.health_status) hCount++
      }
    }
    healthStatuses.value = healthMap
    healthyCount.value = hCount
    pluginHealthTotal.value = hTotal
    for (const p of plugins.value) {
      ;(p as any).health_status = healthMap[p.plugin_id] ?? undefined
    }
    ElMessage.success($t('plugin.healthCheckDone'))
  } catch (error: any) {
    ElMessage.error($t('plugin.healthCheckFailed'))
  } finally {
    healthChecking.value = false
  }
}

async function discoverPlugins() {
  discovering.value = true
  try {
    const res = await pluginsApi.discover()
    discoveredPlugins.value = res.data.map(name => ({ name }))
    discoverDialogVisible.value = true
  } catch (error) {
    ElMessage.error($t('common.failed'))
  } finally {
    discovering.value = false
  }
}

async function loadDiscoveredPlugin(plugin: { name: string }) {
  try {
    await pluginsApi.load(plugin.name)
    ElMessage.success($t('plugin.loadSuccess'))
    discoverDialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('plugin.loadFailed'))
  }
}

function isPluginLoaded(plugin: { name: string }) {
  return plugins.value.some(p => p.plugin_id === plugin.name && p.state === 'loaded')
}

function getStateType(state: string) {
  const types: Record<string, string> = {
    loaded: 'success',
    loading: 'info',
    unloaded: 'info',
    unloading: 'info',
    error: 'danger',
    retrying: 'warning',
    paused: '',
    stopping: 'info',
    stopped: 'info',
    disabled: 'info',
  }
  return types[state] || 'info'
}

function getStateText(state: string) {
  const texts: Record<string, string> = {
    loaded: $t('plugin.loaded'),
    loading: $t('plugin.loading'),
    unloaded: $t('plugin.unloaded'),
    unloading: $t('plugin.unloading'),
    error: $t('plugin.loadError'),
    retrying: $t('plugin.retrying'),
    paused: $t('plugin.paused'),
    stopping: $t('plugin.stopping'),
    stopped: $t('plugin.stopped'),
    disabled: $t('plugin.disabled'),
  }
  return texts[state] || state
}

onMounted(() => {
  loadData()
  loadSubscriptions()
})
</script>

<style scoped lang="scss">
.plugins-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.plugin-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: var(--pc-bg-surface);
    border: 1px solid var(--pc-border);
    border-radius: 12px;
    transition: all 0.3s ease;

    &:hover {
      border-color: var(--pc-primary);
      box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      min-width: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
      font-size: 24px;

      &.total {
        background: rgba(0, 212, 255, 0.1);
        color: var(--pc-primary);
      }

      &.loaded {
        background: rgba(0, 229, 160, 0.1);
        color: var(--pc-accent-green);
      }

      &.unloaded {
        background: rgba(160, 164, 184, 0.1);
        color: var(--pc-text-muted);
      }

      &.error {
        background: rgba(255, 82, 82, 0.1);
        color: var(--pc-accent-red);
      }

      &.healthy {
        background: rgba(0, 229, 160, 0.1);
        color: var(--pc-accent-green);
      }
    }

    .stat-info {
      display: flex;
      flex-direction: column;
      justify-content: center;

      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: var(--pc-text-primary);
        line-height: 1.2;
      }

      .stat-label {
        font-size: 13px;
        color: var(--pc-text-muted);
        margin-top: 4px;
        line-height: 1.4;
      }
    }
  }
}

.plugin-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }
}

.plugins-table,
.events-table {
  background: transparent;
  border-radius: 12px;
  overflow: hidden;
}

.plugin-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .plugin-name {
    font-weight: 500;
    color: var(--pc-text-primary);
  }
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.text-muted {
  color: var(--pc-text-muted);
  font-size: 12px;
}

.retrying-tag {
  animation: retryPulse 1.5s ease-in-out infinite;
}

@keyframes retryPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.deps-list,
.subs-list {
  margin: 0;
  padding-left: 16px;
  font-size: 13px;
  color: var(--pc-text-secondary);

  li {
    margin: 4px 0;
  }
}

@media (max-width: 1200px) {
  .plugin-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .plugin-stats {
    grid-template-columns: 1fr;
  }
}
</style>
