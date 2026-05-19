<template>
  <div class="org-perms-page">
    <!-- Left Navigation -->
    <div class="sidebar">
      <div class="nav-group">
        <div class="nav-title">{{ $t('org.organization') }}</div>
        <div class="nav-item" :class="{ active: activeSection === 'org' }" @click="activeSection = 'org'">
          <el-icon><OfficeBuilding /></el-icon>
          <span>{{ $t('org.organization') }}</span>
        </div>
      </div>

      <div class="nav-group">
        <div class="nav-title">{{ $t('org.permissions') }}</div>
        <div class="nav-item" :class="{ active: activeSection === 'role' }" @click="activeSection = 'role'">
          <el-icon><UserFilled /></el-icon>
          <span>{{ $t('org.permissions') }}</span>
        </div>
      </div>
    </div>

    <!-- Right Content -->
    <div class="content-area" v-loading="loading">

      <!-- ====== Organization Management ====== -->
      <template v-if="activeSection === 'org'">
        <div class="pc-page-header">
          <h2 class="page-title">{{ $t('org.title') }}</h2>
          <el-button type="primary" size="small" @click="showOrgCreateDialog">
            <el-icon><Plus /></el-icon> {{ $t('org.create') }}
          </el-button>
        </div>
        <el-tree
          :data="orgTree"
          :props="{ label: 'name', children: 'children' }"
          node-key="id"
          default-expand-all
          :expand-on-click-node="false"
        >
          <template #default="{ data }">
            <div class="tree-node">
              <span class="node-label">
                <el-icon><OfficeBuilding /></el-icon>
                {{ data.name }}
                <el-tag size="small" :type="data.status === 'active' ? 'success' : 'info'" class="ml-2">
                  {{ data.type }}
                </el-tag>
              </span>
              <span class="node-actions">
                <el-button size="small" link @click.stop="editOrg(data)">{{ $t('common.edit') }}</el-button>
                <el-button size="small" link type="danger" @click.stop="deleteOrg(data)">{{ $t('common.delete') }}</el-button>
              </span>
            </div>
          </template>
        </el-tree>
        <el-empty v-if="orgTree.length === 0" :description="$t('common.noData')" />
      </template>

      <!-- ====== Roles & Permissions ====== -->
      <template v-if="activeSection === 'role'">
        <div class="pc-page-header">
          <h2 class="page-title">{{ $t('org.permissions') }}</h2>
          <el-button type="primary" size="small" @click="showRoleCreateDialog">
            <el-icon><Plus /></el-icon> {{ $t('org.newRole') }}
          </el-button>
        </div>

        <div class="role-layout">
          <div class="role-list">
            <div
              v-for="role in roles"
              :key="role.id"
              class="role-item"
              :class="{ active: currentRole?.id === role.id }"
              @click="selectRole(role)"
            >
              <el-icon><UserFilled /></el-icon>
              <div class="role-info">
                <span class="role-name">{{ role.name }}</span>
                <span class="role-code">{{ role.code }}</span>
              </div>
              <el-tag v-if="role.is_system" type="warning" size="small">{{ $t('org.system') }}</el-tag>
            </div>
            <el-empty v-if="roles.length === 0" :description="$t('common.noData')" :image-size="50" />
          </div>

          <div class="role-detail" v-if="currentRole">
            <div class="detail-header">
              <span class="name">{{ currentRole.name }}</span>
              <el-tag :type="currentRole.is_active ? 'success' : 'danger'" size="small">
                {{ currentRole.is_active ? $t('common.active') : $t('common.inactive') }}
              </el-tag>
              <div class="detail-actions">
                <el-button type="primary" link size="small" @click="showRoleEditDialog(currentRole)" :disabled="currentRole.is_system && !isSuperAdmin">{{ $t('common.edit') }}</el-button>
                <el-button type="danger" link size="small" @click="deleteRole(currentRole)" :disabled="currentRole.is_system">{{ $t('common.delete') }}</el-button>
              </div>
            </div>
            <el-descriptions :column="2" border size="small" style="margin-top: 12px">
              <el-descriptions-item :label="$t('org.roleCode')">{{ currentRole.code }}</el-descriptions-item>
              <el-descriptions-item :label="$t('common.description')">{{ currentRole.description || '-' }}</el-descriptions-item>
            </el-descriptions>

            <div class="perm-section">
              <div class="perm-header">
                <span>{{ $t('org.permConfig') }}</span>
                <el-tag type="info" size="small">{{ rolePermCount }} {{ $t('org.items') }}</el-tag>
              </div>
              <div class="perm-modules">
                <div v-for="module in permissionModules" :key="module.key" class="perm-module">
                  <div class="module-header">
                    <el-checkbox
                      :model-value="isModuleChecked(module.key)"
                      :indeterminate="isModuleIndeterminate(module.key)"
                      @change="toggleModule(module.key, $event)"
                      :disabled="currentRole.is_system && !isSuperAdmin"
                    >{{ module.name }}</el-checkbox>
                  </div>
                  <div class="module-perms">
                    <el-checkbox
                      v-for="perm in module.permissions"
                      :key="perm.key"
                      :model-value="hasPermission(module.key, perm.key)"
                      :disabled="currentRole.is_system && !isSuperAdmin"
                      @change="togglePermission(module.key, perm.key, $event)"
                    >{{ perm.name }}</el-checkbox>
                  </div>
                </div>
              </div>
            </div>

            <!-- Permission Definitions (collapsed) -->
            <el-collapse v-model="permDefExpanded" style="margin-top: 20px">
              <el-collapse-item title="Permission Definitions" name="defs">
                <template #title>
                  <div class="perm-def-title">
                    <span>{{ $t('permission.permDefs') }}</span>
                    <div class="perm-def-actions" @click.stop>
                      <el-button size="small" @click="initDefaultPerms">{{ $t('permission.initDefaults') }}</el-button>
                      <el-button type="primary" size="small" @click="showPermCreateDialog">
                        <el-icon><Plus /></el-icon> {{ $t('common.create') }}
                      </el-button>
                    </div>
                  </div>
                </template>
                <el-tree
                  :data="permTree"
                  :props="{ label: 'name', children: 'children' }"
                  node-key="id"
                  default-expand-all
                  :expand-on-click-node="false"
                >
                  <template #default="{ data }">
                    <div class="tree-node">
                      <span class="node-label">
                        <el-icon><Lock /></el-icon>
                        {{ data.name }}
                        <el-tag size="small" class="ml-2">{{ data.code }}</el-tag>
                        <el-tag v-if="data.is_system" size="small" type="warning" class="ml-1">{{ $t('common.system') }}</el-tag>
                      </span>
                      <span class="node-actions">
                        <el-button size="small" link @click.stop="editPerm(data)" :disabled="data.is_system">{{ $t('common.edit') }}</el-button>
                        <el-button size="small" link type="danger" @click.stop="deletePerm(data)" :disabled="data.is_system">{{ $t('common.delete') }}</el-button>
                      </span>
                    </div>
                  </template>
                </el-tree>
                <el-empty v-if="permTree.length === 0" :description="$t('permission.noPermDefs')" :image-size="40" />
              </el-collapse-item>
            </el-collapse>
          </div>
          <el-empty v-else :description="$t('org.selectRole')" :image-size="60" />
        </div>
      </template>

    </div>

    <!-- Organization Create/Edit Dialog -->
    <el-dialog v-model="orgDialogVisible" :title="editingOrg ? $t('organization.editOrg') : $t('organization.createOrg')" width="500px">
      <el-form :model="orgForm" label-width="80px">
        <el-form-item :label="$t('organization.name')" required>
          <el-input v-model="orgForm.name" :placeholder="$t('organization.name')" />
        </el-form-item>
        <el-form-item :label="$t('organization.code')" required>
          <el-input v-model="orgForm.code" :placeholder="$t('organization.code')" :disabled="!!editingOrg" />
        </el-form-item>
        <el-form-item :label="$t('organization.type')">
          <el-select v-model="orgForm.type">
            <el-option :label="$t('organization.company')" value="company" />
            <el-option :label="$t('organization.department')" value="department" />
            <el-option :label="$t('organization.team')" value="team" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('organization.parentOrg')">
          <el-tree-select
            v-model="orgForm.parent_id"
            :data="orgTreeForSelect"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            clearable
            check-strictly
            :placeholder="$t('organization.parentOrgPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="$t('organization.description')">
          <el-input v-model="orgForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="orgDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitOrg" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Role Create/Edit Dialog -->
    <el-dialog v-model="roleDialogVisible" :title="isRoleEdit ? $t('role.editRole') : $t('role.newRole')" width="500px">
      <el-form :model="roleForm" label-width="80px">
        <el-form-item :label="$t('role.roleName')" required>
          <el-input v-model="roleForm.name" :placeholder="$t('role.roleName')" />
        </el-form-item>
        <el-form-item :label="$t('role.roleCode')" required>
          <el-input v-model="roleForm.code" :placeholder="$t('role.roleCode')" :disabled="isRoleEdit" />
        </el-form-item>
        <el-form-item :label="$t('role.description')">
          <el-input v-model="roleForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="$t('role.status')">
          <el-radio-group v-model="roleForm.is_active">
            <el-radio :value="true">{{ $t('role.enable') }}</el-radio>
            <el-radio :value="false">{{ $t('role.disable') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitRole" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Permission Create/Edit Dialog -->
    <el-dialog v-model="permDialogVisible" :title="editingPerm ? $t('permission.editPerm') : $t('permission.createPerm')" width="500px">
      <el-form :model="permForm" label-width="80px">
        <el-form-item :label="$t('permission.name')" required>
          <el-input v-model="permForm.name" />
        </el-form-item>
        <el-form-item :label="$t('permission.code')" required>
          <el-input v-model="permForm.code" :disabled="!!editingPerm" placeholder="e.g. task:create" />
        </el-form-item>
        <el-form-item :label="$t('permission.resource')">
          <el-input v-model="permForm.resource" placeholder="e.g. task" />
        </el-form-item>
        <el-form-item :label="$t('permission.action')">
          <el-input v-model="permForm.action" placeholder="e.g. create" />
        </el-form-item>
        <el-form-item :label="$t('permission.type')">
          <el-select v-model="permForm.type">
            <el-option :label="$t('permission.app')" value="app" />
            <el-option :label="$t('permission.menu')" value="menu" />
            <el-option :label="$t('permission.system')" value="system" />
            <el-option :label="$t('permission.api')" value="api" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('permission.parentPerm')">
          <el-tree-select
            :data="permTreeForSelect"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            v-model="permForm.parent_id"
            clearable
            check-strictly
            :placeholder="$t('permission.parentPermPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitPerm">{{ editingPerm ? $t('common.save') : $t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, OfficeBuilding, UserFilled, Lock } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { organizationApi } from '@/api/organization'
import { permissionApi } from '@/api/permission'
import { api } from '@/api'
import { useUserStore } from '@/stores/user'

const { t: $t } = useI18n()
const userStore = useUserStore()
const isSuperAdmin = computed(() => (userStore as any).user?.role === 'super_admin')
const submitting = ref(false)
const loading = ref(false)
const activeSection = ref('org')

// ==================== 组织 ====================
interface Org { id: string; name: string; code: string; description?: string; type: string; status: string; level: number; parent_id?: string; children?: Org[] }
const orgTree = ref<Org[]>([])
const orgDialogVisible = ref(false)
const editingOrg = ref<Org | null>(null)
const orgForm = reactive({ name: '', code: '', type: 'department', description: '', parent_id: undefined as string | undefined })
const orgTreeForSelect = computed(() => orgTree.value)

async function fetchOrgTree() {
  loading.value = true
  try {
    const res = await organizationApi.tree()
    orgTree.value = res.data
  } catch { ElMessage.error($t('organization.loadTreeFailed')) }
  finally { loading.value = false }
}

function showOrgCreateDialog() {
  editingOrg.value = null
  Object.assign(orgForm, { name: '', code: '', type: 'department', description: '', parent_id: undefined })
  orgDialogVisible.value = true
}

function editOrg(org: Org) {
  editingOrg.value = org
  Object.assign(orgForm, { name: org.name, code: org.code, type: org.type, description: org.description || '', parent_id: org.parent_id || undefined })
  orgDialogVisible.value = true
}

async function submitOrg() {
  submitting.value = true
  try {
    if (editingOrg.value) {
      await organizationApi.update(editingOrg.value.id, orgForm)
      ElMessage.success($t('organization.updated'))
    } else {
      await organizationApi.create(orgForm)
      ElMessage.success($t('organization.created'))
    }
    orgDialogVisible.value = false
    fetchOrgTree()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || $t('organization.operationFailed')) }
  finally { submitting.value = false }
}

async function deleteOrg(org: Org) {
  try {
    await ElMessageBox.confirm($t('organization.confirmDelete'), $t('common.confirm'), { type: 'warning' })
    await organizationApi.delete(org.id)
    ElMessage.success($t('common.success'))
    fetchOrgTree()
  } catch {}
}

// ==================== 角色 ====================
interface Role { id: number; name: string; code: string; description: string | null; permissions: { codes?: string[] } | null; is_system: boolean; is_active: boolean }
const roles = ref<Role[]>([])
const currentRole = ref<Role | null>(null)
const roleDialogVisible = ref(false)
const isRoleEdit = ref(false)
const roleForm = reactive({ id: 0, name: '', code: '', description: '', is_active: true })

const permissionModules = [
  { key: 'task', name: 'Task', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'agent', name: 'Agent', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }, { key: 'execute', name: 'Execute' }] },
  { key: 'skill', name: 'Skill', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'memory', name: 'Memory', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'knowledge', name: 'Knowledge', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'wiki', name: 'Wiki', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'runner', name: 'Runner', permissions: [{ key: 'read', name: 'View' }, { key: 'approve', name: 'Approve' }, { key: 'delete', name: 'Delete' }] },
  { key: 'org', name: 'Organization', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'user', name: 'User', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'role', name: 'Role', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'permission', name: 'Permission', permissions: [{ key: 'create', name: 'Create' }, { key: 'read', name: 'View' }, { key: 'update', name: 'Edit' }, { key: 'delete', name: 'Delete' }] },
  { key: 'system', name: 'System', permissions: [{ key: 'settings', name: 'Settings' }, { key: 'ai_config', name: 'AI Config' }, { key: 'logs', name: 'Logs' }] },
]

