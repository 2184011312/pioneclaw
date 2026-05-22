# Agent Skill 评估与自演进生态系统 — 完整调研

> 日期：2026-05-19
> 覆盖：Darwin Skill / Skill-Creator / Skill Forge / SkillCompass / SPARK / skill-optimizer / M16 Zeph / skill-factory

---

## 一、Darwin Skill（alchaincyf/darwin-skill）

**定位**：8维评估 + 人在回路的自主优化

### 评估公式

```
Score = Σ(dim_i × w_i) / 10    # dim∈[1,10], 满分100

结构维度 (60分):
  dim1 Frontmatter质量  w=8
  dim2 工作流清晰度    w=15
  dim3 边界条件覆盖    w=10
  dim4 检查点设计      w=7
  dim5 指令具体性      w=15
  dim6 资源整合度      w=5

效果维度 (40分):
  dim7 整体架构        w=15
  dim8 实测表现        w=25   # 子agent跑2-3个prompt对比
```

### 优化循环

```
for each skill:
  while round < 3:
    诊断最低维度 → 改进 → 子agent重评
    if Score_new > Score_old: keep
    else: git revert + break
  人类检查点 → 确认继续
```

### 棘轮机制

```
Score(t+1) > Score(t)  →  keep
Score(t+1) ≤ Score(t)  →  git revert + break
```

### 特色

- 🟢 双重评估（结构+实测）
- 🟢 人在回路
- 🟢 探索性重写（连续卡住时触发）
- 🟡 需要 git 环境
- 🟡 场景：批量优化 60+ skills

---

---

> **更新**: 2026-05-19 基于源码 `D:\skills\skills\skill-creator\` 补充实测公式

---

## 二、Skill-Creator v2（Anthropic 官方，2026年3月更新）

**定位**：创建 + 评估 + 改进 + 基准测试，四模式一体

> 源码：[anthropics/skills](https://github.com/anthropics/skills) | 文件：agents/{grader,comparator,analyzer}.md + scripts/{run_eval,run_loop,aggregate_benchmark}.py

---

### 2.1 四模式架构

| 模式 | 作用 | 关键文件 |
|------|------|---------|
| **Create** | 从任务描述生成新 skill | SKILL.md |
| **Eval** | 写测试用例 → 带/不带 skill 对照跑 → 结构化打分 | agents/grader.md, scripts/run_eval.py |
| **Improve** | 接收 eval 反馈 → 重写 skill 修复失败项 | agents/analyzer.md |
| **Benchmark** | 追踪 pass_rate、耗时、token 用量，多版本对比 | scripts/aggregate_benchmark.py |

---

### 2.2 Eval 模式 — 两套评估体系

#### A. 功能评估（Grader Agent）

**工作流**: `读transcript → 检查输出文件 → 评估断言 → 提取claims → 写评分 → 写eval反馈`

**评分公式（源码 aggregate_benchmark.py）**：

```python
pass_rate = passed / total                    # 单次运行
mean      = Σ(x_i) / n                        # 多次运行平均值
stddev    = sqrt(Σ(x_i - mean)² / (n - 1))   # 标准差
delta     = with_skill − baseline              # 差值
```

**Benchmark 输出表**：
```
| Metric    | With Skill           | Baseline            | Delta     |
|-----------|---------------------|---------------------|-----------|
| Pass Rate | 85% ± 5%            | 65% ± 10%           | +0.20     |
| Time      | 165.0s ± 12.0s      | 140.0s ± 8.0s       | +25s      |
| Tokens    | 12450 ± 800         | 9800 ± 600          | +2650     |
```

#### B. 触发评估（run_eval.py）

**实测方式**：创建临时 command file → `claude -p` 运行 → 检测 stream event 中是否出现 Skill/Read 调用

**触发率公式（源码）**：

```python
trigger_rate = sum(triggers) / runs_per_query  # 每查询跑3次

