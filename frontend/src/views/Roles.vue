<template>
  <div class="roles-page">
    <div class="page-header">
      <!-- 不允许新建角色，只保留系统预设的三个角色 -->
    </div>

    <div class="roles-container" v-loading="loading">
      <div class="roles-sidebar">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>{{ $t('role.roleList') }}</span>
              <el-tag type="info" size="small">{{ roles.length }} {{ $t('role.count') }}</el-tag>
            </div>
          </template>

          <div class="role-list">
            <div
              v-for="role in roles"
              :key="role.id"
              class="role-item"
              :class="{ active: currentRole?.id === role.id }"
              @click="selectRole(role)"
            >
              <div class="role-icon">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="role-info">
                <div class="role-name">{{ role.name }}</div>
                <div class="role-code">{{ role.code }}</div>
              </div>
              <el-tag v-if="role.is_system" type="warning" size="small">{{ $t('role.system') }}</el-tag>
            </div>

            <el-empty v-if="roles.length === 0" :description="$t('role.noRoles')" :image-size="60" />
          </div>
        </el-card>
      </div>

      <div class="roles-content">
        <el-card class="role-detail-card" shadow="never" v-if="currentRole">
          <template #header>
            <div class="card-header">
              <div class="role-title">
                <span class="name">{{ currentRole.name }}</span>
                <el-tag :type="currentRole.is_active ? 'success' : 'danger'" size="small">
                  {{ currentRole.is_active ? $t('role.enable') : $t('role.disable') }}
                </el-tag>
              </div>
              <div class="pc-action-group">
                <el-button size="small" @click="showEditDialog(currentRole)" :disabled="currentRole.is_system && !isSuperAdmin">
                  <el-icon><Edit /></el-icon>
                  {{ $t('common.edit') }}
                </el-button>
                <el-button size="small" type="danger" @click="deleteRole(currentRole)" :disabled="currentRole.is_system">
                  <el-icon><Delete /></el-icon>
                  {{ $t('common.delete') }}
                </el-button>
              </div>
            </div>
          </template>

          <div class="section">
            <div class="section-title">{{ $t('role.basicInfo') }}</div>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item :label="$t('role.roleName')">{{ currentRole.name }}</el-descriptions-item>
              <el-descriptions-item :label="$t('role.roleCode')">{{ currentRole.code }}</el-descriptions-item>
              <el-descriptions-item :label="$t('role.description')">{{ currentRole.description || '-' }}</el-descriptions-item>
              <el-descriptions-item :label="$t('role.createdAt')">{{ formatDate(currentRole.created_at) }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="section">
            <div class="section-title">
              <span>{{ $t('role.permConfig') }}</span>
              <el-button size="small" @click="showPermDialog" :disabled="currentRole.is_system && !isSuperAdmin">
                <el-icon><Edit /></el-icon>
                {{ $t('role.editPerm') }}
              </el-button>
            </div>

            <div class="permission-tree">
              <div v-for="module in permissionModules" :key="module.key" class="permission-module">
                <div class="module-header">
                  <el-checkbox
                    :model-value="isModuleChecked(module.key)"
                    :indeterminate="isModuleIndeterminate(module.key)"
                    @change="toggleModule(module.key, $event)"
                    :disabled="currentRole.is_system && !isSuperAdmin"
                  >
                    <span class="module-name">{{ module.name }}</span>
                  </el-checkbox>
                  <el-tag type="info" size="small">{{ getModulePermCount(module.key) }}/{{ module.permissions.length }}</el-tag>
                </div>
                <div class="module-perms">
                  <el-checkbox
                    v-for="perm in module.permissions"
                    :key="perm.key"
                    :model-value="hasPermission(module.key, perm.key)"
                    :label="`${module.key}:${perm.key}`"
                    :disabled="currentRole.is_system && !isSuperAdmin"
                    @change="togglePermission(module.key, perm.key, $event)"
                  >
                    {{ perm.name }}
                  </el-checkbox>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card v-else class="role-detail-card empty-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>{{ $t('role.roleDetail') }}</span>
            </div>
          </template>
          <div class="empty-state">
            <el-icon :size="64" class="empty-icon"><UserFilled /></el-icon>
            <p>{{ $t('role.selectRole') }}</p>
          </div>
        </el-card>
      </div>
    </div>

    <!-- Create/Edit Role Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('role.editRole') : $t('role.newRole')" width="500px">
      <el-form :model="form" label-width="80px" ref="formRef" :rules="rules">
        <el-form-item :label="$t('role.roleName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('role.enterRoleName')" />
        </el-form-item>
        <el-form-item :label="$t('role.roleCode')" prop="code">
          <el-input v-model="form.code" :placeholder="$t('role.enterRoleCode')" :disabled="isEdit" />
          <div class="form-tip">{{ $t('role.roleCodeTip') }}</div>
        </el-form-item>
        <el-form-item :label="$t('role.description')">
          <el-input v-model="form.description" type="textarea" :rows="2" :placeholder="$t('role.description')" />
        </el-form-item>
        <el-form-item :label="$t('common.status')">
          <el-radio-group v-model="form.is_active">
            <el-radio :value="true">{{ $t('role.enable') }}</el-radio>
            <el-radio :value="false">{{ $t('role.disable') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('role.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">{{ $t('role.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Edit Permissions Dialog -->
    <el-dialog v-model="permDialogVisible" :title="$t('role.editPerm')" width="600px">
      <div class="perm-edit-content">
        <el-tree
          ref="permTreeRef"
          :data="permissionTreeData"
          show-checkbox
          node-key="key"
          default-expand-all
          :default-checked-keys="checkedPermissions"
          check-strictly
        />
      </div>
      <template #footer>
        <el-button @click="permDialogVisible = false">{{ $t('role.cancel') }}</el-button>
        <el-button type="primary" @click="savePermissions" :loading="savingPerms">{{ $t('role.savePerms') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { UserFilled, Edit, Delete } from '@element-plus/icons-vue'
import { api } from '../api'
import { useUserStore } from '../stores/user'

const { t: $t, locale } = useI18n()
const userStore = useUserStore()

const isSuperAdmin = computed(() => userStore.user?.role === 'super_admin')

interface Role {
  id: number
  name: string
  code: string
  description: string | null
  permissions: Record<string, string[]> | null
  is_system: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

const roles = ref<Role[]>([])
const currentRole = ref<Role | null>(null)
const loading = ref(false)
const dialogVisible = ref(false)
const permDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const savingPerms = ref(false)
const formRef = ref<FormInstance>()
const permTreeRef = ref()

const form = reactive({
  id: 0,
  name: '',
  code: '',
  description: '',
  is_active: true
})

const rules = computed(() => ({
  name: [{ required: true, message: $t('role.enterRoleName'), trigger: 'blur' }],
  code: [
    { required: true, message: $t('role.enterRoleCode'), trigger: 'blur' },
    { pattern: /^[a-z_]+$/, message: $t('role.roleCodeFormat'), trigger: 'blur' }
  ]
}))

// Permission module config
const permissionModules = computed(() => [
  {
    key: 'dashboard', name: '仪表盘',
    permissions: [{ key: 'view', name: '查看' }]
  },
  {
    key: 'chat', name: '对话',
    permissions: [
      { key: 'view', name: '查看' },
      { key: 'create', name: '发送消息' },
      { key: 'delete', name: '删除会话' }
    ]
  },
  {
    key: 'agent', name: '智能体',
    permissions: [
      { key: 'view', name: '查看' }, { key: 'create', name: '创建' },
      { key: 'edit', name: '编辑' }, { key: 'delete', name: '删除' },
      { key: 'execute', name: '执行' }
    ]
  },
  {
    key: 'skill', name: '技能',
    permissions: [
      { key: 'view', name: '查看' }, { key: 'create', name: '创建' },
      { key: 'edit', name: '编辑' }, { key: 'delete', name: '删除' }
    ]
  },
  {
    key: 'memory', name: '记忆系统',
    permissions: [
      { key: 'view', name: '查看' }, { key: 'create', name: '创建' },
      { key: 'edit', name: '编辑' }, { key: 'delete', name: '删除' }
    ]
  },
  {
    key: 'knowledge', name: '知识库',
    permissions: [
      { key: 'view', name: '查看' }, { key: 'create', name: '创建' },
      { key: 'edit', name: '编辑' }, { key: 'delete', name: '删除' },
      { key: 'upload', name: '上传' }
    ]
  },
  {
    key: 'runner', name: 'Runner',
    permissions: [
      { key: 'view', name: '查看' }, { key: 'approve', name: '审批' },
      { key: 'delete', name: '删除' }
    ]
  },
  {
    key: 'system', name: '系统管理',
    permissions: [
      { key: 'ai_config', name: 'AI配置' }, { key: 'role', name: '角色管理' },
      { key: 'user', name: '用户管理' }, { key: 'settings', name: '系统设置' }
    ]
  }
])

// Permission tree data
const permissionTreeData = computed(() => {
  return permissionModules.value.map(module => ({
    key: module.key,
    label: module.name,
    children: module.permissions.map(perm => ({
      key: `${module.key}:${perm.key}`,
      label: perm.name
    }))
  }))
})

// Convert backend { codes: [...] } to frontend { module: [perm, ...] }
const currentPerms = computed(() => {
  if (!currentRole.value?.permissions) return {} as Record<string, string[]>
  const codes = (currentRole.value.permissions as any).codes || []
  // Handle wildcard
  if (codes.includes('*')) {
    const all: Record<string, string[]> = {}
    for (const mod of permissionModules.value) {
      all[mod.key] = mod.permissions.map(p => p.key)
    }
    return all
  }
  const result: Record<string, string[]> = {}
  for (const code of codes) {
    const idx = code.indexOf(':')
    if (idx === -1) continue
    const module = code.substring(0, idx)
    const perm = code.substring(idx + 1)
    if (!result[module]) result[module] = []
    result[module].push(perm)
  }
  return result
})

// Currently checked permissions
const checkedPermissions = computed(() => {
  const keys: string[] = []
  for (const [module, perms] of Object.entries(currentPerms.value)) {
    for (const perm of perms) {
      keys.push(`${module}:${perm}`)
    }
  }
  return keys
})

function hasPermission(module: string, perm: string): boolean {
  const perms = currentPerms.value[module]
  if (!perms) return false
  return perms.includes('*') || perms.includes(perm)
}

function isModuleChecked(module: string): boolean {
  const perms = currentPerms.value[module]
  if (!perms) return false
  if (perms.includes('*')) return true
  const modulePerms = permissionModules.value.find(m => m.key === module)
  if (!modulePerms) return false
  return modulePerms.permissions.every(p => perms.includes(p.key))
}

function isModuleIndeterminate(module: string): boolean {
  const modulePerms = permissionModules.value.find(m => m.key === module)
  if (!modulePerms) return false
  const checkedCount = modulePerms.permissions.filter(p => hasPermission(module, p.key)).length
  return checkedCount > 0 && checkedCount < modulePerms.permissions.length
}

function getModulePermCount(module: string): number {
  const perms = currentPerms.value[module]
  if (!perms) return 0
  if (perms.includes('*')) {
    return permissionModules.value.find(m => m.key === module)?.permissions.length || 0
  }
  return perms.length
}

// Build codes array from currentPerms and convert to backend format
function permsToCodes(): string[] {
  const codes: string[] = []
  for (const [module, perms] of Object.entries(currentPerms.value)) {
    for (const perm of perms) {
      codes.push(`${module}:${perm}`)
    }
  }
  return codes
}

function toggleModule(module: string, checked: boolean) {
  if (!currentRole.value || currentRole.value.is_system) return

  const modulePerms = permissionModules.value.find(m => m.key === module)
  if (!modulePerms) return

  const codes = permsToCodes().filter(c => !c.startsWith(module + ':'))
  if (checked) {
    for (const p of modulePerms.permissions) {
      codes.push(`${module}:${p.key}`)
    }
  }

  if (!currentRole.value.permissions) {
    currentRole.value.permissions = {} as any
  }
  (currentRole.value.permissions as any).codes = codes

  savePermissionsToBackend()
}

function togglePermission(module: string, perm: string, checked: boolean) {
  if (!currentRole.value || currentRole.value.is_system) return

  const codes = permsToCodes()
  const key = `${module}:${perm}`

  if (checked) {
    if (!codes.includes(key)) codes.push(key)
  } else {
    const idx = codes.indexOf(key)
    if (idx !== -1) codes.splice(idx, 1)
  }

  if (!currentRole.value.permissions) {
    currentRole.value.permissions = {} as any
  }
  (currentRole.value.permissions as any).codes = codes

  savePermissionsToBackend()
}

async function savePermissionsToBackend() {
  try {
    const codes = (currentRole.value!.permissions as any)?.codes || permsToCodes()
    await api.put(`/roles/${currentRole.value!.id}`, {
      permissions: { codes }
    })
    ElMessage.success($t('role.permsUpdated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('role.saveFailed'))
  }
}

async function loadRoles() {
  loading.value = true
  try {
    const response = await api.get('/roles')
    roles.value = response.data
    if (roles.value.length > 0 && !currentRole.value) {
      selectRole(roles.value[0])
    }
  } catch (error) {
    ElMessage.error($t('role.loadFailed'))
  } finally {
    loading.value = false
  }
}

function selectRole(role: Role) {
  currentRole.value = role
}

function showEditDialog(role: Role) {
  isEdit.value = true
  Object.assign(form, {
    id: role.id,
    name: role.name,
    code: role.code,
    description: role.description || '',
    is_active: role.is_active
  })
  dialogVisible.value = true
}

function showPermDialog() {
  permDialogVisible.value = true
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
    if (isEdit.value) {
      await api.put(`/roles/${form.id}`, {
        name: form.name,
        description: form.description,
        is_active: form.is_active
      })
      ElMessage.success($t('role.roleUpdated'))
    } else {
      await api.post('/roles', {
        name: form.name,
        code: form.code,
        description: form.description,
        is_active: form.is_active
      })
      ElMessage.success($t('role.roleCreated'))
    }
    dialogVisible.value = false
    loadRoles()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('role.operationFailed'))
  } finally {
    submitting.value = false
  }
}

async function savePermissions() {
  if (!currentRole.value) return

  savingPerms.value = true
  try {
    const checkedKeys = permTreeRef.value.getCheckedKeys() as string[]
    const codes = checkedKeys.filter(k => k.includes(':'))

    await api.put(`/roles/${currentRole.value.id}`, { permissions: { codes } })
    currentRole.value.permissions = { codes } as any
    ElMessage.success($t('role.permsSaved'))
    permDialogVisible.value = false
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('role.saveFailed'))
  } finally {
    savingPerms.value = false
  }
}

async function deleteRole(role: Role) {
  if (role.is_system) {
    ElMessage.warning($t('role.systemRoleNoDelete'))
    return
  }

  try {
    await ElMessageBox.confirm(
      $t('role.confirmDeleteRole', { name: role.name }),
      $t('role.confirmDeleteTitle'),
      { type: 'warning' }
    )
    await api.delete(`/roles/${role.id}`)
    ElMessage.success($t('role.roleDeleted'))
    if (currentRole.value?.id === role.id) {
      currentRole.value = null
    }
    loadRoles()
  } catch (error) {
    // User cancelled
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleString(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US')
}

onMounted(() => {
  loadRoles()
})
</script>

<style scoped lang="scss">
.roles-page {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-bottom: 20px;
  }

  .roles-container {
    display: flex;
    gap: 20px;
    min-height: calc(100vh - 160px);
  }

  .roles-sidebar {
    width: 250px;
    flex-shrink: 0;

    .el-card {
      height: 100%;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .role-list {
      flex: 1;
      display: flex;
      flex-direction: column;

      .role-item {
        display: flex;
        align-items: center;
        padding: 12px 14px;
        border-radius: var(--pc-radius-md);
        cursor: pointer;
        margin-bottom: 6px;
        gap: 12px;
        transition: all 0.2s ease;
        border: 1px solid transparent;

        &:hover {
          background: rgba(var(--pc-primary-rgb), 0.06);
          border-color: rgba(var(--pc-primary-rgb), 0.15);
        }

        &.active {
          background: rgba(var(--pc-primary-rgb), 0.1);
          border-color: rgba(var(--pc-primary-rgb), 0.3);
          box-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.08);

          .role-icon {
            background: var(--pc-gradient-primary);
            box-shadow: 0 0 10px rgba(var(--pc-primary-rgb), 0.3);
          }
        }

        .role-icon {
          width: 38px;
          height: 38px;
          border-radius: var(--pc-radius-md);
          background: rgba(var(--pc-primary-rgb), 0.15);
          color: var(--pc-primary);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          flex-shrink: 0;
          transition: all 0.2s ease;
        }

        .role-info {
          flex: 1;
          min-width: 0;

          .role-name {
            font-weight: 600;
            font-size: 14px;
            color: var(--pc-text-primary);
            margin-bottom: 2px;
          }

          .role-code {
            font-size: 11px;
            color: var(--pc-text-muted);
            font-family: 'JetBrains Mono', 'Consolas', monospace;
          }
        }

        :deep(.el-tag) {
          flex-shrink: 0;
        }
      }
    }
  }

  .roles-content {
    flex: 1;
    min-width: 0;

    .el-card {
      height: 100%;
    }
  }

  .role-detail-card {
    :deep(.el-card__body) {
      display: flex;
      flex-direction: column;
      min-height: calc(100vh - 240px);
    }

    &.empty-card {
      :deep(.el-card__body) {
        display: flex;
        justify-content: center;
        align-items: center;
        flex: 1;
      }
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;

      .empty-icon {
        color: var(--pc-text-secondary);
      }

      p {
        margin: 0;
        color: var(--pc-text-regular);
        font-size: 14px;
        text-align: center;
      }
    }

    :deep(.el-empty) {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;

      .el-empty__image {
        display: flex;
        justify-content: center;
      }

      .el-empty__description {
        text-align: center;
        margin-top: 16px;
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .role-title {
        display: flex;
        align-items: center;
        gap: 12px;

        .name {
          font-size: 16px;
          font-weight: 500;
        }
      }
    }

    .section {
      margin-top: 24px;

      .section-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 500;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--pc-border-color-light);
      }

      .permission-tree {
        .permission-module {
          margin-bottom: 16px;
          padding: 16px;
          background: var(--pc-bg-page);
          border-radius: 8px;

          .module-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;

            .module-name {
              font-weight: 500;
            }
          }

          .module-perms {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            padding-left: 24px;

            .el-checkbox {
              margin-right: 0;
            }
          }
        }
      }
    }
  }

  .form-tip {
    font-size: 12px;
    color: var(--pc-text-secondary);
    margin-top: 4px;
  }

  .perm-edit-content {
    max-height: 400px;
    overflow-y: auto;
  }
}
</style>
