<template>
  <div class="security-gateway">
    <el-page-header title="安全网关" @back="$router.back()">
      <template #content>
        <span class="text-large font-600 mr-3">安全网关管理</span>
      </template>
    </el-page-header>

    <el-tabs v-model="activeTab" class="mt-4">
      <!-- 检测测试 -->
      <el-tab-pane label="检测测试" name="test">
        <el-card>
          <template #header>
            <span>输入内容安全检测</span>
          </template>
          <el-input
            v-model="testText"
            type="textarea"
            :rows="6"
            placeholder="输入要检测的文本，例如：身份证号 51012319900101001X，手机号 13800138000"
          />
          <el-button type="primary" class="mt-3" @click="runTest" :loading="testing">
            检测
          </el-button>

          <div v-if="testResult" class="mt-4">
            <el-alert
              :title="`检测结果: ${actionLabel(testResult.action)}`"
              :type="alertType(testResult.action)"
              :description="testResult.reason"
              show-icon
              :closable="false"
            />
            <div v-if="testResult.matched_rules?.length" class="mt-3">
              <el-text type="info">匹配规则:</el-text>
              <el-tag
                v-for="(rule, idx) in testResult.matched_rules"
                :key="idx"
                :type="tagType(rule.severity)"
                class="ml-2 mt-2"
              >
                {{ rule.type }}: {{ rule.match || rule.word }} (severity={{ rule.severity }})
              </el-tag>
            </div>
            <div v-if="testResult.content" class="mt-3">
              <el-text type="info">脱敏结果:</el-text>
              <el-input v-model="testResult.content" type="textarea" :rows="3" readonly class="mt-2" />
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 词库管理 -->
      <el-tab-pane label="词库管理" name="words">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>词库管理</span>
              <div>
                <el-button type="primary" @click="showCreateDialog = true">
                  <el-icon><Plus /></el-icon> 新增
                </el-button>
                <el-button @click="loadWords">
                  <el-icon><Refresh /></el-icon> 刷新
                </el-button>
              </div>
            </div>
          </template>

          <el-table :data="wordList" v-loading="wordLoading" stripe>
            <el-table-column prop="word" label="词汇" width="200" />
            <el-table-column prop="word_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="wordTypeTag(row.word_type)">{{ wordTypeLabel(row.word_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column prop="severity" label="严重度" width="100">
              <template #default="{ row }">
                <el-tag :type="severityTag(row.severity)">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteWord(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="wordPage"
            v-model:page-size="wordPageSize"
            :total="wordTotal"
            layout="total, prev, pager, next"
            class="mt-4"
            @change="loadWords"
          />
        </el-card>
      </el-tab-pane>

      <!-- 审计日志 -->
      <el-tab-pane label="审计日志" name="audit">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>安全审计日志</span>
              <el-button @click="loadAuditLogs">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </template>

          <div class="filter-bar mb-4">
            <el-select v-model="auditFilter.risk_level" placeholder="风险级别" clearable class="mr-2">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="严重" value="critical" />
            </el-select>
            <el-select v-model="auditFilter.check_point" placeholder="检查点" clearable class="mr-2">
              <el-option label="输入过滤" value="filter_input" />
              <el-option label="输出过滤" value="filter_output" />
              <el-option label="工具检查" value="check_tool" />
            </el-select>
            <el-button type="primary" @click="loadAuditLogs">查询</el-button>
          </div>

          <el-table :data="auditList" v-loading="auditLoading" stripe>
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="check_point" label="检查点" width="120">
              <template #default="{ row }">
                {{ checkpointLabel(row.check_point) }}
              </template>
            </el-table-column>
            <el-table-column prop="action" label="操作" width="100">
              <template #default="{ row }">
                <el-tag :type="actionTag(row.action)">{{ actionLabel(row.action) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="risk_level" label="风险" width="100">
              <template #default="{ row }">
                <el-tag :type="riskTag(row.risk_level)">{{ row.risk_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content_preview" label="内容预览" show-overflow-tooltip />
            <el-table-column prop="reason" label="原因" show-overflow-tooltip />
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="session_id" label="会话" width="120" show-overflow-tooltip />
          </el-table>

          <el-pagination
            v-model:current-page="auditPage"
            v-model:page-size="auditPageSize"
            :total="auditTotal"
            layout="total, prev, pager, next"
            class="mt-4"
            @change="loadAuditLogs"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建/编辑词对话框 -->
    <el-dialog v-model="showCreateDialog" :title="isEditing ? '编辑词汇' : '新增词汇'" width="500px">
      <el-form :model="wordForm" label-width="80px">
        <el-form-item label="词汇" required>
          <el-input v-model="wordForm.word" placeholder="输入敏感词/风控词/放通词" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="wordForm.word_type" placeholder="选择类型">
            <el-option label="敏感词" value="sensitive" />
            <el-option label="风险词" value="risk" />
            <el-option label="放通词" value="allow" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="wordForm.category" placeholder="例如：个人信息/警务/系统" />
        </el-form-item>
        <el-form-item label="严重度">
          <el-slider v-model="wordForm.severity" :min="1" :max="5" show-stops />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="wordForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitWord">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { securityGatewayApi, type FilterResult, type WordItem, type AuditLogItem } from '@/api/security_gateway'

const activeTab = ref('test')

// 检测测试
const testText = ref('')
const testing = ref(false)
const testResult = ref<FilterResult | null>(null)

const runTest = async () => {
  if (!testText.value.trim()) {
    ElMessage.warning('请输入要检测的文本')
    return
  }
  testing.value = true
  try {
    const { data } = await securityGatewayApi.testFilter(testText.value)
    testResult.value = data
  } catch (e: any) {
    ElMessage.error('检测失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    testing.value = false
  }
}

// 词库管理
const wordList = ref<WordItem[]>([])
const wordTotal = ref(0)
const wordPage = ref(1)
const wordPageSize = ref(20)
const wordLoading = ref(false)
const showCreateDialog = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const wordForm = reactive<Partial<WordItem>>({
  word: '',
  word_type: 'sensitive',
  category: '',
  severity: 3,
  description: '',
  is_active: true,
})

const resetForm = () => {
  isEditing.value = false
  editingId.value = null
  wordForm.word = ''
  wordForm.word_type = 'sensitive'
  wordForm.category = ''
  wordForm.severity = 3
  wordForm.description = ''
  wordForm.is_active = true
}

const loadWords = async () => {
  wordLoading.value = true
  try {
    const { data } = await securityGatewayApi.listWords({
      skip: (wordPage.value - 1) * wordPageSize.value,
      limit: wordPageSize.value,
    })
    wordList.value = data.items || []
    wordTotal.value = data.total || 0
  } catch (e: any) {
    ElMessage.error('加载词库失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    wordLoading.value = false
  }
}

const openCreateDialog = () => {
  resetForm()
  showCreateDialog.value = true
}

const openEditDialog = (row: WordItem) => {
  isEditing.value = true
  editingId.value = row.id
  wordForm.word = row.word
  wordForm.word_type = row.word_type
  wordForm.category = row.category || ''
  wordForm.severity = row.severity
  wordForm.description = row.description || ''
  wordForm.is_active = row.is_active
  showCreateDialog.value = true
}

const submitWord = async () => {
  if (!wordForm.word || !wordForm.word_type) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    if (isEditing.value && editingId.value !== null) {
      await securityGatewayApi.updateWord(editingId.value, wordForm)
      ElMessage.success('更新成功')
    } else {
      await securityGatewayApi.createWord(wordForm)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetForm()
    loadWords()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
}

const deleteWord = async (id: number) => {
  try {
    await ElMessageBox.confirm('确认删除该词汇?', '提示', { type: 'warning' })
    await securityGatewayApi.deleteWord(id)
    ElMessage.success('删除成功')
    loadWords()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

// 审计日志
const auditList = ref<AuditLogItem[]>([])
const auditTotal = ref(0)
const auditPage = ref(1)
const auditPageSize = ref(20)
const auditLoading = ref(false)
const auditFilter = reactive({
  risk_level: '',
  check_point: '',
})

const loadAuditLogs = async () => {
  auditLoading.value = true
  try {
    const { data } = await securityGatewayApi.listAuditLogs({
      risk_level: auditFilter.risk_level || undefined,
      check_point: auditFilter.check_point || undefined,
      skip: (auditPage.value - 1) * auditPageSize.value,
      limit: auditPageSize.value,
    })
    auditList.value = data.items || []
    auditTotal.value = data.total || 0
  } catch (e: any) {
    ElMessage.error('加载审计日志失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    auditLoading.value = false
  }
}

// 辅助函数
const actionLabel = (action: string) => {
  const map: Record<string, string> = {
    allow: '放行',
    block: '拦截',
    sanitize: '脱敏',
    approve: '审批',
  }
  return map[action] || action
}

const actionTag = (action: string) => {
  const map: Record<string, any> = {
    allow: 'success',
    block: 'danger',
    sanitize: 'warning',
    approve: 'info',
  }
  return map[action] || 'info'
}

const alertType = (action: string) => {
  const map: Record<string, any> = {
    allow: 'success',
    block: 'error',
    sanitize: 'warning',
    approve: 'info',
  }
  return map[action] || 'info'
}

const riskTag = (level: string) => {
  const map: Record<string, any> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    critical: 'danger',
  }
  return map[level] || 'info'
}

const tagType = (severity: number) => {
  if (severity >= 4) return 'danger'
  if (severity >= 3) return 'warning'
  return 'info'
}

const wordTypeTag = (type: string) => {
  const map: Record<string, any> = {
    sensitive: 'danger',
    risk: 'warning',
    allow: 'success',
  }
  return map[type] || 'info'
}

const wordTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    sensitive: '敏感词',
    risk: '风险词',
    allow: '放通词',
  }
  return map[type] || type
}

const severityTag = (severity: number) => {
  if (severity >= 4) return 'danger'
  if (severity >= 3) return 'warning'
  return 'info'
}

const checkpointLabel = (cp: string) => {
  const map: Record<string, string> = {
    filter_input: '输入过滤',
    filter_output: '输出过滤',
    check_tool: '工具检查',
  }
  return map[cp] || cp
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadWords()
  loadAuditLogs()
})
</script>

<style scoped>
.security-gateway {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  align-items: center;
}

.mt-3 {
  margin-top: 12px;
}

.mt-4 {
  margin-top: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.ml-2 {
  margin-left: 8px;
}
</style>
