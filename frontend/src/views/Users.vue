<template>
  <div class="users-page">
    <div class="page-header">
      <el-button class="pc-btn-glow" type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        {{ $t('user.create') }}
      </el-button>
    </div>

    <!-- User list -->
    <el-card class="pc-glass-card" shadow="never">
      <div class="filter-bar">
        <el-select v-model="filterOrg" :placeholder="$t('user.filterOrg')" clearable size="small" class="pc-filter-select" @change="loadUsers">
          <el-option v-for="org in orgOptions" :key="org.id" :label="org.name" :value="org.id" />
        </el-select>
        <el-input v-model="searchKeyword" :placeholder="$t('user.searchPlaceholder')" prefix-icon="Search" clearable size="small" class="pc-filter-input" />
      </div>

      <div class="table-scroll">
        <el-table :data="filteredUsers" v-loading="loading" class="pc-data-table" style="width: 100%">
        <template #empty>
          <el-empty :description="$t('common.noData')" />
        </template>
        <el-table-column prop="id" :label="$t('user.id')" width="70" sortable />
        <el-table-column label="User" min-width="180">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="32" :src="row.avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-info">
                <div class="user-name">{{ row.display_name || row.username }}</div>
                <div class="user-username">@{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" :label="$t('user.email')" min-width="180" />
        <el-table-column :label="$t('user.organization')" min-width="140">
          <template #default="{ row }">
            <span v-if="row.organization_id">{{ getOrgName(row.organization_id) }}</span>
            <span v-else class="text-muted">{{ $t('user.unassigned') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="role" :label="$t('user.role')" width="140">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" class="pc-role-tag">{{ getRoleName(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" size="small" class="pc-status-tag pc-status-active">{{ $t('user.active') }}</el-tag>
            <el-tag v-else type="danger" size="small" class="pc-status-tag pc-status-disabled">{{ $t('user.disabled') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('user.created')" min-width="140">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="120">
          <template #default="{ row }">
            <div class="action-btns">
              <el-tooltip :content="$t('common.edit')" placement="top">
                <el-button size="small" circle class="pc-action-icon" @click="showEditDialog(row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('user.resetPassword')" placement="top">
                <el-button size="small" circle class="pc-action-icon" @click="resetPassword(row)">
                  <el-icon><Key /></el-icon>
                </el-button>
              </el-tooltip>
              <el-popconfirm :title="$t('user.confirmDelete')" @confirm="deleteUser(row)" v-if="row.id !== 1">
                <template #reference>
                  <el-button size="small" circle type="danger" class="pc-action-icon">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
      </div>
    </el-card>

    <!-- Create/Edit dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('user.edit') : $t('user.create')" width="500px" class="pc-dialog">
      <el-form :model="form" label-width="120px" ref="formRef" :rules="rules" class="pc-form">
        <el-form-item :label="$t('user.username')" prop="username">
          <el-input v-model="form.username" :placeholder="$t('user.usernamePlaceholder')" :disabled="isEdit" />
        </el-form-item>
        <el-form-item :label="$t('user.email')" prop="email">
          <el-input v-model="form.email" :placeholder="$t('user.emailPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('user.displayName')" prop="display_name">
          <el-input v-model="form.display_name" :placeholder="$t('user.displayNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('user.password')" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password :placeholder="$t('user.passwordPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('user.role')" prop="role">
          <el-select v-model="form.role" style="width: 100%" :placeholder="$t('user.rolePlaceholder')">
            <el-option :label="$t('user.user')" value="user" />
            <el-option :label="$t('user.orgAdmin')" value="org_admin" />
            <el-option :label="$t('user.superAdmin')" value="super_admin" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('user.organization')">
          <el-select v-model="form.organization_id" style="width: 100%" clearable :placeholder="$t('user.orgPlaceholder')">
            <el-option v-for="org in orgOptions" :key="org.id" :label="org.name" :value="org.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.status')">
          <el-switch v-model="form.is_active" :active-text="$t('user.active')" :inactive-text="$t('user.disabled')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" class="pc-btn-cancel">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting" class="pc-btn-glow">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, User, Edit, Key, Delete } from '@element-plus/icons-vue'
import { api } from '../api'
import { organizationApi } from '@/api/organization'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface UserItem {
  id: number
  username: string
  email: string
  display_name: string
  avatar: string
  role: string
  is_active: boolean
  organization_id: string | null
  created_at: string
}

interface OrgOption {
  id: string
  name: string
  code: string
}

const users = ref<UserItem[]>([])
const orgOptions = ref<OrgOption[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const filterOrg = ref('')
const searchKeyword = ref('')

const form = reactive({
  id: 0,
  username: '',
  email: '',
  display_name: '',
  password: '',
  role: 'user',
  is_active: true,
  organization_id: null as string | null
})

const passwordRules = computed(() => {
  if (isEdit.value) return []
  return [
    { required: true, message: t('user.enterPassword'), trigger: 'blur' },
    { min: 6, message: t('user.passwordLength'), trigger: 'blur' }
  ]
})

const rules = computed(() => ({
  username: [
    { required: true, message: t('user.enterUsername'), trigger: 'blur' },
    { min: 3, max: 50, message: t('user.usernameLength'), trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: t('user.validEmail'), trigger: 'blur' }
  ],
  password: passwordRules.value,
  role: [
    { required: true, message: t('user.selectRole'), trigger: 'change' }
  ]
}))

const filteredUsers = computed(() => {
  if (!searchKeyword.value) return users.value
  const kw = searchKeyword.value.toLowerCase()
  return users.value.filter(u =>
    u.username.toLowerCase().includes(kw) ||
    u.email.toLowerCase().includes(kw) ||
    (u.display_name && u.display_name.toLowerCase().includes(kw))
  )
})

function getOrgName(orgId: string): string {
  const org = orgOptions.value.find(o => o.id === orgId)
  return org ? org.name : orgId
}

function getRoleType(role: string) {
  const types: Record<string, string> = { super_admin: 'danger', org_admin: 'warning', user: 'info' }
  return types[role] || 'info'
}

function getRoleName(role: string) {
  const names: Record<string, string> = { super_admin: t('user.superAdmin'), org_admin: t('user.orgAdmin'), user: t('user.user') }
  return names[role] || role
}

async function loadOrgs() {
  try {
    const res = await organizationApi.simple()
    orgOptions.value = res.data
  } catch { /* ignore */ }
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await api.get('/users')
    let list: UserItem[] = res.data.sort((a: UserItem, b: UserItem) => a.id - b.id)
    if (filterOrg.value) {
      list = list.filter(u => u.organization_id === filterOrg.value)
    }
    users.value = list
  } catch {
    ElMessage.error(t('user.loadFailed'))
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, { id: 0, username: '', email: '', display_name: '', password: '', role: 'user', is_active: true, organization_id: null })
  dialogVisible.value = true
}

function showEditDialog(user: UserItem) {
  isEdit.value = true
  Object.assign(form, {
    id: user.id, username: user.username, email: user.email,
    display_name: user.display_name, password: '', role: user.role,
    is_active: user.is_active, organization_id: user.organization_id
  })
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }

  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/users/${form.id}`, {
        email: form.email, display_name: form.display_name,
        role: form.role, is_active: form.is_active,
        organization_id: form.organization_id
      })
      ElMessage.success(t('user.updated'))
    } else {
      await api.post('/users', {
        username: form.username, email: form.email,
        display_name: form.display_name, password: form.password,
        role: form.role, is_active: form.is_active,
        organization_id: form.organization_id
      })
      ElMessage.success(t('user.createdSuccess'))
    }
    dialogVisible.value = false
    loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('user.operationFailed'))
  } finally {
    submitting.value = false
  }
}

async function resetPassword(user: UserItem) {
  try {
    const { value } = await ElMessageBox.prompt(t('user.enterNewPassword'), t('user.resetPassword'), {
      confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'),
      inputPattern: /^.{6,}$/, inputErrorMessage: t('user.passwordLength')
    })
    await api.put(`/users/${user.id}/password`, { password: value })
    ElMessage.success(t('user.passwordResetFor', { username: user.username }))
  } catch { /* cancel */ }
}

async function deleteUser(user: UserItem) {
  if (user.id === 1) { ElMessage.warning(t('user.cannotDeleteSuperAdmin')); return }
  await api.delete(`/users/${user.id}`)
  ElMessage.success(t('user.deleted'))
  loadUsers()
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('en-US')
}

onMounted(() => {
  loadOrgs()
  loadUsers()
})
</script>

<style scoped lang="scss">
.users-page {
  min-height: 100%;
  padding: 20px;
}

/* ── Page header ── */
.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;
}

/* ── Glow button ── */
.pc-btn-glow {
  background: var(--pc-gradient-primary) !important;
  border: none !important;
  color: #fff !important;
  font-weight: 600;
  border-radius: var(--pc-radius-md) !important;
  box-shadow: var(--pc-shadow-glow);
  transition: all 0.25s ease;

  &:hover {
    box-shadow: 0 0 20px rgba(var(--pc-primary-rgb), 0.5), 0 0 40px rgba(var(--pc-primary-rgb), 0.2);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
}

.pc-btn-cancel {
  border-color: var(--pc-border) !important;
  color: var(--pc-text-secondary) !important;
  border-radius: var(--pc-radius-md) !important;
  background: var(--pc-bg-surface) !important;

  &:hover {
    border-color: var(--pc-border-hover) !important;
    color: var(--pc-text-primary) !important;
  }
}

/* ── Glass card ── */
.pc-glass-card {
  background: var(--pc-glass-bg) !important;
  border: 1px solid var(--pc-glass-border) !important;
  border-radius: var(--pc-radius-lg) !important;
  backdrop-filter: var(--pc-glass-blur);
  box-shadow: var(--pc-shadow-md);
  overflow: hidden;

  :deep(.el-card__body) {
    padding: 20px 24px;
  }
}

/* ── Filter bar ── */
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--pc-bg-surface);
  border: 1px solid var(--pc-border);
  border-radius: var(--pc-radius-md);
}

.pc-filter-select,
.pc-filter-input {
  :deep(.el-input__wrapper),
  :deep(.el-select__wrapper) {
    background: var(--pc-bg-elevated) !important;
    border: 1px solid var(--pc-border) !important;
    border-radius: var(--pc-radius-sm) !important;
    box-shadow: none !important;
    color: var(--pc-text-primary);

    &:hover {
      border-color: var(--pc-border-hover) !important;
    }

    &.is-focus {
      border-color: var(--pc-primary) !important;
      box-shadow: 0 0 0 1px rgba(var(--pc-primary-rgb), 0.25) !important;
    }
  }

  :deep(.el-input__inner) {
    color: var(--pc-text-primary);
  }

  :deep(.el-input__inner::placeholder) {
    color: var(--pc-text-muted);
  }
}

/* ── Table Scroll ── */
.table-scroll {
  overflow-x: auto;
  width: 100%;
}

/* ── Table ── */
.pc-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--pc-bg-surface);
  --el-table-row-hover-bg-color: rgba(var(--pc-primary-rgb), 0.04);
  --el-table-border-color: var(--pc-border);
  --el-table-text-color: var(--pc-text-primary);
  --el-table-header-text-color: var(--pc-text-secondary);

  :deep(th.el-table__cell) {
    background: var(--pc-bg-surface) !important;
    color: var(--pc-text-secondary) !important;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--pc-border) !important;
  }

  :deep(td.el-table__cell) {
    border-bottom: 1px solid var(--pc-border) !important;
    color: var(--pc-text-primary);
  }

  :deep(.el-table__row:hover > td.el-table__cell) {
    background: rgba(var(--pc-primary-rgb), 0.04) !important;
  }

  :deep(.el-table__empty-block) {
    background: transparent;
  }

  /* Stripe rows */
  :deep(.el-table__row--striped td.el-table__cell) {
    background: rgba(var(--pc-primary-rgb), 0.02) !important;
  }
}

/* ── Action buttons (icon only) ── */
.action-btns {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pc-action-icon {
  background: transparent !important;
  border: 1px solid var(--pc-border) !important;
  color: var(--pc-text-secondary) !important;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--pc-primary) !important;
    color: var(--pc-primary) !important;
    background: rgba(var(--pc-primary-rgb), 0.08) !important;
  }

  &.el-button--danger {
    border-color: rgba(var(--pc-accent-red), 0.3) !important;
    color: var(--pc-accent-red) !important;

    &:hover {
      border-color: var(--pc-accent-red) !important;
      background: rgba(var(--pc-accent-red), 0.1) !important;
    }
  }
}

/* ── User cell ── */
.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;

  .user-info {
    .user-name {
      font-weight: 600;
      color: var(--pc-text-primary);
      font-size: 13px;
    }

    .user-username {
      font-size: 12px;
      color: var(--pc-text-muted);
    }
  }
}

.text-muted {
  color: var(--pc-text-muted) !important;
  font-size: 12px;
}

/* ── Role tags ── */
.pc-role-tag {
  border-radius: var(--pc-radius-sm);
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.3px;
  border: none;

  &.el-tag--danger {
    background: rgba(var(--pc-accent-red), 0.12) !important;
    color: var(--pc-accent-red) !important;
  }

  &.el-tag--warning {
    background: rgba(var(--pc-accent-orange), 0.12) !important;
    color: var(--pc-accent-orange) !important;
  }

  &.el-tag--info {
    background: rgba(var(--pc-accent-purple), 0.12) !important;
    color: var(--pc-accent-purple) !important;
  }
}

/* ── Status tags ── */
.pc-status-tag {
  border-radius: var(--pc-radius-sm);
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.3px;
  border: none;
}

.pc-status-active {
  background: rgba(var(--pc-accent-green), 0.12) !important;
  color: var(--pc-accent-green) !important;
}

.pc-status-disabled {
  background: rgba(var(--pc-accent-red), 0.12) !important;
  color: var(--pc-accent-red) !important;
}

/* ── Action buttons ── */
.pc-action-btn {
  font-size: 12px !important;
  font-weight: 500;
  letter-spacing: 0.2px;
  transition: all 0.2s ease;

  &:hover {
    text-shadow: 0 0 8px rgba(var(--pc-primary-rgb), 0.4);
  }
}

/* ── Dialog ── */
.pc-dialog {
  :deep(.el-dialog) {
    background: var(--pc-glass-bg) !important;
    border: 1px solid var(--pc-glass-border) !important;
    border-radius: var(--pc-radius-lg) !important;
    backdrop-filter: var(--pc-glass-blur);
    box-shadow: var(--pc-shadow-lg), var(--pc-shadow-glow);
  }

  :deep(.el-dialog__header) {
    border-bottom: 1px solid var(--pc-border);
    padding: 16px 24px;
    margin-right: 0;

    .el-dialog__title {
      color: var(--pc-text-primary) !important;
      font-weight: 700;
      font-size: 16px;
    }
  }

  :deep(.el-dialog__body) {
    padding: 24px;
  }

  :deep(.el-dialog__footer) {
    border-top: 1px solid var(--pc-border);
    padding: 12px 24px;
  }
}

/* ── Form inside dialog ── */
.pc-form {
  :deep(.el-form-item__label) {
    color: var(--pc-text-secondary) !important;
    font-weight: 500;
    font-size: 13px;
  }

  :deep(.el-input__wrapper) {
    background: var(--pc-bg-elevated) !important;
    border: 1px solid var(--pc-border) !important;
    border-radius: var(--pc-radius-sm) !important;
    box-shadow: none !important;

    &:hover {
      border-color: var(--pc-border-hover) !important;
    }

    &.is-focus {
      border-color: var(--pc-primary) !important;
      box-shadow: 0 0 0 1px rgba(var(--pc-primary-rgb), 0.25) !important;
    }
  }

  :deep(.el-input__inner) {
    color: var(--pc-text-primary);
  }

  :deep(.el-input__inner::placeholder) {
    color: var(--pc-text-muted);
  }

  :deep(.el-select__wrapper) {
    background: var(--pc-bg-elevated) !important;
    border: 1px solid var(--pc-border) !important;
    border-radius: var(--pc-radius-sm) !important;
    box-shadow: none !important;

    &:hover {
      border-color: var(--pc-border-hover) !important;
    }

    &.is-focus {
      border-color: var(--pc-primary) !important;
      box-shadow: 0 0 0 1px rgba(var(--pc-primary-rgb), 0.25) !important;
    }
  }

  :deep(.el-switch) {
    --el-switch-on-color: var(--pc-accent-green);
    --el-switch-off-color: var(--pc-accent-red);
  }
}
</style>
