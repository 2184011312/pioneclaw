import { api } from './index'
import type {
  Organization,
  OrganizationTree,
  OrganizationSimple,
  OrganizationCreate,
  OrganizationUpdate,
} from '../types/organization'
import type { ListResponse } from './index'

export const organizationApi = {
  // 获取组织列表
  list(params?: { status?: string; type?: string; skip?: number; limit?: number }) {
    return api.get<ListResponse<Organization>>('/organizations/', { params })
  },

  // 获取组织树
  tree() {
    return api.get<OrganizationTree[]>('/organizations/tree')
  },

  // 获取简化组织列表
  simple() {
    return api.get<OrganizationSimple[]>('/organizations/simple')
  },

  // 创建组织
  create(data: OrganizationCreate) {
    return api.post<Organization>('/organizations/', data)
  },

  // 获取组织详情
  get(id: string) {
    return api.get<Organization>(`/organizations/${id}`)
  },

  // 更新组织
  update(id: string, data: OrganizationUpdate) {
    return api.put<Organization>(`/organizations/${id}`, data)
  },

  // 删除组织
  delete(id: string) {
    return api.delete(`/organizations/${id}`)
  },

  // 获取组织用户
  getUsers(orgId: string, params?: { skip?: number; limit?: number }) {
    return api.get<ListResponse<any>>(`/organizations/${orgId}/users`, { params })
  },
}
