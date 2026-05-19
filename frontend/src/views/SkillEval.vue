<template>
  <div class="skill-eval-page">
    <div class="pc-page-header">
      <h2 class="pc-page-title">{{ $t('skillEval.title') }}</h2>
      <div class="header-actions">
        <button class="pc-glow-btn secondary" v-if="optimizedContent" @click="showDiff = !showDiff">
          <el-icon><View /></el-icon>
          {{ showDiff ? '原始' : '对比' }}
        </button>
        <button class="pc-glow-btn" @click="runEvaluation" :disabled="!selectedSkill || evaluating">
          <el-icon v-if="evaluating"><Loading /></el-icon>
          <el-icon v-else><MagicStick /></el-icon>
          {{ evaluating ? '评估中...' : $t('skillEval.evaluate') }}
        </button>
      </div>
    </div>

    <div class="eval-container">
      <!-- ===== LEFT PANEL ===== -->
      <div class="left-panel">
        <div class="skill-selector">
          <el-select
            v-model="selectedSkillName"
            filterable
            :placeholder="$t('skillEval.selectSkill')"
            @change="onSkillChange"
            style="width: 100%"
            :loading="loadingSkills"
          >
            <el-option
              v-for="s in skills"
              :key="s.name"
              :label="s.display_name || s.name"
              :value="s.name"
            >
              <div class="skill-option">
                <span class="skill-option-name">{{ s.display_name || s.name }}</span>
                <el-tag size="small" :type="s.source === 'db' ? 'primary' : 'success'">
                  {{ s.source === 'db' ? 'DB' : 'File' }}
                </el-tag>
                <el-tag v-if="s.scope" size="small" type="info" class="scope-tag">
                  {{ getScopeLabel(s.scope) }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </div>

        <div class="file-tree-panel">
          <div class="panel-label">
            <el-icon><FolderOpened /></el-icon>
            <span>文件</span>
          </div>
          <el-tree
            :data="fileTree"
            :props="treeProps"
            node-key="path"
            :current-node-key="activeFile"
            highlight-current
            default-expand-all
            @node-click="onFileClick"
          >
            <template #default="{ data }">
              <span class="tree-node">
                <el-icon :size="14">
                  <Document v-if="data.type === 'file'" />
                  <Folder v-else />
                </el-icon>
                <span class="tree-node-name">{{ data.name }}</span>
                <span v-if="data.size" class="tree-node-size">{{ formatSize(data.size) }}</span>
              </span>
            </template>
          </el-tree>
        </div>

        <div class="file-content-panel">
          <div class="panel-label">
            <el-icon><Memo /></el-icon>
            <span>{{ activeFile || 'SKILL.md' }}</span>
            <button v-if="fileContent" class="copy-btn" @click="copyContent" :title="$t('common.copy')">
              <el-icon :size="14"><CopyDocument /></el-icon>
            </button>
          </div>
          <div class="content-viewer" v-if="fileContent">
            <div class="markdown-body" v-html="renderedContent"></div>
          </div>
          <div class="content-empty" v-else-if="selectedSkill">
            <el-icon :size="36"><Warning /></el-icon>
            <span>选择文件查看内容</span>
          </div>
          <div class="content-empty" v-else>
            <el-icon :size="36"><Document /></el-icon>
            <span>{{ $t('skillEval.selectSkillHint') }}</span>
          </div>
        </div>
      </div>

      <!-- ===== RIGHT PANEL ===== -->
      <div class="right-panel">
        <template v-if="evaluation">
          <!-- Overall Score -->
          <div class="score-overview">
            <div class="overall-circle">
              <el-progress
                type="circle"
                :percentage="evaluation.overall_score"
                :width="120"
                :stroke-width="8"
                :color="scoreColor(evaluation.overall_score)"
              />
              <div class="overall-label">综合评分</div>
            </div>
          </div>

          <!-- Dimension Cards -->
          <div class="dimension-section">
            <div class="section-title">维度评分</div>
            <div class="dimension-grid">
              <div
                class="dimension-card"
                v-for="dim in evaluation.dimensions"
                :key="dim.key"
              >
                <div class="dim-header">
                  <span class="dim-icon">{{ dimIcons[dim.key] || '📌' }}</span>
                  <span class="dim-name">{{ dim.label }}</span>
                  <span class="dim-score" :style="{ color: scoreColor(dim.score) }">
                    {{ dim.score }}<span class="dim-max">/100</span>
                  </span>
                </div>
                <el-progress
                  :percentage="dim.score"
                  :color="scoreColor(dim.score)"
                  :stroke-width="5"
                  :show-text="false"
                />
                <div class="dim-comment" v-if="dim.comment">{{ dim.comment }}</div>
              </div>
            </div>
          </div>

          <!-- Suggestions -->
          <div class="suggestions-section" v-if="evaluation.suggestions?.length">
            <div class="section-title">修改建议</div>
            <div class="suggestion-list">
              <div
                class="suggestion-item"
                v-for="(sg, i) in evaluation.suggestions"
                :key="i"
              >
                <span class="sg-index">{{ i + 1 }}</span>
                <div class="sg-body">
                  <div class="sg-title">{{ sg.title }}</div>
                  <div class="sg-detail" v-if="sg.detail">{{ sg.detail }}</div>
                </div>
                <el-tag
                  :type="sg.severity === 'high' ? 'danger' : sg.severity === 'medium' ? 'warning' : 'info'"
                  size="small"
                  effect="dark"
                >
                  {{ sg.severity === 'high' ? '高' : sg.severity === 'medium' ? '中' : '低' }}
                </el-tag>
              </div>
            </div>
          </div>

          <!-- Optimized Version -->
          <div class="optimized-section" v-if="optimizedContent">
            <div class="section-title">
              优化版本
              <el-tag v-if="showDiff" size="small" type="warning" style="margin-left: 8px">对比模式</el-tag>
            </div>
            <div class="optimized-editor" v-if="!showDiff">
              <el-input
                v-model="optimizedContent"
                type="textarea"
                :rows="14"
                class="monospace-input"
              />
              <div class="editor-actions">
                <el-button size="small" @click="copyOptimized">
                  <el-icon><CopyDocument /></el-icon> 复制
                </el-button>
                <el-button size="small" type="primary" @click="applyOptimization" class="cyber-btn primary-glow">
                  <el-icon><Check /></el-icon> 应用到技能
                </el-button>
              </div>
            </div>
            <div class="diff-view" v-else>
              <!-- Simple side-by-side diff -->
              <div class="diff-panes">
                <div class="diff-pane original">
                  <div class="diff-pane-title">原始版本</div>
                  <pre class="diff-content">{{ fileContent }}</pre>
                </div>
                <div class="diff-pane optimized">
                  <div class="diff-pane-title">优化版本</div>
                  <pre class="diff-content">{{ optimizedContent }}</pre>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- Placeholder when no evaluation -->
        <template v-else>
          <div class="eval-placeholder">
            <div class="placeholder-icon">
              <el-icon :size="48"><MagicStick /></el-icon>
            </div>
            <div class="placeholder-title">Skill 评估与优化</div>
            <div class="placeholder-desc">
              选择左侧 Skill，点击"评估"按钮，AI 将按 8 个维度对 Skill 进行打分并给出优化建议。
            </div>
            <div class="dimension-preview">
              <span class="dim-tag" v-for="d in defaultDimensions" :key="d.key">
                {{ d.label }}
              </span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { api } from '@/api'
import { marked } from 'marked'
import {
  MagicStick, Loading, View, FolderOpened, Document, Folder,
  Memo, Warning, CopyDocument, Check
} from '@element-plus/icons-vue'

const { t: $t } = useI18n()

// ── Skill list ──
interface SkillInfo {
  id?: number
  name: string
  display_name: string
  description: string
  source: string
  scope: string
  enabled: boolean
  skill_format: string
}

interface FileEntry {
  name: string
  path: string
  type: string
  size: number
  children?: FileEntry[]
}

interface DimScore {
  key: string
  label: string
  score: number
  comment: string
}

interface Suggestion {
  title: string
  detail: string
  severity: string
}

interface Evaluation {
  overall_score: number
  dimensions: DimScore[]
  suggestions: Suggestion[]
  optimized_content?: string
  summary: string
}

const loadingSkills = ref(false)
const skills = ref<SkillInfo[]>([])
const selectedSkillName = ref('')
const selectedSkill = ref<SkillInfo | null>(null)

// ── File tree ──
const fileTree = ref<FileEntry[]>([])
const treeProps = { children: 'children', label: 'name' }
const activeFile = ref('SKILL.md')
const fileContent = ref('')

// ── Frontmatter 解析 ──
function parseFrontmatter(content: string): { meta: Record<string, any>; body: string } {
  const match = content.match(/^---\n([\s\S]*?)\n---\n?/)
  if (!match) return { meta: {}, body: content }
  const yaml = match[1]
  const body = content.slice(match[0].length)
  const meta: Record<string, any> = {}
  const lines = yaml.split('\n')
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const colonIdx = line.indexOf(':')
    if (colonIdx === -1) { i++; continue }
    const key = line.slice(0, colonIdx).trim()
    let value = line.slice(colonIdx + 1).trim()
    // YAML 多行值: > (folded) 或 | (literal)
    if (value === '>' || value === '|' || value === '>-' || value === '|-') {
      const parts: string[] = []
      while (i + 1 < lines.length && (lines[i + 1].startsWith('  ') || lines[i + 1].startsWith('\t'))) {
        i++
        parts.push(lines[i].trim())
      }
      value = parts.join(' ')
      // 去引号
    } else if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1)
    }
    if (value.startsWith('[') && value.endsWith(']')) {
      meta[key] = value.slice(1, -1).split(',').map(s => s.trim())
    } else {
      meta[key] = value
    }
    i++
  }
  return { meta, body }
}

