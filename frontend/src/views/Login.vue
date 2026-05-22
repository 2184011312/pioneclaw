<template>
  <div class="login-page">
    <!-- 背景 -->
    <div class="bg-grid"></div>
    <div class="bg-glow glow-1"></div>
    <div class="bg-glow glow-2"></div>

    <!-- 主布局 -->
    <div class="login-layout">
      <!-- 左侧品牌区 -->
      <div class="brand-panel">
        <div class="brand-inner">
          <div class="brand-logo">
            <svg viewBox="0 0 48 48" fill="none">
              <path d="M24 4L42 14V34L24 44L6 34V14L24 4Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
              <circle cx="24" cy="24" r="6" fill="currentColor" opacity="0.5"/>
              <path d="M24 10V18M24 30V38M12 18L18 21M30 27L36 30M12 30L18 27M30 21L36 18" stroke="currentColor" stroke-width="1" opacity="0.3"/>
            </svg>
          </div>
          <h1 class="brand-name">PioneClaw</h1>
          <p class="brand-tagline">{{ $t('login.subtitle') }}</p>

          <div class="feature-list">
            <div class="feature-item">
              <span class="feature-icon"><el-icon><Cpu /></el-icon></span>
              <span class="feature-text">{{ $t('login.feature1') }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><el-icon><Connection /></el-icon></span>
              <span class="feature-text">{{ $t('login.feature2') }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><el-icon><Tools /></el-icon></span>
              <span class="feature-text">{{ $t('login.feature3') }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><el-icon><Lock /></el-icon></span>
              <span class="feature-text">{{ $t('login.feature4') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 分割线 -->
      <div class="divider"></div>

      <!-- 右侧登录区 -->
      <div class="login-panel">
        <div class="login-card">
          <div class="card-accent"></div>
          <h2 class="card-title">{{ $t('login.welcome') }}</h2>
          <p class="card-sub">{{ $t('login.subtitle') }}</p>

          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            @keyup.enter="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                :placeholder="$t('login.username')"
                :prefix-icon="User"
                size="large"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                :placeholder="$t('login.password')"
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>

            <el-form-item>
              <button
                type="button"
                class="login-btn"
                :class="{ loading }"
                @click="handleLogin"
                :disabled="loading"
              >
                <span v-if="!loading">{{ $t('login.submit') }}</span>
                <span v-else class="btn-loader"></span>
              </button>
            </el-form-item>
          </el-form>

          <div class="login-footer">
            <span>{{ $t('login.defaultCredentials') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Cpu, Connection, Tools } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useI18n } from 'vue-i18n'

const { t: $t } = useI18n()

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: $t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: $t('login.passwordRequired'), trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success($t('login.success'))
    router.push('/dashboard')
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--pc-bg-deep);
  position: relative;
  overflow: hidden;
  transition: background 0.3s ease;
}

// ── 背景 ──
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(var(--pc-primary-rgb), 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--pc-primary-rgb), 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 25%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 25%, transparent 70%);
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  pointer-events: none;
}
.glow-1 {
  width: 600px;
  height: 600px;
  background: rgba(var(--pc-primary-rgb), 0.08);
  top: -200px;
  right: -200px;
  animation: breathe 8s ease-in-out infinite;
}
.glow-2 {
  width: 500px;
  height: 500px;
  background: rgba(var(--pc-accent-purple-rgb), 0.06);
  bottom: -150px;
  left: -150px;
  animation: breathe 10s ease-in-out infinite reverse;
}

@keyframes breathe {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

// ── 主布局 ──
.login-layout {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: stretch;
  gap: 0;
  background: var(--pc-glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--pc-glass-border);
  border-radius: var(--pc-radius-xl);
  box-shadow: var(--pc-shadow-lg), 0 0 80px rgba(var(--pc-primary-rgb), 0.06);
  overflow: hidden;
  animation: pc-slide-up 0.5s ease;
}

// ── 品牌面板 ──
.brand-panel {
  width: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 40px;
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at top left, rgba(var(--pc-primary-rgb), 0.08), transparent 60%);
    pointer-events: none;
  }
}

