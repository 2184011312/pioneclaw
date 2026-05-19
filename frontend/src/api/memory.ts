import { api } from './index'

export interface MemoryEntry {
  line_number: number
  source: string
  content: string
  date: string
}

export interface MemoryStats {
  total_entries: number
  sources: Record<string, number>
  date_range: { min: string; max: string } | null
  total_chars: number
  oldest_date?: string
  newest_date?: string
}

export interface MemorySearchResult {
  entries: MemoryEntry[]
  total: number
  keywords: string[]
  match_mode: string
}

export const memoryApi = {
  /** 获取记忆概览 */
  info() {
    return api.get<MemoryStats>('/memory')
  },

  /** 获取详细统计 */
  stats() {
    return api.get<MemoryStats>('/memory/stats')
  },

  /** 获取最近 N 条 */
  recent(count = 20) {
    return api.get<{ entries: MemoryEntry[]; total: number }>('/memory/recent', { params: { count } })
  },

  /** 获取单条 */
  line(lineNumber: number) {
    return api.get<MemoryEntry>(`/memory/line/${lineNumber}`)
  },

  /** 获取多条 */
  lines(start: number, end: number) {
    return api.get<{ entries: MemoryEntry[]; total: number }>('/memory/lines', { params: { start, end } })
  },

  /** 搜索 */
  search(keywords: string[], maxResults = 15, matchMode: 'or' | 'and' = 'or') {
    return api.post<MemorySearchResult>('/memory/search', { keywords, max_results: maxResults, match_mode: matchMode })
  },

  /** 追加一条 */
  append(source: string, content: string, date?: string) {
    return api.post<{ success: boolean; line_number: number }>('/memory/append', { source, content, date })
  },

  /** 批量追加 */
  appendBatch(source: string, entries: string[]) {
    return api.post<{ success: boolean; count: number; line_numbers: number[] }>('/memory/append-batch', { source, entries })
  },

  /** 删除指定行 */
  deleteLine(lineNumber: number) {
    return api.delete(`/memory/line/${lineNumber}`)
  },

  /** 批量删除 */
  deleteLines(lineNumbers: number[]) {
    return api.delete('/memory/lines', { data: { line_numbers: lineNumbers } })
  },

  /** 清空 */
  clear() {
    return api.delete('/memory/clear')
  },

  /** 导出 */
  exportMemory() {
    return api.get<{ content: string; line_count: number }>('/memory/export')
  },

  /** 导入 */
  importMemory(content: string, source = 'import') {
    return api.post<{ success: boolean; imported_count: number }>('/memory/import', { content, source })
  },

  /** 全量更新内容（替换整个文件） */
  saveContent(content: string) {
    return api.put<{ success: boolean; line_count: number }>('/memory/content', { content })
  },

  /** 获取来源列表 */
  sources() {
    return api.get<{ sources: { value: string; label: string }[] }>('/memory/sources')
  },
}
