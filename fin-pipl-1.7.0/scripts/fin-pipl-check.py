#!/usr/bin/env python3
"""
Fin-PIPL — 金融行业个人信息保护合规检查工具
基于《个人信息保护法》《个人金融信息保护规范》(JR/T 0171)、《金融数据安全分级指南》(JR/T 0197)

适用场景：银行 / 证券 / 保险 / 支付
运行模式：纯本地，无网络请求
"""

import argparse
import datetime
import json
import sys
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ============================================================
# 数据模型
# ============================================================

@dataclass
class CheckResult:
    check_id: str
    description: str
    severity: str       # "PASS" / "WARN" / "FAIL" / "N/A"
    passed: bool
    details: str
    recommendation: str
    regulation_ref: str
    applicable: bool = True


def not_applicable(check_id: str, description: str, details: str,
                   regulation_ref: str = "") -> CheckResult:
    """构造一条「不适用」结果。

    判据（全项目统一，只此一条）：
        **该检查项针对的业务活动或技术机制，在本机构不存在 ⇒ 判「不适用」。**
    与之相对，「业务存在但措施未落实」仍判 WARN / FAIL —— 那是应做未做，不是不适用。

    不适用项**不计入合规率分母**，避免用「没检查」冒充「合规」。
    """
    return CheckResult(check_id, description, "N/A", False, details, "",
                       regulation_ref, applicable=False)


# ============================================================
# 《金融产品网络营销管理办法》通用检查逻辑（银行/证券/保险/支付共用同一组问答）
# ============================================================
# 引用口径与全项目一致：该办法属「其余法规」⇒ **只写名称，不写章条号**。

def _online_marketing(enabled, content_clean, staff_qualified, third_party_managed,
                      check_id: str, description: str) -> CheckResult:
    """网络营销合规（通用）。

    `enabled` 为前置问题：未通过互联网开展金融产品营销 ⇒ 本项不适用。
    """
    ref = "《金融产品网络营销管理办法》"
    if not enabled:
        return not_applicable(
            check_id, description,
            "未通过互联网开展金融产品营销，本项不适用", ref
        )

    issues = []
    if not content_clean:
        issues.append("网络营销内容未排查「低风险」「低门槛」「秒到账」「高收益」「低利率」「无成本」等诱导性用语")
    if not staff_qualified:
        issues.append("公众号/直播/短视频营销人员非本机构从业人员、未具备业务资格或未获本机构授权")
    if not third_party_managed:
        issues.append("委托第三方互联网平台营销，未完成事前评估、书面协议与持续跟踪，或第三方介入销售环节")

    passed = not issues
    severity = "FAIL" if not content_clean else ("PASS" if passed else "WARN")
    return CheckResult(
        check_id, description, severity, passed,
        "；".join(issues) if issues else "网络营销合规",
        "排查诱导性用语、营销人员须为本机构持牌从业人员并获授权、"
        "委托第三方须事前评估并签订书面协议",
        ref
    )


# ============================================================
# 个人信息保护影响评估（PIPL Art.55、Art.56）通用检查逻辑
# ============================================================
# ⚠️ 本项是**自述式**检查：工具无法核实机构是否真的留存了评估报告。
#    「留存不短于三年」在**事前**评估的当口尚未届期，任何工具都核实不了，
#    能问的只有"是否已设立不短于三年的保存期限并照此留存"。
#    问的是**机制是否存在**，不是宣称已经核实。

def _pipia(triggered, done, check_id: str, description: str) -> CheckResult:
    """个人信息保护影响评估（通用）。

    `triggered` 为前置问题：不涉及任一触发情形 ⇒ 本项不适用。
    """
    ref = "PIPL Art.55, 56"
    if not triggered:
        return not_applicable(
            check_id, description,
            "不涉及需事前开展个人信息保护影响评估的情形，本项不适用", ref
        )

    issues = []
    if not done:
        issues.append("已涉及触发情形，但未在事前开展个人信息保护影响评估，"
                      "或未按不短于三年的期限留存评估报告与处理记录")

    passed = not issues
    severity = "FAIL" if not done else "PASS"
    return CheckResult(
        check_id, description, severity, passed,
        "；".join(issues) if issues else "已事前完成影响评估并留存记录",
        "对触发情形事前开展影响评估，内容含处理目的是否合法正当必要、"
        "对个人权益的影响与安全风险、保护措施是否有效且与风险相适应；"
        "评估报告与处理情况记录按不短于三年的期限留存",
        ref
    )


@dataclass
class CheckReport:
    tool_name: str
    version: str
    timestamp: str
    scenario: str
    summary: dict
    items: list
    raw_items: list = field(default_factory=list)
    comparison: Optional[dict] = None
    demo: bool = False

    def to_dict(self):
        return {
            "tool": self.tool_name,
            "version": self.version,
            "demo": self.demo,
            "timestamp": self.timestamp,
            "scenario": self.scenario,
            "summary": self.summary,
            "comparison": self.comparison,
            "items": self.items,
        }


# ============================================================
# 金融行业检查项
# ============================================================