// ── File extension → render mode ──
const isMarkdownFile = computed(() => {
  const name = activeFile.value.toLowerCase()
  return name.endsWith('.md') || name.endsWith('.markdown')
})

const codeExtensions = ['.py', '.js', '.ts', '.json', '.yaml', '.yml', '.sh', '.bat', '.ps1',
  '.jsx', '.tsx', '.vue', '.css', '.scss', '.html', '.xml', '.toml', '.ini', '.cfg',
  '.sql', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.rb', '.php', '.swift',
  '.txt', '.rst', '.csv', '.log']

const isCodeFile = computed(() => {
  const name = activeFile.value.toLowerCase()
  return codeExtensions.some(ext => name.endsWith(ext))
})

// ── Rendered content ──
const renderedContent = computed(() => {
  if (!fileContent.value) return ''
  if (isMarkdownFile.value) {
    const { body } = parseFrontmatter(fileContent.value)
    try {
      return marked.parse(body) as string
    } catch {
      return `<pre>${escapeHtml(body)}</pre>`
    }
  }
  if (isCodeFile.value) {
    const ext = activeFile.value.split('.').pop()?.toLowerCase() || ''
    return `<pre class="code-block"><code class="language-${ext}">${escapeHtml(fileContent.value)}</code></pre>`
  }
  return `<pre class="code-block"><code>${escapeHtml(fileContent.value)}</code></pre>`
})

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// ── Evaluation ──
const evaluating = ref(false)
const evaluation = ref<Evaluation | null>(null)
const optimizedContent = ref('')
const showDiff = ref(false)