# 判定
if should_trigger:
    pass = (trigger_rate >= threshold)         # 默认 threshold=0.5
else:
    pass = (trigger_rate < threshold)
```

**评估集**：
- ~20 查询（10 should-trigger + 10 should-not-trigger）
- 60% train / 40% held-out test
- 每查询 3 次运行
- 多进程并行（默认 10 workers）

---

### 2.3 三 Agent 管线

#### Grader Agent（agents/grader.md）

```
7步流程:
  1. Read Transcript → 执行步骤、最终结果、错误
  2. Examine Outputs → 不只看 transcript 描述，实际读文件
  3. Evaluate Assertions → PASS/FAIL + 证据引用
  4. Extract & Verify Claims → factual/process/quality 三类
  5. Read User Notes → 执行者的不确定性、workarounds
  6. Critique Evals → 标记弱断言、遗漏的重要检查
  7. Write grading.json → 标准化格式
```

**判定标准**：
- PASS: 有明确证据 AND 证据反映实质完成（不只是表面合规）
- FAIL: 无证据/证据矛盾/表面合规但内容错误/不可验证
- 不确定时：burden of proof 在断言方 → FAIL

#### Comparator Agent（agents/comparator.md）

**盲比公式（源码）**：

```
content_score   = avg(correctness, completeness, accuracy)      # 每个1-5分
structure_score = avg(organization, formatting, usability)      # 每个1-5分
overall_score   = avg(content_score, structure_score) × 2      # 缩放到1-10

winner = argmax(overall_score(A), overall_score(B))
```

6 维度动态 rubric，按任务类型自适应（PDF→字段对齐/文本可读性，文档→章节结构/标题层级）

#### Analyzer Agent（agents/analyzer.md）

**双模式**：

**配对分析模式**（单次对比后）：
```
读 winner/loser 的 skill + transcript → 分析指令遵循度(1-10)
→ 提取 winner strengths + loser weaknesses
→ 生成改进建议（high/medium/low × 6类别）
```

**Benchmark 分析模式**（多轮后）：
```
标记 non-discriminating 断言（两边都总是通过 = 无效）
标记 high-variance eval（不稳定）
标记 surprising results（带skill反而差）
输出观察笔记 → benchmark.json 的 notes 字段
```

---

### 2.4 改进循环 — history.json 版本追踪

```json
{
  "current_best": "v2",
  "iterations": [
    {"version": "v0", "parent": null, "pass_rate": 0.65, "result": "baseline"},
    {"version": "v1", "parent": "v0", "pass_rate": 0.75, "result": "won"},
    {"version": "v2", "parent": "v1", "pass_rate": 0.85, "result": "won"}
  ]
}
```

```
result ∈ {baseline, won, lost, tie}
won  → 成为新的 current_best
lost → 保留 version，current_best 不变
tie  → 保留 version，current_best 不变
```

触发优化基于 description，非 body——5 轮 loop，每轮 eval train+test split。

---

### 2.5 验证规则（quick_validate.py，原 v1 保留）

```
valid = check_frontmatter() ∧ check_name() ∧ check_description()

check_name():
  regex = ^[a-z0-9-]+$
  len ≤ 64
  不能以 - 开头/结尾/连续 --

check_description():
  len ≤ 1024
  不能含 < >

check_frontmatter():
  仅允许: {name, description, license, allowed-tools, metadata}
