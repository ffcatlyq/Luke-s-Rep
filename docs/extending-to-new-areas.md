# 扩展指南：新增治疗领域

> 如何把这个 PM 智能体从血液扩展到眼科、神经科学、免疫等新领域。
> 核心：**只加知识包，不改通用引擎**（技能/合规/AGENTS.md 不动）。

## 原理

```
通用引擎（不动）                 知识包（新增）
├─ AGENTS.md                    knowledge-packs/
├─ skills/          ← 读取 →    ├─ hematology/      （已有）
└─ compliance/                  └─ ophthalmology/   （新增，照模板填）
```

技能层从"当前知识包"读取产品知识，只要新知识包遵循标准结构，所有技能（双语汇报、竞品简报、讲者管理、物料+MLR）自动适用。

## 步骤（以眼科为例）

1. **复制模板**
   ```
   cp -r knowledge-packs/_TEMPLATE knowledge-packs/ophthalmology
   ```
2. **填元信息** `pack.md`：团队、汇报线、产品清单、该领域合规注意点。
3. **填格局** `landscape.md`：疾病、患者旅程、诊疗路径、市场、关键客户。
4. **填组合** `franchise.md`：单品定位 + 组合协同关系。
5. **填产品**：每个产品复制 `products/_PRODUCT_TEMPLATE` 为 `products/<product>/`，填 `product.md`。
6. **验证**：在对话中让智能体"用眼科知识包做一份 X 的竞品简报"，确认技能正常读取。

## 完成检查清单

- [ ] `pack.md` 产品清单完整，汇报线正确
- [ ] `landscape.md` 疾病与市场信息填充
- [ ] `franchise.md` 组合逻辑清晰（单品 + 协同）
- [ ] 每个产品 `product.md` 六大块齐全：基本信息/适应症/循证/信息屋/竞品/合规边界
- [ ] 所有疗效声明标注来源或"待核实"
- [ ] 该领域特有合规点已在 `pack.md` 注明
- [ ] 未改动 `skills/`、`compliance/`、`AGENTS.md`（保持通用）

## 何时才需要动通用引擎

绝大多数情况**不需要**。仅当出现**跨领域通用的新能力或新合规规则**时才改：
- 新技能对所有领域有用 → 加 `skills/<new>.md`
- 合规规则升级（如接入罗氏内部 SOP）→ 改 `compliance/guardrails.md`
- 某领域特有合规 → 写进该知识包的 `pack.md`，**不要**污染通用护栏