class FinPIPLChecker:
    """金融行业 PIPL 合规检查引擎"""

    SCENARIOS = {
        "banking": "银行业务",
        "securities": "证券/基金业务",
        "insurance": "保险业务",
        "payment": "支付业务",
    }

    def get_scenarios(self):
        return list(self.SCENARIOS.items())

    # ---- 银行业务检查项 ----

    def _bank_account_open(self, data: dict) -> CheckResult:
        """开户环节的告知同意"""
        has_privacy_notice = data.get("has_privacy_notice", False)
        has_separate_consent = data.get("has_separate_consent", False)
        consent_method = data.get("consent_method", "")
        sensitive_items = data.get("sensitive_items", [])

        issues = []
        if not has_privacy_notice:
            issues.append("未提供独立的隐私政策/个人信息告知")
        if not has_separate_consent:
            issues.append("未单独获取个人信息授权（与非必要服务捆绑）")
        if "biometric" in sensitive_items and not has_separate_consent:
            issues.append("人脸/指纹等生物识别信息未单独同意")
        if consent_method == "pre_checked":
            issues.append("同意方式为默认勾选，违反单独同意要求")

        passed = not issues
        severity = "FAIL" if not has_privacy_notice else ("PASS" if passed else "WARN")
        return CheckResult(
            "bank_account_open", "开户环节 - 告知同意检查",
            severity, passed,
            "；".join(issues) if issues else "开户告知同意合规",
            "提供独立隐私政策、对敏感信息单独获取同意、禁止默认勾选",
            "PIPL Art.17, 23; JR/T 0171"
        )

    def _bank_credit(self, data: dict) -> CheckResult:
        """信贷信息处理"""
        has_loan_authorization = data.get("has_loan_authorization", False)
        limits_info_scope = data.get("limits_info_scope", False)
        has_post_lending_notice = data.get("has_post_lending_notice", False)
        shares_with_third_party = data.get("shares_with_third_party", False)
        third_party_consent = data.get("third_party_consent", False)

        issues = []
        if not has_loan_authorization:
            issues.append("未获取信贷信息处理授权")
        if not limits_info_scope:
            issues.append("信息收集范围超出信贷业务必需")
        if not has_post_lending_notice:
            issues.append("贷后管理中的信息使用未充分告知")
        if shares_with_third_party and not third_party_consent:
            issues.append("向第三方（担保/催收/评估）共享信息未单独授权")

        passed = not issues
        severity = "FAIL" if not (has_loan_authorization and limits_info_scope) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "bank_credit", "信贷业务 - 个人信息处理合规",
            severity, passed,
            "；".join(issues) if issues else "信贷信息处理合规",
            "明确授权范围、遵循最小必要、第三方共享需单独同意",
            "PIPL Art.6, 17, 23"
        )

    def _bank_credit_report(self, data: dict) -> CheckResult:
        """征信查询与报送"""
        has_authorization = data.get("has_authorization", False)
        has_purpose_limitation = data.get("has_purpose_limitation", False)
        has_dispute_mechanism = data.get("has_dispute_mechanism", False)
        query_frequency = data.get("query_frequency", "normal")

        issues = []
        if not has_authorization:
            issues.append("未获得征信查询授权书")
        if not has_purpose_limitation:
            issues.append("征信信息使用目的不明确（如贷后管理 vs 贷前审批混用）")
        if not has_dispute_mechanism:
            issues.append("未建立征信异议处理机制")
        if query_frequency != "normal":
            issues.append("征信查询频率异常，存在越权查询风险")

        passed = not issues
        severity = "FAIL" if not (has_authorization and has_purpose_limitation) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "bank_credit_report", "征信信息 - 查询与报送合规",
            severity, passed,
            "；".join(issues) if issues else "征信管理合规",
            "取得书面授权、限定查询用途、建立异议处理机制",
            "《征信业管理条例》"
        )

    def _bank_marketing(self, data: dict) -> CheckResult:
        """信用卡营销"""
        has_marketing_consent = data.get("has_marketing_consent", False)
        opt_out_available = data.get("opt_out_available", False)
        uses_push_notification = data.get("uses_push_notification", False)
        shares_for_marketing = data.get("shares_for_marketing", False)
        marketing_third_party_consent = data.get("marketing_third_party_consent", False)

        issues = []
        if not has_marketing_consent:
            issues.append("营销推广未获得用户同意")
        if not opt_out_available:
            issues.append("未提供便捷的退订/拒绝渠道")
        if uses_push_notification and not opt_out_available:
            issues.append("推送通知无关闭选项")
        if shares_for_marketing and not marketing_third_party_consent:
            issues.append("将个人信息用于第三方营销共享，未取得单独同意")

        passed = not issues
        severity = "FAIL" if (shares_for_marketing and not marketing_third_party_consent) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "bank_marketing", "信用卡营销 - 个人信息使用合规",
            severity, passed,
            "；".join(issues) if issues else "营销合规",
            "获取营销同意、提供便捷退订、第三方营销共享需单独同意",
            "PIPL Art.14, 24; 《金融消费者权益保护实施办法》"
        )

    def _bank_data_share(self, data: dict) -> CheckResult:
        """账户信息共享"""
        group_sharing = data.get("group_sharing", False)
        group_notice = data.get("group_notice", False)
        third_party_sharing = data.get("third_party_sharing", False)
        third_party_consent = data.get("third_party_consent", False)

        if not group_sharing and not third_party_sharing:
            return not_applicable(
                "bank_data_share", "账户信息共享 - 第三方与集团内部合规",
                "既无集团内共享，也未向第三方提供个人金融信息，本项不适用",
                "PIPL Art.21, 23; JR/T 0171"
            )

        issues = []
        if group_sharing and not group_notice:
            issues.append("集团内共享个人金融信息未充分告知用户")
        if third_party_sharing and not third_party_consent:
            issues.append("向第三方提供个人金融信息未单独同意")

        passed = not (group_sharing and not group_notice) and not (third_party_sharing and not third_party_consent)
        severity = "PASS" if passed else "FAIL"
        return CheckResult(
            "bank_data_share", "账户信息共享 - 第三方与集团内部合规",
            severity, passed,
            "；".join(issues) if issues else "信息共享合规",
            "集团共享需告知并明确接收方范围、第三方提供需单独同意",
            "PIPL Art.21, 23; JR/T 0171"
        )

    def _bank_data_classification(self, data: dict) -> CheckResult:
        """个人金融信息分类分级"""
        has_classification = data.get("has_classification", False)
        c3_protection = data.get("c3_protection", False)
        c2_protection = data.get("c2_protection", False)
        has_data_map = data.get("has_data_map", False)

        issues = []
        if not has_classification:
            issues.append("未按 JR/T 0197 建立金融数据分类分级制度")
        if not has_data_map:
            issues.append("未建立个人金融信息数据资产地图")
        if not c3_protection:
            issues.append("C3 类信息（账户鉴别信息）安全保护措施不足")
        if not c2_protection:
            issues.append("C2 类信息（可识别身份信息）安全保护措施不足")

        passed = not issues
        severity = "FAIL" if not (has_classification and c3_protection) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "bank_data_classification", "个人金融信息 - 分类分级合规",
            severity, passed,
            "；".join(issues) if issues else "分类分级合规",
            "按 JR/T 0197 完成分类分级，C3类信息重点保护",
            "PIPL Art.51; JR/T 0197; JR/T 0171"
        )

    def _bank_automated_decision(self, data: dict) -> CheckResult:
        """自动化决策"""
        uses_auto_decision = data.get("uses_auto_decision", False)
        has_disclosure = data.get("has_disclosure", False)
        opt_out_available = data.get("opt_out_available", False)
        has_explanation = data.get("has_explanation", False)

        if not uses_auto_decision:
            return not_applicable(
                "bank_automated_decision", "自动化决策 - 合规检查",
                "未使用自动化决策（如授信模型、评分卡），本项不适用",
                "PIPL Art.24, 73"
            )

        issues = []
        if not has_disclosure:
            issues.append("未告知自动化决策的逻辑、目的和影响")
        if not opt_out_available:
            issues.append("未提供拒绝仅通过自动化决策方式作出决定的权利")
        if not has_explanation:
            issues.append("未提供自动化决策结果的解释说明机制")

        passed = not issues
        severity = "FAIL" if not (has_disclosure and opt_out_available) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "bank_automated_decision", "自动化决策 - 合规检查",
            severity, passed,
            "；".join(issues) if issues else "自动化决策合规",
            "告知逻辑与影响、提供拒绝权、支持解释说明",
            "PIPL Art.24, 73"
        )

    def _bank_data_retention(self, data: dict) -> CheckResult:
        """数据留存与删除"""
        has_retention_policy = data.get("has_retention_policy", False)
        auto_delete = data.get("auto_delete", False)
        account_cancellation = data.get("account_cancellation", False)
        can_request_delete = data.get("can_request_delete", False)

        issues = []
        if not has_retention_policy:
            issues.append("未制定个人信息留存期限制度")
        if not auto_delete:
            issues.append("未设置到期自动删除/匿名化机制")
        if not account_cancellation:
            issues.append("账户注销后个人信息未同步删除")
        if not can_request_delete:
            issues.append("未提供用户主动删除个人信息的渠道")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "bank_data_retention", "数据留存与删除 - 合规检查",
            severity, passed,
            "；".join(issues) if issues else "数据留存合规",
            "短留存期限、到期自动处置、注销即删除",
            "PIPL Art.19, 47"
        )

    # ---- 证券/基金业务检查项 ----

    def _sec_suitability(self, data: dict) -> CheckResult:
        """适当性管理"""
        kyc_scope_reasonable = data.get("kyc_scope_reasonable", False)
        has_privacy_notice = data.get("has_privacy_notice", False)
        kyc_retention_limited = data.get("kyc_retention_limited", False)

        issues = []
        if not kyc_scope_reasonable:
            issues.append("KYC信息收集范围超出适当性管理必需")
        if not has_privacy_notice:
            issues.append("KYC信息收集未充分告知用途")
        if not kyc_retention_limited:
            issues.append("KYC信息留存期限未明确限定")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "sec_suitability", "适当性管理 - KYC信息收集合规",
            severity, passed,
            "；".join(issues) if issues else "适当性管理合规",
            "KYC信息收集最小必要、告知用途、限定留存",
            "PIPL Art.6, 17, 19; 《证券期货投资者适当性管理办法》"
        )

    def _sec_trade_info(self, data: dict) -> CheckResult:
        """交易信息保护"""
        encrypt_transmission = data.get("encrypt_transmission", False)
        access_control = data.get("access_control", False)
        log_audit = data.get("log_audit", False)

        issues = []
        if not encrypt_transmission:
            issues.append("交易信息传输未加密")
        if not access_control:
            issues.append("交易信息访问权限控制不足")
        if not log_audit:
            issues.append("交易信息访问日志不完整")

        passed = not issues
        severity = "FAIL" if not (encrypt_transmission and access_control) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "sec_trade_info", "交易信息 - 安全保护合规",
            severity, passed,
            "；".join(issues) if issues else "交易信息安全保护合规",
            "加密传输、严格权限控制、完整审计日志",
            "PIPL Art.51; JR/T 0171"
        )

    def _sec_investor_share(self, data: dict) -> CheckResult:
        """投资者信息共享"""
        csdc_sharing = data.get("csdc_sharing", False)
        csdc_notice = data.get("csdc_notice", False)
        custodian_sharing = data.get("custodian_sharing", False)
        custodian_notice = data.get("custodian_notice", False)

        if not csdc_sharing and not custodian_sharing:
            return not_applicable(
                "sec_investor_share", "投资者信息 - 登记结算共享合规",
                "既未向中国结算报送，也未向托管银行传输投资者信息，本项不适用",
                "PIPL Art.17, 23"
            )

        issues = []
        if csdc_sharing and not csdc_notice:
            issues.append("向中国结算报送信息未充分告知投资者")
        if custodian_sharing and not custodian_notice:
            issues.append("向托管银行传输信息未告知投资者")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "sec_investor_share", "投资者信息 - 登记结算共享合规",
            severity, passed,
            "；".join(issues) if issues else "信息共享合规",
            "明确告知信息共享的必要性和接收方",
            "PIPL Art.17, 23"
        )

    def _sec_robo_advisor(self, data: dict) -> CheckResult:
        """智能投顾"""
        has_algorithm_filing = data.get("has_algorithm_filing", False)
        has_risk_warning = data.get("has_risk_warning", False)
        has_human_override = data.get("has_human_override", False)

        issues = []
        if not has_algorithm_filing:
            issues.append("算法推荐服务未备案")
        if not has_risk_warning:
            issues.append("智能投顾建议未提示算法风险")
        if not has_human_override:
            issues.append("未提供人工投顾替代选项")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "sec_robo_advisor", "智能投顾 - 自动化决策合规",
            severity, passed,
            "；".join(issues) if issues else "智能投顾合规",
            "算法备案、风险提示、提供人工替代",
            "PIPL Art.24; 《互联网信息服务算法推荐管理规定》"
        )

    def _sec_marketing(self, data: dict) -> CheckResult:
        """营销推介合规"""
        marketing_consent = data.get("sec_marketing_consent", False)
        opt_out = data.get("sec_marketing_opt_out", False)
        personalized_push = data.get("sec_personalized_push", False)
        third_party_marketing = data.get("sec_third_party_marketing", False)
        third_party_consent = data.get("sec_third_party_marketing_consent", False)

        issues = []
        if not marketing_consent:
            issues.append("产品推介/基金销售营销未取得投资者同意")
        if not opt_out:
            issues.append("未提供便捷的退订/拒绝渠道")
        if personalized_push and not opt_out:
            issues.append("基于个人特征的定向推送未提供不针对个人特征的选项")
        if third_party_marketing and not third_party_consent:
            issues.append("向第三方提供投资者信息用于营销未取得单独同意")

        passed = not issues
        severity = "FAIL" if (third_party_marketing and not third_party_consent) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "sec_marketing", "营销推介 - 个人信息使用合规",
            severity, passed,
            "；".join(issues) if issues else "营销推介合规",
            "取得营销同意、提供便捷退订、第三方营销共享需单独同意",
            "PIPL Art.14, 17, 23, 24"
        )

    def _sec_cross_border(self, data: dict) -> CheckResult:
        """跨境投资数据"""
        cross_border = data.get("sec_cross_border", False)
        compliant_path = data.get("sec_cross_border_path", False)
        noticed = data.get("sec_cross_border_notice", False)

        if not cross_border:
            return not_applicable(
                "sec_cross_border", "跨境投资 - 数据出境合规",
                "未涉及投资者个人信息跨境传输（如沪深港通、QDII 等），本项不适用",
                "PIPL Art.38, 39"
            )

        issues = []
        if not compliant_path:
            issues.append("未完成数据出境安全评估 / 订立标准合同 / 通过保护认证")
        if not noticed:
            issues.append("未向投资者告知境外接收方信息并取得单独同意")

        passed = not issues
        severity = "FAIL" if not compliant_path else ("PASS" if passed else "WARN")
        return CheckResult(
            "sec_cross_border", "跨境投资 - 数据出境合规",
            severity, passed,
            "；".join(issues) if issues else "跨境数据传输合规",
            "完成出境合规路径（安全评估/标准合同/认证）、履行告知并取得单独同意",
            "PIPL Art.38, 39"
        )

    # ---- 保险业务检查项 ----

    def _ins_underwriting(self, data: dict) -> CheckResult:
        """核保健康信息"""
        info_collection_reasonable = data.get("info_collection_reasonable", False)
        has_separate_consent = data.get("has_separate_consent", False)
        third_party_verification = data.get("third_party_verification", False)
        third_party_consent = data.get("third_party_consent", False)

        issues = []
        if not info_collection_reasonable:
            issues.append("健康告知问题超出核保必需范围")
        if not has_separate_consent:
            issues.append("健康信息（敏感个人信息）未取得单独同意")
        if third_party_verification and not third_party_consent:
            issues.append("委托第三方（体检/调查公司）验证信息未单独授权")

        passed = not issues
        severity = "FAIL" if not (info_collection_reasonable and has_separate_consent) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "ins_underwriting", "核保环节 - 健康信息收集合规",
            severity, passed,
            "；".join(issues) if issues else "核保信息收集合规",
            "信息收集最小必要、敏感信息单独同意、第三方授权",
            "PIPL Art.28, 29; 《保险法》"
        )

    def _ins_claim(self, data: dict) -> CheckResult:
        """理赔调查"""
        notice_purpose = data.get("notice_purpose", False)
        scope_limited = data.get("scope_limited", False)
        third_party_investigation = data.get("third_party_investigation", False)
        authorization_scope = data.get("authorization_scope", False)

        issues = []
        if not notice_purpose:
            issues.append("理赔调查目的未告知被调查人")
        if not scope_limited:
            issues.append("调查范围超出理赔必需（如调查与出险无关的健康记录）")
        if third_party_investigation and not authorization_scope:
            issues.append("委托第三方调查的授权范围不明确")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "ins_claim", "理赔调查 - 个人信息收集合规",
            severity, passed,
            "；".join(issues) if issues else "理赔调查合规",
            "明示调查目的、限定调查范围、明确第三方授权",
            "PIPL Art.6, 17, 23"
        )

    def _ins_reinsurance(self, data: dict) -> CheckResult:
        """再保险信息共享"""
        has_reinsurance = data.get("has_reinsurance", False)
        has_notice = data.get("has_notice", False)
        cross_border = data.get("cross_border", False)
        cross_border_compliant = data.get("cross_border_compliant", False)

        if not has_reinsurance:
            return not_applicable(
                "ins_reinsurance", "再保险 - 信息共享合规",
                "未涉及再保险安排，本项不适用",
                "PIPL Art.21, 23, 38"
            )

        issues = []
        if not has_notice:
            issues.append("再保险安排中的个人信息共享未告知投保人")
        if cross_border and not cross_border_compliant:
            issues.append("跨境再保险数据未完成出境合规评估")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "ins_reinsurance", "再保险 - 信息共享合规",
            severity, passed,
            "；".join(issues) if issues else "再保险信息共享合规",
            "告知再保险信息共享、跨境数据需完成出境评估",
            "PIPL Art.21, 38"
        )

    def _ins_marketing(self, data: dict) -> CheckResult:
        """保险营销推荐"""
        marketing_consent = data.get("ins_marketing_consent", False)
        opt_out = data.get("ins_marketing_opt_out", False)
        sensitive_for_marketing = data.get("ins_sensitive_for_marketing", False)
        sensitive_consent = data.get("ins_sensitive_marketing_consent", False)

        issues = []
        if not marketing_consent:
            issues.append("保单到期提醒/交叉销售未取得投保人同意")
        if not opt_out:
            issues.append("未提供便捷的退订/拒绝渠道")
        if sensitive_for_marketing and not sensitive_consent:
            issues.append("将健康/理赔信息等敏感个人信息用于营销，未另行取得单独同意")

        over_scope = sensitive_for_marketing and not sensitive_consent
        passed = not issues
        severity = "FAIL" if over_scope else ("PASS" if passed else "WARN")
        return CheckResult(
            "ins_marketing", "保险营销 - 推荐环节合规",
            severity, passed,
            "；".join(issues) if issues else "保险营销推荐合规",
            "取得营销同意、提供便捷退订、敏感信息用于营销需单独同意",
            "PIPL Art.14, 17, 24, 29"
        )

    def _ins_health_classification(self, data: dict) -> CheckResult:
        """健康数据分级"""
        classified = data.get("ins_health_classified", False)
        encrypted = data.get("ins_health_encrypted", False)
        access_audit = data.get("ins_health_access_audit", False)
        retention_limited = data.get("ins_health_retention", False)

        issues = []
        if not classified:
            issues.append("体检报告、病历等健康数据未完成分类分级")
        if not encrypted:
            issues.append("健康数据存储或传输未加密")
        if not access_audit:
            issues.append("健康数据访问未最小授权或未留存审计日志")
        if not retention_limited:
            issues.append("健康数据留存期限未明确限定")

        passed = not issues
        severity = "FAIL" if not (classified and encrypted) else ("PASS" if passed else "WARN")
        return CheckResult(
            "ins_health_classification", "健康数据 - 分级与保护合规",
            severity, passed,
            "；".join(issues) if issues else "健康数据分级保护合规",
            "完成分类分级、加密存储传输、最小授权并留痕、限定留存期限",
            "PIPL Art.28, 51; JR/T 0197"
        )

    def _ins_beneficiary(self, data: dict) -> CheckResult:
        """受益人信息处理"""
        collected = data.get("ins_beneficiary_collected", False)
        noticed = data.get("ins_beneficiary_notice", False)
        has_basis = data.get("ins_beneficiary_basis", False)
        scope_limited = data.get("ins_beneficiary_scope", False)

        if not collected:
            return not_applicable(
                "ins_beneficiary", "受益人信息 - 处理合规",
                "未收集受益人个人信息，本项不适用",
                "PIPL Art.13, 17"
            )

        issues = []
        if not noticed:
            issues.append("未向受益人告知信息处理规则（受益人通常并非合同相对方）")
        if not has_basis:
            issues.append("未明确处理的合法性基础（履行合同所必需或取得同意）")
        if not scope_limited:
            issues.append("受益人信息收集范围超出履行保险合同必需")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "ins_beneficiary", "受益人信息 - 处理合规",
            severity, passed,
            "；".join(issues) if issues else "受益人信息处理合规",
            "向受益人履行告知、明确合法性基础、限定收集范围",
            "PIPL Art.13, 17"
        )

    # ---- 支付业务检查项 ----

    def _pay_transaction(self, data: dict) -> CheckResult:
        """交易信息最小必要"""
        collects_minimal = data.get("collects_minimal", False)
        no_extra_info = data.get("no_extra_info", False)
        has_notice = data.get("has_notice", False)

        issues = []
        if not collects_minimal:
            issues.append("交易信息收集超出支付必需范围（如收集通讯录、位置）")
        if not no_extra_info:
            issues.append("以风控名义过度收集非必要信息")
        if not has_notice:
            issues.append("交易信息收集未在隐私政策中明确告知")

        passed = not issues
        severity = "FAIL" if not (collects_minimal and has_notice) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "pay_transaction", "交易信息 - 最小必要原则合规",
            severity, passed,
            "；".join(issues) if issues else "交易信息最小必要合规",
            "仅收集交易必需信息、明确告知收集范围",
            "PIPL Art.6; JR/T 0171"
        )

    def _pay_risk_control(self, data: dict) -> CheckResult:
        """风控信息使用"""
        fraud_detection = data.get("fraud_detection", False)
        purpose_limited = data.get("purpose_limited", False)
        device_info_used = data.get("device_info_used", False)
        device_info_notice = data.get("device_info_notice", False)

        if not fraud_detection and not device_info_used:
            return not_applicable(
                "pay_risk_control", "风控信息 - 使用目的合规",
                "未使用风控数据用于反欺诈检测，也未收集设备信息，本项不适用",
                "PIPL Art.6, 17"
            )

        issues = []
        if fraud_detection and not purpose_limited:
            issues.append("风控数据用于营销等其他目的，超出原授权范围")
        if device_info_used and not device_info_notice:
            issues.append("设备信息（IMEI/OAID/IMSI）收集未告知")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "pay_risk_control", "风控信息 - 使用目的合规",
            severity, passed,
            "；".join(issues) if issues else "风控信息使用合规",
            "风控数据不得用于营销、设备信息收集需告知",
            "PIPL Art.6, 17"
        )

    def _pay_tokenization(self, data: dict) -> CheckResult:
        """支付标记化"""
        uses_tokenization = data.get("uses_tokenization", False)
        pan_not_stored = data.get("pan_not_stored", False)
        token_scope_limited = data.get("token_scope_limited", False)

        if not uses_tokenization:
            return not_applicable(
                "pay_tokenization", "支付标记化 - 合规检查",
                "未使用支付标记化技术（本机构未采用该机制，本项不适用）。"
                "若后续需直接处理银行卡卡号，建议以令牌替代直接存储完整卡号。",
                "JR/T 0171; PCI DSS"
            )

        issues = []
        if not pan_not_stored:
            issues.append("系统仍直接存储完整卡号，未替换为令牌")
        if not token_scope_limited:
            issues.append("令牌使用范围未限定（如限定商户、渠道、金额）")

        passed = not issues
        severity = "PASS" if passed else "WARN"
        return CheckResult(
            "pay_tokenization", "支付标记化 - 合规检查",
            severity, passed,
            "；".join(issues) if issues else "支付标记化合规",
            "使用令牌替换卡号、限定令牌使用范围",
            "JR/T 0171"
        )

    def _pay_merchant(self, data: dict) -> CheckResult:
        """商户信息处理"""
        collects_personal = data.get("pay_merchant_personal_info", False)
        scope_limited = data.get("pay_merchant_scope", False)
        noticed = data.get("pay_merchant_notice", False)
        retention_limited = data.get("pay_merchant_retention", False)

        if not collects_personal:
            return not_applicable(
                "pay_merchant", "商户信息 - 个人经营者信息合规",
                "未收集商户经营者个人信息，本项不适用",
                "PIPL Art.6, 17; JR/T 0171"
            )

        issues = []
        if not scope_limited:
            issues.append("商户经营者信息收集范围超出收单业务必需（实名审核/资金结算）")
        if not noticed:
            issues.append("未向商户经营者告知信息处理规则")
        if not retention_limited:
            issues.append("商户信息留存期限未明确，存在超期保留")

        passed = not issues
        severity = "FAIL" if not scope_limited else ("PASS" if passed else "WARN")
        return CheckResult(
            "pay_merchant", "商户信息 - 个人经营者信息合规",
            severity, passed,
            "；".join(issues) if issues else "商户经营者信息处理合规",
            "限于收单业务必需、履行告知、限定留存期限",
            "PIPL Art.6, 17; JR/T 0171"
        )

    def _pay_account_protection(self, data: dict) -> CheckResult:
        """账户信息保护"""
        encrypted = data.get("pay_account_encrypted", False)
        masked = data.get("pay_account_masked", False)
        access_audit = data.get("pay_account_access_audit", False)
        track_not_stored = data.get("pay_card_track_not_stored", False)

        issues = []
        if not encrypted:
            issues.append("支付账户与绑定银行卡信息未加密存储/传输")
        if not masked:
            issues.append("账户信息展示未做掩码处理")
        if not access_audit:
            issues.append("账户信息访问未最小授权或未留存审计日志")
        if not track_not_stored:
            issues.append("银行卡磁道/芯片信息、CVN2 等账户鉴别信息在系统落库")

        passed = not issues
        severity = "FAIL" if (not encrypted or not track_not_stored) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "pay_account_protection", "账户信息 - 支付账户保护合规",
            severity, passed,
            "；".join(issues) if issues else "支付账户信息保护合规",
            "加密存储传输、展示掩码、最小授权留痕、账户鉴别信息不落库",
            "PIPL Art.6, 51; JR/T 0171"
        )

    # ---- 《金融产品网络营销管理办法》检查项 ----

    def _bank_online_marketing(self, data: dict) -> CheckResult:
        """网络营销合规（银行业务）"""
        return _online_marketing(
            data.get("om_marketing"), data.get("om_content_prohibited"),
            data.get("om_staff_qualified"), data.get("om_third_party_managed"),
            "bank_online_marketing",
            "网络营销合规 - 《金融产品网络营销管理办法》"
        )

    def _bank_pipia(self, data: dict) -> CheckResult:
        """个人信息保护影响评估（银行业务）"""
        return _pipia(
            data.get("pipia_triggered"), data.get("pipia_done"),
            "bank_pipia", "个人信息保护影响评估 - 事前评估与记录留存"
        )

    def _sec_pipia(self, data: dict) -> CheckResult:
        """个人信息保护影响评估（证券/基金业务）"""
        return _pipia(
            data.get("pipia_triggered"), data.get("pipia_done"),
            "sec_pipia", "个人信息保护影响评估 - 事前评估与记录留存"
        )

    def _ins_pipia(self, data: dict) -> CheckResult:
        """个人信息保护影响评估（保险业务）"""
        return _pipia(
            data.get("pipia_triggered"), data.get("pipia_done"),
            "ins_pipia", "个人信息保护影响评估 - 事前评估与记录留存"
        )

    def _pay_pipia(self, data: dict) -> CheckResult:
        """个人信息保护影响评估（支付业务）"""
        return _pipia(
            data.get("pipia_triggered"), data.get("pipia_done"),
            "pay_pipia", "个人信息保护影响评估 - 事前评估与记录留存"
        )

    def _sec_online_marketing(self, data: dict) -> CheckResult:
        """网络营销合规（证券/基金业务）"""
        return _online_marketing(
            data.get("om_marketing"), data.get("om_content_prohibited"),
            data.get("om_staff_qualified"), data.get("om_third_party_managed"),
            "sec_online_marketing",
            "网络营销合规 - 《金融产品网络营销管理办法》"
        )

    def _ins_online_marketing(self, data: dict) -> CheckResult:
        """网络营销合规（保险业务）"""
        return _online_marketing(
            data.get("om_marketing"), data.get("om_content_prohibited"),
            data.get("om_staff_qualified"), data.get("om_third_party_managed"),
            "ins_online_marketing",
            "网络营销合规 - 《金融产品网络营销管理办法》"
        )

    def _pay_online_marketing(self, data: dict) -> CheckResult:
        """网络营销合规（支付业务）"""
        return _online_marketing(
            data.get("om_marketing"), data.get("om_content_prohibited"),
            data.get("om_staff_qualified"), data.get("om_third_party_managed"),
            "pay_online_marketing",
            "网络营销合规 - 《金融产品网络营销管理办法》"
        )

    def _pay_checkout_display(self, data: dict) -> CheckResult:
        """收银台展示合规（支付机构专属）"""
        operated = data.get("pay_checkout_operated")
        segregated = data.get("pay_segregated_display")
        no_fin_marketing = data.get("pay_no_checkout_fin_marketing")
        active_consent = data.get("pay_combo_active_consent")

        ref = "《金融产品网络营销管理办法》"
        if not operated:
            return not_applicable(
                "pay_checkout_display", "收银台展示合规 - 支付工具与金融产品区隔展示",
                "不运营面向个人的收银台/支付页面，本项不适用", ref
            )

        issues = []
        if not segregated:
            issues.append("收银台未将支付工具与贷款、资产管理产品等金融产品区隔展示"
                          "（或仍将金融产品列入支付工具选项）")
        if not no_fin_marketing:
            issues.append("仍在支付链路内为贷款、资产管理产品等金融产品提供营销服务")
        if not active_consent:
            issues.append("组合销售金融产品的选项被设定为默认同意（未要求用户主动勾选）")

        passed = not issues
        severity = "FAIL" if (not segregated or not no_fin_marketing) else (
            "PASS" if passed else "WARN")
        return CheckResult(
            "pay_checkout_display", "收银台展示合规 - 支付工具与金融产品区隔展示",
            severity, passed,
            "；".join(issues) if issues else "收银台展示合规",
            "支付工具与贷款/资管等金融产品区隔展示、不在支付链路内为其提供营销服务、"
            "组合销售选项不得默认同意",
            ref
        )

    # ---- 场景路由 ----

    def run(self, scenario: str, data: dict) -> List[CheckResult]:
        scenario = scenario.lower()
        results = []

        if scenario == "banking":
            results.append(self._bank_account_open(data))
            results.append(self._bank_credit(data))
            results.append(self._bank_credit_report(data))
            results.append(self._bank_marketing(data))
            results.append(self._bank_data_share(data))
            results.append(self._bank_data_classification(data))
            results.append(self._bank_automated_decision(data))
            results.append(self._bank_data_retention(data))
            results.append(self._bank_online_marketing(data))
            results.append(self._bank_pipia(data))

        elif scenario == "securities":
            results.append(self._sec_suitability(data))
            results.append(self._sec_trade_info(data))
            results.append(self._sec_investor_share(data))
            results.append(self._sec_robo_advisor(data))
            results.append(self._sec_marketing(data))
            results.append(self._sec_cross_border(data))
            results.append(self._sec_online_marketing(data))
            results.append(self._sec_pipia(data))

        elif scenario == "insurance":
            results.append(self._ins_underwriting(data))
            results.append(self._ins_claim(data))
            results.append(self._ins_reinsurance(data))
            results.append(self._ins_marketing(data))
            results.append(self._ins_health_classification(data))
            results.append(self._ins_beneficiary(data))
            results.append(self._ins_online_marketing(data))
            results.append(self._ins_pipia(data))

        elif scenario == "payment":
            results.append(self._pay_transaction(data))
            results.append(self._pay_risk_control(data))
            results.append(self._pay_merchant(data))
            results.append(self._pay_tokenization(data))
            results.append(self._pay_account_protection(data))
            results.append(self._pay_online_marketing(data))
            results.append(self._pay_checkout_display(data))
            results.append(self._pay_pipia(data))

        else:
            raise ValueError(f"不支持的场景: {scenario}，可选: {', '.join(self.SCENARIOS.keys())}")

        return results