const rolePermCount = computed(() => {
  if (!currentRole.value?.permissions) return 0
  return (currentRole.value.permissions.codes || []).length
})

async function fetchRoles() {
  loading.value = true
  try {
    const res = await api.get('/roles')
    roles.value = res.data
    if (roles.value.length > 0 && !currentRole.value) selectRole(roles.value[0])
  } catch { ElMessage.error($t('role.loadFailed')) }
  finally { loading.value = false }
}

function selectRole(role: Role) { currentRole.value = role }

function hasPermission(mod: string, perm: string): boolean {
  if (!currentRole.value?.permissions) return false
  const codes: string[] = currentRole.value.permissions.codes || []
  if (codes.includes('*')) return true
  return codes.includes(`${mod}:${perm}`) || codes.includes(`${mod}:*`)
}

function isModuleChecked(mod: string): boolean {
  const m = permissionModules.find(x => x.key === mod)
  if (!m) return false
  return m.permissions.every(p => hasPermission(mod, p.key))
}

function isModuleIndeterminate(mod: string): boolean {
  const m = permissionModules.find(x => x.key === mod)
  if (!m) return false
  const cnt = m.permissions.filter(p => hasPermission(mod, p.key)).length
  return cnt > 0 && cnt < m.permissions.length
}

async function toggleModule(mod: string, checked: boolean) {
  if (!currentRole.value || (currentRole.value.is_system && !isSuperAdmin.value)) return
  const m = permissionModules.find(x => x.key === mod)
  if (!m) return
  if (!currentRole.value.permissions) currentRole.value.permissions = { codes: [] }
  const codes: string[] = currentRole.value.permissions.codes || []
  const filtered = codes.filter(c => !c.startsWith(`${mod}:`) && c !== '*')
  if (checked) {
    m.permissions.forEach(p => filtered.push(`${mod}:${p.key}`))
  }
  currentRole.value.permissions.codes = filtered
  await saveRolePerms()
}

