<template>
  <div class="ai-configs-page">
    <div class="page-header">
      <el-button v-if="userStore.isAdmin" type="primary" class="btn-create" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        {{ $t('aiConfig.create') }}
      </el-button>
    </div>

    <div class="glass-card">
      <el-table :data="configs" v-loading="loading" style="width: 100%" class="cyber-table" :empty-text="$t('common.noData')" table-layout="auto">
        <el-table-column prop="id" label="ID" width="60" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">#{{ row.id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="display_name" :label="$t('aiConfig.model')" min-width="120" show-overflow-tooltip />
        <el-table-column prop="provider" :label="$t('aiConfig.provider')" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" class="tag-provider">{{ row.provider }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" :label="$t('aiConfig.modelId')" min-width="140" show-overflow-tooltip />
        <el-table-column :label="$t('aiConfig.apiKey')" min-width="160">
          <template #default="{ row }">
            <div class="api-key-cell">
              <span class="api-key-mask">{{ visibleApiKeys[row.id] ? (realApiKeys[row.id] || row.api_key) : maskApiKey(row.api_key) }}</span>
              <el-button
                link
                size="small"
                class="visibility-toggle"
                @click="toggleApiKeyVisibility(row.id)"
              >
                <el-icon v-if="visibleApiKeys[row.id]"><Hide /></el-icon>
                <el-icon v-else><View /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" :label="$t('aiConfig.baseUrl')" min-width="160" show-overflow-tooltip />
        <el-table-column prop="temperature" :label="$t('aiConfig.temp')" width="70" align="center" />
        <el-table-column :label="$t('common.status')" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" size="small" class="tag-default">{{ $t('common.default') }}</el-tag>
            <el-tag v-else-if="row.is_active" size="small" class="tag-active">{{ $t('common.active') }}</el-tag>
            <el-tag v-else size="small" class="tag-disabled">{{ $t('common.inactive') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="userStore.isAdmin" :label="$t('common.actions')" width="140" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-tooltip v-if="!row.is_default" :content="$t('common.enable')" placement="top">
                <el-button size="small" circle class="icon-btn btn-set-default" @click="setDefault(row)">
                  <el-icon><Check /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('aiConfig.test')" placement="top">
                <el-button size="small" circle class="icon-btn btn-test" @click="testConfig(row)" :loading="row.testing">
                  <el-icon><Connection /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('common.edit')" placement="top">
                <el-button size="small" circle class="icon-btn btn-edit" @click="showEditDialog(row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('common.delete')" placement="top">
                <el-button size="small" circle class="icon-btn btn-delete" @click="deleteConfig(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? $t('common.edit') : $t('aiConfig.create')"
      width="600px"
      class="cyber-dialog"
    >
      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item :label="$t('aiConfig.configName')" prop="name">
          <el-input v-model="form.name" placeholder="e.g. gpt-4o-prod" />
        </el-form-item>
        <el-form-item :label="$t('aiConfig.displayName')" prop="display_name">
          <el-input v-model="form.display_name" :placeholder="$t('aiConfig.leaveEmptyUseName')" />
          <div class="form-tip">{{ $t('aiConfig.displayNameTip') }}</div>
        </el-form-item>
        <el-form-item :label="$t('aiConfig.provider')" prop="provider">
          <el-select v-model="form.provider" style="width: 100%">
            <el-option :label="$t('aiConfig.openai')" value="openai" />
            <el-option :label="$t('aiConfig.anthropic')" value="anthropic" />
            <el-option :label="$t('aiConfig.azureOpenai')" value="azure" />
            <el-option :label="$t('aiConfig.customOpenai')" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型等级" prop="tier">
          <el-select v-model="form.tier" style="width: 100%">
            <el-option label="Opus - 最强推理" value="opus" />
            <el-option label="Sonnet - 均衡 (推荐)" value="sonnet" />
            <el-option label="Haiku - 快速响应" value="haiku" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('aiConfig.modelId')" prop="model_name">
          <el-input v-model="form.model_name" placeholder="e.g. gpt-4o, claude-3-opus-20240229" />
        </el-form-item>
        <el-form-item :label="$t('aiConfig.baseUrl')" prop="base_url">
          <el-input v-model="form.base_url" :placeholder="$t('aiConfig.apiSecretKey')" />
          <div class="form-tip">
            <template v-if="form.provider === 'openai'">{{ $t('aiConfig.exampleOpenai') }}</template>
            <template v-else-if="form.provider === 'anthropic'">{{ $t('aiConfig.exampleAnthropic') }}</template>
            <template v-else>{{ $t('aiConfig.customApiUrl') }}</template>
          </div>
        </el-form-item>
        <el-form-item :label="$t('aiConfig.apiKey')" prop="api_key">
          <el-input
            v-model="form.api_key"
            :placeholder="$t('aiConfig.apiSecretKey')"
            :type="showApiKey ? 'text' : 'password'"
          >
            <template #suffix>
              <el-button link @click="showApiKey = !showApiKey">
                {{ showApiKey ? $t('common.close') : $t('common.details') }}
              </el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-divider>{{ $t('aiConfig.advancedSettings') }}</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('aiConfig.contextWindow')">
              <el-input-number v-model="form.context_window" :min="1" :max="1000000" :step="1000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('aiConfig.maxTokens')">
              <el-input-number v-model="form.max_tokens" :min="1" :max="100000" :step="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="$t('aiConfig.temperature')">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item :label="$t('aiConfig.setAsDefault')">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? $t('common.save') : $t('common.create') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Test Result Dialog -->
    <el-dialog v-model="testDialogVisible" :title="$t('aiConfig.test')" width="580px" class="cyber-dialog">
      <div v-if="testResult">
        <el-result
          :icon="testResult.success ? 'success' : 'error'"
          :title="testResult.message"
        >
          <template #sub-title>
            <span v-if="testResult.latency_ms">{{ $t('aiConfig.latency') }}: {{ testResult.latency_ms }}ms</span>
          </template>
          <template #extra>
            <div v-if="testResult.response" class="test-response">
              <div class="label">{{ $t('aiConfig.modelResponse') }}</div>
              <div class="content">{{ testResult.response }}</div>
            </div>
          </template>
        </el-result>
      </div>
      <template #footer>
        <el-button type="primary" @click="testDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { Plus, View, Hide, Check, Connection, Edit, Delete } from '@element-plus/icons-vue'
import { api } from '../api'

const userStore = useUserStore()

const { t: $t } = useI18n()

interface AIConfig {
  id: number
  name: string
  display_name: string
  provider: string
  model_name: string
  tier: string
  base_url: string
  api_key: string
  context_window: number
  max_tokens: number
  temperature: number
  is_default: boolean
  is_active: boolean
  testing?: boolean
}

const configs = ref<AIConfig[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const showApiKey = ref(false)
const visibleApiKeys = ref<Record<number, boolean>>({})

const form = reactive({
  id: 0,
  name: '',
  display_name: '',
  provider: 'openai',
  model_name: '',
  base_url: '',
  tier: 'sonnet',
  api_key: '',
  context_window: 128000,
  max_tokens: 4096,
  temperature: 0.7,
  is_default: false,
})

const rules = {
  name: [{ required: true, message: $t('aiConfig.enterConfigName'), trigger: 'blur' }],
  provider: [{ required: true, message: $t('aiConfig.selectProvider'), trigger: 'change' }],
  model_name: [{ required: true, message: $t('aiConfig.enterModelId'), trigger: 'blur' }],
  base_url: [{ required: true, message: $t('aiConfig.enterBaseUrl'), trigger: 'blur' }],
  api_key: [{ required: true, message: $t('aiConfig.enterApiKey'), trigger: 'blur' }],
}

const testDialogVisible = ref(false)
const testResult = ref<any>(null)

const maskApiKey = (key: string) => {
  if (!key) return $t('aiConfig.notSet')
  if (key.length <= 8) return '****'
  return key.slice(0, 4) + '****' + key.slice(-4)
}

const realApiKeys = ref<Record<number, string>>({})

const toggleApiKeyVisibility = async (id: number) => {
  if (visibleApiKeys.value[id]) {
    visibleApiKeys.value[id] = false
    return
  }
  // 首次显示时从后端获取真实 key
  if (!realApiKeys.value[id]) {
    try {
      const res = await api.get(`/ai-configs/${id}/api-key`)
      realApiKeys.value[id] = res.data.api_key || ''
    } catch {
      realApiKeys.value[id] = ''
    }
  }
  visibleApiKeys.value[id] = true
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await api.get('/ai-configs')
    configs.value = response.data.sort((a: any, b: any) => a.id - b.id)
  } catch (error) {
    ElMessage.error($t('aiConfig.operationFailed'))
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: 0,
    name: '',
    display_name: '',
    provider: 'openai',
    model_name: '',
    base_url: '',
    api_key: '',
    context_window: 128000,
    max_tokens: 4096,
    temperature: 0.7,
    is_default: false,
  })
  dialogVisible.value = true
}

const showEditDialog = async (config: AIConfig) => {
  isEdit.value = true
  // 编辑时获取真实 API Key（列表返回的是脱敏值）
  let realKey = config.api_key || ''
  if (!realKey || realKey === '••••••••') {
    try {
      const res = await api.get(`/ai-configs/${config.id}/api-key`)
      realKey = res.data.api_key || ''
    } catch {}
  }
  Object.assign(form, {
    id: config.id,
    name: config.name,
    display_name: config.display_name,
    provider: config.provider,
    model_name: config.model_name,
    tier: config.tier || 'sonnet',
    base_url: config.base_url,
    api_key: realKey,
    context_window: config.context_window,
    max_tokens: config.max_tokens,
    temperature: config.temperature,
    is_default: config.is_default,
  })
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const data = { ...form }
    if (isEdit.value) {
      await api.put(`/ai-configs/${form.id}`, data)
      ElMessage.success($t('aiConfig.configUpdated'))
    } else {
      // 创建时排除 id 字段
      delete (data as any).id
      await api.post('/ai-configs', data)
      ElMessage.success($t('aiConfig.configCreated'))
    }
    dialogVisible.value = false
    loadConfigs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('aiConfig.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const testConfig = async (config: AIConfig) => {
  config.testing = true
  testDialogVisible.value = true
  testResult.value = null

  try {
    const response = await api.post('/ai-configs/test', {
      model_config_id: config.id,
      test_prompt: 'Hello, are you working?'
    })
    testResult.value = response.data
  } catch (error: any) {
    testResult.value = {
      success: false,
      message: error.response?.data?.detail || $t('aiConfig.testFailed')
    }
  } finally {
    config.testing = false
  }
}

const deleteConfig = async (config: AIConfig) => {
  try {
    await ElMessageBox.confirm($t('aiConfig.confirmDeleteConfig', { name: config.display_name }), $t('skill.confirmDelete'), {
      type: 'warning',
    })
    await api.delete(`/ai-configs/${config.id}`)
    ElMessage.success($t('aiConfig.configDeleted'))
    loadConfigs()
  } catch (error) {
    // User cancelled
  }
}

const setDefault = async (config: AIConfig) => {
  try {
    await api.post(`/ai-configs/${config.id}/set-default`)
    ElMessage.success($t('aiConfig.setAsDefaultSuccess', { name: config.display_name }))
    loadConfigs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('aiConfig.operationFailed'))
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped lang="scss">
.ai-configs-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;
}

// ── Create button gradient glow ──
.btn-create {
  background: var(--pc-gradient-primary) !important;
  border: none !important;
  box-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.4);
  transition: box-shadow 0.3s, transform 0.15s;

  &:hover {
    box-shadow: 0 0 20px rgba(var(--pc-primary-rgb), 0.6);
    transform: translateY(-1px);
  }
}

// ── Glass card ──
.glass-card {
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  backdrop-filter: var(--pc-glass-blur);
  -webkit-backdrop-filter: var(--pc-glass-blur);
  box-shadow: var(--pc-shadow-md);
  padding: 4px;
  overflow: hidden;
}

// ── Cyber table overrides ──
.cyber-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(var(--pc-primary-rgb), 0.06);
  --el-table-border-color: var(--pc-border);
  --el-table-text-color: var(--pc-text-primary);
  --el-table-header-text-color: var(--pc-text-secondary);

  :deep(th.el-table__cell) {
    background: var(--pc-bg-deep) !important;
    border-bottom: 1px solid var(--pc-border) !important;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
  }

  :deep(td.el-table__cell) {
    border-bottom: 1px solid var(--pc-border) !important;
  }

  // Hover glow row
  :deep(tr:hover > td) {
    background: rgba(var(--pc-primary-rgb), 0.06) !important;
    box-shadow: inset 0 0 20px rgba(var(--pc-primary-rgb), 0.04);
  }

  // Fixed column header fix
  :deep(.el-table__fixed-right) {
    .el-table__header-wrapper {
      .el-table__header {
        th {
          background: var(--pc-bg-deep) !important;
        }
      }
    }
  }
}

