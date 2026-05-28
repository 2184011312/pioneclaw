"""Comparator prompt builder — blind A/B output comparison.

Builds an LLM prompt that compares two skill execution outputs (A and B)
without knowing which skill produced which. Uses Content + Structure rubric
for objective scoring. Extracted from skill-creator comparator.md agent logic.
"""


def build_comparator_prompt(
    output_a: str,
    output_b: str,
    eval_prompt: str = "",
    expectations: list[str] | None = None,
) -> str:
    """Build blind A/B comparison prompt using Content+Structure rubric.

    The prompt instructs the LLM to:
    1. Compare outputs A and B (blind - no skill info)
    2. Score each on Content rubric: correctness(1-5), completeness(1-5), accuracy(1-5)
    3. Score each on Structure rubric: organization(1-5), formatting(1-5), usability(1-5)
    4. Calculate content_score, structure_score, overall_score (1-10)
    5. Declare winner: "A", "B", or "TIE"
    6. Return JSON matching ComparisonResult schema
    """
    if expectations is None:
        expectations = []

    eval_section = ""
    if eval_prompt:
        eval_section = f"""## 原始评估任务

{eval_prompt}

"""

    expectations_section = ""
    if expectations:
        exp_text = "\n".join(f"- {e}" for e in expectations)
        expectations_section = f"""## 期望检查清单

{exp_text}

"""

    return f"""你是一个盲比评估专家。你将看到两个版本的输出（A 和 B），但你不必知道哪个 skill 产生了哪个输出。请基于输出质量和任务完成度做出客观判断。

## 背景

盲比（Blind Comparison）的核心原则：
- 你不知道 A 和 B 分别来自哪个 skill 或版本
- 你的判断纯粹基于输出质量和任务完成度
- 不要试图推断 A 或 B 的来源，只关注输出本身

{eval_section}## 输出 A

```
{output_a}
```

## 输出 B

```
{output_b}
```
{expectations_section}
## 评估 Rubric

### 内容 Rubric（Content — 输出包含什么）

| 评分标准 | 1（差） | 3（可接受） | 5（优秀） |
|---------|--------|-----------|---------|
| **正确性 (correctness)** | 存在重大错误 | 存在小错误 | 完全正确 |
| **完整性 (completeness)** | 缺失关键元素 | 大部分完整 | 所有元素齐全 |
| **准确性 (accuracy)** | 明显不准确 | 轻微不准确 | 整体准确 |

### 结构 Rubric（Structure — 输出如何组织）

| 评分标准 | 1（差） | 3（可接受） | 5（优秀） |
|---------|--------|-----------|---------|
| **组织性 (organization)** | 混乱无章 | 基本合理 | 逻辑清晰、结构分明 |
| **格式化 (formatting)** | 不一致/错误 | 大部分一致 | 专业规范 |
| **可用性 (usability)** | 难以使用 | 需要努力才能用 | 直接可用 |

### 评分规则
- 每个标准打分 1-5 分（整数）
- content_score = (correctness + completeness + accuracy) / 3，保留 1 位小数
- structure_score = (organization + formatting + usability) / 3，保留 1 位小数
- overall_score = ((content_score + structure_score) / 2) * 2，映射到 1-10 范围，保留 1 位小数
- 胜者判断：overall_score 高者胜出；相等则 TIE

## 评估要求

1. **先理解任务**：阅读 eval_prompt，理解任务要求和评判标准
2. **独立评分**：先独立评估 A，再独立评估 B，不要互相比较后再打分
3. **客观公正**：基于事实证据，不因格式偏好或个人倾向影响判断
4. **具体举例**：在 reasoning 和 quality 字段中引用具体的输出内容
5. **果断判断**：能分出高下就不要选 TIE；TIE 仅在两个输出确实等同时使用

## 输出格式

请严格输出以下 JSON 结构，它必须符合 ComparisonResult schema 的定义（不要用 markdown 代码块包裹，直接输出纯 JSON）：

{{
  "winner": "A|B|TIE",
  "reasoning": "<清楚说明为什么胜者胜出或为什么平局>",
  "rubric": {{
    "A": {{
      "correctness": <1-5 整数>,
      "completeness": <1-5 整数>,
      "accuracy": <1-5 整数>,
      "organization": <1-5 整数>,
      "formatting": <1-5 整数>,
      "usability": <1-5 整数>,
      "content_score": <(correctness+completeness+accuracy)/3, 保留1位小数>,
      "structure_score": <(organization+formatting+usability)/3, 保留1位小数>,
      "overall_score": <映射到1-10, 保留1位小数>
    }},
    "B": {{
      "correctness": <1-5 整数>,
      "completeness": <1-5 整数>,
      "accuracy": <1-5 整数>,
      "organization": <1-5 整数>,
      "formatting": <1-5 整数>,
      "usability": <1-5 整数>,
      "content_score": <(correctness+completeness+accuracy)/3, 保留1位小数>,
      "structure_score": <(organization+formatting+usability)/3, 保留1位小数>,
      "overall_score": <映射到1-10, 保留1位小数>
    }}
  }},
  "output_quality": {{
    "A": {{
      "score": <1-10 整数, 应等于rubric中的overall_score取整>,
      "strengths": ["<优点1>", "<优点2>", "..."],
      "weaknesses": ["<缺点1>", "<缺点2>", "..."]
    }},
    "B": {{
      "score": <1-10 整数, 应等于rubric中的overall_score取整>,
      "strengths": ["<优点1>", "<优点2>", "..."],
      "weaknesses": ["<缺点1>", "<缺点2>", "..."]
    }}
  }}
}}"""  # noqa: E501
