# Runner Agent 客户端 — 开发设计

> 日期：2026-05-18

## 一、定位

一个后台守护进程 exe，装在员工电脑上，连接 Center 等待指令执行。

```
用户电脑                    Center 服务器
┌─────────────┐            ┌──────────────┐
│ Runner.exe  │──HTTP─────→│ 注册/心跳     │
│ (后台运行)   │←─WebSocket─│ 下发指令      │
│             │──WS结果───→│ 回报结果      │
│ 执行文件操作 │            │              │
│ 执行终端命令 │            │              │
└─────────────┘            └──────────────┘
```

## 二、技术选型

**Python + PyInstaller**（复用 PioneClaw 代码）

| 语言 | 优点 | 缺点 |
|------|------|------|
| Python | 复用现有模型/Schema/加密；快速开发 | exe 较大 (~50MB) |
| Go | 单文件小 (~10MB)、快 | 重写所有对接逻辑 |

选 Python——开发效率优先，exe 大小可接受。

## 三、目录结构

```
D:\pioneclaw-runner\          # 独立项目
├── main.py                  # 入口
├── runner.py                # Runner 核心类
├── center_client.py         # Center 通信（HTTP+WS）
├── executor.py              # 文件操作 + 命令执行
├── config.py                # 配置管理
├── requirements.txt
└── build.bat                # PyInstaller 打包脚本
```

## 四、核心类设计

### RunnerAgent

```python
class RunnerAgent:
    """Runner 主控"""
    
    async def start():
        # 1. 读取配置（center_url, 本地端口）
        # 2. 如果有持久化 token，尝试恢复
        # 3. 首次运行 → 弹登录窗口
        # 4. 注册到 Center (POST /runners/apply)
        # 5. 建立 WebSocket 长连接
        # 6. 启动心跳循环（每 30s，含诊断数据）
        # 7. 等待 Center 指令
    
    async def heartbeat_loop():
        # 每 30s: POST /runners/{id}/heartbeat
        # body: {current_task, capabilities, diagnostics}
        # diagnostics: {cpu_percent, memory_percent, disk_percent, processes}
    
    async def handle_instruction(msg):
        # 收到 Center 下发的指令 → dispatch 到 executor
```

### CenterClient

```python
class CenterClient:
    """Center 通信层"""
    
    def __init__(center_url: str):
        self.http_base = center_url      # http://192.168.1.x:20005
        self.ws_url = f"ws://{host}:{port}/api/ws/runner"
    
    async def register(name, host, token):
        # POST /api/runners/apply
        # body: {name, display_name, host, port, platform, version, user_token}
    
    async def heartbeat(runner_id, data):
        # POST /api/runners/{id}/heartbeat
    
    async def connect_ws(runner_id):
        # WebSocket 连接 → 接收 Center 指令
    
    def send_result(task_id, result):
        # 通过 WebSocket 回传执行结果
```

### Executor

```python
class Executor:
    """本地执行器——接收指令、执行、返回结果"""
    
    SANDBOX_ROOT = None  # 限制操作范围，防止 Runner 操作敏感路径
    
    async def execute(instruction: dict) -> dict:
        """
        instruction = {
            "type": "file_read" | "file_write" | "file_delete" | "exec" | "browse",
            "path": "...",
            "content": "...",  # for write
            "command": "...",  # for exec
        }
        """
    
    # 文件操作
    async def file_read(path) -> str
    async def file_write(path, content)
    async def file_delete(path)
    async def file_browse(path) -> list
    
    # 命令执行
    async def exec_command(cmd, cwd, timeout=60) -> dict
```

## 五、通信协议

### HTTP（注册、心跳）

```
POST /api/runners/apply
→ {name, display_name, host, port, platform, version, user_token}
← {id, status: "pending"}

POST /api/runners/{id}/heartbeat  
→ {current_task, capabilities, diagnostics}
← {message: "心跳更新成功"}
```

### WebSocket（指令通道）

```
Center → Runner（指令下发）:
{
  "type": "instruction",
  "task_id": "abc123",
  "action": "file_read",
  "params": {"path": "C:\\Users\\xxx\\Desktop\\file.txt"}
}

Runner → Center（结果回报）:
{
  "type": "result",
  "task_id": "abc123",
  "success": true,
  "data": "file content here..."
}
```

## 六、安全设计

| 层级 | 措施 |
|------|------|
| **路径沙箱** | 默认限制在用户目录，禁止访问系统目录 |
| **命令白名单** | 高危命令 (rm -rf / format) 硬拦截 |
| **Token 加密** | api_key 用 Fernet 存储 |
| **首次登录** | 弹窗输入 Center 地址 + 账号密码 → 获取 JWT |
| **连接中断** | 自动重连（指数退避），断连期间缓存心跳 |

## 七、安装包

**PyInstaller 打包**:
```bat
pyinstaller --onefile --name PioneClaw-Runner --icon icon.ico main.py
```

**安装流程**:
1. 下载 exe（从 Center 版本管理页面）
2. 双击运行 → 系统托盘图标
3. 首次启动 → 弹窗输入 Center 地址 + 账号密码
4. 登录成功 → 注册 Runner → 等待审批
5. 托盘菜单：查看状态 / 退出

## 八、Center 端配套改动

| 改动 | 说明 |
|------|------|
| WebSocket `/api/ws/runner` | Runner 专用 WS 通道（已有 ws 模块，需扩展） |
| Runner 指令下发 API | Center 端 Agent 调用 → WS 发指令给 Runner |
| 诊断数据存储 | 心跳中的 diagnostics 写入 Runner.diagnostics JSON |
| 前端下载按钮 | 版本管理 Tab 增加下载链接 |

## 九、开发阶段

| 阶段 | 内容 | 估时 |
|------|------|------|
| **P1** | RunnerAgent 框架 + HTTP 注册/心跳 | 3h |
| **P2** | Executor 文件操作 + 命令执行 | 2h |
| **P3** | WebSocket 双向通信 | 2h |
| **P4** | PyInstaller 打包 + 安装体验 | 1h |
| **总估时** | | ~1 天 |
