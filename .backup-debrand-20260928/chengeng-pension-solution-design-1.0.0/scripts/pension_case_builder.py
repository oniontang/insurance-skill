#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build pension_case.json from simple Markdown / text collection sheets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FIELD_MAP = {
    "客户称呼": ("clientProfile", "customerName"),
    "客户姓名": ("clientProfile", "customerName"),
    "姓名": ("clientProfile", "customerName"),
    "性别": ("clientProfile", "gender"),
    "当前年龄": ("clientProfile", "currentAge"),
    "年龄": ("clientProfile", "currentAge"),
    "家庭结构": ("clientProfile", "familyStructure"),
    "社保缴纳地": ("clientProfile", "socialCity"),
    "参保地": ("clientProfile", "socialCity"),
    "计划退休地": ("clientProfile", "retirementCity"),
    "退休地": ("clientProfile", "retirementCity"),
    "当前月收入": ("clientProfile", "monthlyIncome"),
    "月收入": ("clientProfile", "monthlyIncome"),
    "社保缴费基数": ("clientProfile", "contributionBase"),
    "缴费基数": ("clientProfile", "contributionBase"),
    "已缴社保年限": ("clientProfile", "contributedYears"),
    "已缴年限": ("clientProfile", "contributedYears"),
    "社保个人账户余额": ("clientProfile", "personalAccountBalance"),
    "计划退休年龄": ("clientProfile", "retirementAge"),
    "退休年龄": ("clientProfile", "retirementAge"),
    "预期寿命": ("clientProfile", "expectedLongevity"),
    "退休生活标准": ("assumptionsInput", "targetTier"),
    "退休后居住方式": ("assumptionsInput", "livingStyle"),
    "最担心的问题": ("assumptionsInput", "topConcern"),
    "专门养老资金": ("sourceAndGapInput", "currentRetirementAssets"),
    "当前存款余额": ("sourceAndGapInput", "savings"),
    "约定留到退休的存款": ("sourceAndGapInput", "savingsHeldToRetirement"),
    "当前基金": ("sourceAndGapInput", "funds"),
    "计划持有到退休的基金金额": ("sourceAndGapInput", "fundsHeldToRetirement"),
    "明确留到退休的理财产品": ("sourceAndGapInput", "wealthProducts"),
    "退休时可兑现的保单现金价值": ("sourceAndGapInput", "policyCashValue"),
    "企业年金": ("sourceAndGapInput", "enterpriseAnnuityMonthly"),
    "职业年金": ("sourceAndGapInput", "occupationalPensionMonthly"),
    "个人养老金": ("sourceAndGapInput", "personalPensionMonthly"),
    "其他确定性收入": ("sourceAndGapInput", "otherGuaranteedMonthlyIncome"),
    "退休后可实现月租金收入": ("sourceAndGapInput", "propertyRentalIncomeMonthly"),
    "每年计划新增投入": ("assumptionsInput", "annualContribution"),
    "退休前回报率": ("assumptionsInput", "preRetirementReturnRate"),
    "退休后回报率": ("assumptionsInput", "postRetirementReturnRate"),
    "房产总估值": ("sourceAndGapInput", "propertyMarketValue"),
    "退休前计划变现的房产净额": ("sourceAndGapInput", "propertyRetirementSellableValue"),
}

SELECT_MAP = {
    "男": "male",
    "男性": "male",
    "女": "female",
    "女性": "female",
    "基本生活": "basic",
    "体面生活": "comfort",
    "品质生活": "premium",
    "舒适": "comfort",
    "舒适养老": "comfort",
    "基础": "basic",
    "养老底线": "basic",
    "服务型": "premium",
    "服务型退休": "premium",
    "自有住房": "self_owned",
    "租房": "rent",
    "养老社区": "community",
    "钱不够": "money_shortage",
    "病太久": "long_illness",
    "失能照护": "disability_care",
    "身后留钱": "leave_legacy",
    "传承": "leave_legacy",
}


def parse_amount(value: str) -> Any:
    raw = str(value or "").strip()
    if not raw:
        return ""
    for key, mapped in SELECT_MAP.items():
        if key in raw:
            return mapped
    if "未知" in raw or "暂时未知" in raw:
        return ""
    numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", raw)
    if not numbers:
        return raw
    num = float(numbers[0].replace(",", ""))
    if "万" in raw and num < 10000:
        num *= 10000
    if num.is_integer():
        return int(num)
    return num


def normalize_label(label: str) -> str:
    return re.sub(r"[\s*#|：:（）()/_-]+", "", label.strip())


def parse_lines(text: str) -> dict[str, Any]:
    case: dict[str, Any] = {
        "clientProfile": {},
        "assumptionsInput": {},
        "sourceAndGapInput": {},
    }
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("|").strip()
        if not line or set(line.replace("|", "").replace("-", "").replace(" ", "")) == set():
            continue
        parts = [p.strip() for p in re.split(r"\s*\|\s*", line) if p.strip()]
        if len(parts) >= 2 and parts[0] not in {"字段", "项目", "资产类型"}:
            label, value = parts[0], parts[1]
        elif ":" in line or "：" in line:
            label, value = re.split(r"[:：]", line, maxsplit=1)
        else:
            continue
        normalized = normalize_label(label)
        for alias, target in FIELD_MAP.items():
            if normalize_label(alias) == normalized:
                section, key = target
                case[section][key] = parse_amount(value)
                break
    return case


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pension case JSON from Markdown or text.")
    parser.add_argument("input", help="Input Markdown/text file.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()
    text = Path(args.input).read_text(encoding="utf-8")
    case = parse_lines(text)
    Path(args.out).write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
