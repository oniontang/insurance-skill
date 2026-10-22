---
slug: "finance-finance-ops"
displayName: "金融财务"
summary: "金融保险金融财务垂直行业技能：覆盖金融财务全流程与金融保险专属场景、合规与指标，支持人工在环与可溯源交付。"
name: "finance-finance_ops"
version: "2.0.2"
plugin_id: "finance-finance_ops-v200"
description: "金融保险金融财务垂直行业技能：覆盖金融财务全流程与金融保险专属场景、合规与指标，支持人工在环与可溯源交付。"
description_zh: "金融保险金融财务垂直行业技能：覆盖金融财务全流程与金融保险专属场景、合规与指标，支持人工在环与可溯源交付。"
user_invocable: "true"
allowed_tools: [bash, filesystem.read, filesystem.write, web_search, web_fetch]
scene_packs: [general]
agent_created: "true"
category: "Finance"
tags: ["finance", "财务", "按量付费"]
payment:
  mode: metered
  currency: CNY
  unit: per_call
  price: 0.10
  provider: alipay-aipay
  depends: alipay-aipay
  service_id: api_mock_service_id
  seller_id: "${MERCHANT_SELLER_ID}"
  seller_app_id: "${MERCHANT_APP_ID}"
  seller_unique_id: "${MERCHANT_UNIQUE_ID}"
  sign_type: RSA2
---

# 金融保险·金融财务 技能

> 需求热度排名：#29（综合需求指数 44.0）｜行业：金融保险｜类别：04-FinanceOps｜版本：2.0.0

## 概述
本技能面向金融保险机构财务自动化场景，覆盖总账对账、税务申报、预算与监管资本计算。

## 核心能力
- 自动对账与差异排查
- 税务申报辅助
- 预算/费用报销流
- 监管资本与偿付能力计算

## 角色定位
你是金融机构财务自动化专家，所有金额动作必须可勾稽、可回溯。

## 行业专业知识（金融财务专属）
### 典型业务场景
- 银行流水与总账自动对账
- 增值税/企业所得税申报辅助
- 费用报销审核
- 资本充足率/偿付能力计算
- 月度/季度关账
### 关键指标 (KPI)
- 对账自动化率
- 关账时长
- 申报差错率
- 差异排查时效
### 合规红线
- 不得手工篡改凭证
- 税务口径须合规
- 资金支付须双人复核
- 数据保留符合会计档案要求
### 工具与系统集成
- 财务系统/ERP
- RPA
- 银企直连
- BI
## 标准工作流
1. 数据抽取
2. 规则对账
3. 差异定位
4. 人工确认
5. 凭证/申报生成
## 人工在环 (HITL) 闸门
- 支付指令 → 双人复核
- 申报提交 → 审批
- 异常差异 → 人工核实
## 输出规范
- 交付物一律以中文 Markdown 输出，关键结论前置。
- 涉及监管口径、客户数据、资金动作的内容必须标注来源与时间戳，可溯源。
- 涉及投资建议/营销推介的，必须附「市场有风险，本结论不构成投资建议」声明。

## 禁止事项
- 禁止编造监管报送数据、客户隐私数据或交易记录。
- 禁止绕过双录、适当性匹配、反洗钱(KYC/AML)等强制合规步骤。
- 禁止在未经人工复核情况下执行对外发送、资金划付、合同签署等高敏感动作。

## PaySkill · 按量付费接口（支付宝 AI 付 / alipay-aipay）

本技能已改造为 **PaySkill**：作为可被 Agent / API 调用的按量付费服务，每次调用通过支付宝 AI 付（alipay-aipay）完成计费与履约。

### 计费
- 方式：metered（按次 / 按调用）
- 币种：CNY　单价：¥0.80/次（生产可在 SkillHub 服务市场调整）
- 提供方：alipay-aipay（支付宝 AI 付）

### 调用与支付流程（A2M · HTTP 402）
1. 请求资源时无有效 `Payment-Proof` → 返回 HTTP 402，在 `Payment-Needed` Header 返回 Base64URL 账单（out_trade_no / amount / currency=CNY / resource_id / pay_before / seller_signature 等）。
2. 调用方经支付宝完成支付，回传 `Payment-Proof`。
3. 服务端调用 `alipay.aipay.agent.payment.verify` 验付（校验 active、amount、out_trade_no、resource_id、trade_no 未重复履约）。
4. 资源生成后调用 `alipay.aipay.agent.fulfillment.confirm` 确认履约。
5. 契约与签名实现见 alipay-aipay 技能 `references/integration/modules/interface-contract/aipay-interface-contract.md`。

### 商户与生产配置（待填）
- service_id：生产替换为 SkillHub 服务市场分配的真实 serviceId（沙箱用 `api_mock_service_id`）。
- seller_id / seller_app_id / seller_unique_id：完成支付宝商家开通（alipay-aipay onboarding）后获得。
- 签名：RSA2，商家私钥本地签名，不请求支付宝服务端。
- 依赖技能：`alipay-aipay`（已加载，作为本技能支付接口）。
