---
name: literature-research
description: "Systematic literature research for a named clinical trial, intervention, or research program. Triggers on: 'research', 'literature search', 'find papers', 'what studies exist', '文献检索', '查文献', '找论文', '有哪些研究', 'sub-studies', 'follow-up studies', 'citation network', any named trial (e.g. GALLIUM, CLL11, POLARIX). Covers: locate seed paper → read full text → map citation network → classify sub-studies → synthesize implications. Outputs a structured literature map with actionable interpretation."
---

# Literature Research — 系统文献检索与解读

## Workflow

```
1. Seed → 2. Read → 3. Expand → 4. Classify → 5. Interpret
```

### 1. Seed: Locate the anchor paper

Find the primary publication for the target study.

**Source priority:**
- Project files first: `grep -ri "STUDY_NAME" --include="*.html" --include="*.md"` to find existing citations with PMIDs
- PubMed eutils if PMID known: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={PMID}&rettype=abstract&retmode=text`
- PubMed search if PMID unknown: `https://pubmed.ncbi.nlm.nih.gov/?term={STUDY_NAME}`

**Extract from seed paper:**
- PMID, DOI, NCT ID (if trial)
- Study design, sample size, intervention, comparator
- Primary and secondary outcomes with exact numbers
- Funding source / sponsor
- Author group and institution

### 2. Read: Full text extraction

Read the complete paper, not just the abstract.

**Access chain:**
1. PMC full text: `https://pmc.ncbi.nlm.nih.gov/articles/PMC{ID}/`
2. If PMC unavailable, try DOI link
3. Extract: Methods (design, randomization, intervention details), Results (all endpoints with CIs), Discussion (authors' interpretation of limitations)

**Data extraction checklist:**
- [ ] Study design (RCT / cluster RCT / cohort / etc.)
- [ ] Population (N, inclusion/exclusion, demographics)
- [ ] Intervention (what exactly was done — regimen, dose, line of therapy, combination)
- [ ] Comparator (what control group received)
- [ ] Primary outcome (effect size, CI, p-value)
- [ ] Secondary outcomes
- [ ] Subgroup analyses
- [ ] Funding and COI

### 3. Expand: Map the citation network

Search Google Scholar for the complete publication family.

**Query:** `"{STUDY_NAME}" {disease_area}` with date filter `as_ylo={seed_year}`

**Capture from results:**
- Total citation count (e.g., "About 211 results")
- For each relevant paper: title, authors, journal, year, cited-by count, one-line summary

**Pagination:** Read pages 1-2 (20 results) minimum. Continue if high-value papers still appearing.

**Also search for:**
- Design/protocol paper (usually published before main results)
- Sub-studies and secondary analyses (same dataset, different questions)
- Editorials and invited commentaries (same journal, same issue)
- Systematic reviews that include the study
- Follow-up / successor studies by the same team

### 4. Classify: Organize the literature map

Sort all found papers into categories:

| Category | Description | Example |
|----------|-------------|---------|
| **Seed** | The primary results paper | Main RCT publication |
| **Protocol** | Study design paper published before results | Design and rationale paper |
| **Sub-study** | Secondary analysis of the same dataset | Subgroup analysis, biomarker study |
| **Editorial** | Commentary in the same journal issue | Invited editorial on the trial |
| **Successor** | Follow-up study by the same team addressing limitations | Next-generation trial |
| **Review** | Systematic review or meta-analysis including the study | Cochrane review, narrative review |
| **Citing** | Independent papers that reference the study | Guidelines, other trials |

**Output format per paper:**

```
| # | Authors | Title | Journal Year | Cited by | Category | Key finding |
```

### 5. Interpret: Synthesize for the user's context

After mapping the literature, provide:

1. **Why did the study succeed/fail?** — 临床/循证视角：设计是否稳健、主要终点是否达成、人群与终点选择是否合理、亚组是否一致
2. **What did sub-studies reveal?** — Mechanism insights, subgroup effects, process outcomes
3. **How did the field respond?** — Editorial consensus, guideline uptake, replication attempts
4. **What came next?** — Successor studies, design iterations, unresolved questions
5. **Implications for user's project** — 直接映射到 PM 语境：支撑产品信息屋（Message House）、竞品应对、讲者内容循证。从知识包 `knowledge-packs/<领域>/products/<product>/product.md` 读取本产品的获批适应症、核心循证与定位，把文献发现挂到对应字段。

## Anti-patterns

- Do NOT stop at the seed paper. The citation network is where the real insights live.
- Do NOT report citation counts without reading at least the title and snippet of each cited paper.
- Do NOT assume a negative trial is a "failure" — 阴性结果常揭示人群选择、终点设计或机制上的重要信息，对策略同样有价值。
- Do NOT mix up sub-studies (same data) with successor studies (new data).

## Tools

**PubMed eutils (structured data, preferred):**
```
# Single abstract
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={PMID}&rettype=abstract&retmode=text

# Batch abstracts
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={PMID1},{PMID2}&rettype=abstract&retmode=text

# PMC full text
https://pmc.ncbi.nlm.nih.gov/articles/PMC{ID}/
```

**Google Scholar (citation network):**
```
https://scholar.google.com/scholar?q="{STUDY_NAME}"+{disease}&as_ylo={year}
```

**ClinicalTrials.gov (trial metadata):**
```
https://clinicaltrials.gov/api/v2/studies/{NCT_ID}
```

## Data Integrity

All numbers from papers must follow the blog-writer skill's audit rules:
- S-level data (%, n, p, CI) must be traced to the exact location in the paper (abstract/table/figure)
- No numbers from memory — always verify against the source
- Mark unverifiable numbers as `[待验证]`

## 合规挂钩（罗氏 PM 场景）

文献检索本身是内部研究动作，合规要求较低；但**一旦产出进入对外/一线物料**（幻灯、话术、讲者内容、detail aid），
须继续走本仓合规护栏（`compliance/guardrails.md`）：
- **不 off-label**：疗效/人群表述只用知识包 `product.md` 中列明的**中国已获批适应症**；文献里的亚组、探索性终点、未获批线数**不得**当作疗效宣称。
- **循证溯源**：每处疗效/安全性数字标 `[来源：<研究名>]`，以说明书/已发表原文为准。
- **知识包为准**：产品事实、适应症、核心循证以 `knowledge-packs/<领域>/` 为准；知识包没有的，明确说"待核实"，不臆造。
- **物料草稿**：面向外部的成稿顶部标 `⚠️ MLR 送审前草稿`。

## 参考示例

- `references/gallium-example.md` — 血液/淋巴瘤（GALLIUM，一线 FL）完整五步检索示例，可照抄流程。
