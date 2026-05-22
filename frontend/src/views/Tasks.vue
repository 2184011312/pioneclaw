<template>
  <div class="tasks-page">
    <!-- Page Header -->
    <div class="pc-page-header">
      <h2 class="pc-page-title">{{ $t('task.title') }}</h2>
      <button class="pc-glow-btn" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        {{ $t('task.create') }}
      </button>
    </div>

    <!-- Stat Cards -->
    <div class="stats-row">
      <div class="stat-card" :class="{ active: currentTab === '' }" @click="currentTab = ''; loadTasks()">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">{{ $t('common.all') }}</div>
      </div>
      <div class="stat-card todo" :class="{ active: currentTab === 'todo' }" @click="currentTab = 'todo'; loadTasks()">
        <div class="stat-value">{{ stats.todo }}</div>
        <div class="stat-label">{{ $t('task.todo') }}</div>
      </div>
      <div class="stat-card progress" :class="{ active: currentTab === 'in_progress' }" @click="currentTab = 'in_progress'; loadTasks()">
        <div class="stat-value">{{ stats.in_progress }}</div>
        <div class="stat-label">{{ $t('task.inProgress') }}</div>
      </div>
      <div class="stat-card done" :class="{ active: currentTab === 'done' }" @click="currentTab = 'done'; loadTasks()">
        <div class="stat-value">{{ stats.done }}</div>
        <div class="stat-label">{{ $t('task.done') }}</div>
      </div>
      <div class="stat-card mine" :class="{ active: currentTab === 'mine' }" @click="loadMyTasks">
        <div class="stat-value">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-label">{{ $t('task.myTasks') }}</div>
      </div>
    </div>

    <!-- Tabs for Tasks and Approvals -->
    <el-tabs v-model="activeMainTab" class="main-tabs" @tab-change="(tab: string) => { if (tab === 'approvals') loadApprovals(); }">
      <el-tab-pane :label="$t('nav.tasks')" name="tasks">
        <!-- Task List -->
    <el-card class="task-list-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="filter-group">
            <el-select v-model="filterPriority" :placeholder="$t('task.priority')" clearable size="small" style="width: 100px" @change="loadTasks">
              <el-option :label="$t('common.all')" value="" />
              <el-option :label="$t('task.urgent')" value="urgent" />
              <el-option :label="$t('task.high')" value="high" />
              <el-option :label="$t('task.normal')" value="normal" />
              <el-option :label="$t('task.low')" value="low" />
            </el-select>
            <el-select v-model="filterType" :placeholder="$t('common.type')" clearable size="small" style="width: 120px" @change="loadTasks">
              <el-option :label="$t('common.all')" value="" />
              <el-option :label="$t('task.manual')" value="manual" />
              <el-option :label="$t('nav.agents')" value="agent" />
              <el-option :label="$t('nav.cron')" value="cron" />
            </el-select>
          </div>
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('common.search')"
            prefix-icon="Search"
            clearable
            size="small"
            style="width: 200px"
            @input="filterTasks"
          />
        </div>
      </template>

      <div class="task-list" v-loading="loading">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-item"
          :class="task.status"
        >
          <div class="task-checkbox">
            <el-checkbox
              :model-value="task.status === 'done'"
              @change="toggleTask(task)"
            />
          </div>

          <div class="task-content" @click="showTaskDetail(task)">
            <div class="task-header">
              <span class="task-title">{{ task.title }}</span>
              <div class="task-tags">
                <el-tag :type="getPriorityType(task.priority)" size="small">
                  {{ getPriorityLabel(task.priority) }}
                </el-tag>
                <el-tag type="info" size="small">
                  {{ getTypeLabel(task.task_type) }}
                </el-tag>
                <el-tag type="info" size="small">
                  {{ formatDate(task.created_at) }}
                </el-tag>
              </div>
            </div>
            <div v-if="task.description" class="task-meta">
              <span>{{ task.description }}</span>
            </div>
          </div>

          <div class="task-actions">
            <el-button-group size="small">
              <el-button type="primary" @click="editTask(task)" v-if="task.status === 'todo'">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button type="success" @click="startTask(task)" v-if="task.status === 'todo'">
                <el-icon><VideoPlay /></el-icon>
              </el-button>
              <el-button type="warning" @click="completeTask(task)" v-if="task.status === 'in_progress'">
                <el-icon><Select /></el-icon>
              </el-button>
              <el-button type="danger" @click="cancelTask(task)" v-if="task.status !== 'done' && task.status !== 'cancelled'">
                <el-icon><Close /></el-icon>
              </el-button>
              <el-popconfirm :title="$t('user.confirmDelete')" @confirm="deleteTask(task)">
                <template #reference>
                  <el-button type="danger">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-popconfirm>
            </el-button-group>
          </div>
        </div>

        <el-empty v-if="filteredTasks.length === 0" :description="$t('common.noData')" />
      </div>
    </el-card>
      </el-tab-pane>

      <el-tab-pane name="approvals">
        <template #label>
          <span class="tab-label-wrap">
            {{ $t('approval.title') }}
            <el-badge v-if="pendingApprovalCount > 0" :value="pendingApprovalCount" class="tab-badge" />
          </span>
        </template>

        <!-- Approval Filters -->
        <div class="approval-filters">
          <el-select v-model="approvalStatusFilter" :placeholder="$t('approval.filterStatus')" clearable size="small" style="width: 150px" @change="loadApprovals">
            <el-option :label="$t('approval.all')" value="" />
            <el-option :label="$t('approval.pending')" value="pending" />
            <el-option :label="$t('approval.approved')" value="approved" />
            <el-option :label="$t('approval.rejected')" value="rejected" />
          </el-select>
          <el-button size="small" @click="loadApprovals">
            <el-icon><Refresh /></el-icon>
            {{ $t('common.refresh') }}
          </el-button>
        </div>

        <!-- Approval List -->
        <el-card class="approval-list-card" shadow="never">
          <el-table :data="approvals" v-loading="loadingApprovals" style="width: 100%" class="pc-data-table" @row-click="showApprovalDetail">
            <el-table-column :label="$t('common.name')" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="approval-title-link">{{ row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('approval.requester')" width="120">
              <template #default="{ row }">
                <span class="requester-name">{{ row.requester_name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.type')" width="130">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ getResourceTypeLabel(row.resource_type) }}</el-tag>
                <span class="arrow-sep">→</span>
                <el-tag size="small" :type="row.target_scope === 'system' ? 'danger' : 'warning'">
                  {{ row.target_scope === 'system' ? '系统' : '组织' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.status')" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getApprovalStatusType(row.status)" size="small">
                  {{ getApprovalStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" :label="$t('common.time')" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.actions')" width="200" align="center">
              <template #default="{ row }">
                <div class="approval-actions" @click.stop>
                  <template v-if="row.status === 'pending'">
                    <el-button
                      v-if="canApprove(row)"
                      size="small"
                      type="primary"
                      @click="openReviewDialog(row, 'approve')"
                    >
                      {{ $t('approval.approve') }}
                    </el-button>
                    <el-button
                      v-if="canApprove(row)"
                      size="small"
                      type="danger"
                      @click="openReviewDialog(row, 'reject')"
                    >
                      {{ $t('approval.reject') }}
                    </el-button>
                    <el-button
                      v-if="canCancel(row)"
                      size="small"
                      @click="cancelApproval(row)"
                    >
                      {{ $t('approval.cancel') }}
                    </el-button>
                  </template>
                  <el-button v-else size="small" @click="showApprovalDetail(row)">
                    <el-icon><View /></el-icon>
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="approvals.length === 0 && !loadingApprovals" :description="$t('approval.noApprovals')" />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Create / Edit Task Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('task.edit') : $t('task.create')" width="600px" class="pc-dialog">
      <el-form :model="form" label-width="80px" ref="formRef" :rules="rules">
        <el-form-item :label="$t('common.name')" prop="title">
          <el-input v-model="form.title" :placeholder="$t('common.name')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="$t('common.description')" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item :label="$t('task.priority')">
              <el-select v-model="form.priority" style="width: 100%">
                <el-option :label="$t('task.low')" value="low" />
                <el-option :label="$t('task.normal')" value="normal" />
                <el-option :label="$t('task.high')" value="high" />
                <el-option :label="$t('task.urgent')" value="urgent" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('common.type')">
              <el-select v-model="form.task_type" style="width: 100%">
                <el-option :label="$t('task.manual')" value="manual" />
                <el-option :label="$t('nav.agents')" value="agent" />
                <el-option :label="$t('nav.cron')" value="cron" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="$t('task.dueDate')">
          <el-date-picker
            v-model="form.due_at"
            type="datetime"
            :placeholder="$t('task.dueDate')"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Review Dialog -->
    <el-dialog
      v-model="reviewVisible"
      :title="reviewAction === 'approve' ? $t('approval.approve') : $t('approval.reject')"
      width="520px"
      class="pc-dialog review-dialog"
      :close-on-click-modal="false"
    >
      <div class="review-content" v-if="reviewApproval">
        <div class="review-card">
          <div class="review-card-label">{{ $t('common.name') }}</div>
          <div class="review-card-value">{{ reviewApproval.title }}</div>
        </div>
        <div class="review-card">
          <div class="review-card-label">{{ $t('approval.approvalType') }}</div>
          <div class="review-card-value">
            <el-tag size="small" type="info">{{ getApprovalTypeLabel(reviewApproval.approval_type) }}</el-tag>
          </div>
        </div>
        <div class="review-card">
          <div class="review-card-label">{{ $t('approval.targetScope') }}</div>
          <div class="review-card-value">
            <el-tag size="small" :type="reviewApproval.target_scope === 'system' ? 'danger' : 'warning'">
              {{ reviewApproval.target_scope === 'system' ? $t('nav.sysPerms') : $t('nav.orgPerms') }}
            </el-tag>
          </div>
        </div>
        <div v-if="reviewApproval.description" class="review-card">
          <div class="review-card-label">{{ $t('common.description') }}</div>
          <div class="review-card-value desc-text">{{ reviewApproval.description }}</div>
        </div>

        <div class="review-comment-section">
          <div class="review-card-label">{{ $t('approval.comment') }}</div>
          <el-input
            v-model="reviewComment"
            type="textarea"
            :rows="3"
            :placeholder="reviewAction === 'approve' ? $t('approval.approveCommentPlaceholder') : $t('approval.rejectCommentPlaceholder')"
            class="review-comment-input"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="reviewVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button
          :type="reviewAction === 'approve' ? 'primary' : 'danger'"
          @click="submitReview"
          :loading="reviewing"
          class="review-submit-btn"
        >
          {{ reviewAction === 'approve' ? $t('approval.approve') : $t('approval.reject') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Approval Detail Drawer -->
    <el-drawer v-model="approvalDetailVisible" title="审批详情" size="520px" class="pc-drawer approval-detail-drawer">
      <template v-if="approvalDetail">
        <div class="approval-detail-section">
          <h4 class="section-label">审批信息</h4>
          <div class="detail-row">
            <span class="detail-key">标题</span>
            <span class="detail-value">{{ approvalDetail.title }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-key">申请人</span>
            <span class="detail-value">{{ approvalDetail.requester_name || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-key">类型</span>
            <span class="detail-value">
              <el-tag size="small">{{ getApprovalTypeLabel(approvalDetail.approval_type) }}</el-tag>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-key">资源</span>
            <span class="detail-value">
              <el-tag size="small" type="info">{{ getResourceTypeLabel(approvalDetail.resource_type) }}</el-tag>
              <span class="arrow-sep">→</span>
              <el-tag size="small" :type="approvalDetail.target_scope === 'system' ? 'danger' : 'warning'">
                {{ approvalDetail.target_scope === 'system' ? '系统' : '组织' }}
              </el-tag>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-key">状态</span>
            <span class="detail-value">
              <el-tag :type="getApprovalStatusType(approvalDetail.status)" size="small">
                {{ getApprovalStatusLabel(approvalDetail.status) }}
              </el-tag>
            </span>
          </div>
          <div v-if="approvalDetail.description" class="detail-row">
            <span class="detail-key">说明</span>
            <span class="detail-value desc">{{ approvalDetail.description }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-key">提交时间</span>
            <span class="detail-value">{{ formatDate(approvalDetail.created_at) }}</span>
          </div>
          <div v-if="approvalDetail.reviewed_at" class="detail-row">
            <span class="detail-key">审批时间</span>
            <span class="detail-value">{{ formatDate(approvalDetail.reviewed_at) }}</span>
          </div>
          <div v-if="approvalDetail.review_comment" class="detail-row">
            <span class="detail-key">审批意见</span>
            <span class="detail-value comment">{{ approvalDetail.review_comment }}</span>
          </div>
        </div>

        <!-- Resource Content Preview -->
        <div class="approval-detail-section" v-if="resourceLoading || resourceContent">
          <h4 class="section-label">
            {{ getResourceTypeLabel(approvalDetail.resource_type) }} 内容预览
            <span class="resource-name-badge">{{ resourceName }}</span>
          </h4>
          <div v-if="resourceLoading" class="resource-loading">
            <el-icon class="is-loading"><Loading /></el-icon> 加载中...
          </div>
          <div v-else-if="resourceContent" class="resource-preview">
            <div class="resource-body">{{ resourceContent }}</div>
          </div>
          <div v-else class="resource-loading">无法加载资源内容</div>
        </div>

        <div class="approval-detail-actions">
          <el-button
            v-if="approvalDetail.status === 'pending' && canApprove(approvalDetail)"
            type="success"
            @click="openReviewDialog(approvalDetail, 'approve'); approvalDetailVisible = false"
          >
            <el-icon><Select /></el-icon>
            批准
          </el-button>
          <el-button
            v-if="approvalDetail.status === 'pending' && canApprove(approvalDetail)"
            type="danger"
            @click="openReviewDialog(approvalDetail, 'reject'); approvalDetailVisible = false"
          >
            <el-icon><Close /></el-icon>
            拒绝
          </el-button>
        </div>
      </template>

      <el-empty v-else description="加载中..." />
    </el-drawer>

    <!-- Task Detail Drawer -->
    <el-drawer v-model="detailVisible" :title="$t('common.details')" size="500px" class="pc-drawer">
      <el-descriptions :column="1" border v-if="currentTask">
        <el-descriptions-item :label="$t('common.name')">{{ currentTask.title }}</el-descriptions-item>
        <el-descriptions-item :label="$t('common.status')">
          <el-tag :type="getStatusType(currentTask.status)">{{ getStatusLabel(currentTask.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('task.priority')">
          <el-tag :type="getPriorityType(currentTask.priority)">{{ getPriorityLabel(currentTask.priority) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('common.type')">{{ getTypeLabel(currentTask.task_type) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('common.description')">{{ currentTask.description || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('common.time')">{{ formatDate(currentTask.created_at) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('task.started')">{{ currentTask.started_at ? formatDate(currentTask.started_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('task.completed')">{{ currentTask.completed_at ? formatDate(currentTask.completed_at) : '-' }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="currentTask?.output_data" class="output-section">
        <h4>{{ $t('common.details') }}</h4>
        <pre class="code-block">{{ JSON.stringify(currentTask.output_data, null, 2) }}</pre>
      </div>

      <div v-if="currentTask?.error_message" class="error-section">
        <h4>{{ $t('common.failed') }}</h4>
        <el-alert type="error" :closable="false">{{ currentTask.error_message }}</el-alert>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, User, Edit, VideoPlay, Select, Close, Delete, Refresh, View, Loading } from '@element-plus/icons-vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'
import { approvalsApi, type ApprovalResponse } from '@/api/approvals'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const userStore = useUserStore()

interface Task {
  id: number
  title: string
  description: string | null
  status: string
  priority: string
  task_type: string
  agent_id: number | null
  runner_id: number | null
  creator_id: number
  assignee_id: number | null
  input_data: any
  output_data: any
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  due_at: string | null
  created_at: string
  updated_at: string
}

const tasks = ref<Task[]>([])
const stats = ref({ total: 0, todo: 0, in_progress: 0, done: 0, cancelled: 0 })
const loading = ref(false)
const currentTab = ref('')
const filterPriority = ref('')
const filterType = ref('')
const searchKeyword = ref('')
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const currentTask = ref<Task | null>(null)

// Approval related
const activeMainTab = ref('tasks')
const approvals = ref<ApprovalResponse[]>([])
const loadingApprovals = ref(false)
const approvalStatusFilter = ref('pending')
const pendingApprovalCount = ref(0)
const reviewVisible = ref(false)
const reviewApproval = ref<ApprovalResponse | null>(null)
const reviewAction = ref<'approve' | 'reject'>('approve')
const reviewComment = ref('')
const reviewing = ref(false)
const approvalDetailVisible = ref(false)
const approvalDetail = ref<ApprovalResponse | null>(null)
const resourceLoading = ref(false)
const resourceContent = ref<string>('')
const resourceName = ref<string>('')

const form = reactive({
  id: 0,
  title: '',
  description: '',
  priority: 'normal',
  task_type: 'manual',
  due_at: null as Date | null
})

const rules = {
  title: [{ required: true, message: t('common.name'), trigger: 'blur' }]
}

const filteredTasks = computed(() => {
  if (!searchKeyword.value) return tasks.value
  const keyword = searchKeyword.value.toLowerCase()
  return tasks.value.filter(t =>
    t.title.toLowerCase().includes(keyword) ||
    (t.description?.toLowerCase().includes(keyword))
  )
})

function getPriorityLabel(p: string): string {
  const labels: Record<string, string> = {
    low: t('task.low'),
    normal: t('task.normal'),
    medium: t('task.normal'),
    high: t('task.high'),
    urgent: t('task.urgent')
  }
  return labels[p] || p
}

function getStatusLabel(s: string): string {
  const labels: Record<string, string> = {
    todo: t('task.todo'),
    in_progress: t('task.inProgress'),
    done: t('task.done'),
    cancelled: t('task.cancelled')
  }
  return labels[s] || s
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    manual: t('task.manual'),
    agent: t('task.agent'),
    cron: t('task.cron')
  }
  return labels[type] || type
}

const getPriorityType = (p: string) => {
  const types: Record<string, string> = { low: 'info', normal: 'info', high: 'warning', urgent: 'danger' }
  return types[p] || 'info'
}

const getStatusType = (s: string) => {
  const types: Record<string, string> = { todo: 'info', in_progress: 'warning', done: 'success', cancelled: 'danger' }
  return types[s] || 'info'
}

function formatDate(date: string) {
  return new Date(date).toLocaleString()
}

async function loadStats() {
  try {
    const res = await api.get('/tasks/stats')
    stats.value = res.data
  } catch (error) {
    console.error('Failed to load stats')
  }
}

async function loadTasks() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (currentTab.value && currentTab.value !== 'mine') params.append('status', currentTab.value)
    if (filterPriority.value) params.append('priority', filterPriority.value)
    if (filterType.value) params.append('task_type', filterType.value)

    const res = await api.get(`/tasks?${params.toString()}`)
    tasks.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadMyTasks() {
  currentTab.value = 'mine'
  loading.value = true
  try {
    const res = await api.get('/tasks/mine')
    tasks.value = res.data
  } finally {
    loading.value = false
  }
}

function filterTasks() {
  // Local filtering
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, { id: 0, title: '', description: '', priority: 'normal', task_type: 'manual', due_at: null })
  dialogVisible.value = true
}

function editTask(task: Task) {
  isEdit.value = true
  Object.assign(form, {
    id: task.id,
    title: task.title,
    description: task.description || '',
    priority: task.priority,
    task_type: task.task_type,
    due_at: task.due_at ? new Date(task.due_at) : null
  })
  dialogVisible.value = true
}

function showTaskDetail(task: Task) {
  currentTask.value = task
  detailVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const data = {
      title: form.title,
      description: form.description,
      priority: form.priority,
      task_type: form.task_type,
      due_at: form.due_at?.toISOString()
    }

    if (isEdit.value) {
      await api.put(`/tasks/${form.id}`, data)
      ElMessage.success(t('common.success'))
    } else {
      await api.post('/tasks', data)
      ElMessage.success(t('common.success'))
    }
    dialogVisible.value = false
    loadTasks()
    loadStats()
  } finally {
    submitting.value = false
  }
}

async function toggleTask(task: Task) {
  try {
    if (task.status === 'done') {
      await api.post(`/tasks/${task.id}/cancel`)
    } else {
      await api.post(`/tasks/${task.id}/complete`)
    }
    ElMessage.success(t('common.success'))
    loadTasks()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('common.failed'))
  }
}

async function startTask(task: Task) {
  try {
    await api.post(`/tasks/${task.id}/start`)
    ElMessage.success(t('common.success'))
    loadTasks()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('common.failed'))
  }
}

async function completeTask(task: Task) {
  try {
    await api.post(`/tasks/${task.id}/complete`)
    ElMessage.success(t('common.success'))
    loadTasks()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('common.failed'))
  }
}

async function cancelTask(task: Task) {
  try {
    await api.post(`/tasks/${task.id}/cancel`)
    ElMessage.success(t('common.success'))
    loadTasks()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('common.failed'))
  }
}

async function deleteTask(task: Task) {
  try {
    await api.delete(`/tasks/${task.id}`)
    ElMessage.success(t('common.success'))
    loadTasks()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('common.failed'))
  }
}

// ===== Approval Functions =====

async function loadApprovals() {
  loadingApprovals.value = true
  try {
    const params: Record<string, any> = {}
    if (approvalStatusFilter.value) {
      params.status_filter = approvalStatusFilter.value
    }
    const res = await approvalsApi.list(params)
    approvals.value = res.data
  } catch (error) {
    ElMessage.error(t('common.failed'))
  } finally {
    loadingApprovals.value = false
  }
}

async function loadPendingCount() {
  try {
    const res = await approvalsApi.getPendingCount()
    pendingApprovalCount.value = res.data.pending_count
  } catch (error) {
    console.error('Failed to load pending count')
  }
}

function canApprove(_approval: ApprovalResponse): boolean {
  // 管理员可以审批
  return userStore.isSuperAdmin || userStore.user?.role === 'org_admin'
}

function canCancel(approval: ApprovalResponse): boolean {
  // 只有提交者可以取消
  return approval.requester_id === userStore.user?.id
}

function openReviewDialog(approval: ApprovalResponse, action: 'approve' | 'reject') {
  reviewApproval.value = approval
  reviewAction.value = action
  reviewComment.value = ''
  reviewVisible.value = true
}

async function submitReview() {
  if (!reviewApproval.value) return
  reviewing.value = true
  try {
    const approved = reviewAction.value === 'approve'
    await approvalsApi.review(reviewApproval.value.id, { approved, review_comment: reviewComment.value })
    ElMessage.success(approved ? t('approval.approveSuccess') : t('approval.rejectSuccess'))
    reviewVisible.value = false
    loadApprovals()
    loadPendingCount()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('approval.approveFailed'))
  } finally {
    reviewing.value = false
  }
}

async function cancelApproval(approval: ApprovalResponse) {
  try {
    await ElMessageBox.confirm(t('approval.confirmCancel'), t('approval.cancel'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })

    await approvalsApi.cancel(approval.id)
    ElMessage.success(t('approval.cancelSuccess'))
    loadApprovals()
    loadPendingCount()
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error.response?.data?.detail || t('approval.cancelFailed'))
    }
  }
}

function getApprovalStatusType(status: string): string {
  const types: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    cancelled: 'info',
  }
  return types[status] || 'info'
}

function getApprovalStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: t('approval.pending'),
    approved: t('approval.approved'),
    rejected: t('approval.rejected'),
    cancelled: t('approval.cancelled'),
  }
  return labels[status] || status
}

function getApprovalTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    skill_to_org: t('approval.skillToOrg'),
    skill_to_system: t('approval.skillToSystem'),
    doc_to_org: t('approval.docToOrg'),
    doc_to_system: t('approval.docToSystem'),
  }
  return labels[type] || type
}

function getResourceTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    skill: '技能',
    wiki: 'Wiki',
    document: '文档',
  }
  return labels[type] || type
}

async function showApprovalDetail(approval: ApprovalResponse) {
  approvalDetail.value = approval
  approvalDetailVisible.value = true
  resourceContent.value = ''
  resourceLoading.value = true

  try {
    if (approval.resource_type === 'skill') {
      const [detailRes, contentRes] = await Promise.all([
        api.get(`/skills/${approval.resource_id}`),
        api.get(`/skills/${approval.resource_id}/content`),
      ])
      resourceName.value = detailRes.data.display_name || detailRes.data.name
      resourceContent.value = contentRes.data.content || ''
    } else if (approval.resource_type === 'wiki') {
      const res = await api.get(`/wiki/${approval.resource_id}`)
      resourceName.value = res.data.title || ''
      resourceContent.value = res.data.content || ''
    }
  } catch {
    resourceContent.value = ''
  } finally {
    resourceLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadTasks()
  loadPendingCount()
})
</script>

<style scoped lang="scss">
/* ===== Page Layout ===== */
.tasks-page {
  padding: 0;
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

  &:active {
    transform: translateY(0);
  }
}

.tasks-page {
  .stats-row {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;

    .stat-card {
      flex: 1;
      background: var(--pc-glass-bg);
      backdrop-filter: var(--pc-glass-blur);
      -webkit-backdrop-filter: var(--pc-glass-blur);
      border-radius: var(--pc-radius-md);
      padding: 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      border: 1px solid var(--pc-glass-border);
      position: relative;
      overflow: hidden;

      &::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: var(--pc-radius-md);
        border: 1px solid transparent;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
        pointer-events: none;
      }

      &:hover,
      &.active {
        border-color: var(--pc-border-glow);
        box-shadow: var(--pc-shadow-glow);

        &::before {
          border-color: var(--pc-primary);
        }
      }

      &.todo .stat-value {
        color: var(--pc-primary);
        text-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.5);
      }

      &.progress .stat-value {
        color: var(--pc-accent-orange);
        text-shadow: 0 0 12px rgba(var(--pc-accent-orange-rgb, 250, 173, 20), 0.5);
      }

      &.done .stat-value {
        color: var(--pc-accent-green);
        text-shadow: 0 0 12px rgba(var(--pc-accent-green-rgb, 82, 196, 26), 0.5);
      }

      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: var(--pc-primary);
        text-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.4);
      }

      .stat-label {
        font-size: 13px;
        color: var(--pc-text-muted);
        margin-top: 4px;
        letter-spacing: 0.5px;
      }

      &.add-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 2px dashed var(--pc-border);
        color: var(--pc-text-muted);
        background: transparent;

        &:hover {
          border-color: var(--pc-primary);
          color: var(--pc-primary);
          box-shadow: 0 0 20px rgba(var(--pc-primary-rgb), 0.15);
        }
      }
    }
  }

  .task-list-card {
    background: var(--pc-glass-bg);
    backdrop-filter: var(--pc-glass-blur);
    -webkit-backdrop-filter: var(--pc-glass-blur);
    border: 1px solid var(--pc-glass-border);
    border-radius: var(--pc-radius-lg);

    :deep(.el-card__header) {
      background: var(--pc-bg-deep);
      border-bottom: 1px solid var(--pc-border);
    }

    :deep(.el-card__body) {
      background: var(--pc-bg-surface);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .filter-group {
        display: flex;
        gap: 12px;
      }
    }

    .task-list {
      .task-item {
        display: flex;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid var(--pc-border);
        gap: 12px;
        transition: all 0.3s ease;

        &:hover {
          background: rgba(var(--pc-primary-rgb), 0.04);
        }

        &.done {
          opacity: 0.5;

          .task-title {
            text-decoration: line-through;
            color: var(--pc-text-muted);
          }
        }

        .task-checkbox {
          padding-top: 4px;
        }

        .task-content {
          flex: 1;
          cursor: pointer;

          .task-header {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 8px;

            .task-title {
              font-weight: 500;
              color: var(--pc-text-primary);
            }

            .task-tags {
              display: flex;
              gap: 6px;
              align-items: center;
            }
          }

          .task-meta {
            font-size: 13px;
            color: var(--pc-text-muted);
          }
        }

        .task-actions {
          opacity: 0;
          transition: opacity 0.3s ease;

          :deep(.el-button) {
            transition: box-shadow 0.3s ease;

            &:hover {
              box-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.4);
            }
          }
        }

        &:hover .task-actions {
          opacity: 1;
        }
      }
    }
  }

  .output-section,
  .error-section {
    margin-top: 24px;

    h4 {
      margin-bottom: 12px;
      color: var(--pc-text-primary);
    }

    .code-block {
      background: var(--pc-bg-deep);
      padding: 12px;
      border-radius: var(--pc-radius-sm);
      font-size: 12px;
      overflow-x: auto;
      border: 1px solid var(--pc-border);
      color: var(--pc-accent-green);
    }
  }
}