// ── Default dimensions ──
const defaultDimensions = [
  { key: 'clarity', label: '清晰度' },
  { key: 'completeness', label: '完整性' },
  { key: 'conciseness', label: '简洁度' },
  { key: 'structure', label: '结构规范' },
  { key: 'trigger_specificity', label: '触发精准' },
  { key: 'dependencies', label: '依赖声明' },
  { key: 'config', label: '配置合理性' },
  { key: 'safety', label: '安全性' },
]

const dimIcons: Record<string, string> = {
  clarity: '💡',
  completeness: '📋',
  conciseness: '✂️',
  structure: '🏗️',
  trigger_specificity: '🎯',
  dependencies: '🔗',
  config: '⚙️',
  safety: '🛡️',
}

// ── Methods ──
function getScopeLabel(scope: string): string {
  const m: Record<string, string> = { user: '本地', org: '组织', system: '系统' }
  return m[scope] || scope
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

function scoreColor(score: number): string {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

async function fetchSkills() {
  loadingSkills.value = true
  try {
    const res = await api.get('/skill-eval/skills')
    skills.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '加载技能列表失败')
  } finally {
    loadingSkills.value = false
  }
}

async function onSkillChange(name: string) {
  const skill = skills.value.find(s => s.name === name)
  selectedSkill.value = skill || null
  evaluation.value = null
  optimizedContent.value = ''
  activeFile.value = 'SKILL.md'
  fileContent.value = ''

  if (!skill) return

  // 加载文件树
  try {
    const res = await api.get(`/skill-eval/skills/${encodeURIComponent(name)}/tree`)
    fileTree.value = res.data.tree || []

    // 如果有直接返回的 content（DB 技能），直接显示
    if (res.data.content) {
      setFileContent(res.data.content)
    } else if (fileTree.value.length > 0) {
      // 加载第一个文件的内容
      const firstFile = fileTree.value.find((f: FileEntry) => f.type === 'file')
      if (firstFile) {
        activeFile.value = firstFile.name
        await loadFileContent(firstFile.path)
      }
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '加载文件树失败')
  }
}

async function onFileClick(data: FileEntry) {
  if (data.type !== 'file') return
  activeFile.value = data.name
  await loadFileContent(data.path)
}

function setFileContent(content: string) {
  fileContent.value = content
}

async function loadFileContent(path: string) {
  try {
    const res = await api.get(
      `/skill-eval/skills/${encodeURIComponent(selectedSkillName.value)}/file`,
      { params: { path } }
    )
    setFileContent(res.data.content || '')
  } catch (e: any) {
    ElMessage.error('加载文件内容失败')
    fileContent.value = ''
  }
}

async function runEvaluation() {
  if (!selectedSkillName.value) return
  evaluating.value = true
  evaluation.value = null

  // 始终以 SKILL.md 内容为准
  let skillMdContent = fileContent.value
  if (activeFile.value !== 'SKILL.md') {
    try {
      const res = await api.get(
        `/skill-eval/skills/${encodeURIComponent(selectedSkillName.value)}/file`,
        { params: { path: 'SKILL.md' } }
      )
      skillMdContent = res.data.content || ''
    } catch { /* 保持当前内容 */ }
  }

  try {
    const res = await api.post(
      `/skill-eval/skills/${encodeURIComponent(selectedSkillName.value)}/evaluate`,
      { content: skillMdContent }
    )
    evaluation.value = res.data
    optimizedContent.value = res.data.optimized_content || ''
  } catch (e: any) {
    // 如果后端评估 API 还没实现，展示占位数据
    ElMessage.warning('评估 API 尚未接入，显示模拟评估结果')
    evaluation.value = generateMockEvaluation(skillMdContent)
    optimizedContent.value = evaluation.value.optimized_content || ''
  } finally {
    evaluating.value = false
  }
}

function generateMockEvaluation(skillMdContent: string): Evaluation {
  const dims: DimScore[] = defaultDimensions.map(d => ({
    key: d.key,
    label: d.label,
    score: 50 + Math.floor(Math.random() * 45),
    comment: '待 AI 评估...',
  }))
  const total = Math.round(dims.reduce((sum, d) => sum + d.score, 0) / dims.length)
  return {
    overall_score: total,
    dimensions: dims,
    suggestions: [
      { title: '评估功能即将上线', detail: '后端评估 API 开发中，当前为占位数据', severity: 'medium' },
    ],
    optimized_content: skillMdContent,
    summary: '评估 API 尚未接入。',
  }
}

async function applyOptimization() {
  if (!optimizedContent.value || !selectedSkill.value) return
  if (selectedSkill.value.source === 'db' && selectedSkill.value.id) {
    try {
      await api.put(`/skills/${selectedSkill.value.id}`, { content: optimizedContent.value })
      ElMessage.success('优化版本已应用')
      fileContent.value = optimizedContent.value
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '应用失败')
    }
  } else {
    // 文件系统技能 — 提示用户手动更新
    ElMessage.info('文件系统技能暂不支持自动保存，请手动复制优化内容')
  }
}

