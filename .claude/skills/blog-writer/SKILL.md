---
name: blog-writer
description: "Write and audit data-driven external articles (WeChat / 公众号 / case studies) for a Roche PM, with verified references and MLR/off-label compliance guardrails. Triggers on: blog writing, WeChat article creation, case study writing, medical/scientific article drafting, data verification requests, '写博文', '公众号文章', '写科普文章', '案例分析', '核实数据', '审计博文'. Covers the full lifecycle: topic framing → literature search → drafting → data verification → HTML formatting. Enforces two rules: (1) every number traced to a primary source; (2) every external-facing claim passes the repo compliance guardrails (no off-label, evidence-cited, MLR-draft banner)."
---

# Blog Writer — PM 对外文章写作与数据核对

> 角色：**助理**。为罗氏 PM 起草面向外部的科普/案例文章（微信公众号等），核心是**数据溯源 + 合规护栏**双铁律。
> ⚠️ 对外发文属**高合规敏感区**：本 skill 产出一律为 `⚠️ MLR 送审前草稿`，须经医学(M)/法规(R)/法务合规(L)审核后方可发布。发文主体与流程以罗氏内部 SOP 为准。

## 合规护栏（第一铁律，先于写作）

对外文章须全程挂本仓合规红线（`compliance/guardrails.md`）：
- **不 off-label**：适应症/人群表述只用知识包 `product.md` 的**中国已获批适应症**，不暗示、不类推、不延伸。
- **不夸大**：疗效/安全性声明须有循证支撑并标 `[来源：<研究名>]`；禁绝对化用语；获益与风险**平衡呈现**。
- **不与处方/采购挂钩**；**数据分级**：敏感/未公开数据不写入对外稿。
- **产出标注**：成稿顶部标 `⚠️ MLR 送审前草稿`（模板 `assets/wechat-template.html` 已内置横幅），附 MLR 自查清单。
- **知识包为准**：产品事实以 `knowledge-packs/<领域>/` 为准；缺则标"待核实"，不臆造。

## 两阶段工作流

```
阶段一：写作          阶段二：审计
选题 → 文献 → 成文 → 数字提取 → 逐条溯源 → 修正 → 标注
```

**铁律：写作和审计必须分开执行。** 不要边写边验——先写完，再以审计者身份重新审视每一个数字。

## 阶段一：写作

### 1. 选题与框架

- 确定案例数量（通常 3-5 个）
- 每个案例需要：核心框架 + 实施策略 + 可量化成果
- 确定目标读者（医学事务、临床研究、公共卫生）

### 2. 文献检索

```
PubMed eutils API（首选，结构化数据）:
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={PMID}&rettype=abstract&retmode=text

批量检索（逗号分隔多个 PMID）:
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={PMID1},{PMID2},{PMID3}&rettype=abstract&retmode=text

PMC 全文 XML:
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMC{ID}&rettype=xml

ClinicalTrials.gov API:
https://clinicaltrials.gov/api/v2/studies/{NCT_ID}?fields=protocolSection.identificationModule,protocolSection.sponsorCollaboratorsModule
```

### 3. 引用规范

每条引用必须包含：
```
作者 et al. 标题. 期刊缩写. 年份;卷(期):页码. PMID: XXXXXXXX（附 PubMed 链接）
```

引用元数据（期刊、卷、期、页码）必须从 PubMed eutils 返回值逐字复制，不得凭记忆填写。

### 4. 归属标注

每篇引用论文必须标注与主题公司的关系：
- 有公司作者/资助 → 不标注（默认关联）
- 独立研究 → 标注"独立研究，非 XX 资助"
- 竞品公司 → 标注"XX 资助"
- 政府/机构报告 → 标注来源机构

### 5. 成文

- 使用微信公众号 HTML 模板（见 `assets/wechat-template.html`）
- 简体中文，学术科普风格
- 关键数字用 `<span class="key-num">` 或 `<strong>` 标记

## 阶段二：审计

