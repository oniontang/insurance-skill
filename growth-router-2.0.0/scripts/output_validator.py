#!/usr/bin/env python3
"""Validate onboarding and single-skill routing output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RISK_PHRASES = ("保证成交", "一定理赔", "确定核保", "保证收益")
NON_ROUTED_SLUGS = ("bazi-work-rhythm-advisor",)


def load_catalog(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*([^|`]+?)\s*\|\s*`([a-z0-9\-]+)`\s*\|", line)
        if not match:
            continue
        name, slug = match.group(1).strip(), match.group(2)
        if name == "对外名称" or slug in NON_ROUTED_SLUGS:
            continue
        names.add(name)
    return names


def extract_primary_skills(text: str) -> list[str]:
    matches = re.findall(r"(?:主 Skill|目标 Skill)[：:]\s*([^\n]+)", text)
    cleaned = []
    for match in matches:
        value = match.strip().strip("-*` ").split("，", 1)[0].strip()
        cleaned.append(value)
    return cleaned


def detect_mode(text: str, requested_mode: str) -> str:
    if requested_mode != "auto":
        return requested_mode
    if "主 Skill" in text or "目标 Skill" in text:
        return "routing"
    if "暂无对应 Skill" in text or "线上匹配：暂无" in text:
        return "no_match"
    if "你可以直接" in text and "现在" in text:
        return "onboarding"
    return "routing"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="Markdown output file")
    parser.add_argument("--mode", choices=("auto", "onboarding", "routing", "no_match"), default="auto")
    parser.add_argument("--catalog", help="Path to skill-catalog.md")
    args = parser.parse_args()

    output_path = Path(args.output)
    text = output_path.read_text(encoding="utf-8")
    mode = detect_mode(text, args.mode)
    catalog_path = Path(args.catalog) if args.catalog else Path(__file__).resolve().parents[1] / "references" / "skill-catalog.md"
    catalog = load_catalog(catalog_path)

    missing_blocks: list[str] = []
    invalid_skills: list[str] = []
    primary_skills = extract_primary_skills(text)

    if mode == "onboarding":
        for block in ("你可以直接", "不用先判断", "现在"):
            if block not in text:
                missing_blocks.append(block)
    elif mode == "no_match":
        for block in ("当前判断", "暂无对应 Skill", "当前需求", "原因", "下一步"):
            if block not in text:
                missing_blocks.append(block)
    else:
        for block in ("当前判断", "主 Skill", "判断依据", "下一步"):
            if block not in text:
                missing_blocks.append(block)
        if len(primary_skills) != 1:
            missing_blocks.append("exactly_one_primary_skill")
        invalid_skills = [name for name in primary_skills if name not in catalog]
        handoff_markers = ("直接沿用", "交接卡", "交给「", "打开「")
        if not any(marker in text for marker in handoff_markers):
            missing_blocks.append("handoff_method")

    risk_hits = [phrase for phrase in RISK_PHRASES if phrase in text]
    passed = not missing_blocks and not invalid_skills and not risk_hits
    result = {
        "status": "pass" if passed else "retry",
        "mode": mode,
        "primarySkills": primary_skills,
        "missingBlocks": missing_blocks,
        "invalidSkills": invalid_skills,
        "riskHits": risk_hits,
        "nextAction": "accept_output" if passed else "rewrite_with_single_valid_skill_and_handoff",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