function copyContent() {
  navigator.clipboard.writeText(fileContent.value)
  ElMessage.success($t('common.copied'))
}

function copyOptimized() {
  navigator.clipboard.writeText(optimizedContent.value)
  ElMessage.success($t('common.copied'))
}

onMounted(fetchSkills)
</script>

<style scoped lang="scss">
.skill-eval-page {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

// ── Eval Container ──
.eval-container {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

// ── Left Panel ──
.left-panel {
  width: 42%;
  min-width: 380px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.skill-selector {
  flex-shrink: 0;

  .skill-option {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;

    .skill-option-name {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .scope-tag {
      margin-left: auto;
    }
  }

  :deep(.el-select) {
    .el-input__wrapper {
      background: var(--pc-glass-bg) !important;
      border: 1px solid var(--pc-glass-border) !important;
      box-shadow: none !important;
    }
    .el-input__inner {
      color: var(--pc-text-primary);
    }
  }
}

.file-tree-panel {
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-md);
  backdrop-filter: var(--pc-glass-blur);
  flex-shrink: 0;
  max-height: 200px;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .panel-label {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 600;
    color: var(--pc-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--pc-border);
  }

  :deep(.el-tree) {
    background: transparent;
    padding: 6px 8px;
    overflow-y: auto;
    flex: 1;

    .el-tree-node__content {
      padding: 3px 6px;
      border-radius: 4px;
      color: var(--pc-text-secondary);
      transition: all 0.15s;

      &:hover {
        background: rgba(var(--pc-primary-rgb), 0.06);
        color: var(--pc-text-primary);
      }
    }

    .el-tree-node.is-current > .el-tree-node__content {
      background: rgba(var(--pc-primary-rgb), 0.1);
      color: var(--pc-primary);
    }
  }

  .tree-node {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;

    .tree-node-name {
      flex: 1;
    }

    .tree-node-size {
      font-size: 11px;
      color: var(--pc-text-muted);
    }
  }
}

.file-content-panel {
  flex: 1;
  min-height: 0;
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-md);
  backdrop-filter: var(--pc-glass-blur);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .panel-label {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 600;
    color: var(--pc-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--pc-border);
    flex-shrink: 0;

    span {
      flex: 1;
    }

    .copy-btn {
      background: none;
      border: none;
      color: var(--pc-text-muted);
      cursor: pointer;
      padding: 2px 4px;
      border-radius: 4px;
      transition: all 0.15s;

      &:hover {
        color: var(--pc-primary);
        background: rgba(var(--pc-primary-rgb), 0.08);
      }
    }
  }

  .content-viewer {
    flex: 1;
    overflow-y: auto;
    padding: 14px 16px;
  }


  .content-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: var(--pc-text-muted);
    font-size: 13px;
  }
}

// ── Markdown ──
.markdown-body {
  color: var(--pc-text-primary);
  font-size: 13.5px;
  line-height: 1.7;

  :deep(h1) { font-size: 1.5em; margin: 0 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--pc-border); }
  :deep(h2) { font-size: 1.25em; margin: 16px 0 8px; }
  :deep(h3) { font-size: 1.1em; margin: 12px 0 6px; }
  :deep(p) { margin: 0 0 10px; }
  :deep(code) {
    background: var(--pc-bg-deep);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.9em;
  }
  :deep(pre) {
    background: var(--pc-bg-deep);
    border: 1px solid var(--pc-border);
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    code { background: none; padding: 0; }
  }
  :deep(ul), :deep(ol) { padding-left: 20px; margin: 0 0 10px; }
  :deep(li) { margin: 2px 0; }
  :deep(blockquote) {
    border-left: 3px solid var(--pc-primary);
    padding-left: 12px;
    margin: 0 0 10px;
    color: var(--pc-text-muted);
  }
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    th, td {
      border: 1px solid var(--pc-border);
      padding: 6px 10px;
      text-align: left;
    }
    th { background: var(--pc-bg-surface); font-weight: 600; }
  }
}

