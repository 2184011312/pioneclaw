<template>
  <div class="wiki-page">
    <div class="pc-page-header">
      <h2 class="pc-page-title">{{ $t('wiki.title') }}</h2>
      <div class="header-actions">
        <el-input v-model="searchQuery" :placeholder="$t('wiki.search')" style="width: 200px" @keyup.enter="search" clearable :disabled="searching" size="small">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-dropdown trigger="click">
          <button class="pc-glow-btn secondary">
            <el-icon><MoreFilled /></el-icon>
            {{ $t('common.more') }}
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="showSemanticSearchDialog">
                <el-icon><Aim /></el-icon>{{ $t('wiki.semanticSearch') }}
              </el-dropdown-item>
              <el-dropdown-item @click="showGraphQueryDialog">
                <el-icon><Share /></el-icon>{{ $t('wiki.graphQuery') }}
              </el-dropdown-item>
              <el-dropdown-item divided @click="showImportDialog">
                <el-icon><Upload /></el-icon>{{ $t('wiki.import') }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <button class="pc-glow-btn" @click="showCreateDialog">
          <el-icon><Plus /></el-icon> {{ $t('wiki.create') }}
        </button>
      </div>
    </div>

    <div class="wiki-layout">
      <!-- Sidebar -->
      <div class="wiki-sidebar">
        <div class="sidebar-header">
          <span>{{ $t('wiki.documentList') }}</span>
          <span class="sidebar-count">{{ wikiTree.length }}</span>
        </div>
        <el-empty v-if="!loading && wikiTree.length === 0" :description="$t('common.noData')" :image-size="48" />
        <div v-else class="wiki-tree-list">
          <div
            v-for="item in wikiTree"
            :key="item.id"
            class="tree-item"
            :class="{ active: currentWiki?.id === item.id }"
            @click="selectWiki(item)"
          >
            <span class="scope-dot" :class="'scope-' + (item.scope || 'user')"></span>
            <span class="item-title">{{ item.title }}</span>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="wiki-content">
        <div v-if="!currentWiki" class="empty-content">
          <el-empty :description="$t('wiki.selectWiki')" :image-size="80" />
        </div>

        <!-- View Mode -->
        <div v-else-if="!editing" class="wiki-view">
          <div class="view-toolbar">
            <h3 class="view-title">
              {{ currentWiki.title }}
              <el-tag v-if="currentWiki.scope" size="small" :type="currentWiki.scope === 'system' ? 'danger' : currentWiki.scope === 'org' ? 'warning' : ''" class="ml-2">
                {{ currentWiki.scope === 'user' ? $t('wiki.user') : currentWiki.scope === 'org' ? $t('wiki.org') : $t('wiki.system') }}
              </el-tag>
            </h3>
            <div class="view-actions">
              <el-button size="small" @click="startEdit">
                <el-icon><Edit /></el-icon> {{ $t('common.edit') }}
              </el-button>
              <el-button v-if="currentWiki.scope === 'user' && currentWiki.created_by === userStore.user?.id" size="small" type="success" @click="showWikiSubmitDialog">
                <el-icon><Upload /></el-icon> {{ $t('wiki.submitReview') }}
              </el-button>
              <el-button size="small" @click="showHistory">
                <el-icon><Clock /></el-icon> {{ $t('wiki.history') }}
              </el-button>
              <el-popconfirm :title="$t('wiki.confirmDeleteWiki', { title: currentWiki.title })" @confirm="deleteWiki">
                <template #reference>
                  <el-button size="small" type="danger">
                    <el-icon><Delete /></el-icon> {{ $t('common.delete') }}
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
          <div class="markdown-body" v-html="renderedContent"></div>
        </div>

        <!-- Edit Mode -->
        <div v-else class="wiki-editor">
          <div class="editor-toolbar">
            <span class="edit-label">{{ $t('common.edit') }}</span>
            <div class="edit-actions">
              <el-button size="small" @click="cancelEdit">{{ $t('common.cancel') }}</el-button>
              <el-button size="small" type="primary" @click="saveWiki">
                <el-icon><Check /></el-icon> {{ $t('common.save') }}
              </el-button>
            </div>
          </div>
          <el-input v-model="currentWiki.title" :placeholder="$t('wiki.titlePlaceholder')" class="title-input" />
          <el-input
            v-model="currentWiki.content"
            type="textarea"
            :rows="18"
            :placeholder="$t('wiki.contentPlaceholder')"
            class="content-input"
          />
        </div>
      </div>
    </div>

    <!-- Dialogs remain the same -->
    <el-dialog v-model="searchDialogVisible" :title="$t('wiki.searchResults')" width="600px">
      <el-empty v-if="searchResults.length === 0" :description="$t('wiki.noResults')" />
      <div v-else class="search-results">
        <div v-for="item in searchResults" :key="item.id" class="search-item" @click="selectSearchResult(item)">
          <div class="search-title">{{ item.title }}</div>
          <div class="search-snippet">{{ item.snippet || item.content?.slice(0, 100) }}</div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="semanticDialogVisible" :title="$t('wiki.semanticSearch')" width="600px">
      <el-input v-model="semanticQuery" :placeholder="$t('wiki.enterQuery')" @keyup.enter="doSemanticSearch">
        <template #append>
          <el-button :loading="semanticSearching" @click="doSemanticSearch">{{ $t('common.search') }}</el-button>
        </template>
      </el-input>
      <div v-if="semanticResults.length" class="search-results" style="margin-top: 16px">
        <div v-for="item in semanticResults" :key="item.id" class="search-item" @click="selectSearchResult(item)">
          <div class="search-title">{{ item.title }}</div>
          <div class="search-snippet">{{ item.snippet || item.content?.slice(0, 100) }}</div>
        </div>
      </div>
      <el-empty v-else-if="semanticQuery && !semanticSearching" :description="$t('wiki.noResults')" />
    </el-dialog>

    <el-dialog v-model="graphDialogVisible" :title="$t('wiki.graphQuery')" width="600px">
      <el-input v-model="graphQuery" :placeholder="$t('wiki.enterQuery')" @keyup.enter="doGraphQuery">
        <template #append>
          <el-button :loading="graphSearching" @click="doGraphQuery">{{ $t('common.search') }}</el-button>
        </template>
      </el-input>
      <div v-if="graphResults.length" class="search-results" style="margin-top: 16px">
        <div v-for="item in graphResults" :key="item.id" class="search-item" @click="selectSearchResult(item)">
          <div class="search-title">{{ item.title }}</div>
          <div class="search-snippet">{{ item.snippet || item.content?.slice(0, 100) }}</div>
        </div>
      </div>
      <el-empty v-else-if="graphQuery && !graphSearching" :description="$t('wiki.noResults')" />
    </el-dialog>

    <!-- Create Wiki Dialog -->
    <el-dialog v-model="createDialogVisible" :title="$t('wiki.create')" width="600px" class="cyber-dialog">
      <el-form :model="createForm" label-width="80px">
        <el-form-item :label="$t('common.name')" required>
          <el-input v-model="createForm.title" :placeholder="$t('wiki.titlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('wiki.visibleScope')">
          <el-select v-model="createForm.scope" style="width: 100%">
            <el-option :label="$t('wiki.scopeUserDesc')" value="user" />
            <el-option v-if="userStore.isOrgAdmin || userStore.isSuperAdmin" :label="$t('wiki.scopeOrgDesc')" value="org" />
            <el-option v-if="userStore.isSuperAdmin" :label="$t('wiki.scopeSystemDesc')" value="system" />
          </el-select>
          <div v-if="!userStore.isAdmin" class="form-tip">{{ $t('wiki.normalUserTip') }}</div>
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <div class="content-input-method">
            <el-radio-group v-model="contentInputMethod" size="small" style="margin-bottom: 10px">
              <el-radio-button value="paste">{{ $t('wiki.directInput') }}</el-radio-button>
              <el-radio-button value="upload">{{ $t('wiki.uploadFile') }}</el-radio-button>
            </el-radio-group>

            <el-input
              v-if="contentInputMethod === 'paste'"
              v-model="createForm.content"
              type="textarea"
              :rows="10"
              placeholder="Markdown 内容"
            />

            <el-upload
              v-else
              ref="wikiUploadRef"
              :auto-upload="false"
              :show-file-list="true"
              :limit="1"
              accept=".md,.txt,.markdown,.docx,.pdf"
              :on-change="handleWikiFileChange"
              drag
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text"><span v-html="$t('wiki.dragOrClick')"></span></div>
              <template #tip>
                <div class="el-upload__tip">{{ $t('wiki.supportedFormats') }}</div>
              </template>
            </el-upload>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creatingWiki" @click="createWiki">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>

    <!-- Wiki Submit Review Dialog -->
    <el-dialog v-model="wikiSubmitDialogVisible" :title="$t('wiki.submitReview')" width="520px" class="submit-review-dialog">
      <div v-if="submittingWiki" class="submit-review-body">
        <p class="submit-intro">
          {{ $t('wiki.submitReviewFor', { title: submittingWiki.title }) }}
        </p>
        <div class="scope-cards">
          <div class="scope-card" :class="{ selected: wikiTargetScope === 'org' }" @click="wikiTargetScope = 'org'">
            <div class="scope-card-icon org-icon"><el-icon :size="28"><OfficeBuilding /></el-icon></div>
            <div class="scope-card-body">
              <div class="scope-card-title"><el-tag type="warning" size="small">{{ $t('wiki.org') }}</el-tag></div>
              <p class="scope-card-desc">{{ $t('wiki.submitToOrgDesc') }}</p>
            </div>
            <div v-if="wikiTargetScope === 'org'" class="scope-card-check"><el-icon><Check /></el-icon></div>
          </div>
          <div class="scope-card" :class="{ selected: wikiTargetScope === 'system' }" @click="wikiTargetScope = 'system'">
            <div class="scope-card-icon sys-icon"><el-icon :size="28"><Monitor /></el-icon></div>
            <div class="scope-card-body">
              <div class="scope-card-title"><el-tag type="danger" size="small">{{ $t('wiki.system') }}</el-tag></div>
              <p class="scope-card-desc">{{ $t('wiki.submitToSystemDesc') }}</p>
            </div>
            <div v-if="wikiTargetScope === 'system'" class="scope-card-check"><el-icon><Check /></el-icon></div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="wikiSubmitDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submittingWikiApproval" @click="submitWikiForReview" class="cyber-btn primary-glow">{{ $t('wiki.submitReview') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" :title="$t('wiki.import')" width="600px">
      <el-form :model="importForm" label-width="80px">
        <el-form-item :label="$t('wiki.importPath')" required>
          <el-input v-model="importForm.path" :placeholder="$t('wiki.importPathPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('wiki.importTitle')">
          <el-input v-model="importForm.title" :placeholder="$t('wiki.importTitlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('wiki.docType')">
          <el-select v-model="importForm.doc_type" style="width: 100%">
            <el-option label="Markdown" value="markdown" />
            <el-option :label="$t('wiki.text')" value="text" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('wiki.importSource')">
          <el-input v-model="importForm.source" :placeholder="$t('wiki.importSourcePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('wiki.importTags')">
          <el-select v-model="importForm.tags" multiple filterable allow-create style="width: 100%" :placeholder="$t('wiki.addTags')" />
        </el-form-item>
        <el-form-item :label="$t('wiki.importContent')" required>
          <el-input v-model="importForm.content" type="textarea" :rows="10" :placeholder="$t('wiki.pasteContent')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- History Dialog -->
    <el-dialog v-model="historyDialogVisible" :title="$t('wiki.history')" width="550px">
      <el-table :data="historyItems" v-loading="historyLoading" max-height="400" :empty-text="$t('common.noData')">
        <el-table-column prop="version" :label="$t('wiki.version')" width="80" />
        <el-table-column :label="$t('wiki.changeSummary')" min-width="200">
          <template #default="{ row }">
            {{ row.summary || row.change_summary || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.time')" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="historyDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Search, MoreFilled, Plus, Check, Clock, Delete, Aim, Share, Upload, Edit, OfficeBuilding, Monitor } from '@element-plus/icons-vue'
import { wikiApi } from '@/api/wiki'
import { api } from '@/api'
import { useUserStore } from '@/stores/user'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const userStore = useUserStore()

const { t } = useI18n()
const loading = ref(false)
const editing = ref(false)
const searchQuery = ref('')
const wikiTree = ref<any[]>([])
const currentWiki = ref<any>(null)
const editSnapshot = ref<any>(null)
const searchResults = ref<any[]>([])
const searchDialogVisible = ref(false)
const searching = ref(false)

const semanticDialogVisible = ref(false)
const semanticQuery = ref('')
const semanticResults = ref<any[]>([])
const semanticSearching = ref(false)

const graphDialogVisible = ref(false)
const graphQuery = ref('')
const graphResults = ref<any[]>([])
const graphSearching = ref(false)

const importDialogVisible = ref(false)
const importForm = ref({ path: '', title: '', content: '', doc_type: 'markdown', source: '', tags: [] as string[] })
const importing = ref(false)

// Create dialog
const createDialogVisible = ref(false)
const creatingWiki = ref(false)
const createForm = ref({ title: '', content: '', scope: 'user' })
const contentInputMethod = ref<'paste' | 'upload'>('paste')
const wikiUploadRef = ref()

// Submit review
const wikiSubmitDialogVisible = ref(false)
const submittingWiki = ref<any>(null)
const wikiTargetScope = ref('org')
const submittingWikiApproval = ref(false)

const renderedContent = computed(() => {
  if (!currentWiki.value?.content) return '<p style="color: var(--pc-text-muted)">No content</p>'
  const raw = marked.parse(currentWiki.value.content) as string
  return DOMPurify.sanitize(raw)
})

async function fetchTree() {
  loading.value = true
  try {
    const res = await wikiApi.tree()
    wikiTree.value = res.data
  } catch (e: any) {
    ElMessage.error(t('wiki.loadFailed'))
  } finally {
    loading.value = false
  }
}

function selectWiki(data: any) {
  editing.value = false
  currentWiki.value = { ...data }
}

function startEdit() {
  editSnapshot.value = { title: currentWiki.value.title, content: currentWiki.value.content }
  editing.value = true
}

function cancelEdit() {
  if (editSnapshot.value) {
    currentWiki.value.title = editSnapshot.value.title
    currentWiki.value.content = editSnapshot.value.content
  }
  editing.value = false
}

async function saveWiki() {
  if (!currentWiki.value) return
  try {
    await wikiApi.update(currentWiki.value.id, {
      title: currentWiki.value.title,
      content: currentWiki.value.content
    })
    ElMessage.success(t('wiki.saved'))
    editing.value = false
    fetchTree()
  } catch (e: any) {
    ElMessage.error(t('wiki.saveFailed'))
  }
}

function showCreateDialog() {
  const defaultScope = userStore.isSuperAdmin ? 'system' : (userStore.isOrgAdmin ? 'org' : 'user')
  createForm.value = { title: '', content: '', scope: defaultScope }
  contentInputMethod.value = 'paste'
  createDialogVisible.value = true
}

async function handleWikiFileChange(file: any) {
  if (!file.raw) return
  const ext = file.raw.name.split('.').pop()?.toLowerCase() || ''

  if (ext === 'md' || ext === 'txt' || ext === 'markdown') {
    // Plain text: read directly
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = (e.target?.result as string) || ''
      createForm.value.content = text
      if (!createForm.value.title) {
        const match = text.match(/^#\s*(.+)$/m)
        if (match) createForm.value.title = match[1].trim()
      }
    }
    reader.readAsText(file.raw)
  } else {
    // Binary formats (docx, pdf): send to backend for parsing
    try {
      const formData = new FormData()
      formData.append('file', file.raw)
      const res = await api.post('/wiki/parse-file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const { title, content } = res.data
      createForm.value.content = content || ''
      if (!createForm.value.title && title) {
        createForm.value.title = title
      }
      ElMessage.success(t('wiki.fileParsed'))
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || t('wiki.fileParseFailed'))
    }
  }

  if (wikiUploadRef.value) wikiUploadRef.value.clearFiles()
}

async function createWiki() {
  if (!createForm.value.title) {
    ElMessage.warning(t('wiki.titleRequired'))
    return
  }
  creatingWiki.value = true
  try {
    await wikiApi.create({
      title: createForm.value.title,
      content: createForm.value.content || '',
      path: createForm.value.title,
      scope: createForm.value.scope,
    })
    ElMessage.success(t('wiki.created'))
    createDialogVisible.value = false
    fetchTree()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('wiki.createFailed'))
  } finally {
    creatingWiki.value = false
  }
}

function showWikiSubmitDialog() {
  if (!currentWiki.value) return
  submittingWiki.value = currentWiki.value
  wikiTargetScope.value = 'org'
  wikiSubmitDialogVisible.value = true
}

async function submitWikiForReview() {
  if (!submittingWiki.value) return
  submittingWikiApproval.value = true
  try {
    const wiki = submittingWiki.value
    await api.post('/approvals', {
      approval_type: wikiTargetScope.value === 'system' ? 'doc_to_system' : 'doc_to_org',
      title: `文档评审: ${wiki.title}`,
      resource_type: 'wiki',
      resource_id: String(wiki.id),
      target_scope: wikiTargetScope.value,
    })
    ElMessage.success(t('wiki.submittedReview'))
    wikiSubmitDialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('wiki.submitReviewFailed'))
  } finally {
    submittingWikiApproval.value = false
  }
}

async function deleteWiki() {
  if (!currentWiki.value) return
  try {
    await wikiApi.delete(currentWiki.value.id)
    currentWiki.value = null
    ElMessage.success(t('wiki.deleted'))
    fetchTree()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || t('wiki.deleteFailed'))
  }
}

const historyDialogVisible = ref(false)
const historyItems = ref<any[]>([])
const historyLoading = ref(false)

async function showHistory() {
  if (!currentWiki.value) return
  historyLoading.value = true
  historyDialogVisible.value = true
  try {
    const res = await wikiApi.history(currentWiki.value.id)
    historyItems.value = res.data.items || []
  } catch (e: any) {
    ElMessage.error(t('wiki.loadHistoryFailed'))
  } finally {
    historyLoading.value = false
  }
}

function showSemanticSearchDialog() { semanticDialogVisible.value = true }
async function doSemanticSearch() {
  if (!semanticQuery.value.trim()) return
  semanticSearching.value = true
  try {
    const res = await wikiApi.search({ q: semanticQuery.value })
    semanticResults.value = res.data.items
  } catch (e: any) { ElMessage.error(t('wiki.semanticSearchFailed')) }
  finally { semanticSearching.value = false }
}

function showGraphQueryDialog() { graphDialogVisible.value = true }
async function doGraphQuery() {
  if (!graphQuery.value.trim()) return
  graphSearching.value = true
  try {
    const res = await wikiApi.search({ q: graphQuery.value })
    graphResults.value = res.data.items
  } catch (e: any) { ElMessage.error(t('wiki.graphQueryFailed')) }
  finally { graphSearching.value = false }
}

function showImportDialog() {
  importForm.value = { path: '', title: '', content: '', doc_type: 'markdown', source: '', tags: [] }
  importDialogVisible.value = true
}

async function doImport() {
  if (!importForm.value.path || !importForm.value.content) {
    ElMessage.warning(t('wiki.fillPathAndContent'))
    return
  }
  importing.value = true
  try {
    await wikiApi.import({
      path: importForm.value.path,
      title: importForm.value.title || undefined,
      content: importForm.value.content,
      doc_type: importForm.value.doc_type,
      source: importForm.value.source || undefined,
      tags: importForm.value.tags.length > 0 ? importForm.value.tags : undefined
    })
    ElMessage.success(t('wiki.importSuccess'))
    importDialogVisible.value = false
    fetchTree()
  } catch (e: any) { ElMessage.error(t('wiki.importFailed')) }
  finally { importing.value = false }
}

async function search() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    const res = await wikiApi.search({ q: searchQuery.value })
    searchResults.value = res.data.items
    searchDialogVisible.value = true
  } catch (e: any) { ElMessage.error(t('wiki.searchFailed')) }
  finally { searching.value = false }
}

