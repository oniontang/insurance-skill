# 🏦 Fin-PIPL — 金融行业个人信息保护合规检查工具

金融行业专属的 **个人信息保护法（PIPL）合规检查工具**，覆盖银行、证券/基金、保险、支付四大业务场景。

## 功能特色

- **34 项金融场景专属检查项**：按业务类型定制，不套用通用检查（银行 10 / 证券 8 / 保险 8 / 支付 8），全部为脚本实际执行的检查
- **四大业务覆盖**：银行（开户/信贷/征信/营销/分级/自动化决策/留存/网络营销/影响评估）、证券（适当性/交易/信息共享/智能投顾/营销推介/跨境数据/网络营销/影响评估）、保险（核保/理赔/再保险/营销推荐/健康数据分级/受益人信息/网络营销/影响评估）、支付（最小必要/风控/商户信息/标记化/账户保护/网络营销/收银台展示/影响评估）
- **个人信息保护影响评估（PIPL Art.55、Art.56）**：五种触发情形下的事前评估与记录留存（**自述式**——留存期限在事前尚未届期，工具无法核实，只能问机制）
- **交互式问答**：一问一答引导完成自查
- **一键样例**：`--demo` 用内置样例作答直接预览报告形态，无需先答题；报告标注 DEMO，且与台账互斥
- **多格式报告**：Markdown / JSON / HTML
- **支持「不适用」**：未开展的业务/未采用的机制判 `N/A`，**不计入合规率分母**，避免用「没检查」冒充「合规」
- **合规台账与整改进度对比**：`--ledger` 累积历史，下次自动对比出「新增通过 / 新增未通过 / 状态未变」
- **纯本地运行**：数据不离开用户环境

## 快速使用

> ⚠️ 结论必须基于真实作答。只指定 `--scenario` 而不提供作答来源时，程序会直接拒绝执行（退出码 2）。

```bash
# 0) 先看看报告长什么样（内置样例作答，无需先答题；标注 DEMO，不写台账）
python3 scripts/fin-pipl-check.py -s banking --demo
python3 scripts/fin-pipl-check.py -s banking --demo -o demo.html -f html

# 1) 交互式自查（推荐），可把答案存盘
python3 scripts/fin-pipl-check.py -s banking --interactive
python3 scripts/fin-pipl-check.py -s banking --interactive --save-answers answers-banking.json

# 2) 用答案文件作答（复核复跑 / 批处理 / Agent 调用）
python3 scripts/fin-pipl-check.py -s banking --input answers-banking.json

# 3) 出具报告
python3 scripts/fin-pipl-check.py -s banking --input answers-banking.json -o report.md
python3 scripts/fin-pipl-check.py -s banking --input answers-banking.json -o report.json -f json
python3 scripts/fin-pipl-check.py -s banking --input answers-banking.json -o report.html -f html

# 4) 合规台账：自动与上次对比，输出整改进度
python3 scripts/fin-pipl-check.py -s banking --input answers-banking.json --ledger ledger.jsonl

# 场景可选：banking / securities / insurance / payment
python3 scripts/fin-pipl-check.py --list-scenarios
python3 scripts/fin-pipl-check.py --version
```

答案文件格式（`--save-answers` 产物可直接复用）：

```json
{
  "scenario": "banking",
  "answers": {
    "has_privacy_notice": "y",
    "consent_method": "manual",
    "sensitive_items": ["biometric"],
    "has_loan_authorization": false
  }
}
```

## 参考法规

引用**只写到能核对的层级**：PIPL 写到条文号（已核对中国人大网公布的法律全文原文）；行业标准与其余法规**只写名称，不写章条号**。

- 《个人信息保护法》（PIPL）
- JR/T 0171-2020《个人金融信息保护技术规范》
- JR/T 0197-2020《金融数据安全 数据安全分级指南》
- 《金融产品网络营销管理办法》（人民银行等八部门公告〔2026〕第9号，2026-09-30 起施行）
- 《征信业管理条例》
- 《金融消费者权益保护实施办法》
- 《证券期货投资者适当性管理办法》
- 《互联网信息服务算法推荐管理规定》

## 免责声明

本工具是**自述式问卷**，不接入用户的信息系统或文档库，**对作答不作任何核实**；检查结果仅供参考，**不构成法律意见**，不得作为合规证明或监管呈报材料。金融行业合规涉及多重监管要求，请咨询专业法律顾问确认合规状态。

完整免责声明与使用条款见 [`DISCLAIMER.md`](DISCLAIMER.md)，与 [`SKILL.md`](SKILL.md)「⚠️ 重要法律声明」节同源同文。

## 许可证

MIT © 2026 Wei Wu (wwumit)

[GitHub](https://github.com/wwumit/fin-pipl)
