# Skill 重叠审计与整理

扫描时间：2026-09-29　扫描范围：全局技能仓库 `~/.qwenworkcn/skills/`（33 个）+ 本项目 `Desktop/保险/`（12 个）
口径：逐个读取 `SKILL.md` frontmatter 与正文，按关键词全文检索与文件级命中计数取证；未改动任何技能文件。

## 一、结论摘要

1. 全局技能仓库里**没有任何保险/销售/理财垂直技能**，因此"把保险相关技能 fork 到项目"这一操作没有对象可执行。
2. 仓库内**真正的同类型重复只有一组**：`media-generation` 与 `media-generation-premium`。
3. 项目内 12 个保险技能之间**存在 4 组实质重叠**，集中在话术与异议处理、医疗险对比、KYC 客户分类、产品匹配与方案讲解。
4. 这 12 个包**尚未安装进技能仓库**，只是躺在项目目录里的源码包，当前对话无法调用它们。

## 二、全局技能仓库盘点（33 个）

| 分组 | 数量 | 成员 | 判定 |
|---|---:|---|---|
| 钉钉族 | 14 | aisearch / aitable / calendar / chat / contact / doc / drive / event / mail / minutes / misc / shared / todo / wiki | 同族不同产品，职责边界在 description 里已互写，**不算重复** |
| 办公文档 | 4 | docx / pptx / xlsx / pdf | 按文件格式分工，**不重复** |
| 媒体生成 | 2 | media-generation v1.2.1 / media-generation-premium v1.1.1 | **重复**，见下 |
| 前端与界面 | 4 | finesse-ui / ui-ux-pro-max-plus / frontend-spec / website-building | 部分重叠：实现工艺 / 设计资源库 / 编码规范 / 变现指南，各有侧重但触发词互相打架 |
| 网页发布 | 2 | qw-pages / qw-pages-supabase | 互补（发布 vs 数据库准备），**不重复** |
| 元工具 | 4 | create-skill / plugin-creator / find-skills / config-sync | 职责不同（建技能 / 建插件 / 找技能 / 同步配置） |
| 其他 | 3 | pc-health-report / qwenwork-guidance / yunqi-agent | 独立 |

### 重复项证据：media-generation vs media-generation-premium

- 两者 description 同义：均为"生成或编辑图片、生成视频或音乐，异步产物，不用于文字转语音"。
- 版本关系倒挂：premium 为 v1.1.1，标准版已 v1.2.1。
- 两份 SKILL.md 差异 163 行，差异集中在模型选路与计费描述，能力清单几乎一致。
- `media-generation-premium` **未出现在当前可用技能列表**中，属于未启用的孤儿副本；仅当应用启用企业旗舰版媒体体验时才应由它接管。

### 仓库自身的三个缺陷（顺手记录）

| 技能 | 问题 | 影响 |
|---|---|---|
| yunqi-agent | `SKILL.md` 顶部存在两段 frontmatter（先是 install_source 等安装元数据块，再是 name/displayName 块） | 技能列表里它的 description 被解析成 `---`，语义检索与自动触发都会失效 |
| ui-ux-pro-max-plus | frontmatter `name: ui-ux-pro-max` 与目录名不一致 | 按名调用或引用时易错 |
| website-building | frontmatter `name: 网站搭建`（中文）与英文目录名不一致 | 同上 |

## 三、项目内 12 个保险 Skill 的重叠（附文件级证据）

### 重叠 1：话术与异议处理，4 个包各写一遍（核心）

| 包 | 证据（关键词命中数） |
|---|---|
| kunlun-sales-script-insurance-1.0.0 | `SKILL.md` 话术×40、异议×10、成交×12（整个包即话术流水线） |
| insurance-salesmaster-1.0.0 | `SKILL.md` 话术×10、异议×25；`references/research/02-objection-handling.md` 异议×25 |
| insurance-consultant-2-1.0.1 | `SKILL.md` 异议×11；`references/话术库.md` 话术×25、`references/异议处理.md` 异议×9、`references/宏观话术.md` 三个专章 |
| licai-insurance-skill-1.0.0 | `SKILL.md` 话术×11、异议×4；`references/scripts.md` 话术×7 |
| sales-review-1.0.2 | 弱重叠（复盘视角回看表达风险，话术×0、异议×5） |