async function togglePermission(mod: string, perm: string, checked: boolean) {
  if (!currentRole.value || (currentRole.value.is_system && !isSuperAdmin.value)) return
  if (!currentRole.value.permissions) currentRole.value.permissions = { codes: [] }
  const codes: string[] = currentRole.value.permissions.codes || []
  const code = `${mod}:${perm}`
  const wildcard = `${mod}:*`
  const filtered = codes.filter(c => c !== code && c !== wildcard)
  if (checked) {
    filtered.push(code)
  }
  currentRole.value.permissions.codes = filtered
  await saveRolePerms()
}

async function saveRolePerms() {
  try {
    await api.put(`/roles/${currentRole.value!.id}`, {
      permissions: { codes: currentRole.value!.permissions?.codes || [] }
    })
    ElMessage.success($t('role.permsUpdated'))
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || $t('role.saveFailed')) }
}

function showRoleCreateDialog() {
  isRoleEdit.value = false
  Object.assign(roleForm, { id: 0, name: '', code: '', description: '', is_active: true })
  roleDialogVisible.value = true
}

function showRoleEditDialog(role: Role) {
  isRoleEdit.value = true
  Object.assign(roleForm, { id: role.id, name: role.name, code: role.code, description: role.description || '', is_active: role.is_active })
  roleDialogVisible.value = true
}