function selectSearchResult(item: any) {
  editing.value = false
  currentWiki.value = { ...item }
  searchDialogVisible.value = false
  semanticDialogVisible.value = false
  graphDialogVisible.value = false
}

function formatTime(dateStr: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

onMounted(() => { fetchTree() })
</script>

<style scoped lang="scss">
.wiki-page {
  .wiki-layout {
    display: flex;
    gap: 16px;
    height: calc(100vh - 180px);

    .wiki-sidebar {
      width: 240px;
      flex-shrink: 0;
      background: var(--pc-glass-bg);
      border: 1px solid var(--pc-glass-border);
      border-radius: var(--pc-radius-lg);
      overflow: hidden;
      display: flex;
      flex-direction: column;

      .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 16px;
        border-bottom: 1px solid var(--pc-border);
        font-size: 12px;
        font-weight: 600;
        color: var(--pc-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.8px;

        .sidebar-count {
          background: rgba(var(--pc-primary-rgb), 0.12);
          color: var(--pc-primary);
          font-size: 11px;
          font-weight: 700;
          min-width: 20px;
          height: 20px;
          line-height: 20px;
          text-align: center;
          border-radius: 10px;
          padding: 0 6px;
        }
      }

      .wiki-tree-list {
        flex: 1;
        overflow-y: auto;
        padding: 8px;

        .tree-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          border-radius: var(--pc-radius-md);
          cursor: pointer;
          transition: all 0.15s ease;
          border: 1px solid transparent;
          color: var(--pc-text-secondary);

          .scope-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
            opacity: 0.7;
            transition: opacity 0.15s;

            &.scope-user { background: var(--pc-accent-green); }
            &.scope-org { background: var(--pc-accent-orange); }
            &.scope-system { background: var(--pc-accent-red); }
          }

          .item-title {
            font-size: 13px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          &:hover {
            .scope-dot { opacity: 1; }
            background: rgba(var(--pc-primary-rgb), 0.06);
            color: var(--pc-text-primary);
          }

          &.active {
            background: rgba(var(--pc-primary-rgb), 0.1);
            border-color: rgba(var(--pc-primary-rgb), 0.2);
            color: var(--pc-primary);
            font-weight: 500;
            box-shadow: inset 3px 0 0 var(--pc-primary);
          }
        }
      }
    }

    .wiki-content {
      flex: 1;
      min-width: 0;
      background: var(--pc-glass-bg);
      border: 1px solid var(--pc-glass-border);
      border-radius: var(--pc-radius-lg);
      overflow-y: auto;

      .empty-content {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
      }

      // View mode
      .wiki-view {
        padding: 24px 32px;

        .view-toolbar {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding-bottom: 16px;
          margin-bottom: 8px;
          border-bottom: 1px solid var(--pc-border);

          .view-title {
            font-size: 22px;
            font-weight: 700;
            margin: 0;
            color: var(--pc-text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
          }

          .view-actions {
            display: flex;
            gap: 6px;
            flex-shrink: 0;
            flex-wrap: wrap;
            justify-content: flex-end;
          }
        }

        .markdown-body {
          font-size: 14px;
          line-height: 1.8;
          color: var(--pc-text-primary);

          :deep(h1) { font-size: 24px; font-weight: 700; margin: 24px 0 12px; border-bottom: 1px solid var(--pc-border); padding-bottom: 8px; }
          :deep(h2) { font-size: 20px; font-weight: 600; margin: 20px 0 10px; }
          :deep(h3) { font-size: 16px; font-weight: 600; margin: 16px 0 8px; }
          :deep(p) { margin: 8px 0; }
          :deep(ul), :deep(ol) { padding-left: 24px; margin: 8px 0; }
          :deep(li) { margin: 4px 0; }
          :deep(code) {
            background: rgba(var(--pc-primary-rgb), 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            font-size: 13px;
          }
          :deep(pre) {
            background: rgba(0,0,0,0.2);
            padding: 16px;
            border-radius: var(--pc-radius-md);
            overflow-x: auto;
            border: 1px solid var(--pc-border);

            code { background: transparent; padding: 0; }
          }
          :deep(blockquote) {
            border-left: 3px solid var(--pc-primary);
            padding: 4px 16px;
            margin: 12px 0;
            color: var(--pc-text-secondary);
            background: rgba(var(--pc-primary-rgb), 0.04);
            border-radius: 0 var(--pc-radius-sm) var(--pc-radius-sm) 0;
          }
          :deep(a) {
            color: var(--pc-primary);
            text-decoration: none;
            &:hover { text-decoration: underline; }
          }
          :deep(table) {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            th, td { border: 1px solid var(--pc-border); padding: 8px 12px; text-align: left; }
            th { background: rgba(var(--pc-primary-rgb), 0.06); font-weight: 600; }
          }
          :deep(hr) { border: none; border-top: 1px solid var(--pc-border); margin: 20px 0; }
        }
      }

      // Edit mode
      .wiki-editor {
        padding: 24px 32px;

        .editor-toolbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding: 10px 16px;
          background: rgba(var(--pc-accent-orange-rgb), 0.06);
          border: 1px solid rgba(var(--pc-accent-orange-rgb), 0.15);
          border-radius: var(--pc-radius-md);

          .edit-label {
            font-size: 13px;
            color: var(--pc-accent-orange);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;

            &::before {
              content: '';
              width: 6px;
              height: 6px;
              border-radius: 50%;
              background: var(--pc-accent-orange);
              animation: pulse-dot 1.5s ease-in-out infinite;
            }
          }

          .edit-actions {
            display: flex;
            gap: 6px;
          }
        }

        .title-input {
          margin-bottom: 16px;
          :deep(.el-input__wrapper) {
            font-size: 20px;
            font-weight: 700;
            background: var(--pc-bg-deep);
            border-color: var(--pc-border);
            box-shadow: none;
            padding: 8px 16px;
            border-radius: var(--pc-radius-md);
            &:hover, &.is-focus {
              border-color: var(--pc-primary);
              box-shadow: 0 0 0 2px rgba(var(--pc-primary-rgb), 0.1);
            }
          }
        }

        .content-input {
          :deep(.el-textarea__inner) {
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.8;
            min-height: 420px;
            background: var(--pc-bg-deep);
            border-color: var(--pc-border);
            border-radius: var(--pc-radius-md);
            padding: 16px;
            resize: vertical;
            &:hover {
              border-color: var(--pc-primary);
            }
            &:focus {
              border-color: var(--pc-primary);
              box-shadow: 0 0 0 2px rgba(var(--pc-primary-rgb), 0.1);
            }
          }
        }
      }
    }
  }

  .search-results {
    .search-item {
      padding: 12px;
      border: 1px solid var(--pc-border);
      border-radius: var(--pc-radius-md);
      margin-bottom: 8px;
      cursor: pointer;
      transition: all 0.15s;
      &:hover { border-color: var(--pc-primary); background: rgba(var(--pc-primary-rgb), 0.04); }
      .search-title { font-weight: 600; margin-bottom: 4px; }
      .search-snippet { font-size: 13px; color: var(--pc-text-secondary); }
    }
  }

  // Submit review dialog
  .submit-review-body {
    .submit-intro {
      color: var(--pc-text-secondary);
      margin-bottom: 20px;
      line-height: 1.8;
      .skill-highlight { color: var(--pc-text-primary); font-weight: 600; }
    }
    .scope-cards { display: flex; gap: 16px; }
    .scope-card {
      flex: 1; position: relative; display: flex; align-items: flex-start; gap: 16px;
      padding: 20px; border-radius: var(--pc-radius-lg); border: 2px solid var(--pc-border);
      background: var(--pc-bg-surface); cursor: pointer; transition: all 0.25s ease;
      &:hover { border-color: rgba(var(--pc-primary-rgb), 0.3); background: rgba(var(--pc-primary-rgb), 0.02); }
      &.selected { border-color: var(--pc-primary); background: rgba(var(--pc-primary-rgb), 0.06); box-shadow: 0 0 20px rgba(var(--pc-primary-rgb), 0.15); }
      .scope-card-icon {
        width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        &.org-icon { background: rgba(var(--pc-accent-orange-rgb), 0.12); color: var(--pc-accent-orange); }
        &.sys-icon { background: rgba(var(--pc-accent-red-rgb), 0.12); color: var(--pc-accent-red); }
      }
      .scope-card-body { flex: 1; min-width: 0; .scope-card-title { margin-bottom: 6px; } .scope-card-desc { color: var(--pc-text-muted); font-size: 13px; line-height: 1.5; margin: 0; } }
      .scope-card-check { position: absolute; top: 12px; right: 12px; width: 24px; height: 24px; border-radius: 50%; background: var(--pc-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 0 10px rgba(var(--pc-primary-rgb), 0.4); }
    }
  }

  .form-tip {
    font-size: 12px; color: var(--pc-text-muted); margin-top: 4px; line-height: 1.5;
  }

  .content-input-method {
    width: 100%;
    :deep(.el-upload-dragger) {
      background: var(--pc-bg-deep); border: 1px dashed var(--pc-border); border-radius: var(--pc-radius-md);
      &:hover { border-color: var(--pc-primary); }
    }
  }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

// Dialog glass styles
:deep(.cyber-dialog),
:deep(.submit-review-dialog) {
  .el-dialog {
    background: var(--pc-glass-bg) !important;
    border: 1px solid var(--pc-glass-border) !important;
    border-radius: var(--pc-radius-lg) !important;
    backdrop-filter: var(--pc-glass-blur);
    box-shadow: var(--pc-shadow-lg), var(--pc-shadow-glow);
    .el-dialog__header { border-bottom: 1px solid var(--pc-border); padding: 16px 20px; .el-dialog__title { color: var(--pc-text-primary) !important; font-weight: 600; } }
    .el-dialog__body { color: var(--pc-text-secondary); }
    .el-dialog__footer { border-top: 1px solid var(--pc-border); padding: 12px 20px; }
  }
}
</style>