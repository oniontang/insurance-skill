# -*- coding: utf-8 -*-
"""从当前目录的 Skill 包生成单页 HTML 目录。
视图一：紧凑清单（默认，一行一个，点行展开）
视图二：分组卡片（便于读全文）
用 @@TOKEN@@ 占位而非 f-string，避免 CSS/JS 花括号被格式化吞掉。
"""
import os, json, datetime

ROOT = "/Users/tangkunhu/Desktop/保险"
OUT = os.path.join(ROOT, "保险Skill目录.html")

CAT = {
    "router":  ("体系与路由",   "#1F6F5C"),
    "sales":   ("销售与经营",   "#8A5A00"),
    "plan":    ("方案与产品分析", "#2F5D8C"),
    "content": ("内容与获客",   "#6B4C9A"),
    "comp":    ("合规与行业通用", "#8C2F39"),
}
ORDER = ["router", "sales", "plan", "content", "comp"]

S = [
 dict(dir="chengeng-growth-router-2.0.0", slug="chengeng-growth-router", cat="router",
      title="陈庚 · 超级保险人", ver="2.0.0", date="2026-07-13",
      brief="读对话判断该用哪个 Skill，只推一个主入口",
      purpose="陈庚系列 Skill 的总入口。先读当前对话，再在四种模式里选一种，每次只为你确定 1 个主 Skill，让顾问直接从真实问题开始，不必先搞懂体系。",
      when="首次安装陈庚 Skill、不知道怎么开始、只说“帮我看看”、交材料但没点名具体 Skill，或一轮任务结束后问“下一步做什么”。用户已点名某个 Skill 时尊重选择，不抢路由。",
      how="四种模式：首次使用 / 任务前路由 / 任务后导航 / 体系说明；按单步路由规则只推一个主 Skill；输出统一为「当前判断 — 还缺什么 — 下一步」三段。",
      out="一次交接：平台支持 Skill 间调用时直接交接，不支持时生成可继续使用的交接卡。",
      note="保留保险合规边界，不承诺成交、理赔、核保、医疗、法律或收入结果。"),

 dict(dir="chengeng-sales-review-1.0.2", slug="chengeng-sales-review", cat="sales",
      title="陈庚 · 销售复盘", ver="1.0.2", date="2026-07-05",
      brief="把客户沟通复盘成事实纪要与下一步动作",
      purpose="复盘保险客户沟通、面谈与方案推进过程，严格区分「客户明确说过的事实」和「从上下文推断的判断」，避免复盘变成自我感动。",
      when="需要复盘客户聊天、电话、面谈、方案讲解、异议处理、跟进结果或陪访记录。",
      how="先分离事实与判断 → 判断客户阶段 → 定位主要需求与关键顾虑 → 找销售卡点与表达风险 → 定下一步动作 → 沉淀可复用经验。",
      out="事实纪要 + 客户阶段与卡点诊断 + 表达问题清单 + 下一步动作 + 可复用经验。",
      note="不编造成交意向、不写成流水账；内置输入校验、错误码、重试复核、反模式 FAQ 与国内模型适配，减少格式漂移。"),

 dict(dir="insurance-consultant-2-1.0.1", slug="insurance-consultant-2", cat="sales",
      title="保险顾问专属智能体技能包", ver="1.0.1", date="2026-05-26",
      brief="保障方案五步框架 + 朋友圈文案 + 异议话术",
      purpose="把一线保险顾问（寿险 + 家庭保障 + 个人 IP 打造）的专业知识系统化打包，覆盖从客户需求到朋友圈经营的完整链路。",
      when="提到保险、保障方案、客户、话术、朋友圈文案（保险相关）、保险行业；需要做客户保障方案、家庭风险评估、异议处理。",
      how="保障方案五步框架：家庭信息采集 → 需求四问 → 风险优先级排序 → 场景差异化方案 → 产品精准匹配；朋友圈三大模板（情感切入 / 场景切入 / 反向切入）；宏观经济信号 → 保险话术映射表；六大常见异议应对 + 关键数据武器；行业标杆「三讲三不讲、三分钟响应、三个主动服务」；信任重建四步法与高净值专项话术。",
      out="客户保障方案、朋友圈文案、宏观关联话术、异议应答、知识库更新记录。",
      note="附客户信息采集表与朋友圈文案模板，可直接填用。"),

 dict(dir="insurance-salesmaster-1.0.0", slug="insurance-salesmaster", cat="sales",
      title="中国保险超级销冠 · 融合 Skill", ver="1.0.0", date="2026-05-29",
      brief="三条通道销冠的心智模型与决策启发式",
      purpose="全通道方法论：融合代理人（叶云燕、曹纪平）、经纪人（明亚精英李扬/翟童瞳/熊琦琦/易容）、互联网平台（慧择程斯文/黄思思、i云保赵斌/吴雄军）三条通道的思维框架与实战心法。",
      when="需要按顶尖销冠的思路拆客户、设计面谈节奏、准备异议应答，或判断自己该用哪种通道打法。",
      how="5 个核心心智模型（需求三角激活、KYC 深度穿透、方案阶梯法、通道适配策略、异议即成交契机）+ 8 条决策启发式（首问恐惧末问渴望、方案讲完等 30 秒、报价前先确认需求、大额保单必须线下见、理赔是最好的销售、先处理情绪再处理方案等）+ 表达 DNA（语气、禁忌词、高频词、句式）+ 异议处理话术库。",
      out="带角色激活规则的销售思路拆解、面谈节奏建议与异议应答话术。",
      note="含明确禁忌词表，输出前需按“表达 DNA”自检语气。"),

 dict(dir="kunlun-sales-script-insurance-1.0.0", slug="kunlun-sales-script-insurance", cat="sales",
      title="保险销售话术助手", ver="1.0.0", date="2026-08-24",
      brief="画客户 → 提价值 → 写话术 → 排异议 → 引成交",
      purpose="面向保险从业者的话术实战助手，按固定五步产出一套可落地、可复用的客户沟通方案。",
      when="要写给具体客户的开场与促成话术、做行业/运营方案类沟通材料，或需要增长型展业工具。",
      how="画客户 → 提价值 → 写话术 → 排异议 → 引成交；配套能力地图、标准流程、输入→产出说明、输出样例与卡点自救。",
      out="按客户画像定制的话术包与成交引导路径，含质量护栏与落地前检查清单。",
      note="明确划分「不适用，请转专业渠道」的情形；自带业务适用识别信号与效果评分矩阵。"),

 dict(dir="licai-insurance-skill-1.0.0", slug="licai-insurance-sales", cat="sales",
      title="理财保险销售专家", ver="1.0.0", date="2026-09-16",
      brief="从 KYC 到保单检视、客户经营与转介绍",
      purpose="理财险与健康险销售的全流程支持：从客户信息采集分类一路做到成交后的客户经营与转介绍。",
      when="向 AI 描述某个客户的情况或销售场景；提到理财险、增额终身寿、年金险、分红险、万能险、重疾险、KYC、客户分类、需求挖掘、产品匹配、话术、异议处理、促成、保单检视、生日祝福、客户经营、转介绍。",
      how="先过合规红线自查，再按场景路由到 7 个模块：kyc 客户采集与分类、matching 需求与产品匹配、scripts 话术设计、proposal 方案讲解与收益演示、policy-review 保单检视与整理、care 祝福与关怀、ops 客户经营复盘与转介绍。",
      out="客户档案与分类、需求总结、产品匹配建议、销售话术、利益演示方案、保单检视报告、关怀文案、经营复盘与转介绍动作。",
      note="附 KYC 模板、保单检视报告模板与产品库模板，可直接复用。"),

 dict(dir="chengeng-pension-solution-design-1.0.0", slug="chengeng-pension-solution-design", cat="plan",
      title="陈庚 · 养老方案设计", ver="1.0.0", date="2026-07-23",
      brief="按生、老、病、死四模块出养老方案报告",
      purpose="养老规划四步法里的第四步：不重复计算，按生、老、病、死四个模块把前面的数字变成可讲给客户听的方案。",
      when="前三步（养老金测算、退休现金流、来源与缺口）已完成，要出养老方案设计报告时。",
      how="生：退休之后怎么生活、资金池怎么安排；老：4 级护理状态与照护资源；病：5 档风险情况下的保障工具组合；死：传承安排如何落地；最后给分阶段行动计划。",
      out="八节结构的《养老方案设计报告》，含方案前提、设计原则与行动计划，可导出 DOCX。",
      note="不写具体保险产品名称、不承诺收益、不把方案写成销售逼单。"),

 dict(dir="insurance-product-compare-1.0.1", slug="insurance-product-compare", cat="plan",
      title="保险产品对比（双引擎）", ver="1.0.1", date="2026-05-30",
      brief="内置 19 个产品 + 自贴方案多公司比价",
      purpose="双引擎保险产品对比工具：一边是内置产品数据，一边是用户自贴方案，支持多公司横向比价与同险种 / 跨险种对比。",
      when="保险经纪人、代理人要给客户做方案比选、整理多家报价，或回答“这两第三款哪个更合适”。",
      how="三种模式：① 内置 19 个产品数据对比（医疗险 6 / 重疾险 6 / 雇主险 3 / 寿险储蓄 3 / 意外险 1）；② 用户自贴方案做多公司横向比价；③ 同险种或跨险种同标的对比。",
      out="结构化对比表 + 场景问答结论。",
      note="数据内置于 SKILL.md，带数据更新日志与已知限制说明（作者 weyn）。"),

 dict(dir="medical-insurance-policy-comparison-1.0.0", slug="medical-insurance-policy-comparison", cat="plan",
      title="医疗保险产品分析与对比", ver="1.0.0", date="2026-07-20",
      brief="医疗险 7 维拆解与 9 级优先级横向对比",
      purpose="懂条款、懂精算、立场明确站在打工人利益一侧的医疗险分析工具，覆盖百万医疗、中端、高端、防癌、惠民保与专项医疗（孕产 / 齿科 / 眼科）。",
      when="任何涉及医疗险条款拆解、产品对比、保障分析、续保稳定性评估的话题：分析这份保险、对比几款百万医疗险、我家怎么配、保不保、外购药报销、保证续保 20 年哪个好。",
      how="先做保单结构识别与条款完整性检查。单一产品按 7 大维度拆解（基本信息、免责条款必须列全、各类清单实用性、值得关注条款、费率分析、增值服务、7 维度总结）；多产品按 9 级优先级排序对比：预算 → 续保稳定性 → 核保/免责 → 基础责任 → 免赔额 → 赔付比例 → 特需部 → 特色保障 → 增值服务。",
      out="单产品深度拆解报告或多产品横向对比表。",
      note="准确性铁律 6 条不可违反，并规定「找不到信息时的标准回复模板」；自带 evals 评测集。"),

 dict(dir="xls-content-1.0.0", slug="xls-content", cat="content",
      title="小绿书内容生产线（保险垂直）", ver="1.0.0", date="2026-07-20",
      brief="选题到配图推草稿箱的六阶段流水线",
      purpose="微信图文 / 图片消息（小绿书）的成批生产线，纯保险垂直。知识性 × 情绪性双载体：封面吃情绪价值，后端给手绘风专业指引，内容先情绪挑逗再专业指导。",
      when="要持续产出保险选题的小绿书图文，或需要选题、提纲、初稿、配图到推草稿箱的一条龙。",
      how="六阶段：Stage 0 选题策划 → 1 提纲确认 → 2 素材与文风 → 3 初稿（≤200 字 + 私域钩子、去 AI 味）→ 4 配图（封面情绪图 + 后端手绘指引图）→ 5 合规与微信规则 → 6 推小绿书草稿箱。",
      out="可直接进草稿箱的完整图文（文案 + 封面图 + 手绘指引图）。",
      note="微信内强私域闭环；配图与推送均有脚本支撑，推送前需过合规检查。"),

 dict(dir="fin-pipl-1.7.0", slug="fin-pipl", cat="comp",
      title="Fin-PIPL 金融个人信息保护合规检查", ver="1.7.0", date="2026-09-26",
      brief="金融个保合规自查，出报告与整改台账",
      purpose="金融行业个人信息保护（PIPL）合规检查工具，基于《个人信息保护法》、JR/T 0171《个人金融信息保护技术规范》与 JR/T 0197《金融数据安全 数据安全分级指南》，覆盖银行、证券、保险、支付四大场景。",
      when="需要给金融业务做个人信息处理合规自查、出具评估报告，或长期跟踪整改进度。",
      how="四种用法：--demo 用内置样例直接出报告（不必先答题）；交互式逐题自查并存盘；用答案文件作答（适合复跑、批处理与 Agent 调用）；--ledger 合规台账自动与上次对比、输出整改进度（跨次累积）。",
      out="Markdown / JSON / HTML 三格式合规报告 + 可持续累积的整改台账。",
      note="SKILL.md 开头有 12 条法律声明：非法律建议、结论基于用户自述且未核实、准确性与责任均有限制。"),

 dict(dir="finance-finance-ops-2.0.2", slug="finance-finance_ops", cat="comp",
      title="金融保险 · 金融财务", ver="2.0.2", date="2026-09-03",
      brief="金融保险财务全流程，人工在环可溯源交付",
      purpose="金融保险行业的财务垂直技能，覆盖金融财务全流程与行业专属场景、指标口径与合规要求，强调人工在环与可溯源交付。",
      when="保险/金融机构的财务分析、指标口径核对、流程性财务交付任务。",
      how="角色定位 → 典型业务场景 → 关键指标 KPI → 合规红线 → 工具与系统集成 → 标准工作流 → 人工在环（HITL）闸门 → 输出规范 → 禁止事项。",
      out="经人工确认、可溯源的财务交付物。",
      note="内置 PaySkill 按量付费接口（支付宝 AI 付，A2M · HTTP 402），商户与生产配置尚待填写。"),
]


