<template>
  <div class="agents-page">
    <div class="pc-page-header">
      <h2 class="pc-page-title">{{ $t('agent.title') }}</h2>
      <button class="pc-glow-btn" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        {{ $t('agent.create') }}
      </button>
    </div>

    <!-- Agent List -->
    <div class="pc-glass-card agent-card">
      <div class="card-gradient-line"></div>
      <div class="table-scroll">
        <el-table
          v-loading="loading"
          :data="agents"
          class="pc-data-table"
          :header-cell-style="{ background: 'transparent' }"
          :cell-style="{ background: 'transparent' }"
        >
        <template #empty>
          <el-empty :description="$t('common.noData')" />
        </template>
        <el-table-column prop="name" :label="$t('common.name')" width="150">
          <template #default="{ row }">
            <span class="agent-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="display_name" :label="$t('agent.displayName')" width="140" />
        <el-table-column prop="description" :label="$t('common.description')" min-width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="desc-text">{{ row.description }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="model" :label="$t('agent.model')" width="150">
          <template #default="{ row }">
            <span class="model-tag">{{ row.model }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="max_turns" :label="$t('agent.turns')" width="80" />
        <el-table-column prop="status" :label="$t('common.status')" width="110">
          <template #default="{ row }">
            <span :class="['status-badge', row.status === 'active' ? 'status-active' : 'status-inactive']">
              <span class="status-dot"></span>
              {{ row.status === 'active' ? $t('agent.active') : $t('agent.inactive') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="280">
          <template #default="{ row }">
            <div class="pc-action-group">
              <el-button size="small" @click="showDialog(row)">
                <el-icon><Edit /></el-icon>
                {{ $t('common.edit') }}
              </el-button>
              <el-button size="small" type="warning" @click="toggleStatus(row)">
                <el-icon><Switch /></el-icon>
                {{ row.status === 'active' ? $t('agent.disable') : $t('agent.enable') }}
              </el-button>
              <el-popconfirm :title="$t('agent.confirmDelete')" @confirm="deleteAgent(row.id)">
                <template #reference>
                  <el-button size="small" type="danger">
                    <el-icon><Delete /></el-icon>
                    {{ $t('common.delete') }}
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
      </div>
    </div>

    <!-- Create / Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingAgent ? $t('agent.edit') : $t('agent.create')"
      width="550px"
      class="cyber-dialog"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="cyber-form">
        <el-form-item :label="$t('common.name')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('agent.uniqueId')" :disabled="!!editingAgent" />
        </el-form-item>
        <el-form-item :label="$t('agent.displayName')" prop="display_name">
          <el-input v-model="form.display_name" :placeholder="$t('agent.displayNameExample')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" :placeholder="$t('agent.agentDescription')" />
        </el-form-item>
        <el-form-item :label="$t('agent.model')" prop="model">
          <el-select v-model="form.model" style="width: 100%" :placeholder="$t('agent.selectModel')">
            <el-option
              v-for="config in modelConfigs"
              :key="config.id"
              :label="config.display_name"
              :value="config.model_name"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('agent.maxTurns')" prop="max_turns">
          <el-input-number v-model="form.max_turns" :min="1" :max="200" />
        </el-form-item>
        <el-form-item :label="$t('agent.systemPrompt')" prop="system_prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="4" :placeholder="$t('agent.systemPromptPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <button class="pc-glow-btn secondary" @click="dialogVisible = false">{{ $t('common.cancel') }}</button>
          <button class="pc-glow-btn" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? $t('agent.submitting') : $t('common.confirm') }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { api } from '@/api'
import { Plus, Edit, Delete, Switch } from '@element-plus/icons-vue'

const { t: $t } = useI18n()

interface Agent {
  id: number
  name: string
  display_name: string
  description: string
  model: string
  max_turns: number
  status: string
  system_prompt?: string
}

interface ModelConfig {
  id: number
  name: string
  display_name: string
  model_name: string
  provider: string
  is_default: boolean
}

const loading = ref(false)
const agents = ref<Agent[]>([])
const modelConfigs = ref<ModelConfig[]>([])
const dialogVisible = ref(false)
const editingAgent = ref<Agent | null>(null)
const submitting = ref(false)
const formRef = ref()

const form = reactive({
  name: '',
  display_name: '',
  description: '',
  model: '',
  max_turns: 20,
  system_prompt: '',
  skill_ids: [] as number[]
})

const rules = {
  name: [{ required: true, message: $t('agent.name'), trigger: 'blur' }],
  display_name: [{ required: true, message: $t('agent.displayName'), trigger: 'blur' }]
}

async function fetchAgents() {
  loading.value = true
  try {
    const res = await api.get('/agents')
    agents.value = res.data
  } finally {
    loading.value = false
  }
}

async function fetchModelConfigs() {
  try {
    const res = await api.get('/ai-configs')
    modelConfigs.value = res.data
    // Set default model
    const defaultModel = modelConfigs.value.find(m => m.is_default)
    if (defaultModel && !form.model) {
      form.model = defaultModel.model_name
    }
  } catch (error) {
    console.error('Failed to load model configs:', error)
  }
}

function showDialog(agent?: Agent) {
  editingAgent.value = agent || null
  if (agent) {
    Object.assign(form, {
      name: agent.name,
      display_name: agent.display_name,
      description: agent.description || '',
      model: agent.model,
      max_turns: agent.max_turns,
      system_prompt: agent.system_prompt || '',
      skill_ids: []
    })
  } else {
    // Set default model when creating new agent
    const defaultModel = modelConfigs.value.find(m => m.is_default)
    Object.assign(form, {
      name: '',
      display_name: '',
      description: '',
      model: defaultModel?.model_name || '',
      max_turns: 20,
      system_prompt: '',
      skill_ids: []
    })
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (editingAgent.value) {
      await api.put(`/agents/${editingAgent.value.id}`, form)
      ElMessage.success($t('agent.updatedSuccess'))
    } else {
      await api.post('/agents', form)
      ElMessage.success($t('agent.createdSuccess'))
    }
    dialogVisible.value = false
    fetchAgents()
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(agent: Agent) {
  const newStatus = agent.status === 'active' ? 'inactive' : 'active'
  try {
    await api.put(`/agents/${agent.id}`, { status: newStatus })
    ElMessage.success($t('agent.statusUpdated'))
    fetchAgents()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || $t('common.failed'))
  }
}

async function deleteAgent(id: number) {
  await api.delete(`/agents/${id}`)
  ElMessage.success($t('agent.deletedSuccess'))
  fetchAgents()
}

onMounted(() => {
  fetchAgents()
  fetchModelConfigs()
})
</script>

<style scoped lang="scss">
/* ===== Page Layout ===== */
.agents-page {
  padding: 0;
}

/* ===== Glow Button ===== */
.pc-glow-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  border: 1px solid var(--pc-primary);
  border-radius: var(--pc-radius-md);
  background: linear-gradient(135deg, rgba(var(--pc-primary-rgb), 0.15), rgba(var(--pc-primary-rgb), 0.05));
  color: var(--pc-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.15);

  &:hover {
    background: linear-gradient(135deg, rgba(var(--pc-primary-rgb), 0.25), rgba(var(--pc-primary-rgb), 0.12));
    box-shadow: 0 0 24px rgba(var(--pc-primary-rgb), 0.3), 0 0 48px rgba(var(--pc-primary-rgb), 0.1);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }

  &.secondary {
    border-color: var(--pc-border);
    color: var(--pc-text-secondary);
    background: var(--pc-bg-elevated);
    box-shadow: none;

    &:hover {
      border-color: var(--pc-border-hover);
      color: var(--pc-text-primary);
      box-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.08);
    }
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
}

/* ===== Glass Card ===== */
.pc-glass-card {
  position: relative;
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  backdrop-filter: var(--pc-glass-blur);
  -webkit-backdrop-filter: var(--pc-glass-blur);
  overflow: hidden;

  .card-gradient-line {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--pc-gradient-primary);
    z-index: 1;
  }
}

.agent-card {
  :deep(.el-card__body) {
    padding: 0;
  }
}

/* ===== Table Scroll Wrapper ===== */
.table-scroll {
  overflow-x: auto;
  width: 100%;
}

/* ===== Cyber Table ===== */
.cyber-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(var(--pc-primary-rgb), 0.06);
  --el-table-border-color: var(--pc-border);
  --el-table-text-color: var(--pc-text-primary);
  --el-table-header-text-color: var(--pc-text-secondary);
  --el-table-current-row-bg-color: rgba(var(--pc-primary-rgb), 0.08);
  width: 100%;

  :deep(.el-table__inner-wrapper) {
    &::before {
      display: none;
    }
  }

  :deep(.el-table__header-wrapper) {
    th {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--pc-text-muted) !important;
      border-bottom: 1px solid var(--pc-border) !important;
    }
  }

  :deep(.el-table__body-wrapper) {
    td {
      border-bottom: 1px solid rgba(var(--pc-primary-rgb), 0.08) !important;
      transition: all 0.2s ease;
    }

    tr {
      transition: all 0.2s ease;

      &:hover > td {
        background: rgba(var(--pc-primary-rgb), 0.04) !important;
      }
    }
  }

  :deep(.el-table__empty-block) {
    background: transparent;
  }

  /* Remove stripe - we handle it ourselves */
  &.el-table--striped .el-table__body tr.el-table__row--striped td {
    background: rgba(var(--pc-primary-rgb), 0.02) !important;
  }
}

.agent-name {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  color: var(--pc-primary);
  font-weight: 600;
  font-size: 13px;
}

.desc-text {
  color: var(--pc-text-secondary);
  font-size: 13px;
}

.model-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--pc-radius-sm);
  background: rgba(var(--pc-primary-rgb), 0.1);
  border: 1px solid rgba(var(--pc-primary-rgb), 0.2);
  color: var(--pc-primary);
  font-size: 12px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-weight: 500;
}

