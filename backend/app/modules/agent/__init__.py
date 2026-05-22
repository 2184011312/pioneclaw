"""
Agent 模块 - Agent 执行引擎

包含：
- AgentLoop: ReAct 推理循环
- WorkflowEngine: 多智能体工作流
- SubagentManager: 子 Agent 管理
- TaskManager: 任务取消令牌和管理
- ContextBuilder: 上下文构建（待实现）
- Handoff: 统一委托机制（借鉴 PraisonAI）
"""

from app.modules.agent.loop import (
    AgentLoop,
    AgentStatus,
    AgentIteration,
    AgentExecutionResult,
    CancelToken,
    ToolCall,
)
from app.modules.agent.handoff import (
    Handoff,
    HandoffConfig,
    HandoffResult,
    ContextPolicy,
    CycleDetectedError,
    HandoffDepthExceededError,
    HandoffTracker,
    handoff_filters,
    parallel_handoffs,
    get_handoff_tracker,
    reset_handoff_tracker,
)
from app.modules.agent.guardrails import (
    Guardrail,
    GuardrailConfig,
    GuardrailExecutor,
    ValidationResult,
    GuardrailFailedError,
    builtin_validators,
)
from app.modules.agent.tool_hooks import (
    HookEvent,
    HookContext,
    HookResult,
    ToolHook,
    ToolHookRunner,
    builtin_hooks,
    hook,
)
from app.modules.agent.injected_state import (
    Injected,
    AgentState,
    InjectedContext,
    StateInjector,
    is_injected_type,
    get_injected_inner_type,
    get_state_injector,
    reset_state_injector,
    injectable,
    with_state,
    mark_injected_in_schema,
)
from app.modules.agent.auto_agents import (
    TaskComplexity,
    AgentRole,
    AgentTemplate,
    DEFAULT_TEMPLATES,
    SubTask,
    TaskDecomposition,
    AutoAgentResult,
    TaskAnalyzer,
    AutoAgents,
    auto_run,
)
from app.modules.agent.interrupt import (
    InterruptManager,
    InterruptPoint,
    InterruptReason,
    InterruptStatus,
    InterruptOption,
    Checkpoint,
    get_interrupt_manager,
    reset_interrupt_manager,
    interrupt_options,
)
from app.modules.agent.tracing import (
    SpanKind,
    SpanStatus,
    Span,
    Trace,
    TokenUsage,
    AgentTracer,
    get_tracer,
    reset_tracer,
    trace_agent,
    trace_tool,
)
from app.modules.agent.workflow import (
    WorkflowEngine,
    WorkflowMode,
    AgentSlot,
    SlotPhase,
)
from app.modules.agent.subagent import (
    SubagentManager,
    SubagentTask,
    TaskStatus,
    TaskType,
    BuiltinAgentType,
    SubagentRole,
    SubagentConfig,
    SubagentLane,
    LaneType,
    SubagentTargetPolicy,
    SubagentAnnouncer,
    resolve_subagent_role,
    resolve_subagent_capabilities,
    SUBAGENT_SYSTEM_PROMPT_TEMPLATE,
)
from app.modules.agent.task_manager import (
    CancellationToken,
    CancellationTokenSource,
    TaskManager,
    TaskState,
    SessionTask,
    get_task_manager,
    create_cancellation_token,
)
from app.modules.agent.personalities import (
    Personality,
    PersonalityCategory,
    get_personality_prompt,
    get_personality_system_prompt,
    get_all_personalities,
    get_all_personality_ids,
    get_personality_info,
    register_custom_personality,
    get_default_personality_id,
)
from app.modules.agent.analyzer import (
    MessageAnalyzer,
    MessageStats,
)
from app.modules.agent.compactor import (
    Compactor,
    CompactionConfig,
    CompactionResult,
    create_compactor,
)
from app.modules.agent.prompts import (
    get_conversation_to_memory_prompt,
    get_recursive_summary_prompt,
    get_short_context_summary_prompt,
    get_overflow_summary_prompt,
    get_heartbeat_greeting_prompt,
    get_cron_task_prompt,
    format_memory_entry,
)
from app.modules.agent.memory import (
    MemoryStore,
    MemoryEntry,
    MemoryStats,
    MemorySource,
    get_memory_store,
    init_memory_store,
)
from app.modules.agent.heartbeat import (
    HeartbeatService,
    HeartbeatConfig,
    HeartbeatDispatch,
    create_heartbeat_service,
    get_default_heartbeat_config,
    HEARTBEAT_JOB_ID,
    HEARTBEAT_MESSAGE,
)
from app.modules.agent.context import (
    ContextBuilder,
    PersonaConfig,
    SessionContext,
    create_context_builder,
    get_default_persona_config,
)
from app.modules.agent.context_files import (
    ContextFileLoader,
    IdentityFile,
    PromptCacheStrategy,
    parse_identity_md,
    merge_identity_content,
    CONTEXT_FILE_ORDER,
    STABLE_FILES,
    DYNAMIC_FILES,
)
from app.modules.agent.skills import (
    SkillsLoader,
    Skill,
    SkillMetadata,
    get_skills_loader,
    init_skills_loader,
    _xml_escape,
)
from app.modules.agent.skills_schema import (
    SkillsSchemaRegistry,
    SkillSchema,
    SchemaField,
    get_schema_registry,
    init_schema_registry,
)
from app.modules.agent.skills_config import (
    SkillsConfigManager,
    ConfigStatus,
    get_config_manager,
    init_config_manager,
)
from app.modules.agent.taskflow import (
    TaskFlowManager,
    RevisionConflictError,
    InvalidStateTransition,
    VALID_TRANSITIONS,
)
from app.modules.agent.memory_extractor import MemoryExtractor
from app.modules.agent.conversation_summarizer import ConversationSummarizer, SummarizerConfig
from app.modules.agent.magic_docs import MagicDocUpdater