// Dialog cyberpunk glass style
:global(.pc-dialog) {
  .el-dialog {
    background: var(--pc-glass-bg);
    backdrop-filter: var(--pc-glass-blur);
    -webkit-backdrop-filter: var(--pc-glass-blur);
    border: 1px solid var(--pc-glass-border);
    border-radius: var(--pc-radius-lg);
    box-shadow: var(--pc-shadow-lg), var(--pc-shadow-glow);

    .el-dialog__header {
      border-bottom: 1px solid var(--pc-border);
    }

    .el-dialog__title {
      color: var(--pc-text-primary);
    }
  }
}

// Drawer cyberpunk glass style
:global(.pc-drawer) {
  .el-drawer {
    background: var(--pc-glass-bg);
    backdrop-filter: var(--pc-glass-blur);
    -webkit-backdrop-filter: var(--pc-glass-blur);
    border-left: 1px solid var(--pc-glass-border);
    box-shadow: var(--pc-shadow-lg);

    .el-drawer__header {
      border-bottom: 1px solid var(--pc-border);
      color: var(--pc-text-primary);
    }
  }
}

// Approval styles
.main-tabs {
  margin-top: 16px;

  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }

  .tab-label-wrap {
    position: relative;
  }

  :deep(.tab-badge) {
    position: absolute;
    top: -4px;
    right: -20px;
  }
}

