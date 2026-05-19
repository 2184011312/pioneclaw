<template>
  <div class="runners-page">
    <!-- 顶部统计卡片 - 始终显示，在 Tabs 外部 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon total">
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_runners }}</div>
          <div class="stat-label">{{ $t('runner.totalNodes') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon online">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.online_count }}</div>
          <div class="stat-label">{{ $t('runner.onlineCount') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon pending">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pending_count || 0 }}</div>
          <div class="stat-label">{{ $t('runner.pendingCount') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon tasks">
          <el-icon><List /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_tasks }}</div>
          <div class="stat-label">{{ $t('runner.totalTasks') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">
          <el-icon><Select /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.success_rate }}%</div>
          <div class="stat-label">{{ $t('runner.successRate') }}</div>
        </div>
      </div>
    </div>

    <!-- Tab 布局 -->
    <el-tabs v-model="activeTab" @tab-change="onTabChange" class="runner-tabs">
      <!-- ========== Tab 1: Runner 列表（仅管理员可见） ========== -->
      <el-tab-pane v-if="isAdmin" label="Runner 列表" name="list">
        <div class="toolbar">
          <div class="toolbar-spacer"></div>
          <el-button type="primary" @click="showDialog()">
            <el-icon><Plus /></el-icon>{{ $t('runner.add') }}
          </el-button>
        </div>

        <!-- 接入信息卡片 -->
        <el-card class="connection-card" shadow="never">
          <div class="connection-header">
            <div class="connection-title">
              <el-icon><Link /></el-icon>
              <span>{{ $t('runner.centerAddress') }}</span>
            </div>
            <el-tag type="info" size="small">{{ $t('runner.applyEndpoint') }}</el-tag>
          </div>
          <div class="connection-content">
            <div class="connection-item">
              <span class="label">HTTP {{ $t('common.details') }}:</span>
              <code>{{ centerInfo.http_address }}</code>
              <el-button type="primary" link size="small" @click="copyToClipboard(centerInfo.http_address)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </div>
            <div class="connection-item">
              <span class="label">{{ $t('runner.applyEndpoint') }}:</span>
              <code>{{ centerInfo.apply_endpoint }}</code>
              <el-button type="primary" link size="small" @click="copyToClipboard(centerInfo.apply_endpoint)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- Runner 列表 -->
        <el-card class="list-card" shadow="never">
          <template #header>
            <div class="list-header">
              <div class="filter-tabs">
                <span
                  v-for="tab in statusTabs"
                  :key="tab.value"
                  :class="['tab', { active: filterStatus === tab.value }]"
                  @click="filterStatus = tab.value; fetchRunners()"
                >
                  {{ tab.label }}
                  <el-badge v-if="tab.count && tab.value !== ''" :value="tab.count" :max="99" class="tab-badge" />
                </span>
              </div>
              <el-input
                v-model="searchKeyword"
                :placeholder="$t('common.search')"
                prefix-icon="Search"
                clearable
                style="width: 200px"
                @input="fetchRunners"
              />
            </div>
          </template>

          <div class="runner-grid" v-loading="loading">
            <div
              v-for="runner in filteredRunners"
              :key="runner.id"
              class="runner-card"
              :class="runner.status"
            >
              <div class="card-head">
                <div class="head-left">
                  <span :class="['status-dot', runner.status]"></span>
                  <span class="card-name">{{ runner.display_name || runner.name }}</span>
                  <span v-if="runner.version" class="tag-version">v{{ runner.version }}</span>
                </div>
                <el-dropdown trigger="click">
                  <el-button link class="btn-menu"><el-icon><MoreFilled /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="showDetail(runner)">{{ $t('runner.viewDetail') }}</el-dropdown-item>
                      <el-dropdown-item v-if="runner.status === 'pending'" @click="showAssociateDialog(runner)">{{ $t('runner.associateUser') }}</el-dropdown-item>
                      <el-dropdown-item @click="showDialog(runner)" v-if="runner.status !== 'pending'">{{ $t('common.edit') }}</el-dropdown-item>
                      <el-dropdown-item v-if="runner.status === 'online'" @click="setOffline(runner.id)">{{ $t('runner.setOffline') }}</el-dropdown-item>
                      <!-- 新增管理操作 -->
                      <el-dropdown-item v-if="isAdmin" @click="showBindDialog(runner)">绑定用户</el-dropdown-item>
                      <el-dropdown-item v-if="isAdmin && runner.user_id" @click="handleUnbind(runner)">解绑用户</el-dropdown-item>
                      <el-dropdown-item v-if="isAdmin" @click="handleRotateToken(runner)">轮换 Token</el-dropdown-item>
                      <el-dropdown-item v-if="isAdmin" @click="switchToDiagnostics(runner)">诊断</el-dropdown-item>
                      <el-dropdown-item divided @click="deleteRunner(runner)" v-if="runner.status !== 'pending'">
                        <span style="color: #f56c6c">{{ $t('common.delete') }}</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>

              <div class="card-info">
                <span v-if="runner.platform" class="info-label">{{ runner.platform }}</span>
                <code v-if="runner.host">{{ runner.host }}:{{ runner.port || 20006 }}</code>
                <span v-if="runner.username" class="info-user">
                  <el-icon><User /></el-icon>{{ runner.username }}
                </span>
              </div>

              <div class="card-stats">
                <div class="stat-col">
                  <span class="stat-num ok">{{ runner.success_tasks || 0 }}</span>
                  <span class="stat-lbl">{{ $t('common.success') }}</span>
                </div>
                <div class="stat-col">
                  <span class="stat-num" :class="{ fail: (runner.failed_tasks || 0) > 0 }">{{ runner.failed_tasks || 0 }}</span>
                  <span class="stat-lbl">{{ $t('common.failed') }}</span>
                </div>
                <div class="stat-col">
                  <span class="stat-num">{{ runner.total_tasks || 0 }}</span>
                  <span class="stat-lbl">{{ $t('common.total') }}</span>
                </div>
              </div>

              <div class="card-foot">
                <div class="foot-left">
                  <span v-if="runner.last_heartbeat" class="heartbeat" :class="isRecent(runner.last_heartbeat) ? 'hb-ok' : 'hb-stale'">
                    <el-icon><Timer /></el-icon>{{ formatRelativeTime(runner.last_heartbeat) }}
                  </span>
                  <span v-else class="heartbeat hb-stale">
                    <el-icon><WarningFilled /></el-icon>{{ $t('runner.noHeartbeat') }}
                  </span>
                  <span v-if="runner.current_task && runner.status === 'online'" class="task-info">
                    <el-icon class="task-icon"><Loading /></el-icon>{{ runner.current_task }}
                  </span>
                </div>
              </div>

              <div class="card-actions" v-if="runner.status === 'pending'">
                <el-button type="success" size="small" @click="approveRunner(runner.id, true)">
                  <el-icon><CircleCheck /></el-icon>同意
                </el-button>
                <el-button type="primary" size="small" v-if="!runner.user_id" @click="showAssociateDialog(runner)">
                  <el-icon><Link /></el-icon>{{ $t('runner.associateUser') }}
                </el-button>
                <el-button type="danger" size="small" @click="showRejectDialog(runner)">
                  <el-icon><CloseBold /></el-icon>{{ $t('runner.reject') }}
                </el-button>
              </div>
            </div>

            <el-empty v-if="filteredRunners.length === 0" :description="$t('common.noData')" :image-size="120">
              <template #image>
                <el-icon :size="80" color="#c0c4cc"><Monitor /></el-icon>
              </template>
              <el-button type="primary" @click="showDialog()">{{ $t('runner.add') }}</el-button>
            </el-empty>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ========== Tab 2: 诊断面板（管理员可见）========== -->
      <el-tab-pane
        v-if="userStore.isSuperAdmin || userStore.isOrgAdmin"
        label="诊断面板"
        name="diagnostics"
      >
        <div class="diagnostics-panel">
          <div class="diag-toolbar">
            <el-select
              v-model="selectedDiagnosticsRunnerId"
              placeholder="选择 Runner"
              style="width: 300px"
              filterable
              @change="onDiagnosticsRunnerChange"
            >
              <el-option
                v-for="r in runners"
                :key="r.id"
                :label="r.display_name || r.name"
                :value="r.id"
              />
            </el-select>
          </div>

          <div v-if="!selectedDiagnosticsRunnerId" class="diag-placeholder">
            <el-empty description="请从上方下拉框选择一个 Runner 以查看诊断信息" :image-size="100" />
          </div>

          <div v-else v-loading="diagLoading" class="diag-content">
            <!-- 资源使用 -->
            <el-card shadow="never" class="diag-card">
              <template #header><span class="diag-card-title">资源使用</span></template>
              <div class="resource-bars">
                <div class="resource-item">
                  <div class="resource-label">CPU</div>
                  <el-progress
                    :percentage="diagnosticsData.cpu_percent"
                    :color="progressColor(diagnosticsData.cpu_percent)"
                    :stroke-width="16"
                  />
                </div>
                <div class="resource-item">
                  <div class="resource-label">内存</div>
                  <el-progress
                    :percentage="diagnosticsData.memory_percent"
                    :color="progressColor(diagnosticsData.memory_percent)"
                    :stroke-width="16"
                  />
                </div>
                <div class="resource-item">
                  <div class="resource-label">磁盘</div>
                  <el-progress
                    :percentage="diagnosticsData.disk_percent"
                    :color="progressColor(diagnosticsData.disk_percent)"
                    :stroke-width="16"
                  />
                </div>
              </div>
            </el-card>

            <!-- 进程列表 -->
            <el-card shadow="never" class="diag-card">
              <template #header><span class="diag-card-title">进程列表</span></template>
              <el-table :data="diagnosticsData.processes || []" size="small" max-height="300" stripe>
                <el-table-column prop="pid" label="PID" width="80" />
                <el-table-column prop="name" label="进程名" min-width="150" />
                <el-table-column prop="cpu_percent" label="CPU %" width="100" />
                <el-table-column prop="memory_percent" label="内存 %" width="100" />
              </el-table>
              <el-empty v-if="!diagnosticsData.processes?.length" description="暂无进程数据" :image-size="60" />
            </el-card>

            <!-- 连接事件 -->
            <el-card shadow="never" class="diag-card">
              <template #header><span class="diag-card-title">连接事件</span></template>
              <div class="connection-timeline" v-if="connectionEvents.length > 0">
                <el-timeline>
                  <el-timeline-item
                    v-for="(evt, idx) in connectionEvents"
                    :key="idx"
                    :timestamp="formatTime(evt.timestamp)"
                    :type="evt.event_type === 'connected' ? 'success' : evt.event_type === 'disconnected' ? 'danger' : 'info'"
                  >
                    <span class="event-type">{{ evt.event_type }}</span>
                    <span v-if="evt.detail" class="event-detail"> — {{ evt.detail }}</span>
                  </el-timeline-item>
                </el-timeline>
              </div>
              <el-empty v-else description="暂无连接事件" :image-size="60" />
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 3: 版本管理（超管可见）========== -->
      <el-tab-pane
        v-if="userStore.isSuperAdmin"
        label="版本管理"
        name="versions"
      >
        <div class="versions-panel" v-loading="releasesLoading">
          <el-row :gutter="24">
            <!-- 左侧：版本列表 -->
            <el-col :span="14">
              <el-card shadow="never" class="version-card">
                <template #header>
                  <div class="version-header">
                    <span class="diag-card-title">版本列表</span>
                    <el-select
                      v-model="releasePlatformFilter"
                      placeholder="按平台筛选"
                      clearable
                      style="width: 140px"
                      @change="fetchReleases"
                    >
                      <el-option label="Windows" value="windows" />
                      <el-option label="Linux" value="linux" />
                      <el-option label="macOS" value="macos" />
                    </el-select>
                  </div>
                </template>
                <el-table :data="releases" size="small" max-height="450" stripe>
                  <el-table-column prop="version" label="版本" width="100" />
                  <el-table-column prop="platform" label="平台" width="90">
                    <template #default="{ row }">
                      <el-tag size="small">{{ row.platform }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
                  <el-table-column prop="created_at" label="日期" width="160">
                    <template #default="{ row }">
                      {{ formatTime(row.created_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="最新" width="70" align="center">
                    <template #default="{ row }">
                      <el-tag v-if="row.is_latest" type="success" size="small">最新</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="160" align="center">
                    <template #default="{ row }">
                      <el-button
                        v-if="!row.is_latest"
                        type="primary"
                        link
                        size="small"
                        @click="handleSetLatest(row)"
                      >
                        设为最新
                      </el-button>
                      <el-button
                        type="danger"
                        link
                        size="small"
                        @click="handleDeleteVersion(row)"
                      >
                        删除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="releases.length === 0" description="暂无版本" :image-size="80" />
              </el-card>
            </el-col>

            <!-- 右侧：上传表单 -->
            <el-col :span="10">
              <el-card shadow="never" class="version-card">
                <template #header><span class="diag-card-title">上传新版本</span></template>
                <el-form :model="releaseForm" label-width="80px">
                  <el-form-item label="版本号" required>
                    <el-input v-model="releaseForm.version" placeholder="1.0.0" />
                  </el-form-item>
                  <el-form-item label="平台" required>
                    <el-select v-model="releaseForm.platform" style="width: 100%">
                      <el-option label="Windows" value="windows" />
                      <el-option label="Linux" value="linux" />
                      <el-option label="macOS" value="macos" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="更新说明">
                    <el-input
                      v-model="releaseForm.release_notes"
                      type="textarea"
                      :rows="3"
                      placeholder="可选"
                    />
                  </el-form-item>
                  <el-form-item label="安装包" required>
                    <el-upload
                      ref="uploadRef"
                      :auto-upload="false"
                      :limit="1"
                      :on-change="handleReleaseFileChange"
                      :on-remove="() => releaseFile = null"
                      :file-list="releaseFileList"
                      drag
                    >
                      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                      <div class="el-upload__text">拖拽或点击上传安装包</div>
                    </el-upload>
                  </el-form-item>
                  <el-form-item>
                    <el-button
                      type="primary"
                      :loading="releaseUploading"
                      :disabled="!releaseForm.version || !releaseForm.platform || !releaseFile"
                      @click="handleUploadRelease"
                    >
                      <el-icon><Upload /></el-icon>上传
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 4: 我的 Runner ========== -->
      <el-tab-pane label="我的 Runner" name="my">
        <div class="my-runners-panel" v-loading="myBindingsLoading">
          <div class="runner-grid" v-if="myBindings.length > 0">
            <div
              v-for="runner in myBindings"
              :key="runner.id"
              class="runner-card"
              :class="runner.status"
            >
              <div class="card-head">
                <div class="head-left">
                  <span :class="['status-dot', runner.status]"></span>
                  <span class="card-name">{{ runner.display_name || runner.name }}</span>
                  <el-tag v-if="runner.id === defaultRunnerId" type="warning" size="small">默认</el-tag>
                </div>
              </div>

              <div class="card-info">
                <span v-if="runner.platform" class="info-label">{{ runner.platform }}</span>
                <code v-if="runner.host">{{ runner.host }}:{{ runner.port || 20006 }}</code>
              </div>

              <div class="card-foot">
                <div class="foot-left">
                  <span v-if="runner.last_heartbeat" class="heartbeat" :class="isRecent(runner.last_heartbeat) ? 'hb-ok' : 'hb-stale'">
                    <el-icon><Timer /></el-icon>{{ formatRelativeTime(runner.last_heartbeat) }}
                  </span>
                  <span v-else class="heartbeat hb-stale">
                    <el-icon><WarningFilled /></el-icon>{{ $t('runner.noHeartbeat') }}
                  </span>
                </div>
              </div>

              <div class="card-actions">
                <el-button
                  v-if="runner.id !== defaultRunnerId"
                  type="primary"
                  size="small"
                  @click="handleSetDefault(runner.id)"
                >
                  设为默认
                </el-button>
                <el-tag v-else type="warning" size="small">当前默认</el-tag>
              </div>
            </div>
          </div>
          <el-empty v-else description="你还没有绑定的 Runner" :image-size="120">
            <template #image>
              <el-icon :size="80" color="#c0c4cc"><Monitor /></el-icon>
            </template>
          </el-empty>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- ========== 所有对话框 ========== -->

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingRunner ? $t('common.edit') : $t('runner.add')" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item :label="$t('common.name')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('common.name')" :disabled="!!editingRunner" />
        </el-form-item>
        <el-form-item :label="$t('user.displayName')" prop="display_name">
          <el-input v-model="form.display_name" :placeholder="$t('user.displayName')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <el-input v-model="form.description" type="textarea" :rows="2" :placeholder="$t('common.description')" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="14">
            <el-form-item :label="$t('runner.host')">
              <el-input v-model="form.host" placeholder="IP address" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item :label="$t('runner.port')">
              <el-input
                v-model.number="form.port"
                type="number"
                :min="1"
                :max="65535"
                placeholder="1-65535"
                style="width: 100%"
                class="port-input"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item :label="$t('runner.platform')">
              <el-select v-model="form.platform" style="width: 100%" clearable>
                <el-option label="Windows" value="windows" />
                <el-option label="Linux" value="linux" />
                <el-option label="macOS" value="macos" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('runner.version')">
              <el-input v-model="form.version" placeholder="1.0.0" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝对话框 -->
    <el-dialog v-model="rejectDialogVisible" :title="$t('runner.reject')" width="400px">
      <el-form label-width="80px">
        <el-form-item :label="$t('runner.rejectReason')">
          <el-input v-model="rejectReason" type="textarea" :rows="3" :placeholder="$t('runner.rejectReason')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="danger" @click="confirmReject">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 关联用户对话框 -->
    <el-dialog v-model="associateVisible" :title="$t('runner.associateUser')" width="450px">
      <div class="associate-info" v-if="associatingRunner">
        <p>将 Runner <strong>{{ associatingRunner.display_name || associatingRunner.name }}</strong>
          ({{ associatingRunner.host }}) 关联到用户：</p>
      </div>
      <el-table
        :data="userList"
        highlight-current-row
        @row-click="selectUser"
        max-height="300"
        stripe
        :empty-text="$t('common.noData')"
      >
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="display_name" label="显示名称" />
        <el-table-column prop="role" label="角色" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.role === 'super_admin' ? 'danger' : row.role === 'org_admin' ? 'warning' : 'info'">
              {{ row.role === 'super_admin' ? '超级管理员' : row.role === 'org_admin' ? '组织管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="selectedUserId" class="selected-hint">
        已选择用户 ID: {{ selectedUserId }}
      </div>
      <template #footer>
        <el-button @click="associateVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!selectedUserId" @click="confirmAssociate">
          确认关联并上线
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" :title="$t('runner.viewDetail')" size="500px">
      <el-descriptions :column="1" border v-if="detailRunner">
        <el-descriptions-item :label="$t('common.name')">{{ detailRunner.name }}</el-descriptions-item>
        <el-descriptions-item :label="$t('user.displayName')">{{ detailRunner.display_name }}</el-descriptions-item>
        <el-descriptions-item :label="$t('common.status')">
          <el-tag :type="getStatusTagType(detailRunner.status)" size="small">
            {{ getStatusLabel(detailRunner.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('runner.platform')">{{ detailRunner.platform || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('runner.host')">{{ detailRunner.host }}:{{ detailRunner.port }}</el-descriptions-item>
        <el-descriptions-item :label="$t('runner.version')">{{ detailRunner.version || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('task.current')">{{ detailRunner.current_task || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('task.stats')">
          {{ $t('task.total') }} {{ detailRunner.total_tasks }} /
          {{ $t('common.success') }} {{ detailRunner.success_tasks }} /
          {{ $t('common.failed') }} {{ detailRunner.failed_tasks }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('runner.heartbeat')">
          {{ detailRunner.last_heartbeat ? formatTime(detailRunner.last_heartbeat) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('common.time')">{{ formatTime(detailRunner.applied_at) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('common.description')">{{ detailRunner.description || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="detailRunner?.capabilities" class="capabilities-section">
        <h4>{{ $t('skill.config') }}</h4>
        <pre class="code-block">{{ JSON.stringify(detailRunner.capabilities, null, 2) }}</pre>
      </div>
    </el-drawer>

    <!-- NEW: 绑定用户对话框 -->
    <el-dialog v-model="bindDialogVisible" title="绑定用户" width="450px">
      <div class="associate-info" v-if="bindingRunner">
        <p>将 Runner <strong>{{ bindingRunner.display_name || bindingRunner.name }}</strong>
          ({{ bindingRunner.host }}) 绑定到用户：</p>
      </div>
      <el-table
        :data="bindUserList"
        highlight-current-row
        @row-click="selectBindUser"
        max-height="300"
        stripe
      >
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="display_name" label="显示名称" />
        <el-table-column prop="role" label="角色" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.role === 'super_admin' ? 'danger' : row.role === 'org_admin' ? 'warning' : 'info'">
              {{ row.role === 'super_admin' ? '超级管理员' : row.role === 'org_admin' ? '组织管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="bindSelectedUserId" class="selected-hint">
        已选择用户 ID: {{ bindSelectedUserId }}
      </div>
      <template #footer>
        <el-button @click="bindDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!bindSelectedUserId" :loading="bindSubmitting" @click="handleBindConfirm">
          确认绑定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, CircleCheck, Clock, List, Select, Plus, Link, CopyDocument,
  MoreFilled, Loading, CloseBold, User, Timer, WarningFilled,
  Upload, UploadFilled
} from '@element-plus/icons-vue'
import { api } from '@/api'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const userStore = useUserStore()

// ── 接口 ──
interface Runner {
  id: number
  name: string
  display_name: string
  description?: string
  status: string
  host?: string
  port?: number
  platform?: string
  version?: string
  last_heartbeat?: string
  current_task?: string
  total_tasks: number
  success_tasks: number
  failed_tasks: number
  applied_at: string
  approved_at?: string
  reject_reason?: string
  capabilities?: Record<string, any>
  user_id?: number
  username?: string
}

interface DiagnosticsData {
  cpu_percent: number
  memory_percent: number
  disk_percent: number
  processes: Array<{ pid: number; name: string; cpu_percent: number; memory_percent: number }>
  updated_at?: string
}

interface ConnectionEvent {
  id?: number
  runner_id?: number
  event_type: string
  detail?: string
  timestamp: string
}

interface ReleaseItem {
  id: number
  version: string
  filename: string
  file_size: number
  checksum: string
  platform: string
  release_notes?: string
  is_latest: boolean
  uploaded_by?: number
  created_at: string
}

// ── 权限 ──
const isAdmin = computed(() => userStore.isSuperAdmin || userStore.isOrgAdmin)

// ── Tab 状态 ──
const activeTab = ref(isAdmin.value ? 'list' : 'my')

// ── 原有状态（Tab 1）──
const loading = ref(false)
const runners = ref<Runner[]>([])
const filterStatus = ref('')
const searchKeyword = ref('')
const dialogVisible = ref(false)
const rejectDialogVisible = ref(false)
const detailVisible = ref(false)
const editingRunner = ref<Runner | null>(null)
const rejectingRunner = ref<Runner | null>(null)
const detailRunner = ref<Runner | null>(null)
const rejectReason = ref('')
const submitting = ref(false)
const formRef = ref()
const associateVisible = ref(false)
const associatingRunner = ref<Runner | null>(null)
const userList = ref<any[]>([])
const selectedUserId = ref<number | null>(null)

const centerInfo = ref({
  http_address: 'http://localhost:20005',
  apply_endpoint: 'http://localhost:20005/api/runners/apply'
})

const stats = ref({
  total_runners: 0,
  online_count: 0,
  pending_count: 0,
  total_tasks: 0,
  success_rate: 0
})

const form = reactive({
  name: '',
  display_name: '',
  description: '',
  host: '',
  port: 20006,
  platform: '',
  version: ''
})

const rules = {
  name: [{ required: true, message: t('common.name'), trigger: 'blur' }],
  display_name: [{ required: true, message: t('user.displayName'), trigger: 'blur' }]
}

// ── 绑定用户状态 ──
const bindDialogVisible = ref(false)
const bindingRunner = ref<Runner | null>(null)
const bindUserList = ref<any[]>([])
const bindSelectedUserId = ref<number | null>(null)
const bindSubmitting = ref(false)

// ── 诊断状态 ──
const selectedDiagnosticsRunnerId = ref<number | null>(null)
const diagLoading = ref(false)
const diagnosticsData = ref<DiagnosticsData>({
  cpu_percent: 0,
  memory_percent: 0,
  disk_percent: 0,
  processes: []
})
const connectionEvents = ref<ConnectionEvent[]>([])

// ── 版本管理状态 ──
const releasesLoading = ref(false)
const releases = ref<ReleaseItem[]>([])
const releasePlatformFilter = ref('')
const releaseUploading = ref(false)
const releaseFile = ref<File | null>(null)
const releaseFileList = ref<any[]>([])
const uploadRef = ref()
const releaseForm = reactive({
  version: '',
  platform: '',
  release_notes: ''
})

// ── 我的 Runner 状态 ──
const myBindingsLoading = ref(false)
const myBindings = ref<Runner[]>([])
const defaultRunnerId = ref<number | null>(null)

// ── 计算属性（Tab 1）──
const statusTabs = computed(() => [
  { label: t('common.all'), value: '', count: stats.value.total_runners },
  { label: t('common.online'), value: 'online', count: stats.value.online_count },
  { label: t('common.pending'), value: 'pending', count: stats.value.pending_count },
  { label: t('common.offline'), value: 'offline', count: 0 }
])

const filteredRunners = computed(() => {
  if (!searchKeyword.value) return runners.value
  const keyword = searchKeyword.value.toLowerCase()
  return runners.value.filter(r =>
    r.name.toLowerCase().includes(keyword) ||
    (r.display_name?.toLowerCase().includes(keyword))
  )
})

const statusLabels: Record<string, string> = {
  pending: 'pending',
  approved: 'approved',
  rejected: 'rejected',
  online: 'online',
  offline: 'offline'
}

// ── 工具函数 ──
function getStatusLabel(status: string): string {
  const key = statusLabels[status] || status
  if (key === 'pending') return t('common.pending')
  if (key === 'approved') return t('common.approved')
  if (key === 'rejected') return t('common.rejected')
  if (key === 'online') return t('common.online')
  if (key === 'offline') return t('common.offline')
  return status
}

function getStatusTagType(status: string): string {
  const types: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    online: 'success',
    offline: 'info'
  }
  return types[status] || ''
}

function formatTime(time?: string): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function formatRelativeTime(time: string): string {
  const diff = Date.now() - new Date(time).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return t('dashboard.justNow')
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return t('dashboard.minutesAgo', { n: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('dashboard.hoursAgo', { n: hours })
  return t('runner.daysAgo', { n: Math.floor(hours / 24) })
}

function isRecent(time: string): boolean {
  return Date.now() - new Date(time).getTime() < 60000
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
  ElMessage.success(t('common.copied'))
}

function progressColor(percent: number): string {
  if (percent >= 90) return '#f56c6c'
  if (percent >= 70) return '#e6a23c'
  return '#67c23a'
}

// ── Tab 切换 ──
function onTabChange(tabName: string) {
  if (tabName === 'diagnostics' && (userStore.isSuperAdmin || userStore.isOrgAdmin)) {
    // 诊断面板需要完整的 runner 列表，清除过滤后重新加载
    filterStatus.value = ''
    fetchRunners()
  }
  if (tabName === 'versions' && userStore.isSuperAdmin) {
    fetchReleases()
  }
  if (tabName === 'my') {
    fetchMyBindings()
  }
}

function switchToDiagnostics(runner: Runner) {
  selectedDiagnosticsRunnerId.value = runner.id
  activeTab.value = 'diagnostics'
  fetchRunnerDiagnostics(runner.id)
}

// ── Tab 1: 原有 API ──
async function fetchCenterInfo() {
  try {
    const res = await api.get('/runners/center-info')
    centerInfo.value = res.data
  } catch (error) {
    console.error('Failed to fetch center info')
  }
}

async function fetchStats() {
  try {
    const res = await api.get('/runners/stats')
    stats.value = res.data
  } catch (error) {
    console.error('Failed to fetch stats')
  }
}

async function fetchRunners() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filterStatus.value) params.append('status_filter', filterStatus.value)

    const res = await api.get(`/runners?${params.toString()}`)
    runners.value = res.data
  } finally {
    loading.value = false
  }
}

function showDialog(runner?: Runner) {
  editingRunner.value = runner || null
  if (runner) {
    Object.assign(form, {
      name: runner.name,
      display_name: runner.display_name,
      description: runner.description || '',
      host: runner.host || '',
      port: runner.port || 20006,
      platform: runner.platform || '',
      version: runner.version || ''
    })
  } else {
    Object.assign(form, {
      name: '',
      display_name: '',
      description: '',
      host: '',
      port: 20006,
      platform: '',
      version: ''
    })
  }
  dialogVisible.value = true
}

function showRejectDialog(runner: Runner) {
  rejectingRunner.value = runner
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

async function confirmReject() {
  if (!rejectingRunner.value) return
  await approveRunner(rejectingRunner.value.id, false, rejectReason.value)
  rejectDialogVisible.value = false
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (editingRunner.value) {
      await api.put(`/runners/${editingRunner.value.id}`, form)
      ElMessage.success(t('common.success'))
    } else {
      await api.post('/runners', form)
      ElMessage.success(t('common.success'))
    }
    dialogVisible.value = false
    fetchRunners()
    fetchStats()
  } finally {
    submitting.value = false
  }
}

async function approveRunner(id: number, approve: boolean, reason?: string) {
  await api.post(`/runners/${id}/approve`, { approve, reject_reason: reason })
  ElMessage.success(approve ? t('runner.approve') : t('runner.reject'))
  fetchRunners()
  fetchStats()
}

async function fetchUsers() {
  try {
    const res = await api.get('/users')
    userList.value = (res.data.items || res.data || []).filter((u: any) => u.role === 'user')
  } catch (e) {
    userList.value = []
  }
}

async function fetchAllUsers() {
  try {
    const res = await api.get('/users')
    bindUserList.value = (res.data.items || res.data || []).filter((u: any) => u.role === 'user')
  } catch (e) {
    bindUserList.value = []
  }
}

function showAssociateDialog(runner: Runner) {
  associatingRunner.value = runner
  selectedUserId.value = null
  fetchUsers()
  associateVisible.value = true
}

function selectUser(row: any) {
  selectedUserId.value = row.id
}

async function confirmAssociate() {
  if (!associatingRunner.value || !selectedUserId.value) return
  try {
    await api.post(`/runners/${associatingRunner.value.id}/approve`, {
      approve: true,
      user_id: selectedUserId.value
    })
    ElMessage.success('关联成功，Runner 已上线')
    associateVisible.value = false
    fetchRunners()
    fetchStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '关联失败')
  }
}

async function setOffline(id: number) {
  await api.post(`/runners/${id}/offline`)
  ElMessage.success(t('common.success'))
  fetchRunners()
  fetchStats()
}

async function showDetail(runner: Runner) {
  const res = await api.get(`/runners/${runner.id}`)
  detailRunner.value = res.data
  detailVisible.value = true
}

async function deleteRunner(runner: Runner) {
  try {
    await ElMessageBox.confirm(
      `${t('common.confirm')} ${runner.display_name || runner.name}?`,
      t('common.delete'),
      { type: 'warning' }
    )
    await api.delete(`/runners/${runner.id}`)
    ElMessage.success(t('common.success'))
    fetchRunners()
    fetchStats()
  } catch (error) {
    // 用户取消
  }
}

// ── 用户绑定 API ──
function showBindDialog(runner: Runner) {
  bindingRunner.value = runner
  bindSelectedUserId.value = null
  fetchAllUsers()
  bindDialogVisible.value = true
}

function selectBindUser(row: any) {
  bindSelectedUserId.value = row.id
}

async function handleBindConfirm() {
  if (!bindingRunner.value || !bindSelectedUserId.value) return
  bindSubmitting.value = true
  try {
    await api.post(`/runners/${bindingRunner.value.id}/bind-user`, {
      user_id: bindSelectedUserId.value
    })
    ElMessage.success('绑定成功')
    bindDialogVisible.value = false
    fetchRunners()
    fetchStats()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '绑定失败')
  } finally {
    bindSubmitting.value = false
  }
}

async function handleUnbind(runner: Runner) {
  try {
    await ElMessageBox.confirm(
      `确认解绑 Runner "${runner.display_name || runner.name}" 的用户？`,
      '解绑用户',
      { type: 'warning' }
    )
    await api.delete(`/runners/${runner.id}/unbind-user`)
    ElMessage.success('解绑成功')
    fetchRunners()
    fetchStats()
  } catch (error) {
    // 用户取消
  }
}

// ── Token 轮换 ──
async function handleRotateToken(runner: Runner) {
  try {
    await ElMessageBox.confirm(
      `确认轮换 Runner "${runner.display_name || runner.name}" 的 API Token？轮换后旧 Token 将立即失效。`,
      '轮换 Token',
      { type: 'warning', confirmButtonText: '确认轮换' }
    )
  } catch {
    return
  }

  try {
    const res = await api.post(`/runners/${runner.id}/rotate-token`)
    const newToken: string = res.data.new_token
    await ElMessageBox.alert(
      `新的 API Token（仅显示一次，请立即保存）:\n\n${newToken}`,
      'Token 轮换成功',
      {
        type: 'success',
        confirmButtonText: '复制并关闭',
      }
    )
    navigator.clipboard.writeText(newToken)
    ElMessage.success('Token 已复制到剪贴板')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || 'Token 轮换失败')
  }
}

// ── 诊断 API ──
async function fetchRunnerDiagnostics(runnerId: number) {
  diagLoading.value = true
  try {
    const [diagRes, eventsRes] = await Promise.all([
      api.get(`/runners/${runnerId}/diagnostics`),
      api.get(`/runners/${runnerId}/connection-events?limit=50`),
    ])
    diagnosticsData.value = diagRes.data
    connectionEvents.value = eventsRes.data || []
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '获取诊断信息失败')
  } finally {
    diagLoading.value = false
  }
}

function onDiagnosticsRunnerChange(runnerId: number) {
  if (runnerId) {
    fetchRunnerDiagnostics(runnerId)
  }
}

// ── 版本管理 API ──
async function fetchReleases() {
  releasesLoading.value = true
  try {
    const params = new URLSearchParams()
    if (releasePlatformFilter.value) params.append('platform', releasePlatformFilter.value)
    const res = await api.get(`/runner-releases/versions?${params.toString()}`)
    releases.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '获取版本列表失败')
  } finally {
    releasesLoading.value = false
  }
}

function handleReleaseFileChange(file: any) {
  releaseFile.value = file.raw
}

async function handleUploadRelease() {
  if (!releaseForm.version || !releaseForm.platform || !releaseFile.value) {
    ElMessage.warning('请填写版本号、选择平台并上传安装包')
    return
  }
  releaseUploading.value = true
  try {
    const formData = new FormData()
    formData.append('version', releaseForm.version)
    formData.append('platform', releaseForm.platform)
    if (releaseForm.release_notes) formData.append('release_notes', releaseForm.release_notes)
    formData.append('file', releaseFile.value)

    await api.post('/runner-releases/upload', formData)
    ElMessage.success('版本上传成功')
    releaseForm.version = ''
    releaseForm.platform = ''
    releaseForm.release_notes = ''
    releaseFile.value = null
    releaseFileList.value = []
    uploadRef.value?.clearFiles()
    fetchReleases()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  } finally {
    releaseUploading.value = false
  }
}

async function handleSetLatest(row: ReleaseItem) {
  try {
    await ElMessageBox.confirm(
      `确认将 ${row.platform} 平台 v${row.version} 设为最新版本？`,
      '设为最新',
      { type: 'info' }
    )
    const formData = new FormData()
    formData.append('platform', row.platform)
    await api.post(`/runner-releases/versions/${row.version}/set-latest`, formData)
    ElMessage.success('已设为最新版本')
    fetchReleases()
  } catch (error) {
    // 用户取消
  }
}

async function handleDeleteVersion(row: ReleaseItem) {
  try {
    await ElMessageBox.confirm(
      `确认删除 ${row.platform} 平台 v${row.version}？此操作不可恢复。`,
      '删除版本',
      { type: 'warning' }
    )
    await api.delete(`/runner-releases/versions/${row.version}`, {
      data: new URLSearchParams({ platform: row.platform })
    })
    ElMessage.success('版本已删除')
    fetchReleases()
  } catch (error) {
    // 用户取消
  }
}

// ── 我的 Runner API ──
async function fetchMyBindings() {
  myBindingsLoading.value = true
  try {
    const res = await api.get('/runners/my-bindings')
    myBindings.value = res.data || []
    defaultRunnerId.value = null
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '获取绑定列表失败')
  } finally {
    myBindingsLoading.value = false
  }
}

async function handleSetDefault(runnerId: number) {
  try {
    await api.put('/runners/my-default', { runner_id: runnerId })
    ElMessage.success('默认 Runner 设置成功')
    defaultRunnerId.value = runnerId
    fetchMyBindings()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '设置默认 Runner 失败')
  }
}

// ── 生命周期 ──
onMounted(() => {
  fetchCenterInfo()
  fetchStats()
  fetchRunners()
  // 如果初始 Tab 是非管理员的"我的 Runner"，加载绑定数据
  if (activeTab.value === 'my') fetchMyBindings()
  if (activeTab.value === 'versions') fetchReleases()
})
</script>

<style scoped lang="scss">
/* ===== Page Layout ===== */
.runners-page {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 16px;

  .toolbar-spacer {
    flex: 1;
  }
}

/* ===== Tabs ===== */
.runner-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }
}

.runners-page {
  .stats-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 20px;

    .stat-card {
      background: var(--pc-glass-bg);
      border: 1px solid var(--pc-glass-border);
      border-radius: var(--pc-radius-lg);
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      backdrop-filter: var(--pc-glass-blur);
      transition: all 0.3s ease;

      &:hover {
        border-color: rgba(var(--pc-primary-rgb), 0.3);
        box-shadow: 0 0 20px rgba(var(--pc-primary-rgb), 0.1);
      }

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;

        &.total {
          background: rgba(var(--pc-primary-rgb), 0.12);
          color: var(--pc-primary);
          box-shadow: 0 0 12px rgba(var(--pc-primary-rgb), 0.2);
        }
        &.online {
          background: rgba(var(--pc-accent-green), 0.12);
          color: var(--pc-accent-green);
          box-shadow: 0 0 12px rgba(var(--pc-accent-green), 0.2);
        }
        &.pending {
          background: rgba(var(--pc-accent-orange), 0.12);
          color: var(--pc-accent-orange);
          box-shadow: 0 0 12px rgba(var(--pc-accent-orange), 0.2);
        }
        &.tasks {
          background: rgba(var(--pc-accent-purple), 0.12);
          color: var(--pc-accent-purple);
          box-shadow: 0 0 12px rgba(var(--pc-accent-purple), 0.2);
        }
        &.success {
          background: rgba(var(--pc-accent-cyan), 0.12);
          color: var(--pc-accent-cyan);
          box-shadow: 0 0 12px rgba(var(--pc-accent-cyan), 0.2);
        }
      }

      .stat-content {
        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: var(--pc-text-primary);
          letter-spacing: -0.5px;
        }
        .stat-label {
          font-size: 13px;
          color: var(--pc-text-muted);
          margin-top: 2px;
        }
      }

      &.add-card {
        cursor: pointer;
        flex-direction: column;
        justify-content: center;
        border: 2px dashed var(--pc-border);
        background: transparent;
        color: var(--pc-text-muted);
        transition: all 0.3s ease;

        &:hover {
          border-color: var(--pc-primary);
          color: var(--pc-primary);
          background: rgba(var(--pc-primary-rgb), 0.04);
          box-shadow: 0 0 20px rgba(var(--pc-primary-rgb), 0.15);
        }
      }
    }
  }

  .connection-card {
    margin-bottom: 20px;
    background: var(--pc-glass-bg) !important;
    border: 1px solid var(--pc-glass-border) !important;
    border-radius: var(--pc-radius-lg) !important;
    backdrop-filter: var(--pc-glass-blur);

    .connection-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .connection-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: var(--pc-text-primary);
      }
    }

    .connection-content {
      .connection-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        background: var(--pc-bg-elevated);
        border-radius: var(--pc-radius-sm);
        margin-bottom: 8px;
        border: 1px solid var(--pc-border);

        .label { color: var(--pc-text-muted); }
        code {
          background: none;
          color: var(--pc-primary);
          font-family: 'Monaco', 'Menlo', monospace;
        }
      }
    }
  }

  .list-card {
    background: var(--pc-glass-bg) !important;
    border: 1px solid var(--pc-glass-border) !important;
    border-radius: var(--pc-radius-lg) !important;
    backdrop-filter: var(--pc-glass-blur);

    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .filter-tabs {
        display: flex;
        gap: 24px;

        .tab {
          cursor: pointer;
          padding: 8px 0;
          color: var(--pc-text-secondary);
          border-bottom: 2px solid transparent;
          transition: all 0.3s;
          font-weight: 500;
          position: relative;

          &:hover { color: var(--pc-primary); }
          &.active {
            color: var(--pc-primary);
            border-bottom-color: var(--pc-primary);
          }

          :deep(.tab-badge) {
            position: absolute;
            top: 0;
            right: -20px;
          }
        }
      }
    }

    .runner-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;
      margin-top: 16px;
      min-height: 300px;

      &:empty, &:has(.el-empty) {
        display: flex;
        justify-content: center;
        align-items: center;
      }

      :deep(.el-empty) {
        grid-column: 1 / -1;
        width: 100%;
      }

      .runner-card {
        background: var(--pc-glass-bg);
        border: 1px solid var(--pc-glass-border);
        border-radius: var(--pc-radius-lg);
        padding: 16px 18px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;

        &::before {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 3px;
          background: var(--pc-border);
          transition: all 0.3s ease;
        }
        &.online::before {
          background: var(--pc-accent-green);
          box-shadow: 0 0 10px rgba(var(--pc-accent-green-rgb), 0.5);
        }
        &.pending::before {
          background: var(--pc-accent-orange);
          box-shadow: 0 0 10px rgba(var(--pc-accent-orange-rgb), 0.5);
        }
        &.offline::before {
          background: var(--pc-text-muted);
        }

        &:hover {
          border-color: var(--pc-border-hover);
          box-shadow: var(--pc-shadow-glow);
          transform: translateY(-2px);
        }

        // ── 头部 ──
        .card-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;

          .head-left {
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
          }

          .status-dot {
            width: 8px; height: 8px;
            border-radius: 50%; flex-shrink: 0;
            &.online { background: var(--pc-accent-green); box-shadow: 0 0 8px rgba(var(--pc-accent-green-rgb), 0.6); animation: pulse 2s infinite; }
            &.pending { background: var(--pc-accent-orange); box-shadow: 0 0 8px rgba(var(--pc-accent-orange-rgb), 0.6); animation: pulse 2s infinite; }
            &.offline { background: var(--pc-text-muted); }
          }

          .card-name {
            font-size: 15px;
            font-weight: 600;
            color: var(--pc-text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .tag-version {
            font-size: 10px;
            color: var(--pc-text-muted);
            background: rgba(255,255,255,0.06);
            padding: 1px 6px;
            border-radius: 8px;
            flex-shrink: 0;
          }

          .btn-menu {
            padding: 2px;
            color: var(--pc-text-muted);
            flex-shrink: 0;
          }
        }

        // ── 信息行 ──
        .card-info {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
          font-size: 12px;
          color: var(--pc-text-muted);

          .info-label {
            background: rgba(255,255,255,0.04);
            padding: 1px 8px;
            border-radius: 4px;
          }
          code {
            color: var(--pc-primary);
            background: rgba(var(--pc-primary-rgb), 0.08);
            padding: 1px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
          }
          .info-user {
            display: flex;
            align-items: center;
            gap: 4px;
            color: var(--pc-accent-green);
            font-size: 11px;
          }
        }

        // ── 任务统计 ──
        .card-stats {
          display: flex;
          justify-content: space-around;
          padding: 10px 0;
          background: rgba(255,255,255,0.015);
          border-radius: var(--pc-radius-md);
          border: 1px solid var(--pc-glass-border);
          margin-bottom: 10px;

          .stat-col {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2px;

            .stat-num {
              font-size: 20px;
              font-weight: 700;
              color: var(--pc-text-primary);
              line-height: 1.1;
              &.ok { color: var(--pc-accent-green); }
              &.fail { color: var(--pc-accent-red); }
            }
            .stat-lbl {
              font-size: 11px;
              color: var(--pc-text-muted);
              text-transform: uppercase;
              letter-spacing: 0.3px;
            }
          }
        }

        // ── 底部信息 ──
        .card-foot {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .foot-left {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
          }

          .heartbeat {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            &.hb-ok { color: var(--pc-accent-green); }
            &.hb-stale { color: var(--pc-accent-orange); }
          }

          .task-info {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            color: var(--pc-primary);
            max-width: 160px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            .task-icon { animation: spin 1s linear infinite; flex-shrink: 0; }
          }
        }

        // ── 操作按钮 ──
        .card-actions {
          display: flex;
          gap: 8px;
          margin-top: 10px;
          padding-top: 10px;
          border-top: 1px solid var(--pc-glass-border);

          :deep(.el-button--small) {
            height: 28px;
            padding: 0 14px;
            font-size: 12px;
          }
        }
      }
    }
  }

  .capabilities-section {
    margin-top: 24px;

    h4 {
      margin-bottom: 12px;
      color: var(--pc-text-primary);
    }

    .code-block {
      background: var(--pc-bg-elevated);
      padding: 12px;
      border-radius: var(--pc-radius-sm);
      font-size: 12px;
      overflow-x: auto;
      border: 1px solid var(--pc-border);
      color: var(--pc-text-primary);
    }
  }
}

/* ===== 诊断面板 ===== */
.diagnostics-panel {
  .diag-toolbar {
    margin-bottom: 20px;
  }

  .diag-placeholder {
    padding: 40px 0;
  }

  .diag-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .diag-card {
    background: var(--pc-glass-bg) !important;
    border: 1px solid var(--pc-glass-border) !important;
    border-radius: var(--pc-radius-lg) !important;

    .diag-card-title {
      font-weight: 600;
      color: var(--pc-text-primary);
    }
  }

  .resource-bars {
    display: flex;
    flex-direction: column;
    gap: 20px;

    .resource-item {
      .resource-label {
        font-size: 13px;
        color: var(--pc-text-secondary);
        margin-bottom: 6px;
        font-weight: 500;
      }
    }
  }

  .connection-timeline {
    max-height: 400px;
    overflow-y: auto;

    .event-type {
      font-weight: 600;
      text-transform: capitalize;
    }

    .event-detail {
      color: var(--pc-text-muted);
      font-size: 13px;
    }
  }
}

/* ===== 版本管理面板 ===== */
.versions-panel {
  .version-card {
    background: var(--pc-glass-bg) !important;
    border: 1px solid var(--pc-glass-border) !important;
    border-radius: var(--pc-radius-lg) !important;
    height: 100%;

    .version-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .diag-card-title {
    font-weight: 600;
    color: var(--pc-text-primary);
  }
}

/* ===== 我的 Runner 面板 ===== */
.my-runners-panel {
  .runner-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
    min-height: 200px;

    .runner-card {
      background: var(--pc-glass-bg);
      border: 1px solid var(--pc-glass-border);
      border-radius: var(--pc-radius-lg);
      padding: 16px 18px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;

      &::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--pc-border);
        transition: all 0.3s ease;
      }
      &.online::before {
        background: var(--pc-accent-green);
        box-shadow: 0 0 10px rgba(var(--pc-accent-green-rgb), 0.5);
      }
      &.pending::before {
        background: var(--pc-accent-orange);
        box-shadow: 0 0 10px rgba(var(--pc-accent-orange-rgb), 0.5);
      }
      &.offline::before {
        background: var(--pc-text-muted);
      }

      &:hover {
        border-color: var(--pc-border-hover);
        box-shadow: var(--pc-shadow-glow);
        transform: translateY(-2px);
      }

      .card-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;

        .head-left {
          display: flex;
          align-items: center;
          gap: 8px;
          min-width: 0;
        }

        .status-dot {
          width: 8px; height: 8px;
          border-radius: 50%; flex-shrink: 0;
          &.online { background: var(--pc-accent-green); box-shadow: 0 0 8px rgba(var(--pc-accent-green-rgb), 0.6); animation: pulse 2s infinite; }
          &.pending { background: var(--pc-accent-orange); box-shadow: 0 0 8px rgba(var(--pc-accent-orange-rgb), 0.6); animation: pulse 2s infinite; }
          &.offline { background: var(--pc-text-muted); }
        }

        .card-name {
          font-size: 15px;
          font-weight: 600;
          color: var(--pc-text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }

      .card-info {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
        font-size: 12px;
        color: var(--pc-text-muted);

        .info-label {
          background: rgba(255,255,255,0.04);
          padding: 1px 8px;
          border-radius: 4px;
        }
        code {
          color: var(--pc-primary);
          background: rgba(var(--pc-primary-rgb), 0.08);
          padding: 1px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-family: 'JetBrains Mono', 'Consolas', monospace;
        }
      }

      .card-foot {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .foot-left {
          display: flex;
          align-items: center;
          gap: 12px;
          min-width: 0;
        }

        .heartbeat {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 11px;
          &.hb-ok { color: var(--pc-accent-green); }
          &.hb-stale { color: var(--pc-accent-orange); }
        }
      }

      .card-actions {
        display: flex;
        gap: 8px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--pc-glass-border);
        align-items: center;
      }
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Port 输入框样式修复 */
.port-input {
  :deep(.el-input__wrapper) {
    padding-left: 8px;
    padding-right: 8px;
  }
  :deep(.el-input__inner) {
    text-align: center;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 14px;
    font-weight: 500;
    -moz-appearance: textfield;
    &::-webkit-outer-spin-button,
    &::-webkit-inner-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }
  }
}
</style>