// ── Code blocks (non-Markdown files) ──
.code-block {
  background: var(--pc-bg-deep);
  border: 1px solid var(--pc-border);
  border-radius: 8px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 0;

  code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', monospace;
    font-size: 12.5px;
    color: var(--pc-text-primary);
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
    background: none;
    padding: 0;
  }
}

// ── Right Panel ──
.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
}

.score-overview {
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  backdrop-filter: var(--pc-glass-blur);
  padding: 24px;
  display: flex;
  justify-content: center;

  .overall-circle {
    text-align: center;

    .overall-label {
      margin-top: 8px;
      font-size: 13px;
      color: var(--pc-text-muted);
      font-weight: 500;
    }
  }

  &.placeholder {
    justify-content: center;
    align-items: center;
    padding: 48px 24px;
    flex-direction: column;
    gap: 10px;
    color: var(--pc-text-muted);
    font-size: 13px;
  }
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--pc-text-primary);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dimension-section {
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  backdrop-filter: var(--pc-glass-blur);
  padding: 16px;
}

.dimension-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.dimension-card {
  background: var(--pc-bg-surface);
  border: 1px solid var(--pc-border);
  border-radius: var(--pc-radius-md);
  padding: 12px;

  .dim-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;

    .dim-icon { font-size: 14px; }
    .dim-name {
      flex: 1;
      font-size: 12.5px;
      font-weight: 500;
      color: var(--pc-text-primary);
    }
    .dim-score {
      font-size: 16px;
      font-weight: 700;
      .dim-max { font-size: 10px; font-weight: 400; color: var(--pc-text-muted); }
    }
  }

  .dim-comment {
    margin-top: 5px;
    font-size: 11.5px;
    color: var(--pc-text-muted);
    line-height: 1.4;
  }
}

