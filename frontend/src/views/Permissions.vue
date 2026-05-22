<template>
  <div class="permissions-page">
    <div class="perm-toolbar">
      <el-button @click="initDefaults">
        <el-icon><RefreshRight /></el-icon> {{ $t('permission.initDefaults') }}
      </el-button>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon> {{ $t('permission.createPerm') }}
      </el-button>
    </div>

    <el-tabs v-model="activeTab" v-loading="loading">
      <el-tab-pane :label="$t('permission.permTree')" name="tree">
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
                <span class="node-dot" :class="'dot-' + (data.type || 'app')"></span>
                <span class="node-name">{{ data.name }}</span>
                <span class="node-code">{{ data.code }}</span>
                <el-icon v-if="data.is_system" class="sys-icon"><Lock /></el-icon>
              </span>
              <span class="node-actions">
                <el-button size="small" link @click.stop="editPerm(data)" :disabled="data.is_system">{{ $t('common.edit') }}</el-button>
                <el-button size="small" link type="danger" @click.stop="deletePerm(data)" :disabled="data.is_system">{{ $t('common.delete') }}</el-button>
              </span>
            </div>
          </template>
        </el-tree>
      </el-tab-pane>

      <el-tab-pane :label="$t('permission.permList')" name="list">
        <el-table :data="permList" stripe :empty-text="$t('common.noData')" class="pc-data-table">
          <el-table-column prop="name" :label="$t('permission.name')" min-width="120" show-overflow-tooltip />
          <el-table-column prop="code" :label="$t('permission.code')" width="140" show-overflow-tooltip />
          <el-table-column prop="resource" :label="$t('permission.resource')" width="80" />
          <el-table-column prop="action" :label="$t('permission.action')" width="80" />
          <el-table-column prop="type" :label="$t('common.type')" width="80">
            <template #default="{ row }">
              <span class="type-dot" :class="'dot-' + (row.type || 'app')"></span>
              {{ row.type }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('permission.isSystem')" width="90" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.is_system" class="sys-lock"><Lock /></el-icon>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.actions')" width="140" fixed="right">
            <template #default="{ row }">
              <el-button size="small" link @click="editPerm(row)" :disabled="row.is_system">{{ $t('common.edit') }}</el-button>
              <el-button size="small" link type="danger" @click="deletePerm(row)" :disabled="row.is_system">{{ $t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingPerm ? $t('permission.editPerm') : $t('permission.createPerm')" width="500">
      <el-form :model="formData" label-width="80px">
        <el-form-item :label="$t('permission.name')" required>
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item :label="$t('permission.code')" required>
          <el-input v-model="formData.code" placeholder="例: task:create" :disabled="!!editingPerm" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" />
        </el-form-item>
        <el-form-item :label="$t('permission.type')">
          <el-select v-model="formData.type">
            <el-option :label="$t('permission.menu')" value="menu" />
            <el-option :label="$t('permission.isSystem')" value="system" />
            <el-option :label="$t('permission.app')" value="app" />
            <el-option :label="$t('permission.api')" value="api" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('permission.resource')">
          <el-input v-model="formData.resource" placeholder="例: task" />
        </el-form-item>
        <el-form-item :label="$t('permission.action')">
          <el-input v-model="formData.action" placeholder="例: create" />
        </el-form-item>
        <el-form-item :label="$t('permission.parentPerm')">
          <el-tree-select
            v-model="formData.parent_id"
            :data="permTreeForSelect"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            clearable
            check-strictly
            :placeholder="$t('permission.parentPermPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('permission.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm">{{ editingPerm ? $t('permission.save') : $t('permission.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Lock, RefreshRight } from '@element-plus/icons-vue'
import { permissionApi } from '@/api/permission'
import type { Permission, PermissionTree, PermissionCreate, PermissionUpdate } from '@/types/permission'

const { t: $t } = useI18n()

const activeTab = ref('tree')
const permTree = ref<PermissionTree[]>([])
const permList = ref<Permission[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingPerm = ref<Permission | null>(null)
const formData = ref<PermissionCreate>({
  name: '',
  code: '',
  description: '',
  type: 'app',
  resource: '',
  action: '',
  parent_id: undefined,
})

const permTreeForSelect = computed(() => permTree.value)

async function fetchTree() {
  loading.value = true
  try {
    const res = await permissionApi.tree()
    permTree.value = res.data
  } catch (e: any) {
    ElMessage.error($t('permission.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function fetchList() {
  try {
    const res = await permissionApi.list()
    permList.value = res.data.items
  } catch (e: any) {
    ElMessage.error($t('permission.loadFailed'))
  }
}

async function initDefaults() {
  try {
    await ElMessageBox.confirm($t('permission.initConfirm'), $t('common.confirm'))
    const res = await permissionApi.initDefaults()
    ElMessage.success(res.data.message || $t('permission.initSuccess'))
    fetchTree()
    fetchList()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error($t('permission.initFailed'))
  }
}

function showCreateDialog() {
  editingPerm.value = null
  formData.value = { name: '', code: '', description: '', type: 'app', resource: '', action: '', parent_id: undefined }
  dialogVisible.value = true
}

function editPerm(perm: Permission) {
  if (perm.is_system) return
  editingPerm.value = perm
  formData.value = {
    name: perm.name,
    code: perm.code,
    description: perm.description || '',
    type: perm.type,
    resource: perm.resource,
    action: perm.action,
    parent_id: perm.parent_id || undefined,
  }
  dialogVisible.value = true
}

async function submitForm() {
  if (!formData.value.name || !formData.value.code) {
    ElMessage.warning($t('permission.fillRequired'))
    return
  }
  try {
    if (editingPerm.value) {
      await permissionApi.update(editingPerm.value.id, formData.value as PermissionUpdate)
      ElMessage.success($t('permission.updated'))
    } else {
      await permissionApi.create(formData.value)
      ElMessage.success($t('permission.created'))
    }
    dialogVisible.value = false
    fetchTree()
    fetchList()
  } catch (e: any) {
    if (editingPerm.value) {
      ElMessage.error(e.response?.data?.detail || $t('permission.updateFailed'))
    } else {
      ElMessage.error(e.response?.data?.detail || $t('permission.createFailed'))
    }
  }
}

async function deletePerm(perm: Permission) {
  if (perm.is_system) {
    ElMessage.warning($t('permission.systemPermNoDelete'))
    return
  }
  try {
    await ElMessageBox.confirm($t('permission.confirmDeletePerm', { name: perm.name }), $t('permission.confirmDelete'), { type: 'warning' })
    await permissionApi.delete(perm.id)
    ElMessage.success($t('permission.deleted'))
    fetchTree()
    fetchList()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || $t('permission.deleteFailed'))
  }
}

onMounted(() => {
  fetchTree()
  fetchList()
})
</script>

<style scoped lang="scss">
.permissions-page {
  padding: 16px 20px;
  color: var(--pc-text-primary);
}

/* —— Toolbar —— */
.perm-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 18px;

  :deep(.el-button) {
    height: 34px;
  }
}

/* —— Tabs —— */
:deep(.el-tabs) {
  .el-tabs__header { margin-bottom: 16px; }
  .el-tabs__item {
    color: var(--pc-text-secondary);
    &.is-active { color: var(--pc-primary); }
  }
  .el-tabs__active-bar { background: var(--pc-primary); }
}

/* —— Tree —— */
:deep(.el-tree) {
  background: transparent;
  padding: 8px 0;

  .el-tree-node__content {
    height: auto;
    padding: 8px 12px;
    border-radius: var(--pc-radius-md);
    border: 1px solid transparent;
    transition: all 0.15s ease;
    margin-bottom: 1px;

    &:hover {
      background: rgba(var(--pc-primary-rgb), 0.05);
      border-color: rgba(var(--pc-primary-rgb), 0.12);

      .node-actions { opacity: 1; }
      .node-code { opacity: 1; }
    }
  }

  .el-tree-node__expand-icon {
    color: var(--pc-text-muted);
    &:hover { color: var(--pc-primary); }
  }
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  min-width: 0;
}

.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &.dot-menu { background: var(--pc-accent-purple); }
  &.dot-system { background: var(--pc-accent-red); }
  &.dot-app { background: var(--pc-primary); }
  &.dot-api { background: var(--pc-accent-green); }
}

.node-name {
  font-weight: 500;
  color: var(--pc-text-primary);
}

.node-code {
  font-size: 11px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  color: var(--pc-text-muted);
  background: rgba(var(--pc-primary-rgb), 0.06);
  padding: 1px 6px;
  border-radius: 3px;
  opacity: 0.6;
  transition: opacity 0.15s;
}

.sys-icon {
  color: var(--pc-accent-orange);
  font-size: 14px;
  flex-shrink: 0;
}

.sys-lock {
  color: var(--pc-accent-orange);
  font-size: 16px;
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

/* —— Table —— */
.type-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;

  &.dot-menu { background: var(--pc-accent-purple); }
  &.dot-system { background: var(--pc-accent-red); }
  &.dot-app { background: var(--pc-primary); }
  &.dot-api { background: var(--pc-accent-green); }
}

.text-muted { color: var(--pc-text-muted); }
</style>