```

---

### 2.6 特色

- 🟢 4 模式完整生命周期
- 🟢 三 Agent 独立评分（grader/comparator/analyzer）
- 🟢 Trigger Rate 源码级实测（run_eval.py 创建临时 command file + 检测 stream event）
- 🟢 盲比消除偏见（comparator 不知道 A/B 哪个是 baseline）
- 🟢 Claims 提取（超越预定义断言，发现隐藏问题）
- 🟢 Eval 自检（grader 自我批判断言质量）
- 🟢 基准对比（pass/token/time delta + mean/stddev）
- 🟢 grading.json 标准化格式
- 🟡 无安全审计维度
- 🟡 无自动回滚（人工决定 current_best）

---

## 三、Skill Forge（GodModeAI2025/skill-forge）

**定位**：全自主 skill 进化引擎，无人干预

### 评分公式

**默认模式**：
```
composite = assertion_pass_rate × 0.80 + efficiency × 0.20
```

**LLM-as-Judge 模式**：
```
composite = assertion_pass_rate × 0.50 + llm_judge × 0.30 + efficiency × 0.20
```

### 保留/回滚决策

```
| Δscore | 决策 |
| > +0.02  | KEEP  — 明确改进 |
| < -0.05  | REVERT — 回退 |
| -0.05~+0.02 | NEUTRAL — 保留，偏新 |
```

### 过拟合防护（5层）

```
1. 训练/测试分离: 60% evals for hypothesis, 40% held-out for scoring
2. 泛化检查: Hypothesis agent 必须解释为什么改动能泛化
3. 变异多样性: Coverage Matrix 追踪实验分布
4. Eval 轮换: 5轮实验后自动生成新 eval
5. 回归测试: Test evals 仅用于评分，不参与分析
```

### 探索-利用调度

```
Phase Early  (R1-3): Explore — 优先未探索类别
Phase Mid    (R4-7): Mixed — 平衡覆盖与高回报
Phase Late   (R8+):  Exploit — 聚焦最佳增量
```

### 实测结果

| Skill | 迭代 | Before | After | Δ |
|-------|------|--------|-------|-----|
| humanizer | 3 | 0.74 | 0.90 | +21.6% |
| fachbuch-lektorat | 3 | 87% | 100% | +13% |

### 特色

- 🟢 全自主（无人在回路）
- 🟢 断言驱动（eval assertions）
- 🟢 过拟合防护完善
- 🟡 需要编写 eval assertions
- 🟡 场景：技术性 skill，有可量化指标

---

## 四、SkillCompass（Evol-ai/SkillCompass）

**定位**：6维质量+安全评估器，CI友好

### 评分公式

```
overall = round((D1×0.10 + D2×0.15 + D3×0.20 + D4×0.30 + D5×0.15 + D6×0.10) × 10)
# 0-100 量表
```

### 6维度权重

| # | 维度 | 权重 | 评估内容 |
|---|------|------|---------|
| D1 | Structure | 10% | Frontmatter、格式、声明 |
| D2 | Trigger | 15% | 激活质量、拒识准确、可发现性 |
| D3 | **Security** | 20% | 密钥、注入、权限、泄露、嵌入shell |
| D4 | **Functional** | 30% | 核心质量、边界情况、输出稳定性 |
| D5 | Comparative | 15% | 相比直接对话的增量价值 |
| D6 | Uniqueness | 10% | 与类似 skill 重叠度、被模型取代风险 |

### 判定门限

```
PASS:    score ≥ 70 ∧ D3 pass
CAUTION: 50 ≤ score < 70 ∨ D3有High级发现
FAIL:    score < 50 ∨ D3有Critical发现  ← gate override
```

### 闭环改进

```
改进最弱维度 → 重评 → 验证提升 → 下个最弱
         ↓ 失败则自动回滚 (SHA-256 snapshot)
```

### 特色

- 🟢 **Security 是 gate**（安全不通过直接 FAIL）
- 🟢 CI 模式（exit codes: pass/caution/fail）
- 🟢 自动回滚
- 🟡 场景：需要安全审计的 skill

---

## 五、SPARK（EtaYang10th/spark-skills）

**定位**：研究原型——基于执行证据的 skill 蒸馏

### 核心公式

```
PDI = Posterior Distillation Index
     = measure(skill_grounded_in(posterior_execution_evidence))

