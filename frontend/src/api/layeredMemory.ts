import { api } from './index'

export interface LayeredMemoryItem {
  id: number
  uri: string
  layer: number
  context_type: string
  name: string
  abstract?: string
  overview?: string
  importance: number
  access_count: number
  source?: string
  session_id?: string
  created_at: string
  updated_at: string
}

export interface LayeredMemoryDetail extends LayeredMemoryItem {
  content: string
  parent_uri?: string
  user_id: number
  agent_id?: number
  vector_id?: string
  is_active: boolean
  tags?: string[]
}

export interface LayeredMemoryStats {
  total: number
  l0_count: number
  l1_count: number
  l2_count: number
  by_type: Record<string, number>
  by_source: Record<string, number>
  vector_count: number
}

export interface RecallResult {
  uri: string
  name: string
  layer: number
  context_type: string
  text: string
  score: number
  abstract?: string
  overview?: string
}

export interface ListResponse<T> {
  items: T[]
  total: number
}

export const layeredMemoryApi = {
  // 存储记忆
  store(data: {
    content: string
    name: string
    context_type?: string
    tags?: string[]
    source?: string
    importance?: number
    session_id?: string
    agent_id?: number
  }) {
    return api.post<LayeredMemoryDetail>('/layered-memory/store', data)
  },

  // 语义检索
  recall(data: {
    query: string
    context_type?: string
    layers?: number[]
    top_k?: number
    session_id?: string
    agent_id?: number
  }) {
    return api.post<{ results: RecallResult[]; intent?: string; total: number }>('/layered-memory/recall', data)
  },

  // 获取指定记忆
  get(uri: string, layer?: number) {
    const params = layer !== undefined ? { layer } : {}
    return api.get<LayeredMemoryDetail>(`/layered-memory/${encodeURIComponent(uri)}`, { params })
  },

  // 更新记忆
  update(uri: string, data: {
    content?: string
    name?: string
    tags?: string[]
    importance?: number
    is_active?: boolean
    regenerate_tiers?: boolean
  }) {
    return api.put<LayeredMemoryDetail>(`/layered-memory/${encodeURIComponent(uri)}`, data)
  },

  // 删除记忆
  delete(uri: string) {
    return api.delete(`/layered-memory/${encodeURIComponent(uri)}`)
  },

  // 列表
  list(params?: {
    layer?: number
    context_type?: string
    session_id?: string
    keyword?: string
    page?: number
    page_size?: number
  }) {
    return api.get<ListResponse<LayeredMemoryItem>>('/layered-memory', { params })
  },

  // 统计
  stats() {
    return api.get<LayeredMemoryStats>('/layered-memory/stats/overview')
  },

  // L1→L2 提升
  promote(uri: string) {
    return api.post<LayeredMemoryDetail>('/layered-memory/promote', { uri })
  },

  // 清理 L0
  evict(sessionId: string) {
    return api.post('/layered-memory/evict', { session_id: sessionId })
  },
}
