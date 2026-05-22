# PioneClaw vs CircleBot 功能缺口分析

> 分析日期：2026-05-12
> 定位：非商用 Runner + Center 平台
>
> 本文逐项列出 CircleBot 有而 PioneClaw 没有的功能，分析每项对 PioneClaw 是否必要。

---

## 安全模型（先统一认知）

审批的唯一判据：**被操作的东西是谁的？**

```
Center 超管           → 想干啥干啥，不审批（本来就是老大）

Runner 动自己电脑的东西 → 自己负责，不审批
  安全网：Plan 模式 + 用户确认弹窗（防 LLM 幻觉，不是防 Runner）

Runner 动系统/组织共享的东西 → Center 必须审批
  共享的东西不属于 Runner 一个，动了影响所有人
```

### 哪些是"共享的"——需要 Center 审批的高危操作

**数据库（CircleBot `allow_destructive` 级）：**

| 操作 | 后果 | 严重度 |
|------|------|--------|
| DROP DATABASE | 整库消失 | 致命 |
| DROP TABLE | 整表消失 | 致命 |
| TRUNCATE TABLE | 数据全清但表还在 | 致命 |
| ALTER TABLE ... DROP COLUMN | 删除字段 | 严重 |
| CREATE DATABASE | 新建库——虽不丢数据但是系统级变更 | 严重 |

**知识库（Wiki）：**

| 操作 | 后果 | 严重度 |
|------|------|--------|
| 删除 Wiki 空间/所有文档 | 知识库全丢，RAG 失效 | 致命 |
| 清空/重建向量索引 | 所有 RAG 检索瞬间失效 | 致命 |
| 批量删除文档 | 大量知识丢失 | 严重 |

**平台数据：**

| 操作 | 后果 | 严重度 |
|------|------|--------|
| 删除用户/账号 | 该用户所有数据消失 | 致命 |
| 删除系统级 Agent | 所有人用的 Agent 没了 | 致命 |
| 删除系统级 Skill | 所有人依赖的能力消失 | 致命 |
| 删除组织 | 整个组织及其数据被移除 | 致命 |

**系统配置（Center）：**

| 操作 | 后果 | 严重度 |
|------|------|--------|
| 修改 LLM API Key / Provider 配置 | 改错了整个平台无法调用模型 | 致命 |
| git force push 到主分支 | 代码历史不可逆覆盖 | 致命 |
| 修改 RBAC 权限/角色 | 连锁影响所有人的访问权限 | 严重 |

**Runner 侧——以下不需要 Center 审批（自己的电脑）：**

| 操作 | 为什么不需要审批 |
|------|-----------------|
| 读写 workspace 内文件 | Runner 自己的地盘 |
| 读写 workspace 外文件 | 自己电脑自己负责 |
| 执行本地命令 | 同上 |
| 安装/卸载软件 | 同上——但可能影响系统稳定性，看用户配置 |
| 修改环境变量/hosts/注册表 | 同上 |

### 高危操作的三道防线

关键不看操作是什么，看**被操作的东西是谁的**：

```
Runner 自己的，还没共享的 → 随便删，不审批（自己的东西自己负责）
Runner 自己的，已经审批成系统/组织级的 → 删要 Center 审批（所有权在 Runner，但影响别人了）
别人的 / 系统原生的 → 不给开口（Runner 根本没资格碰）
```

举个例子：Runner 写了一个 Skill → Center 审批通过 → 变成了系统级 Skill，大家都在用。这时候 Runner 想删它 → 不能直接删（已经是共享的了），也不能不给开口（确实是 Runner 写的），正确的做法是**审批**。

```
第一道：不需要审批（Runner 操作自己的私有资源）
  判据：resource.owner == runner && resource.scope == "user"
  实现：直接放行

第二道：需要审批（Runner 操作自己的已共享资源）
  判据：resource.owner == runner && resource.scope in ("org", "system")
  实现：请求进入审批队列 → Center 确认 → 放行/拒绝

第三道：不给开口（Runner 操作别人的或系统原生的资源）
  判据：resource.owner != runner 或 resource 是系统基础设施
  实现：API 中间件识别调用者是 Runner → 直接 403
```