四套异议处理各自独立成文，口径不统一：同一个"太贵了，买不起"，insurance-consultant-2 在 `references/异议处理.md` 与 `references/话术库.md` 里给的是**对比法**（保费 vs 重疾治疗费、折合每天多少钱），insurance-salesmaster 在 `SKILL.md` 与 `references/research/02-objection-handling.md` 里给的是**追问法**（"跟什么比觉得贵"、功能不同不能直接比）。实际调用时结果取决于命中哪个包。

### 重叠 2：医疗险对比，2 个包覆盖同一场景（核心）

| 包 | 证据 |
|---|---|
| medical-insurance-policy-comparison-1.0.0 | `SKILL.md` 医疗险×32、百万医疗×12、横向对比×6；功能二即"多产品横向对比" |
| insurance-product-compare-1.0.1 | `SKILL.md` 医疗险×10、百万医疗×4；内置 19 个产品中含 6 个医疗险 |

两者都能接"帮我对比几款百万医疗险"。差异在深度：前者做条款与续保精算视角（免责列全、9 级优先级），后者做多公司比选表（含重疾/雇主/寿险/意外）。但两边的 description 都没有互写边界，触发会抢。

### 重叠 3：KYC 与客户分类，2 套模板并存（次一级）

| 包 | 证据 |
|---|---|
| insurance-consultant-2-1.0.1 | `assets/客户信息采集表.md`（姓名/社保/负债字段）、`references/客户分类.md`（家庭×16、年收入×3）、五步框架第一步"家庭信息采集" |
| licai-insurance-skill-1.0.0 | `references/kyc.md`（KYC×4、需求挖掘×2）、`assets/kyc-template.md` |
| insurance-salesmaster-1.0.0 | `SKILL.md` KYC×11（模型 2"KYC 深度穿透"） |

两份采集模板字段不互通，客户档案无法在两个包之间复用。

### 重叠 4：产品匹配与方案讲解（次一级）

| 包 | 证据 |
|---|---|
| licai-insurance-skill-1.0.0 | `references/matching.md` 匹配×10、`references/proposal.md` 年金/增额寿方案讲解与收益演示 |
| insurance-consultant-2-1.0.1 | 五步框架第三步"风险优先级排序"、第五步"产品精准匹配" |
| pension-solution-design-1.0.0 | 生老病死四模块方案设计（明确不写具体产品名），与 licai 的 proposal 在"养老/年金方案"上部分重叠 |

### 非重叠但同域（无需处理）

内容获客侧：insurance-consultant-2 的朋友圈三大模板与 xls-content 的小绿书六阶段生产线属不同平台、不同工序，互补而非重复；growth-router 只在体系层做路由，不产内容。

## 四、处置建议

核心（影响能否调用与结果一致性）

1. 话术与异议处理确立单一事实源：建议以 kunlun（话术流水线最完整）或 licai `scripts.md` 为主库，其余三包改为引用，或按"渠道（代理人/经纪人/互联网）× 险种"显式切分各自负责的话术域。
2. 两个医疗险对比包互写边界：在各自 description 与"与其他技能的边界"章节写明——多公司比选走 insurance-product-compare，单产品条款与续保深度走 medical-insurance-policy-comparison。

次一级

3. KYC 合并为一份采集表 + 一份分类规则，统一字段，使客户档案可跨包复用。
4. 产品匹配统一口径：把 consultant 的"需求四问 → 风险优先级 → 精准匹配"与 licai 的 kyc → matching 流程对齐成同一条链路。

可选

5. 用 plugin-creator 把这 12 个包打成一个"保险销售"插件，统一入口、统一合规边界声明，并解决"未安装即不可用"的问题。
6. 仓库侧清理：给 media-generation-premium 标注启用条件或下架；修复 yunqi-agent 的双 frontmatter。

## 五、本次未执行的操作

- 未 fork：全局仓库无保险类技能可复制，"fork 到保险目录"没有对象。
- 未安装：没有把 12 个包复制进 `~/.qwenworkcn/skills/`。
- 未修改：项目内 12 个技能包与目录页文件全部保持原样（此前的去品牌改动是上一轮任务，备份在 `.backup-debrand-20260928/`）。
