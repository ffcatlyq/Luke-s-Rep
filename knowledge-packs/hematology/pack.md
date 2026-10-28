# 知识包元信息 —— 血液 Hematology

> Demo 知识包，兼作其他治疗领域的复制模板。
> ⚠️ 本知识包内容基于公开医学信息整理，用于智能体演示。**产品事实、适应症、循证数据须由 PM 核实后使用**，尤其对外产出前须核对最新说明书与 MLR 要求。

## 领域概览
血液领域覆盖两大板块：**血液肿瘤**（以淋巴瘤为主）与**血友病**（非肿瘤）。罗氏在此布局了 CD20 全周期产品、ADC、CD20×CD3 双抗，以及血友病拟似双抗。

## 团队与汇报线
- **团队**：血液 Customer Engagement（CE）部门，服务三类人群——中央市场 / 区域市场（PST）/ 销售管理
- **三条汇报线**（完整结构见 `org/department.md`）：
  - 中央市场：PM（IC）→ MM → Franchise Head（FH）
  - 区域市场：PSM → PSL → RCL
  - 销售管理：LEL（圈长）→（REL，部分区域）→ RCL
  - RCL 与 MM 平级，均向 FH 汇报
- **主要跨部门伙伴**：Medical（医学）/ Market Access（市场准入）/ RWE（真实世界研究）/ Regulatory（注册）/ Compliance（合规）

## 产品清单
| 通用名 | 商品名 | 机制 | 主要适应症领域 | 生命周期阶段 |
|---|---|---|---|---|
| rituximab（利妥昔单抗） | 美罗华 MabThera | 抗 CD20 单抗 | NHL / CLL | 成熟期（面临生物类似药） |
| obinutuzumab（奥妥珠单抗） | 佳罗华 Gazyva | 抗 CD20 单抗（糖基化改造） | FL / CLL | 成长期 |
| polatuzumab vedotin（维泊妥珠单抗） | 优罗华 Polivy | 抗 CD79b ADC | DLBCL | 成长期 |
| glofitamab（格菲妥单抗） | 高罗华 Columvi | CD20×CD3 双特异抗体 | R/R DLBCL | 上市期（新兴） |
| mosunetuzumab（莫妥珠单抗） | 皓罗华 Lunsumio | CD20×CD3 双特异抗体 | R/R FL | 上市期（新兴） |
| emicizumab（艾美赛珠单抗） | 舒友立乐 Hemlibra | FVIIIa 拟似双特异抗体 | 血友病 A | 成长期 |

> 注：各产品在中国的**确切获批适应症、线数、说明书表述**以最新版说明书为准，见各产品 `product.md` 并须 PM 核实。

## 目录导航
- `products/`：各产品事实与循证卡（适应症/剂量/循证/信息屋/异议/合规）
- `patient-journey/`：各瘤种全病程患者旅程（标准流转 + 机会点草稿），与五步法配套找业务机会点
- `playbooks/`：产品特定业务打法（"产品 × 五步法某步"的定制化，如 `pola-conversion.md` = Pola 转化率提升），方法引擎在五步法 skill、口径落在本层
- `wiki/`：**学术推广方法论 wiki**（信息屋/异议应对/患者旅程/CRS 沟通/幻灯叙事等通用方法，见 `wiki/index.md`）
- `customers/`：客户/医院分级与患者细分
- `regions/`：区域市场结构 · `sales/`：销售管理维度 · `org/`：组织与汇报线
- `franchise.md`：产品组合策略 · `landscape.md`：竞争格局

## 该领域特有的合规注意点
- **讲者管理高敏感**：血液学术活动多、KOL 集中，讲者遴选/劳务/场次合规是重点（JD 单列职责）。
- **淋巴瘤联合方案多**：注意区分"已获批联合方案"与"探索性方案"，后者不得用于推广。
- **生物类似药竞争**（美罗华）：竞争话术须基于循证，不得贬损。
- **血友病长期用药**：患者援助、长期治疗获益表述须合规。
- 通用规则见 `/compliance/guardrails.md`。
