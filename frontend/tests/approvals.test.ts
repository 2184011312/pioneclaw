import { describe, it, expect, vi, beforeEach } from 'vitest'
import { approvalsApi } from '@/api/approvals'

// Mock axios
vi.mock('@/api/index', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { api } from '@/api/index'

describe('approvalsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('should call GET /approvals with default params', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] })

      await approvalsApi.list()

      expect(api.get).toHaveBeenCalledWith('/approvals', { params: undefined })
    })

    it('should call GET /approvals with filter params', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] })

      await approvalsApi.list({ status_filter: 'pending', scope: 'org' })

      expect(api.get).toHaveBeenCalledWith('/approvals', {
        params: { status_filter: 'pending', scope: 'org' },
      })
    })
  })

  describe('getPendingCount', () => {
    it('should call GET /approvals/pending-count', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: { pending_count: 5 } })

      const result = await approvalsApi.getPendingCount()

      expect(api.get).toHaveBeenCalledWith('/approvals/pending-count')
      expect(result.data.pending_count).toBe(5)
    })
  })

  describe('get', () => {
    it('should call GET /approvals/:id', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: { id: 1 } })

      await approvalsApi.get(1)

      expect(api.get).toHaveBeenCalledWith('/approvals/1')
    })
  })

  describe('create', () => {
    it('should call POST /approvals with data', async () => {
      const createData = {
        approval_type: 'skill_to_org',
        title: 'Test Approval',
        resource_type: 'skill',
        resource_id: '1',
        target_scope: 'org',
      }
      vi.mocked(api.post).mockResolvedValue({ data: { id: 1, ...createData } })

      await approvalsApi.create(createData)

      expect(api.post).toHaveBeenCalledWith('/approvals', createData)
    })
  })

  describe('review', () => {
    it('should call POST /approvals/:id/review with approve', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: { id: 1, status: 'approved' } })

      await approvalsApi.review(1, { approved: true, review_comment: 'OK' })

      expect(api.post).toHaveBeenCalledWith('/approvals/1/review', {
        approved: true,
        review_comment: 'OK',
      })
    })

    it('should call POST /approvals/:id/review with reject', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: { id: 1, status: 'rejected' } })

      await approvalsApi.review(1, { approved: false, review_comment: 'Not good' })

      expect(api.post).toHaveBeenCalledWith('/approvals/1/review', {
        approved: false,
        review_comment: 'Not good',
      })
    })
  })

  describe('cancel', () => {
    it('should call POST /approvals/:id/cancel', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: { message: 'Approval cancelled' } })

      await approvalsApi.cancel(1)

      expect(api.post).toHaveBeenCalledWith('/approvals/1/cancel')
    })
  })
})