# ============================================================
# 交互式问答数据
# ============================================================

BANKING_QUESTIONS = [
    ("has_privacy_notice", "开户时是否提供独立的隐私政策/个人信息保护告知？(y/n): "),
    ("has_separate_consent", "个人信息授权是否单独获取（不与服务协议捆绑）？(y/n): "),
    ("consent_method", "同意方式是什么？（manual=手动勾选 / pre_checked=默认勾选）: "),
    ("sensitive_items", "是否收集人脸/指纹等生物识别信息？（如有，输入 biometric，否则留空）: "),
    ("has_loan_authorization", "信贷业务是否取得个人信息处理授权？(y/n): "),
    ("limits_info_scope", "信贷信息收集范围是否限于业务必需？(y/n): "),
    ("has_post_lending_notice", "贷后管理中的信息使用是否充分告知？(y/n): "),
    ("shares_with_third_party", "是否向第三方（担保/催收/评估）共享信贷信息？(y/n): "),
    ("third_party_consent", "第三方共享是否取得单独同意？(y/n): "),
    ("has_authorization", "征信查询是否有书面授权？(y/n): "),
    ("has_purpose_limitation", "征信信息使用目的是否明确限定？(y/n): "),
    ("has_dispute_mechanism", "是否建立征信异议处理机制？(y/n): "),
    ("query_frequency", "征信查询频率是否正常？（normal=正常 / abnormal=异常）: "),
    ("has_marketing_consent", "信用卡营销是否获得用户同意？(y/n): "),
    ("opt_out_available", "是否提供便捷的退订/拒绝渠道？(y/n): "),
    ("uses_push_notification", "是否使用推送通知进行营销？(y/n): "),
    ("shares_for_marketing", "是否将个人信息用于第三方营销共享？(y/n): "),
    ("marketing_third_party_consent", "第三方营销共享是否取得单独同意？(y/n): "),
    ("group_sharing", "是否存在集团内信息共享安排？(y/n): "),
    ("group_notice", "集团共享是否已告知用户？(y/n): "),
    ("third_party_sharing", "是否向第三方提供个人金融信息？(y/n): "),
    ("has_classification", "是否按 JR/T 0197 完成数据分类分级？(y/n): "),
    ("has_data_map", "是否建立个人金融信息数据资产地图？(y/n): "),
    ("c3_protection", "C3类信息（账户鉴别信息）是否有安全保护措施？(y/n): "),
    ("c2_protection", "C2类信息（可识别身份信息）是否有安全保护措施？(y/n): "),
    ("uses_auto_decision", "是否使用自动化决策（如授信模型）？(y/n): "),
    ("has_disclosure", "自动化决策的逻辑和影响是否告知用户？(y/n): "),
    ("has_explanation", "是否提供自动化决策结果的解释说明？(y/n): "),
    ("has_retention_policy", "是否制定个人信息留存期限制度？(y/n): "),
    ("auto_delete", "是否设置到期自动删除/匿名化机制？(y/n): "),
    ("account_cancellation", "账户注销后个人信息是否同步删除？(y/n): "),
    ("can_request_delete", "是否提供用户主动删除个人信息的渠道？(y/n): "),
    ("om_marketing", "是否通过互联网开展金融产品营销（自营平台/公众号/直播/短视频，或委托第三方平台）？(y/n): "),
    ("om_content_prohibited", "网络营销内容是否已排查，不使用「低风险/低门槛/秒到账/高收益/低利率/无成本」等诱导性用语？(y/n): "),
    ("om_staff_qualified", "公众号/直播/短视频营销人员是否均为本机构从业人员、具备业务资格并获授权？(y/n): "),
    ("om_third_party_managed", "委托第三方平台营销的，是否完成事前评估、签订书面协议、持续跟踪，且第三方未介入销售环节（未委托答 y）？(y/n): "),
    ("pipia_triggered", "是否涉及需事前开展个人信息保护影响评估的情形（敏感个人信息/自动化决策/委托处理或对外提供或公开/跨境/其他重大影响）？(y/n): "),
    ("pipia_done", "（若涉及）是否已在事前完成影响评估，并按不短于三年的期限留存评估报告与处理情况记录？(y/n): "),
]