async function submitRole() {
  submitting.value = true
  try {
    if (isRoleEdit.value) {
      await api.put(`/roles/${roleForm.id}`, { name: roleForm.name, description: roleForm.description, is_active: roleForm.is_active })
      ElMessage.success($t('role.roleUpdated'))
    } else {
      const { id: _id, ...createData } = roleForm
      await api.post('/roles', createData)
      ElMessage.success($t('role.roleCreated'))
    }
    roleDialogVisible.value = false
    fetchRoles()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || $t('organization.operationFailed')) }
  finally { submitting.value = false }
}

async function deleteRole(role: Role) {
  if (role.is_system) { ElMessage.warning($t('role.systemRoleNoDelete')); return }
  try {
    await ElMessageBox.confirm($t('role.confirmDelete'), $t('common.confirm'), { type: 'warning' })
    await api.delete(`/roles/${role.id}`)
    ElMessage.success($t('common.success'))
    if (currentRole.value?.id === role.id) currentRole.value = null
    fetchRoles()
  } catch {}
}

// ==================== 权限 ====================
interface Perm { id: string; name: string; code: string; description?: string; type: string; resource: string; action: string; is_system: boolean; is_active: boolean; parent_id?: string; children?: Perm[] }
const permTree = ref<Perm[]>([])
const permDialogVisible = ref(false)
const editingPerm = ref<Perm | null>(null)
const permForm = reactive({ name: '', code: '', description: '', type: 'app', resource: '', action: '', parent_id: undefined as string | undefined })
const permTreeForSelect = computed(() => permTree.value)
const permDefExpanded = ref<string[]>([])

