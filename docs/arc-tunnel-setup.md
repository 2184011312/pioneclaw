# Arc Tunnel 浏览器自动化（可选）

Arc Tunnel 让 PioneClaw 能够控制你的真实浏览器，执行导航、点击、输入、截图等操作。

## 架构

```
PioneClaw Backend ──stdio──► Arc Tunnel MCP Server ──WebSocket──► Chrome/Edge Extension
                                                                    │
                                                              chrome.debugger API
                                                                    │
                                                              Browser Tabs
```

- **MCP Server**: Node.js 进程，提供 15 个浏览器自动化工具
- **Browser Extension**: Chrome/Edge 扩展，通过 CDP 控制浏览器
- **通信**: stdio (MCP) + WebSocket (localhost:8765)

## 快速开始

### 1. 启用配置

在 `backend/.env` 中添加：

```bash
ARC_TUNNEL_ENABLED=true
```

或在启动时设置环境变量：

```bash
# Windows
set ARC_TUNNEL_ENABLED=true

# macOS / Linux
export ARC_TUNNEL_ENABLED=true
```

### 2. 安装浏览器扩展

**方式一：加载已解压的扩展（开发/测试）**

1. 打开 Chrome 或 Edge，地址栏输入 `chrome://extensions/` 或 `edge://extensions/`
2. 启用右上角「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `external/arc-tunnel/extension/dist` 目录

**方式二：打包安装（分发）**

```bash
cd external/arc-tunnel/extension
npm install        # 首次需要
npm run build      # 构建扩展
```

构建产物在 `extension/dist/` 目录，已预构建可直接使用。

### 3. 启动 PioneClaw

```bash
cd backend
uv run uvicorn app.main:app --reload
```

启动日志中会显示：

```
[MCP] 内置 arc-tunnel 已连接: 15 工具
```

### 4. 验证连接

1. 点击浏览器扩展图标
2. 弹窗应显示 **"Status: Connected"**
3. 如果 MCP Server 运行在非默认端口，可在扩展弹窗中修改 MCP Server URL

## 可用工具

arc-tunnel 注册后，工具以 `mcp__arc-tunnel__{tool}` 命名空间暴露：

| 工具 | 功能 |
|------|------|
| `mcp__arc-tunnel__snapshot` | 返回页面可交互元素 ref 列表 |
| `mcp__arc-tunnel__interact` | click, type, press, hover 等 |
| `mcp__arc-tunnel__navigate` | goto, back, forward, reload |
| `mcp__arc-tunnel__screenshot` | 页面截图 |
| `mcp__arc-tunnel__create_tab` | 创建新标签页 |
| `mcp__arc-tunnel__list_tabs` | 列出所有标签页 |
| `mcp__arc-tunnel__execute_script` | 在页面执行 JavaScript |
| `mcp__arc-tunnel__manage_storage` | cookies / localStorage / sessionStorage |
| `mcp__arc-tunnel__start_recording` | 开始录制用户操作 |
| `mcp__arc-tunnel__stop_recording` | 停止录制 |
| `mcp__arc-tunnel__replay_recording` | 回放录制 |
| `mcp__arc-tunnel__save_session` | 保存浏览器会话 |
| `mcp__arc-tunnel__restore_session` | 恢复浏览器会话 |

## 手动启动 MCP Server（调试）

如果 PioneClaw 没有自动启动，可以手动运行：

```bash
node external/arc-tunnel/mcp-server/dist/mcp-server.js
# 或指定端口
node external/arc-tunnel/mcp-server/dist/mcp-server.js --port 9876
```

## 故障排查

| 问题 | 解决方法 |
|------|---------|
| "arc-tunnel 未找到" | 检查 `external/arc-tunnel/` 目录是否存在 |
| "node 不可用" | 安装 Node.js 18+ |
| 扩展显示 "Disconnected" | 检查 MCP Server 是否运行，端口是否一致 |
| 工具未出现在列表中 | 确认 `ARC_TUNNEL_ENABLED=true` 已设置 |

## 禁用

将 `.env` 中的 `ARC_TUNNEL_ENABLED` 设为 `false` 或删除该行，重启 PioneClaw 即可。
