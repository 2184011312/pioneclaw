<template>
  <div class="settings-page">
    <div class="page-header">
      <!-- 标题已在左侧边栏显示 -->
    </div>

    <div class="settings-container">
      <!-- Left Menu -->
      <div class="settings-sidebar">
        <el-menu :default-active="activeMenu" @select="activeMenu = $event">
          <el-menu-item index="general">
            <div class="menu-item-content">
              <el-icon class="menu-icon general"><Setting /></el-icon>
              <div class="menu-text">
                <span class="menu-title">{{ $t('settings.general') }}</span>
                <span class="menu-desc">{{ $t('settings.generalDesc') }}</span>
              </div>
            </div>
          </el-menu-item>
          <el-menu-item index="execution">
            <div class="menu-item-content">
              <el-icon class="menu-icon execution"><Cpu /></el-icon>
              <div class="menu-text">
                <span class="menu-title">{{ $t('settings.execution') }}</span>
                <span class="menu-desc">{{ $t('settings.executionDesc') }}</span>
              </div>
            </div>
          </el-menu-item>
          <el-menu-item index="security">
            <div class="menu-item-content">
              <el-icon class="menu-icon security"><Lock /></el-icon>
              <div class="menu-text">
                <span class="menu-title">{{ $t('settings.security') }}</span>
                <span class="menu-desc">{{ $t('settings.securityDesc') }}</span>
              </div>
            </div>
          </el-menu-item>
          <el-menu-item index="notification">
            <div class="menu-item-content">
              <el-icon class="menu-icon notification"><Bell /></el-icon>
              <div class="menu-text">
                <span class="menu-title">{{ $t('settings.notification') }}</span>
                <span class="menu-desc">{{ $t('settings.notificationDesc') }}</span>
              </div>
            </div>
          </el-menu-item>
          <el-menu-item index="about">
            <div class="menu-item-content">
              <el-icon class="menu-icon about"><InfoFilled /></el-icon>
              <div class="menu-text">
                <span class="menu-title">{{ $t('settings.about') }}</span>
                <span class="menu-desc">{{ $t('settings.aboutDesc') }}</span>
              </div>
            </div>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- Right Content -->
      <div class="settings-content" v-loading="loading">
        <!-- General Settings -->
        <el-card v-if="activeMenu === 'general'">
          <template #header>
            <span>{{ $t('settings.generalSettings') }}</span>
          </template>

          <el-form label-width="160px">
            <el-form-item :label="$t('settings.systemName')">
              <el-input v-model="generalSettings.systemName" style="width: 400px" />
            </el-form-item>
            <el-form-item :label="$t('settings.systemDesc')">
              <el-input v-model="generalSettings.systemDesc" type="textarea" :rows="3" style="width: 400px" />
            </el-form-item>
            <el-form-item :label="$t('settings.language')">
              <el-select v-model="generalSettings.language" style="width: 200px">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('settings.timezone')">
              <el-select v-model="generalSettings.timezone" style="width: 200px">
                <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
                <el-option label="UTC" value="UTC" />
                <el-option label="America/New_York (UTC-5)" value="America/New_York" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('settings.debugMode')">
              <el-switch v-model="generalSettings.debugMode" />
              <span class="form-tip">{{ $t('settings.debugModeTip') }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings('general')">{{ $t('settings.save') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Execution Settings -->
        <el-card v-if="activeMenu === 'execution'">
          <template #header>
            <span>{{ $t('settings.executionSettings') }}</span>
          </template>

          <el-form label-width="180px">
            <el-divider content-position="left">{{ $t('settings.taskExecution') }}</el-divider>
            <el-form-item :label="$t('settings.maxToolTurns')">
              <el-input-number v-model="executionSettings.maxToolTurns" :min="1" :max="100" />
              <span class="form-tip">{{ $t('settings.maxToolTurnsTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('settings.skillTimeout')">
              <el-input-number v-model="executionSettings.skillTimeout" :min="10" :max="600" />
              <span class="form-tip">{{ $t('settings.skillTimeoutTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('settings.taskTimeout')">
              <el-input-number v-model="executionSettings.taskTimeout" :min="10" :max="600" />
              <span class="form-tip">{{ $t('settings.taskTimeoutTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('settings.maxConcurrentTasks')">
              <el-input-number v-model="executionSettings.maxConcurrency" :min="1" :max="100" />
            </el-form-item>

            <el-divider content-position="left">{{ $t('settings.planning') }}</el-divider>
            <el-form-item :label="$t('settings.enablePlanning')">
              <el-switch v-model="executionSettings.enablePlanning" />
              <span class="form-tip">{{ $t('settings.enablePlanningTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('settings.enableReflection')">
              <el-switch v-model="executionSettings.enableReflection" />
              <span class="form-tip">{{ $t('settings.enableReflectionTip') }}</span>
            </el-form-item>

            <el-divider content-position="left">{{ $t('settings.retryStrategy') }}</el-divider>
            <el-form-item :label="$t('settings.autoRetry')">
              <el-switch v-model="executionSettings.autoRetry" />
            </el-form-item>
            <el-form-item :label="$t('settings.maxRetries')" v-if="executionSettings.autoRetry">
              <el-input-number v-model="executionSettings.maxRetries" :min="1" :max="10" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings('execution')">{{ $t('settings.save') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Security Settings -->
        <el-card v-if="activeMenu === 'security'">
          <template #header>
            <span>{{ $t('settings.securitySettings') }}</span>
          </template>

          <el-alert type="warning" :closable="false" style="margin-bottom: 20px">
            {{ $t('settings.jwtSecretWarning') }}
          </el-alert>

          <el-form label-width="180px">
            <el-divider content-position="left">{{ $t('settings.authentication') }}</el-divider>
            <el-form-item :label="$t('settings.jwtSecret')">
              <el-input v-model="securitySettings.jwtSecret" type="password" show-password style="width: 400px" />
            </el-form-item>
            <el-form-item :label="$t('settings.tokenExpiry')">
              <el-input-number v-model="securitySettings.tokenExpiry" :min="60" :max="10080" />
              <span class="form-tip">{{ $t('settings.tokenExpiryTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('settings.multiLogin')">
              <el-switch v-model="securitySettings.multiLogin" />
              <span class="form-tip">{{ $t('settings.multiLoginTip') }}</span>
            </el-form-item>

            <el-divider content-position="left">{{ $t('settings.operationApproval') }}</el-divider>
            <el-form-item :label="$t('settings.fileApproval')">
              <el-switch v-model="securitySettings.fileApproval" />
              <span class="form-tip">{{ $t('settings.fileApprovalTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('settings.networkApproval')">
              <el-switch v-model="securitySettings.networkApproval" />
              <span class="form-tip">{{ $t('settings.networkApprovalTip') }}</span>
            </el-form-item>
            <el-form-item :label="$t('settings.codeApproval')">
              <el-switch v-model="securitySettings.codeApproval" />
              <span class="form-tip">{{ $t('settings.codeApprovalTip') }}</span>
            </el-form-item>

            <el-divider content-position="left">{{ $t('settings.logging') }}</el-divider>
            <el-form-item :label="$t('settings.logLevel')">
              <el-select v-model="securitySettings.logLevel" style="width: 200px">
                <el-option label="DEBUG" value="debug" />
                <el-option label="INFO" value="info" />
                <el-option label="WARNING" value="warning" />
                <el-option label="ERROR" value="error" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('settings.logRetention')">
              <el-input-number v-model="securitySettings.logRetention" :min="1" :max="365" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings('security')">{{ $t('settings.save') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Notification Settings -->
        <el-card v-if="activeMenu === 'notification'">
          <template #header>
            <span>{{ $t('settings.notificationSettings') }}</span>
          </template>

          <el-form label-width="180px">
            <el-divider content-position="left">{{ $t('settings.emailNotifications') }}</el-divider>
            <el-form-item :label="$t('settings.enableEmail')">
              <el-switch v-model="notificationSettings.emailEnabled" />
            </el-form-item>
            <template v-if="notificationSettings.emailEnabled">
              <el-form-item :label="$t('settings.smtpServer')">
                <el-input v-model="notificationSettings.smtpHost" style="width: 300px" placeholder="smtp.example.com" />
              </el-form-item>
              <el-form-item :label="$t('settings.smtpPort')">
                <el-input-number v-model="notificationSettings.smtpPort" :min="1" :max="65535" />
              </el-form-item>
              <el-form-item :label="$t('settings.senderEmail')">
                <el-input v-model="notificationSettings.smtpUser" style="width: 300px" />
              </el-form-item>
              <el-form-item :label="$t('settings.emailPassword')">
                <el-input v-model="notificationSettings.smtpPass" type="password" show-password style="width: 300px" />
              </el-form-item>
            </template>

            <el-divider content-position="left">{{ $t('settings.webhookNotifications') }}</el-divider>
            <el-form-item :label="$t('settings.enableWebhook')">
              <el-switch v-model="notificationSettings.webhookEnabled" />
            </el-form-item>
            <el-form-item :label="$t('settings.webhookUrl')" v-if="notificationSettings.webhookEnabled">
              <el-input v-model="notificationSettings.webhookUrl" style="width: 400px" placeholder="https://example.com/webhook" />
            </el-form-item>

            <el-divider content-position="left">{{ $t('settings.notificationEvents') }}</el-divider>
            <el-form-item :label="$t('settings.taskComplete')">
              <el-switch v-model="notificationSettings.notifyTaskComplete" />
            </el-form-item>
            <el-form-item :label="$t('settings.taskFailed')">
              <el-switch v-model="notificationSettings.notifyTaskFailed" />
            </el-form-item>
            <el-form-item :label="$t('settings.systemAlerts')">
              <el-switch v-model="notificationSettings.notifySystemAlert" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings('notification')">{{ $t('settings.save') }}</el-button>
              <el-button @click="testNotification">{{ $t('settings.sendTestNotification') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- About -->
        <el-card v-if="activeMenu === 'about'">
          <template #header>
            <span>{{ $t('settings.aboutSystem') }}</span>
          </template>

          <div class="about-content">
            <div class="system-logo">
              <img src="/pioneclaw-logo.svg" alt="PioneClaw" width="80" />
              <h2>PioneClaw</h2>
              <p class="version">{{ $t('settings.version') }} 1.0.0</p>
            </div>

            <el-descriptions :column="2" border>
              <el-descriptions-item :label="$t('settings.systemName')">PioneClaw</el-descriptions-item>
              <el-descriptions-item :label="$t('settings.version')">1.0.0</el-descriptions-item>
              <el-descriptions-item :label="$t('settings.frontendFramework')">Vue 3 + Element Plus</el-descriptions-item>
              <el-descriptions-item :label="$t('settings.backendFramework')">FastAPI + SQLAlchemy</el-descriptions-item>
              <el-descriptions-item :label="$t('settings.database')">SQLite</el-descriptions-item>
              <el-descriptions-item :label="$t('settings.pythonVersion')">3.14</el-descriptions-item>
              <el-descriptions-item :label="$t('settings.nodeVersion')">25.8.1</el-descriptions-item>
              <el-descriptions-item :label="$t('settings.developer')">PioneClaw Team</el-descriptions-item>
            </el-descriptions>

            <el-divider />

            <div class="tech-stack">
              <h4>{{ $t('settings.techStack') }}</h4>
              <div class="tech-tags">
                <el-tag>Vue 3</el-tag>
                <el-tag>TypeScript</el-tag>
                <el-tag>Vite</el-tag>
                <el-tag>Element Plus</el-tag>
                <el-tag>FastAPI</el-tag>
                <el-tag>SQLAlchemy</el-tag>
                <el-tag>SQLite</el-tag>
                <el-tag>Pydantic</el-tag>
              </div>
            </div>

            <el-divider />

            <div class="links">
              <el-button type="primary" link>
                <el-icon><Link /></el-icon>
                {{ $t('settings.github') }}
              </el-button>
              <el-button type="primary" link>
                <el-icon><Document /></el-icon>
                {{ $t('settings.documentation') }}
              </el-button>
              <el-button type="primary" link>
                <el-icon><ChatDotRound /></el-icon>
                {{ $t('settings.community') }}
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Cpu, Lock, Bell, InfoFilled, Link, Document, ChatDotRound } from '@element-plus/icons-vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const activeMenu = ref('general')
const loading = ref(false)

const generalSettings = reactive({
  systemName: 'PioneClaw',
  systemDesc: t('login.subtitle'),
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  debugMode: false
})

// Watch language changes and update i18n
watch(() => generalSettings.language, (newLang) => {
  locale.value = newLang
  localStorage.setItem('language', newLang)
})

const executionSettings = reactive({
  maxToolTurns: 20,
  skillTimeout: 300,
  taskTimeout: 60,
  maxConcurrency: 10,
  enablePlanning: false,
  enableReflection: false,
  autoRetry: true,
  maxRetries: 3
})

const securitySettings = reactive({
  jwtSecret: '',
  tokenExpiry: 1440,
  multiLogin: true,
  fileApproval: false,
  networkApproval: false,
  codeApproval: true,
  logLevel: 'info',
  logRetention: 30
})

const notificationSettings = reactive({
  emailEnabled: false,
  smtpHost: '',
  smtpPort: 587,
  smtpUser: '',
  smtpPass: '',
  webhookEnabled: false,
  webhookUrl: '',
  notifyTaskComplete: true,
  notifyTaskFailed: true,
  notifySystemAlert: true
})

async function loadSettings() {
  loading.value = true
  try {
    const res = await api.get('/settings')
    const settings = res.data

    // 映射到各个设置组
    if (settings.system_name) generalSettings.systemName = settings.system_name.value
    if (settings.system_desc) generalSettings.systemDesc = settings.system_desc.value
    if (settings.language) generalSettings.language = settings.language.value
    if (settings.timezone) generalSettings.timezone = settings.timezone.value
    if (settings.debug_mode) generalSettings.debugMode = settings.debug_mode.value === 'true'

    if (settings.max_tool_turns) executionSettings.maxToolTurns = parseInt(settings.max_tool_turns.value)
    if (settings.skill_timeout) executionSettings.skillTimeout = parseInt(settings.skill_timeout.value)
    if (settings.task_timeout) executionSettings.taskTimeout = parseInt(settings.task_timeout.value)
    if (settings.max_concurrency) executionSettings.maxConcurrency = parseInt(settings.max_concurrency.value)
    if (settings.enable_planning) executionSettings.enablePlanning = settings.enable_planning.value === 'true'
    if (settings.enable_reflection) executionSettings.enableReflection = settings.enable_reflection.value === 'true'
    if (settings.auto_retry) executionSettings.autoRetry = settings.auto_retry.value === 'true'
    if (settings.max_retries) executionSettings.maxRetries = parseInt(settings.max_retries.value)

    if (settings.token_expiry) securitySettings.tokenExpiry = parseInt(settings.token_expiry.value)
    if (settings.multi_login) securitySettings.multiLogin = settings.multi_login.value === 'true'
    if (settings.file_approval) securitySettings.fileApproval = settings.file_approval.value === 'true'
    if (settings.network_approval) securitySettings.networkApproval = settings.network_approval.value === 'true'
    if (settings.code_approval) securitySettings.codeApproval = settings.code_approval.value === 'true'
    if (settings.log_level) securitySettings.logLevel = settings.log_level.value
    if (settings.log_retention) securitySettings.logRetention = parseInt(settings.log_retention.value)

    if (settings.email_enabled) notificationSettings.emailEnabled = settings.email_enabled.value === 'true'
    if (settings.smtp_host) notificationSettings.smtpHost = settings.smtp_host.value
    if (settings.smtp_port) notificationSettings.smtpPort = parseInt(settings.smtp_port.value)
    if (settings.smtp_user) notificationSettings.smtpUser = settings.smtp_user.value
    if (settings.smtp_pass) notificationSettings.smtpPass = settings.smtp_pass.value
    if (settings.webhook_enabled) notificationSettings.webhookEnabled = settings.webhook_enabled.value === 'true'
    if (settings.webhook_url) notificationSettings.webhookUrl = settings.webhook_url.value
    if (settings.notify_task_complete) notificationSettings.notifyTaskComplete = settings.notify_task_complete.value === 'true'
    if (settings.notify_task_failed) notificationSettings.notifyTaskFailed = settings.notify_task_failed.value === 'true'
    if (settings.notify_system_alert) notificationSettings.notifySystemAlert = settings.notify_system_alert.value === 'true'
  } catch (error) {
    console.error('Failed to load settings')
  } finally {
    loading.value = false
  }
}

async function saveSettings(type: string) {
  const settings: Record<string, string> = {}

  if (type === 'general') {
    settings.system_name = generalSettings.systemName
    settings.system_desc = generalSettings.systemDesc
    settings.language = generalSettings.language
    settings.timezone = generalSettings.timezone
    settings.debug_mode = String(generalSettings.debugMode)
  } else if (type === 'execution') {
    settings.max_tool_turns = String(executionSettings.maxToolTurns)
    settings.skill_timeout = String(executionSettings.skillTimeout)
    settings.task_timeout = String(executionSettings.taskTimeout)
    settings.max_concurrency = String(executionSettings.maxConcurrency)
    settings.enable_planning = String(executionSettings.enablePlanning)
    settings.enable_reflection = String(executionSettings.enableReflection)
    settings.auto_retry = String(executionSettings.autoRetry)
    settings.max_retries = String(executionSettings.maxRetries)
  } else if (type === 'security') {
    settings.token_expiry = String(securitySettings.tokenExpiry)
    settings.multi_login = String(securitySettings.multiLogin)
    settings.file_approval = String(securitySettings.fileApproval)
    settings.network_approval = String(securitySettings.networkApproval)
    settings.code_approval = String(securitySettings.codeApproval)
    settings.log_level = securitySettings.logLevel
    settings.log_retention = String(securitySettings.logRetention)
  } else if (type === 'notification') {
    settings.email_enabled = String(notificationSettings.emailEnabled)
    settings.smtp_host = notificationSettings.smtpHost
    settings.smtp_port = String(notificationSettings.smtpPort)
    settings.smtp_user = notificationSettings.smtpUser
    settings.smtp_pass = notificationSettings.smtpPass
    settings.webhook_enabled = String(notificationSettings.webhookEnabled)
    settings.webhook_url = notificationSettings.webhookUrl
    settings.notify_task_complete = String(notificationSettings.notifyTaskComplete)
    settings.notify_task_failed = String(notificationSettings.notifyTaskFailed)
    settings.notify_system_alert = String(notificationSettings.notifySystemAlert)
  }

  try {
    await api.put('/settings', { settings })
    ElMessage.success(t('settings.settingsSaved'))
  } catch (error) {
    ElMessage.error(t('settings.saveFailed'))
  }
}

function testNotification() {
  ElMessage.success(t('settings.testNotificationSent'))
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped lang="scss">
.settings-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;
}

.settings-container {
  display: flex;
  gap: 20px;
  align-items: stretch;
}

.settings-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--pc-bg-elevated);
  border-radius: var(--pc-radius-lg);
  border: 1px solid var(--pc-border);
  overflow: hidden;

  .el-menu {
    border-right: none;
    background: transparent;
    height: 100%;
    padding: 8px;
  }

  .el-menu-item {
    height: auto;
    line-height: normal;
    padding: 12px 16px !important;
    margin: 4px 0;
    border-radius: var(--pc-radius-md);
    transition: all 0.2s ease;

    .menu-item-content {
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }

    .menu-icon {
      font-size: 20px;
      margin-top: 2px;
      padding: 8px;
      border-radius: var(--pc-radius-sm);

      &.general {
        background: rgba(var(--pc-primary-rgb), 0.1);
        color: var(--pc-primary);
      }
      &.execution {
        background: rgba(var(--pc-accent-purple-rgb), 0.1);
        color: var(--pc-accent-purple);
      }
      &.security {
        background: rgba(var(--pc-accent-red-rgb), 0.1);
        color: var(--pc-accent-red);
      }
      &.notification {
        background: rgba(var(--pc-accent-orange-rgb), 0.1);
        color: var(--pc-accent-orange);
      }
      &.about {
        background: rgba(var(--pc-accent-green-rgb), 0.1);
        color: var(--pc-accent-green);
      }
    }

    .menu-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .menu-title {
      font-size: 14px;
      font-weight: 500;
      color: var(--pc-text-primary);
    }

    .menu-desc {
      font-size: 11px;
      color: var(--pc-text-muted);
      line-height: 1.3;
    }

    &:hover {
      background: rgba(var(--pc-primary-rgb), 0.06);
    }

    &.is-active {
      background: rgba(var(--pc-primary-rgb), 0.1);

      .menu-title {
        color: var(--pc-primary);
      }
    }
  }
}

.settings-content {
  flex: 1;
  min-width: 0;

  .el-card {
    box-sizing: border-box;
    background: var(--pc-bg-elevated);
    border: 1px solid var(--pc-border);
    min-height: 100%;
  }
}

.form-tip {
  color: var(--pc-text-muted);
  font-size: 12px;
  margin-left: 12px;
}

.about-content {
  .system-logo {
    text-align: center;
    padding: 20px 0 30px;

    img {
      margin-bottom: 16px;
    }

    h2 {
      margin: 0 0 8px;
      color: var(--pc-text-primary);
    }

    .version {
      color: var(--pc-text-muted);
      margin: 0;
    }
  }

  .tech-stack {
    h4 {
      margin: 0 0 12px;
      color: var(--pc-text-primary);
    }

    .tech-tags {
      .el-tag {
        margin-right: 8px;
        margin-bottom: 8px;
      }
    }
  }

  .links {
    display: flex;
    gap: 16px;
  }
}
</style>