.approval-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.approval-list-card {
  background: var(--pc-bg-surface);
  border: 1px solid var(--pc-border);
  border-radius: var(--pc-radius-lg);
}

.approval-title-link {
  cursor: pointer;
  color: var(--pc-primary);
  font-weight: 500;
  transition: color 0.2s;

  &:hover {
    color: var(--pc-primary-light, var(--pc-primary));
    text-decoration: underline;
  }
}

.requester-name {
  color: var(--pc-text-secondary);
  font-size: 13px;
}

.arrow-sep {
  margin: 0 4px;
  color: var(--pc-text-muted);
  font-size: 11px;
}

.approval-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* ===== Approval Detail Drawer ===== */
.approval-detail-drawer {
  .approval-detail-section {
    margin-bottom: 20px;

    .section-label {
      font-size: 13px;
      font-weight: 600;
      color: var(--pc-text-primary);
      margin-bottom: 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--pc-border);
      letter-spacing: 0.5px;
    }

    .detail-row {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 8px 0;

      .detail-key {
        width: 70px;
        flex-shrink: 0;
        font-size: 12px;
        color: var(--pc-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.3px;
      }

      .detail-value {
        flex: 1;
        font-size: 13px;
        color: var(--pc-text-primary);
        line-height: 1.5;

        &.desc {
          color: var(--pc-text-secondary);
          font-size: 12px;
          line-height: 1.6;
        }

        &.comment {
          background: rgba(var(--pc-primary-rgb), 0.06);
          border-left: 2px solid var(--pc-primary);
          padding: 8px 12px;
          border-radius: 0 var(--pc-radius-sm) var(--pc-radius-sm) 0;
          font-size: 12px;
          color: var(--pc-text-secondary);
        }
      }
    }
  }

  .approval-detail-actions {
    padding-top: 16px;
    border-top: 1px solid var(--pc-border);
    display: flex;
    gap: 8px;

    :deep(.el-button) {
      font-weight: 500;
    }
  }

  .resource-loading {
    text-align: center;
    padding: 24px;
    color: var(--pc-text-muted);
    font-size: 13px;
  }

  .resource-preview {
    .resource-body {
      background: var(--pc-bg-deep);
      border: 1px solid var(--pc-glass-border);
      border-radius: var(--pc-radius-md);
      padding: 16px;
      font-size: 12px;
      line-height: 1.7;
      color: var(--pc-text-secondary);
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 400px;
      overflow-y: auto;
      font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', Consolas, monospace;
    }
  }

  .resource-name-badge {
    font-size: 12px;
    font-weight: 400;
    color: var(--pc-primary);
    background: rgba(var(--pc-primary-rgb), 0.08);
    padding: 2px 10px;
    border-radius: 10px;
    margin-left: 8px;
  }
}

