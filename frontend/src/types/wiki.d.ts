// PioneClaw - Wiki 类型
export interface Wiki {
  id: string
  title: string
  content: string
  path: string
  parent_id?: string
  tags?: string[]
  created_by: number
  organization_id?: string
  version: number
  status: string // draft/published/archived
  scope: string // system/org/user
  doc_type?: string // markdown/text/pdf/url
  source?: string
  chunk_count?: number
  is_indexed?: boolean
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface WikiDetail extends Wiki {
  author_name?: string
  organization_name?: string
}

export interface WikiTree extends Wiki {
  children: WikiTree[]
}

export interface WikiVersion {
  id: string
  wiki_id: string
  version: number
  title: string
  content: string
  change_summary?: string
  created_by: number
  created_at: string
  author_name?: string
}

export interface WikiCreate {
  title: string
  content?: string
  path: string
  parent_id?: string
  tags?: string[]
  organization_id?: string | null
  status?: string
  scope?: string
  doc_type?: string
  source?: string | null
}

export interface WikiUpdate {
  title?: string
  content?: string
  path?: string
  parent_id?: string
  tags?: string[]
  status?: string
  scope?: string
  change_summary?: string
  doc_type?: string
  source?: string | null
}

export interface WikiImport {
  path: string
  title?: string
  content: string
  tags?: string[]
  doc_type?: string
  source?: string
  scope?: string
}

export interface WikiSearchResult {
  id: string
  title: string
  path: string
  highlight?: string
  score?: number
}