.brand-inner {
  position: relative;
  z-index: 1;
}

.brand-logo {
  width: 60px;
  height: 60px;
  margin: 0 auto 20px;
  color: var(--pc-primary);
  filter: drop-shadow(0 0 18px rgba(var(--pc-primary-rgb), 0.5));
  margin-bottom: 20px;
}

.brand-name {
  font-size: 32px;
  font-weight: 700;
  background: var(--pc-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.brand-tagline {
  font-size: 14px;
  color: var(--pc-text-muted);
  margin: 0 0 36px;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--pc-radius-sm);
  transition: all 0.25s ease;

  .feature-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(var(--pc-primary-rgb), 0.1);
    color: var(--pc-primary);
    font-size: 16px;
    flex-shrink: 0;
  }

  .feature-text {
    font-size: 13px;
    color: var(--pc-text-secondary);
  }

  &:hover {
    background: rgba(var(--pc-primary-rgb), 0.06);
    transform: translateY(-1px);

    .feature-icon {
      background: rgba(var(--pc-primary-rgb), 0.18);
    }
  }
}

// ── 分割线 ──
.divider {
  width: 1px;
  align-self: stretch;
  background: linear-gradient(
    to bottom,
    transparent,
    var(--pc-border) 20%,
    var(--pc-border) 80%,
    transparent
  );
  flex-shrink: 0;
}

// ── 登录面板 ──
.login-panel {
  width: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 48px;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at bottom right, rgba(var(--pc-accent-purple-rgb), 0.04), transparent 60%);
    pointer-events: none;
  }
}

.login-card {
  width: 100%;
  position: relative;
  z-index: 1;

  .card-accent {
    position: absolute;
    top: -48px;
    left: -48px;
    right: -48px;
    height: 2px;
    background: var(--pc-gradient-primary);
    opacity: 0;
  }
}

.card-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--pc-text-primary);
  margin: 0 0 6px;
  text-align: center;
}

.card-sub {
  font-size: 13px;
  color: var(--pc-text-muted);
  margin: 0 0 28px;
  text-align: center;
}

// ── 表单 ──
.login-form {
  :deep(.el-form-item) {
    margin-bottom: 18px;
  }

  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid var(--pc-border) !important;
    border-radius: var(--pc-radius-md) !important;
    box-shadow: none !important;
    padding: 4px 12px;
    transition: all 0.2s;

    &:hover {
      border-color: var(--pc-border-hover) !important;
    }

    &.is-focus {
      border-color: var(--pc-primary) !important;
      box-shadow: 0 0 0 3px rgba(var(--pc-primary-rgb), 0.12) !important;
    }
  }

  :deep(.el-input__inner) {
    color: var(--pc-text-primary);

    &::placeholder {
      color: var(--pc-text-muted);
    }
  }

  :deep(.el-input__prefix .el-icon) {
    color: var(--pc-text-muted);
  }
}

// ── 登录按钮 ──
.login-btn {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: var(--pc-radius-md);
  background: var(--pc-gradient-primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, transparent, rgba(255,255,255,0.1), transparent);
    transform: translateX(-100%);
    transition: transform 0.5s;
  }

  &:hover::before {
    transform: translateX(100%);
  }

  &:hover {
    box-shadow: 0 0 25px rgba(var(--pc-primary-rgb), 0.4);
    transform: translateY(-1px);
  }

  &.loading {
    opacity: 0.7;
    pointer-events: none;
  }

  .btn-loader {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-footer {
  text-align: center;
  margin-top: 20px;

  span {
    color: var(--pc-text-muted);
    font-size: 12px;
    letter-spacing: 0.3px;
  }
}

// ── 响应式 ──
@media (max-width: 860px) {
  .brand-panel {
    display: none;
  }

  .divider {
    display: none;
  }

  .login-layout {
    border-radius: var(--pc-radius-lg);
  }

  .login-panel {
    width: 400px;
    padding: 40px 36px;
  }
}

@media (max-width: 440px) {
  .login-panel {
    width: calc(100vw - 32px);
    padding: 32px 24px;
  }
}
</style>
