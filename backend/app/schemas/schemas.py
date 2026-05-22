from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.models import UserRole, AgentStatus


# ==================== User Schemas ====================
class UserBase(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_一-鿿]+$',
        description="用户名，3-50位，支持字母/数字/下划线/中文",
    )
    email: EmailStr
    display_name: Optional[str] = Field(default=None, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=8, description="密码，至少8位")


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str  # 改为 str 类型，避免 EmailStr 严格验证导致已有数据无法返回
    display_name: Optional[str] = None
    role: UserRole
    is_active: bool
    avatar: Optional[str] = None
    organization_id: Optional[str] = None
    is_super_admin: bool = False
    is_org_admin: bool = False
    permissions: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str
    ip: Optional[str] = None  # 可选，记录登录 IP


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    avatar: Optional[str] = Field(default=None, max_length=200000)
    phone: Optional[str] = Field(default=None, max_length=20, pattern=r'^[\d\-\+\(\)\s]*$')
    department: Optional[str] = Field(default=None, max_length=100)
    position: Optional[str] = Field(default=None, max_length=100)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int
    exp: datetime


# ==================== Agent Schemas ====================
class AgentBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    model: str = "gpt-4o"
    max_turns: int = 20
    system_prompt: Optional[str] = None


class AgentCreate(AgentBase):
    skill_ids: List[int] = []


class AgentUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    max_turns: Optional[int] = None
    system_prompt: Optional[str] = None
    status: Optional[AgentStatus] = None
    skill_ids: Optional[List[int]] = None


class AgentResponse(AgentBase):
    id: int
    status: AgentStatus
    creator_id: int
    created_at: datetime
    updated_at: datetime
    skills: List["SkillBrief"] = []

    class Config:
        from_attributes = True


class AgentBrief(BaseModel):
    id: int
    name: str
    display_name: str
    status: AgentStatus

    class Config:
        from_attributes = True


# ==================== Skill Schemas ====================
class SkillBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    category: str = "custom"
    scope: str = "user"


class SkillCreate(SkillBase):
    content: Optional[str] = None
    is_public: bool = True
    always_activate: bool = False
    skill_format: str = "inline"
    dependencies: Optional[dict] = None


class SkillUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    always_activate: Optional[bool] = None
    skill_format: Optional[str] = None
    dependencies: Optional[dict] = None
    scope: Optional[str] = None


class SkillResponse(SkillBase):
    id: Optional[int] = None
    source: str = "db"  # "db" | "file"
    content: Optional[str] = None
    package_type: str = "inline"
    package_size: int = 0
    always_activate: bool = False
    skill_format: str = "inline"
    tags: Optional[list] = None
    dependencies: Optional[dict] = None
    is_active: bool = True
    is_public: bool = True
    creator_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SkillBrief(BaseModel):
    id: int
    name: str
    display_name: str
    category: str
    always_activate: bool = False

    class Config:
        from_attributes = True


# ==================== Dashboard Schemas ====================
class DashboardStats(BaseModel):
    total_calls: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    avg_duration_ms: float
    failed_calls: int
    model_distribution: dict
    hourly_calls: list = []


class UsageStats(BaseModel):
    date: str
    calls: int
    tokens: int


# ==================== Runner Schemas ====================
from app.models.models import RunnerStatus


class RunnerBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None


class RunnerCreate(RunnerBase):
    api_key: Optional[str] = None
    capabilities: Optional[dict] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    user_token: Optional[str] = None  # Runner 端携带的用户 JWT，用于自动关联用户


class RunnerUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    status: Optional[RunnerStatus] = None
    user_id: Optional[int] = None


class RunnerResponse(RunnerBase):
    id: int
    status: RunnerStatus
    api_key: Optional[str] = None
    capabilities: Optional[dict]
    version: Optional[str]
    platform: Optional[str]
    last_heartbeat: Optional[datetime]
    current_task: Optional[str]
    total_tasks: int
    success_tasks: int
    failed_tasks: int
    applied_at: datetime
    approved_at: Optional[datetime]
    approved_by: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    reject_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    @field_validator("api_key", mode="before")
    @classmethod
    def mask_api_key(cls, v):
        if v and str(v).strip():
            return "••••••••"
        return None

    class Config:
        from_attributes = True