__all__ = [
    "AgentLoop",
    "AgentStatus",
    "AgentIteration",
    "AgentExecutionResult",
    "CancelToken",
    "ToolCall",
    # Handoff（借鉴 PraisonAI）
    "Handoff",
    "HandoffConfig",
    "HandoffResult",
    "ContextPolicy",
    "CycleDetectedError",
    "HandoffDepthExceededError",
    "HandoffTracker",
    "handoff_filters",
    "parallel_handoffs",
    "get_handoff_tracker",
    "reset_handoff_tracker",
    # Guardrails（借鉴 CrewAI）
    "Guardrail",
    "GuardrailConfig",
    "GuardrailExecutor",
    "ValidationResult",
    "GuardrailFailedError",
    "builtin_validators",
    # Tool Hooks（借鉴 PraisonAI）
    "HookEvent",
    "HookContext",
    "HookResult",
    "ToolHook",
    "ToolHookRunner",
    "builtin_hooks",
    "hook",
    # Injected State（借鉴 PraisonAI）
    "Injected",
    "AgentState",
    "InjectedContext",
    "StateInjector",
    "is_injected_type",
    "get_injected_inner_type",
    "get_state_injector",
    "reset_state_injector",
    "injectable",
    "with_state",
    "mark_injected_in_schema",
    # AutoAgents（借鉴 PraisonAI）
    "TaskComplexity",
    "AgentRole",
    "AgentTemplate",
    "DEFAULT_TEMPLATES",
    "SubTask",
    "TaskDecomposition",
    "AutoAgentResult",
    "TaskAnalyzer",
    "AutoAgents",
    "auto_run",
    # Interrupt（借鉴 LangGraph）
    "InterruptManager",
    "InterruptPoint",
    "InterruptReason",
    "InterruptStatus",
    "InterruptOption",
    "Checkpoint",
    "get_interrupt_manager",
    "reset_interrupt_manager",
    "interrupt_options",
    # Tracing（借鉴 LangSmith）
    "SpanKind",
    "SpanStatus",
    "Span",
    "Trace",
    "TokenUsage",
    "AgentTracer",
    "get_tracer",
    "reset_tracer",
    "trace_agent",
    "trace_tool",
    "SubTask",
    "TaskDecomposition",
    "AutoAgentResult",
    "TaskAnalyzer",
    "AutoAgents",
    "auto_run",
    # Workflow
    "WorkflowEngine",
    "WorkflowMode",
    "AgentSlot",
    "SlotPhase",
    "SubagentManager",
    "SubagentTask",
    "TaskStatus",
    "TaskType",
    "BuiltinAgentType",
    "SubagentRole",
    "SubagentConfig",
    "SubagentLane",
    "LaneType",
    "SubagentTargetPolicy",
    "SubagentAnnouncer",
    "resolve_subagent_role",
    "resolve_subagent_capabilities",
    "SUBAGENT_SYSTEM_PROMPT_TEMPLATE",
    # TaskManager
    "CancellationToken",
    "CancellationTokenSource",
    "TaskManager",
    "TaskState",
    "SessionTask",
    "get_task_manager",
    "create_cancellation_token",
    # Personalities
    "Personality",
    "PersonalityCategory",
    "get_personality_prompt",
    "get_personality_system_prompt",
    "get_all_personalities",
    "get_all_personality_ids",
    "get_personality_info",
    "register_custom_personality",
    "get_default_personality_id",
    # Analyzer
    "MessageAnalyzer",
    "MessageStats",
    # Compactor
    "Compactor",
    "CompactionConfig",
    "CompactionResult",
    "create_compactor",
    # Prompts
    "get_conversation_to_memory_prompt",
    "get_recursive_summary_prompt",
    "get_short_context_summary_prompt",
    "get_overflow_summary_prompt",
    "get_heartbeat_greeting_prompt",
    "get_cron_task_prompt",
    "format_memory_entry",
    # Memory
    "MemoryStore",
    "MemoryEntry",
    "MemoryStats",
    "MemorySource",
    "get_memory_store",
    "init_memory_store",
    # Heartbeat
    "HeartbeatService",
    "HeartbeatConfig",
    "HeartbeatDispatch",
    "create_heartbeat_service",
    "get_default_heartbeat_config",
    "HEARTBEAT_JOB_ID",
    "HEARTBEAT_MESSAGE",
    # Context
    "ContextBuilder",
    "PersonaConfig",
    "SessionContext",
    "create_context_builder",
    "get_default_persona_config",
    # Context Files (OpenClaw)
    "ContextFileLoader",
    "IdentityFile",
    "PromptCacheStrategy",
    "parse_identity_md",
    "merge_identity_content",
    "CONTEXT_FILE_ORDER",
    "STABLE_FILES",
    "DYNAMIC_FILES",
    # Skills
    "SkillsLoader",
    "Skill",
    "SkillMetadata",
    "get_skills_loader",
    "init_skills_loader",
    "_xml_escape",
    # SkillsSchema
    "SkillsSchemaRegistry",
    "SkillSchema",
    "SchemaField",
    "get_schema_registry",
    "init_schema_registry",
    # SkillsConfig
    "SkillsConfigManager",
    "ConfigStatus",
    "get_config_manager",
    "init_config_manager",
    # TaskFlow
    "TaskFlowManager",
    "RevisionConflictError",
    "InvalidStateTransition",
    "VALID_TRANSITIONS",
    # Stage VV: 持久化记忆增强
    "MemoryExtractor",
    "ConversationSummarizer",
    "SummarizerConfig",
    "MagicDocUpdater",
]
