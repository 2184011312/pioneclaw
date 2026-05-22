<template>
  <div class="organizations-page">
    <div class="page-header">
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon> {{ $t('organization.createOrg') }}
      </el-button>
    </div>

    <el-tabs v-model="activeTab" v-loading="loading">
      <el-tab-pane :label="$t('organization.orgTree')" name="tree">
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
                <el-tag size="small" type="info" class="ml-1">Level {{ data.level }}</el-tag>
              </span>
              <span class="node-actions">
                <el-button size="small" link @click.stop="editOrg(data)">{{ $t('organization.edit') }}</el-button>
                <el-button size="small" link type="danger" @click.stop="deleteOrg(data)">{{ $t('organization.delete') }}</el-button>
              </span>
            </div>
          </template>
        </el-tree>
      </el-tab-pane>

      <el-tab-pane :label="$t('organization.orgList')" name="list">
        <el-table :data="orgList" stripe :empty-text="$t('common.noData')">
          <el-table-column prop="name" :label="$t('organization.name')" />
          <el-table-column prop="code" :label="$t('organization.code')" width="120" />
          <el-table-column prop="type" :label="$t('organization.type')" width="100" />
          <el-table-column prop="level" :label="$t('organization.level')" width="80" />
          <el-table-column prop="status" :label="$t('organization.status')" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? $t('organization.active') : $t('organization.inactive') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('organization.actions')" width="150">
            <template #default="{ row }">
              <el-button size="small" link @click="editOrg(row)">{{ $t('organization.edit') }}</el-button>
              <el-button size="small" link type="danger" @click="deleteOrg(row)">{{ $t('organization.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingOrg ? $t('organization.editOrg') : $t('organization.createOrg')" width="500">
      <el-form :model="formData" label-width="80px">
        <el-form-item :label="$t('organization.name')" required>
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item :label="$t('organization.code')" required>
          <el-input v-model="formData.code" :disabled="!!editingOrg" />
        </el-form-item>
        <el-form-item :label="$t('organization.description')">
          <el-input v-model="formData.description" type="textarea" />
        </el-form-item>
        <el-form-item :label="$t('organization.type')">
          <el-select v-model="formData.type">
            <el-option :label="$t('organization.company')" value="company" />
            <el-option :label="$t('organization.department')" value="department" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('organization.parentOrg')">
          <el-tree-select
            v-model="formData.parent_id"
            :data="orgTreeForSelect"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            clearable
            check-strictly
            :placeholder="$t('organization.parentOrgPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('organization.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm">{{ editingOrg ? $t('organization.save') : $t('organization.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, OfficeBuilding } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { organizationApi } from '@/api/organization'
import type { Organization, OrganizationTree, OrganizationCreate, OrganizationUpdate } from '@/types/organization'

const { t: $t } = useI18n()
const activeTab = ref('tree')
const orgTree = ref<OrganizationTree[]>([])
const orgList = ref<Organization[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingOrg = ref<Organization | null>(null)
const formData = ref<OrganizationCreate>({
  name: '',
  code: '',
  description: '',
  type: 'department',
  parent_id: undefined,
})

const orgTreeForSelect = computed(() => orgTree.value)

async function fetchTree() {
  loading.value = true
  try {
    const res = await organizationApi.tree()
    orgTree.value = res.data
  } catch (e: any) {
    ElMessage.error($t('organization.loadTreeFailed'))
  } finally {
    loading.value = false
  }
}

async function fetchList() {
  try {
    const res = await organizationApi.list()
    orgList.value = res.data.items
  } catch (e: any) {
    ElMessage.error($t('organization.loadListFailed'))
  }
}

function showCreateDialog() {
  editingOrg.value = null
  formData.value = { name: '', code: '', description: '', type: 'department', parent_id: undefined }
  dialogVisible.value = true
}

function editOrg(org: Organization) {
  editingOrg.value = org
  formData.value = {
    name: org.name,
    code: org.code,
    description: org.description || '',
    type: org.type,
    parent_id: org.parent_id || undefined,
  }
  dialogVisible.value = true
}

async function submitForm() {
  if (!formData.value.name || !formData.value.code) {
    ElMessage.warning($t('organization.fillRequired'))
    return
  }
  try {
    if (editingOrg.value) {
      await organizationApi.update(editingOrg.value.id, formData.value as OrganizationUpdate)
      ElMessage.success($t('organization.updated'))
    } else {
      await organizationApi.create(formData.value)
      ElMessage.success($t('organization.created'))
    }
    dialogVisible.value = false
    fetchTree()
    fetchList()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || $t('organization.operationFailed'))
  }
}

async function deleteOrg(org: Organization) {
  try {
    await ElMessageBox.confirm($t('organization.confirmDelete'), $t('common.confirm'), { type: 'warning' })
    await organizationApi.delete(org.id)
    ElMessage.success($t('organization.deleted'))
    fetchTree()
    fetchList()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || $t('organization.deleteFailed'))
  }
}

onMounted(() => {
  fetchTree()
  fetchList()
})
</script>

<style scoped lang="scss">
.organizations-page {
  padding: 20px;
  color: var(--pc-text-primary);

  .page-header {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-bottom: 20px;
  }

  :deep(.el-tabs) {
    .el-tabs__header {
      margin-bottom: 16px;
    }

    .el-tabs__item {
      color: var(--pc-text-secondary);
      &.is-active { color: var(--pc-primary); }
    }

    .el-tabs__active-bar { background: var(--pc-primary); }
  }

  // Tree tab
  :deep(.el-tree) {
    background: transparent;
    padding: 16px;

    .el-tree-node__content {
      height: auto;
      padding: 10px 12px;
      border-radius: var(--pc-radius-md);
      border: 1px solid transparent;
      transition: all 0.15s ease;
      margin-bottom: 2px;

      &:hover {
        background: rgba(var(--pc-primary-rgb), 0.06);
        border-color: rgba(var(--pc-primary-rgb), 0.15);

        .node-actions { opacity: 1; }
      }
    }

    .el-tree-node__expand-icon {
      color: var(--pc-text-muted);
      &:hover { color: var(--pc-primary); }
    }
  }

  // List tab
  :deep(.el-table) {
    --el-table-bg-color: transparent;
    --el-table-tr-bg-color: transparent;
    --el-table-header-bg-color: transparent;
    --el-table-row-hover-bg-color: rgba(var(--pc-primary-rgb), 0.06);
    --el-table-border-color: var(--pc-border);
    --el-table-text-color: var(--pc-text-primary);
    --el-table-header-text-color: var(--pc-text-secondary);
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
  font-weight: 500;
  color: var(--pc-text-primary);

  .el-icon {
    color: var(--pc-primary);
  }
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.ml-1 { margin-left: 4px; }
.ml-2 { margin-left: 8px; }
</style>
