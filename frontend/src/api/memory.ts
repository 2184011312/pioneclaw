import { api } from './index'

export interface MemoryEntry {
  id: string
  filename: string
  name: string
  description: string
  type: 'user' | 'feedback' | 'project' | 'reference'
  content: string
  created_at: string | null
  updated_at: string | null
  freshness: string
  is_stale: boolean
  tags: string[]
}

export interface MemoryIndexEntry {
  filename: string
  description: string
  path: string
}

export interface MemoryIndexResponse {
  content: string
  entries: MemoryIndexEntry[]
}

export interface MemoryStats {
  total_files: number
  index_entries: number
  by_type: Record<string, number>
}

export interface MemoryListResponse {
  entries: MemoryEntry[]
  total: number
}

export interface MemorySearchResponse {
  entries: MemoryEntry[]
  total: number
  keyword: string
}

export interface MemoryCreatePayload {
  content: string
  type?: string
  name?: string
  description?: string
  tags?: string[]
}

export interface MemoryUpdatePayload {
  content: string
  name?: string
  description?: string
  tags?: string[]
}

export const memoryApi = {
  /** 获取所有记忆列表 */
  list(params?: {
    type?: string
    sort_by?: string
    order?: string
    limit?: number
    offset?: number
  }) {
    return api.get<MemoryListResponse>('/memory', { params })
  },

  /** 获取 MEMORY.md 索引 */
  getIndex() {
    return api.get<MemoryIndexResponse>('/memory/index')
  },

  /** 获取统计概览 */
  stats() {
    return api.get<MemoryStats>('/memory/stats')
  },

  /** 获取单个记忆文件 */
  get(filename: string) {
    return api.get<MemoryEntry>(`/memory/${encodeURIComponent(filename)}`)
  },

  /** 创建新记忆 */
  create(payload: MemoryCreatePayload) {
    return api.post<MemoryEntry>('/memory', payload)
  },

  /** 更新记忆 */
  update(filename: string, payload: MemoryUpdatePayload) {
    return api.put<MemoryEntry>(`/memory/${encodeURIComponent(filename)}`, payload)
  },

  /** 删除记忆 */
  delete(filename: string) {
    return api.delete(`/memory/${encodeURIComponent(filename)}`)
  },

  /** 全文搜索 */
  search(keyword: string, type?: string, limit?: number) {
    return api.post<MemorySearchResponse>('/memory/search', { keyword, type, limit })
  },
}
