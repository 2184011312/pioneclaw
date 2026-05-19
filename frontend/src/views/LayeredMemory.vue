<template>
  <div class="layered-memory-panel">
    <!-- 统计卡片 -->
    <div class="memory-stats">
      <el-card class="stat-card">
        <div class="stat-icon l0">
          <el-icon><Collection /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.l0_count }}</div>
          <div class="stat-label">L0 {{ $t('memory.l0Desc') }}</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon l1">
          <el-icon><FolderOpened /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.l1_count }}</div>
          <div class="stat-label">L1 {{ $t('memory.l1Desc') }}</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon l2">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.l2_count }}</div>
          <div class="stat-label">L2 {{ $t('memory.l2Desc') }}</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon total">
          <el-icon><Star /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">{{ $t('memory.totalMemories') }}</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon vector">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.vector_count }}</div>
          <div class="stat-label">{{ $t('memory.vectors') }}</div>
        </div>
      </el-card>
    </div>

    <!-- 筛选栏 - Skills 风格 -->
    <div class="filter-bar">
      <div class="layer-filter">
        <button
          class="layer-chip"
          :class="{ active: layerFilter === null }"
          @click="layerFilter = null; loadList()"
        >
          {{ $t('memory.allLayers') }}
        </button>
        <span class="chip-divider"></span>
        <button
          v-for="lv in layerSteps"
          :key="lv.value"
          class="layer-chip"
          :class="[lv.cssClass, { active: layerFilter === lv.value }]"
          @click="layerFilter = lv.value; loadList()"
        >
          <span class="chip-dot"></span>
          {{ lv.label }} · {{ lv.desc }}
        </button>
      </div>

      <el-select v-model="typeFilter" :placeholder="$t('memory.type')" style="width: 120px" @change="loadList" clearable>
        <el-option :label="$t('common.all')" value="" />
        <el-option :label="$t('memory.title')" value="memory" />
        <el-option :label="$t('common.details')" value="resource" />
        <el-option :label="$t('nav.skills')" value="skill" />
      </el-select>

      <el-input
        v-model="keyword"
        :placeholder="$t('memory.search')"
        style="width: 220px"
        clearable
        @clear="loadList"
        @keyup.enter="loadList"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>

      <div style="flex: 1" />

      <button class="pc-glow-btn secondary" @click="recallDialogVisible = true">
        <el-icon><Search /></el-icon> {{ $t('memory.semanticSearch') }}
      </button>
      <button class="pc-glow-btn" @click="storeDialogVisible = true">
        <el-icon><Plus /></el-icon> {{ $t('memory.storeMemory') }}
      </button>
    </div>

    <!-- 记忆表格 - Skills 风格 -->
    <el-card class="table-card">
      <el-table :data="memories" v-loading="loading" stripe style="width: 100%" class="pc-data-table">
        <el-table-column :label="$t('memory.layer')" width="80">
          <template #default="{ row }">
            <el-tag :type="layerTagType(row.layer)" size="small" effect="dark">L{{ row.layer }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('common.name')" min-width="200" show-overflow-tooltip />
        <el-table-column :label="$t('memory.summary')" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-muted">{{ row.overview || row.abstract || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('memory.type')" width="90">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.context_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="importance" :label="$t('memory.importance')" width="80" align="center" />
        <el-table-column prop="access_count" :label="$t('memory.hotness')" width="70" align="center" />
        <el-table-column prop="source" :label="$t('wiki.source')" width="100" show-overflow-tooltip />
        <el-table-column :label="$t('common.time')" width="160">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="240" align="center">
          <template #default="{ row }">
            <div class="pc-action-group">
              <el-button size="small" @click="viewDetail(row)">
                <el-icon><View /></el-icon>
                {{ $t('common.details') }}
              </el-button>
              <el-button v-if="row.layer === 1" size="small" type="warning" @click="promoteMemory(row)">
                <el-icon><Top /></el-icon>
                {{ $t('memory.promote') }}
              </el-button>
              <el-button size="small" type="danger" @click="deleteMemory(row)">
                <el-icon><Delete /></el-icon>
                {{ $t('common.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="pagination-row">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadList"
      />
    </div>

    <!-- 存储对话框 -->
    <el-dialog v-model="storeDialogVisible" :title="$t('memory.storeMemory')" width="600px" destroy-on-close class="cyber-dialog">
      <el-form :model="storeForm" label-width="100px">
        <el-form-item :label="$t('common.name')" required>
          <el-input v-model="storeForm.name" :placeholder="$t('common.name')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')" required>
          <el-input v-model="storeForm.content" type="textarea" :rows="6" :placeholder="$t('common.description')" />
        </el-form-item>
        <el-form-item :label="$t('memory.type')">
          <el-select v-model="storeForm.context_type" style="width: 100%">
            <el-option :label="$t('memory.title')" value="memory" />
            <el-option :label="$t('common.details')" value="resource" />
            <el-option :label="$t('nav.skills')" value="skill" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('memory.importance')">
          <el-rate v-model="storeForm.importance" :max="5" />
        </el-form-item>
        <el-form-item :label="$t('wiki.source')">
          <el-input v-model="storeForm.source" :placeholder="$t('wiki.source')" />
        </el-form-item>
        <el-form-item :label="$t('wiki.tags')">
          <el-select v-model="storeForm.tags" multiple filterable allow-create style="width: 100%" :placeholder="$t('wiki.tags')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="storeDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="storing" @click="storeMemory" class="cyber-btn primary-glow">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 语义检索对话框 -->
    <el-dialog v-model="recallDialogVisible" :title="$t('memory.semanticSearch')" width="700px" destroy-on-close class="cyber-dialog">
      <el-input v-model="recallQuery" :placeholder="$t('memory.search')" @keyup.enter="doRecall">
        <template #append>
          <el-button :loading="recalling" @click="doRecall">{{ $t('common.search') }}</el-button>
        </template>
      </el-input>
      <div v-if="recallResults.length" class="recall-results">
        <div class="recall-hint">
          <el-tag v-if="recallIntent" size="small" type="info">{{ $t('common.type') }}: {{ recallIntent }}</el-tag>
          <span>{{ $t('skill.total') }}: {{ recallTotal }}</span>
        </div>
        <div v-for="r in recallResults" :key="r.uri" class="recall-item" @click="viewRecallDetail(r)">
          <div class="recall-header">
            <el-tag :type="layerTagType(r.layer)" size="small" effect="dark">L{{ r.layer }}</el-tag>
            <span class="recall-name">{{ r.name }}</span>
            <span class="recall-score">{{ (r.score * 100).toFixed(1) }}%</span>
          </div>
          <div class="recall-text">{{ r.text.slice(0, 200) }}{{ r.text.length > 200 ? '...' : '' }}</div>
        </div>
      </div>
      <el-empty v-else-if="recallSearched && !recallResults.length" :description="$t('memory.noMemory')" />
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" :title="detailData?.name || $t('common.details')" size="500px">
      <template v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('memory.uri')">{{ detailData.uri }}</el-descriptions-item>
          <el-descriptions-item :label="$t('memory.layer')">
            <el-tag :type="layerTagType(detailData.layer)" effect="dark">L{{ detailData.layer }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('memory.type')">{{ detailData.context_type }}</el-descriptions-item>
          <el-descriptions-item :label="$t('memory.importance')">{{ detailData.importance }}</el-descriptions-item>
          <el-descriptions-item :label="$t('memory.hotness')">{{ detailData.access_count }}</el-descriptions-item>
          <el-descriptions-item :label="$t('wiki.source')">{{ detailData.source || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-tabs v-model="detailTab" style="margin-top: 16px">
          <el-tab-pane :label="$t('memory.l0Summary')" name="l0">
            <div class="detail-content">{{ detailData.abstract || $t('common.noData') }}</div>
          </el-tab-pane>
          <el-tab-pane :label="$t('memory.l1Overview')" name="l1">
            <div class="detail-content">{{ detailData.overview || $t('common.noData') }}</div>
          </el-tab-pane>
          <el-tab-pane :label="$t('memory.l2Content')" name="l2">
            <div class="detail-content">{{ detailData.content }}</div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Plus, View, Top, Delete,
  Collection, FolderOpened, Document, Star, Connection,
} from '@element-plus/icons-vue'
import { layeredMemoryApi, type LayeredMemoryItem, type LayeredMemoryDetail, type LayeredMemoryStats, type RecallResult } from '@/api/layeredMemory'

const { t: $t } = useI18n()

const props = defineProps<{ stats?: LayeredMemoryStats }>()
const emit = defineEmits<{ updated: [] }>()

// 统计
const stats = ref<LayeredMemoryStats>(props.stats || { total: 0, l0_count: 0, l1_count: 0, l2_count: 0, by_type: {}, by_source: {}, vector_count: 0 })

// 列表
const memories = ref<LayeredMemoryItem[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const layerFilter = ref<number | null>(null)
const typeFilter = ref('')
const keyword = ref('')

const layerSteps = computed(() => [
  { label: 'L0', value: 0, desc: $t('memory.l0Desc'), cssClass: 'l0' },
  { label: 'L1', value: 1, desc: $t('memory.l1Desc'), cssClass: 'l1' },
  { label: 'L2', value: 2, desc: $t('memory.l2Desc'), cssClass: 'l2' },
])

// 存储
const storeDialogVisible = ref(false)
const storing = ref(false)
const storeForm = ref({
  name: '', content: '', context_type: 'memory', importance: 3, source: '', tags: [] as string[],
})

// 检索
const recallDialogVisible = ref(false)
const recallQuery = ref('')
const recalling = ref(false)
const recallResults = ref<RecallResult[]>([])
const recallIntent = ref('')
const recallTotal = ref(0)
const recallSearched = ref(false)

// 详情
const detailVisible = ref(false)
const detailData = ref<LayeredMemoryDetail | null>(null)
const detailTab = ref('l0')

function layerTagType(layer: number) {
  if (layer === 0) return 'danger'
  if (layer === 1) return 'warning'
  return 'success'
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString()
}

async function loadStats() {
  try {
    const { data } = await layeredMemoryApi.stats()
    if (data) stats.value = data
  } catch { /* ignore */ }
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (layerFilter.value !== null) params.layer = layerFilter.value
    if (typeFilter.value) params.context_type = typeFilter.value
    if (keyword.value) params.keyword = keyword.value

    const { data } = await layeredMemoryApi.list(params)
    if (data) {
      memories.value = data.items
      total.value = data.total
    }
  } catch { /* ignore */ }
  loading.value = false
}

async function storeMemory() {
  if (!storeForm.value.name || !storeForm.value.content) {
    ElMessage.warning($t('memory.fillNameAndContent'))
    return
  }
  storing.value = true
  try {
    await layeredMemoryApi.store(storeForm.value)
    ElMessage.success($t('memory.stored'))
    storeDialogVisible.value = false
    storeForm.value = { name: '', content: '', context_type: 'memory', importance: 3, source: '', tags: [] }
    await Promise.all([loadList(), loadStats()])
    emit('updated')
  } catch { /* ignore */ }
  storing.value = false
}

async function doRecall() {
  if (!recallQuery.value) return
  recalling.value = true
  recallSearched.value = false
  try {
    const { data } = await layeredMemoryApi.recall({ query: recallQuery.value, top_k: 10 })
    if (data) {
      recallResults.value = data.results
      recallIntent.value = data.intent || ''
      recallTotal.value = data.total
    }
  } catch { /* ignore */ }
  recallSearched.value = true
  recalling.value = false
}

async function viewDetail(row: LayeredMemoryItem) {
  try {
    const { data } = await layeredMemoryApi.get(row.uri)
    if (data) {
      detailData.value = data
      detailTab.value = 'l0'
      detailVisible.value = true
    }
  } catch { /* ignore */ }
}

async function viewRecallDetail(r: RecallResult) {
  try {
    const l2Uri = r.uri.replace('/.level_0', '').replace('/.level_1', '')
    const { data } = await layeredMemoryApi.get(l2Uri)
    if (data) {
      detailData.value = data
      detailTab.value = 'l0'
      detailVisible.value = true
    }
  } catch { /* ignore */ }
}

async function promoteMemory(row: LayeredMemoryItem) {
  try {
    await ElMessageBox.confirm($t('memory.confirmPromote'), $t('memory.promoteConfirm'))
    await layeredMemoryApi.promote(row.uri)
    ElMessage.success($t('memory.promoted'))
    await Promise.all([loadList(), loadStats()])
    emit('updated')
  } catch { /* ignore */ }
}

async function deleteMemory(row: LayeredMemoryItem) {
  try {
    await ElMessageBox.confirm($t('memory.confirmDeleteAll'), $t('memory.deleteConfirm'), { type: 'warning' })
    const l2Uri = row.uri.replace('/.level_0', '').replace('/.level_1', '')
    await layeredMemoryApi.delete(l2Uri)
    ElMessage.success($t('memory.deleted'))
    await Promise.all([loadList(), loadStats()])
    emit('updated')
  } catch { /* ignore */ }
}

onMounted(() => {
  if (!props.stats) loadStats()
  loadList()
})
</script>

<style scoped>
.layered-memory-panel {
  padding: 0;
}

/* Stats */
.memory-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  border: 1px solid var(--pc-glass-border);
  background: var(--pc-glass-bg);
  backdrop-filter: var(--pc-glass-blur);
  border-radius: var(--pc-radius-lg);
  transition: all 0.25s ease;
}

.stat-card:hover {
  border-color: rgba(var(--pc-primary-rgb), 0.3);
  box-shadow: 0 0 20px rgba(var(--pc-primary-rgb), 0.1);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px;
  background: transparent;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  flex-shrink: 0;
}

.stat-icon.l0 { background: var(--pc-accent-red); box-shadow: 0 0 14px rgba(var(--pc-accent-red-rgb), 0.3); }
.stat-icon.l1 { background: var(--pc-accent-orange); box-shadow: 0 0 14px rgba(var(--pc-accent-orange-rgb), 0.3); }
.stat-icon.l2 { background: var(--pc-accent-green); box-shadow: 0 0 14px rgba(var(--pc-accent-green-rgb), 0.3); }
.stat-icon.total { background: var(--pc-primary); box-shadow: 0 0 14px rgba(var(--pc-primary-rgb), 0.35); }
.stat-icon.vector { background: var(--pc-accent-purple); box-shadow: 0 0 14px rgba(var(--pc-accent-purple-rgb), 0.3); }

.stat-info {
  min-width: 0;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--pc-text-primary);
  letter-spacing: 0.5px;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--pc-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
  white-space: nowrap;
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.layer-filter {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  padding: 4px;
}

.layer-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--pc-radius-md);
  border: 1px solid transparent;
  background: transparent;
  color: var(--pc-text-muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  font-family: inherit;
}

.layer-chip:hover {
  color: var(--pc-text-primary);
  background: rgba(var(--pc-primary-rgb), 0.05);
}

.layer-chip.active {
  background: rgba(var(--pc-primary-rgb), 0.12);
  color: var(--pc-primary);
  font-weight: 600;
  border-color: rgba(var(--pc-primary-rgb), 0.2);
}

.chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.layer-chip.l0 .chip-dot { background: var(--pc-accent-red, #ff4d4f); }
.layer-chip.l1 .chip-dot { background: var(--pc-accent-orange, #faad14); }
.layer-chip.l2 .chip-dot { background: var(--pc-accent-green, #52c41a); }

.layer-chip.l0.active { color: var(--pc-accent-red, #ff4d4f); border-color: rgba(var(--pc-accent-red-rgb, 255, 77, 79), 0.25); background: rgba(var(--pc-accent-red-rgb, 255, 77, 79), 0.08); }
.layer-chip.l1.active { color: var(--pc-accent-orange, #faad14); border-color: rgba(var(--pc-accent-orange-rgb, 250, 173, 20), 0.25); background: rgba(var(--pc-accent-orange-rgb, 250, 173, 20), 0.08); }
.layer-chip.l2.active { color: var(--pc-accent-green, #52c41a); border-color: rgba(var(--pc-accent-green-rgb, 82, 196, 26), 0.25); background: rgba(var(--pc-accent-green-rgb, 82, 196, 26), 0.08); }

.chip-divider {
  width: 1px;
  height: 20px;
  background: var(--pc-glass-border);
  margin: 0 4px;
}

/* Table */
.table-card {
  background: var(--pc-glass-bg) !important;
  border: 1px solid var(--pc-glass-border) !important;
  border-radius: var(--pc-radius-lg) !important;
  backdrop-filter: var(--pc-glass-blur);
}

.table-card :deep(.el-card__body) {
  background: transparent;
}

.text-muted {
  color: var(--pc-text-secondary);
  font-size: 13px;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* Recall */
.recall-results {
  margin-top: 16px;
}

.recall-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--pc-text-secondary);
}

.recall-item {
  padding: 12px;
  border: 1px solid var(--pc-border);
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.recall-item:hover {
  border-color: var(--pc-primary);
}

.recall-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.recall-name {
  font-weight: 600;
}

.recall-score {
  margin-left: auto;
  font-size: 13px;
  color: var(--pc-accent-green, #52c41a);
  font-weight: 600;
}

.recall-text {
  font-size: 13px;
  color: var(--pc-text-primary);
  line-height: 1.5;
}

.detail-content {
  padding: 12px;
  background: rgba(var(--pc-primary-rgb), 0.04);
  border-radius: 6px;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 1100px) {
  .memory-stats {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 700px) {
  .memory-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
