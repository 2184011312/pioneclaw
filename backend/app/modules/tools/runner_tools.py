"""
Runner Agent 工具 — Agent 调用 Runner 执行文件操作和命令
"""
import asyncio
import uuid
import logging
from app.modules.tools.base import BaseTool, ToolParameter
from app.core.execution_context import current_user_id

logger = logging.getLogger("runner_tools")


async def _find_runner(user_id: int) -> dict | None:
    from app.core.database import async_session_maker
    from app.models import User, Runner, RunnerStatus
    from sqlalchemy import select
    async with async_session_maker() as db:
        user = await db.get(User, user_id)
        if user and user.default_runner_id:
            runner = await db.get(Runner, user.default_runner_id)
            if runner and runner.status in (RunnerStatus.ONLINE, RunnerStatus.APPROVED):
                return {"id": runner.id, "name": runner.name, "host": runner.host}
        result = await db.execute(
            select(Runner).where(
                Runner.user_id == user_id,
                Runner.status.in_([RunnerStatus.ONLINE, RunnerStatus.APPROVED]),
            ).limit(1)
        )
        runner = result.scalar_one_or_none()
        if runner:
            return {"id": runner.id, "name": runner.name, "host": runner.host}
    return None


async def _send_and_wait(runner_id: int, action: str, params: dict, timeout: int = 30) -> str:
    from app.api.runners import _instruction_queues, _instruction_results
    task_id = str(uuid.uuid4())[:8]
    _instruction_queues.setdefault(runner_id, []).append({
        "task_id": task_id, "action": action, "params": params
    })
    for _ in range(timeout * 2):
        await asyncio.sleep(0.5)
        result = _instruction_results.pop(task_id, None)
        if result:
            if result["success"]:
                return str(result.get("data", "(空)"))
            return f"Runner 执行失败: {result.get('error', '未知错误')}"
    return f"执行超时 ({timeout}s)，请确认 Runner 在线"


def _make_execute(action: str):
    async def execute(self, **kwargs) -> str:
        uid = current_user_id.get()
        if not uid:
            return "错误: 无法识别当前用户"
        runner = await _find_runner(uid)
        if not runner:
            return "错误: 你还没有绑定 Runner。请在 Runner 管理页面绑定或安装 Runner 客户端"
        params = {}
        if "path" in kwargs: params["path"] = kwargs["path"]
        if "content" in kwargs: params["content"] = kwargs["content"]
        if "command" in kwargs: params["command"] = kwargs["command"]
        logger.info(f"Runner tool: user={uid}, runner={runner['id']}, action={action}")
        return await _send_and_wait(runner["id"], action, params)
    return execute


class RunnerFileReadTool(BaseTool):
    name = "runner_file_read"
    description = "读取 Runner 机器上的文件。参数 path 为文件路径（必填）"
    parameters = {"path": ToolParameter(type="string", description="文件路径")}
    required = []
    execute = _make_execute("file_read")


class RunnerFileWriteTool(BaseTool):
    name = "runner_file_write"
    description = "向 Runner 机器写入文件。参数 path 为文件路径（必填），content 为内容（必填）"
    parameters = {
        "path": ToolParameter(type="string", description="文件路径"),
        "content": ToolParameter(type="string", description="文件内容"),
    }
    required = []
    execute = _make_execute("file_write")


class RunnerFileBrowseTool(BaseTool):
    name = "runner_file_browse"
    description = "浏览 Runner 机器上的目录。参数 path 为目录路径"
    parameters = {"path": ToolParameter(type="string", description="目录路径")}
    required = []
    execute = _make_execute("file_browse")


class RunnerExecTool(BaseTool):
    name = "runner_exec"
    description = "在 Runner 机器上执行终端命令。参数 command 为命令（必填）"
    parameters = {"command": ToolParameter(type="string", description="要执行的命令")}
    required = []
    execute = _make_execute("exec")