SECURITIES_QUESTIONS = [
    ("kyc_scope_reasonable", "KYC信息收集范围是否限于适当性管理必需？(y/n): "),
    ("has_privacy_notice", "KYC信息的收集用途是否告知投资者？(y/n): "),
    ("kyc_retention_limited", "KYC信息留存期限是否明确限定？(y/n): "),
    ("encrypt_transmission", "交易信息传输是否加密？(y/n): "),
    ("access_control", "交易信息访问是否有权限控制？(y/n): "),
    ("log_audit", "交易信息访问日志是否完整？(y/n): "),
    ("csdc_sharing", "是否向中国结算报送投资者信息？(y/n): "),
    ("csdc_notice", "投资者是否知晓信息报送中国结算？(y/n): "),
    ("custodian_sharing", "是否向托管银行传输投资者信息？(y/n): "),
    ("custodian_notice", "投资者是否知晓信息传输托管银行？(y/n): "),
    ("has_algorithm_filing", "算法推荐服务是否完成备案？(y/n): "),
    ("has_risk_warning", "智能投顾建议是否提示算法风险？(y/n): "),
    ("has_human_override", "是否提供人工投顾替代选项？(y/n): "),
    ("sec_marketing_consent", "产品推介/基金销售等营销是否取得投资者同意？(y/n): "),
    ("sec_marketing_opt_out", "营销是否提供便捷的退订/拒绝渠道？(y/n): "),
    ("sec_personalized_push", "是否基于个人特征进行定向推送？(y/n): "),
    ("sec_third_party_marketing", "是否向第三方提供投资者信息用于营销？(y/n): "),
    ("sec_third_party_marketing_consent", "第三方营销共享是否取得单独同意？(y/n): "),
    ("sec_cross_border", "是否涉及投资者个人信息跨境传输（如沪深港通、QDII 等）？(y/n): "),
    ("sec_cross_border_path", "是否完成出境合规路径（安全评估/标准合同/保护认证之一）？(y/n): "),
    ("sec_cross_border_notice", "是否告知境外接收方信息并取得单独同意？(y/n): "),
    ("om_marketing", "是否通过互联网开展金融产品营销（自营平台/公众号/直播/短视频，或委托第三方平台）？(y/n): "),
    ("om_content_prohibited", "网络营销内容是否已排查，不使用「低风险/低门槛/秒到账/高收益/低利率/无成本」等诱导性用语？(y/n): "),
    ("om_staff_qualified", "公众号/直播/短视频营销人员是否均为本机构从业人员、具备业务资格并获授权？(y/n): "),
    ("om_third_party_managed", "委托第三方平台营销的，是否完成事前评估、签订书面协议、持续跟踪，且第三方未介入销售环节（未委托答 y）？(y/n): "),
    ("pipia_triggered", "是否涉及需事前开展个人信息保护影响评估的情形（敏感个人信息/自动化决策/委托处理或对外提供或公开/跨境/其他重大影响）？(y/n): "),
    ("pipia_done", "（若涉及）是否已在事前完成影响评估，并按不短于三年的期限留存评估报告与处理情况记录？(y/n): "),
]


