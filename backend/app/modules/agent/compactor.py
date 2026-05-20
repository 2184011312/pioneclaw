"""
Compactor - 对话压缩和上下文管理

借鉴自 CountBot 的 prompts.py 和 AIE 的 analyzer.py，实现：
1. 对话历史压缩（递归总结）
2. Token 计数和阈值判断
3. 消息分割和保留策略
4. 记忆条目生成
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== 提示词模板 ====================

# 对话总结 → 记忆条目提示词
CONVERSATION_TO_MEMORY_PROMPT = """你是一个对话总结器。将下面的对话总结为简洁的记忆条目。

要求:
1. 输出格式: 一行文本，多个事项用中文分号（；）分隔
2. 只记录有长期价值的事实信息:
   - 用户明确表达的偏好和习惯
   - 重要决策和结论
   - 项目配置和技术细节
   - 用户要求记住的内容
3. 不要记录:
   - 寒暄、确认、重复内容
   - 一次性查询结果（天气、新闻、搜索结果）
   - 工具执行的中间过程
   - 闲聊和测试内容
4. 每个事项必须包含具体信息（名称、数字、时间、地点等）
5. 如果对话没有值得长期记录的信息，输出: 无需记录

对话内容:
{messages}

输出（一行，事项用；分隔）:"""


# 递归总结提示词（用于更新已有总结）
RECURSIVE_SUMMARY_PROMPT = """你是一个对话总结器。将新的对话内容合并到已有总结中。

已有总结:
{previous_summary}

新对话:
{past_messages}

要求:
1. 合并新信息到已有总结
2. 去除过时或重复的内容
3. 保持简洁，不超过 {char_limit} 字符
4. 输出纯文本，不要 markdown 格式

更新后的总结:"""


# 短上下文压缩提示词
SHORT_CONTEXT_SUMMARY_PROMPT = """你是一个对话压缩器。将以下对话历史压缩成一个结构化的简洁摘要。

按以下 9 个部分组织输出：

### 1. 当前任务
用户的核心目标和当前正在进行的工作

### 2. 已完成
已经完成的关键步骤和成果

### 3. 待办
尚未完成的任务和下一步计划

### 4. 关键决策
已做出的重要决策及其原因

### 5. 技术细节
关键文件路径、代码片段、配置参数

### 6. 错误与修复
遇到的错误及其解决方案

### 7. 用户偏好
用户表达的习惯、偏好、风格要求

### 8. 开放问题
尚未解决或需要进一步确认的问题

### 9. 上下文
其他对后续对话重要的背景信息

要求：
- 保留用户原始消息的完整内容（不压缩用户消息）
- 不编造未出现的信息
- 某部分若无内容则写"无"
- 不超过 {char_limit} 字符

对话内容:
{messages}

简洁摘要:"""


# 递归短上下文总结提示词
RECURSIVE_SHORT_CONTEXT_SUMMARY_PROMPT = """你是一个对话压缩器。将新对话合并到已有的短摘要中，生成新的短摘要。

旧摘要:
{previous_summary}

新对话:
{past_messages}

要求:
1. 保留当前主题、关键决策、未解决问题
2. 删除过时、重复、无关信息
3. 输出纯文本，不要 markdown 格式
4. 不超过 {char_limit} 字符

更新后的短摘要:"""


# 溢出总结提示词
OVERFLOW_SUMMARY_PROMPT = """你是一个对话总结器。在即将截断旧的对话历史前，将其中有长期价值的信息总结为记忆条目。

要求:
1. 输出格式: 一行文本，多个事项用中文分号（；）分隔
2. 只记录有长期价值的事实信息:
   - 用户明确表达的偏好和习惯
   - 重要决策和结论
   - 项目配置和技术细节
   - 或者涉及的重要关键信息（如时间查询）
3. 不要记录:
   - 寒暄、确认、重复内容
   - 一次性查询结果
   - 工具执行的中间过程
4. 每个事项必须包含具体信息
5. 如果没有值得记录的信息，输出: 无需记录

对话内容:
{messages}