### 1. 数字提取

逐行扫描博文，提取所有可验证数字，按级别分类：

| 级别 | 类型 | 验证要求 |
|------|------|---------|
| S | 论文数据（%、n、p、CI、OR、HR） | 回溯原文摘要/正文逐字核对 |
| A | 统计结论（"显著高于""降低了 X%"） | 核对数值 + 方向 + 显著性 |
| B | 计算衍生（比率、差值） | 展示计算过程 |
| C | 常识性（年份、人口） | 合理性检查 |

详见 `references/audit-checklist.md`。

### 2. 溯源核对（五步）

1. **溯源** — 这个数字从哪来的？找到一手来源
2. **核对** — 与原文逐字比对，不是"大概对"，是精确匹配
3. **交叉验证** — 有第二来源吗？不一致则标注差异
4. **合理性检查** — 数量级、方向、与同领域基准比
5. **标注** — 无法验证的数字标注 `[待验证]`

### 3. 引用审计

对每个 PMID/链接执行：
- 链接是否有效（200 响应）
- 论文标题是否与博文引用一致（从 eutils 逐字比对）
- 期刊/卷/期/页码是否正确
- ClinicalTrials.gov NCT ID 是否指向正确研究（用 API 验证 sponsor + title）
- 项目全称/缩写是否与论文原文一致

### 4. 摘要 vs 正文

**教训**：摘要通常只报告 primary endpoint，secondary endpoints 可能仅在正文表格中。

规则：
- 摘要中找不到的数字 ≠ 数字不存在
- 判定"虚构"前，必须尝试获取全文（PMC XML → 期刊网站 → Europe PMC）
- 如果全文不可访问，标注"摘要未列，需全文确认"，**不得判定为虚构**

### 5. 修正输出

发现错误时：
1. 展示修正前后对比表
2. 标注错误来源（记忆偏差 / 来源混淆 / 四舍五入 / 张冠李戴）
3. 修改后的内容加 `<u>` 下划线标注
4. 检查同批次其他数字是否有同类问题

## 常见错误模式

详见 `references/error-patterns.md`，10 类错误模式（已去公司名的通用形态）。

## 写作风格

### 生态圈写法

当公司与某项目的关联较弱时，不要硬说"XX 主导"，改用生态圈视角：
- 列出各层参与方和角色
- 如实描述公司在生态圈中的定位
- 用表格呈现多层结构

### 数据引用格式

正文中引用数据时使用：
```
数据点（来源研究, 年份, 摘要/正文/表X）
例：一线 FL PFS 获益 [来源：GALLIUM, 摘要 Results 段，数值待核实]（须比对说明书获批适应症）
```

## 交付前自查（MLR 送审前）

- [ ] 顶部已标 `⚠️ MLR 送审前草稿`（模板已内置横幅）
- [ ] 所有适应症/人群在已获批范围内（无 off-label），已比对 `product.md`
- [ ] 所有疗效/安全性数字已溯源、标 `[来源：<研究名>]`，通过审计阶段
- [ ] 无绝对化/夸大用语，获益与风险平衡呈现
- [ ] 无敏感/未公开数据，无与处方/采购挂钩表述
- [ ] 引用元数据（PMID/卷期页/NCT）逐字核对无误

## 归档

成稿存入 `outputs/物料/<日期>_<主题>_对外文章.md`（或 .html）。命名与归档遵循 `AGENTS.md` 第 6 节。

## 关联

- `compliance/guardrails.md` — 合规红线与 MLR 自查清单（对外物料强制）
- `literature-research` — 检索与引文网络（写作阶段的文献来源）
- `slide-ocr-verify` — 图片型来源的数字识别与验证
- `knowledge-packs/<领域>/` — 产品获批适应症、核心循证、信息屋
- `assets/wechat-template.html` — 微信公众号 HTML 模板（已内置 MLR 横幅）
- `references/audit-checklist.md`、`references/error-patterns.md` — 审计清单与错误模式
