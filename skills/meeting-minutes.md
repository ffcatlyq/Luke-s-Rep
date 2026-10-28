# 技能：会议纪要（Meeting Minutes）

> 角色：**助理**。把会议 transcript（或速记）转成结构化中英双语纪要，突出决议与行动项。JD 明确要求中英双语写作，会议纪要是 PM 高频场景。
> 移植自通用技能库（silicon-hitchhiker），已适配 PM 场景与合规护栏。

## 触发条件
用户诉求包含："整理会议纪要""翻译会议纪要""出英文 minutes""meeting minutes""summarize meeting""会议纪要"，或提供一份 transcript/录音转写要求整理。

## 输入（缺失则追问）
- 会议 transcript / 速记 / 转写文本（若是 ASR 转写且专名有误，先走 `transcript-cleanup.md` 校对）
- 会议基本信息：主题、时间、参会人（含 title/角色，若有）
- 语言需求：中英对照（默认）/ 仅中 / 仅英
- 输出用途：内部存档 / 上报 / 跨部门同步（决定详略与敏感度）

## 任务流
1. **确认会议元数据**：主题、时间、主持、参会人（含 title）。参会人信息缺失就追问或让用户手工列。
2. **敏感内容过滤**（起草前必做）：grep transcript 找 marker，**标记段整段不进纪要**：
   - "不要记录" / "这条不要记" / "口头说一下" / "不要在大群里说" / "private 一下" / "敏感的话"
   - C3/C4 数据（PII、合规、商业策略、未公开决议）即便无 marker 也保守处理，不确定就不进。
3. **保守做 speaker attribution**（见下规则）——不靠语气/职责猜说话人。
4. **生成中英并排纪要**：按下方模板，决议与行动项优先。
5. **合规检查**：产品相关表述遵循护栏；敏感数据标注"内部，勿外传"。
6. **沉淀**：存 `outputs/minutes/<日期>_<主题>_会议纪要.md`。
7.（可选）**上下文增强**：若环境接了 Google Workspace，可从 Calendar 拉参会人/agenda、People API 拉 title/manager 补全 attribution。无账号则纯 transcript 出纪要。

## Speaker attribution 规则（保守，避免张冠李戴）

| 情境 | 处理 |
|---|---|
| 自我指认明确（"我刘锐认为"） | 标 speaker |
| 显式 @ 称呼后续段落 | 加 `[likely speaker: X]`，保留 `[likely]` 标记 |
| merged 双路转写（有 mic/loopback 标注） | 按声道标"本人"/对方 |
| 仅靠词汇/角色/语气推断 | **永远不标** |
| 多人混说一段 | 不标 |

> 同名人按 canonical email 区分——罗氏同名 4+ 人常见，不要按 displayName 匹配。
> dept code（如 `TSCBH`/`ARGA`）对读者无意义，**不进纪要**；title 才有用。

## 产出模板（中英并排）
```markdown
# 会议纪要 / Meeting Minutes

**会议 / Meeting**: <主题> / <英译>
**时间 / Time**: 2026-XX-XX HH:MM–HH:MM (Asia/Shanghai)
**主持 / Chair**: <name (role)>
**参会 / Attendees**:
- <Name (title)> — Roche
- ...

## 议程对照 / Agenda Recap
**CN**: <计划议程 vs 实际讨论，标记跑题项>
**EN**: <same>

## 决议 / Decisions
- **CN**: <决议> ｜ **EN**: <decision>

## 行动项 / Action Items
| Owner | Action (CN) | Action (EN) | Due |
|---|---|---|---|
| <name> | <行动> | <action> | <date> |

## 未决问题 / Open Questions
- **CN**: <问题> ｜ **EN**: <question>

## 议题讨论 / Topics Discussed
### 1. <主题> / <Topic>
**CN**: <段落> ｜ **EN**: <paragraph>
```

## 合规检查（本技能）
- [ ] "不要记录"等 marker 段落已过滤，未进纪要
- [ ] C3/C4 敏感数据不进外发版本，内部版标注"内部，勿外传"
- [ ] speaker 未靠猜标注（存疑处保留 `[likely]` 或不标）
- [ ] 产品疗效相关表述有循证、不夸大、不 off-label
- [ ] 中英术语一致，产品名对照准确

## 关联
- `transcript-cleanup.md` — ASR 转写先校对专名再整理纪要
- `bilingual-report.md` — 纪要可作为向上双语汇报的素材
- `email-authoring.md` — 纪要发送 / follow-up 邮件
