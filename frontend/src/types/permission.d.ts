// PioneClaw - 权限类型
export interface Permission {
  id: string
  name: string
  code: string
  description?: string
  type: string // menu/system/app/api
  resource: string
  action: string
  parent_id?: string
  menu_id?: string
  is_system: boolean
  is_active: boolean
  sort_order: number
  created_at: string
}

export interface PermissionTree extends Permission {
  children: PermissionTree[]
}

export interface PermissionCreate {
  name: string
  code: string
  description?: string
  type?: string
  resource?: string
  action?: string
  parent_id?: string
  sort_order?: number
}

export interface PermissionUpdate {
  name?: string
  code?: string
  description?: string
  type?: string
  resource?: string
  action?: string
  parent_id?: string
  is_active?: boolean
  sort_order?: number
}

export interface UserPermissions {
  user_id: number
  permissions: string[]
  is_super_admin: boolean
  is_org_admin: boolean
}