:deep(.pc-data-table tbody tr) {
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: rgba(var(--pc-primary-rgb), 0.04);
  }
}

.text-muted {
  color: var(--pc-text-muted);
  font-size: 12px;
}

/* ===== Review Dialog ===== */
.review-dialog {
  .review-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .review-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--pc-glass-border);
    border-radius: var(--pc-radius-md);

    &-label {
      flex-shrink: 0;
      width: 80px;
      font-size: 12px;
      color: var(--pc-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding-top: 2px;
    }

    &-value {
      flex: 1;
      font-weight: 500;
      color: var(--pc-text-primary);
      font-size: 14px;

      &.desc-text {
        font-weight: 400;
        color: var(--pc-text-secondary);
        font-size: 13px;
        line-height: 1.5;
      }
    }
  }

  .review-comment-section {
    margin-top: 12px;

    .review-card-label {
      font-size: 12px;
      color: var(--pc-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }

    .review-comment-input {
      :deep(.el-textarea__inner) {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--pc-glass-border);
        border-radius: var(--pc-radius-md);
        color: var(--pc-text-primary);
        font-size: 13px;
        resize: none;
        transition: border-color 0.3s, box-shadow 0.3s;

        &::placeholder {
          color: var(--pc-text-muted);
        }

        &:focus {
          border-color: var(--pc-primary);
          box-shadow: 0 0 0 2px rgba(var(--pc-primary-rgb), 0.15);
        }
      }
    }
  }

  .review-submit-btn {
    min-width: 100px;
    font-weight: 500;
    letter-spacing: 0.5px;
  }
}
</style>
