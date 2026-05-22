# 上下文余量指示器（Context Ring）

本文档描述 PioneClaw 聊天界面中**圆形上下文余量指示器**的设计与实现。该组件将上下文压缩功能从分散的按钮+进度条整合为一个始终可见的圆环控件，放置在对话框左下角，兼具状态展示与操作入口的双重职责。

---

## 1. 设计动机

### 1.1 旧方案的问题

改造前的上下文压缩功能分散在两处：

| 位置 | 元素 | 问题 |
|------|------|------|
| 右上角 header | "压缩"按钮 (`Collection` 图标) | 远离用户视线焦点，使用频率低 |
| 输入区上方 | 横向进度条 + "立即压缩"按钮 | 仅在高使用率时显示，用户无法预判余量 |

**核心痛点**：
- 用户不知道当前会话已经消耗了多少上下文空间
- 压缩入口隐蔽，发现成本高
- 进度条突然出现会造成"惊吓式"提醒

### 1.2 新方案的目标

- **始终可见**：用户随时扫一眼即可了解上下文余量
- **极简占位**：28px 圆环不占用输入区域空间
- **渐进式警示**：颜色随使用率平滑过渡，低使用率时不打扰
- **一键直达**：点击即触发压缩流程，无需寻找按钮

---

## 2. 组件结构

### 2.1 布局位置

```
┌─────────────────────────────────────────────┐
│                                             │
│              消息列表区域                    │
│                                             │
├─────────────────────────────────────────────┤
│ [◯] 📎 [停止]                  [发送]      │  ← footer-left
│         ↑                                   │
│    Context Ring (28px)                      │
└─────────────────────────────────────────────┘
```

圆环位于 `.input-footer .footer-left`，在 Paperclip（上传文件）按钮的左侧。

### 2.2 SVG 实现

不使用第三方图表库，采用原生 SVG `<circle>` 实现，两个同心圆叠加：

```svg
<svg viewBox="0 0 32 32" width="28" height="28">
  <!-- 底环：灰色背景轨道 -->
  <circle class="context-ring__track"
          cx="16" cy="16" r="13"
          fill="none" stroke-width="2.5" />
  <!-- 进度环：彩色进度指示 -->
  <circle class="context-ring__progress"
          cx="16" cy="16" r="13"
          fill="none" stroke-width="2.5"
          stroke-linecap="round"
          :stroke="color"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset" />
</svg>
```

**数学原理**：
- 半径 `r = 13`，周长 `C = 2πr ≈ 81.68`
- 进度通过 `stroke-dashoffset` 控制：`offset = C - (percent / 100) * C`
- SVG 整体旋转 `-90deg`，使进度从顶部开始顺时针增长

### 2.3 元素拆解

| 元素 | 实现 | 说明 |
|------|------|------|
| 圆环主体 | SVG 双 `circle` | 底环 `#dcdfe6`，进度环动态颜色 |
| Tooltip | `el-tooltip` | hover 显示 `56k / 256k` 格式用量 |
| 脉冲警示 | CSS `::after` + `@keyframes pulse-ring` | critical 状态外圈呼吸灯 |
| 确认弹窗 | `el-dialog` | 点击圆环弹出，显示用量百分比和说明 |

---

## 3. 数据流

### 3.1 从后端到前端

```
后端 AgentLoop
    │
    ▼ 发送消息完成
done_event = {
    type: 'done',
    context_usage: {
        input_tokens: 56000,
        context_window: 256000,
        usage_percent: 21.9,
        status: 'normal',
        ...
    }
}
    │
    ▼ SSE 推送
前端 wrappedDispatch()
    │
    ▼ 提取并保存
contextUsage.value = data.context_usage
```

`contextUsage` 只有在收到 `done` 事件后才被赋值。因此：
- **新会话/未发送消息**：圆环灰色，tooltip 显示"发送消息后将显示 token 用量"
- **进行中**：保留上次 `done` 事件的值（切换会话时重置）
- **完成后**：显示最新用量数据

### 3.2 状态分级

前端 `contextUsageStatus` computed 将原始数据转换为 UI 状态：

| 后端 status | usage_percent | 前端 color | 场景 |
|-------------|---------------|-----------|------|
| `normal` | 0~50% | `#67c23a` 绿 | 健康状态 |
| `warning` | 50~70% | `#409eff` 蓝 | 开始关注 |
| `caution` | 70~85% | `#e6a23c` 橙 | 建议压缩 |
| `critical` / `block` | 85%+ | `#f56c6c` 红 | 即将/已经自动压缩 |