// ── Status tags ──
.tag-default {
  background: rgba(var(--pc-accent-green), 0.15) !important;
  color: var(--pc-accent-green) !important;
  border: 1px solid rgba(var(--pc-accent-green), 0.3) !important;
  box-shadow: 0 0 8px rgba(var(--pc-accent-green), 0.25);
  font-weight: 600;
}

.tag-active {
  background: rgba(var(--pc-primary-rgb), 0.12) !important;
  color: var(--pc-primary) !important;
  border: 1px solid rgba(var(--pc-primary-rgb), 0.3) !important;
  font-weight: 500;
}

.tag-disabled {
  background: rgba(var(--pc-accent-red), 0.12) !important;
  color: var(--pc-accent-red) !important;
  border: 1px solid rgba(var(--pc-accent-red), 0.25) !important;
  font-weight: 500;
}

.tag-provider {
  background: var(--pc-bg-elevated) !important;
  color: var(--pc-text-secondary) !important;
  border: 1px solid var(--pc-border) !important;
}

// ── API key monospace ──
.api-key-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.api-key-mask {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 12px;
  color: var(--pc-text-secondary);
  letter-spacing: 0.5px;
  word-break: break-all;
}

.visibility-toggle {
  color: var(--pc-text-muted) !important;
  padding: 2px !important;

  &:hover {
    color: var(--pc-primary) !important;
  }
}

