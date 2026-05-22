<template>
  <div class="monitor-page">
    <!-- 模型使用总览 -->
    <div class="section-header">
      <span class="section-title">{{ $t('monitor.modelUsage') }}</span>
      <span class="section-sub">{{ $t('monitor.last24h') }}</span>
    </div>
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ modelUsage.total_calls }}</div>
        <div class="stat-label">{{ $t('monitor.totalCalls') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(modelUsage.total_tokens) }}</div>
        <div class="stat-label">{{ $t('monitor.totalTokens') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ modelUsage.avg_duration_ms }}ms</div>
        <div class="stat-label">{{ $t('monitor.avgDuration') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value fail">{{ modelUsage.failed_calls }}</div>
        <div class="stat-label">{{ $t('monitor.failed') }}</div>
      </div>
    </div>

    <!-- 模型使用明细表 -->
    <div class="pc-glass-card">
      <div class="card-gradient-line"></div>
      <div class="table-scroll">
        <el-table :data="modelUsage.models" v-loading="modelLoading" class="pc-data-table">
          <template #empty><el-empty :description="$t('monitor.noModelUsageData')" /></template>
          <el-table-column :label="$t('monitor.model')" min-width="200">
            <template #default="{ row }">
              <code class="model-name">{{ row.model }}</code>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.calls')" prop="calls" width="110" sortable />
          <el-table-column :label="$t('monitor.tokenUsage')" prop="tokens" width="130" sortable>
            <template #default="{ row }">
              {{ formatNumber(row.tokens) }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.avgDuration')" prop="avg_duration_ms" width="110" sortable>
            <template #default="{ row }">
              {{ row.avg_duration_ms }}ms
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.successRate')" prop="success_rate" width="100" sortable>
            <template #default="{ row }">
              <span :class="row.success_rate >= 95 ? 'rate-ok' : 'rate-warn'">{{ row.success_rate }}%</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.failed')" prop="failures" width="80" sortable>
            <template #default="{ row }">
              <span v-if="row.failures > 0" class="fail-count">{{ row.failures }}</span>
              <span v-else class="no-fail">0</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- Runner 状态 -->
    <div class="section-header" style="margin-top: 28px">
      <span class="section-title">{{ $t('monitor.runnerStatus') }}</span>
      <el-button size="small" @click="fetchRunners" :loading="loading" text>
        <el-icon><Refresh /></el-icon>
        {{ $t('common.refresh') }}
      </el-button>
    </div>
    <div class="pc-glass-card">
      <div class="card-gradient-line"></div>
      <div class="table-scroll">
        <el-table :data="runners" v-loading="loading" class="pc-data-table">
          <template #empty><el-empty :description="$t('monitor.noRunners')" /></template>
          <el-table-column :label="$t('monitor.name')" width="200">
            <template #default="{ row }">
              <div class="runner-cell">
                <span class="runner-name">{{ row.display_name || row.name }}</span>
                <span v-if="row.version" class="runner-version">v{{ row.version }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.status')" width="90">
            <template #default="{ row }">
              <span :class="['status-dot', getStatusClass(row.status)]"></span>
              <span class="status-text">{{ getStatusLabel(row.status) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.host')" width="180">
            <template #default="{ row }">
              <code v-if="row.host" class="host-code">{{ row.host }}:{{ row.port }}</code>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.platform')" width="100">
            <template #default="{ row }">
              <span v-if="row.platform" class="platform-tag">{{ row.platform }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.success')" width="70" sortable prop="success_tasks">
            <template #default="{ row }">
              <span class="count-ok">{{ row.success_tasks || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.failed')" width="70" sortable prop="failed_tasks">
            <template #default="{ row }">
              <span :class="(row.failed_tasks || 0) > 0 ? 'count-fail' : 'count-zero'">{{ row.failed_tasks || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.total')" width="70" sortable prop="total_tasks">
            <template #default="{ row }">
              {{ row.total_tasks || 0 }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.heartbeat')" width="130">
            <template #default="{ row }">
              <span v-if="row.last_heartbeat" :class="isRecent(row.last_heartbeat) ? 'hb-ok' : 'hb-stale'">
                {{ formatRelative(row.last_heartbeat) }}
              </span>
              <span v-else class="hb-stale">{{ $t('monitor.none') }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('monitor.currentTask')" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.current_task" class="current-task">{{ row.current_task }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/api'
import { Refresh } from '@element-plus/icons-vue'

const { t } = useI18n()

interface ModelItem {
  model: string
  calls: number
  tokens: number
  avg_duration_ms: number
  failures: number
  success_rate: number
}

interface ModelUsage {
  total_calls: number
  total_tokens: number
  avg_duration_ms: number
  failed_calls: number
  models: ModelItem[]
}

interface Runner {
  id: number
  name: string
  display_name: string | null
  status: string
  host: string | null
  port: number | null
  version: string | null
  platform: string | null
  last_heartbeat: string | null
  current_task: string | null
  total_tasks: number
  success_tasks: number
  failed_tasks: number
}

const loading = ref(false)
const modelLoading = ref(false)
const runners = ref<Runner[]>([])

const modelUsage = ref<ModelUsage>({
  total_calls: 0,
  total_tokens: 0,
  avg_duration_ms: 0,
  failed_calls: 0,
  models: [],
})

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 1000).toFixed(1) + 'K'
  return n.toLocaleString()
}

function getStatusClass(status: string): string {
  const map: Record<string, string> = {
    running: 'dot-running', active: 'dot-running',
    idle: 'dot-idle', inactive: 'dot-idle',
    offline: 'dot-offline', disabled: 'dot-offline',
    pending: 'dot-pending',
  }
  return map[status] || 'dot-idle'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    running: t('monitor.statusRunning'), active: t('monitor.statusRunning'),
    idle: t('monitor.statusIdle'), inactive: t('monitor.statusIdle'),
    offline: t('monitor.statusOffline'), disabled: t('monitor.statusOffline'),
    pending: t('monitor.statusPending'),
  }
  return map[status] || status
}

function formatRelative(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 5) return t('monitor.justNow')
  if (sec < 60) return t('monitor.secondsAgo', { n: sec })
  const min = Math.floor(sec / 60)
  if (min < 60) return t('monitor.minutesAgo', { n: min })
  const hour = Math.floor(min / 60)
  if (hour < 24) return t('monitor.hoursAgo', { n: hour })
  return t('monitor.daysAgo', { n: Math.floor(hour / 24) })
}

function isRecent(dateStr: string | null): boolean {
  if (!dateStr) return false
  return Date.now() - new Date(dateStr).getTime() < 60000
}

async function fetchModelUsage() {
  modelLoading.value = true
  try {
    const res = await api.get('/runners/model-usage')
    modelUsage.value = res.data
  } catch (e) {
    console.error('Failed to fetch model usage', e)
  } finally {
    modelLoading.value = false
  }
}

async function fetchRunners() {
  loading.value = true
  try {
    const res = await api.get('/runners')
    runners.value = res.data
  } catch (e) {
    console.error('Failed to fetch runners', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchModelUsage()
  fetchRunners()
})
</script>

<style scoped lang="scss">
.monitor-page {
  padding: 20px;

  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--pc-text-primary);
    }

    .section-sub {
      font-size: 12px;
      color: var(--pc-text-muted);
    }
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;

    .stat-card {
      padding: 20px;
      background: var(--pc-glass-bg);
      border: 1px solid var(--pc-glass-border);
      border-radius: var(--pc-radius-lg);
      text-align: center;

      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--pc-text-primary);
        line-height: 1.2;

        &.fail { color: var(--pc-accent-red); }
      }

      .stat-label {
        font-size: 12px;
        color: var(--pc-text-muted);
        margin-top: 4px;
      }
    }
  }
}

.pc-glass-card {
  position: relative;
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  overflow: hidden;

  .card-gradient-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--pc-gradient-primary);
    z-index: 1;
  }
}

.table-scroll {
  overflow-x: auto;
  width: 100%;
}

.pc-data-table {
  :deep(.el-table__header th) {
    background: transparent;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--pc-text-muted);
  }

  :deep(.el-table__body td) {
    border-color: var(--pc-glass-border);
  }

  :deep(.el-table__row:hover > td) {
    background: rgba(var(--pc-primary-rgb), 0.04);
  }
}

.model-name {
  color: var(--pc-primary);
  background: rgba(var(--pc-primary-rgb), 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}

.rate-ok { color: var(--pc-accent-green); font-weight: 600; }
.rate-warn { color: var(--pc-accent-orange); font-weight: 600; }
.fail-count { color: var(--pc-accent-red); font-weight: 600; }
.no-fail { color: var(--pc-text-muted); }

.runner-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .runner-name {
    font-weight: 600;
    color: var(--pc-text-primary);
    font-size: 13px;
  }

  .runner-version {
    font-size: 10px;
    color: var(--pc-text-muted);
    background: rgba(255,255,255,0.06);
    padding: 2px 6px;
    border-radius: 8px;
  }
}

.status-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 6px;

  &.dot-running { background: var(--pc-accent-green); box-shadow: 0 0 6px rgba(var(--pc-accent-green-rgb), 0.6); }
  &.dot-idle { background: var(--pc-text-muted); }
  &.dot-offline { background: var(--pc-accent-red); }
  &.dot-pending { background: var(--pc-accent-orange); }
}

.status-text {
  font-size: 12px;
  color: var(--pc-text-secondary);
}

.host-code {
  color: var(--pc-primary);
  background: rgba(var(--pc-primary-rgb), 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}

.platform-tag {
  font-size: 11px;
  color: var(--pc-text-muted);
  background: rgba(255,255,255,0.04);
  padding: 2px 8px;
  border-radius: 8px;
}

.count-ok { color: var(--pc-accent-green); font-weight: 600; }
.count-fail { color: var(--pc-accent-red); font-weight: 600; }
.count-zero { color: var(--pc-text-muted); }

.hb-ok { color: var(--pc-accent-green); font-size: 12px; }
.hb-stale { color: var(--pc-accent-orange); font-size: 12px; }

.current-task {
  font-size: 12px;
  color: var(--pc-text-secondary);
}

.text-muted { color: var(--pc-text-muted); font-size: 12px; }

@media (max-width: 900px) {
  .monitor-page .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .monitor-page .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
