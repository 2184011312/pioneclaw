import { api } from './index'

// ==================== TypeScript 接口 ====================

export interface SpanItem {
  id: string
  trace_id: string
  parent_id: string | null
  kind: string  // "trace" | "agent" | "llm" | "tool" | "handoff" | "guardrail" | "hook" | "retrieval" | "embedding"
  name: string
  start_time: number  // unix timestamp (seconds)
  end_time: number | null
  duration_ms: number
  status: string  // "running" | "success" | "error" | "cancelled"
  error: string | null
  input_data: Record<string, unknown>
  output_data: Record<string, unknown>
  metadata: Record<string, unknown>
  tokens: { prompt: number; completion: number; total: number } | null
  children: SpanItem[]
}

export interface TraceItem {
  id: string
  name: string
  start_time: number
  end_time: number | null
  duration_ms: number
  total_tokens: number
  total_cost: number
  span_count: number
  error_count: number
  agent_id: string
  agent_name: string
  session_id: string
  user_id: number | null
  metadata: Record<string, unknown>
  root_span: SpanItem | null
}

export interface TimelineItem {
  id: string
  name: string
  kind: string
  start: number
  end: number | null
  duration_ms: number
  status: string
  depth: number
  start_offset_ms: number
}

export interface TimelineResponse {
  trace_id: string
  trace_name: string
  total_duration_ms: number
  items: TimelineItem[]
}

export interface TraceStats {
  total_traces: number
  total_spans: number
  total_tokens: number
  total_errors: number
  avg_duration_ms: number
  by_kind: Record<string, number>
  by_agent: Record<string, number>
}

export interface TraceListResponse {
  items: TraceItem[]
  total: number
}

// ==================== API 方法 ====================

export const tracingApi = {
  /** 获取追踪列表 */
  list(params?: {
    agent_id?: string
    session_id?: string
    user_id?: number
    limit?: number
  }) {
    return api.get<TraceListResponse>('/tracing/', { params })
  },

  /** 获取追踪统计 */
  stats(params?: {
    agent_id?: string
    session_id?: string
    user_id?: number
  }) {
    return api.get<TraceStats>('/tracing/stats', { params })
  },

  /** 获取单条追踪详情（含 span 树） */
  get(traceId: string) {
    return api.get<TraceItem>(`/tracing/${traceId}`)
  },

  /** 获取追踪时间线（Gantt 图表数据） */
  getTimeline(traceId: string) {
    return api.get<TimelineResponse>(`/tracing/${traceId}/timeline`)
  },

  /** 获取追踪的所有 span（平铺列表） */
  getSpans(traceId: string, params?: { kind?: string; status?: string }) {
    return api.get<SpanItem[]>(`/tracing/${traceId}/spans`, { params })
  },

  /** 删除单条追踪 */
  delete(traceId: string) {
    return api.delete(`/tracing/${traceId}`)
  },

  /** 清空所有追踪 */
  clearAll(keepRecent: number = 100) {
    return api.delete('/tracing/', { params: { keep_recent: keepRecent } })
  },
}
