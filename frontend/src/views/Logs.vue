<template>
  <div class="logs-page">
    <div class="page-header">
      <div class="header-actions">
        <el-button @click="showClearDialog" :disabled="logs.length === 0">
          <el-icon><Delete /></el-icon>
          {{ $t('common.delete') }}
        </el-button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_calls }}</div>
        <div class="stat-label">{{ $t('dashboard.callCount') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.success_calls }}</div>
        <div class="stat-label">{{ $t('common.success') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.failed_calls }}</div>
        <div class="stat-label">{{ $t('dashboard.failedCount') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(stats.total_tokens) }}</div>
        <div class="stat-label">{{ $t('log.totalTokens') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.avg_duration_ms.toFixed(0) }}ms</div>
        <div class="stat-label">{{ $t('dashboard.avgDuration') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ successRate }}%</div>
        <div class="stat-label">{{ $t('dashboard.successRate') || 'Success Rate' }}</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-section">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="$t('log.model')">
          <el-select v-model="filters.model" :placeholder="$t('common.all')" clearable style="width: 200px" @change="loadLogs">
            <el-option v-for="m in models" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.status')">
          <el-select v-model="filters.is_success" :placeholder="$t('common.all')" clearable style="width: 120px" @change="loadLogs">
            <el-option :label="$t('common.success')" :value="true" />
            <el-option :label="$t('common.failed')" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.time')">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="-"
            :start-placeholder="$t('log.startTime')"
            :end-placeholder="$t('log.endTime')"
            style="width: 260px"
            @change="loadLogs"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">
            <el-icon><Search /></el-icon>
            {{ $t('common.search') }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Log List -->
    <div class="table-scroll">
      <el-table :data="logs" v-loading="loading" stripe :empty-text="$t('common.noData')" class="pc-data-table logs-table">
      <el-table-column type="index" label="ID" width="60">
        <template #default="{ $index }">
          <el-tag type="info" size="small">{{ $index + 1 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="model" :label="$t('log.model')" width="180" show-overflow-tooltip />
      <el-table-column :label="$t('log.tokenUsage')" width="160">
        <template #default="{ row }">
          <span class="token-info">
            <el-tag size="small" type="info">{{ row.input_tokens }}</el-tag>
            <el-icon><ArrowRight /></el-icon>
            <el-tag size="small" type="success">{{ row.output_tokens }}</el-tag>
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="total_tokens" :label="$t('log.totalTokens')" width="120">
        <template #default="{ row }">
          <span class="token-total">{{ formatNumber(row.total_tokens) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="duration_ms" :label="$t('dashboard.avgDuration')" width="100">
        <template #default="{ row }">
          <span>{{ row.duration_ms }}ms</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.status')" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_success ? 'success' : 'danger'" size="small">
            {{ row.is_success ? $t('common.success') : $t('common.failed') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="error_message" :label="$t('common.details')" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
          <span v-else class="no-error">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="$t('log.timestamp')" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.actions')" width="80">
        <template #default="{ row }">
          <el-popconfirm :title="$t('common.confirm')" @confirm="deleteLog(row)">
            <template #reference>
              <el-button size="small" link type="danger">{{ $t('common.delete') }}</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <!-- Pagination -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="loadLogs"
        @current-change="loadLogs"
      />
    </div>

    <!-- Clear Logs Dialog -->
    <el-dialog v-model="clearDialogVisible" :title="$t('common.delete')" width="400px">
      <el-form label-width="80px">
        <el-form-item :label="$t('common.time')">
          <el-radio-group v-model="clearBefore">
            <el-radio :value="7">7 {{ $t('log.days') }}</el-radio>
            <el-radio :value="30">30 {{ $t('log.days') }}</el-radio>
            <el-radio :value="90">90 {{ $t('log.days') }}</el-radio>
            <el-radio :value="0">{{ $t('common.all') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="clearDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="danger" @click="clearLogs" :loading="clearing">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Search, ArrowRight } from '@element-plus/icons-vue'
import { api } from '../api'

interface LogItem {
  id: number
  user_id: number
  model: string
  call_count: number
  input_tokens: number
  output_tokens: number
  total_tokens: number
  duration_ms: number
  is_success: boolean
  error_message: string | null
  created_at: string
}

interface LogStats {
  total_calls: number
  success_calls: number
  failed_calls: number
  total_tokens: number
  avg_duration_ms: number
}

const logs = ref<LogItem[]>([])
const stats = ref<LogStats>({
  total_calls: 0,
  success_calls: 0,
  failed_calls: 0,
  total_tokens: 0,
  avg_duration_ms: 0
})
const models = ref<string[]>([])
const loading = ref(false)
const clearing = ref(false)
const clearDialogVisible = ref(false)
const clearBefore = ref(30)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const filters = reactive({
  model: '',
  is_success: null as boolean | null,
  dateRange: null as [Date, Date] | null
})

const successRate = computed(() => {
  if (stats.value.total_calls === 0) return 100
  return ((stats.value.success_calls / stats.value.total_calls) * 100).toFixed(1)
})

function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

function formatDate(date: string): string {
  return new Date(date).toLocaleString('en-US')
}

async function loadStats() {
  try {
    const res = await api.get('/logs/stats')
    stats.value = res.data
  } catch (error) {
    console.error('Failed to load stats')
  }
}

async function loadModels() {
  try {
    const res = await api.get('/logs/models')
    models.value = res.data
  } catch (error) {
    console.error('Failed to load models')
  }
}

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', String(pagination.page))
    params.append('page_size', String(pagination.pageSize))

    if (filters.model) params.append('model', filters.model)
    if (filters.is_success !== null) params.append('is_success', String(filters.is_success))
    if (filters.dateRange) {
      params.append('start_date', filters.dateRange[0].toISOString())
      params.append('end_date', filters.dateRange[1].toISOString())
    }

    const res = await api.get(`/logs?${params.toString()}`)
    logs.value = res.data
    // 优先使用后端返回的 total，否则根据当前页数据量估算
    pagination.total = res.data.total ?? (
      logs.value.length < pagination.pageSize
        ? (pagination.page - 1) * pagination.pageSize + logs.value.length
        : pagination.page * pagination.pageSize + 1
    )
  } catch (error) {
    ElMessage.error('Failed to load logs')
  } finally {
    loading.value = false
  }
}

async function deleteLog(log: LogItem) {
  try {
    await api.delete(`/logs/${log.id}`)
    ElMessage.success('Log deleted')
    loadLogs()
    loadStats()
  } catch (error) {
    ElMessage.error('Delete failed')
  }
}

function showClearDialog() {
  clearDialogVisible.value = true
}

async function clearLogs() {
  clearing.value = true
  try {
    let beforeDate: Date | null = null
    if (clearBefore.value > 0) {
      beforeDate = new Date()
      beforeDate.setDate(beforeDate.getDate() - clearBefore.value)
    }

    const params = beforeDate ? `?before_date=${beforeDate.toISOString()}` : ''
    const res = await api.delete(`/logs${params}`)
    ElMessage.success(res.data.message)
    clearDialogVisible.value = false
    loadLogs()
    loadStats()
  } catch (error) {
    ElMessage.error('Clear failed')
  } finally {
    clearing.value = false
  }
}

onMounted(() => {
  loadStats()
  loadModels()
  loadLogs()
})
</script>

<style scoped lang="scss">
.logs-page {
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

.logs-page {
  .stats-row {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
    margin-bottom: 20px;

    .stat-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      background: var(--pc-bg-surface);
      border: 1px solid var(--pc-border);
      border-radius: 12px;
      transition: all 0.3s ease;

      &:hover {
        border-color: var(--pc-primary);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
      }

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
        white-space: nowrap;
        line-height: 1.4;
      }
    }
  }

  .filter-section {
    margin-bottom: 20px;
    padding: 16px;
    background: var(--pc-bg-surface);
    border: 1px solid var(--pc-border);
    border-radius: 12px;
  }

  .table-scroll {
    overflow-x: auto;
    width: 100%;
  }

  .logs-table {
    background: transparent;
    border-radius: 12px;
    overflow: hidden;
  }

  .token-info {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .token-total {
    font-weight: 600;
    color: var(--pc-primary);
  }

  .error-text {
    color: var(--pc-accent-red);
  }

  .no-error {
    color: var(--pc-text-muted);
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }

  // Fix table header text wrapping
  :deep(.el-table__header-wrapper) {
    th .cell {
      white-space: nowrap;
    }
  }
}

@media (max-width: 1400px) {
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