INSURANCE_QUESTIONS = [
    ("info_collection_reasonable", "健康告知问题是否限于核保必需范围？(y/n): "),
    ("has_separate_consent", "健康信息（敏感信息）是否取得单独同意？(y/n): "),
    ("third_party_verification", "是否委托第三方（体检/调查公司）进行核保验证？(y/n): "),
    ("third_party_consent", "第三方验证是否取得投保人单独授权？(y/n): "),
    ("notice_purpose", "理赔调查目的是否告知被调查人？(y/n): "),
    ("scope_limited", "调查范围是否限于理赔必需？(y/n): "),
    ("third_party_investigation", "是否委托第三方进行理赔调查？(y/n): "),
    ("authorization_scope", "第三方理赔调查的授权范围是否明确？(y/n): "),
    ("has_reinsurance", "是否涉及再保险安排？(y/n): "),
    ("has_notice", "再保险信息共享是否告知投保人？(y/n): "),
    ("cross_border", "再保险是否涉及跨境数据传输？(y/n): "),
    ("cross_border_compliant", "跨境数据是否完成出境合规评估？(y/n): "),
    ("ins_marketing_consent", "保单到期提醒/交叉销售是否取得投保人同意？(y/n): "),
    ("ins_marketing_opt_out", "营销是否提供便捷的退订/拒绝渠道？(y/n): "),
    ("ins_sensitive_for_marketing", "是否将健康/理赔信息用于营销推荐？(y/n): "),
    ("ins_sensitive_marketing_consent", "上述用途是否另行取得单独同意？(y/n): "),
    ("ins_health_classified", "体检报告、病历等健康数据是否完成分类分级？(y/n): "),
    ("ins_health_encrypted", "健康数据是否加密存储与传输？(y/n): "),
    ("ins_health_access_audit", "健康数据访问是否最小授权并留存审计日志？(y/n): "),
    ("ins_health_retention", "健康数据留存期限是否明确限定？(y/n): "),
    ("ins_beneficiary_collected", "是否收集受益人个人信息？(y/n): "),
    ("ins_beneficiary_notice", "是否向受益人告知信息处理规则？(y/n): "),
    ("ins_beneficiary_basis", "是否明确处理的合法性基础（履行合同必需或取得同意）？(y/n): "),
    ("ins_beneficiary_scope", "受益人信息收集范围是否限于履行保险合同必需？(y/n): "),
    ("om_marketing", "是否通过互联网开展金融产品营销（自营平台/公众号/直播/短视频，或委托第三方平台）？(y/n): "),
    ("om_content_prohibited", "网络营销内容是否已排查，不使用「低风险/低门槛/秒到账/高收益/低利率/无成本」等诱导性用语？(y/n): "),
    ("om_staff_qualified", "公众号/直播/短视频营销人员是否均为本机构从业人员、具备业务资格并获授权？(y/n): "),
    ("om_third_party_managed", "委托第三方平台营销的，是否完成事前评估、签订书面协议、持续跟踪，且第三方未介入销售环节（未委托答 y）？(y/n): "),
    ("pipia_triggered", "是否涉及需事前开展个人信息保护影响评估的情形（敏感个人信息/自动化决策/委托处理或对外提供或公开/跨境/其他重大影响）？(y/n): "),
    ("pipia_done", "（若涉及）是否已在事前完成影响评估，并按不短于三年的期限留存评估报告与处理情况记录？(y/n): "),
]


PAYMENT_QUESTIONS = [
    ("collects_minimal", "交易信息是否限于支付必需（不收集通讯录/位置等）？(y/n): "),
    ("no_extra_info", "是否以风控名义过度收集非必要信息？(y/n): "),
    ("has_notice", "交易信息收集是否在隐私政策中明确告知？(y/n): "),
    ("fraud_detection", "是否使用风控数据用于反欺诈检测？(y/n): "),
    ("purpose_limited", "风控数据是否限定用于安全目的（不用于营销）？(y/n): "),
    ("device_info_used", "是否收集设备信息（IMEI/OAID/IMSI）？(y/n): "),
    ("device_info_notice", "设备信息收集是否告知用户？(y/n): "),
    ("uses_tokenization", "是否使用支付标记化技术（Tokenization）？(y/n): "),
    ("pan_not_stored", "系统是否不存储完整卡号（已替换为令牌）？(y/n): "),
    ("token_scope_limited", "令牌使用范围是否限定（商户/渠道/金额）？(y/n): "),
    ("pay_merchant_personal_info", "是否收集商户经营者个人信息（证件、结算账户、手机号等）？(y/n): "),
    ("pay_merchant_scope", "收集范围是否限于收单业务必需（实名审核/资金结算）？(y/n): "),
    ("pay_merchant_notice", "是否向商户经营者告知信息处理规则？(y/n): "),
    ("pay_merchant_retention", "商户信息留存期限是否明确（不超期保留）？(y/n): "),
    ("pay_account_encrypted", "支付账户与绑定银行卡信息是否加密存储与传输？(y/n): "),
    ("pay_account_masked", "账户信息展示是否做掩码处理？(y/n): "),
    ("pay_account_access_audit", "账户信息访问是否最小授权并留存审计日志？(y/n): "),
    ("pay_card_track_not_stored", "银行卡磁道/芯片信息、CVN2 等是否未在系统落库？(y/n): "),
    ("om_marketing", "是否通过互联网开展金融产品营销（自营平台/公众号/直播/短视频，或委托第三方平台）？(y/n): "),
    ("om_content_prohibited", "网络营销内容是否已排查，不使用「低风险/低门槛/秒到账/高收益/低利率/无成本」等诱导性用语？(y/n): "),
    ("om_staff_qualified", "公众号/直播/短视频营销人员是否均为本机构从业人员、具备业务资格并获授权？(y/n): "),
    ("om_third_party_managed", "委托第三方平台营销的，是否完成事前评估、签订书面协议、持续跟踪，且第三方未介入销售环节（未委托答 y）？(y/n): "),
    ("pay_checkout_operated", "是否运营面向个人的收银台/支付页面？(y/n): "),
    ("pay_segregated_display", "收银台是否将支付工具与贷款、资管等金融产品区隔展示，未将金融产品列入支付工具选项？(y/n): "),
    ("pay_no_checkout_fin_marketing", "是否已停止在支付链路内为贷款、资管等金融产品提供营销服务（不在收银台设推广入口）？(y/n): "),
    ("pay_combo_active_consent", "组合销售的选项是否均需用户主动勾选（未设定为默认同意）？(y/n): "),
    ("pipia_triggered", "是否涉及需事前开展个人信息保护影响评估的情形（敏感个人信息/自动化决策/委托处理或对外提供或公开/跨境/其他重大影响）？(y/n): "),
    ("pipia_done", "（若涉及）是否已在事前完成影响评估，并按不短于三年的期限留存评估报告与处理情况记录？(y/n): "),
]