def counts(d):
    p = os.path.join(ROOT, d)
    fs = [os.path.relpath(os.path.join(r, f), p)
          for r, _, sub in os.walk(p) for f in sub
          if f not in (".DS_Store", "_meta.json")]
    g = lambda pre: [x for x in fs if x.startswith(pre)]
    refs, scripts, assets = g("references"), g("scripts"), g("assets")
    other = [x for x in fs if not x.startswith(("references", "scripts", "assets", "agents"))
             and x not in ("SKILL.md", "skill.yaml", "package.json", "requirements.txt")]
    parts = []
    if refs:    parts.append(str(len(refs)) + " 份参考文档")
    if scripts: parts.append(str(len(scripts)) + " 个脚本")
    if assets:  parts.append(str(len(assets)) + " 份模板")
    if other:   parts.append("、".join(os.path.splitext(os.path.basename(x))[0] for x in other))
    res = " · ".join(parts) if parts else "单文件（内容全部内置于 SKILL.md）"
    return refs, scripts, assets, other, res, len(refs) + len(scripts) + len(assets) + len(other)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


FIELDS = ["when", "how", "out", "note"]
LABELS = {"when": "何时用", "how": "怎么做", "out": "输出", "note": "边界与注意"}

rows, cards = [], []
T_R = T_S = T_A = 0
for s in S:
    refs, scripts, assets, other, res, nfiles = counts(s["dir"])
    T_R += len(refs); T_S += len(scripts); T_A += len(assets)
    cname, ccolor = CAT[s["cat"]]
    hay = " ".join([s["title"], s["slug"], s["brief"], s["purpose"], s["when"], s["how"],
                    s["out"], s["note"], cname] + refs + scripts + assets + other).lower()

    body_fields = "\n".join(
        '        <div class="row"><dt>' + LABELS[k] + "</dt><dd>" + esc(s[k]) + "</dd></div>"
        for k in FIELDS)
    rows.append(
        '      <div class="item" data-cat="' + s["cat"] + '" data-text="' + esc(hay) + '">\n'
        '        <button class="hd" type="button" aria-expanded="false">\n'
        '          <span class="c-t"><i class="dot" style="background:' + ccolor + '"></i>'
        + esc(s["title"]) + "</span>\n"
        '          <span class="c-b">' + esc(s["brief"]) + "</span>\n"
        '          <span class="c-c">' + cname + "</span>\n"
        '          <span class="c-v mono">' + s["ver"] + "</span>\n"
        '          <span class="c-d mono">' + s["date"] + "</span>\n"
        '          <span class="c-x" aria-hidden="true"></span>\n'
        "        </button>\n"
        '        <div class="bd"><dl>\n' + body_fields + "\n"
        '          <div class="row"><dt>附带资源</dt><dd class="mono">' + esc(res)
        + " · 共 " + str(nfiles) + ' 个文件</dd></div>\n'
        '          <div class="row"><dt>包目录</dt><dd class="mono">' + esc(s["dir"])
        + "</dd></div>\n"
        "        </dl></div>\n"
        "      </div>")

    cards.append(
        '  <article class="card" data-cat="' + s["cat"] + '" data-text="' + esc(hay) + '">\n'
        '    <header class="ch"><span class="tag" style="--c:' + ccolor + '">' + cname
        + '</span><span class="vr"><b class="mono">' + s["ver"] + "</b><i>" + s["date"] + "</i></span></header>\n"
        "    <h3>" + esc(s["title"]) + "</h3>\n"
        '    <p class="purpose">' + esc(s["purpose"]) + "</p>\n"
        '    <div class="use"><span class="ul">应用场景</span><p>' + esc(s["when"]) + "</p></div>\n"
        "  </article>")