// ── Action buttons ──
.action-btns {
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: center;
}

.icon-btn {
  background: transparent !important;
  border: 1px solid var(--pc-border) !important;
  color: var(--pc-text-secondary) !important;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-1px);
  }
}

.btn-set-default {
  &:hover {
    border-color: var(--pc-accent-green) !important;
    color: var(--pc-accent-green) !important;
    background: rgba(var(--pc-accent-green), 0.1) !important;
    box-shadow: 0 0 8px rgba(var(--pc-accent-green), 0.3);
  }
}

.btn-test {
  &:hover {
    border-color: var(--pc-primary) !important;
    color: var(--pc-primary) !important;
    background: rgba(var(--pc-primary-rgb), 0.1) !important;
    box-shadow: 0 0 8px rgba(var(--pc-primary-rgb), 0.3);
  }
}

.btn-edit {
  &:hover {
    border-color: var(--pc-accent-orange) !important;
    color: var(--pc-accent-orange) !important;
    background: rgba(var(--pc-accent-orange), 0.1) !important;
    box-shadow: 0 0 8px rgba(var(--pc-accent-orange), 0.3);
  }
}

.btn-delete {
  &:hover {
    border-color: var(--pc-accent-red) !important;
    color: var(--pc-accent-red) !important;
    background: rgba(var(--pc-accent-red), 0.1) !important;
    box-shadow: 0 0 8px rgba(var(--pc-accent-red), 0.3);
  }
}

