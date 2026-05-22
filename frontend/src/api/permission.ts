import { api } from './index'
import type {
  Permission,
  PermissionTree,
  PermissionCreate,
  PermissionUpdate,
  UserPermissions,
} from '../types/permission'
import type { ListResponse } from './index'

export const permissionApi = {
  // 获取权限列表
  list(params?: { type?: string; resource?: string; is_active?: boolean; skip?: number; limit?: number }) {
    return api.get<ListResponse<Permission>>('/permissions/', { params })
  },

  // 获取权限树
  tree() {
    return api.get<PermissionTree[]>('/permissions/tree')
  },

  // 获取所有资源类型
  resources() {
    return api.get<string[]>('/permissions/resources')
  },

  // 创建权限
  create(data: PermissionCreate) {
    return api.post<Permission>('/permissions/', data)
  },

  // 获取权限详情
  get(id: string) {
    return api.get<Permission>(`/permissions/${id}`)
  },

  // 更新权限
  update(id: string, data: PermissionUpdate) {
    return api.put<Permission>(`/permissions/${id}`, data)
  },

  // 删除权限
  delete(id: string) {
    return api.delete(`/permissions/${id}`)
  },

  // 初始化默认权限
  initDefaults() {
    return api.post('/permissions/init-defaults')
  },

  // 获取用户权限
  getUserPermissions(userId: number) {
    return api.get<UserPermissions>(`/permissions/user/${userId}/permissions`)
  },
}
