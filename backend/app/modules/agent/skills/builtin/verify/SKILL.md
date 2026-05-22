---
title: 验证代码变更
description: 运行测试套件验证代码变更的正确性
tags: [test, verification, quality]
always: false
---

# 验证代码变更

运行相关测试，验证代码变更没有引入回归问题。

## 验证流程

### 1. 检查测试结构

首先了解项目的测试结构：

```
# Python 项目
ls tests/
ls test_*.py

# 检查测试配置
cat pytest.ini 2>/dev/null || cat pyproject.toml 2>/dev/null
```

确认：
- 测试框架（pytest、unittest、jest 等）
- 测试文件位置
- 是否有测试配置（conftest.py、pytest.ini）

### 2. 确定测试范围

根据变更内容确定需要运行的测试：
- 如果变更集中在某个模块 → 只跑该模块的测试
- 如果是跨模块变更 → 跑相关模块的测试
- 如果是核心基础设施变更 → 跑全量测试

**询问用户确认测试范围。**

### 3. 运行测试

```bash
# Python - 单元测试
python -m pytest tests/<target_test_file>.py -v

# Python - 全量测试
python -m pytest tests/ -v

# 带覆盖率
python -m pytest tests/<target>.py -v --cov=app --cov-report=term
```

### 4. 分析结果

检查测试输出：
- 通过的测试数量
- 失败的测试及其原因
- 跳过的测试
- 覆盖率数据（如有）

对每个失败的测试：
1. 读取测试代码，理解测试意图
2. 检查是否与本次变更相关
3. 给出初步诊断：是测试需要更新，还是代码有bug

### 5. 生成报告

```
## 测试验证报告

### 测试范围
- tests/test_xxx.py
- tests/test_yyy.py

### 结果
- 通过: 25
- 失败: 0
- 跳过: 2
- 覆盖率: 85%

### 失败诊断（如有）
- test_xxx: 原因分析 → 建议修复
```

## 重要原则

- 优先跑与变更相关的测试，避免不必要的全量测试
- 对于失败测试，先判断是代码问题还是测试需要更新
- 不要修改测试代码来"让测试通过"，除非确认测试本身有问题
- 如果测试依赖外部服务（数据库、API），确认这些服务可用
