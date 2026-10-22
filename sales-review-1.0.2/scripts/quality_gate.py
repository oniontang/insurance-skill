#!/usr/bin/env python3
"""Lightweight quality gate for WorkBuddy skills.

It checks whether a task has enough context before the model writes a final answer.
The script is optional: when the host cannot run scripts, use the same checks as a
manual preflight list.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_REQUIRED = ["task", "scene", "audience", "materials", "output_target"]
RISK_PHRASES = [
    "保证成交",
    "一定理赔",
    "确定核保",
    "替代医生",
    "替代律师",
    "编造案例",
    "虚构数据",
]


def load_payload(path: str | None) -> dict:
    if path:
        text = Path(path).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read().strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"task": text}


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON file with task context")
    parser.add_argument("--required", nargs="*", default=DEFAULT_REQUIRED)
    args = parser.parse_args()

    payload = load_payload(args.input)
    missing = [key for key in args.required if not as_text(payload.get(key))]
    joined = "\n".join(as_text(v) for v in payload.values())
    risk_hits = [phrase for phrase in RISK_PHRASES if phrase in joined]

    if risk_hits:
        status = "needs_review"
    elif missing:
        status = "needs_more_info"
    else:
        status = "ready"

    result = {
        "status": status,
        "missing": missing,
        "riskHits": risk_hits,
        "nextAction": {
            "ready": "write_final_output_with_quality_check",
            "needs_more_info": "ask_for_missing_fields_or_output_low_confidence_version",
            "needs_review": "stop_final_claims_and_rewrite_with_boundary",
        }[status],
        "requiredOutputBlocks": [
            "input_check",
            "one_sentence_judgement",
            "core_output",
            "basis_and_gap",
            "next_action",
            "boundary",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
