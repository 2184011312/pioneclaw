<template>
  <div class="memory-view">
    <!-- Stats Cards -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-statistic title="记忆总数" :value="stats.total_files" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="索引条目" :value="stats.index_entries" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="用户偏好" :value="stats.by_type?.user ?? 0" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="项目知识" :value="stats.by_type?.project ?? 0" />
      </el-col>
    </el-row>

    <!-- Toolbar -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索记忆..."
        style="width: 300px"
        clearable
        @keyup.enter="doSearch"
        @clear="loadMemories"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterType" placeholder="类型过滤" clearable style="width: 140px" @change="loadMemories">
        <el-option label="用户偏好" value="user" />
        <el-option label="用户反馈" value="feedback" />
        <el-option label="项目知识" value="project" />
        <el-option label="参考资料" value="reference" />
      </el-select>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建记忆
      </el-button>
    </div>

    <!-- Table -->
    <el-table :data="memories" v-loading="loading" stripe style="margin-top: 16px">
      <el-table-column prop="name" label="名称" min-width="200" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="typeColor(row.type)" size="small">{{ typeLabel(row.type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
      <el-table-column prop="freshness" label="新鲜度" width="90" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.is_stale" type="warning" size="small">已过期</el-tag>
          <el-tag v-else type="success" size="small">活跃</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="viewDetail(row)">查看</el-button>
          <el-button link type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadMemories"
      />
    </div>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetail" title="记忆详情" width="700px">
      <template v-if="currentEntry">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentEntry.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="typeColor(currentEntry.type)" size="small">{{ typeLabel(currentEntry.type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件名">{{ currentEntry.filename }}</el-descriptions-item>
          <el-descriptions-item label="新鲜度">{{ currentEntry.freshness }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentEntry.updated_at }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ currentEntry.tags?.join(', ') || '—' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentEntry.description }}</el-descriptions-item>
        </el-descriptions>
        <div class="content-section">
          <h4>内容</h4>
          <div class="markdown-body" v-html="renderedContent" />
        </div>
      </template>
    </el-dialog>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建记忆" width="600px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="类型" required>
          <el-select v-model="createForm.type" style="width: 100%">
            <el-option label="用户偏好" value="user" />
            <el-option label="用户反馈" value="feedback" />
            <el-option label="项目知识" value="project" />
            <el-option label="参考资料" value="reference" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="createForm.name" placeholder="可选，留空则自动生成" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" placeholder="可选，留空则自动生成" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="8"
            placeholder="Markdown 格式的记忆内容"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="createForm.tags"
            multiple
            filterable
            allow-create
            style="width: 100%"
            placeholder="输入后回车添加标签"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="doCreate" :loading="creating">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { memoryApi, type MemoryEntry, type MemoryStats } from '@/api/memory'

// --- State ---
const loading = ref(false)
const creating = ref(false)
const memories = ref<MemoryEntry[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const filterType = ref('')
const showDetail = ref(false)
const showCreateDialog = ref(false)
const currentEntry = ref<MemoryEntry | null>(null)

const stats = ref<MemoryStats>({ total_files: 0, index_entries: 0, by_type: {} })

const createForm = ref({
  type: 'user',
  name: '',
  description: '',
  content: '',
  tags: [] as string[],
})

// --- Render ---
const renderedContent = computed(() => {
  if (!currentEntry.value?.content) return ''
  // Simple markdown rendering
  return currentEntry.value.content
    .replace(/\n/g, '<br>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
})

// --- Labels ---
function typeLabel(type: string) {
  const map: Record<string, string> = {
    user: '用户偏好',
    feedback: '用户反馈',
    project: '项目知识',
    reference: '参考资料',
  }
  return map[type] ?? type
}

function typeColor(type: string) {
  const map: Record<string, string> = {
    user: 'primary',
    feedback: 'warning',
    project: 'success',
    reference: 'info',
  }
  return map[type] ?? ''
}

// --- Actions ---
async function loadStats() {
  try {
    const { data } = await memoryApi.stats()
    if (data) stats.value = data
  } catch { /* ignore */ }
}

async function loadMemories() {
  loading.value = true
  try {
    if (searchKeyword.value) {
      const { data } = await memoryApi.search(searchKeyword.value, filterType.value || undefined, pageSize.value)
      memories.value = data.entries ?? []
      total.value = data.total ?? 0
    } else {
      const { data } = await memoryApi.list({
        type: filterType.value || undefined,
        sort_by: 'updatedAt',
        order: 'desc',
        limit: pageSize.value,
        offset: (page.value - 1) * pageSize.value,
      })
      memories.value = data.entries ?? []
      total.value = data.total ?? 0
    }
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function doSearch() {
  page.value = 1
  loadMemories()
}

function viewDetail(entry: MemoryEntry) {
  currentEntry.value = entry
  showDetail.value = true
}

async function confirmDelete(entry: MemoryEntry) {
  try {
    await ElMessageBox.confirm(`确定删除记忆「${entry.name}」吗？`, '确认删除', { type: 'warning' })
    await memoryApi.delete(entry.filename)
    ElMessage.success('已删除')
    await loadMemories()
    await loadStats()
  } catch { /* cancelled */ }
}

async function doCreate() {
  if (!createForm.value.content.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  creating.value = true
  try {
    await memoryApi.create({
      type: createForm.value.type,
      name: createForm.value.name || undefined,
      description: createForm.value.description || undefined,
      content: createForm.value.content,
      tags: createForm.value.tags.length > 0 ? createForm.value.tags : undefined,
    })
    ElMessage.success('记忆已创建')
    showCreateDialog.value = false
    createForm.value = { type: 'user', name: '', description: '', content: '', tags: [] }
    await loadMemories()
    await loadStats()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? '创建失败')
  }
  finally { creating.value = false }
}

onMounted(() => {
  loadStats()
  loadMemories()
})
</script>

<style scoped>
.stats-row {
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.content-section {
  margin-top: 16px;
}

.content-section h4 {
  margin-bottom: 8px;
}

.markdown-body {
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.6;
}

.markdown-body :deep(code) {
  background: var(--el-color-primary-light-9);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}
</style>
