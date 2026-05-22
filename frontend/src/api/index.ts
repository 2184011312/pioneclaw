import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getAccessToken } from '@/stores/user'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,  // 普通 CRUD 操作默认 30 秒超时
})

/** Agent Loop / Chat 等长时间运行的操作使用更长超时 */
export const longApi = axios.create({
  baseURL: '/api',
  timeout: 300000,  // Agent 循环可能需要 5 分钟
})

// 通用响应类型
export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface UserResponse {
  id: number
  username: string
  email: string
  display_name: string
  avatar?: string
  role: string
  is_active: boolean
  organization_id?: string
  is_super_admin: boolean
  is_org_admin: boolean
  created_at: string
}

// 共享的重定向锁，防止多个拦截器同时触发跳转
let isRedirecting = false

function setupInterceptors(instance: ReturnType<typeof axios.create>) {
  instance.interceptors.request.use(
    (config) => {
      const token = getAccessToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  instance.interceptors.response.use(
    (response) => {
      return response
    },
    (error) => {
      if (error.response) {
        const { status, data } = error.response

        if (status === 401) {
          const token = getAccessToken()
          const isLoginRequest = error.config?.url?.includes('/auth/login') || error.config?.url?.includes('/auth/token')

          if (token && !isRedirecting && !isLoginRequest) {
            isRedirecting = true
            ElMessage.error('登录已过期，请重新登录')
            setTimeout(() => {
              window.location.href = '/login'
            }, 800)
          }
        }
        if (status === 422 && Array.isArray(data?.detail)) {
          ;(error as any).detail = data.detail.map((e: any) => e.msg || e.message).join('; ')
        } else {
          ;(error as any).detail = data?.detail || ''
        }
      } else {
        ;(error as any).detail = ''
      }

      return Promise.reject(error)
    }
  )
}

setupInterceptors(api)
setupInterceptors(longApi)

export default api
