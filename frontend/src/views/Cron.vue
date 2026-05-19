<template>
  <div class="cron-page">
    <div class="pc-page-header">
      <h2 class="pc-page-title">{{ $t('cron.title') }}</h2>
      <button class="pc-glow-btn" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        {{ $t('cron.create') }}
      </button>
    </div>

    <!-- Job List -->
    <el-card shadow="never">
      <div class="table-scroll">
        <el-table :data="jobs" v-loading="loading" stripe v-if="jobs.length > 0">
        <el-table-column prop="id" :label="$t('cron.id')" width="60">
          <template #default="{ row }">
            <el-tag type="info" size="small">#{{ row.id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('common.name')" width="170" />
        <el-table-column prop="cron_expr" :label="$t('cron.expression')" width="180">
          <template #default="{ row }">
            <code class="cron-code">{{ row.cron_expr }}</code>
          </template>
        </el-table-column>
        <el-table-column :label="$t('cron.schedule')" width="150">
          <template #default="{ row }">
            {{ getCronHint(row.cron_expr) }}
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('common.description')" min-width="70" show-overflow-tooltip />
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? $t('common.active') : $t('common.inactive') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="run_count" :label="$t('cron.runs')" width="100" />
        <el-table-column prop="last_run" :label="$t('cron.lastRun')" width="160">
          <template #default="{ row }">
            {{ row.last_run ? formatDate(row.last_run) : '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="340">
          <template #default="{ row }">
            <div class="pc-action-group">
              <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleJob(row)">
                <el-icon><Switch /></el-icon>
                {{ row.is_active ? $t('common.disable') : $t('common.enable') }}
              </el-button>
              <el-button size="small" type="primary" @click="runJobNow(row)">
                <el-icon><VideoPlay /></el-icon>
                {{ $t('cron.run') }}
              </el-button>
              <el-button size="small" @click="showEditDialog(row)">
                <el-icon><Edit /></el-icon>
                {{ $t('common.edit') }}
              </el-button>
              <el-button size="small" type="danger" @click="deleteJob(row)">
                <el-icon><Delete /></el-icon>
                {{ $t('common.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="jobs.length === 0" :description="$t('common.noData')" />
      </div>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('common.edit') : $t('cron.create')" width="600px">
      <el-form :model="form" label-width="130px" ref="formRef" :rules="rules">
        <el-form-item :label="$t('common.name')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('common.name')" />
        </el-form-item>
        <el-form-item :label="$t('cron.expression')" prop="cron_expr">
          <el-input v-model="form.cron_expr" :placeholder="$t('cron.expression')" />
          <div class="cron-help">
            <p>{{ $t('cron.format') }}</p>
            <p>{{ $t('cron.examples') }}</p>
            <ul>
              <li><code>0 9 * * *</code> - {{ $t('cron.dailyAt9') }}</li>
              <li><code>0 */2 * * *</code> - {{ $t('cron.everyHour') }}</li>
              <li><code>30 8 * * 1-5</code> - {{ $t('cron.weekdaysAt9') }}</li>
              <li><code>0 0 * * 0</code> - {{ $t('cron.everySunday') }}</li>
            </ul>
          </div>
        </el-form-item>
        <el-form-item :label="$t('cron.task')">
          <el-select v-model="form.agent_id" :placeholder="$t('cron.task')" clearable style="width: 100%">
            <el-option v-for="agent in agents" :key="agent.id" :label="agent.name" :value="agent.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('cron.inputParams')">
          <el-input v-model="form.input_data_str" type="textarea" :rows="3" :placeholder="$t('cron.inputParams')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <el-input v-model="form.description" type="textarea" :rows="2" :placeholder="$t('common.description')" />
        </el-form-item>
        <el-form-item :label="$t('common.status')">
          <el-switch v-model="form.is_active" :active-text="$t('common.enable')" :inactive-text="$t('common.disable')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, Switch, VideoPlay, Edit, Delete } from '@element-plus/icons-vue'
import { api } from '../api'

const { t: $t } = useI18n()

interface CronJob {
  id: number
  name: string
  cron_expr: string
  agent_id: number | null
  input_data: any
  description: string | null
  is_active: boolean
  last_run: string | null
  next_run: string | null
  run_count: number
  created_at: string
  updated_at: string
}

interface Agent {
  id: number
  name: string
}

const jobs = ref<CronJob[]>([])
const agents = ref<Agent[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  id: 0,
  name: '',
  cron_expr: '',
  agent_id: null as number | null,
  input_data_str: '',
  description: '',
  is_active: true
})

const rules = {
  name: [{ required: true, message: () => $t('cron.enterJobName'), trigger: 'blur' }],
  cron_expr: [{ required: true, message: () => $t('cron.enterCronExpression'), trigger: 'blur' }]
}

const cronHintKeys: Record<string, string> = {
  '* * * * *': 'cron.everyMinute',
  '0 * * * *': 'cron.everyHour',
  '0 0 * * *': 'cron.dailyAt0',
  '0 9 * * *': 'cron.dailyAt9',
  '0 18 * * *': 'cron.dailyAt18',
  '0 9 * * 1-5': 'cron.weekdaysAt9',
  '0 0 * * 0': 'cron.everySunday',
  '0 0 1 * *': 'cron.firstOfMonth'
}

function getCronHint(expr: string): string {
  return cronHintKeys[expr] ? $t(cronHintKeys[expr]) : $t('cron.custom')
}

function formatDate(date: string) {
  return new Date(date).toLocaleString()
}

async function loadJobs() {
  loading.value = true
  try {
    const res = await api.get('/cron')
    jobs.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadAgents() {
  try {
    const res = await api.get('/agents')
    agents.value = res.data
  } catch (error) {
    console.error('Failed to load agents')
  }
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, { id: 0, name: '', cron_expr: '', agent_id: null, input_data_str: '', description: '', is_active: true })
  dialogVisible.value = true
}

function showEditDialog(job: CronJob) {
  isEdit.value = true
  Object.assign(form, {
    id: job.id,
    name: job.name,
    cron_expr: job.cron_expr,
    agent_id: job.agent_id,
    input_data_str: job.input_data ? JSON.stringify(job.input_data, null, 2) : '',
    description: job.description || '',
    is_active: job.is_active
  })
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  let inputData = null
  if (form.input_data_str) {
    try {
      inputData = JSON.parse(form.input_data_str)
    } catch {
      ElMessage.error($t('cron.invalidJson'))
      return
    }
  }

  submitting.value = true
  try {
    const data = {
      name: form.name,
      cron_expr: form.cron_expr,
      agent_id: form.agent_id,
      input_data: inputData,
      description: form.description,
      is_active: form.is_active
    }

    if (isEdit.value) {
      await api.put(`/cron/${form.id}`, data)
      ElMessage.success($t('cron.updated'))
    } else {
      await api.post('/cron', data)
      ElMessage.success($t('cron.created'))
    }
    dialogVisible.value = false
    loadJobs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('cron.operationFailed'))
  } finally {
    submitting.value = false
  }
}

async function toggleJob(job: CronJob) {
  try {
    await api.post(`/cron/${job.id}/toggle`)
    ElMessage.success(job.is_active ? $t('cron.disabled') : $t('common.enable'))
    loadJobs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('cron.operationFailed'))
  }
}

async function runJobNow(job: CronJob) {
  try {
    await api.post(`/cron/${job.id}/run`)
    ElMessage.success($t('cron.jobTriggered'))
    loadJobs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('cron.operationFailed'))
  }
}

async function deleteJob(job: CronJob) {
  try {
    await ElMessageBox.confirm($t('cron.confirmDeleteJob', { name: job.name }), $t('cron.confirmDelete'), { type: 'warning' })
    await api.delete(`/cron/${job.id}`)
    ElMessage.success($t('cron.deleted'))
    loadJobs()
  } catch (error) {
    // User cancelled
  }
}

onMounted(() => {
  loadJobs()
  loadAgents()
})
</script>

<style scoped lang="scss">
.cron-page {
  padding: 0;
}

.table-scroll {
  overflow-x: auto;
  width: 100%;
}

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
}

.cron-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 { margin: 0; }
  }

  .cron-code {
    background: var(--pc-bg-deep);
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 13px;
  }

  .cron-help {
    margin-top: 8px;
    padding: 12px;
    background: var(--pc-bg-deep);
    border-radius: 4px;
    font-size: 12px;

    p { margin: 4px 0; }
    ul { margin: 4px 0; padding-left: 20px; }
    li { margin: 4px 0; }
    code {
      background: var(--pc-border);
      padding: 1px 4px;
      border-radius: 2px;
    }
  }
}
</style>
