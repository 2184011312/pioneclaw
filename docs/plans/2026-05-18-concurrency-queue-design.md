# 并发限流 + 排队系统 — 设计方案

> 日期：2026-05-18

## 一、问题

多用户并发对话时，AgentLoop 无限制启动，导致模型 API 被打爆、部分用户得不到回复。

## 二、架构

```
用户请求 → AgentLoop 启动前
    ↓
ConcurrencyManager.acquire(user_id)
    ├─ 配额充足 → 立即执行 → 完成后 release
    └─ 配额不足 → 加入 TaskQueue → 排队等待
                              ↓
                    前面任务完成 → release() 触发下一个
                              ↓
                    通过 WebSocket 通知前端"轮到你"
```

### 核心组件

**ConcurrencyManager** (单例，进程内存)

```python
class ConcurrencyManager:
    max_per_user: int = 3      # 每用户最大并发
    max_global: int = 20       # 全局最大并发
    max_queue_per_user: int = 5 # 每用户最大排队数
    
    _active: dict[str, int]           # user_id → 活跃任务数
    _total_active: int                # 全局活跃数
    _queues: dict[str, asyncio.Queue] # user_id → 等待队列
    
    async def acquire(user_id, task_id) -> AcquireResult:
        # 1. 检查用户并发
        if _active.get(user_id, 0) >= max_per_user:
            # 检查用户排队是否已满
            if queue_size(user_id) >= max_queue_per_user:
                return AcquireResult(rejected=True, reason="排队已满")
            # 加入等待队列
            position = await enqueue(user_id, task_id)
            return AcquireResult(queued=True, position=position)
        
        # 2. 检查全局并发
        if _total_active >= max_global:
            await enqueue(user_id, task_id)
            return AcquireResult(queued=True, position=...)
        
        # 3. 通过
        _active[user_id] = _active.get(user_id, 0) + 1
        _total_active += 1
        return AcquireResult(acquired=True)
    
    def release(user_id):
        _active[user_id] -= 1
        _total_active -= 1
        # 唤醒下一个排队任务
        wake_next()
```

**TaskQueue** (优先级队列)

```python
class TaskQueue:
    # 优先级：短任务优先（用 message 长度估算）
    # 同用户的任务 FIFO
    
    async def enqueue(user_id, task_id, priority=0):
        ...
    
    async def dequeue() -> QueuedTask:
        # 优先取短任务、等待时间长的任务
        ...
    
    def position(user_id, task_id) -> int:
        # 返回当前排队位置
        ...
```

## 三、API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/concurrency/status` | 当前并发状态（活跃数、排队数） |
| GET | `/api/concurrency/my-position` | 当前用户的排队位置 |
| POST | `/api/concurrency/cancel` | 取消排队 |

## 四、AgentLoop 集成

在 `chat.py` 的 `react_chat_stream` 中：

```python
from app.core.concurrency import concurrency_manager

# 在 AgentLoop 启动前
result = await concurrency_manager.acquire(current_user.id, task_id)

if result.rejected:
    yield error("排队已满，请稍后重试")
    return

if result.queued:
    # 通知前端排队
    yield queue_status(position=result.position)
    # 等待唤醒
    await result.wait()
    yield queue_status(position=0, active=True)

try:
    # 正常执行 AgentLoop
    async for chunk in agent_loop.process_message(...):
        yield chunk
finally:
    concurrency_manager.release(current_user.id)
```

## 五、前端改造

Chat.vue 发送消息时：
1. 请求正常 → 当前不在排队 → 直接对话
2. 收到 `queued` 事件 → 显示"排队中，前面还有 N 个任务，预计等待 X 秒"
3. 收到 `rejected` → 显示"当前排队人数过多，请稍后再试"

通过 SSE 流推送排队状态更新。

## 六、配置项（可调）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MAX_CONCURRENT_PER_USER` | 3 | 每用户最大并发 |
| `MAX_CONCURRENT_GLOBAL` | 20 | 全局最大并发 |
| `MAX_QUEUE_PER_USER` | 5 | 每用户最多排队任务 |
| `QUEUE_TIMEOUT_SECONDS` | 120 | 排队超时（超时自动取消） |
| `PRIORITY_BOOST_SMALL_TASK` | true | 短消息（<100字）优先 |

## 七、文件清单

| 操作 | 文件 |
|------|------|
| 新建 | `backend/app/core/concurrency.py` — ConcurrencyManager |
| 修改 | `backend/app/api/chat.py` — 集成 acquire/release |
| 新建 | `backend/app/api/concurrency_status.py` — 状态 API |
| 修改 | `frontend/src/views/Chat.vue` — 排队 UI |

## 八、估时

~2h