SCENARIO_QUESTIONS = {
    "banking": BANKING_QUESTIONS,
    "securities": SECURITIES_QUESTIONS,
    "insurance": INSURANCE_QUESTIONS,
    "payment": PAYMENT_QUESTIONS,
}


# ============================================================
# 样例作答（仅用于 --demo 预览输出形态）
# ============================================================
# 规则：以「全部合规」为基线，再覆盖少量条目，使样例报告能同时出现
# ✅ 通过 / ⚠️ 警告 / ❌ 未通过 / ➖ 不适用 四种状态。
# 基线 + 覆盖的写法保证问答列表变动时不会缺项。
#
# ⚠️ 这里的答案是**构造出来的**，不含任何真实机构信息；
#    其产物一律标注 DEMO，且禁止写入合规台账。

DEMO_OVERRIDES = {
    # 银行：能同时展示四种状态
    "banking": {
        "consent_method": "manual",
        "sensitive_items": "",
        "query_frequency": "normal",
        "has_authorization": "n",          # ❌ 征信查询无授权
        "has_retention_policy": "n",       # ⚠️ 未制定留存期限制度
        "uses_auto_decision": "n",         # ➖ 未使用自动化决策
        "group_sharing": "n",              # ┐ 既无集团共享
        "third_party_sharing": "n",        # ┘ 也不向第三方提供
    },
    "securities": {
        "has_human_override": "n",         # ⚠️ 未提供人工投顾替代
        "encrypt_transmission": "n",       # ❌ 交易信息传输未加密
        "sec_cross_border": "n",           # ➖ 不涉及跨境传输
        "csdc_sharing": "n",               # ┐ 既不向中国结算报送
        "custodian_sharing": "n",          # ┘ 也不向托管银行传输
    },
    "insurance": {
        "ins_health_encrypted": "n",       # ❌ 健康数据未加密
        "notice_purpose": "n",             # ⚠️ 理赔调查目的未告知
        "has_reinsurance": "n",            # ➖ 未涉及再保险
        "ins_beneficiary_collected": "n",  # ➖ 未收集受益人信息
    },
    "payment": {
        "has_notice": "n",                 # ❌ 交易信息收集未告知
        "pay_account_masked": "n",         # ⚠️ 账户信息未掩码
        "pay_merchant_personal_info": "n", # ➖ 未收集商户经营者信息
        "uses_tokenization": "n",          # ➖ 未使用支付标记化
    },
}


def build_demo_answers(scenario: str) -> dict:
    """构造样例作答（首次按问答列表取「全合规」基线，再套用覆盖项）。"""
    ids = [qid for qid, _ in SCENARIO_QUESTIONS.get(scenario, [])]
    data = {qid: "y" for qid in ids}
    for key, value in (("consent_method", "manual"),
                       ("sensitive_items", ""),
                       ("query_frequency", "normal")):
        if key in ids:
            data[key] = value
    for key, value in DEMO_OVERRIDES.get(scenario, {}).items():
        if key in ids:
            data[key] = value
    return data


# ============================================================
# 答案来源：交互作答与答案文件共用同一套转换规则
# ============================================================

def convert_answer(key: str, raw):
    """把用户可见答案转成检查引擎使用的内部值。

    交互作答与答案文件走同一套规则，保证两条路径等价。
    幂等：内部值再次传入结果不变。
    """
    if isinstance(raw, list):
        base = raw
    elif isinstance(raw, bool):
        base = "y" if raw else "n"
    else:
        base = str(raw).strip().lower()

    if key == "consent_method":
        return "pre_checked" if base == "pre_checked" else "manual" if base == "manual" else ""
    if key == "query_frequency":
        return "abnormal" if base in ("abnormal", "异常") else "normal"
    if key == "sensitive_items":
        if isinstance(base, list):
            return base
        return ["biometric"] if ("biometric" in base or "人脸" in base or "指纹" in base) else []
    if isinstance(base, list):
        return bool(base)
    return base.startswith("y")


def scene_question_ids(scenario: str) -> List[str]:
    """该场景需要作答的全部问题 id。"""
    return [qid for qid, _ in SCENARIO_QUESTIONS.get(scenario, [])]


def build_answers(scenario: str, raw_answers: dict):
    """把关卡答案转成引擎输入，并报告缺失/多余项。

    返回 (data, missing, extra)。missing 非空时不得出具任何结论。
    """
    ids = scene_question_ids(scenario)
    idset = set(ids)
    missing = [qid for qid in ids if qid not in raw_answers]
    extra = [k for k in raw_answers if k not in idset]
    data = {qid: convert_answer(qid, raw_answers[qid]) for qid in ids if qid in raw_answers}
    return data, missing, extra


def load_answers_file(path: str, scenario: str):
    """读取答案文件，返回 (raw_answers, errors)。

    文件格式（"answers" 可省略，亦接受直接给出 {问题id: 答案}）：
        {"scenario": "banking", "answers": {"has_privacy_notice": "y", ...}}
    """
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return None, [f"答案文件不存在：{path}"]
    except json.JSONDecodeError as e:
        return None, [f"答案文件不是合法 JSON：{e}"]

    if not isinstance(payload, dict):
        return None, ["答案文件顶层必须是 JSON 对象"]

    errors = []
    if "answers" in payload:
        file_scenario = payload.get("scenario")
        if file_scenario and file_scenario != scenario:
            errors.append(f"答案文件记录的场景为 {file_scenario}，与 --scenario {scenario} 不一致")
        answers = payload["answers"]
    else:
        answers = payload

    if not isinstance(answers, dict):
        errors.append("answers 必须是对象，形如 {\"问题id\": \"答案\"}")
        return None, errors
    return answers, errors