**Critical 状态的特殊处理**：
- 外圈添加 `pulse-ring` 呼吸灯动画（CSS `@keyframes`）
- 放大系数 1.0 → 1.15 → 1.0，透明度 0.6 → 0.3 → 0.6
- 周期 1.5s，持续吸引用户注意

### 3.3 数值格式化

Tooltip 采用 `k` 单位简化大数字：

```typescript
function formatK(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1).replace(/\.0$/, '')}k`
  return n.toString()
}
// 56000 → "56k", 256000 → "256k", 800 → "800"
```

---

## 4. 交互设计

### 4.1 Hover

```
┌──────────────────┐
│ 56k / 256k       │  ← el-tooltip (placement="top")
└──────────────────┘
        ▼
      [◯]
```

### 4.2 Click → 确认弹窗

点击圆环打开 `el-dialog`（宽度 420px，居中）：

```
┌─────────────────────────────┐
│ 压缩上下文                   │
├─────────────────────────────┤
│          67%                │  ← 大字号百分比
│      56k / 256k             │  ← 用量详情
│                             │
│ 压缩将保留核心内容并生成摘要   │
│ 可以显著减少 token 消耗      │
├─────────────────────────────┤
│          [取消] [确认压缩]   │
└─────────────────────────────┘
```

点击"确认压缩"后：
1. 关闭弹窗
2. 调用现有的 `compactContext()` 函数
3. 展示 `ElMessage.info('正在压缩上下文...')` loading
4. 成功后用后端返回的压缩后消息列表替换当前会话

### 4.3 生命周期中的重置点

防止旧会话数据残留：

| 操作 | 行为 |
|------|------|
| 切换会话 (`selectConversation`) | `contextUsage.value = null` |
| 清空对话 (`clearCurrentConversation`) | `contextUsage.value = null` |
| 删除对话 (`deleteCurrentConversation`) | `contextUsage.value = null` |

---

## 5. 关键代码位置

| 功能 | 文件 | 区域 |
|------|------|------|
| 圆环模板 | `frontend/src/views/Chat.vue` | `.input-footer .footer-left` |
| 弹窗模板 | `frontend/src/views/Chat.vue` | `<!-- 压缩上下文确认弹窗 -->` |
| 数据计算 | `frontend/src/views/Chat.vue` | `contextUsageStatus`, `ringDashOffset`, `contextUsageTooltip` |
| 样式定义 | `frontend/src/views/Chat.vue` | `.context-ring`, `@keyframes pulse-ring`, `.compact-dialog-body` |
| 后端数据生成 | `backend/app/api/sessions.py` | `get_session()` 中通过 `TokenBudget.to_dict()` 生成 |
| Token 预算 | `backend/app/modules/agent/token_budget.py` | `TokenBudget.to_dict()` |

---

## 6. 与 Phase 1 压缩系统的关系

Context Ring 是 Phase 1 上下文压缩系统的**前端交互层**，与后端压缩机制解耦：

```
┌─────────────────┐     ┌──────────────────┐
│   Context Ring  │────▶│  compactContext()│
│   (UI 触发入口)  │     │  (调用 /chat/compact)
└─────────────────┘     └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ 后端压缩引擎      │
                        │ (Compactor/      │
                        │  MicroCompact)   │
                        └──────────────────┘
```

圆环本身不参与压缩逻辑，只是：
1. **展示**后端计算的 `context_usage` 状态
2. **触发**已有的手动压缩 API

---

## 7. 设计决策记录

### 7.1 为什么用 SVG 而不是 Element Plus 的 Progress 组件？

Element Plus 的 `el-progress` 支持 `type="circle"`，但我们选择原生 SVG：
- **更轻量**：不需要额外组件开销
- **更灵活**：可以自定义脉冲动画、hover 缩放等交互
- **更精确**：直接控制 `stroke-dasharray/dashoffset`，动画更流畅

### 7.2 为什么放在左下角而不是保留在右上角？

- **视线动线**：用户输入消息时，视线自然落在输入区域左下角
- **操作连贯性**：看完余量 → 决定是否压缩 → 点击圆环，动线最短
- **空间利用**：左下角 Paperclip 按钮旁有空余空间，不侵占输入框宽度

### 7.3 为什么点击后需要确认弹窗？

压缩是**破坏性操作**（会替换消息列表），虽然保留了核心内容，但用户可能不了解压缩的具体效果。弹窗起到：
- 教育作用：说明压缩会做什么
- 确认作用：防止误触导致意外压缩
- 信息展示：在弹窗中清晰展示当前用量，帮助用户决策