class RunnerApprove(BaseModel):
    approve: bool
    user_id: Optional[int] = None
    reject_reason: Optional[str] = None


class RunnerHeartbeat(BaseModel):
    current_task: Optional[str] = None
    capabilities: Optional[dict] = None


# ==================== AI Model Config Schemas ====================
class AIModelConfigBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    provider: str = "openai"
    model_name: str
    base_url: str
    tier: str = "sonnet"  # opus/sonnet/haiku/custom
    context_window: int = 128000
    max_tokens: int = 4096
    temperature: float = 0.7


class AIModelConfigCreate(AIModelConfigBase):
    api_key: str  # 必填
    is_default: bool = False
    extra_config: Optional[dict] = None


class AIModelConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    extra_config: Optional[dict] = None


class AIModelConfigResponse(AIModelConfigBase):
    id: int
    api_key: Optional[str] = None
    is_default: bool
    is_active: bool
    tier: str
    extra_config: Optional[dict]
    created_at: datetime
    updated_at: datetime

    @field_validator("api_key", mode="before")
    @classmethod
    def mask_api_key(cls, v):
        if v and str(v).strip():
            return "••••••••"
        return None

    class Config:
        from_attributes = True


class AIModelTestRequest(BaseModel):
    model_config_id: Optional[int] = None
    # 或者直接传入配置测试
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    test_prompt: str = "Hello, are you working?"


class AIModelTestResponse(BaseModel):
    success: bool
    message: str
    response: Optional[str] = None
    latency_ms: Optional[int] = None


# ==================== Knowledge Base Schemas ====================
class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeDocumentBase(BaseModel):
    title: str
    content: str
    source: Optional[str] = None


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    knowledge_base_id: int


class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    id: int
    knowledge_base_id: int
    doc_type: str
    file_path: Optional[str]
    file_size: Optional[int]
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    is_active: bool
    document_count: int = 0
    total_chunks: int = 0
    created_at: datetime
    updated_at: datetime
    documents: List[KnowledgeDocumentResponse] = []

    class Config:
        from_attributes = True


# ==================== Role Schemas ====================
class RoleBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permissions: Optional[dict] = None
    is_active: bool = True


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[dict] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    id: int
    permissions: Optional[dict]
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Task Schemas ====================
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "normal"
    task_type: str = "manual"
    parent_id: Optional[int] = None
    agent_id: Optional[int] = None
    assignee_id: Optional[int] = None
    due_at: Optional[datetime] = None
    input_data: Optional[dict] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    due_at: Optional[datetime] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    status: str
    parent_id: Optional[int] = None
    runner_id: Optional[int]
    creator_id: int
    input_data: Optional[dict]
    output_data: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Cron Schemas ====================
class CronJobBase(BaseModel):
    name: str
    cron_expr: str
    agent_id: Optional[int] = None
    input_data: Optional[dict] = None
    description: Optional[str] = None


class CronJobCreate(CronJobBase):
    is_active: bool = True


class CronJobUpdate(BaseModel):
    name: Optional[str] = None
    cron_expr: Optional[str] = None
    agent_id: Optional[int] = None
    input_data: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CronJobResponse(CronJobBase):
    id: int
    is_active: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    created_at: datetime
    updated_at: datetime


class CronExecutionLogResponse(BaseModel):
    """Cron 任务执行日志响应"""
    id: int
    cron_job_id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    result: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True


# ==================== MCP Schemas ====================
class MCPServerConfigCreate(BaseModel):
    name: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    auth_config: Optional[dict] = None
    is_enabled: bool = True


class MCPServerConfigUpdate(BaseModel):
    name: Optional[str] = None
    transport: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    auth_config: Optional[dict] = None
    is_enabled: Optional[bool] = None


class MCPServerConfigResponse(BaseModel):
    id: int
    name: str
    transport: str
    command: Optional[str] = None
    args: Optional[list] = None
    env: Optional[dict] = None
    url: Optional[str] = None
    auth_config: Optional[dict] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MCPConnectionStatus(BaseModel):
    server: str
    status: str
    tool_count: int = 0
    resource_count: int = 0
    server_info: Optional[dict] = None
    error_message: Optional[str] = None


# ==================== Common Schemas ====================
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# 更新 forward references
AgentResponse.model_rebuild()