// ── Form tips ──
.form-tip {
  font-size: 12px;
  color: var(--pc-text-muted);
  margin-top: 4px;
  line-height: 1.5;
}

// ── Test response ──
.test-response {
  margin-top: 16px;
  text-align: left;
  width: 100%;
  box-sizing: border-box;
  max-width: 100%;
  overflow: hidden;

  .label {
    font-weight: 600;
    margin-bottom: 8px;
    color: var(--pc-text-primary);
  }

  .content {
    background: var(--pc-bg-deep);
    color: var(--pc-text-primary);
    padding: 12px;
    border-radius: var(--pc-radius-sm);
    border: 1px solid var(--pc-border);
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 200px;
    overflow-y: auto;
    overflow-x: hidden;
    text-align: left;
    width: 100%;
    box-sizing: border-box;
    max-width: 100%;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 13px;
  }
}

// ── Test result: 长文本换行 ──
:deep(.el-result__title) {
  word-break: break-all;
  white-space: normal;
  font-size: 14px;
}

// ── Dialog styling ──
:deep(.cyber-dialog) {
  .el-dialog {
    background: var(--pc-bg-surface);
    border: 1px solid var(--pc-glass-border);
    border-radius: var(--pc-radius-lg);
    box-shadow: var(--pc-shadow-lg);
  }

  .el-dialog__header {
    border-bottom: 1px solid var(--pc-border);
    padding-bottom: 16px;
  }

  .el-dialog__title {
    color: var(--pc-text-primary);
    font-weight: 600;
  }

  .el-dialog__body {
    color: var(--pc-text-primary);
  }

  .el-form-item__label {
    color: var(--pc-text-secondary);
  }

  .el-divider__text {
    color: var(--pc-text-muted);
    background: var(--pc-bg-surface);
  }
}
</style>
