#!/usr/bin/env python3
"""Preflight mode detection for the Chen Geng Super Insurance entry skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ONBOARDING_PHRASES = ("第一次使用", "怎么开始", "教我使用", "新手入门")
NEXT_STEP_PHRASES = ("下一步", "接下来做什么", "然后呢", "做完了")
SYSTEM_PHRASES = ("完整体系", "六环节", "增长地图", "理论体系")
ENTRY_NAMES = ("陈庚-超级保险人", "陈庚-增长路由")
RISK_PHRASES = (
    "保证成交",
    "一定理赔",
    "确定核保",
    "替代医生",
    "替代律师",
    "保证收益",
    "编造案例",
    "虚构数据",
)


def load_payload(path: str | None) -> dict:
    if path:
        raw = Path(path).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"task": value}
    except json.JSONDecodeError:
        return {"task": raw}


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False)


def joined_text(payload: dict) -> str:
    return "\n".join(as_text(value) for value in payload.values() if as_text(value))


def find_named_skill(text: str) -> str:
    matches = re.findall(r"陈庚-[A-Za-z0-9\u4e00-\u9fff～-]+", text)
    for match in matches:
        cleaned = match.rstrip("，。；：、")
        if cleaned not in ENTRY_NAMES:
            return cleaned
    return ""


def detect_mode(payload: dict, requested_mode: str) -> tuple[str, str]:
    text = joined_text(payload)
    named_skill = as_text(payload.get("named_skill")) or find_named_skill(text)

    if requested_mode != "auto":
        return requested_mode, named_skill
    if named_skill:
        return "direct_skill", named_skill
    if any(phrase in text for phrase in ONBOARDING_PHRASES) or not text:
        return "onboarding", ""
    if as_text(payload.get("previous_result")) or as_text(payload.get("已有 Skill 结果")):
        return "post_task", ""
    if any(phrase in text for phrase in NEXT_STEP_PHRASES):
        return "post_task", ""
    if any(phrase in text for phrase in SYSTEM_PHRASES):
        return "system_overview", ""
    return "pre_task", ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON file with conversation context")
    parser.add_argument(
        "--mode",
        choices=("auto", "onboarding", "pre_task", "post_task", "system_overview", "direct_skill"),
        default="auto",
    )
    args = parser.parse_args()

    payload = load_payload(args.input)
    text = joined_text(payload)
    mode, named_skill = detect_mode(payload, args.mode)
    risk_hits = [phrase for phrase in RISK_PHRASES if phrase in text]

    if risk_hits:
        status = "needs_review"
        next_action = "remove_guarantees_and_preserve_professional_boundary"
    elif mode == "onboarding":
        status = "onboarding_ready"
        next_action = "show_short_onboarding_and_accept_real_task"
    elif mode == "direct_skill":
        status = "direct_skill"
        next_action = "respect_named_skill_and_do_not_reroute"
    elif mode == "system_overview":
        status = "ready"
        next_action = "handoff_to_chengeng_growth_system"
    elif text:
        status = "ready"
        next_action = "select_one_primary_skill_and_handoff"
    else:
        status = "needs_more_info"
        next_action = "ask_one_route_changing_question"

    required_blocks = {
        "onboarding": ["what_user_can_send", "how_routing_works", "start_now"],
        "direct_skill": ["named_skill", "reuse_context"],
        "pre_task": ["current_judgement", "primary_skill", "basis", "next_step"],
        "post_task": ["previous_result", "primary_skill", "basis", "next_step"],
        "system_overview": ["primary_skill", "handoff"],
    }[mode]

    result = {
        "status": status,
        "mode": mode,
        "namedSkill": named_skill,
        "riskHits": risk_hits,
        "nextAction": next_action,
        "maxClarifyingQuestions": 1,
        "maxPrimarySkills": 1,
        "requiredOutputBlocks": required_blocks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 3 if status == "needs_review" else 0


if __name__ == "__main__":
    raise SystemExit(main())