循环: execute → judge → reflect → retry → distill
```

### 实测结果

86 tasks across 11 domains:
- SPARK skills **始终战胜** no-skill baseline
- SPARK skills **优于** human-written skills

### 特色

- 🟢 证据驱动（不是猜测好坏）
- 🟢 研究级方法论
- 🟡 原型阶段，非生产就绪

---

## 六、skill-optimizer（tessl-labs）

**定位**：实战工具——"Does my skill actually work?"

### 诊断分类

```
Working   — 带 skill 明显优于 baseline
Gap       — 带 skill 没提升（skill 没覆盖此场景）
Redundant — 带不带没区别
Regression — 带 skill 反而更差
```

### 工作流

```
Skill Review(静态) → Scenario Generation(5+ eval) → Evals(跑agent)
  → Diagnosis(4桶分类) → Auto-fix(最小补丁)
```

### 实测

fastify-best-practices: 67% → 94%（一轮优化）

### 特色

- 🟢 开箱即用（零 eval 编写）
- 🟢 自动生成测试场景
- 🟢 跨模型测试（Haiku/Sonnet/Opus）
- 🟡 商业化产品（tessl.io）

---

## 七、M16 Zeph（bug-ops/zeph）

**定位**：生产 agent 的自我学习系统

### 触发-优化流程

```
skill 失败 → self-reflection → retry alternative
  → if success: generate improved skill → store version → activate
  → if still fail: log failure, don't improve
```

### 安全约束

```
自动回滚: success_rate < 50% after 5 evaluations
版本限制: max 10 auto-versions
体积限制: body ≤ 2× original
频率限制: 1 improvement/skill/hour
```

### 特色

- 🟢 在线学习（生产环境实时优化）
- 🟢 多层安全锁
- 🟡 需要与 bug-ops/zeph 系统集成

---

## 八、SkillScore（joeynyc/skillscore） ⭐ 最匹配

**定位**：CLI 技能评分工具——专门做 evaluate + score + feedback

### 七维加权公式

```
Raw Score (0–10) = Σ(dim_i × w_i) for i=1..7
Percentage = raw_score × 10
Grade = lookup(percentage)
```

### 七维度 + 权重

| # | 维度 | 权重 | 评测内容 |
|---|------|------|---------|
| 1 | Identity & Metadata | 20% | name 规范(^[a-z0-9-]+$, ≤64字符)、description ≤1024字符、第三人称、无XML标签 |
| 2 | Conciseness | 15% | body ≤500行、渐进式披露(file引用)、不解释Claude已知的基础知识 |
| 3 | Clarity & Instructions | 15% | 编号步骤、术语一致、代码示例、祈使+灵活混合 |
| 4 | Routing & Scope | 15% | 动作动词+触发条件、反向路由(什么时候不用)、领域词汇 |
| 5 | Robustness | 10% | 代码块错误处理(try/catch, set -e)、依赖验证(command -v, --version)、魔法常量检测 |
| 6 | **Safety & Security** | 15% | 邻近密钥检测(5行内secret+network)、危险命令扫描、提权检测、无限循环检测 |
| 7 | Portability & Standards | 10% | Windows路径检测、硬编码路径、MCP格式(ServerName:tool_name)、时间敏感信息 |

### 等级表

```
A+ 97-100 | A 93-96 | A- 90-92
B+ 87-89  | B 83-86 | B- 80-82
C+ 77-79  | C 73-76 | C- 70-72
D+ 67-69  | D 65-66 | D- 60-64
F 0-59
```

### 用例

```bash
skillscore ./my-skill/ --json --output score.json
skillscore ./skill1 ./skill2 --batch
skillscore -g user/repo --verbose
```

---

## 九、ordinary-claude-skills（Activer007）

**定位**：社区技能评审 + 分级体系（S/A/B/C/D）

### 四维评分

| 维度 | 分值 | 内容 |
|------|------|------|
| Content Quality | 50 | 清晰度、技术深度、文档完整性 |
| Technical Implementation | 30 | 代码质量、设计模式、错误处理 |
| Maintenance | 10 | 更新频率、社区活跃度 |
| User Experience | 10 | 易用性、可读性 |

**总分 100**，实测算数平均分 61.6。A级(10.4%)、D级(36.4%)。含 `analyze_all_skills.py` 自动评审脚本。

---

## 十、SkillHub（iflytek/skillhub）⭐ 企业级

**定位**：自托管企业技能注册中心（发布→版本→评审→RBAC→审计）

### 评审流水线

```
上传包 → 安全扫描 → 扩展名白名单检查
  → 命名空间管理员评审 → 平台超级管理员全局推广审批
  → 审计日志记录每一步
  → 社区评分（用户打分+下载量+星标）