.suggestions-section {
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  backdrop-filter: var(--pc-glass-blur);
  padding: 16px;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: var(--pc-bg-surface);
  border: 1px solid var(--pc-border);
  border-radius: var(--pc-radius-md);

  .sg-index {
    flex-shrink: 0;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(var(--pc-primary-rgb), 0.1);
    color: var(--pc-primary);
    font-size: 11px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .sg-body {
    flex: 1;
    .sg-title { font-size: 13px; font-weight: 600; color: var(--pc-text-primary); }
    .sg-detail { font-size: 12px; color: var(--pc-text-muted); margin-top: 2px; line-height: 1.4; }
  }
}

.optimized-section {
  background: var(--pc-glass-bg);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-lg);
  backdrop-filter: var(--pc-glass-blur);
  padding: 16px;
}

.optimized-editor {
  .monospace-input :deep(textarea) {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 12.5px;
    background: var(--pc-bg-deep);
    color: var(--pc-text-primary);
    border: 1px solid var(--pc-border);
    border-radius: 6px;
  }

  .editor-actions {
    display: flex;
    gap: 8px;
    margin-top: 10px;
    justify-content: flex-end;
  }
}

.diff-view {
  .diff-panes {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .diff-pane {
    .diff-pane-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--pc-text-muted);
      text-transform: uppercase;
      margin-bottom: 6px;
      padding: 4px 8px;
      background: var(--pc-bg-surface);
      border-radius: 4px;
    }

    .diff-content {
      background: var(--pc-bg-deep);
      border: 1px solid var(--pc-border);
      border-radius: 6px;
      padding: 10px;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 11.5px;
      color: var(--pc-text-primary);
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 420px;
      overflow-y: auto;
      line-height: 1.5;
    }
  }
}

// ── Placeholder ──
.eval-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  text-align: center;

  .placeholder-icon {
    width: 80px;
    height: 80px;
    border-radius: 20px;
    background: rgba(var(--pc-primary-rgb), 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--pc-primary);
    margin-bottom: 16px;
  }

  .placeholder-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--pc-text-primary);
    margin-bottom: 8px;
  }

  .placeholder-desc {
    font-size: 13px;
    color: var(--pc-text-muted);
    max-width: 360px;
    line-height: 1.6;
    margin-bottom: 16px;
  }

  .dimension-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;

    .dim-tag {
      padding: 4px 12px;
      border-radius: 20px;
      background: rgba(var(--pc-primary-rgb), 0.06);
      border: 1px solid rgba(var(--pc-primary-rgb), 0.15);
      color: var(--pc-primary);
      font-size: 12px;
      font-weight: 500;
    }
  }
}

// ── Cyberpunk buttons ──
.cyber-btn.primary-glow {
  box-shadow: 0 0 14px rgba(var(--pc-primary-rgb), 0.3);
  transition: box-shadow 0.25s;
  &:hover { box-shadow: 0 0 22px rgba(var(--pc-primary-rgb), 0.5); }
}
</style>
