import { api } from './index'

export interface PluginResponse {
  plugin_id: string
  name: string
  version: string
  description: string
  state: string // loaded | unloaded | error
  error: string | null
  dependencies: string[]
  subscriptions: string[]
}

export interface PluginStats {
  total: number
  by_state: Record<string, number>
  plugin_dir: string | null
}

export interface LifecycleResponse {
  plugin_id: string
  name: string
  state: string
  health_status: boolean | null
  last_health_check: string | null
  retry_count: number | null
  max_retries: number | null
  error_history: Array<Record<string, any>>
  paused_at: string | null
  stopped_at: string | null
  last_transition: Record<string, any> | null
}

export interface SubscriptionInfo {
  sub_id: string
  topic: string
  handler: string
  priority: number
  wildcard: boolean
}

export const pluginsApi = {
  // 发现可用插件
  discover() {
    return api.get<string[]>('/plugins/discover')
  },

  // 列出已加载插件
  list(state?: string) {
    const params = state ? { state } : {}
    return api.get<PluginResponse[]>('/plugins/list', { params })
  },

  // 获取插件详情
  get(pluginId: string) {
    return api.get<PluginResponse>(`/plugins/${pluginId}`)
  },

  // 加载插件
  load(pluginId: string, config?: Record<string, unknown>) {
    return api.post<PluginResponse>('/plugins/load', {
      plugin_id: pluginId,
      config,
    })
  },

  // 卸载插件
  unload(pluginId: string) {
    return api.post<{ success: boolean; message: string }>(`/plugins/unload/${pluginId}`)
  },

  // 热重载插件
  reload(pluginId: string) {
    return api.post<PluginResponse>(`/plugins/reload/${pluginId}`)
  },

  // 插件统计
  stats() {
    return api.get<PluginStats>('/plugins/stats')
  },

  // 发布事件
  publishEvent(topic: string, data: Record<string, unknown> = {}) {
    return api.post<{ success: boolean; handlers_fired: number }>('/plugins/events/publish', {
      topic,
      data,
    })
  },

  // 列出事件订阅
  listSubscriptions(topic?: string) {
    const params = topic ? { topic } : {}
    return api.get<SubscriptionInfo[]>('/plugins/events/subscriptions', { params })
  },

  // ---- 生命周期操作 (Stage PP) ----

  pause(pluginId: string) {
    return api.post<{ success: boolean; message: string }>(`/plugins/${pluginId}/pause`)
  },

  resume(pluginId: string) {
    return api.post<{ success: boolean; message: string }>(`/plugins/${pluginId}/resume`)
  },

  stop(pluginId: string) {
    return api.post<{ success: boolean; message: string }>(`/plugins/${pluginId}/stop`)
  },

  restart(pluginId: string) {
    return api.post<{ success: boolean; message: string; state: string }>(`/plugins/${pluginId}/restart`)
  },

  enable(pluginId: string) {
    return api.post<{ success: boolean; message: string }>(`/plugins/${pluginId}/enable`)
  },

  disable(pluginId: string) {
    return api.post<{ success: boolean; message: string }>(`/plugins/${pluginId}/disable`)
  },

  health(pluginId: string) {
    return api.get<LifecycleResponse>(`/plugins/${pluginId}/health`)
  },

  healthAll() {
    return api.get<LifecycleResponse[]>('/plugins/health')
  },
}
