#!/usr/bin/env python3
"""Retry policy helper for prompt skills.

This does not call a model. It tells the host whether a generated answer should be
accepted, retried, or handed to a human reviewer.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--validator", default="scripts/output_validator.py")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()

    validator = Path(args.validator)
    output = Path(args.output)
    if not output.exists():
        print(json.dumps({"status": "retry", "reason": "output_file_missing"}, ensure_ascii=False))
        return 2

    try:
        completed = subprocess.run(
            [sys.executable, str(validator), str(output)],
            text=True,
            capture_output=True,
            timeout=args.timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "retry", "reason": "validation_timeout"}, ensure_ascii=False))
        return 2

    if completed.returncode == 0:
        print(json.dumps({"status": "pass", "reason": "validator_passed"}, ensure_ascii=False))
        return 0

    if args.attempt < args.max_retries:
        print(json.dumps({"status": "retry", "reason": "required_blocks_missing", "nextAttempt": args.attempt + 1}, ensure_ascii=False))
        return 2

    print(json.dumps({"status": "needs_review", "reason": "retry_limit_reached"}, ensure_ascii=False))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