async function fetchPermTree() {
  loading.value = true
  try {
    const res = await permissionApi.tree()
    permTree.value = res.data
  } catch { ElMessage.error($t('permission.loadFailed')) }
  finally { loading.value = false }
}

async function initDefaultPerms() {
  try {
    await ElMessageBox.confirm($t('permission.initConfirm'), $t('common.confirm'))
    const res = await permissionApi.initDefaults()
    ElMessage.success(res.data.message || $t('permission.initSuccess'))
    fetchPermTree()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error($t('permission.initFailed')) }
}

function showPermCreateDialog() {
  editingPerm.value = null
  Object.assign(permForm, { name: '', code: '', description: '', type: 'app', resource: '', action: '', parent_id: undefined })
  permDialogVisible.value = true
}

function editPerm(perm: Perm) {
  if (perm.is_system) return
  editingPerm.value = perm
  Object.assign(permForm, { name: perm.name, code: perm.code, description: perm.description || '', type: perm.type, resource: perm.resource, action: perm.action, parent_id: perm.parent_id || undefined })
  permDialogVisible.value = true
}

async function submitPerm() {
  try {
    if (editingPerm.value) {
      await permissionApi.update(editingPerm.value.id, permForm)
      ElMessage.success($t('organization.updated'))
    } else {
      await permissionApi.create(permForm)
      ElMessage.success($t('organization.created'))
    }
    permDialogVisible.value = false
    fetchPermTree()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || $t('organization.operationFailed')) }
}

