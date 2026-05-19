import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

interface User {
  id: number
  username: string
  email: string
  display_name: string
  role: string
  avatar?: string
  permissions?: string[]
}

// 模块级私有变量：access_token 仅存内存，不落 localStorage/sessionStorage
let _token: string = ''

export function getAccessToken(): string {
  return _token
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(_token)
  const user = ref<User | null>(null)
  const isInitialized = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const displayName = computed(() => user.value?.display_name || user.value?.username || '用户')
  const avatar = computed(() => user.value?.avatar || '')
  const permissions = computed<string[]>(() => user.value?.permissions || [])
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
  const isOrgAdmin = computed(() => user.value?.role === 'org_admin')
  const isAdmin = computed(() => user.value?.role === 'super_admin' || user.value?.role === 'org_admin')

  async function login(username: string, password: string) {
    const response = await api.post('/auth/login', {
      username,
      password
    })
    // access_token 仅存内存，refresh_token 由后端 HttpOnly cookie 管理
    _token = response.data.access_token
    token.value = _token

    await fetchUser()
  }

  async function restoreSession(): Promise<boolean> {
    // 页面刷新后，通过 refresh_token cookie 获取新 access_token
    try {
      const response = await api.post('/auth/refresh-token')
      _token = response.data.access_token
      token.value = _token
      await fetchUser()
      isInitialized.value = true
      return true
    } catch {
      isInitialized.value = true
      return false
    }
  }

  async function fetchUser() {
    if (!token.value) return

    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // ignore network errors
    }
    _token = ''
    token.value = ''
    user.value = null
    // 清除会话数据
    localStorage.removeItem('pioneclaw_conversations')
  }

  return {
    token,
    user,
    isInitialized,
    isLoggedIn,
    displayName,
    avatar,
    permissions,
    isSuperAdmin,
    isOrgAdmin,
    isAdmin,
    login,
    restoreSession,
    fetchUser,
    logout
  }
})