| 高危操作 | 防线 | 理由 |
|---------|------|------|
| **数据库（数据库没有"谁的"概念，统一视为共享资源）** | | |
| DROP DATABASE | 不给开口 | Runner 的业务是查/改数据，不是管理数据库结构 |
| DROP TABLE | 需要审批 | Runner 可能有清理临时表的合理场景，但删正式表要确认 |
| TRUNCATE TABLE | 需要审批 | 同上 |
| ALTER TABLE DROP COLUMN | 需要审批 | 改表结构可能有合理场景（数据迁移），但需确认 |
| CREATE DATABASE | 不给开口 | Runner 不是 DBA |
| **知识库** | | |
| 删自己的 Wiki 文档（user 级） | 不审批 | 自己的，没共享 |
| 删自己的 Wiki 文档（已共享到 org/system） | 需要审批 | 自己的，但别人在用 |
| 删别人的 Wiki 文档 | 不给开口 | 不是你的 |
| 清空/重建向量索引 | 不给开口 | 系统基础设施 |
| 删除 Wiki 空间 | 不给开口 | 系统基础设施 |
| **Skill** | | |
| 删自己的 Skill（user 级） | 不审批 | 自己的，没共享 |
| 删自己的 Skill（已审批成 org/system 级） | 需要审批 | 自己的，但别人在用 |
| 删别人的 Skill | 不给开口 | 不是你的 |
| **Agent** | | |
| 删自己的 Agent（私有） | 不审批 | 自己的 |
| 删自己的 Agent（已共享） | 需要审批 | 自己的，但别人在用 |
| 删别人的 / 系统级 Agent | 不给开口 | 不是你的 / 系统原生 |
| **平台数据** | | |
| 删除用户/账号 | 不给开口 | 纯管理操作 |
| 删除组织 | 不给开口 | 纯管理操作 |
| 修改 RBAC 权限/角色 | 不给开口 | 纯管理操作 |
| **系统配置** | | |
| 修改 LLM API Key / 模型配置 | 不给开口 | 纯管理操作 |
| 修改系统设置 | 不给开口 | 纯管理操作 |
| **代码** | | |
| git push（正常） | 不审批 | 正常开发流程 |
| git force push 到主分支 | 需要审批 | push 正常，force 要确认 |

### 实现方式总结

```python
# 伪代码
def check_permission(runner, operation, resource):
    # 数据库操作：统一视为共享资源
    if operation.target == "database":
        if operation in (DROP_DATABASE, CREATE_DATABASE):
            return BLOCK  # 不给开口
        if operation in (DROP_TABLE, TRUNCATE, ALTER_DROP):
            return APPROVAL_REQUIRED  # 需要审批

    # 资源操作：看所有权 + scope
    if resource.owner == runner.user_id:
        if resource.scope == "user":
            return ALLOW  # 自己的，没共享，直接放行
        else:
            return APPROVAL_REQUIRED  # 自己的，已共享，需审批
    else:
        if operation.is_destructive:
            return BLOCK  # 别人的，不给开口
        return ALLOW  # 读操作可以放行
```

---

## 决策标记

| 标记 | 含义 |
|------|------|
| ✅ 缺，应该补 | 功能是刚需，PioneClaw 当前缺失 |
| ⬜ 缺，有条件补 | 取决于是否使用某能力（如连数据库） |
| 🔧 缺，不紧急 | 有更好，但 P3 优先级 |
| ❌ 缺，不需要 | CircleBot 的企业/商用功能，PioneClaw 用不上 |

---

## 一、安全相关

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| 命令审批中心 | Agent 执行命令前需审批（auto/plan/bubble 三级） | ❌ | CircleBot 是 Center 管控 Runner 的思路。PioneClaw 原则：Runner 动自己电脑自己负责，安全网用 Plan 模式 + 确认弹窗防 LLM 幻觉即可，不需要 Center 对 Runner 的审批链 |
| 数据库高危操作审批 | DROP/TRUNCATE/ALTER DROP/CREATE DATABASE 需 Center 审批 | ✅ | 数据库是共享的，不属于 Runner。一句话删库不可逆，Center 必须审批。详见上方高危操作表 |
| 共享资源高危操作审批（Wiki/Agent/Skill/平台数据） | 删除系统级 Wiki/Agent/Skill、删除用户、清空向量索引等需 Center 审批 | ✅ | 同上逻辑：这些东西是系统/组织共享的，动了影响所有人。CircleBot 没有集中做这块，但原理一致 |
| 数据源读写分级 | read_only / allow_dml / allow_ddl / allow_destructive 四级 | ⬜ | 连了数据库就必做。大部分时候 Agent 只需要查，写操作显式授权更安全 |
| 数据操作审计记录 | 谁、什么时间、执行了什么 SQL、结果 | ⬜ | 同上，连了数据库就需要追溯 |
| Runner Token 轮换 | 定期更换 Runner 认证凭据 | 🔧 | 自己连自己，Token 泄露风险远低于企业多用户。但保留轮换能力没坏处 |
| Runner 接入审批 | 新 Runner 注册需管理员审批 | 🔧 | PioneClaw 已有 pending/approve/reject 基础。个人用不会有陌生 Runner 接入，保留即可 |
| 角色数据源白名单 | 不同角色只能访问分配的数据源 | ❌ | 企业多角色场景。个人部署一个用户就是所有角色 |
| UI 操作日志 | 记录管理员在 UI 上的关键操作 | ❌ | 企业合规审计需要 |