/* ===== Status Badge ===== */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.3px;

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
  }

  &.status-active {
    color: var(--pc-accent-green);
    background: rgba(var(--pc-accent-green), 0.1);
    border: 1px solid rgba(var(--pc-accent-green), 0.25);

    .status-dot {
      background: var(--pc-accent-green);
      box-shadow: 0 0 8px rgba(var(--pc-accent-green), 0.6);
      animation: pulse-green 2s ease-in-out infinite;
    }
  }

  &.status-inactive {
    color: var(--pc-text-muted);
    background: rgba(var(--pc-text-muted), 0.08);
    border: 1px solid rgba(var(--pc-text-muted), 0.15);

    .status-dot {
      background: var(--pc-text-muted);
    }
  }
}

@keyframes pulse-green {
  0%, 100% {
    box-shadow: 0 0 4px rgba(var(--pc-accent-green), 0.4);
  }
  50% {
    box-shadow: 0 0 12px rgba(var(--pc-accent-green), 0.8);
  }
}

/* ===== Action Buttons (unified via .pc-action-group in main.scss) ===== */

/* ===== Cyber Dialog ===== */
:deep(.cyber-dialog) {
  .el-dialog {
    background: var(--pc-bg-elevated);
    border: 1px solid var(--pc-glass-border);
    border-radius: var(--pc-radius-lg);
    box-shadow: var(--pc-shadow-lg), 0 0 60px rgba(var(--pc-primary-rgb), 0.08);
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: var(--pc-gradient-primary);
    }
  }

  .el-dialog__header {
    border-bottom: 1px solid var(--pc-border);
    padding: 16px 24px;
    margin-right: 0;

    .el-dialog__title {
      color: var(--pc-text-primary);
      font-weight: 700;
      font-size: 16px;
      letter-spacing: 0.3px;
    }

    .el-dialog__headerbtn {
      top: 16px;
      right: 20px;

      .el-dialog__close {
        color: var(--pc-text-muted);
        &:hover {
          color: var(--pc-text-primary);
        }
      }
    }
  }

  .el-dialog__body {
    padding: 24px;
    color: var(--pc-text-primary);
  }

  .el-dialog__footer {
    border-top: 1px solid var(--pc-border);
    padding: 16px 24px;
  }
}

