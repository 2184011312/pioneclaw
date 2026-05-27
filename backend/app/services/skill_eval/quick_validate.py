"""Quick validation for SKILL.md frontmatter — adapted from skill-creator.

Validates YAML frontmatter structure and content against PioneClaw conventions.
"""

import re
from pathlib import Path


def validate_skill(skill_path: Path) -> tuple[bool, str, list[dict]]:
    """Validate a skill directory.

    Returns (is_valid, message, checks) where checks is a list of dicts:
      {"check": str, "passed": bool, "score": int, "max_score": int, "detail": str}
    """
    skill_path = Path(skill_path)
    checks: list[dict] = []

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        checks.append(_mk_check("SKILL.md 存在", False, 0, 5, "未找到"))
        return False, "SKILL.md not found", checks
    checks.append(_mk_check("SKILL.md 存在", True, 5, 5, "通过"))

    # Read content
    content = skill_md.read_text(encoding="utf-8")

    # Check frontmatter exists
    if not content.startswith("---"):
        checks.append(_mk_check("YAML frontmatter", False, 0, 10, "无 frontmatter"))
        return False, "No YAML frontmatter found", checks

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        checks.append(_mk_check("YAML frontmatter", False, 0, 10, "格式错误"))
        return False, "Invalid frontmatter format", checks

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter (simple line-based parser for validation)
    try:
        frontmatter = _simple_yaml_parse(frontmatter_text)
    except Exception as e:
        checks.append(_mk_check("YAML frontmatter", False, 0, 10, f"解析失败: {e}"))
        return False, f"Invalid YAML in frontmatter: {e}", checks

    if not isinstance(frontmatter, dict):
        checks.append(_mk_check("YAML frontmatter", False, 0, 10, "frontmatter 必须是字典"))
        return False, "Frontmatter must be a YAML dictionary", checks

    checks.append(_mk_check("YAML frontmatter", True, 10, 10, "格式正确"))

    # Define allowed properties (PioneClaw conventions)
    ALLOWED_PROPERTIES = {
        "name", "title", "description", "license", "tags", "always",
        "compatibility", "install", "metadata", "dependencies",
    }

    # Check for unexpected properties
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        checks.append(_mk_check(
            "frontmatter 字段合规",
            False, 0, 5,
            f"意外字段: {', '.join(sorted(unexpected_keys))}",
        ))
    else:
        checks.append(_mk_check("frontmatter 字段合规", True, 5, 5, "通过"))

    # Check name/title (at least one required)
    name = frontmatter.get("name", "")
    title = frontmatter.get("title", "")
    if not name and not title:
        checks.append(_mk_check("name/title 必填", False, 0, 10, "缺失"))
    else:
        identifier = name or title
        details: list[str] = []
        score = 10

        # kebab-case or reasonable format
        if re.match(r"^[a-z0-9-]+$", identifier):
            details.append("✓ kebab-case")
        elif re.match(r"^[一-龥a-zA-Z0-9_-]+$", identifier):
            details.append("✓ 有效格式")
        else:
            details.append(f"✗ 格式异常: {identifier}")
            score -= 3

        # length
        if len(identifier) <= 64:
            details.append("✓ ≤64字符")
        else:
            details.append(f"✗ 超长({len(identifier)}字符)")
            score -= 3

        # no consecutive hyphens or edge hyphens
        if identifier.startswith("-") or identifier.endswith("-") or "--" in identifier:
            details.append("✗ 连字符位置异常")
            score -= 2
        else:
            details.append("✓ 连字符位置正常")

        checks.append(_mk_check("name/title 必填", score >= 7, score, 10, "; ".join(details)))

    # Check description
    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        description = ""
    description = description.strip()

    desc_score = 0
    desc_details: list[str] = []
    if not description:
        desc_details.append("✗ 缺失")
    else:
        desc_score = 10
        desc_details.append("✓ 存在")
        if "<" in description or ">" in description:
            desc_details.append("✗ 含尖括号")
            desc_score -= 5
        else:
            desc_details.append("✓ 无尖括号")
        if len(description) > 1024:
            desc_details.append(f"✗ 超长({len(description)}字符)")
            desc_score -= 5
        else:
            desc_details.append(f"✓ ≤1024字符({len(description)})")

    checks.append(_mk_check("description 合规", desc_score >= 6, desc_score, 10, "; ".join(desc_details)))

    # Validate compatibility if present
    compatibility = frontmatter.get("compatibility", "")
    if compatibility:
        if not isinstance(compatibility, str):
            checks.append(_mk_check("compatibility 类型", False, 0, 5, "必须是字符串"))
        elif len(compatibility) > 500:
            checks.append(_mk_check("compatibility 类型", False, 0, 5, f"超长({len(compatibility)}字符)"))
        else:
            checks.append(_mk_check("compatibility 类型", True, 5, 5, "通过"))
    else:
        checks.append(_mk_check("compatibility 类型", True, 5, 5, "可选字段，未设置"))

    total_score = sum(c["score"] for c in checks)
    max_score = sum(c["max_score"] for c in checks)
    passed = all(c["passed"] for c in checks)

    return passed, f"{total_score}/{max_score}", checks


def _mk_check(check: str, passed: bool, score: int, max_score: int, detail: str) -> dict:
    return {"check": check, "passed": passed, "score": score, "max_score": max_score, "detail": detail}


def _simple_yaml_parse(text: str) -> dict:
    """Simple line-based YAML parser for flat key-value frontmatter."""
    result: dict[str, str] = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line or line.strip().startswith("#"):
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        # Handle inline list like tags: [a, b, c]
        if value.startswith("[") and not value.endswith("]"):
            parts = [value]
            i += 1
            while i < len(lines) and not lines[i].strip().endswith("]"):
                parts.append(lines[i].strip())
                i += 1
            if i < len(lines):
                parts.append(lines[i].strip())
            value = " ".join(parts)

        # Handle multiline (> or |)
        if value in (">", "|",">-", "|-"):
            i += 1
            continuation: list[str] = []
            while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t") or lines[i].strip() == ""):
                if lines[i].strip():
                    continuation.append(lines[i].strip())
                i += 1
            value = " ".join(continuation)
            result[key] = value
            continue

        result[key] = value.strip('"').strip("'")
        i += 1
    return result
