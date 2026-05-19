# Skill 评估体系对比分析 — Darwin vs Skill-Creator

> 日期：2026-05-19

---

## 一、Darwin Skill — 8 维评估体系（100分制）

### 核心理念

`评估 → 改进 → 实测验证 → 人类确认 → 保留或回滚`

借鉴 Karpathy autoresearch 的棘轮机制：**只保留改进，自动回滚退步**。

### 1.1 评估公式

#### 总分公式

```
Score = Σ(dim_i × w_i) / 10

其中:
  dim_i ∈ [1, 10]  # 每个维度打 1-10 分
  w_i = 该维度权重

满分 = 100
```

#### 8 维度权重

##### 结构维度（60分，静态分析）

| # | 维度 | 权重 w | 评分要点 |
|---|------|--------|---------|
| 1 | Frontmatter 质量 | 8 | name 规范、description 含"做什么+何时用+触发词"、≤1024字符 |
| 2 | 工作流清晰度 | 15 | 步骤明确可执行、有序号、每步有明确输入/输出 |
| 3 | 边界条件覆盖 | 10 | 处理异常情况、有 fallback 路径、错误恢复 |
| 4 | 检查点设计 | 7 | 关键决策前有用户确认、防止自主失控 |
| 5 | 指令具体性 | 15 | 不模糊、有具体参数/格式/示例、可直接执行 |
| 6 | 资源整合度 | 5 | references/scripts/assets 引用正确、路径可达 |

##### 效果维度（40分，需实测）

| # | 维度 | 权重 w | 评分要点 |
|---|------|--------|---------|
| 7 | 整体架构 | 15 | 结构层次清晰、不冗余不遗漏、与生态一致 |
| 8 | 实测表现 | 25 | 跑 2-3 个测试 prompt，对比带/不带 skill 的输出质量 |

#### 维度 8 实测公式

```
dim_8 = avg(Q_1, Q_2, Q_3)

Q_i = quality(agent(skill, prompt_i), agent(baseline, prompt_i))

# quality 评估角度:
# - 输出是否完成了用户意图？
# - 相比不带 skill 的 baseline，质量提升明显吗？
# - 有没有 skill 引入的负面影响？

# 如果无法跑子 agent:
dim_8 = dry_run_score  # 人工模拟推演，标记 dry_run
```

### 1.2 优化循环

```
for each skill (按 Score 从低到高):
  round = 0
  while round < MAX_ROUNDS (默认 3) AND Score_new > Score_old:
    round += 1
    1. 诊断: 找出 min(dim_1...dim_8)
    2. 提案: 针对最低维度生成改进方案
    3. 执行: 编辑 SKILL.md → git commit
    4. 重评: 结构重打分 + 独立子 agent 重跑测试
    5. 决策:
         if Score_new > Score_old: keep, 更新 Score_old
         else: revert (git revert), break  # 该 skill 到瓶颈
    6. 日志: results.tsv 追加行
  
  # 每个 skill 优化完暂停 → 人类检查点
```

### 1.3 棘轮机制

```
Score(t+1) > Score(t)  →  keep (git commit)
Score(t+1) ≤ Score(t)  →  revert (git revert) + break
```

约束：
- Score 保留 1 位小数
- 比较必须**严格大于**（不靠四舍五入）
- 改进后文件大小 ≤ 原始 × 1.5

### 1.4 探索性重写触发

```
if consecutive_break_at_round1 >= 2:
    提议探索性重写
    git stash → 从头重写 SKILL.md → 重评
    if Score(重写) > Score(stash): 采用
    else: git stash pop 恢复
```

### 1.5 四项优化策略优先级

```
P0: 效果问题（实测发现）→ 测试输出偏离意图、带skill反而更差
P1: 结构性问题 → Frontmatter缺触发词、缺少流程结构、缺检查点
P2: 具体性问题 → 步骤模糊、缺输入输出规格、缺异常处理
P3: 可读性问题 → 段落过长、重复、缺速查
```

### 1.6 五条核心原则