/* ===== Cyber Form ===== */
.cyber-form {
  :deep(.el-form-item__label) {
    color: var(--pc-text-secondary);
    font-weight: 500;
    font-size: 13px;
  }

  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner),
  :deep(.el-select__wrapper) {
    background-color: var(--pc-bg-surface) !important;
    border: 1px solid var(--pc-border) !important;
    border-radius: var(--pc-radius-md) !important;
    box-shadow: none !important;
    color: var(--pc-text-primary);
    transition: all 0.25s ease;

    &:hover {
      border-color: var(--pc-border-hover) !important;
    }

    &.is-focus,
    &:focus {
      border-color: var(--pc-primary) !important;
      box-shadow: 0 0 0 2px rgba(var(--pc-primary-rgb), 0.15) !important;
    }
  }

  :deep(.el-input__inner),
  :deep(.el-textarea__inner) {
    color: var(--pc-text-primary);

    &::placeholder {
      color: var(--pc-text-muted);
    }
  }

  :deep(.el-input__inner:disabled) {
    opacity: 0.5;
    cursor: not-allowed;
  }

  :deep(.el-input-number) {
    .el-input__wrapper {
      background-color: var(--pc-bg-surface) !important;
    }
  }

  :deep(.el-select-dropdown) {
    background: var(--pc-bg-elevated);
    border: 1px solid var(--pc-glass-border);
    border-radius: var(--pc-radius-md);

    .el-select-dropdown__item {
      color: var(--pc-text-secondary);

      &.is-hovering {
        background: rgba(var(--pc-primary-rgb), 0.08);
        color: var(--pc-text-primary);
      }

      &.is-selected {
        color: var(--pc-primary);
        font-weight: 600;
      }
    }
  }
}

/* ===== Dialog Footer ===== */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* ===== Loading Overlay ===== */
:deep(.el-loading-mask) {
  background: rgba(var(--pc-bg-deep), 0.7);
  backdrop-filter: blur(4px);

  .el-loading-spinner {
    .circular {
      .path {
        stroke: var(--pc-primary);
      }
    }

    .el-loading-text {
      color: var(--pc-text-secondary);
    }
  }
}

/* ===== Popconfirm Dark Mode ===== */
:deep(.el-popconfirm) {
  .el-popconfirm__main {
    color: var(--pc-text-primary);
  }
}

:deep(.el-popper) {
  background: var(--pc-bg-elevated) !important;
  border: 1px solid var(--pc-glass-border) !important;
  border-radius: var(--pc-radius-md) !important;
  color: var(--pc-text-primary) !important;

  .el-popconfirm__main {
    color: var(--pc-text-primary) !important;
  }

  .el-popconfirm__action {
    .el-button--primary {
      background: var(--pc-primary);
      border-color: var(--pc-primary);
    }
  }
}
</style>