async function deletePerm(perm: Perm) {
  if (perm.is_system) return
  try {
    await ElMessageBox.confirm($t('permission.confirmDelete'), $t('common.confirm'), { type: 'warning' })
    await permissionApi.delete(perm.id)
    ElMessage.success($t('common.success'))
    fetchPermTree()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || $t('permission.deleteFailed')) }
}

// ==================== 初始化 ====================
onMounted(() => {
  fetchOrgTree()
  fetchRoles()
  fetchPermTree()
})
</script>

<style scoped lang="scss">
.org-perms-page {
  display: flex;
  gap: 16px;
  min-height: calc(100vh - 120px);

  // Left Navigation
  .sidebar {
    width: 180px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;

    .nav-group {
      margin-bottom: 8px;

      .nav-title {
        font-size: 11px;
        color: var(--pc-text-muted);
        padding: 4px 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
      }

      .nav-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        color: var(--pc-text-secondary);
        transition: all 0.2s;

        &:hover {
          background: rgba(var(--pc-primary-rgb), 0.06);
          color: var(--pc-text-primary);
        }

        &.active {
          background: rgba(var(--pc-primary-rgb), 0.1);
          color: var(--pc-primary);
          font-weight: 500;
        }
      }
    }
  }

  // Right Content
  .content-area {
    flex: 1;
    min-width: 0;
    background: var(--pc-bg-elevated);
    border-radius: 8px;
    border: 1px solid var(--pc-border);
    padding: 20px;
    overflow-y: auto;

  }

  // Tree Node
  .tree-node {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;

    .node-label {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .node-actions { display: none; }
    &:hover .node-actions { display: inline; }
  }

  .ml-1 { margin-left: 4px; }
  .ml-2 { margin-left: 8px; }

  // Permission Definition Collapse
  .perm-def-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    font-weight: 500;

    .perm-def-actions {
      display: flex;
      gap: 8px;
    }
  }

  // Role Layout
  .role-layout {
    display: flex;
    gap: 16px;
  }

  .role-list {
    width: 200px;
    flex-shrink: 0;
    border: 1px solid var(--pc-border);
    border-radius: 6px;
    padding: 8px;
    overflow-y: auto;
    max-height: calc(100vh - 260px);

    .role-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 4px;
      cursor: pointer;

      &:hover { background: rgba(var(--pc-primary-rgb), 0.04); }
      &.active { background: rgba(var(--pc-primary-rgb), 0.08); border: 1px solid var(--pc-primary); }

      .role-info {
        flex: 1;
        min-width: 0;

        .role-name { display: block; font-weight: 500; font-size: 13px; color: var(--pc-text-primary); }
        .role-code { display: block; font-size: 11px; color: var(--pc-text-muted); }
      }
    }
  }

  .role-detail {
    flex: 1;
    min-width: 0;

    .detail-header {
      display: flex;
      align-items: center;
      gap: 8px;

      .name { font-size: 16px; font-weight: 500; color: var(--pc-text-primary); }
      .detail-actions { margin-left: auto; }
    }

    .perm-section {
      margin-top: 20px;

      .perm-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 500;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--pc-border);
        color: var(--pc-text-primary);
      }

      .perm-modules {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;

        .perm-module {
          padding: 12px;
          background: var(--pc-bg-surface);
          border-radius: 6px;
          border: 1px solid var(--pc-border);

          .module-header { margin-bottom: 8px; }

          .module-perms {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding-left: 20px;
          }
        }
      }
    }
  }
}
</style>
