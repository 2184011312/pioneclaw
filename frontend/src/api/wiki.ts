import { api } from './index'
import type {
  Wiki,
  WikiDetail,
  WikiTree,
  WikiVersion,
  WikiCreate,
  WikiUpdate,
  WikiImport,
  WikiSearchResult,
} from '../types/wiki'
import type { ListResponse } from './index'

export const wikiApi = {
  // 获取 Wiki 列表
  list(params?: { organization_id?: string; status?: string; tag?: string; skip?: number; limit?: number }) {
    return api.get<ListResponse<Wiki>>('/wiki/', { params })
  },

  // 获取 Wiki 树
  tree(params?: { organization_id?: string }) {
    return api.get<WikiTree[]>('/wiki/tree', { params })
  },

  // 搜索 Wiki
  search(params: { q: string; skip?: number; limit?: number }) {
    return api.get<{ items: WikiSearchResult[]; total: number }>('/wiki/search', { params })
  },

  // 创建 Wiki
  create(data: WikiCreate) {
    return api.post<Wiki>('/wiki/', data)
  },

  // 导入 Markdown
  import(data: WikiImport) {
    return api.post<Wiki>('/wiki/import', data)
  },

  // 获取 Wiki 详情
  get(id: string) {
    return api.get<WikiDetail>(`/wiki/${id}`)
  },

  // 更新 Wiki
  update(id: string, data: WikiUpdate) {
    return api.put<Wiki>(`/wiki/${id}`, data)
  },

  // 删除 Wiki
  delete(id: string) {
    return api.delete(`/wiki/${id}`)
  },

  // 获取版本历史
  history(id: string, params?: { skip?: number; limit?: number }) {
    return api.get<ListResponse<WikiVersion>>(`/wiki/${id}/history`, { params })
  },

  // 恢复到指定版本
  restore(id: string, version: number) {
    return api.post<Wiki>(`/wiki/${id}/restore/${version}`)
  },
}
