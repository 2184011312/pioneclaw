<template>
  <div class="profile-page">
    <el-card class="pc-glass-card" v-loading="loading">
      <template #header>
        <span class="card-title page-title">{{ $t('profile.title') }}</span>
      </template>

      <el-row :gutter="40">
        <!-- 左侧：头像区域 -->
        <el-col :span="6">
          <div class="avatar-section">
            <el-avatar :size="100" :src="userForm.avatar" class="avatar-preview">
              <el-icon :size="50"><User /></el-icon>
            </el-avatar>
            <div class="avatar-info">
              <div class="username">{{ userForm.display_name || userForm.username || $t('nav.profile') }}</div>
              <div class="user-role">{{ getRoleName(userStore.user?.role) }}</div>
            </div>
            <el-upload
              action="#"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              accept="image/*"
            >
              <el-button size="small">{{ $t('profile.changeAvatar') }}</el-button>
            </el-upload>
          </div>
        </el-col>

        <!-- 右侧：信息表单 -->
        <el-col :span="18">
          <el-tabs v-model="activeTab">
            <!-- 基本信息 -->
            <el-tab-pane :label="$t('profile.basicInfo')" name="info">
              <el-form :model="userForm" label-width="120px" ref="formRef" :rules="rules">
                <el-form-item :label="$t('profile.username')">
                  <el-input v-model="userForm.username" disabled />
                </el-form-item>

                <el-form-item :label="$t('profile.email')">
                  <el-input v-model="userForm.email" disabled />
                </el-form-item>

                <el-form-item :label="$t('profile.displayName')" prop="display_name">
                  <el-input v-model="userForm.display_name" :placeholder="$t('profile.enterDisplayName')" />
                </el-form-item>

                <el-form-item :label="$t('profile.avatarUrl')" prop="avatar">
                  <el-input v-model="userForm.avatar" :placeholder="$t('profile.avatarUrl')" />
                  <div class="form-tip">{{ $t('profile.avatarUrlTip') }}</div>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveProfile" :loading="saving">{{ $t('profile.saveChanges') }}</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 修改密码 -->
            <el-tab-pane :label="$t('profile.changePassword')" name="password">
              <el-form :model="passwordForm" label-width="120px" ref="passwordFormRef" :rules="passwordRules">
                <el-form-item :label="$t('profile.currentPassword')" prop="old_password">
                  <el-input v-model="passwordForm.old_password" type="password" show-password :placeholder="$t('profile.enterCurrentPassword')" />
                </el-form-item>

                <el-form-item :label="$t('profile.newPassword')" prop="new_password">
                  <el-input v-model="passwordForm.new_password" type="password" show-password :placeholder="$t('profile.enterNewPassword')" />
                </el-form-item>

                <el-form-item :label="$t('profile.confirmPassword')" prop="confirm_password">
                  <el-input v-model="passwordForm.confirm_password" type="password" show-password :placeholder="$t('profile.enterNewPassword')" />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="changePassword" :loading="changingPassword">{{ $t('profile.changePassword') }}</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type UploadProps } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'
import { useUserStore } from '../stores/user'

const { t: $t } = useI18n()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const saving = ref(false)
const loading = ref(false)
const changingPassword = ref(false)
const activeTab = ref('info')

const userForm = reactive({
  username: userStore.user?.username || '',
  email: userStore.user?.email || '',
  display_name: userStore.user?.display_name || '',
  avatar: userStore.user?.avatar || ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const rules = {
  display_name: [
    { max: 50, message: () => $t('profile.displayNameMaxLength'), trigger: 'blur' }
  ]
}

const passwordRules = {
  old_password: [
    { required: true, message: () => $t('profile.enterCurrentPassword'), trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: () => $t('profile.enterNewPassword'), trigger: 'blur' },
    { min: 6, message: () => $t('user.passwordLength'), trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: () => $t('profile.enterNewPassword'), trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== passwordForm.new_password) {
          callback(new Error($t('profile.passwordMismatch')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

function getRoleName(role?: string): string {
  const names: Record<string, string> = { SUPER_ADMIN: $t('user.superAdmin'), ORG_ADMIN: $t('user.orgAdmin'), user: $t('user.user') }
  return names[role || ''] || role || $t('user.user')
}

async function loadProfile() {
  loading.value = true
  try {
    const response = await api.get('/auth/me')
    userForm.username = response.data.username || ''
    userForm.email = response.data.email || ''
    userForm.display_name = response.data.display_name || ''
    userForm.avatar = response.data.avatar || ''
  } catch (error) {
    const u = userStore.user
    if (u) {
      userForm.username = u.username || ''
      userForm.email = u.email || ''
      userForm.display_name = u.display_name || ''
      userForm.avatar = u.avatar || ''
    }
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    await api.put('/auth/profile', {
      display_name: userForm.display_name,
      avatar: userForm.avatar
    })
    await userStore.fetchUser()
    ElMessage.success($t('profile.profileUpdated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('profile.updateFailed'))
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }

  changingPassword.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success($t('profile.passwordChanged'))
    Object.assign(passwordForm, { old_password: '', new_password: '', confirm_password: '' })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || $t('profile.passwordChangeFailed'))
  } finally {
    changingPassword.value = false
  }
}

const beforeAvatarUpload: UploadProps['beforeUpload'] = (rawFile) => {
  if (rawFile.size / 1024 / 1024 > 2) {
    ElMessage.error($t('profile.avatarSizeLimit'))
    return false
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    userForm.avatar = e.target?.result as string
  }
  reader.readAsDataURL(rawFile)
  return false
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped lang="scss">
.profile-page {
  .page-title {
    background: var(--pc-gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .card-title {
    font-size: 16px;
    font-weight: 600;
  }

  .avatar-section {
    text-align: center;
    padding: 20px 0;

    .avatar-preview {
      margin-bottom: 16px;
      background: var(--pc-primary);
    }

    .avatar-info {
      margin-bottom: 16px;

      .username {
        font-size: 16px;
        font-weight: 500;
        color: var(--pc-text-primary);
        margin-bottom: 4px;
      }

      .user-role {
        font-size: 13px;
        color: var(--pc-text-muted);
      }
    }
  }

  .form-tip {
    font-size: 12px;
    color: var(--pc-text-muted);
    margin-top: 4px;
  }

  :deep(.el-tabs__content) {
    padding: 20px 0;
  }
}
</style>