输出（一行，事项用；分隔）:"""


# ==================== 数据类 ====================

@dataclass
class CompactionResult:
    """压缩结果"""
    summary: str  # 压缩后的摘要
    removed_messages: int  # 移除的消息数
    kept_messages: int  # 保留的消息数
    saved_tokens: int  # 节省的 Token 数
    memory_entries: List[str] = field(default_factory=list)  # 生成的记忆条目


@dataclass
class CompactionConfig:
    """压缩配置"""
    # 消息数量阈值
    message_threshold: int = 30

    # Token 数阈值
    token_threshold: int = 5000

    # 保留最近消息数
    keep_recent_messages: int = 8

    # 摘要最大字符数
    max_summary_chars: int = 3000
    
    # 是否生成记忆条目
    generate_memory: bool = True
    
    # 是否使用递归总结
    use_recursive_summary: bool = True


# ==================== Compactor 类 ====================

class Compactor:
    """
    对话压缩器
    
    功能：
    1. 检测是否需要压缩
    2. 分割消息（总结 vs 保留）
    3. 生成摘要
    4. 提取记忆条目
    """
    
    def __init__(
        self,
        config: Optional[CompactionConfig] = None,
        llm_client=None,  # LLM 客户端（用于生成摘要）
        memory_orchestrator=None,  # LayeredMemory MemoryOrchestrator（写入 L1）
        user_id: int = 1,  # 用户 ID（写入记忆时使用）
        session_id: Optional[str] = None,  # 会话 ID
        agent_id: Optional[int] = None,  # Agent ID
    ):
        self.config = config or CompactionConfig()
        self.llm_client = llm_client
        self.memory_orchestrator = memory_orchestrator
        self.user_id = user_id
        self.session_id = session_id
        self.agent_id = agent_id

        # 当前摘要（递归总结用）
        self._current_summary: Optional[str] = None
    
    def should_compact(
        self,
        messages: List[dict],
        token_count: Optional[int] = None,
    ) -> bool:
        """
        判断是否需要压缩
        
        Args:
            messages: 消息列表
            token_count: Token 数（可选，不传则估算）
            
        Returns:
            bool: 是否需要压缩
        """
        if len(messages) > self.config.message_threshold:
            return True
        
        if token_count is None:
            token_count = self._estimate_tokens(messages)
        
        if token_count > self.config.token_threshold:
            return True
        
        return False
    
    async def compact(
        self,
        messages: List[dict],
        existing_summary: Optional[str] = None,
    ) -> CompactionResult:
        """
        压缩对话历史
        
        Args:
            messages: 消息列表
            existing_summary: 已有的摘要（用于递归总结）
            
        Returns:
            CompactionResult: 压缩结果
        """
        if not self.should_compact(messages):
            return CompactionResult(
                summary="",
                removed_messages=0,
                kept_messages=len(messages),
                saved_tokens=0,
            )
        
        # 分割消息
        to_summarize, to_keep = self._split_messages(messages)
        
        if not to_summarize:
            return CompactionResult(
                summary="",
                removed_messages=0,
                kept_messages=len(messages),
                saved_tokens=0,
            )
        
        # 估算节省的 Token
        saved_tokens = self._estimate_tokens(to_summarize)
        
        # 生成摘要
        summary = await self._generate_summary(
            to_summarize,
            existing_summary or self._current_summary,
        )
        
        # 更新当前摘要
        self._current_summary = summary
        
        # 生成记忆条目
        memory_entries = []
        if self.config.generate_memory:
            memory_entries = await self._generate_memory_entries(to_summarize)

            # 将记忆条目写入 L1（如果 MemoryOrchestrator 可用）
            if self.memory_orchestrator and memory_entries:
                await self._write_memories_to_l1(memory_entries)

        return CompactionResult(
            summary=summary,
            removed_messages=len(to_summarize),
            kept_messages=len(to_keep),
            saved_tokens=saved_tokens,
            memory_entries=memory_entries,
        )
    
    def _split_messages(
        self,
        messages: List[dict],
    ) -> Tuple[List[dict], List[dict]]:
        """分割消息：要总结的和要保留的"""
        keep_recent = self.config.keep_recent_messages
        
        if len(messages) <= keep_recent:
            return [], messages
        
        to_summarize = messages[:-keep_recent]
        to_keep = messages[-keep_recent:]
        
        return to_summarize, to_keep
    
    async def _generate_summary(
        self,
        messages: List[dict],
        existing_summary: Optional[str] = None,
    ) -> str:
        """生成摘要"""
        if not self.llm_client:
            # 无 LLM 客户端，返回简单统计
            return self._generate_simple_summary(messages)
        
        # 格式化消息
        formatted_messages = self._format_messages(messages)
        
        try:
            if existing_summary and self.config.use_recursive_summary:
                # 递归总结
                prompt = RECURSIVE_SHORT_CONTEXT_SUMMARY_PROMPT.format(
                    previous_summary=existing_summary,
                    past_messages=formatted_messages,
                    char_limit=self.config.max_summary_chars,
                )
            else:
                # 首次总结
                prompt = SHORT_CONTEXT_SUMMARY_PROMPT.format(
                    messages=formatted_messages,
                    char_limit=self.config.max_summary_chars,
                )
            
            # 调用 LLM
            response = await self._call_llm(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return self._generate_simple_summary(messages)
    
    async def _generate_memory_entries(
        self,
        messages: List[dict],
    ) -> List[str]:
        """生成记忆条目（使用 CONVERSATION_TO_MEMORY_PROMPT）"""
        if not self.llm_client:
            return []

        formatted_messages = self._format_messages(messages)

        try:
            # 使用更完整的对话→记忆提示词
            prompt = CONVERSATION_TO_MEMORY_PROMPT.format(messages=formatted_messages)
            response = await self._call_llm(prompt)

            if "无需记录" in response:
                return []

            # 按分号分割
            entries = [e.strip() for e in response.split("；") if e.strip()]
            return entries

        except Exception as e:
            logger.error(f"Failed to generate memory entries: {e}")
            return []

    async def _write_memories_to_l1(self, entries: List[str]) -> None:
        """将记忆条目写入 L1 会话记忆（通过 MemoryOrchestrator）"""
        try:
            for entry in entries:
                await self.memory_orchestrator.store(
                    content=entry,
                    name=f"压缩记忆_{datetime.now().strftime('%H%M%S')}",
                    user_id=self.user_id,
                    session_id=self.session_id,
                    agent_id=self.agent_id,
                    context_type="memory",
                    source="compactor",
                    importance=2,
                )
            logger.info(f"Wrote {len(entries)} memory entries to L1 via MemoryOrchestrator")
        except Exception as e:
            logger.warning(f"Failed to write memories to L1: {e}")

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if not self.llm_client:
            return ""
        
        # 这里需要根据实际的 LLM 客户端接口调整
        # 假设 llm_client 有 chat 方法
        try:
            if hasattr(self.llm_client, 'chat'):
                response = await self.llm_client.chat([{"role": "user", "content": prompt}])
                return response.get("content", "")
            elif hasattr(self.llm_client, 'complete'):
                response = await self.llm_client.complete(prompt)
                return response
            else:
                return ""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""
    
    def _format_messages(self, messages: List[dict]) -> str:
        """格式化消息为文本"""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            
            content = str(content).strip()
            if len(content) > 500:
                content = content[:500] + "..."
            
            role_label = {
                "user": "用户",
                "assistant": "助手",
                "system": "系统",
                "tool": "工具",
            }.get(role, role)
            
            lines.append(f"[{role_label}]: {content}")
        
        return "\n".join(lines)
    
    def _generate_simple_summary(self, messages: List[dict]) -> str:
        """生成简单统计摘要（无 LLM 时使用）"""
        user_msgs = sum(1 for m in messages if m.get("role") == "user")
        assistant_msgs = sum(1 for m in messages if m.get("role") == "assistant")
        
        return (
            f"[历史对话摘要] 共 {len(messages)} 条消息 "
            f"(用户: {user_msgs}, 助手: {assistant_msgs})。"
            f"已压缩 {len(messages)} 条历史消息以节省上下文空间。"
        )
    
    def _estimate_tokens(self, messages: List[dict]) -> int:
        """估算 Token 数"""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            # 简单估算：中文 1.5 字符/token，英文 4 字符/token
            import re
            chinese = len(re.findall(r'[\u4e00-\u9fff]', str(content)))
            english = len(str(content)) - chinese
            total += int(chinese / 1.5 + english / 4) + 4
        return total
    
    @property
    def current_summary(self) -> Optional[str]:
        """获取当前摘要"""
        return self._current_summary
    
    def reset_summary(self) -> None:
        """重置摘要"""
        self._current_summary = None


# ==================== 便捷函数 ====================

def create_compactor(
    message_threshold: int = 50,
    token_threshold: int = 8000,
    keep_recent: int = 10,
    llm_client=None,
    user_id: int = 1,
    session_id: Optional[str] = None,
    agent_id: Optional[int] = None,
) -> Compactor:
    """创建 Compactor 实例"""
    config = CompactionConfig(
        message_threshold=message_threshold,
        token_threshold=token_threshold,
        keep_recent_messages=keep_recent,
    )
    return Compactor(
        config=config, llm_client=llm_client,
        user_id=user_id, session_id=session_id, agent_id=agent_id,
    )