---

## 二、Runner 运维

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| Runner 诊断信息 | Center 远程查看 Runner 运行环境、配置、资源占用 | ✅ | Runner 可能跑在远程机器上，出问题不能靠走过去看屏幕。CircleBot 的诊断信息面板值得做 |
| Runner 本地日志浏览 | Center 远程拉取和查看 Runner 端日志 | ✅ | Runner 报错时 Center 能直接看到日志，不需要 SSH 或截图。CircleBot 有按分类筛选，可以参考 |
| Runner 连接事件时间线 | 记录 Runner 上下线/断开的事件历史 | 🔧 | 排查"Runner 为什么断了"时有用，但优先级低于日志和诊断 |
| Runner 版本管理 | 上传安装包、设置最新版、客户端检查更新 | ❌ | 企业管控几百个 Runner 版本一致性才需要，自己手动更新即可 |

---

## 三、Wiki 知识库

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| Wiki Lint 检查 | 自动检查断链、缺失引用 | ✅ | Wiki 是 Agent RAG 的知识来源。CircleBot 的 Lint 不只是格式美化——断链意味着 Agent 检索到空内容 |
| Wiki 修改审批 | Wiki 被编辑后需审批才生效 | ✅ | 防止 Agent 批量写入错误信息直接生效。PioneClaw 已有 Approval 体系，加一个 WIKI_MODIFICATION 类型即可 |
| 从对话捕获 Wiki | 聊天中提取知识点一键存入 Wiki | ✅ | CircleBot 的 `capture_from_chat` 端点。记忆沉淀最自然的入口 |
| 素材源管理 | 粘贴 URL/文本自动提取内容索引到 Wiki | 🔧 | 经常收集外部资料就实用 |
| Wiki Dream 自动维护 | 夜间自动 lint + 反向链接更新 + 同步 + 提取 | 🔧 | CircleBot 有 `wiki_dream` 定时任务。手动 Lint 够用后再考虑自动化 |
| Wiki 导出 | 将 Wiki 空间或文档导出为文件 | 🔧 | 低频操作 |
| Schema 强制执行 | 定义文档必须包含哪些章节 | ❌ | 企业知识管理才需要 |
| 索引任务管理 | 异步查看/应用/取消 Wiki 向量索引 | 🔧 | 大规模文档才需要，PioneClaw 现有索引是同步的 |
| Wiki 空间隔离 | 用户级/组织级独立 Wiki 空间 | ❌ | PioneClaw 已有 scope 三级权限，不需要额外空间层 |

---

## 四、记忆系统

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| Agent 记忆提升 | Agent 产生的记忆提升为用户长期记忆 | 🔧 | CircleBot 的 `promote` 端点。减少手动整理 |
| 每日摘要 | 自动生成每天对话摘要 | 🔧 | CircleBot 有 `daily_summaries` 定时任务。习惯回顾就有用 |
| 组织共享记忆 | 组织级别的共享记忆库 | ❌ | 多人共用才需要 |
| Dream 智能整理仪表盘 | 可视化记忆自动整理进度/审核 | ❌ | 企业展示功能 |
| 记忆置顶/归档 | Pin/Archive 管理记忆生命周期 | 🔧 | CircleBot 四个记忆子模块都有 pin/archive。记忆多了有用 |

---