| # | 原则 | 公式表达 |
|---|------|---------|
| 01 | 单一可编辑资产 | `|modified_files| = 1`（每次只改 1 个 SKILL.md） |
| 02 | 双重评估 | `eval = f_struct(SKILL.md) + f_effect(agent(skill), agent(baseline))` |
| 03 | 棘轮机制 | `Score(t+1) > Score(t) ∨ git revert` |
| 04 | 独立评分 | `scorer ≠ modifier`（子 agent 独立评分） |
| 05 | 人在回路 | `∀ skill: optimize → pause → human_confirm → next` |

---

## 二、Skill-Creator — 结构验证体系（Pass/Fail 制）

### 核心理念

**指导创建** + **打包前校验**。不是评分系统，而是规范检查。

### 2.1 验证规则（quick_validate.py）

#### 文件结构

```
SKILL.md 存在? → False: "SKILL.md not found"
```

#### Frontmatter 规则

```
规则1: 以 '---' 开头 → False: "No YAML frontmatter found"
规则2: YAML 解析成功 → False: "Invalid YAML"
规则3: 必须是 dict → False: "Frontmatter must be a YAML dictionary"
规则4: 仅允许这些 key: {name, description, license, allowed-tools, metadata}
      → False: "Unexpected key(s): {keys}"
规则5: name 必填 → False: "Missing 'name'"
规则6: description 必填 → False: "Missing 'description'"
```

#### Name 规则

```
规则7: 必须是字符串 → False: "Name must be a string"
规则8: 匹配 ^[a-z0-9-]+$（hyphen-case）→ False: "should be hyphen-case"
规则9: 不能以 - 开头/结尾，不能含 -- → False
规则10: 长度 ≤ 64 字符 → False: "too long"
```

#### Description 规则

```
规则11: 必须是字符串 → False: "Description must be a string"
规则12: 不能含 < 或 > → False: "cannot contain angle brackets"
规则13: 长度 ≤ 1024 字符 → False: "too long"
```

### 2.2 设计原则（定性，非公式化）

#### 渐进式加载

```
Level 1: Metadata (name + description) — 始终在上下文 (~100 words)
Level 2: SKILL.md body — skill 触发时加载 (<500 lines)
Level 3: Bundled resources — 按需加载（无限制）
```

#### 上下文成本意识

```
consume(tokens) = metadata_tokens + body_tokens + Σ reference_tokens(loaded)

约束: body < 500 lines
约束: 避免深度嵌套引用（仅一层）
约束: 大的 reference 文件需含目录（TOC）
```

#### 自由度控制

```
自由度 = f(任务脆弱性, 变异性)

高自由度 → 文本指令（多种方式有效）
中自由度 → 伪代码/可配置脚本
低自由度 → 特定脚本、少参数（操作脆弱、一致性关键）
```

---

## 三、对比总结

| 维度 | Darwin Skill | Skill-Creator |
|------|:-----------:|:------------:|
| **评估方式** | 8维加权评分 (0-100) | Pass/Fail 规则检查 |
| **评分单位** | 连续分值 (1-10 × 权重) | 二元 (valid/invalid) |
| **是否实测** | ✅ 维度8跑子agent对比 | ❌ 仅静态 |
| **优化机制** | hill-climbing + git ratchet | 人工迭代 |
| **人在回路** | 每个skill优化后确认 | 不涉及 |
| **回滚机制** | git revert (自动) | 无 |
| **适用场景** | 批量优化 60+ skills | 创建新 skill |
| **公式化程度** | 高（8维加权+棘轮+重写触发） | 低（规则集，非数值） |

### Darwin 擅长

- 已有 skill 的**持续优化**
- **量化**好坏，可对比
- 防止**退化**（棘轮机制）
- 大规模 skill 生态的管理

### Skill-Creator 擅长

- **从零创建** skill 的规范指导
- **打包前校验**（自动化）
- 结构设计模式（progressive disclosure）

### 互补关系

```
Skill-Creator: 创建新 skill → 通过结构验证
       ↓
Darwin Skill:  优化已有 skill → 8维评估 + 自动回滚
```

两者可以串联使用：先创建，再持续优化。