groups = []
for cat in ORDER:
    cs = [c for c, s in zip(cards, S) if s["cat"] == cat]
    if not cs:
        continue
    name, color = CAT[cat]
    groups.append(
        '  <section class="grp">\n'
        '    <h2 class="gh"><span class="dot" style="background:' + color + '"></span>' + name
        + '<span class="gc mono">' + str(len(cs)) + "</span></h2>\n"
        '    <div class="grid">\n' + "\n".join(cs) + "\n    </div>\n"
        "  </section>")

chips = ['<button class="chip on" data-f="all" type="button">全部 <b class="mono">' + str(len(S)) + "</b></button>"]
for cat in ORDER:
    n = sum(1 for s in S if s["cat"] == cat)
    chips.append('<button class="chip" data-f="' + cat + '" type="button" style="--c:' + CAT[cat][1]
                 + '">' + CAT[cat][0] + ' <b class="mono">' + str(n) + "</b></button>")

stats = " · ".join([str(len(S)) + " 个技能包", str(len(CAT)) + " 类",
                    str(T_R) + " 份参考文档", str(T_S) + " 个脚本", str(T_A) + " 份模板",
                    "发布 2026-05 ~ 2026-09"])

TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>保险 Skill 目录 · @@N@@ 个技能包</title>
<style>
  :root{ --paper:#FBFAF8; --card:#FFFFFF; --ink:#15161A; --ink2:#3F4148;
         --muted:#8A8D96; --line:#E7E3DD; --line2:#F1EEE9; }
  *{box-sizing:border-box;margin:0;padding:0}
  body{ background:var(--paper); color:var(--ink);
        font:15px/1.68 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue","Microsoft YaHei",sans-serif;
        -webkit-font-smoothing:antialiased; font-variant-numeric:tabular-nums; }
  .mono{ font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace; font-size:.86em; letter-spacing:-.01em }
  .wrap{ max-width:1180px; margin:0 auto; padding:0 26px }
  .dim{ color:var(--muted) }

  header.top{ padding:36px 0 20px; border-bottom:1px solid var(--line) }
  .hl{ display:flex; align-items:baseline; gap:14px; flex-wrap:wrap }
  h1{ font-size:26px; font-weight:640; letter-spacing:-.015em }
  .kicker{ font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted) }
  .stats{ margin-top:9px; font-size:12.5px; color:var(--muted) }

  .bar{ position:sticky; top:0; z-index:20; background:rgba(251,250,248,.95); backdrop-filter:blur(8px);
        border-bottom:1px solid var(--line); padding:9px 0 }
  .bar .wrap{ display:flex; gap:12px; align-items:center; flex-wrap:wrap }
  .sw{ position:relative; flex:0 0 214px }
  input{ width:100%; padding:7px 30px 7px 11px; font:inherit; font-size:13px; color:var(--ink);
         background:var(--card); border:1px solid var(--line); border-radius:7px; outline:none }
  input:focus{ border-color:var(--ink); box-shadow:0 0 0 3px rgba(21,22,26,.06) }
  input::placeholder{ color:#A8ABB3 }
  .clr{ position:absolute; right:6px; top:50%; transform:translateY(-50%); border:0; background:none;
        cursor:pointer; color:var(--muted); font-size:16px; line-height:1; padding:4px 7px; display:none }
  .chips{ display:flex; gap:5px; flex-wrap:wrap; align-items:center }
  .chip{ font:inherit; font-size:12px; padding:4px 10px; border:1px solid var(--line); border-radius:999px;
         background:var(--card); color:var(--ink2); cursor:pointer; white-space:nowrap }
  .chip b{ color:var(--muted); font-weight:500; margin-left:2px }
  .chip:hover{ border-color:#C6C1B8 }
  .chip.on{ background:var(--ink); border-color:var(--ink); color:#fff }
  .chip.on b{ color:rgba(255,255,255,.55) }
  .chip[data-f]:not([data-f="all"])::before{ content:""; display:inline-block; width:6px; height:6px;
         border-radius:50%; background:var(--c); margin-right:6px; vertical-align:1px; opacity:.85 }
  .tools{ display:flex; gap:12px; align-items:center; margin-left:auto; font-size:12px; color:var(--muted) }
  .lnk{ font:inherit; font-size:12px; border:0; background:none; color:var(--ink2); cursor:pointer;
        padding:0; border-bottom:1px solid var(--line) }
  .lnk:hover{ color:var(--ink); border-color:var(--ink) }
  .seg{ display:flex; border:1px solid var(--line); border-radius:7px; overflow:hidden; background:var(--card) }
  .seg button{ font:inherit; font-size:12px; padding:4px 10px; border:0; background:none; color:var(--ink2);
               cursor:pointer; border-right:1px solid var(--line) }
  .seg button:last-child{ border-right:0 }
  .seg button.on{ background:var(--ink); color:#fff }

  main{ padding:4px 0 20px }

  /* ---------- 视图一：紧凑清单 ---------- */
  .lvh{ display:grid; grid-template-columns:var(--cols); gap:16px; padding:9px 12px 7px;
        font-size:10.5px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted) }
  .list{ border-top:1px solid var(--line) }
  .item{ border-bottom:1px solid var(--line2) }
  .hd{ display:grid; grid-template-columns:var(--cols); gap:16px; width:100%; align-items:center;
       padding:8px 12px; border:0; background:none; font:inherit; text-align:left; cursor:pointer; color:var(--ink) }
  .hd:hover{ background:#FDFCFA }
  .item.open .hd{ background:#FDFCFA }
  .c-t{ display:flex; align-items:center; gap:9px; font-weight:560; font-size:13.5px; letter-spacing:-.01em; min-width:0 }
  .c-t span,.c-t{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
  .dot{ flex:0 0 7px; width:7px; height:7px; border-radius:50% }
  .c-b{ font-size:12.5px; color:var(--ink2); overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
  .c-c{ font-size:11.5px; color:var(--muted); white-space:nowrap }
  .c-v{ font-size:11.5px; color:var(--ink2) }
  .c-d{ font-size:11.5px; color:var(--muted) }
  .c-x{ justify-self:end; width:14px; height:14px; position:relative }
  .c-x::before,.c-x::after{ content:""; position:absolute; background:#A8ABB3; transition:transform .16s }
  .c-x::before{ left:0; top:6px; width:14px; height:1.5px }
  .c-x::after{ left:6px; top:0; width:1.5px; height:14px }
  .item.open .c-x::after{ transform:scaleY(0) }
  .item.open .c-x::before{ background:var(--ink) }
  .item.open .c-x::after{ background:var(--ink) }
  .bd{ display:none; padding:2px 26px 20px 48px }
  .item.open .bd{ display:block }
  dl{ border-top:1px dashed var(--line) }
  .row{ display:grid; grid-template-columns:76px 1fr; gap:16px; padding:9px 0; border-bottom:1px dashed var(--line) }
  .row:last-child{ border-bottom:0 }
  dt{ font-size:12px; color:var(--muted) }
  dd{ font-size:13.5px; color:var(--ink2) }
  dd.mono{ font-size:12px; color:#6C6F77; word-break:break-all }

  /* ---------- 视图二：分组卡片 ---------- */
  .grp{ margin-top:34px }
  .gh{ display:flex; align-items:center; gap:10px; font-size:13.5px; font-weight:600; padding-bottom:10px;
       margin-bottom:14px; border-bottom:1px solid var(--line) }
  .gc{ margin-left:2px; padding:1px 7px; border:1px solid var(--line); border-radius:999px;
       font-size:11.5px; color:var(--muted); font-weight:400 }
  .grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(318px,1fr)); gap:14px }
  .card{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:17px 19px 18px }
  .ch{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:12px }
  .tag{ font-size:11.5px; letter-spacing:.04em; color:var(--c); font-weight:600 }
  .tag::before{ content:""; display:inline-block; width:5px; height:5px; border-radius:50%;
                background:var(--c); margin-right:6px; vertical-align:2px }
  .vr{ display:flex; align-items:center; gap:9px; font-size:11.5px; color:var(--muted) }
  .vr b{ font-weight:500; color:var(--ink2); background:var(--line2); padding:1px 7px; border-radius:5px }
  .card h3{ font-size:15.5px; font-weight:620; letter-spacing:-.01em; line-height:1.45 }
  .purpose{ margin-top:9px; color:var(--ink2); font-size:13px; line-height:1.72 }
  .use{ margin-top:13px; padding-top:11px; border-top:1px dashed var(--line) }
  .ul{ display:block; font-size:11px; color:var(--muted); letter-spacing:.02em; margin-bottom:4px }
  .use p{ font-size:12.5px; color:var(--ink2); line-height:1.72 }

  footer{ margin-top:48px; padding:22px 0 54px; border-top:1px solid var(--line);
          font-size:12.5px; color:var(--muted); line-height:1.9 }
  .empty{ display:none; text-align:center; padding:70px 0; color:var(--muted); font-size:14px }
  .hide{ display:none !important }

  :root{ --cols:236px minmax(200px,1fr) 104px 56px 84px 16px }
  @media (max-width:1080px){ :root{ --cols:210px minmax(160px,1fr) 96px 52px 78px 16px } }
  @media (max-width:900px){
    .c-c,.c-d{ display:none } :root{ --cols:minmax(150px,1fr) minmax(150px,1.4fr) 54px 16px }
    .grid{ grid-template-columns:repeat(auto-fill,minmax(270px,1fr)) } .sw{ flex:1 1 100% }
    .tools{ margin-left:0; width:100%; justify-content:space-between }
  }
  @media (max-width:600px){
    .wrap{ padding:0 16px } h1{ font-size:22px }
    :root{ --cols:1fr 16px } .c-b{ display:none }
    .row{ grid-template-columns:1fr; gap:2px } .bd{ padding-left:16px }
  }
  @media (prefers-reduced-motion:reduce){ *{ transition:none !important } }
</style>
</head>
<body>

<header class="top">
  <div class="wrap">
    <div class="hl"><p class="kicker">Skill Catalog</p><h1>保险 Skill 目录</h1></div>
    <p class="stats">@@STATS@@</p>
  </div>
</header>

<div class="bar">
  <div class="wrap">
    <div class="sw">
      <input id="q" type="search" placeholder="搜索名称、用途、触发词（按 / 聚焦）" autocomplete="off" spellcheck="false">
      <button class="clr" id="clr" type="button" aria-label="清空">&times;</button>
    </div>
    <nav class="chips" id="chips">@@CHIPS@@</nav>
    <div class="tools">
      <span id="count">@@N@@ / @@N@@</span>
      <button class="lnk" id="exp" type="button">展开全部</button>
      <span class="seg">
        <button type="button" data-v="list" class="on">清单</button>
        <button type="button" data-v="card">卡片</button>
      </span>
    </div>
  </div>
</div>

<main class="wrap">
  <section id="v-list">
    <div class="lvh"><span>名称</span><span>一句话用途</span><span>分类</span><span>版本</span><span>发布</span><span></span></div>
    <div class="list">
@@ROWS@@
    </div>
  </section>

  <section id="v-card" class="hide">
@@CARDS@@
  </section>

  <p class="empty" id="empty">没有匹配的 Skill，换个关键词试试。</p>

  <footer>
    数据来源：各技能包 <span class="mono">SKILL.md</span> frontmatter 与正文章节结构、<span class="mono">_meta.json</span> 发布信息，扫描时间 @@DATE@@。
    所有技能均含保险合规边界，输出不构成收益承诺或法律、医疗建议。
  </footer>
</main>

<script>
(function(){
  var q=document.getElementById('q'), clr=document.getElementById('clr'),
      items=[].slice.call(document.querySelectorAll('.item')),
      cards=[].slice.call(document.querySelectorAll('.card'),),
      grps=[].slice.call(document.querySelectorAll('.grp'),),
      chips=[].slice.call(document.querySelectorAll('.chip'),),
      cnt=document.getElementById('count'), empty=document.getElementById('empty'),
      exp=document.getElementById('exp'),
      vlist=document.getElementById('v-list'), vcard=document.getElementById('v-card'),
      segs=[].slice.call(document.querySelectorAll('.seg button'),),
      f='all', view='list';

  function pool(){ return view==='list' ? items : cards; }

  function apply(){
    var t=q.value.trim().toLowerCase(), n=0;
    pool().forEach(function(el){
      var ok=(f==='all'||el.dataset.cat===f)&&(!t||el.dataset.text.indexOf(t)>-1);
      el.classList.toggle('hide',!ok); if(ok) n++;
    });
    if(view==='card'){
      grps.forEach(function(g){
        var vis=[].slice.call(g.querySelectorAll('.card:not(.hide)')).length;
        g.classList.toggle('hide', vis===0);
      });
    }
    chips.forEach(function(b){ b.classList.toggle('on', b.dataset.f===f); });
    cnt.textContent=n+' / '+pool().length;
    empty.style.display=n?'none':'block';
    clr.style.display=q.value?'block':'none';
    if(t && n===1) open(pool().filter(function(e){return !e.classList.contains('hide');})[0], true);
  }

  function open(el,on){
    if(!el) return;
    el.classList.toggle('open',on);
    el.querySelector('.hd').setAttribute('aria-expanded',on?'true':'false');
    syncExp();
  }
  function syncExp(){
    var open=items.filter(function(i){return i.classList.contains('open');}).length;
    exp.textContent = open ? '收起全部' : '展开全部';
    exp.style.visibility = view==='list' ? 'visible' : 'hidden';
  }

  items.forEach(function(it){
    it.querySelector('.hd').addEventListener('click',function(){
      open(it, !it.classList.contains('open'));
    });
  });
  exp.addEventListener('click',function(){
    var any=items.some(function(i){return !i.classList.contains('open');});
    items.forEach(function(i){ open(i, any); });
  });
  chips.forEach(function(b){ b.addEventListener('click',function(){ f=b.dataset.f; apply(); }); });
  segs.forEach(function(b){
    b.addEventListener('click',function(){
      view=b.dataset.v;
      segs.forEach(function(x){ x.classList.toggle('on', x===b); });
      vlist.classList.toggle('hide', view!=='list');
      vcard.classList.toggle('hide', view!=='card');
      apply(); syncExp();
    });
  });
  q.addEventListener('input',apply);
  q.addEventListener('keydown',function(e){ if(e.key==='Escape'){ q.value=''; apply(); } });
  clr.addEventListener('click',function(){ q.value=''; q.focus(); apply(); });
  document.addEventListener('keydown',function(e){
    if(e.key==='/' && document.activeElement!==q){ e.preventDefault(); q.focus(); }
  });
  apply(); syncExp();
})();
</script>
</body>
</html>
"""

html = (TPL.replace("@@N@@", str(len(S)))
            .replace("@@STATS@@", stats)
            .replace("@@CHIPS@@", "\n".join(chips))
            .replace("@@ROWS@@", "\n".join(rows))
            .replace("@@CARDS@@", "\n".join(groups))
            .replace("@@DATE@@", datetime.date.today().isoformat()))
open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, os.path.getsize(OUT), "bytes | rows", len(rows), "| cards", len(cards),
      "| refs", T_R, "scripts", T_S, "assets", T_A)
