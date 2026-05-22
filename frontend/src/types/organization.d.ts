// PioneClaw - 组织类型
export interface Organization {
  id: string
  name: string
  code: string
  description?: string
  parent_id?: string
  level: number
  path: string
  manager_id?: number
  type: string // company/department
  status: string // active/inactive
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface OrganizationTree extends Organization {
  children: OrganizationTree[]
  user_count: number
}

export interface OrganizationSimple {
  id: string
  name: string
  code: string
  level: number
  parent_id?: string
}

export interface OrganizationCreate {
  name: string
  code: string
  description?: string
  type?: string
  parent_id?: string
  manager_id?: number
}

export interface OrganizationUpdate {
  name?: string
  code?: string
  description?: string
  type?: string
  parent_id?: string
  manager_id?: number
  status?: string
  metadata?: Record<string, any>
}
