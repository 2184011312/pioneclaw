import { api } from './index'

export interface ApprovalResponse {
  id: number
  approval_type: string
  status: string // pending | approved | rejected | cancelled
  title: string
  description: string | null
  requester_id: number
  requester_name: string | null
  requester_org_id: string | null
  reviewer_id: number | null
  reviewed_at: string | null
  review_comment: string | null
  resource_type: string // skill | wiki | document
  resource_id: string
  target_scope: string // org | system
  target_org_id: string | null
  extra_data: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ApprovalCreate {
  approval_type: string
  title: string
  description?: string
  resource_type: string
  resource_id: string
  target_scope: string
  target_org_id?: string
  metadata?: Record<string, unknown>
}

export interface ApprovalReview {
  approved: boolean
  review_comment?: string
}

export const approvalsApi = {
  // 获取审批列表
  list(params?: { status_filter?: string; scope?: string; skip?: number; limit?: number }) {
    return api.get<ApprovalResponse[]>('/approvals', { params })
  },

  // 获取待审批数量
  getPendingCount() {
    return api.get<{ pending_count: number }>('/approvals/pending-count')
  },

  // 获取审批详情
  get(id: number) {
    return api.get<ApprovalResponse>(`/approvals/${id}`)
  },

  // 提交审批
  create(data: ApprovalCreate) {
    return api.post<ApprovalResponse>('/approvals', data)
  },

  // 审批（批准/拒绝）
  review(id: number, data: ApprovalReview) {
    return api.post<ApprovalResponse>(`/approvals/${id}/review`, data)
  },

  // 取消审批
  cancel(id: number) {
    return api.post<{ message: string }>(`/approvals/${id}/cancel`)
  },
}