def write_answers_file(path: str, scenario: str, data: dict):
    """把（内部值形式的）答案写成可与 --input 互认的 JSON。"""
    payload = {
        "scenario": scenario,
        "answers": data,
        "_note": "可直接用 --input <本文件> 复用；值可用 y/n 或 true/false。",
    }
    with open(os.path.expanduser(path), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 答案已保存到: {path}（下次可直接 --input 复用）")


def interactive_input(scenario: str) -> dict:
    """交互式问答"""
    data = {}
    questions = SCENARIO_QUESTIONS.get(scenario, [])

    print(f"\n{'='*50}")
    print(f"📋 {FinPIPLChecker.SCENARIOS.get(scenario, scenario)} — 合规自查")
    print(f"{'='*50}")
    print("（输入 y/n 或按提示输入，直接回车默认为 n/留空）\n")

    total = len(questions)
    for idx, (key, prompt) in enumerate(questions, 1):
        raw = input(f"[{idx}/{total}] {prompt}")
        data[key] = convert_answer(key, raw)

    return data


# ============================================================
# 合规台账（时间序列）与整改进度对比
# ============================================================

def load_ledger_last(path: str, scenario: str):
    """读取台账里最近一条**同场景**记录，作为对比基线。

    台账为 JSONL：每行一条记录，可人工阅读、可 grep、可直接入版本库。
    返回 (record, error)：文件不存在时返回 (None, None)（视为首次记录）。
    """
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return None, None
    last = None
    try:
        with open(expanded, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    return None, (f"台账第 {lineno} 行不是合法 JSON"
                                  "（台账应为每行一条 JSON 记录，请勿手工改动结构）")
                if isinstance(rec, dict) and rec.get("scenario") == scenario:
                    last = rec
    except OSError as e:
        return None, f"台账读取失败：{e}"
    return last, None


def append_ledger(path: str, record: dict):
    """把本次结果追加到台账末尾。"""
    expanded = os.path.expanduser(path)
    parent = os.path.dirname(os.path.abspath(expanded))
    if parent and not os.path.isdir(parent):
        raise OSError(f"台账所在目录不存在：{parent}")
    with open(expanded, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_ledger_record(scenario: str, version: str, timestamp: str,
                        summary: dict, results: List[CheckResult]) -> dict:
    """一条台账记录：汇总 + 逐项状态（用于下次对比）。"""
    return {
        "timestamp": timestamp,
        "scenario": scenario,
        "version": version,
        "summary": {k: summary[k] for k in
                    ("total", "applicable", "not_applicable",
                     "passed", "warnings", "failed", "pass_rate")},
        "items": {r.check_id: r.severity for r in results},
    }


def compare_with_previous(prev: dict, results: List[CheckResult]) -> dict:
    """把本次逐项结果与上次记录对比，得出整改进度。"""
    prev_items = prev.get("items") or {}
    by_id = {r.check_id: r for r in results}
    improved, regressed, unchanged, added = [], [], [], []
    applicability = []

    for r in results:
        was = prev_items.get(r.check_id)
        if was is None:
            added.append(r.description)
        elif was == r.severity:
            unchanged.append(r.description)
        elif was == "N/A" or r.severity == "N/A":
            # 适用性变了（本机构业务范围变化），既不算改善也不算退步
            applicability.append(f"{r.description}（{was} → {r.severity}）")
        elif r.severity == "PASS":
            improved.append(r.description)
        elif was == "PASS":
            regressed.append(r.description)
        elif r.severity == "WARN":       # FAIL -> WARN 算改善
            improved.append(r.description)
        else:                            # WARN -> FAIL 算退步
            regressed.append(r.description)

    removed = [cid for cid in prev_items if cid not in by_id]
    return {
        "prev_timestamp": prev.get("timestamp"),
        "prev_rate": (prev.get("summary") or {}).get("pass_rate"),
        "prev_applicable": (prev.get("summary") or {}).get("applicable"),
        "improved": improved,
        "regressed": regressed,
        "unchanged": unchanged,
        "added": added,
        "removed": removed,
        "applicability_changed": applicability,
    }


def render_comparison_text(comp: dict, rate: float) -> List[str]:
    """控制台用的对比文本。"""
    prev_ts = comp.get("prev_timestamp") or "—"
    prev_rate = comp.get("prev_rate")
    lines = []
    if prev_rate is None:
        lines.append(f"📈 与上次相比（上次：{prev_ts}）")
    else:
        delta = rate - prev_rate
        sign = "+" if delta >= 0 else ""
        lines.append(f"📈 与上次相比（上次：{prev_ts}，合规率 "
                     f"{prev_rate:.0f}% → {rate:.0f}%，{sign}{delta:.0f} 个百分点）")
    if comp["improved"]:
        lines.append(f"  ✅ 新增通过 {len(comp['improved'])} 项："
                     + "、".join(comp["improved"]))
    if comp["regressed"]:
        lines.append(f"  ❌ 新增未通过 {len(comp['regressed'])} 项："
                     + "、".join(comp["regressed"]))
    if comp["added"]:
        lines.append(f"  ➕ 本次新增检查项 {len(comp['added'])} 项："
                     + "、".join(comp["added"]))
    if comp["removed"]:
        lines.append(f"  ➖ 本次不再检查 {len(comp['removed'])} 项（检查项版本变更）")
    if comp.get("applicability_changed"):
        lines.append(f"  🔁 适用性变化 {len(comp['applicability_changed'])} 项："
                     + "、".join(comp["applicability_changed"]))
    lines.append(f"  ➖ 状态未变 {len(comp['unchanged'])} 项")
    return lines


# ============================================================
# 报告生成
# ============================================================

def generate_report_markdown(report: CheckReport) -> str:
    """生成 Markdown 格式报告"""
    lines = []
    lines.append(f"# 🏦 Fin-PIPL 合规检查报告\n")
    if report.demo:
        lines.append("> ⚠️ **DEMO — 样例报告，非真实检查结果**  ")
        lines.append("> 本报告基于内置样例作答，仅用于预览报告形态；")
        lines.append("> 它不是对任何机构的检查结论，请勿作为合规依据。\n")
    lines.append(f"**工具版本**: {report.version}  ")
    lines.append(f"**检查时间**: {report.timestamp}  ")
    lines.append(f"**检查场景**: {FinPIPLChecker.SCENARIOS.get(report.scenario, report.scenario)}  ")
    lines.append(f"**检查项**: {report.summary['total']} 项  ")
    if report.summary.get("not_applicable"):
        lines.append(f"**不适用**: {report.summary['not_applicable']} 项（不计入合规率）  ")
    lines.append(f"**合规率**: {report.summary['pass_rate']:.0f}%"
                 f"（按 {report.summary.get('applicable', report.summary['total'])} 项适用项计）\n")

    lines.append("## 📊 总体结果\n")
    lines.append(f"- ✅ 通过: {report.summary['passed']} 项")
    lines.append(f"- ⚠️ 警告: {report.summary['warnings']} 项")
    lines.append(f"- ❌ 未通过: {report.summary['failed']} 项")
    if report.summary.get("not_applicable"):
        lines.append(f"- ➖ 不适用: {report.summary['not_applicable']} 项"
                     "（业务活动/技术机制在本机构不存在，不计入合规率）")
    lines.append("")

    if report.comparison:
        comp = report.comparison
        lines.append("## 📈 与上次相比\n")
        prev_ts = comp.get("prev_timestamp") or "—"
        prev_rate = comp.get("prev_rate")
        lines.append(f"- 上次检查时间: {prev_ts}")
        if prev_rate is None:
            lines.append("- 本次为首次记录，无对比基线")
        else:
            delta = report.summary["pass_rate"] - prev_rate
            sign = "+" if delta >= 0 else ""
            lines.append(f"- 合规率: {prev_rate:.0f}% → {report.summary['pass_rate']:.0f}%"
                         f"（{sign}{delta:.0f} 个百分点）")
        lines.append(f"- ✅ 新增通过: {len(comp['improved'])} 项")
        for d in comp["improved"]:
            lines.append(f"  - {d}")
        lines.append(f"- ❌ 新增未通过: {len(comp['regressed'])} 项")
        for d in comp["regressed"]:
            lines.append(f"  - {d}")
        if comp["added"]:
            lines.append(f"- ➕ 本次新增检查项: {len(comp['added'])} 项")
        if comp["removed"]:
            lines.append(f"- ➖ 本次不再检查: {len(comp['removed'])} 项（检查项版本变更）")
        if comp.get("applicability_changed"):
            lines.append(f"- 🔁 适用性变化: {len(comp['applicability_changed'])} 项")
            for d in comp["applicability_changed"]:
                lines.append(f"  - {d}")
        lines.append(f"- ➖ 状态未变: {len(comp['unchanged'])} 项\n")

    lines.append("## 📋 详细检查结果\n")
    for item in report.items:
        if not item.get("applicable", True):
            status_icon = "➖"
        else:
            status_icon = "✅" if item["passed"] else (
                "❌" if item["severity"] == "FAIL" else "⚠️")
        lines.append(f"### {status_icon} {item['description']}")
        lines.append(f"**状态**: {item['severity']}  ")
        lines.append(f"**详情**: {item['details']}  ")
        if item.get("applicable", True):
            lines.append(f"**建议**: {item['recommendation']}  ")
        else:
            lines.append("**说明**: 本项不适用，不计入合规率  ")
        lines.append(f"**法规依据**: {item['regulation_ref']}  ")
        lines.append("")

    lines.append("---")
    lines.append(f"*本报告由 Fin-PIPL v{report.version} 自动生成。结论基于**用户自述**，"
                 "工具未对作答作任何核实；仅供参考，不构成法律意见，"
                 "不得作为合规证明或监管呈报材料。*")
    return "\n".join(lines)


def generate_report_html(report: CheckReport) -> str:
    """生成 HTML 格式报告"""
    items_html = ""
    for item in report.items:
        applicable = item.get("applicable", True)
        sev_color = {"PASS": "#27ae60", "WARN": "#f39c12", "FAIL": "#e74c3c", "N/A": "#95a5a6"}
        color = sev_color.get(item["severity"], "#333")
        if not applicable:
            icon = "&#8212;"
        elif item["passed"]:
            icon = "&#10004;"
        elif item["severity"] == "FAIL":
            icon = "&#10008;"
        else:
            icon = "&#9888;"
        advice = (f"<p><strong>建议：</strong>{item['recommendation']}</p>"
                  if applicable else
                  "<p><strong>说明：</strong>本项不适用，不计入合规率</p>")
        items_html += f"""
        <div class="check-item">
            <div class="check-header" style="border-left: 4px solid {color};">
                <span class="check-icon" style="color: {color};">{icon}</span>
                <span class="check-title">{item['description']}</span>
                <span class="check-status" style="background: {color}20; color: {color};">{item['severity']}</span>
            </div>
            <div class="check-body">
                <p><strong>详情：</strong>{item['details']}</p>
                {advice}
                <p><strong>法规依据：</strong>{item['regulation_ref']}</p>
            </div>
        </div>"""

    comp_html = ""
    if report.comparison:
        comp = report.comparison
        prev_ts = comp.get("prev_timestamp") or "—"
        prev_rate = comp.get("prev_rate")
        if prev_rate is None:
            rate_line = "本次为首次记录，无对比基线"
        else:
            delta = report.summary["pass_rate"] - prev_rate
            sign = "+" if delta >= 0 else ""
            rate_line = (f"合规率 {prev_rate:.0f}% → {report.summary['pass_rate']:.0f}%"
                         f"（{sign}{delta:.0f} 个百分点）")

        def _ul(title, items, cls):
            if not items:
                return ""
            lis = "".join(f"<li>{d}</li>" for d in items)
            return f'<p class="{cls}"><strong>{title}：</strong></p><ul class="{cls}">{lis}</ul>'

        comp_html = f"""
<div class="compare">
<h2>📈 与上次相比</h2>
<p>上次检查时间：{prev_ts} &nbsp;|&nbsp; {rate_line}</p>
{_ul("✅ 新增通过", comp["improved"], "cmp-up")}
{_ul("❌ 新增未通过", comp["regressed"], "cmp-down")}
{_ul("➕ 本次新增检查项", comp["added"], "cmp-new")}
        {_ul("🔁 适用性变化", comp.get("applicability_changed", []), "cmp-na")}
        <p class="cmp-flat">➖ 状态未变 {len(comp['unchanged'])} 项</p>
</div>"""

    demo_html = ""
    if report.demo:
        demo_html = ('<div class="demo-banner">⚠️ <strong>DEMO — 样例报告，非真实检查结果</strong><br>'
                     '本报告基于内置样例作答，仅用于预览报告形态；'
                     '它不是对任何机构的检查结论，请勿作为合规依据。</div>')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>Fin-PIPL 合规检查报告</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #333; line-height: 1.6; }}
h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
.demo-banner {{ background: #fdf3e3; border: 1px solid #f0c987; border-left: 4px solid #f39c12; border-radius: 6px; padding: 12px 16px; margin: 16px 0; color: #8a5a00; }}
.summary {{ display: flex; gap: 20px; margin: 20px 0; }}
.summary-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; flex: 1; text-align: center; }}
.summary-card.pass {{ border-top: 3px solid #27ae60; }}
.summary-card.warn {{ border-top: 3px solid #f39c12; }}
.summary-card.fail {{ border-top: 3px solid #e74c3c; }}
.summary-card.na {{ border-top: 3px solid #95a5a6; }}
.num {{ font-size: 2em; font-weight: bold; }}
.pass .num {{ color: #27ae60; }}
.warn .num {{ color: #f39c12; }}
.fail .num {{ color: #e74c3c; }}
.na .num {{ color: #95a5a6; }}
.check-item {{ background: #fff; border: 1px solid #eee; border-radius: 8px; margin: 10px 0; overflow: hidden; }}
.check-header {{ padding: 12px 16px; display: flex; align-items: center; gap: 10px; cursor: default; }}
.check-icon {{ font-size: 1.2em; }}
.check-title {{ flex: 1; font-weight: 500; }}
.check-status {{ padding: 2px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
.check-body {{ padding: 0 16px 12px; color: #555; font-size: 0.95em; }}
.footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 0.85em; color: #999; }}
.compare {{ background: #f8f9fa; border-radius: 8px; padding: 16px 20px; margin: 20px 0; }}
.compare h2 {{ font-size: 1.1em; margin: 0 0 8px; color: #2c3e50; }}
.compare ul {{ margin: 4px 0 12px; padding-left: 22px; }}
.cmp-up {{ color: #1e8449; }}
.cmp-down {{ color: #c0392b; }}
.cmp-new {{ color: #2471a3; }}
.cmp-na {{ color: #7f8c8d; }}
.cmp-flat {{ color: #7f8c8d; }}
</style></head><body>
<h1>🏦 Fin-PIPL 合规检查报告</h1>
{demo_html}
<p><strong>工具版本：</strong>{report.version} &nbsp;|&nbsp; <strong>检查时间：</strong>{report.timestamp} &nbsp;|&nbsp; <strong>检查场景：</strong>{FinPIPLChecker.SCENARIOS.get(report.scenario, report.scenario)}</p>
<p><strong>检查项：</strong>{report.summary['total']} 项 &nbsp;|&nbsp; <strong>不适用：</strong>{report.summary.get('not_applicable', 0)} 项（不计入合规率） &nbsp;|&nbsp; <strong>合规率：</strong>{report.summary['pass_rate']:.0f}%（按 {report.summary.get('applicable', report.summary['total'])} 项适用项计）</p>
<div class="summary">
<div class="summary-card pass"><div class="num">{report.summary['passed']}</div><div>通过</div></div>
<div class="summary-card warn"><div class="num">{report.summary['warnings']}</div><div>警告</div></div>
<div class="summary-card fail"><div class="num">{report.summary['failed']}</div><div>未通过</div></div>
<div class="summary-card na"><div class="num">{report.summary.get('not_applicable', 0)}</div><div>不适用</div></div>
</div>
{comp_html}
{items_html}
<div class="footer">本报告由 Fin-PIPL v{report.version} 自动生成。结论基于<strong>用户自述</strong>，工具未对作答作任何核实；仅供参考，不构成法律意见，不得作为合规证明或监管呈报材料。</div>
</body></html>"""


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fin-PIPL — 金融行业个人信息保护合规检查工具"
    )
    parser.add_argument(
        "--scenario", "-s",
        choices=["banking", "securities", "insurance", "payment"],
        default="banking",
        help="检查场景：banking(银行), securities(证券), insurance(保险), payment(支付)"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="输出格式（默认 markdown）"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互式问答模式"
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        help="从答案文件读取作答（JSON），与 --interactive 二选一"
    )
    parser.add_argument(
        "--save-answers",
        metavar="FILE",
        help="交互作答结束后把答案保存到该文件（可被 --input 直接复用）"
    )
    parser.add_argument(
        "--ledger",
        metavar="FILE",
        help="合规台账（JSONL）：读取该场景上次记录做整改进度对比，并追加本次记录"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="用内置样例作答预览报告形态（标注 DEMO，不是检查结论，不可写入台账）"
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="列出支持的业务场景"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="Fin-PIPL v1.7.0"
    )

    args = parser.parse_args()

    if args.list_scenarios:
        print("Fin-PIPL 支持的场景：")
        for key, name in FinPIPLChecker.SCENARIOS.items():
            print(f"  {key:15s} - {name}")
        return 0

    # ---- 输入来源：必须有真实作答，否则不出任何结论 ----
    exclusive = [name for name, on in (("--interactive", args.interactive),
                                       ("--input", bool(args.input)),
                                       ("--demo", args.demo)) if on]
    if len(exclusive) > 1:
        print(f"错误：{' 与 '.join(exclusive)} 不能同时使用。", file=sys.stderr)
        return 2
    if args.save_answers and not args.interactive:
        print("错误：--save-answers 仅在 --interactive 模式下有效。", file=sys.stderr)
        return 2
    if args.demo and args.ledger:
        print("错误：--demo 产出的是样例预览、不是检查结论，不得写入合规台账（--ledger）。",
              file=sys.stderr)
        print("  若要看台账对比效果，请用真实作答：--interactive 或 --input。", file=sys.stderr)
        return 2

    if args.demo:
        demo_raw = build_demo_answers(args.scenario)
        data, demo_missing, _ = build_answers(args.scenario, demo_raw)
        if demo_missing:
            print(f"错误：内置样例作答缺少 {len(demo_missing)} 项，与问答列表不一致（属程序缺陷）。",
                  file=sys.stderr)
            for qid in demo_missing:
                print(f"  - {qid}", file=sys.stderr)
            return 2
    elif args.interactive:
        data = interactive_input(args.scenario)
        if args.save_answers:
            write_answers_file(args.save_answers, args.scenario, data)
    elif args.input:
        raw_answers, errors = load_answers_file(args.input, args.scenario)
        if errors:
            for e in errors:
                print(f"错误：{e}", file=sys.stderr)
            return 2
        data, missing, extra = build_answers(args.scenario, raw_answers)
        if missing:
            print(f"错误：答案文件缺少 {len(missing)} 项作答，无法出具检查结论。", file=sys.stderr)
            print("缺失项：", file=sys.stderr)
            for qid in missing:
                print(f"  - {qid}", file=sys.stderr)
            print("\n补齐后重试；或用 --interactive --save-answers answers.json 生成一份完整答案。",
                  file=sys.stderr)
            return 2
        if extra:
            print(f"提示：答案文件含本场景不使用的项，已忽略：{', '.join(extra)}", file=sys.stderr)
    else:
        print("错误：未提供作答，已中止（不会用空答案生成报告）。", file=sys.stderr)
        print("  fin-pipl 的结论必须基于你的实际作答，请二选一：", file=sys.stderr)
        print(f"    python3 scripts/fin-pipl-check.py --scenario {args.scenario} --interactive", file=sys.stderr)
        print(f"    python3 scripts/fin-pipl-check.py --scenario {args.scenario} --input answers.json", file=sys.stderr)
        return 2

    # ---- 合规台账：先读上次基线，再追加本次记录 ----
    comparison = None
    if args.ledger:
        prev_record, ledger_error = load_ledger_last(args.ledger, args.scenario)
        if ledger_error:
            print(f"错误：{ledger_error}", file=sys.stderr)
            return 2
    else:
        prev_record = None

    # 执行检查
    checker = FinPIPLChecker()
    results = checker.run(args.scenario, data)

    # 统计
    passed = sum(1 for r in results if r.severity == "PASS")
    warnings = sum(1 for r in results if r.severity == "WARN")
    failed = sum(1 for r in results if r.severity == "FAIL")
    na_count = sum(1 for r in results if not r.applicable)
    total = len(results)
    applicable = total - na_count

    report = CheckReport(
        tool_name="fin-pipl",
        version="1.7.0",
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scenario=args.scenario,
        summary={
            "total": total, "applicable": applicable,
            "not_applicable": na_count,
            "passed": passed, "warnings": warnings, "failed": failed,
            "pass_rate": (passed / applicable * 100) if applicable else 0
        },
        items=[asdict(r) for r in results],
        demo=bool(args.demo),
    )

    if args.ledger:
        record = build_ledger_record(args.scenario, report.version, report.timestamp,
                                     report.summary, results)
        if prev_record:
            comparison = compare_with_previous(prev_record, results)
        else:
            comparison = {"prev_timestamp": None, "prev_rate": None,
                          "improved": [], "regressed": [], "unchanged": [],
                          "added": [], "removed": [], "applicability_changed": []}
        report.comparison = comparison
        try:
            append_ledger(args.ledger, record)
        except OSError as e:
            print(f"错误：台账写入失败：{e}", file=sys.stderr)
            return 2

    # 控制台输出
    print(f"\n{'='*50}")
    if report.demo:
        print("⚠️  DEMO — 样例报告，非真实检查结果")
        print("=" * 50)
    print(f"🏦 Fin-PIPL 合规检查报告")
    print(f"{'='*50}")
    print(f"场景: {FinPIPLChecker.SCENARIOS.get(args.scenario, args.scenario)}")
    print(f"时间: {report.timestamp}")
    na_note = f"（另有 {na_count} 项不适用）" if na_count else ""
    print(f"结果: {passed}/{applicable} 通过, {warnings} 警告, {failed} 未通过{na_note}")
    print(f"合规率: {report.summary['pass_rate']:.0f}%（按 {applicable} 项适用项计）\n")

    if report.demo:
        print("※ 以上基于**内置样例作答**，仅用于预览报告形态。")
        print("  它不是对任何机构的检查结论，请勿作为合规依据，也不会写入台账。\n")

    for r in results:
        if not r.applicable:
            icon = "➖"
        elif r.passed:
            icon = "✅"
        elif r.severity == "WARN":
            icon = "⚠️"
        else:
            icon = "❌"
        print(f"  {icon} {r.description}")
        if r.details:
            print(f"    详情: {r.details}")
        if not r.applicable:
            print(f"    不适用（业务活动/技术机制在本机构不存在），不计入合规率")
        elif not r.passed:
            print(f"    建议: {r.recommendation}")
            if r.regulation_ref:
                print(f"    依据: {r.regulation_ref}")

    if comparison is not None:
        for line in render_comparison_text(comparison, report.summary["pass_rate"]):
            print(line)
        print(f"\n📗 台账已更新: {args.ledger}")

    # 文件输出
    if args.output:
        if args.format == "json":
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        elif args.format == "html":
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(generate_report_html(report))
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(generate_report_markdown(report))
        print(f"\n✅ 报告已保存到: {args.output}")
    elif report.demo:
        print("\n提示：加 --output <文件> 可把这份样例报告存下来（--format 支持 markdown/json/html）。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
