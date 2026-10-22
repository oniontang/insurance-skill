#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline pension planning calculator.

This script is intentionally standalone. It does not call SuperBXR servers and
does not require private databases. The formulas mirror the public planning
logic used by the course package: social pension estimate, lifestyle cashflow,
source inventory, gap sizing, and staged funding advice.
"""

from __future__ import annotations

import argparse
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any


REGION_WAGE_ANCHORS = {
    "北京": 13500,
    "上海": 14000,
    "深圳": 13500,
    "广州": 12000,
    "杭州": 11500,
    "成都": 8426,
    "重庆": 9000,
    "武汉": 9500,
    "西安": 8800,
    "南京": 11000,
    "天津": 9800,
    "default": 10000,
}

REGION_STAT_REFERENCES = {
    "成都": {
        "wageAnchorName": "2024 年成都市全口径城镇单位就业人员平均工资估算",
        "wageAnchorAnnual": 101112.88,
        "wageAnchorMonthly": 8426.07,
        "wageAnchorGrowth": 0.005,
        "nonPrivateWageAnnual": 125512,
        "nonPrivateWageGrowth": 0.001,
        "privateWageAnnual": 68954,
        "privateWageGrowth": 0.017,
        "nonPrivateEmploymentWeight": 0.5688,
        "privateEmploymentWeight": 0.4312,
        "weightBaseYear": 2023,
        "weightMethod": "用 2023 年成都已发布的城镇全部单位、非私营、私营三组平均工资反推非私营与私营就业人员权重；2024 年暂沿用该结构权重，不预测未来人数结构。",
        "allCaliberFormula": "全口径平均工资 = 非私营平均工资 × 非私营人数权重 + 私营平均工资 × 私营人数权重",
        "pensionAccrualBaseName": "养老金计发基数",
        "pensionAccrualBaseMonthly": None,
        "pensionAccrualBaseNote": "当前离线版暂用全口径工资锚点估算。实际退休核定时，应以当地人社部门发布的养老金计发基数为准。",
        "cpiGrowth": 0.0,
        "note": "社保缴费基数口径采用非私营与私营加权后的全口径工资，不单独采用非私营或私营工资。养老金计发基数与缴费基数不是同一个概念，正式核定以当地人社部门公布口径为准。",
        "sources": [
            "国务院办公厅《降低社会保险费率综合方案》（国办发〔2019〕13 号），2019-04-01。",
            "成都市统计局关于发布 2024 年全市城镇单位就业人员年平均工资的公告，2025-07-04。",
            "成都市统计局关于 2023 年全市城镇全部单位就业人员平均工资的公告，2024-06-27。",
            "2024 年成都市国民经济和社会发展统计公报，2025-03-28。",
        ],
        "sourceUrls": [
            "https://fgw.sh.gov.cn/cmsres/b6/b6d1e79b92844c4f96871eba8c806810/313adbe3963278ecb3c7f5542e081563.pdf",
            "https://m.cd.bendibao.com/live/199463.shtm",
            "https://cd.bendibao.com/live/2024627/185762.shtm",
            "https://www.cd12371.com/info/2025/2130789.html",
        ],
    },
    "default": {
        "wageAnchorName": "离线城市工资锚点",
        "wageAnchorAnnual": 120000,
        "wageAnchorMonthly": 10000,
        "wageAnchorGrowth": None,
        "nonPrivateWageAnnual": None,
        "nonPrivateWageGrowth": None,
        "privateWageAnnual": None,
        "privateWageGrowth": None,
        "nonPrivateEmploymentWeight": None,
        "privateEmploymentWeight": None,
        "weightBaseYear": None,
        "weightMethod": "",
        "allCaliberFormula": "全口径平均工资 =（非私营单位工资总额 + 私营单位工资总额）÷（非私营就业人数 + 私营就业人数）",
        "pensionAccrualBaseName": "养老金计发基数",
        "pensionAccrualBaseMonthly": None,
        "pensionAccrualBaseNote": "当前离线版暂用工资锚点估算。实际退休核定时，应以当地人社部门最新口径为准。",
        "cpiGrowth": None,
        "note": "当前使用离线估算锚点。若当地已经发布更新数据，可按最新公开统计数据校准。",
        "sources": [],
        "sourceUrls": [],
    },
}

CITY_MULTIPLIERS = {
    "北京": 1.35,
    "上海": 1.35,
    "深圳": 1.30,
    "广州": 1.20,
    "杭州": 1.15,
    "南京": 1.12,
    "成都": 1.00,
    "重庆": 0.92,
    "武汉": 0.95,
    "西安": 0.90,
    "default": 1.00,
}

PAYOUT_MONTHS = {
    50: 195,
    55: 170,
    60: 139,
    61: 132,
    62: 125,
    63: 117,
    64: 109,
    65: 101,
}

SCENARIOS = {
    "pessimistic": {"label": "悲观", "salary_growth": 0.01, "inflation": 0.03},
    "neutral": {"label": "中性", "salary_growth": 0.03, "inflation": 0.025},
    "optimistic": {"label": "积极", "salary_growth": 0.05, "inflation": 0.02},
}

RETIREMENT_STANDARDS = {
    "basic": {"label": "基本生活", "social_wage_ratio": 0.4},
    "comfort": {"label": "体面生活", "social_wage_ratio": 1.0},
    "premium": {"label": "品质生活", "social_wage_ratio": 2.0},
}

LIFESTYLE_WEIGHTS = [
    ("food", "日常饮食", 0.233, "刚性"),
    ("utilities", "居家水电通讯", 0.042, "刚性"),
    ("medical", "基础医疗与慢病管理", 0.142, "刚性"),
    ("rehab", "体检保健与康复储备", 0.058, "半刚性"),
    ("transport", "日常出行", 0.078, "刚性"),
    ("shopping", "衣物购物与家居用品", 0.097, "半刚性"),
    ("social", "家庭社交与礼金", 0.117, "半刚性"),
    ("leisure", "休闲旅行与学习娱乐", 0.104, "弹性"),
    ("housing", "居住成本", 0.129, "刚性"),
]

STAGE_CASHFLOW_PERIODS = [
    {"key": "active_start", "label": "活力启动", "startAge": 60, "endAge": 64, "state": "刚退休，自主安排多", "pressure": "旅行、兴趣、健康管理"},
    {"key": "active_stable", "label": "活力 / 稳健", "startAge": 65, "endAge": 74, "state": "身体尚可，开始稳健管理", "pressure": "慢病管理、生活便利"},
    {"key": "assisted_transition", "label": "舒心过渡", "startAge": 75, "endAge": 79, "state": "需要适度帮助", "pressure": "适老化、助餐助浴"},
    {"key": "care_start", "label": "安心启动", "startAge": 80, "endAge": 84, "state": "专业照护开始重要", "pressure": "护理、康复、陪护"},
    {"key": "high_care", "label": "高照护", "startAge": 85, "endAge": 89, "state": "照护需求显著上升", "pressure": "长期护理、认知照护"},
    {"key": "late_life", "label": "终末 / 高龄", "startAge": 90, "endAge": 95, "state": "高龄或生命末期", "pressure": "舒缓疗护、医疗照护"},
]

STAGE_EXPENSE_ITEMS = [
    ("food", "日常饮食", 0.233, "刚性", {"active_start": 1.0, "active_stable": 1.03, "assisted_transition": 1.05, "care_start": 1.08, "high_care": 1.10, "late_life": 1.00}),
    ("utilities", "居家水电通讯", 0.042, "刚性", {"active_start": 1.0, "active_stable": 1.02, "assisted_transition": 1.05, "care_start": 1.08, "high_care": 1.10, "late_life": 1.05}),
    ("medical", "基础医疗", 0.090, "刚性", {"active_start": 1.0, "active_stable": 1.25, "assisted_transition": 1.50, "care_start": 1.80, "high_care": 2.10, "late_life": 1.80}),
    ("chronic", "慢病管理", 0.052, "刚性", {"active_start": 0.4, "active_stable": 1.0, "assisted_transition": 1.50, "care_start": 1.90, "high_care": 2.30, "late_life": 2.00}),
    ("rehab", "体检康复", 0.058, "半刚性", {"active_start": 1.0, "active_stable": 1.20, "assisted_transition": 1.60, "care_start": 1.90, "high_care": 2.10, "late_life": 1.60}),
    ("transport", "日常出行", 0.078, "刚性", {"active_start": 1.0, "active_stable": 0.95, "assisted_transition": 0.85, "care_start": 0.65, "high_care": 0.45, "late_life": 0.30}),
    ("shopping", "衣物家居", 0.097, "半刚性", {"active_start": 1.0, "active_stable": 0.95, "assisted_transition": 0.85, "care_start": 0.75, "high_care": 0.65, "late_life": 0.50}),
    ("social", "家庭社交", 0.117, "半刚性", {"active_start": 1.0, "active_stable": 0.95, "assisted_transition": 0.80, "care_start": 0.65, "high_care": 0.50, "late_life": 0.35}),
    ("leisure", "旅行兴趣", 0.104, "弹性", {"active_start": 1.25, "active_stable": 1.00, "assisted_transition": 0.75, "care_start": 0.40, "high_care": 0.20, "late_life": 0.10}),
    ("housing", "居住成本", 0.129, "刚性", {"active_start": 1.0, "active_stable": 1.0, "assisted_transition": 1.10, "care_start": 1.15, "high_care": 1.20, "late_life": 1.10}),
    ("housekeeping", "家政助餐", 0.060, "半刚性", {"active_start": 0.00, "active_stable": 0.00, "assisted_transition": 1.00, "care_start": 1.50, "high_care": 1.80, "late_life": 1.50}),
    ("aging_mod", "适老化改造", 0.040, "半刚性", {"active_start": 0.00, "active_stable": 0.00, "assisted_transition": 1.20, "care_start": 0.70, "high_care": 0.40, "late_life": 0.20}),
    ("longterm_care", "长期护理", 0.180, "刚性", {"active_start": 0.00, "active_stable": 0.00, "assisted_transition": 0.80, "care_start": 2.00, "high_care": 3.00, "late_life": 2.20}),
    ("cognitive", "认知 / 防走失照护", 0.100, "刚性", {"active_start": 0.00, "active_stable": 0.00, "assisted_transition": 0.30, "care_start": 0.80, "high_care": 1.50, "late_life": 1.00}),
    ("palliative", "临终舒缓照护", 0.120, "刚性", {"active_start": 0.00, "active_stable": 0.00, "assisted_transition": 0.00, "care_start": 0.10, "high_care": 0.40, "late_life": 2.50}),
]

EXPENSE_ITEM_REFERENCES = {
    "food": {
        "includes": "一日三餐、基础食材、外出简餐、营养补充。",
        "reason": "饮食是全生命周期刚性支出，年龄增加后金额未必暴涨，但营养要求和便利性会提高。",
        "standard": "以退休起点月预算的基础权重为底，再随阶段做小幅调整。",
        "source": "居民消费分类口径 + 养老咨询预算模型。",
        "review": "您是否长期外食、是否有特殊饮食习惯、是否与子女同住。",
    },
    "utilities": {
        "includes": "水电燃气、物业基础杂费、手机宽带、常用订阅服务。",
        "reason": "维持居家生活的基础费用，不因活动减少而消失。",
        "standard": "按基础权重估算，高龄期考虑居家时间增加。",
        "source": "居家生活固定支出口径 + 养老咨询预算模型。",
        "review": "您的物业费、取暖或制冷成本，是否存在多套房居住成本。",
    },
    "medical": {
        "includes": "门诊、常用药、基础检查、医保外自费小额医疗。",
        "reason": "医疗支出随年龄增长通常上升，是后期现金流的核心压力。",
        "standard": "从活力期开始计入，随稳健期、舒心期和高照护期逐步放大。",
        "source": "健康老龄化规划框架 + 养老咨询压力测试模型。",
        "review": "您的既往症、慢病情况、医保类型和商业医疗险覆盖情况。",
    },
    "chronic": {
        "includes": "血压血糖管理、慢病复诊、长期用药、家庭监测设备。",
        "reason": "慢病管理往往不是一次性大额，而是长期、稳定、不可忽视的支出。",
        "standard": "低龄期低权重，65 岁后按阶段逐步抬升。",
        "source": "健康管理支出口径 + 养老阶段压力测试模型。",
        "review": "您是否已有三高、心脑血管风险或相关家族病史。",
    },
    "rehab": {
        "includes": "体检、康复理疗、运动康复、牙科眼科听力等保健支出。",
        "reason": "它介于医疗和生活品质之间，管理得好可以降低后期大额风险。",
        "standard": "按半刚性支出处理，随年龄上升后再进入平台期。",
        "source": "预防性健康管理口径 + 养老咨询预算模型。",
        "review": "您是否重视体检，是否有长期保健、康复、牙科或眼科需求。",
    },
    "transport": {
        "includes": "公共交通、打车、短途出行、看病往返交通。",
        "reason": "出行需求会从主动活动转向生活便利和就医交通。",
        "standard": "低龄期较高，高龄后主动出行下降。",
        "source": "退休生活行为假设 + 养老阶段模型。",
        "review": "您是否开车，居住地到医院、商圈和公共交通是否便利。",
    },
    "shopping": {
        "includes": "衣物、日用品、小家电、床品、家居消耗品。",
        "reason": "不是核心生存支出，但会影响退休生活体面感。",
        "standard": "低龄期正常计入，高龄后随活动范围收缩下调。",
        "source": "居民消费分类口径 + 养老咨询预算模型。",
        "review": "您的消费习惯，是否承担家庭采购，是否有大件更新计划。",
    },
    "social": {
        "includes": "家庭聚餐、节日礼金、人情往来、兴趣社群支出。",
        "reason": "社交支出关系到心理状态和家庭关系，不宜完全忽略。",
        "standard": "活力期和稳健期正常计入，后期随社交半径缩小下调。",
        "source": "退休生活质量口径 + 养老咨询预算模型。",
        "review": "您的家庭结构、子女所在地，以及当地人情往来习惯。",
    },
    "leisure": {
        "includes": "旅行、摄影、书画、运动、老年大学、文娱活动。",
        "reason": "活力期是退休生活获得感的主要来源，后期会逐步下降。",
        "standard": "活力期上调，高龄和照护阶段明显下调。",
        "source": "积极老龄化 / 健康老龄化理念 + 养老咨询预算模型。",
        "review": "您的旅行频率、兴趣爱好，是否有高消费型爱好。",
    },
    "housing": {
        "includes": "物业、维修、家具家电维护、居家安全维护；租房或养老社区需另加系数。",
        "reason": "居住方式决定现金流底座，自有住房也不代表没有居住成本。",
        "standard": "按基础权重估算，租房和养老社区按居住系数修正。",
        "source": "居住成本口径 + 养老咨询预算模型。",
        "review": "您是否租房、是否计划换房，是否考虑进入养老社区。",
    },
    "housekeeping": {
        "includes": "家政、助餐、助浴、陪诊、代买代办、社区上门服务。",
        "reason": "从舒心期开始，生活辅助会从可选服务变成稳定支出。",
        "standard": "低龄期低权重，75 岁后明显上升。",
        "source": "养老服务场景口径 + 养老阶段压力测试模型。",
        "review": "您的家庭照护人是否在身边，社区服务是否方便，当地上门服务价格如何。",
    },
    "aging_mod": {
        "includes": "扶手、防滑、卫浴改造、照明改造、护理床和安全设备。",
        "reason": "适老化通常是阶段性支出，但不提前规划会在风险出现时被动发生。",
        "standard": "舒心过渡期集中放大，后续按维护和补充设备处理。",
        "source": "适老化改造场景 + 养老咨询预算模型。",
        "review": "您的房屋结构、电梯条件、卫生间安全情况，是否已经做过适老化改造。",
    },
    "longterm_care": {
        "includes": "长期护理、护工、康复护理、机构照护、失能照护。",
        "reason": "这是高龄期最容易拉高现金流的项目，也是家庭最容易低估的项目。",
        "standard": "80 岁后明显放大，高照护期作为主要压力项。",
        "source": "老年人能力评估框架 + 长期照护场景压力测试。",
        "review": "您的失能风险、长期护理险、家庭照护资源，以及当地护工或机构价格。",
    },
    "cognitive": {
        "includes": "认知训练、防走失设备、看护、安全空间改造、专业失智照护。",
        "reason": "失智风险不是人人发生，但一旦发生，照护强度和安全成本会快速上升。",
        "standard": "75 岁后开始计入压力情景，85 岁后明显放大。",
        "source": "认知照护场景 + 老年人能力评估框架。",
        "review": "您的家族病史、记忆力变化、是否独居，以及可选机构是否有失智照护能力。",
    },
    "palliative": {
        "includes": "疼痛管理、舒缓疗护、临终护理、心理支持和尊严告别安排。",
        "reason": "生命末期支出时间短但可能集中出现，需要在现金流里留有弹性。",
        "standard": "高龄后作为压力情景计入，终末阶段明显放大。",
        "source": "舒缓疗护 / 临终关怀场景 + 养老咨询压力测试模型。",
        "review": "您的家庭观念、医疗决策偏好，以及所在城市是否有安宁疗护资源。",
    },
}

CITY_LIVING_COST_EVIDENCE = {
    "成都": [
        {
            "category": "水电气",
            "relatedItems": "居家水电通讯、居住成本",
            "evidence": "四川居民用水监测价可参考 2.81 元 / 立方米；成都居民用电一档常见口径为 0.5224 元 / 度。",
            "source": "四川省发展和改革委员会价格监测资料、居民阶梯电价政策说明。",
            "url": "https://fgw.sc.gov.cn/sfgw/cxjmfw/2025/6/17/515409831cb542faaec4c7dda89e64b8/files/%E5%9B%9B%E5%B7%9D%E7%9C%81%E5%9F%8E%E4%B9%A1%E5%B1%85%E6%B0%91%E6%9C%8D%E5%8A%A1%E4%BB%B7%E6%A0%BC%E7%9B%91%E6%B5%8B%E8%A1%A8%20%EF%BC%882025%E5%B9%B45%E6%9C%88%EF%BC%89.pdf",
            "usage": "帮助判断居家水电通讯是否明显偏离城市基础价格；如果您能提供家庭账单，可以进一步校准。",
        },
        {
            "category": "城市交通",
            "relatedItems": "日常出行",
            "evidence": "成都地铁采用里程计价，线网最高单程票价曾公开说明为 13 元，具体站点间票价可用成都地铁 APP 查询。",
            "source": "成都轨道集团官网票务政策说明。",
            "url": "https://www.chengdurail.com/info/2382/59092.htm",
            "usage": "帮助您理解日常出行不是只按公交低价估算，还要考虑打车、就医往返和跨区出行。",
        },
        {
            "category": "餐饮样本",
            "relatedItems": "日常饮食、家庭社交",
            "evidence": "可参考普通家常餐、家庭聚餐、社区周边餐饮、商圈餐饮等公开价格样本，观察人均价格区间。",
            "source": "大众点评、美团、高德 / 百度地图、餐厅公开菜单；以实际检索日期为准。",
            "url": "",
            "usage": "帮助您理解饮食预算为什么不只按家里做饭估算。如果您长期居家做饭，可下调外食和社交餐饮权重。",
        },
        {
            "category": "活动与兴趣",
            "relatedItems": "旅行兴趣、家庭社交",
            "evidence": "可参考老年大学、兴趣班、摄影书画、近郊旅行、城市文化活动等公开价格样本。",
            "source": "老年大学 / 社区中心公开信息、旅行平台、场馆官网或票务平台。",
            "url": "",
            "usage": "帮助您理解活力期弹性支出为什么会高于高龄期。",
        },
        {
            "category": "家政与照护",
            "relatedItems": "家政助餐、长期护理、认知 / 防走失照护、临终舒缓照护",
            "evidence": "可参考家政小时工、陪诊、护工、养老机构、失智照护专区、安宁疗护资源等公开价格样本。",
            "source": "民政 / 发改价格监测、养老机构官网、家政平台、医院或安宁疗护机构公开信息。",
            "url": "",
            "usage": "帮助您理解高龄期现金流上升的主要原因；如果您所在区县有明确照护资源或报价，可以进一步校准。",
        },
    ],
    "default": [
        {
            "category": "城市生活成本",
            "relatedItems": "全部生活费用科目",
            "evidence": "该城市暂未内置样例。可补充水电气、交通、餐饮、活动、家政照护和养老机构等公开价格信息。",
            "source": "当地发改委 / 民政 / 交通 / 供水供电燃气企业 / 地图餐饮平台 / 养老服务平台。",
            "url": "",
            "usage": "帮助把模型预算转换成当地可解释的生活成本证据。",
        }
    ],
}

ASSET_RISK_MATRIX = [
    {
        "assetType": "现金养老",
        "timeCertainty": "退休时可直接支配。",
        "formCertainty": "现金或接近现金。",
        "amountCertainty": "本金金额相对明确。",
        "flowCertainty": "进入本人养老账户或本人可支配账户。",
        "includeRule": "明确留给养老、不会被提前花掉，才计入养老资本。",
    },
    {
        "assetType": "房子养老",
        "timeCertainty": "退休时点能卖出或出租。",
        "formCertainty": "能转化为现金或稳定租金。",
        "amountCertainty": "出售净额或租金金额有可验证依据。",
        "flowCertainty": "出售或出租后的钱由本人可支配。",
        "includeRule": "只有明确出售净额或稳定租金计入；自住房市值不直接计入。",
    },
    {
        "assetType": "股票养老",
        "timeCertainty": "退休时可按计划减仓或兑现。",
        "formCertainty": "能转成现金。",
        "amountCertainty": "金额波动大，不能按当前市值直接锁定。",
        "flowCertainty": "兑现后进入本人养老账户。",
        "includeRule": "第一版只计入明确留到退休且愿意承受波动的部分；不确定部分不计入。",
    },
    {
        "assetType": "基金养老",
        "timeCertainty": "退休时可按计划赎回。",
        "formCertainty": "能转成现金。",
        "amountCertainty": "金额会随市场波动。",
        "flowCertainty": "赎回后进入本人养老账户。",
        "includeRule": "只计入明确留到退休的部分；短期或用途不清的部分不计入。",
    },
    {
        "assetType": "房租养老",
        "timeCertainty": "退休后持续出租。",
        "formCertainty": "按月或按年现金流。",
        "amountCertainty": "租金水平、空置和维修成本需要校准。",
        "flowCertainty": "租金由本人可支配。",
        "includeRule": "可作为稳定收入计入，但要保留空置、维修和租客变化风险。",
    },
    {
        "assetType": "社保养老",
        "timeCertainty": "达到退休条件后领取。",
        "formCertainty": "按月养老金。",
        "amountCertainty": "以当前测算为估算，最终以社保核定为准。",
        "flowCertainty": "发放到本人养老金账户。",
        "includeRule": "作为稳定收入底座计入。",
    },
    {
        "assetType": "年金养老",
        "timeCertainty": "按年金规则领取。",
        "formCertainty": "按月、按年或按约定方式领取。",
        "amountCertainty": "取决于企业年金、职业年金或个人养老金账户规则。",
        "flowCertainty": "发放到本人账户。",
        "includeRule": "已明确领取金额的部分计入稳定收入。",
    },
]

ASSET_INVENTORY_TEMPLATE = [
    {"assetType": "现金养老", "fields": "金额、账户、是否专款专用、是否会提前使用", "includeCondition": "明确留给养老且本人可支配。"},
    {"assetType": "房子养老", "fields": "房产套数、自住 / 投资、预计出售时间、预计出售净额、是否有家庭共识", "includeCondition": "明确出售时间、净额和本人可支配金额。"},
    {"assetType": "股票养老", "fields": "持仓金额、计划持有时间、退休时减仓规则、可承受波动", "includeCondition": "明确留到退休且愿意按波动资产处理。"},
    {"assetType": "基金养老", "fields": "持仓金额、基金类型、计划持有时间、赎回规则", "includeCondition": "明确留到退休且用途清楚。"},
    {"assetType": "房租养老", "fields": "出租房地址、月租金、空置率、维修成本、租金归属", "includeCondition": "退休后持续出租且租金由本人可支配。"},
    {"assetType": "社保养老", "fields": "退休年龄、缴费年限、缴费基数、个人账户余额", "includeCondition": "按养老金测算报告的中性口径计入稳定收入。"},
    {"assetType": "年金养老", "fields": "企业年金、职业年金、个人养老金、领取方式、预计月领取额", "includeCondition": "已明确领取金额和领取规则。"},
]


def money(value: float) -> str:
    return f"{round(value):,} 元"


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    return int(round(safe_float(value, default)))


def normalize_rate(value: Any, default: float) -> float:
    raw = safe_float(value, default)
    if raw > 1:
        return raw / 100
    return raw


def get_region_value(region: str, table: dict[str, float]) -> float:
    region = str(region or "").strip()
    for key, value in table.items():
        if key != "default" and key in region:
            return value
    return table["default"]


def get_region_reference(region: str) -> dict[str, Any]:
    region = str(region or "").strip()
    for key, value in REGION_STAT_REFERENCES.items():
        if key != "default" and key in region:
            return deepcopy(value)
    return deepcopy(REGION_STAT_REFERENCES["default"])


def get_city_living_cost_evidence(region: str) -> list[dict[str, str]]:
    region = str(region or "").strip()
    for key, value in CITY_LIVING_COST_EVIDENCE.items():
        if key != "default" and key in region:
            return deepcopy(value)
    return deepcopy(CITY_LIVING_COST_EVIDENCE["default"])


def add_asset_row(rows: list[dict[str, Any]], name: str, asset_type: str, amount: float, reason: str) -> None:
    if amount > 0:
        rows.append(
            {
                "name": name,
                "assetType": asset_type,
                "amount": round(amount, 2),
                "reason": reason,
                "certainty": "满足确定时间、确定形式、确定金额、确定流向。",
            }
        )


def add_excluded_asset_row(
    rows: list[dict[str, Any]],
    name: str,
    asset_type: str,
    amount: float,
    reason: str,
    failed_conditions: list[str],
) -> None:
    if amount > 0:
        rows.append(
            {
                "name": name,
                "assetType": asset_type,
                "amount": round(amount, 2),
                "reason": reason,
                "failedConditions": failed_conditions,
            }
        )


def present_value_stage_gap(annual_gap: float, real_rate: float, stage_offset_years: int, stage_years: int) -> float:
    if annual_gap <= 0 or stage_years <= 0:
        return 0.0
    stage_value = present_value_annuity(annual_gap, real_rate, stage_years)
    return stage_value / ((1 + real_rate) ** stage_offset_years)


def get_social_wage_anchor(region: str, stat_reference: dict[str, Any]) -> float:
    monthly = safe_float(stat_reference.get("wageAnchorMonthly"))
    if monthly:
        return monthly
    return get_region_value(region, REGION_WAGE_ANCHORS)


def get_payout_months(retirement_age: int) -> int:
    ages = sorted(PAYOUT_MONTHS)
    if retirement_age <= ages[0]:
        return PAYOUT_MONTHS[ages[0]]
    if retirement_age >= ages[-1]:
        return PAYOUT_MONTHS[ages[-1]]
    return PAYOUT_MONTHS.get(retirement_age, PAYOUT_MONTHS[min(ages, key=lambda x: abs(x - retirement_age))])


def build_cashflow_stages(retirement_age: int, expected_longevity: int) -> list[dict[str, Any]]:
    stages = []
    for period in STAGE_CASHFLOW_PERIODS:
        start_age = max(retirement_age, safe_int(period["startAge"]))
        end_age = min(expected_longevity, safe_int(period["endAge"]))
        if end_age < start_age:
            continue
        stages.append(
            {
                "key": period["key"],
                "label": period["label"],
                "ageRange": f"{start_age}-{end_age} 岁" if start_age != end_age else f"{start_age} 岁",
                "startAge": start_age,
                "endAge": end_age,
                "years": end_age - start_age + 1,
                "state": period["state"],
                "pressure": period["pressure"],
            }
        )
    return stages


def future_value_annuity(annual_amount: float, return_rate: float, years: int) -> float:
    if years <= 0 or annual_amount <= 0:
        return 0.0
    if abs(return_rate) < 1e-9:
        return annual_amount * years
    return annual_amount * (((1 + return_rate) ** years - 1) / return_rate)


def future_value_growing_annuity(annual_amount: float, return_rate: float, growth_rate: float, years: int) -> float:
    if years <= 0 or annual_amount <= 0:
        return 0.0
    total = 0.0
    for year in range(years):
        contribution = annual_amount * ((1 + growth_rate) ** year)
        total += contribution * ((1 + return_rate) ** (years - year - 1))
    return total


def present_value_annuity(annual_amount: float, real_rate: float, years: int) -> float:
    if years <= 0 or annual_amount <= 0:
        return 0.0
    if abs(real_rate) < 1e-9:
        return annual_amount * years
    return annual_amount * (1 - (1 + real_rate) ** (-years)) / real_rate


def required_annual_saving(target_gap: float, return_rate: float, years: int) -> float:
    if target_gap <= 0:
        return 0.0
    if years <= 0:
        return target_gap
    factor = future_value_annuity(1, return_rate, years)
    return target_gap / factor if factor else target_gap / years


def normalize_case(case: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(case)
    profile = data.setdefault("clientProfile", {})
    assumptions = data.setdefault("assumptionsInput", {})
    sources = data.setdefault("sourceAndGapInput", {})

    profile.setdefault("customerName", "客户")
    profile.setdefault("gender", "male")
    profile.setdefault("currentAge", 40)
    profile.setdefault("retirementAge", 60 if profile.get("gender") != "female" else 55)
    profile.setdefault("expectedLongevity", 90)
    profile.setdefault("retirementCity", profile.get("socialCity") or "成都")
    profile.setdefault("monthlyIncome", 0)
    profile.setdefault("contributionBase", profile.get("monthlyIncome") or 0)
    profile.setdefault("contributedYears", max(10, safe_int(profile.get("currentAge"), 40) - 25))

    assumptions.setdefault("targetTier", "comfort")
    assumptions.setdefault("livingStyle", "self_owned")
    assumptions.setdefault("topConcern", "money_shortage")
    assumptions.setdefault("annualContribution", sources.get("annualContribution", 0))
    assumptions.setdefault("preRetirementReturnRate", 0.035)
    assumptions.setdefault("postRetirementReturnRate", 0.025)

    return data


def calculate_basic_pension(case: dict[str, Any]) -> dict[str, Any]:
    profile = case["clientProfile"]
    city = profile.get("retirementCity") or profile.get("socialCity") or "成都"
    stat_reference = get_region_reference(city)
    social_avg_salary_now = get_social_wage_anchor(city, stat_reference)
    current_age = safe_int(profile.get("currentAge"), 40)
    retirement_age = safe_int(profile.get("retirementAge"), 60)
    years_to_retirement = max(0, retirement_age - current_age)
    contribution_base = safe_float(profile.get("contributionBase")) or safe_float(profile.get("monthlyIncome")) or social_avg_salary_now
    contributed_years = safe_float(profile.get("contributedYears"), max(10, current_age - 25))
    total_contribution_years = contributed_years + years_to_retirement
    provided_balance = safe_float(profile.get("personalAccountBalance"))
    estimated_balance_now = contribution_base * 12 * 0.08 * contributed_years * 0.92
    balance_now = provided_balance or estimated_balance_now
    payout_months = get_payout_months(retirement_age)

    scenario_rows = []
    for key, scenario in SCENARIOS.items():
        salary_growth = normalize_rate(
            profile.get(f"{key}SalaryGrowthRate"),
            scenario["salary_growth"],
        )
        inflation = normalize_rate(profile.get(f"{key}InflationRate"), scenario["inflation"])
        projected_social_avg = social_avg_salary_now * ((1 + salary_growth) ** years_to_retirement)
        projected_base = contribution_base * ((1 + salary_growth) ** years_to_retirement)
        basic = ((projected_social_avg + projected_base) / 2) * total_contribution_years * 0.01
        account_rate = min(max(normalize_rate(case["assumptionsInput"].get("preRetirementReturnRate"), 0.035), 0.02), 0.04)
        grown_balance = balance_now * ((1 + account_rate) ** years_to_retirement)
        future_contrib = future_value_growing_annuity(
            contribution_base * 12 * 0.08,
            account_rate,
            salary_growth,
            years_to_retirement,
        )
        account_balance_at_retirement = grown_balance + future_contrib
        account = account_balance_at_retirement / payout_months if payout_months else 0
        total = basic + account
        today_power = total / ((1 + inflation) ** years_to_retirement) if years_to_retirement else total
        scenario_rows.append(
            {
                "key": key,
                "label": scenario["label"],
                "salaryGrowthRate": salary_growth,
                "inflationRate": inflation,
                "projectedSocialAvgSalaryMonthly": round(projected_social_avg, 2),
                "projectedContributionBaseMonthly": round(projected_base, 2),
                "totalContributionYears": round(total_contribution_years, 2),
                "currentPersonalAccountBalance": round(balance_now, 2),
                "accountGrowthRate": account_rate,
                "grownCurrentBalanceAtRetirement": round(grown_balance, 2),
                "futurePersonalContributionsAtRetirement": round(future_contrib, 2),
                "basicPensionMonthly": round(basic, 2),
                "personalAccountMonthly": round(account, 2),
                "totalMonthly": round(total, 2),
                "todayPurchasingPowerMonthly": round(today_power, 2),
                "personalAccountBalanceAtRetirement": round(account_balance_at_retirement, 2),
            }
        )

    neutral = next(row for row in scenario_rows if row["key"] == "neutral")
    return {
        "city": city,
        "socialAvgSalaryNow": social_avg_salary_now,
        "statReference": stat_reference,
        "contributionBaseNow": round(contribution_base, 2),
        "contributedYears": round(contributed_years, 2),
        "totalContributionYears": round(total_contribution_years, 2),
        "yearsToRetirement": years_to_retirement,
        "retirementAge": retirement_age,
        "payoutMonths": payout_months,
        "personalAccountBalanceSource": "provided" if provided_balance else "estimated",
        "personalAccountBalanceNow": round(balance_now, 2),
        "scenarios": scenario_rows,
        "neutral": neutral,
    }


def calculate_lifestyle_cashflow(case: dict[str, Any], basic: dict[str, Any]) -> dict[str, Any]:
    assumptions = case["assumptionsInput"]
    profile = case["clientProfile"]
    city = profile.get("retirementCity") or "成都"
    tier = assumptions.get("targetTier") or "comfort"
    standard = RETIREMENT_STANDARDS.get(tier, RETIREMENT_STANDARDS["comfort"])
    multiplier = get_region_value(city, CITY_MULTIPLIERS)
    living_style = assumptions.get("livingStyle", "self_owned")
    housing_multiplier = 1.0
    if living_style == "rent":
        housing_multiplier = 1.35
    elif living_style == "community":
        housing_multiplier = 1.65

    years = basic["yearsToRetirement"]
    inflation = basic["neutral"]["inflationRate"]
    standard_base_monthly = safe_float(basic["neutral"].get("projectedSocialAvgSalaryMonthly"))
    provided_monthly_today = safe_float(assumptions.get("targetMonthlyExpenseToday"))
    if provided_monthly_today:
        monthly_today = provided_monthly_today
        monthly_retirement = monthly_today * ((1 + inflation) ** years)
        monthly_today_source = "您提供"
    else:
        monthly_retirement = standard_base_monthly * standard["social_wage_ratio"]
        monthly_today = monthly_retirement / ((1 + inflation) ** years) if years else monthly_retirement
        monthly_today_source = "按社平工资预期值和退休生活标准估算"
    retirement_living_standards = [
        {
            "label": "基本生活",
            "ratio": 0.4,
            "monthlyAtRetirement": round(standard_base_monthly * 0.4, 2),
            "annualAtRetirement": round(standard_base_monthly * 0.4 * 12, 2),
            "meaning": "覆盖基础饮食、居住、水电通讯、基础医疗和必要出行。",
        },
        {
            "label": "体面生活",
            "ratio": 1.0,
            "monthlyAtRetirement": round(standard_base_monthly, 2),
            "annualAtRetirement": round(standard_base_monthly * 12, 2),
            "meaning": "在基本生活之外，保留健康管理、家庭社交和适度休闲空间。",
        },
        {
            "label": "品质生活",
            "ratio": 2.0,
            "monthlyAtRetirement": round(standard_base_monthly * 2, 2),
            "annualAtRetirement": round(standard_base_monthly * 2 * 12, 2),
            "meaning": "更强调服务、旅行、兴趣、居住品质和照护冗余。",
        },
    ]

    items = []
    annual_total = 0.0
    rigid_total = 0.0
    type_totals: dict[str, float] = {"刚性": 0.0, "半刚性": 0.0, "弹性": 0.0}
    for key, label, weight, item_type in LIFESTYLE_WEIGHTS:
        item_monthly = monthly_retirement * weight
        multiplier_applied = 1.0
        if key == "housing":
            multiplier_applied = housing_multiplier
            item_monthly *= multiplier_applied
        annual = item_monthly * 12
        annual_total += annual
        type_totals[item_type] = type_totals.get(item_type, 0.0) + annual
        if item_type == "刚性":
            rigid_total += annual
        items.append(
            {
                "key": key,
                "label": label,
                "weight": round(weight, 4),
                "multiplier": round(multiplier_applied, 4),
                "monthlyAtRetirement": round(item_monthly, 2),
                "annualAtRetirement": round(annual, 2),
                "type": item_type,
            }
        )

    care_scenario_annual = annual_total * 1.65
    type_summary = [
        {
            "type": item_type,
            "annualAtRetirement": round(amount, 2),
            "ratio": round(amount / annual_total if annual_total else 0, 4),
        }
        for item_type, amount in type_totals.items()
    ]
    retirement_age = safe_int(profile.get("retirementAge"), basic["retirementAge"])
    expected_longevity = safe_int(profile.get("expectedLongevity"), 90)
    cashflow_stages = build_cashflow_stages(retirement_age, expected_longevity)
    stage_totals = {stage["key"]: 0.0 for stage in cashflow_stages}
    stage_type_totals = {stage["key"]: {"刚性": 0.0, "半刚性": 0.0, "弹性": 0.0} for stage in cashflow_stages}
    matrix_items = []
    for key, label, base_weight, item_type, stage_factors in STAGE_EXPENSE_ITEMS:
        reference = EXPENSE_ITEM_REFERENCES.get(key, {})
        row = {
            "key": key,
            "label": label,
            "type": item_type,
            "baseWeight": round(base_weight, 4),
            "includes": reference.get("includes", ""),
            "reason": reference.get("reason", ""),
            "standard": reference.get("standard", ""),
            "source": reference.get("source", ""),
            "review": reference.get("review", ""),
            "stages": [],
        }
        for stage in cashflow_stages:
            stage_key = stage["key"]
            age_offset = max(0, stage["startAge"] - retirement_age)
            stage_base_monthly = monthly_retirement * ((1 + inflation) ** age_offset)
            factor = safe_float(stage_factors.get(stage_key), 0.0)
            item_multiplier = housing_multiplier if key == "housing" else 1.0
            monthly = stage_base_monthly * base_weight * factor * item_multiplier
            annual = monthly * 12
            stage_totals[stage_key] += annual
            stage_type_totals[stage_key][item_type] = stage_type_totals[stage_key].get(item_type, 0.0) + annual
            row["stages"].append(
                {
                    "stageKey": stage_key,
                    "factor": round(factor, 4),
                    "monthly": round(monthly, 2),
                    "annual": round(annual, 2),
                }
            )
        matrix_items.append(row)

    stage_summaries = []
    for stage in cashflow_stages:
        stage_key = stage["key"]
        annual = stage_totals[stage_key]
        stage_summaries.append(
            {
                **stage,
                "annualAtStageStart": round(annual, 2),
                "monthlyAtStageStart": round(annual / 12, 2),
                "totalStageExpense": round(annual * stage["years"], 2),
                "rigidAnnual": round(stage_type_totals[stage_key].get("刚性", 0.0), 2),
                "semiRigidAnnual": round(stage_type_totals[stage_key].get("半刚性", 0.0), 2),
                "flexibleAnnual": round(stage_type_totals[stage_key].get("弹性", 0.0), 2),
            }
        )
    total_lifetime_expense = sum(stage["totalStageExpense"] for stage in stage_summaries)
    return {
        "targetTier": tier,
        "targetLabel": standard["label"],
        "standardSocialWageRatio": standard["social_wage_ratio"],
        "cityMultiplier": multiplier,
        "livingStyle": living_style,
        "housingMultiplier": housing_multiplier,
        "monthlyTodaySource": monthly_today_source,
        "retirementStandardBaseMonthly": round(standard_base_monthly, 2),
        "retirementLivingStandards": retirement_living_standards,
        "retirementLivingStandardsNote": "基本生活 40% 参考国际劳工组织 C102 老年给付最低保障思想；本报告将其转译为退休生活现金流底线，不等同于中国社保部门核定待遇。",
        "monthlyToday": round(monthly_today, 2),
        "yearsToRetirement": years,
        "inflationRate": inflation,
        "monthlyAtRetirement": round(monthly_retirement, 2),
        "annualAtRetirement": round(annual_total, 2),
        "rigidAnnualAtRetirement": round(rigid_total, 2),
        "rigidRatio": round(rigid_total / annual_total if annual_total else 0, 4),
        "careScenarioAnnual": round(care_scenario_annual, 2),
        "careScenarioMonthly": round(care_scenario_annual / 12, 2),
        "typeSummary": type_summary,
        "items": items,
        "cashflowStages": cashflow_stages,
        "stageCashflowMatrix": matrix_items,
        "stageSummaries": stage_summaries,
        "totalLifetimeExpense": round(total_lifetime_expense, 2),
        "cityLivingCostEvidence": get_city_living_cost_evidence(city),
    }


def calculate_source_gap(case: dict[str, Any], basic: dict[str, Any], lifestyle: dict[str, Any]) -> dict[str, Any]:
    sources = case.get("sourceAndGapInput", {})
    assumptions = case["assumptionsInput"]
    years = basic["yearsToRetirement"]
    retirement_age = basic["retirementAge"]
    longevity = safe_int(case["clientProfile"].get("expectedLongevity"), 90)
    planning_years = max(10, longevity - retirement_age)
    pre_return = normalize_rate(assumptions.get("preRetirementReturnRate"), 0.035)
    post_return = normalize_rate(assumptions.get("postRetirementReturnRate"), 0.025)
    inflation = basic["neutral"]["inflationRate"]
    real_drawdown_rate = ((1 + post_return) / (1 + inflation)) - 1

    stable_income_sources = [
        {"name": "社保养老金", "assetType": "社保养老", "monthlyAmount": basic["neutral"]["totalMonthly"], "certainty": "按养老金测算报告中性口径估算。"},
        {"name": "企业年金", "assetType": "年金养老", "monthlyAmount": safe_float(sources.get("enterpriseAnnuityMonthly")), "certainty": "已明确月领取额时计入。"},
        {"name": "职业年金", "assetType": "年金养老", "monthlyAmount": safe_float(sources.get("occupationalPensionMonthly")), "certainty": "已明确月领取额时计入。"},
        {"name": "个人养老金", "assetType": "年金养老", "monthlyAmount": safe_float(sources.get("personalPensionMonthly")), "certainty": "已明确月领取额时计入。"},
        {"name": "其他确定收入", "assetType": "现金养老", "monthlyAmount": safe_float(sources.get("otherGuaranteedMonthlyIncome")), "certainty": "确定时间、金额和流向后计入。"},
        {"name": "稳定租金收入", "assetType": "房租养老", "monthlyAmount": safe_float(sources.get("propertyRentalIncomeMonthly")), "certainty": "能持续出租且租金由本人可支配时计入。"},
    ]
    stable_monthly = sum(row["monthlyAmount"] for row in stable_income_sources)
    annual_need = lifestyle["annualAtRetirement"]
    rigid_annual_need = lifestyle["rigidAnnualAtRetirement"]
    flexible_annual_need = max(0.0, annual_need - rigid_annual_need)
    annual_stable_income = stable_monthly * 12
    floor_ratio = normalize_rate(assumptions.get("floorLivingRatio"), 0.8)
    floor_ratio = min(max(floor_ratio, 0.6), 1.0)
    stage_gap_cashflow = []
    certainty_target_capital = 0.0
    quality_target_capital = 0.0
    for stage in lifestyle.get("stageSummaries", []):
        annual_target = safe_float(stage.get("annualAtStageStart"))
        stage_years = safe_int(stage.get("years"), 0)
        stage_offset = max(0, safe_int(stage.get("startAge"), retirement_age) - retirement_age)
        floor_need = max(annual_target * floor_ratio, rigid_annual_need)
        certainty_gap = max(0.0, floor_need - annual_stable_income)
        quality_gap = max(0.0, annual_target - max(annual_stable_income, floor_need))
        certainty_capital = present_value_stage_gap(certainty_gap, real_drawdown_rate, stage_offset, stage_years)
        quality_capital = present_value_stage_gap(quality_gap, real_drawdown_rate, stage_offset, stage_years)
        certainty_target_capital += certainty_capital
        quality_target_capital += quality_capital
        stage_gap_cashflow.append(
            {
                "label": stage.get("label", ""),
                "ageRange": stage.get("ageRange", ""),
                "years": stage_years,
                "annualLifeTarget": round(annual_target, 2),
                "floorLivingNeed": round(floor_need, 2),
                "certainIncome": round(annual_stable_income, 2),
                "certaintyGap": round(certainty_gap, 2),
                "qualityGap": round(quality_gap, 2),
                "certaintyTargetCapital": round(certainty_capital, 2),
                "qualityTargetCapital": round(quality_capital, 2),
                "pressure": stage.get("pressure", ""),
            }
        )
    annual_gap = max(0.0, annual_need - annual_stable_income)
    rigid_income_coverage = min(annual_stable_income, rigid_annual_need)
    stable_income_after_rigid = max(0.0, annual_stable_income - rigid_annual_need)
    rigid_annual_gap = max(0.0, rigid_annual_need - annual_stable_income)
    flexible_income_coverage = min(stable_income_after_rigid, flexible_annual_need)
    flexible_annual_gap = max(0.0, flexible_annual_need - stable_income_after_rigid)
    rigid_target_capital = certainty_target_capital
    flexible_target_capital = quality_target_capital
    target_capital = certainty_target_capital + quality_target_capital

    countable_assets = {
        "currentRetirementAssets": safe_float(sources.get("currentRetirementAssets")),
        "savingsHeldToRetirement": safe_float(sources.get("savingsHeldToRetirement")),
        "stocksHeldToRetirement": safe_float(sources.get("stocksHeldToRetirement")),
        "fundsHeldToRetirement": safe_float(sources.get("fundsHeldToRetirement")),
        "wealthProducts": safe_float(sources.get("wealthProducts")),
        "policyCashValue": safe_float(sources.get("policyCashValue")),
        "propertyRetirementSellableValue": safe_float(sources.get("propertyRetirementSellableValue")),
    }
    current_countable_capital = sum(countable_assets.values())
    included_assets: list[dict[str, Any]] = []
    excluded_assets: list[dict[str, Any]] = []
    add_asset_row(included_assets, "养老专款", "现金养老", countable_assets["currentRetirementAssets"], "已经明确作为养老资金。")
    add_asset_row(included_assets, "明确留到退休的存款", "现金养老", countable_assets["savingsHeldToRetirement"], "确定留到退休且本人可支配。")
    add_asset_row(included_assets, "明确留到退休的股票", "股票养老", countable_assets["stocksHeldToRetirement"], "已明确留到退休，按波动资产处理。")
    add_asset_row(included_assets, "明确留到退休的基金", "基金养老", countable_assets["fundsHeldToRetirement"], "已明确留到退休，按波动资产处理。")
    add_asset_row(included_assets, "明确留到退休的理财", "现金养老", countable_assets["wealthProducts"], "已明确留到退休，且可转为本人养老现金流。")
    add_asset_row(included_assets, "保单现金价值", "现金养老", countable_assets["policyCashValue"], "退休时可兑现且用于养老。")
    add_asset_row(included_assets, "计划出售的房产净额", "房子养老", countable_assets["propertyRetirementSellableValue"], "已经明确出售时间、出售净额和本人可支配金额。")
    add_excluded_asset_row(
        excluded_assets,
        "未明确留到退休的存款",
        "现金养老",
        max(0.0, safe_float(sources.get("savings")) - countable_assets["savingsHeldToRetirement"]),
        "这部分钱还没有明确留给养老，可能提前使用。",
        ["确定时间", "确定流向"],
    )
    add_excluded_asset_row(
        excluded_assets,
        "未明确留到退休的股票",
        "股票养老",
        max(0.0, safe_float(sources.get("stocks")) - countable_assets["stocksHeldToRetirement"]),
        "股票金额和兑现时间不确定，第一版不直接计入刚性养老缺口。",
        ["确定时间", "确定金额"],
    )
    add_excluded_asset_row(
        excluded_assets,
        "未明确留到退休的基金",
        "基金养老",
        max(0.0, safe_float(sources.get("funds")) - countable_assets["fundsHeldToRetirement"]),
        "基金金额和用途没有完全锁定，未明确部分暂不计入。",
        ["确定金额", "确定流向"],
    )
    add_excluded_asset_row(
        excluded_assets,
        "未计划出售的房产市值",
        "房子养老",
        safe_float(sources.get("propertyMarketValue")) if countable_assets["propertyRetirementSellableValue"] <= 0 else max(0.0, safe_float(sources.get("propertyMarketValue")) - countable_assets["propertyRetirementSellableValue"]),
        "房产如果没有明确出售时间、出售净额和本人可支配金额，就不能直接当作养老金。",
        ["确定时间", "确定金额", "确定流向"],
    )
    annual_contribution = safe_float(assumptions.get("annualContribution") or sources.get("annualContribution"))
    projected_new_capital = future_value_annuity(annual_contribution, pre_return, years)
    projected_total_capital = current_countable_capital + projected_new_capital
    remaining_capital_gap = max(0.0, target_capital - projected_total_capital)
    required_annual = required_annual_saving(remaining_capital_gap, pre_return, years)
    annual_income = safe_float(case["clientProfile"].get("monthlyIncome")) * 12

    return {
        "stableMonthlyIncome": round(stable_monthly, 2),
        "annualNeedAtRetirement": round(annual_need, 2),
        "planningYears": planning_years,
        "preRetirementReturnRate": round(pre_return, 4),
        "postRetirementReturnRate": round(post_return, 4),
        "realDrawdownRate": round(real_drawdown_rate, 4),
        "floorLivingRatio": round(floor_ratio, 4),
        "floorLivingRule": "底线生活需求 = max(阶段年度生活目标 × 底线系数, 退休起点刚性支出)。默认底线系数为 80%。",
        "stageGapCashflow": stage_gap_cashflow,
        "rigidAnnualNeed": round(rigid_annual_need, 2),
        "flexibleAnnualNeed": round(flexible_annual_need, 2),
        "annualStableIncome": round(annual_stable_income, 2),
        "annualGap": round(annual_gap, 2),
        "rigidIncomeCoverage": round(rigid_income_coverage, 2),
        "flexibleIncomeCoverage": round(flexible_income_coverage, 2),
        "rigidAnnualGap": round(rigid_annual_gap, 2),
        "flexibleAnnualGap": round(flexible_annual_gap, 2),
        "rigidTargetCapital": round(rigid_target_capital, 2),
        "flexibleTargetCapital": round(flexible_target_capital, 2),
        "targetCapital": round(target_capital, 2),
        "countableAssets": {k: round(v, 2) for k, v in countable_assets.items()},
        "includedAssets": included_assets,
        "excludedAssets": excluded_assets,
        "assetRiskMatrix": deepcopy(ASSET_RISK_MATRIX),
        "assetInventoryTemplate": deepcopy(ASSET_INVENTORY_TEMPLATE),
        "stableIncomeSources": [
            {**row, "monthlyAmount": round(row["monthlyAmount"], 2), "annualAmount": round(row["monthlyAmount"] * 12, 2)}
            for row in stable_income_sources
        ],
        "currentCountableCapital": round(current_countable_capital, 2),
        "plannedAnnualContribution": round(annual_contribution, 2),
        "projectedNewCapital": round(projected_new_capital, 2),
        "projectedTotalCapital": round(projected_total_capital, 2),
        "remainingCapitalGap": round(remaining_capital_gap, 2),
        "requiredAdditionalAnnualContribution": round(required_annual, 2),
        "incomeRatio": round(required_annual / annual_income, 4) if annual_income else None,
    }


def design_solution(case: dict[str, Any], gap: dict[str, Any]) -> dict[str, Any]:
    concern = case["assumptionsInput"].get("topConcern", "money_shortage")
    profile = case["clientProfile"]
    years = safe_int(profile.get("retirementAge"), 60) - safe_int(profile.get("currentAge"), 40)
    annual_income = safe_float(profile.get("monthlyIncome")) * 12
    planned_annual = safe_float(gap.get("plannedAnnualContribution"))
    required_annual = safe_float(gap.get("requiredAdditionalAnnualContribution"))
    remaining_gap = safe_float(gap.get("remainingCapitalGap"))
    target_capital = safe_float(gap.get("targetCapital"))
    current_capital = safe_float(gap.get("currentCountableCapital"))
    projected_total = safe_float(gap.get("projectedTotalCapital"))
    income_ratio = safe_float(gap.get("incomeRatio"))
    base = ["社保养老金", "个人账户养老金"]
    supplement = ["年度养老专款账户"]
    flexible = ["房产处置先观察", "基金和权益仓只放非刚性责任资金"]
    legacy = ["先保证自己退休现金流，再单独规划留给家人的资产"]

    if remaining_gap > 0:
        supplement.append("用确定性现金流工具补年度缺口")
    if years > 10:
        supplement.append("可把长期增值仓和确定领取仓分开管理")
    else:
        flexible.insert(0, "退休前 10 年内优先降低波动")

    if concern == "disability_care":
        base.append("长期照护预算")
        supplement.insert(0, "护理或照护专项资金池")
    elif concern == "long_illness":
        base.append("医疗保障与慢病管理预算")
    elif concern == "leave_legacy":
        legacy.insert(0, "受益人和身后资产安排要单独列账")
    else:
        supplement.insert(0, "先把年度缺口补到可承受区间")

    if remaining_gap <= 0:
        money_diagnosis = "现有稳定收入和已计入资产能够覆盖当前测算缺口，下一步重点是把领取路径、账户边界和照护资源确认清楚。"
    elif income_ratio >= 0.3:
        money_diagnosis = "当前待补资本较大，如果只靠新增储蓄补足，年度压力偏高，需要同时调整生活目标、延长准备期、补充确定现金流，并重新盘点可计入资产。"
    elif income_ratio >= 0.15:
        money_diagnosis = "当前缺口可以通过持续年度补充缓慢修复，但需要把这笔钱和日常资金分开管理，避免中途被挪用。"
    else:
        money_diagnosis = "当前缺口压力相对可控，重点是把年度补充动作稳定下来，并定期校准社保、通胀和照护费用。"

    annual_saving_comment = (
        "当前未形成年度养老补充计划，需要先确定每年能稳定拿出多少钱。"
        if planned_annual <= 0
        else f"当前计划每年补充 {money(planned_annual)}，按退休前收益率测算，预计形成新增资本 {money(gap.get('projectedNewCapital', 0))}。"
    )
    extra_comment = (
        "按当前口径，不需要额外新增年度补充。"
        if required_annual <= 0
        else f"剩余资本缺口折算为每年还需额外补充约 {money(required_annual)}。"
    )
    city = str(profile.get("retirementCity") or profile.get("socialCity") or "退休城市")
    city_care_note = (
        "以成都公开价格样本看，普惠型养老机构常见价格约 2,000 - 6,000 元/月，中高端机构约 7,000 元/月起；全护理、特护或专护样本可到 3,800 - 12,000 元/月以上。您所在区县的机构和床位价格，还需要再单独确认。"
        if "成都" in city
        else "您所在城市的养老机构等级、床位价格、护理费、长护险政策和上门护理资源，还需要再单独确认。"
    )

    return {
        "moneyProblem": "生的部分先确认退休生活目标、年度确定收入和待补资本，再决定每年能稳定补多少钱。",
        "resourceProblem": "老的部分重点看护理状态、照护资源和所在城市能买到什么服务。",
        "legacyProblem": "死的部分不是简单写遗嘱，而是确认哪些资产能在确定时间、确定形式下传给确定的人。",
        "baseLayer": base,
        "supplementLayer": supplement,
        "flexibleLayer": flexible,
        "legacyLayer": legacy,
        "solutionSummary": money_diagnosis,
        "solutionPrinciples": [
            "生：先确认退休之后怎么生活，钱从哪里来，够不够，不够怎么补。",
            "老：护理会分层，不能把所有照护压力都留到失能之后再处理。",
            "病：小病、意外、中等住院、大病和大意外分别看保障工具，不用一个险种解释所有风险。",
            "死：传承必须建立在本人养老安全之后，并且要做到确定时间、确定方式、确定形式、确定对象。",
        ],
        "lifeModule": {
            "summary": money_diagnosis,
            "focus": "退休之后的生活安排和钱的问题：要花多少钱、钱从哪里来、够不够、不够怎么补。",
            "capitalActionPlan": [
                ("目标资金池", money(target_capital), "用来承接确定性缺口和品质缺口。"),
                ("已明确可计入资产", money(current_capital), "只包含满足确定性标准的资产。"),
                ("当前年度补充计划", money(planned_annual), annual_saving_comment),
                ("退休前预计资金池", money(projected_total), "由当前可计入资产和未来年度补充累积形成。"),
                ("剩余待补资本", money(remaining_gap), extra_comment),
            ],
        },
        "agingCareModule": {
            "summary": f"护理不是一个状态。现在身体好，主要是体检、运动和生活安排；以后如果需要帮助，会逐步进入上门护理、机构护理，甚至重度护理。{city_care_note}",
            "careLevels": [
                {
                    "level": "活力养老",
                    "state": "基本不需要护理",
                    "resourceNeed": "体检、运动、兴趣社群、便利交通和基础健康管理。",
                    "costReference": "主要进入生活现金流，不单独列护理费。",
                    "action": "保留旅行、兴趣和社交预算，同时建立体检和慢病记录。",
                },
                {
                    "level": "上门护理",
                    "state": "居家生活为主，需要助餐、助浴、家政或短时护理。",
                    "resourceNeed": "社区服务、家政公司、上门护理、长护险定点服务。",
                    "costReference": "按小时、按次或套餐计费；长期护理保险可按失能等级提供部分待遇。",
                    "action": "按您常住区域确认上门护理机构、服务项目和价格。",
                },
                {
                    "level": "机构护理",
                    "state": "养老院、护理院或医养结合机构提供持续护理。",
                    "resourceNeed": "星级养老机构、护理型床位、康复护理、慢病管理。",
                    "costReference": "公开样本常见约 2,000 - 8,000 元/月，中高端或医养结合机构更高。",
                    "action": "按您退休城市列出机构等级、床位费、护理费、押金和医保 / 长护险可用情况。",
                },
                {
                    "level": "重度护理",
                    "state": "失能、失智、术后长期康复或 24 小时照护。",
                    "resourceNeed": "全护理、特护、认知症照护、康复护理和医疗协同。",
                    "costReference": "公开样本可到 3,800 - 12,000 元/月以上，重症或高端机构更高。",
                    "action": "这部分单独测算，不简单塞进普通生活费。",
                },
            ],
            "cityResourceChecklist": [
                ("星级养老机构", "机构等级、地址、床位数量、是否护理型。", "看您所在城市有没有可选择的中高质量机构。"),
                ("护理院 / 医养结合机构", "是否有护理型床位、康复资源、医保或长护险结算能力。", "看重度护理时能不能落地。"),
                ("上门护理资源", "助浴、助餐、上门护士、家政护理的价格和服务范围。", "看居家养老能撑多久。"),
                ("长期护理保险", "申请条件、失能评估、待遇方式、支付标准。", "看哪些费用能由公共保障分担。"),
            ],
        },
        "illnessProtectionModule": {
            "summary": "看病这件事，不能只问“有没有保险”。小病、意外、住院、大病和大意外，花钱方式不一样，需要接住的工具也不一样。",
            "riskMatrix": [
                {
                    "risk": "小病小灾",
                    "scene": "感冒发烧、头疼脑热、普通门急诊。",
                    "tool": "医保门诊、单位二次报销、小额医疗险。",
                    "coveragePath": "先看社保，再看单位福利，最后看商业保险是否补门急诊。",
                    "keyLimit": "年度门诊额度、免赔额、报销比例。",
                    "status": "需要确认医保、单位福利和小额医疗险。",
                },
                {
                    "risk": "小意外",
                    "scene": "磕碰摔伤、猫抓狗咬、轻微骨折或门急诊处理。",
                    "tool": "意外医疗、医保、单位二次报销。",
                    "coveragePath": "重点看意外医疗是否覆盖门急诊、狂犬疫苗、社保外用药。",
                    "keyLimit": "意外医疗额度、免赔额、报销比例、是否限社保内。",
                    "status": "需要确认意外险保单。",
                },
                {
                    "risk": "中等疾病住院",
                    "scene": "肺炎住院、肾结石住院、短期手术，费用通常在 10 万元以内。",
                    "tool": "医保住院、单位二次报销、住院医疗险或百万医疗险。",
                    "coveragePath": "先报医保，再看二次报销，最后看商业医疗险补剩余部分。",
                    "keyLimit": "住院额度、免赔额、社保外用药、既往症限制。",
                    "status": "需要确认医疗险责任和续保条件。",
                },
                {
                    "risk": "重大疾病",
                    "scene": "癌症、心脑血管重大疾病、重大手术或长期治疗。",
                    "tool": "百万医疗险、重疾险、特药责任、就医资源服务。",
                    "coveragePath": "同时看三件事：能不能报销，能不能去好医院，社保外药和特效疗法是否覆盖。",
                    "keyLimit": "医疗报销上限、重疾保额、特药清单、院外购药、异地就医支持。",
                    "status": "需要确认重疾险、医疗险和就医服务权益。",
                },
                {
                    "risk": "大意外",
                    "scene": "严重伤残、身故、长期康复或收入中断。",
                    "tool": "意外伤残 / 身故保额、医疗险、寿险。",
                    "coveragePath": "看伤残比例赔付、身故赔付、医疗报销和家庭责任是否足够。",
                    "keyLimit": "身故保额、伤残保额、交通意外额外赔付、免责条款。",
                    "status": "需要确认意外险和寿险保额。",
                },
            ],
        },
        "legacyTransferModule": {
            "summary": "传承要基于第三份报告里的资产盘点。先确认哪些资产属于本人养老安全线，哪些资产在不影响养老的前提下可以安排给家人。",
            "transferMatrix": [
                {
                    "asset": "房产",
                    "currentQuestion": "有几套房，哪套自住，哪套可处置，是否有贷款、共有权或继承争议。",
                    "tool": "遗嘱、公证、家庭协议、产权安排。",
                    "certainty": "确定时间、确定方式、确定形式、确定对象。",
                    "action": "先区分自住房和可传承房产，不把仍需居住的房子提前安排掉。",
                },
                {
                    "asset": "现金、存款、理财",
                    "currentQuestion": "哪些钱属于养老专款，哪些钱是可传承资产。",
                    "tool": "账户分账、遗嘱、家庭清单。",
                    "certainty": "确定金额、确定对象、确定可支配权。",
                    "action": "养老专款先锁定用途，剩余部分再进入传承清单。",
                },
                {
                    "asset": "股票、基金",
                    "currentQuestion": "是否长期持有到退休，是否愿意承担波动，是否明确给谁。",
                    "tool": "账户清单、受益安排、遗嘱。",
                    "certainty": "确定形式和确定金额较弱，需要定期更新。",
                    "action": "先作为弹性资产，不用于刚性养老和确定传承承诺。",
                },
                {
                    "asset": "保单权益",
                    "currentQuestion": "受益人是谁，保额多少，现金价值是否已计入养老。",
                    "tool": "保单受益人指定、保单整理表。",
                    "certainty": "确定对象、确定形式较强，但要避免和养老现金价值重复计算。",
                    "action": "单独列保单权益，不和养老资金池混在一起。",
                },
            ],
        },
        "fundingBuckets": [
            {
                "bucket": "底线生活资金池",
                "responsibility": "覆盖底线生活、基础医疗、必要居住和基础照护。",
                "target": gap.get("rigidTargetCapital", 0),
                "currentStatus": f"年度确定收入 {money(gap.get('annualStableIncome', 0))}，确定性缺口目标资本 {money(gap.get('rigidTargetCapital', 0))}。",
                "action": "优先用社保、年金、确定领取现金流和专款账户承接。",
            },
            {
                "bucket": "品质生活资金池",
                "responsibility": "覆盖旅行、社交、兴趣、品质医疗和阶段性改善。",
                "target": gap.get("flexibleTargetCapital", 0),
                "currentStatus": f"品质缺口目标资本 {money(gap.get('flexibleTargetCapital', 0))}，可根据真实偏好上调或压缩。",
                "action": "可以用基金、权益仓、退休后兼职收入和弹性消费调整承接。",
            },
            {
                "bucket": "长期照护资金池",
                "responsibility": "覆盖 75 岁以后生活辅助、护理、康复和机构照护压力。",
                "target": max(safe_float(gap.get("rigidTargetCapital")) * 0.35, 0),
                "currentStatus": "先按现金流报告里的阶段压力识别，不在这里把照护费用写死。",
                "action": "结合您的健康史、家庭照护能力和城市照护价格，再补一版照护专项测算。",
            },
        ],
        "capitalActionPlan": [
            ("目标资金池", money(target_capital), "用来承接确定性缺口和品质缺口。"),
            ("已明确可计入资产", money(current_capital), "只包含满足确定性标准的资产。"),
            ("当前年度补充计划", money(planned_annual), annual_saving_comment),
            ("退休前预计资金池", money(projected_total), "由当前可计入资产和未来年度补充累积形成。"),
            ("剩余待补资本", money(remaining_gap), extra_comment),
        ],
        "resourceChecklist": [
            ("居住资源", "退休城市、住房是否适老、是否靠近医院和子女。", "确认自住房是否长期居住，是否需要适老化改造预算。"),
            ("医疗资源", "医保、商保、常用医院、慢病管理和体检频率。", "把基础医疗和慢病支出从弹性消费里单独列出来。"),
            ("照护资源", "配偶、子女、社区、家政、护理机构能否接力。", "75 岁前完成一次照护方案预案，不等失能后临时决策。"),
            ("城市资源", "退休城市的交通、养老服务、社区配套和照护价格。", "后续按退休城市补充公开价格样本。"),
        ],
        "legacyChecklist": [
            ("本人安全线", "本人底线生活和照护资金先留足。", "没有达成前，不把核心养老资金提前赠与或锁死。"),
            ("家庭沟通", "让配偶和子女知道养老资金池、房产计划和照护预案。", "减少未来临时卖房、临时借钱和责任不清。"),
            ("资产分账", "把养老专款、弹性投资和传承资产分开。", "避免把所有资产混在一个账户里，导致用途不清。"),
            ("受益安排", "身后资产、保单受益人和房产继承顺序。", "在本人现金流安全后再进入细化设计。"),
        ],
        "actionTimeline": [
            {
                "stage": "现在到退休",
                "ageRange": f"{profile.get('currentAge')} - {profile.get('retirementAge')} 岁",
                "focus": "建立养老专款账户，稳定年度补充，临近退休时降低刚性资金波动。",
                "action": "每年复核社保、可计入资产和生活目标；退休前 10 年确认领取路径。",
            },
            {
                "stage": "退休后活力期",
                "ageRange": "60 - 75 岁",
                "focus": "控制弹性支出，保留照护资金。",
                "action": "旅行、兴趣和社交可以花，但不提前消耗 75 岁以后的照护准备。",
            },
            {
                "stage": "75 岁以后",
                "ageRange": "75 岁以后",
                "focus": "照护资源和现金流稳定性。",
                "action": "优先保障医疗、护理、居住安全和家庭照护接力，再处理传承分配。",
            },
        ],
    }


def build_summary_markdown(result: dict[str, Any]) -> str:
    profile = result["clientProfile"]
    basic = result["basicPensionEstimate"]
    lifestyle = result["lifestyleCashflow"]
    gap = result["sourceAndGap"]
    solution = result["solutionDesign"]
    neutral = basic["neutral"]

    def text(value: Any, default: str = "待确认") -> str:
        if value in ("", None):
            return default
        return str(value)

    def amount(value: Any) -> str:
        return money(safe_float(value))

    def rate(value: Any) -> str:
        return percent(safe_float(value))

    def rows_to_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
        table = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for row in rows:
            table.append("| " + " | ".join(text(item, "") for item in row) + " |")
        return table

    def bullet_list(items: list[str]) -> list[str]:
        return [f"- {item}" for item in items] if items else ["- 待确认。"]

    stat = basic.get("statReference", {})
    scenarios = basic.get("scenarios", [])
    standards = lifestyle.get("retirementLivingStandards", [])
    stages = lifestyle.get("cashflowStages", [])
    stage_labels = [stage["label"] for stage in stages]
    stage_keys = [stage["key"] for stage in stages]

    scenario_rows = [
        [
            item["label"],
            amount(item["basicPensionMonthly"]),
            amount(item["personalAccountMonthly"]),
            amount(item["totalMonthly"]),
            amount(item["todayPurchasingPowerMonthly"]),
        ]
        for item in scenarios
    ]
    standard_rows = [
        [item["label"], f"社平工资预期值 × {percent(item['ratio'])}", amount(item["monthlyAtRetirement"]), item["meaning"]]
        for item in standards
    ]
    stage_rows = [
        [stage["label"], stage["ageRange"], stage["state"], stage["pressure"], "见阶段现金流矩阵"]
        for stage in stages
    ]
    premise_rows = [
        ["退休城市", text(profile.get("retirementCity") or profile.get("socialCity"))],
        ["退休生活目标", text(lifestyle.get("targetLabel"))],
        ["居住方式", text(lifestyle.get("livingStyle"))],
        ["当前生活预算来源", text(lifestyle.get("monthlyTodaySource"))],
        ["今天口径月预算", amount(lifestyle.get("monthlyToday"))],
        ["社平工资预期值", amount(lifestyle.get("retirementStandardBaseMonthly"))],
        ["距退休时间", f"{basic.get('yearsToRetirement')} 年"],
        ["采用通胀率", rate(lifestyle.get("inflationRate"))],
        ["居住成本系数", text(lifestyle.get("housingMultiplier"))],
        ["退休起点月预算", amount(lifestyle.get("monthlyAtRetirement"))],
        ["退休起点年预算", amount(lifestyle.get("annualAtRetirement"))],
    ]
    stage_summary_rows = [
        [
            item["label"],
            item["ageRange"],
            amount(item["annualAtStageStart"]),
            f"{item['years']} 年",
            amount(item["totalStageExpense"]),
            item["pressure"],
        ]
        for item in lifestyle.get("stageSummaries", [])
    ]

    matrix_rows = []
    for item in lifestyle.get("stageCashflowMatrix", []):
        values = {stage["stageKey"]: amount(stage["annual"]) for stage in item.get("stages", [])}
        matrix_rows.append([item["label"]] + [values.get(key, "") for key in stage_keys])

    cost_rows = [
        [item["label"], item.get("includes", ""), item.get("reason", ""), item.get("standard", ""), item.get("review", "")]
        for item in lifestyle.get("stageCashflowMatrix", [])
    ]
    evidence_rows = [
        [item.get("category", ""), item.get("relatedItems", ""), item.get("evidence", ""), item.get("source", ""), item.get("usage", "")]
        for item in lifestyle.get("cityLivingCostEvidence", [])
    ]
    source_rows = [
        [
            item.get("name", ""),
            item.get("assetType", ""),
            amount(item.get("monthlyAmount")),
            amount(item.get("annualAmount")),
            item.get("certainty", ""),
        ]
        for item in gap.get("stableIncomeSources", [])
    ]
    gap_rows = [
        [
            item.get("ageRange", ""),
            amount(item.get("annualLifeTarget")),
            amount(item.get("floorLivingNeed")),
            amount(item.get("certainIncome")),
            amount(item.get("certaintyGap")),
            amount(item.get("qualityGap")),
        ]
        for item in gap.get("stageGapCashflow", [])
    ]
    asset_risk_rows = [[item.get("assetType", ""), item.get("includeRule", "")] for item in gap.get("assetRiskMatrix", [])]
    inventory_rows = [
        [item.get("assetType", ""), item.get("fields", ""), item.get("includeCondition", "")]
        for item in gap.get("assetInventoryTemplate", [])
    ]

    scenario_detail_lines: list[str] = []
    for item in scenarios:
        scenario_detail_lines.extend(
            [
                f"#### {item['label']}口径",
                "",
                f"- 当前全口径工资锚点：{amount(basic['socialAvgSalaryNow'])}/月。",
                f"- 退休时计发基数估算：{amount(basic['socialAvgSalaryNow'])} ×（1 + {rate(item['salaryGrowthRate'])}）^{basic['yearsToRetirement']} = {amount(item['projectedSocialAvgSalaryMonthly'])}/月。",
                f"- 退休时缴费基数：{amount(basic['contributionBaseNow'])} ×（1 + {rate(item['salaryGrowthRate'])}）^{basic['yearsToRetirement']} = {amount(item['projectedContributionBaseMonthly'])}/月。",
                f"- 基础养老金：（{amount(item['projectedSocialAvgSalaryMonthly'])} + {amount(item['projectedContributionBaseMonthly'])}）÷ 2 × {item['totalContributionYears']} 年 × 1% = {amount(item['basicPensionMonthly'])}/月。",
                f"- 退休时个人账户余额：当前余额增长 {amount(item['grownCurrentBalanceAtRetirement'])} + 未来个人缴费累计 {amount(item['futurePersonalContributionsAtRetirement'])} = {amount(item['personalAccountBalanceAtRetirement'])}。",
                f"- 个人账户养老金：{amount(item['personalAccountBalanceAtRetirement'])} ÷ {basic['payoutMonths']} = {amount(item['personalAccountMonthly'])}/月。",
                f"- 名义合计：{amount(item['basicPensionMonthly'])} + {amount(item['personalAccountMonthly'])} = {amount(item['totalMonthly'])}/月。",
                f"- 折算今天购买力：{amount(item['totalMonthly'])} ÷（1 + {rate(item['inflationRate'])}）^{basic['yearsToRetirement']} = {amount(item['todayPurchasingPowerMonthly'])}/月。",
                "",
            ]
        )

    lines: list[str] = [
        f"# {profile.get('customerName', '客户')}养老规划分步报告",
        "",
        "> 本报告基于您提供的信息做估算，用于养老咨询沟通。",
        "",
        "## 报告 1：养老金测算报告",
        "",
        "### 一、这份报告解决什么问题",
        "",
        "这份报告只回答一件事：按您目前的参保信息和退休城市估算，退休后社保养老金大概能提供多少稳定现金流。",
        "",
        *rows_to_table(
            ["步骤", "要解决的问题", "对应章节"],
            [
                ["第一步", "确认参保地、退休地、缴费基数、已缴年限和个人账户余额。", "测算前提"],
                ["第二步", "写出基础养老金和个人账户养老金公式。", "计算公式"],
                ["第三步", "用悲观、中性、积极三档估算。", "测算结果"],
                ["第四步", "判断社保养老金能覆盖多少退休生活支出。", "结论与待确认"],
            ],
        ),
        "",
        "### 二、测算前提",
        "",
        *rows_to_table(
            ["测算前提", "采用数据"],
            [
                ["退休城市", text(basic.get("city"))],
                ["当前全口径工资锚点", amount(basic.get("socialAvgSalaryNow"))],
                ["当前社保缴费基数", amount(basic.get("contributionBaseNow"))],
                ["已缴社保年限", f"{basic.get('contributedYears')} 年"],
                ["距退休时间", f"{basic.get('yearsToRetirement')} 年"],
                ["预计累计缴费年限", f"{basic.get('totalContributionYears')} 年"],
                ["个人账户余额", f"{amount(basic.get('personalAccountBalanceNow'))}（{basic.get('personalAccountBalanceSource')}）"],
                ["退休年龄与计发月数", f"{basic.get('retirementAge')} 岁 / {basic.get('payoutMonths')} 个月"],
            ],
        ),
        "",
        "### 三、公开统计参考",
        "",
        *rows_to_table(
            ["公开统计参考", "当前可查数据"],
            [
                ["工资锚点来源", text(stat.get("wageAnchorName"))],
                ["全口径估算公式", text(stat.get("allCaliberFormula"))],
                ["非私营年平均工资", amount(stat.get("nonPrivateWageAnnual")) if stat.get("nonPrivateWageAnnual") else "待确认"],
                ["非私营工资增长", rate(stat.get("nonPrivateWageGrowth")) if stat.get("nonPrivateWageGrowth") is not None else "待确认"],
                ["私营年平均工资", amount(stat.get("privateWageAnnual")) if stat.get("privateWageAnnual") else "待确认"],
                ["私营工资增长", rate(stat.get("privateWageGrowth")) if stat.get("privateWageGrowth") is not None else "待确认"],
                ["人数权重", f"非私营 {rate(stat.get('nonPrivateEmploymentWeight'))} / 私营 {rate(stat.get('privateEmploymentWeight'))}" if stat.get("nonPrivateEmploymentWeight") is not None else "待确认"],
                ["权重口径", text(stat.get("weightMethod"))],
                ["养老金计发基数", amount(stat.get("pensionAccrualBaseMonthly")) if stat.get("pensionAccrualBaseMonthly") else "暂用全口径工资锚点估算"],
                ["当地 CPI", rate(stat.get("cpiGrowth")) if stat.get("cpiGrowth") is not None else "待确认"],
                ["口径说明", text(stat.get("note"))],
            ],
        ),
        "",
        "> 社保缴费基数和养老金计发基数不是同一个概念。缴费基数看全口径城镇单位就业人员平均工资及上下限；养老金计发基数优先看当地人社部门公布值。没有官方计发基数时，离线报告只能写“估算”，不能写成核定结果。",
        "",
        "### 四、计算公式",
        "",
        "**计算口径：**",
        "",
        "- 基础养老金按养老金计发基数、本人指数化缴费工资和累计缴费年限估算。",
        "- 社保里的社平工资采用非私营与私营就业人员平均工资加权后的全口径工资，不直接采用非私营工资。",
        "- 个人账户养老金按个人账户余额除以计发月数估算；余额未知时，用缴费基数、年限和 8% 个人缴费保守估算。",
        "- 悲观、中性、积极三档主要调整工资增速和通胀，用来看不同环境下的承压能力。",
        "",
        *rows_to_table(
            ["计算公式", "公式说明"],
            [
                ["全口径工资", "非私营平均工资 × 非私营人数权重 + 私营平均工资 × 私营人数权重"],
                ["基础养老金 / 月", "（退休时养老金计发基数 + 本人指数化缴费工资）÷ 2 × 累计缴费年限 × 1%"],
                ["个人账户养老金 / 月", "退休时个人账户余额 ÷ 退休年龄对应计发月数"],
                ["退休时个人账户余额", "当前余额按退休前回报率增长 + 未来个人缴费累计增长"],
                ["今天购买力", "退休时名义养老金 ÷（1 + 通胀率）^ 距退休年数"],
            ],
        ),
        "",
        "### 五、测算结果",
        "",
        *rows_to_table(["口径", "基础养老金 / 月", "个人账户 / 月", "名义合计 / 月", "折算今天购买力 / 月"], scenario_rows),
        "",
        "### 六、三档口径代入过程",
        "",
        *scenario_detail_lines,
        "### 七、结论与待确认",
        "",
        f"- 中性口径下，预计社保养老金名义合计约 {amount(neutral['totalMonthly'])}/月，折算今天购买力约 {amount(neutral['todayPurchasingPowerMonthly'])}/月。",
        f"- 当前用 {basic['city']} 离线工资锚点估算，后续应按当地最新公开数据校准。",
        "",
        "## 报告 2：退休现金流规划报告",
        "",
        "### 一、这份报告解决什么问题",
        "",
        "这份报告把退休生活拆成可讨论的预算，而不是只问一句“退休后想花多少钱”。",
        "",
        "> 为什么您应该知道：养老金够不够，不是看绝对金额，而是看它能不能覆盖退休后的日常生活、医疗照护和居住成本。",
        "",
        "**您应该怎么看：**",
        "",
        "- 刚性支出优先保证，不能用乐观假设压低。",
        "- 半刚性支出可以按家庭情况调整，但不能完全忽略。",
        "- 弹性支出决定退休生活质量，可以作为后续优化空间。",
        "- 照护压力要单独看，不能只按正常年份估算。",
        "",
        "### 二、退休生活的三大标准与阶段",
        "",
        *rows_to_table(
            ["标准基础", "采用口径"],
            [
                ["社平工资预期值", amount(lifestyle.get("retirementStandardBaseMonthly"))],
                ["基本生活参考", "社平工资预期值 × 40%"],
                ["体面生活参考", "社平工资预期值 × 100%"],
                ["品质生活参考", "社平工资预期值 × 200%"],
                ["口径说明", text(lifestyle.get("retirementLivingStandardsNote"))],
            ],
        ),
        "",
        *rows_to_table(["标准", "计算口径", "退休起点月预算", "生活含义"], standard_rows),
        "",
        *rows_to_table(["阶段", "年龄参考", "状态", "核心需求", "现金流重点"], stage_rows),
        "",
        "> 年龄段是咨询规划框架，用于现金流和照护成本情景推演。真实照护等级应以专业能力评估为准。",
        "",
        "### 三、规划前提",
        "",
        *rows_to_table(["生活前提", "测算结果"], premise_rows),
        "",
        "### 四、阶段现金流计算公式",
        "",
        *rows_to_table(
            ["计算公式", "公式说明"],
            [
                ["今天口径月预算", "您提供的数值；未提供时，由退休起点目标预算折回今天购买力"],
                ["退休起点月预算", "您提供的数值按通胀折算；未提供时，按社平工资预期值 × 生活标准比例"],
                ["阶段基础月预算", "退休起点月预算 ×（1 + 通胀率）^ 阶段起点距退休年数"],
                ["阶段单项月支出", "阶段基础月预算 × 项目基础权重 × 阶段调整系数 × 居住 / 照护修正"],
                ["阶段单项年支出", "阶段单项月支出 × 12"],
                ["阶段年度预算", "Σ 阶段内所有支出项目年支出"],
                ["阶段总支出", "阶段年度预算 × 阶段年数"],
            ],
        ),
        "",
        "### 五、代入过程",
        "",
        f"- 退休起点月预算：今天口径 {amount(lifestyle.get('monthlyToday'))} ×（1 + {rate(lifestyle.get('inflationRate'))}）^{lifestyle.get('yearsToRetirement')} = {amount(lifestyle.get('monthlyAtRetirement'))}。",
        f"- 退休起点年预算：{amount(lifestyle.get('monthlyAtRetirement'))} × 12 = {amount(lifestyle.get('annualAtRetirement'))}。",
        "- 阶段基础月预算、阶段单项年支出和阶段总支出见下方矩阵。",
        "",
        "### 六、阶段现金流矩阵",
        "",
        *rows_to_table(["支出项目"] + stage_labels, matrix_rows),
        "",
        "### 七、阶段总预算与压力点",
        "",
        *rows_to_table(["阶段", "年龄", "年度预算", "阶段年数", "阶段总支出", "主要压力"], stage_summary_rows),
        "",
        "### 八、照护压力与调整顺序",
        "",
        "- 正常年份看日常生活、基础医疗、居住和社交支出。",
        "- 压力年份要考虑慢病、康复、陪护、适老化改造等集中支出。",
        "- 调整顺序：先保刚性支出，再调半刚性支出，最后压缩弹性支出。",
        "",
        "### 九、数据来源与口径限制",
        "",
        "- 本报告的生活预算是养老咨询规划假设，不是统计部门发布的居民消费结论。",
        "- 基本生活 40% 的参考来自国际劳工组织 ILO C102 老年给付最低保障思想。",
        "- 养老阶段是“年龄阶段 + 能力状态”的咨询规划框架，真实照护等级应以专业能力评估为准。",
        "- 通胀率沿用养老金测算报告中的中性口径。",
        "- 阶段现金流矩阵里的阶段系数用于咨询压力测试，您可以结合自己的健康状况、家庭照护资源和所在城市服务价格进一步调整。",
        "- 您已明确提供的目标月支出优先于系统默认生活标准。",
        "- 您可以逐项确认预算是否符合自己的生活方式。",
        "",
        "### 十、费用科目测算底稿",
        "",
        "这一节供您了解现金流支出包括哪些科目。您如果觉得某个数字偏高或偏低，可以按自己的实际账单、生活习惯和所在城市价格继续调整。",
        "",
        *rows_to_table(["科目", "包含内容", "纳入原因", "计算标准", "影响指标"], cost_rows),
        "",
        "### 十一、城市生活成本查证清单",
        "",
        "基于您的退休城市，我们根据公开信息整理一些数据样本，用来支持本报告的生活成本测算。您也可以用自己的账单、消费记录或所在区域报价来校准这些预算。",
        "",
        *rows_to_table(["查证项", "关联科目", "应查什么", "推荐来源", "测算中的用途"], evidence_rows),
        "",
        "## 报告 3：养老金来源与缺口报告",
        "",
        "### 一、这份报告解决什么问题",
        "",
        "这份报告要回答：退休后每个阶段还差多少钱，哪些钱真的能用来补这个缺口。",
        "",
        "### 二、目标生活、底线生活与确定性缺口",
        "",
        *rows_to_table(
            ["缺口概念", "计算口径"],
            [
                ["目标生活支出", "第二份现金流报告测算出的阶段年度生活目标"],
                ["底线生活需求", "目标生活支出 × 80%，且不能低于刚性支出"],
                ["确定性缺口", "底线生活需求扣除社保、年金、租金等确定收入后的缺口"],
                ["品质缺口", "目标生活支出高于底线生活需求的部分，可以按生活状态调整"],
            ],
        ),
        "",
        "### 三、每年待准备的养老金缺口",
        "",
        "#### 确定收入来源",
        "",
        *rows_to_table(["收入来源", "类型", "月金额", "年金额", "说明"], source_rows),
        "",
        "#### 年度缺口现金流",
        "",
        *rows_to_table(["年龄阶段", "年度生活目标", "底线生活需求", "年度确定收入", "确定性缺口", "品质缺口"], gap_rows),
        "",
        "### 四、养老资产的 4 个确定性标准",
        "",
        *rows_to_table(
            ["确定性标准", "判断含义"],
            [
                ["确定时间", "退休时点或约定年龄能不能拿到"],
                ["确定形式", "能不能转化为现金、养老金、租金或其他可用于生活的现金流"],
                ["确定金额", "能不能大致确认到手金额，而不是只看当前估值"],
                ["确定流向", "钱最终是不是进入本人可支配的养老账户或现金流"],
            ],
        ),
        "",
        "### 五、资产类型与风险矩阵",
        "",
        *rows_to_table(["资产类型", "计入规则"], asset_risk_rows),
        "",
        "### 六、规划前提",
        "",
        *rows_to_table(
            ["规划前提", "当前采用数据"],
            [
                ["社保假设", f"中性口径社保养老金 {amount(neutral['totalMonthly'])}/月"],
                ["退休生活金额", f"{amount(lifestyle.get('annualAtRetirement'))}/年"],
                ["退休年龄", f"{profile.get('retirementAge')} 岁"],
                ["预期寿命", f"{profile.get('expectedLongevity')} 岁"],
                ["底线生活系数", percent(gap.get("floorLivingRatio", 0.8))],
                ["退休后收益率", rate(gap.get("postRetirementReturnRate"))],
            ],
        ),
        "",
        "### 七、资产清单与可纳入养老资产核算",
        "",
        *rows_to_table(["资产类型", "需要补充的信息", "计入条件"], inventory_rows),
        "",
        "### 八、结论与待补动作",
        "",
        f"- 当前确定性缺口目标资本：{amount(gap.get('rigidTargetCapital'))}。",
        f"- 当前品质缺口目标资本：{amount(gap.get('flexibleTargetCapital'))}。",
        f"- 当前待补资本：{amount(gap.get('remainingCapitalGap'))}。",
        "- 如果某项房产、股票或基金后续能够满足 4 个确定性标准，可以再纳入养老资产核算。",
        "",
        "## 报告 4：养老方案设计报告",
        "",
        "### 一、这份报告解决什么问题",
        "",
        "前三份报告已经回答了能领多少钱、要花多少钱、缺口在哪里。第四份报告不重复计算，而是把养老方案按生、老、病、死四件事展开。",
        "",
        "> 为什么您应该知道：生解决退休生活和钱，老解决护理资源，病解决保障方案，死解决传承安排。",
        "",
        "### 二、方案前提",
        "",
        *rows_to_table(
            ["方案依据", "当前测算"],
            [
                ["中性口径社保养老金", f"{amount(neutral['totalMonthly'])}/月"],
                ["退休生活目标", lifestyle["targetLabel"]],
                ["退休起点年度生活目标", amount(lifestyle["annualAtRetirement"])],
                ["年度确定收入", amount(gap["annualStableIncome"])],
                ["确定性缺口目标资本", amount(gap["rigidTargetCapital"])],
                ["品质缺口目标资本", amount(gap["flexibleTargetCapital"])],
                ["目标资金池", amount(gap["targetCapital"])],
                ["待补资本", amount(gap["remainingCapitalGap"])],
                ["建议额外年度补充", f"{amount(gap['requiredAdditionalAnnualContribution'])}/年"],
            ],
        ),
        "",
        solution.get("solutionSummary", ""),
        "",
        "### 三、方案设计原则",
        "",
        *bullet_list(solution.get("solutionPrinciples", [])),
        "",
        "### 四、生：退休后的生活和钱",
        "",
        solution.get("lifeModule", {}).get("focus", ""),
        "",
        *rows_to_table(
            ["资金池", "这笔钱负责什么", "目标金额", "接下来怎么做"],
            [
                [row["bucket"], row["responsibility"], amount(row["target"]), row["action"]]
                for row in solution.get("fundingBuckets", [])
            ],
        ),
        "",
        *rows_to_table(
            ["项目", "当前测算", "说明"],
            solution.get("capitalActionPlan", []),
        ),
        "",
        "### 五、老：护理状态和照护资源",
        "",
        solution.get("agingCareModule", {}).get("summary", ""),
        "",
        *rows_to_table(
            ["护理状态", "可能出现的情况", "会用到的资源", "费用参考", "接下来怎么做"],
            [
                [row["level"], row["state"], row["resourceNeed"], row["costReference"], row["action"]]
                for row in solution.get("agingCareModule", {}).get("careLevels", [])
            ],
        ),
        "",
        *rows_to_table(["城市资源", "您需要确认的事", "和方案的关系"], solution.get("agingCareModule", {}).get("cityResourceChecklist", [])),
        "",
        "### 六、病：保障方案怎么接住风险",
        "",
        solution.get("illnessProtectionModule", {}).get("summary", ""),
        "",
        *rows_to_table(
            ["风险情况", "常见场景", "可以用什么保障", "钱怎么报", "重点看什么", "还需要确认"],
            [
                [row["risk"], row["scene"], row["tool"], row["coveragePath"], row["keyLimit"], row["status"]]
                for row in solution.get("illnessProtectionModule", {}).get("riskMatrix", [])
            ],
        ),
        "",
        "### 七、死：传承安排怎么落地",
        "",
        solution.get("legacyTransferModule", {}).get("summary", ""),
        "",
        *rows_to_table(
            ["资产", "先问清楚什么", "可以用什么方式", "要做到什么程度", "接下来怎么做"],
            [
                [row["asset"], row["currentQuestion"], row["tool"], row["certainty"], row["action"]]
                for row in solution.get("legacyTransferModule", {}).get("transferMatrix", [])
            ],
        ),
        "",
        "### 八、分阶段行动计划",
        "",
        *rows_to_table(
            ["阶段", "年龄", "重点", "动作"],
            [
                [row["stage"], row["ageRange"], row["focus"], row["action"]]
                for row in solution.get("actionTimeline", [])
            ],
        ),
        "",
        "### 九、估算口径与风险提示",
        "",
        "> 这一节不是免责套话，而是告诉您哪些数字是确定信息，哪些数字只是当前阶段的估算。",
        "",
        *bullet_list(result.get("assumptions", [])),
        "- 本报告为养老咨询测算，不是收益承诺。",
        "- 社保养老金以当前信息和通用公式估算，最终以社保部门核定为准。",
        "- 未提供的数据会按保守口径估算，您可以结合真实账单和最新公开数据继续校准。",
        "- 房产估值不直接计入养老资本，只有计划出售净额或稳定租金才计入。",
    ]
    return "\n".join(lines)


def calculate(case: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_case(case)
    basic = calculate_basic_pension(normalized)
    lifestyle = calculate_lifestyle_cashflow(normalized, basic)
    gap = calculate_source_gap(normalized, basic, lifestyle)
    solution = design_solution(normalized, gap)
    result = {
        "clientProfile": normalized["clientProfile"],
        "basicPensionEstimate": basic,
        "lifestyleCashflow": lifestyle,
        "sourceAndGap": gap,
        "solutionDesign": solution,
        "assumptions": [
            "地区全口径工资使用离线锚点估算；养老金计发基数正式值以当地人社部门公布为准。",
            "基础养老金与个人账户养老金按通用公式估算。",
            "社保个人账户未知时，按缴费基数、年限和 8% 个人缴费估算。",
            "房产不直接计入养老资本，只有计划出售净额或稳定租金才计入。",
        ],
        "missingFields": detect_missing_fields(normalized),
    }
    result["summaryMarkdown"] = build_summary_markdown(result)
    return result


def detect_missing_fields(case: dict[str, Any]) -> list[dict[str, str]]:
    profile = case["clientProfile"]
    sources = case.get("sourceAndGapInput", {})
    required = [
        ("clientProfile.customerName", profile.get("customerName"), "客户称呼"),
        ("clientProfile.currentAge", profile.get("currentAge"), "当前年龄"),
        ("clientProfile.monthlyIncome", profile.get("monthlyIncome"), "当前月收入"),
        ("clientProfile.contributionBase", profile.get("contributionBase"), "社保缴费基数"),
        ("clientProfile.contributedYears", profile.get("contributedYears"), "已缴社保年限"),
    ]
    missing = []
    for key, value, label in required:
        if value in ("", None) or safe_float(value) <= 0 and key not in {"clientProfile.customerName"}:
            missing.append({"field": key, "label": label, "reason": "缺少后会影响核心测算。"})
    optional = [
        ("sourceAndGapInput.enterpriseAnnuityMonthly", "企业年金"),
        ("sourceAndGapInput.occupationalPensionMonthly", "职业年金"),
        ("sourceAndGapInput.personalPensionMonthly", "个人养老金"),
    ]
    for key, label in optional:
        short = key.split(".")[-1]
        if short not in sources:
            missing.append({"field": key, "label": label, "reason": "未提供时暂按 0 估算。"})
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate offline pension planning report.")
    parser.add_argument("case_json", help="Input pension case JSON.")
    parser.add_argument("--out", default="", help="Output calculated JSON path.")
    parser.add_argument("--markdown", default="", help="Output Markdown report path.")
    args = parser.parse_args()

    case = json.loads(Path(args.case_json).read_text(encoding="utf-8"))
    result = calculate(case)
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(result["summaryMarkdown"], encoding="utf-8")
    if not args.out and not args.markdown:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