## 五、工作任务

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| 任务依赖关系 | 前置依赖检查（如"部署"依赖"测试通过"） | ✅ | 没有依赖链的任务管理只是 Todo List |
| 任务模板 | 预定义结构，一键创建 | 🔧 | 重复性任务多就实用 |
| AI 建议拆分 | AI 分析大任务建议如何拆分 | 🔧 | 锦上添花 |
| AI 建议指派 | AI 分析任务推荐执行人 | ❌ | 单人不需要 |
| 任务语义搜索 | 自然语言搜索任务 | 🔧 | 任务多了有用 |
| 工作量视图 | 成员工作负载分布 | ❌ | 管理者视角 |
| 批量排序 | 拖拽调整优先级 | ❌ | 小规模不需要 |

---

## 六、数据管理

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| SQL 数据源管理 | 连接外部关系型数据库，Agent 直接查业务数据 | ⬜ | 看是否让 Agent 连数据库 |
| 数据目录 | 自动扫描表结构生成数据集/字段目录 | ❌ | 企业几百张表才需要 |
| 数据同步任务 | 定时同步外部数据源元数据 | ❌ | 同上 |

---

## 七、通道与消息

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| 通道管理 UI | 可视化配置/启用/禁用通道 | ❌ | 企业运营钉钉/企微/飞书通道才需要 UI。PioneClaw 有代码级适配器够用 |
| 钉钉 Stream 状态/重连 | 钉钉长连接管理 | ❌ | 企业 IM |
| 通道投递列表 | 查看哪些通道可用于消息投递 | ❌ | 同上 |

---

## 八、模型与资源

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| LLM 用量分析面板 | Token 消耗汇总、调用日志、按小时趋势 | 🔧 | CircleBot 的 `llm/usage/*` 端点。API 是花钱的，可视化面板对成本控制有帮助 |
| 多级模型调用队列 | 默认/标准/高级三级队列 + 成员管理 | ❌ | 多用户争抢 LLM 资源才需要 |
| 模型代理（chat/vl/embed/image） | 统一的模型调用网关 | 🔧 | PioneClaw 已有 provider 系统，功能接近 |

---

## 九、平台与系统

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| 执行监控面板 | Agent 执行记录、Skill 调用日志、运行中任务管理 | 🔧 | CircleBot 的 `monitor/*` 端点。PioneClaw 有 dashboard + tracing，完善即可 |
| 系统设置分组 | 按分组（LLM/安全/品牌）管理设置，含描述 | 🔧 | 设置多以后有用 |
| 品牌定制 | 自定义 Logo/名称/配色 | ❌ | 面向客户才需要 |
| 外部应用 + SSO | 对接第三方应用、单点登录 | ❌ | 企业 OA/邮箱集成 |
| License 管理 | 商业授权激活、到期、Runner 上限控制 | ❌ | 不商用 |

---

## 十、Skill 生态

| CircleBot 有的 | 作用 | 决策 | 原因 |
|---------------|------|------|------|
| Skill 上架审核 | 用户提交 Skill 到组织/系统级需审核 | 🔧 | 复用 Approval，多人协作就需要 |
| Local Skill 分享 | 用户分享 Skill 给指定用户 | 🔧 | 有分享需求就做 |
| Skill 审核队列 | 待审核 Skill 列表、审核操作 | 🔧 | 同上 |

---

## 汇总

### 按决策统计

| 决策 | 数量 | 功能 |
|------|------|------|
| ✅ 缺，应该补 | 9 | 三道安全防线、数据库高危审批、Runner 诊断、Runner 日志、Wiki Lint、Wiki 修改审批、对话捕获 Wiki、任务依赖 |
| ⬜ 有条件补 | 3 | 数据源读写分级、数据审计、SQL 数据源管理 |
| 🔧 缺，不紧急 | 18 | Token 轮换、连接事件、接入审批、Wiki 素材源/Dream/导出/索引任务、记忆提升/摘要/置顶归档、任务模板/AI拆分/语义搜索、LLM 面板、模型代理、执行监控、设置分组、Skill 审核/分享 |
| ❌ 缺，不需要 | 23 | 命令审批中心、角色白名单、UI 操作日志、Runner 版本管理、Wiki Schema/空间、组织记忆、Dream 面板、AI 指派、工作量/批量排序、数据目录/同步、通道 UI/钉钉/投递、模型队列、品牌、SSO、License |

### 建议开发顺序

```
P0：三道安全防线（不给开口 + 需要审批 + 直接放行）—— 平台安全基础，必须先做
P1：Runner 诊断 + 日志、Wiki Lint、Wiki 修改审批、任务依赖、对话捕获 Wiki
P2：操作审计、Token 轮换、连接事件、LLM 面板、Agent 记忆提升、任务模板
P3：其余 🔧
```