```

三层 RBAC：Owner / Admin / Member + SUPER_ADMIN 跨命名空间。

---

## 十一、LobeHub skill-reviewer（gitgoodordietrying/clawhub-lab）⭐ 最详细 Rubric

**定位**：社区最完整的 SKILL.md 结构化评审技能

### 七维评分（总分 54+）

| 类别 | 满分 | 评估要点 |
|------|------|---------|
| **Structure** | 11 | YAML frontmatter、name/description/metadata 完整性、When to Use 章节 |
| **Description** | 8 | 主动动词开头、触发短语、具体范围、50-200字符、可搜索关键词 |
| **Metadata** | 4 | emoji 相关性、requires.anyBins 准确性、OS 声明、JSON 合法性 |
| **Example Density** | 3* | 每 8-15 行一个代码块 |
| **Example Quality** | 3* | 语言标签、语法正确、现实值、无占位符、覆盖常见场景 |
| **Organization** | 6 | 按任务/场景组织、常见操作优先、章节自包含、标题层级一致 |
| **Actionability** | 10 | 祈使语气、步骤逻辑顺序、错误处理、输出验证 |
| **Tips** | 8 | 5-10条非显而易见的技巧、具体可操作、覆盖陷阱 |

### 评级标准

```
45+        Excellent（可发布）
35-44      Good（需小改进）
25-34      Fair（有显著差距）
<25        Poor（需大修）
```

### 缺陷分类

- **Critical**: 无效 frontmatter、代码示例错误、工具依赖不准、描述误导
- **Major**: 缺少 When to Use、缺少代码示例、组织抽象化、缺少 Tips
- **Minor**: 占位符值、格式不一致、缺少交叉引用、命令过时

---

## 十二、Tessl Quality Score（tessl.io）

**定位**：自动化 skill 质量评分平台

### 四维评分

| 维度 | 内容 |
|------|------|
| **Discovery（发现）** | 描述清晰度、`Use when...` 触发子句、触发词自然度、是否与其他skill冲突 |
| **Implementation（实现）** | 指令简洁性、可操作性、工作流清晰度、渐进式信息披露 |
| **Validation（验证）** | YAML frontmatter 结构、必要字段完整性 |
| **Security** | Pass/Fail 安全检查 |

### mattpocock/skills 实测分数

| Skill | Quality |
|-------|---------|
| write-a-skill | 80% |
| request-refactor-plan | 75% |
| handoff | 52% |

---

## 十三、agentskills/agentskills（12k⭐）

**定位**：Agent Skills 开放标准——所有评分工具的基准规范

定义了 SKILL.md 格式、目录结构、元数据规范。本身不评分，但所有评分工具（SkillScore、SkillCompass、skill-reviewer）都基于此标准。

---

## 十四、skill-factory（zhelunSun/skill-factory）

**定位**：元 skill——创造所有 skill 的 skill

```
自动生成 SKILL.md 从:
  - 对话历史
  - 工作流描述
  - 已有 skill 模式
