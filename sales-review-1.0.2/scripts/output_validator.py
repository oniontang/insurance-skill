#!/usr/bin/env python3
"""Validate a Markdown output against required skill blocks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_BLOCKS = ["输入校验", "一句话判断", "依据", "下一步", "边界"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", help="Markdown output file")
    parser.add_argument("--required", nargs="*", default=DEFAULT_BLOCKS)
    args = parser.parse_args()
    text = Path(args.output).read_text(encoding="utf-8") if args.output else ""
    missing = [block for block in args.required if block not in text]
    result = {
        "status": "pass" if not missing else "retry",
        "missingBlocks": missing,
        "nextAction": "accept_output" if not missing else "rewrite_with_required_blocks",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
