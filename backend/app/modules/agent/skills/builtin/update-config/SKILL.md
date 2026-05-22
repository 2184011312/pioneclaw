---
title: 配置管理
description: 查看和修改 PioneClaw 的系统配置
tags: [config, settings, administration]
always: false
---

# 配置管理

管理 PioneClaw 的运行时配置。

## 配置存储

PioneClaw 配置分两层：

| 层级 | 位置 | 内容 |
|------|------|------|
| 环境变量 | `.env` | 数据库连接、密钥、服务端口等敏感配置 |
| 系统设置 | DB `system_settings` | 运行时参数，通过 `/api/settings` 管理 |

## 工作流程

### 1. 读取当前配置

通过 Settings API 获取当前配置：

```
GET /api/settings/{key}
```

列出所有设置：

```
GET /api/settings
```

### 2. 理解用户意图

确定用户要修改的配置项、期望的值、修改的原因。

如果不确定配置项的完整路径，先询问用户。

### 3. 展示修改对比

在应用修改前，展示前后对比：

```
## 配置变更预览

### 修改
- {key}: "old_value" → "new_value"
```

### 4. 应用修改

通过 Settings API 执行修改：

```
PUT /api/settings/{key}
{"value": "new_value"}
```

### 5. 验证

修改后重新读取确认生效。

## 重要原则

- 修改前必须展示前后对比
- 不要修改用户未提及的配置项
- 如果修改可能影响系统行为，给出提醒
- 敏感信息（密钥、密码）通过 `.env` 管理，不走 Settings API