```

### 特色

- 🟢 从零生成 skill
- 🟡 无评估/优化能力（造出来就不管了）

---

## 十二、全生态对比矩阵

| 系统 | 评分维度 | 公式化 | 实测 | 自主优化 | 安全审计 | 回滚 |
|------|:-------:|:-----:|:---:|:-------:|:-------:|:---:|
| **Darwin** | 8维 | Score=Σ(d×w)/10 | ✅ sub-agent | 半自主 | ❌ | git revert |
| **Skill-Creator v2** | 2类8指标 | pass_rate + trigger_rate | ✅ 3-Agent管线 | ✅ 5轮desc优化 | ❌ | 人工current_best |
| **Skill Forge** | 3指标 | composite=0.8×assert+0.2×eff | ✅ 断言驱动 | **全自主** | ❌ | 阈值判定 |
| **SkillCompass** | 6维 | overall=Σ(d×w)×10 | ❌ | **闭环** | ✅ gate | SHA256 snap |
| **SkillScore** | 7维 | Score=Σ(d×w), %=score×10 | ❌ 静态 | ❌ | ✅ 邻近密钥+危险命令 | ❌ |
| **ordinary-claude** | 4维 | 50+30+10+10=100pts | ❌ 静态 | ❌ | ❌ | ❌ |
| **SkillHub** | 社区评分 | 社区打分+下载量+星标 | ✅ 安全扫描 | ❌ | ✅ RBAC+审计 | ❌ |
| **SPARK** | PDI | 证据驱动 | ✅ trajectory | ✅ | ❌ | ? |
| **skill-optimizer** | 4桶 | 诊断分类 | ✅ cross-model | 半自主 | ❌ | ✅ |
| **M16 Zeph** | - | 通过/失败 | ✅ production | **在线学习** | ✅ | auto-rollback |
| **skill-reviewer** | 8维 | Σ(category) / 54+ | ❌ 静态review | ❌ | ✅ 5类缺陷检测 | ❌ |
| **Tessl** | 4维 | % score | ✅ 自动评测 | ❌ | ✅ Pass/Fail | ❌ |
| **agentskills** | 标准规范 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **skill-factory** | - | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 十五、给 PioneClaw 的最终建议

### 最优组合

```
SkillScore 7维静态评分 + Skill-Creator v2 trigger_rate实测 + skill-reviewer缺陷分类
```

### 推荐评分模型（4大类 100分制）

```
静态评分 (40分) = SkillScore 公式（选最关键的4维）:
  Identity 15% + Conciseness 10% + Clarity 10% + Safety 5%

实测评分 (30分) = Skill-Creator v2 方式:
  trigger_rate × 15  (触发准确率)
  + pass_rate × 15  (功能通过率)

结构评分 (20分) = skill-reviewer 方式:
  Structure 5 + Organization 5 + Example Quality 5 + Actionability 5

缺陷扣分 (10分) = 0 缺陷 10分, Critical 扣5, Major 扣2, Minor 扣1

Total = 40 + 30 + 20 + 10 = 100
```

### 为什么不是全抄 Darwin？

Darwin 的 8 维主观打分（1-10 人工评）适合人工 Review，不适合自动化。SkillScore 的 7 维静态检查 + Skill-Creator 的实测才构成完整的自动化 pipeline。

---

## 十六、给 PioneClaw 的建议

### 可以借鉴的组合

```
SkillCompass 的 Security gate  +  Darwin 的 8维评分  +  Skill Forge 的过拟合防护
```

### 最小可行评估（MVP）

```
Score = structure_score × 0.55 + security_score × 0.20 + functional_score × 0.25

structure_score: Skill-Creator 规则  →  Pass/Fail
security_score:  SkillCompass D3    →  0-10
functional_score: Darwin dim8实现    →  0-10
```

### 最佳实践

1. **评分独立性**: scorer ≠ modifier（Darwin + Skill Forge 都用子 agent）
2. **Security Gate**: D3 不通过直接 FAIL（SkillCompass 的创新）
3. **过拟合防护**: Train/test split + eval rotation（Skill Forge）
4. **人在回路**: 每个 skill 优化后确认（Darwin）
5. **棘轮机制**: 只保留改进，自动回滚（所有系统共用）
