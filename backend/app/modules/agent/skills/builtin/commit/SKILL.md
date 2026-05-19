---
title: Git 提交
description: 分析变更、生成规范 commit message 并安全提交
tags: [git, commit, version-control]
always: false
---

# Git 提交流程

按照以下步骤完成一次安全的 Git 提交。

## 1. 分析变更

运行以下命令检查当前状态：

```
git status
git diff
git diff --cached
```

识别：
- 修改的文件（modified）
- 新增的文件（untracked）
- 删除的文件（deleted）

## 2. 安全检查

检查变更中是否包含敏感文件：
- `.env`、`.env.local`、`.env.production`
- `credentials.json`、`*.pem`、`*.key`
- 任何包含密码、token、密钥的文件

如果发现敏感文件，**立即警告用户**，不要将其加入暂存区。

## 3. 查看最近提交风格

```
git log --oneline -5
```

了解项目的 commit message 风格（语言、格式、前缀等）。

## 4. 生成 Commit Message

根据变更内容生成 commit message，遵循以下规则：
- 使用中文（或与项目已有风格一致）
- 1-2 句话，聚焦"为什么"而非"改了什么"
- 格式：`<类型>: <简短描述>`
- 类型包括：feat（新功能）、fix（修复）、refactor（重构）、docs（文档）、test（测试）、chore（杂项）

在提交前，**向用户展示变更摘要和 commit message**，等待确认。

## 5. 暂存文件

使用 `git add <具体文件>` 逐个添加，**不要使用 `git add -A` 或 `git add .`**，避免误提交敏感文件或无关文件。

## 6. 提交

```
git commit -m "<commit message>"
```

署名规范：
```
Co-Authored-By: Claude Code <noreply@anthropic.com>
```

## 安全红线

- **绝不**跳过 Git hooks（`--no-verify`）
- **绝不**跳过 GPG 签名（除非用户明确要求）
- **绝不** force push 到 main/master
- **绝不**在未确认的情况下提交
