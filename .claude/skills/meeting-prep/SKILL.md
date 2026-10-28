---
name: meeting-prep
description: 给一个 Google Calendar event ID 或会议标题/时间，输出会前 prep brief：参会人简介、agenda、相关 doc、最近邮件讨论摘要。当用户要求"会前准备"、"meeting prep"、"准备这个会议"、"待会儿这个会有啥背景"、"prep brief" 时触发。
---

# Meeting Prep — Pre-meeting brief

## 定位

会议开始前 5 分钟用得上。给一份 prep brief 让你进会议室就知道：

- 谁在场，title / 团队 / 老板是谁
- 议程是什么（event description 解析）
- 相关讨论历史（最近 14 天邮件 thread 摘要）
- 相关 doc（attached agenda doc / prep doc 摘要）
- 建议关注的问题（基于以上 context 推荐）

走 build-cli 自带 Claude Code budget，**不调外部 LLM**。

## 触发 + CLI

| 用法 | 说明 |
|---|---|
| `/meeting-prep` | 列出今天还没开始的会议让用户选 |
| `/meeting-prep <event_id>` | 指定 Calendar event ID |
| `/meeting-prep "title fragment"` | 模糊匹配今天/明天的会议 |
| `--days-ahead 1`（默认）/ `--days-ahead 3` | 不指定 event_id 时往前看几天 |
| `--output <path>` | 默认 `/tmp/meeting-prep-<event_id>.md` |
| `--no-emails` | 跳过 Gmail 搜索（快但少 context） |
| `--no-docs` | 跳过 Drive doc 导出 |

## 工作流（5 步）

### Step 1 — 解析 event

**用户给了 event_id**：

```bash
cd demos/meeting-transcribe/scripts && python3 build-context.py \
    --event-id <id> --include-docs
```

**用户给了 title fragment**：

```bash
python3 find-meeting.py --start <today_start> --end <today_end + days_ahead>
```

返候选 events 后按 title 模糊匹配，唯一命中直接用，多命中让用户选。

**用户没给参数**：

```bash
python3 find-meeting.py --start <now> --end <now + days_ahead>
```

列出所有未开始的会议让用户选 event_id。

### Step 2 — People enrichment

`build-context.py --event-id <id> --include-docs` 已经返了 attendees + organizer 含 title + manager（一跳）。

**注意**：

- 同名人按 canonical email 区分（参考 [chat-reply skill](../chat-reply/SKILL.md) Canonical ID rule）
- dept code（`TSCBH` / `ARGA`）**不要**原样进 brief，用 title 替代

### Step 3 — Linked docs（默认开）

`build-context.py --include-docs --max-doc-bytes 10000` 把 attached Doc 全文（截 10KB）导出。比 [meeting-minutes](../meeting-minutes/SKILL.md) 的 5KB 容许长——prep 阶段需要更完整 context。

### Step 4 — Recent emails（默认开）

```python
# Gmail.search 拼 query:
attendees = " OR ".join(f"from:{email}" for email in attendee_emails)
keywords = "<event title 关键词>"
query = f"({attendees}) ({keywords}) newer_than:14d"

# Gmail API users.messages.list(q=query, maxResults=20)
# 取每个 thread 第一封，做 1 句摘要
```

**限制**：

- 单 query 限 20 封
- 每个 thread 取最新 1 封（不展开整个 thread）
- 单封正文截 1KB 给 Claude 做摘要

### Step 5 — 输出 prep brief

写到 `--output <path>`，默认 `/tmp/meeting-prep-<event_id>.md`。

## 输出格式

```markdown
# 会前准备 / Pre-Meeting Brief

**会议**: 聊一下 IEGC 问答机器人
**时间**: 2026-05-26 11:00–11:30 (Asia/Shanghai)
**地点 / Meet**: 一楼咖啡吧
**主持**: Weiwei Zhang (Senior RWD Scientist)

## 议程 / Agenda

<event description 解析后的议程项>

- IEGC 问答机器人上线方案
- 资源评估（IT / 算力）
- 知识库范围

## 参会人 / Attendees

- **Weiwei Zhang** (Senior RWD Scientist, manager: Sha TAO/Head of IEG&MC) — 主持
- **Felix Yu** (Publication Manager, manager: Jing Li/Biometrics & Publication Leader)
  - 5/15 邮件提了"机器人 v0 已经能回答 80% FAQ，但需要 IT 评估生产化路径"
- **Silicon Hitchhiker** (Data & Analytics Solution Architect, manager: Fred Lu/Head of Product) — 你

## 相关文档 / Related Docs

- [IEGC 问答机器人方案 v0.3](url) — Felix 整理的草稿。摘要：基于 Galileo Platform，知识库 100 篇 FAQ，目前 RAG retrieval 命中 78%。

## 邮件讨论摘要 / Email Thread Summary

- **Re: IEGC 问答机器人 IT 资源** (Felix → Sha, 5/22)
  Sha 5/22 回复"建议先走 ADP，避免自建"。Felix 还在评估 ADP 是否能跑过 v0 的 retrieval pipeline。

- **IEGC 知识库源数据准备** (Weiwei → Felix, 5/19)
  讨论用 SharePoint 还是 Drive 当 source。Felix 倾向 Drive（直接接 RAG）。

## 建议关注问题 / Suggested Talking Points

1. **资源边界**：Felix 说"v0 能跑"，但生产化要不要走 ADP？ADP 限制对 IEGC 知识库（C2 数据）有什么影响
2. **数据范围**：知识库目前 100 篇 FAQ，未来扩到全 IEGC SOP（500+）时算力够吗
3. **上线 timeline**：Sha 之前提"今年内上线"，Q3 还是 Q4？
4. **维护 owner**：机器人上线后 RAG 重建谁来跑（Weiwei / Felix / IT）
```

## Anti-patterns

- ❌ 把所有 attendees 邮件历史全 dump（信息爆炸） — 单 thread 只取最新 1 封 + 1 句摘要
- ❌ 把 attendees 私聊 / Chat 历史也拉进来 — 隐私越界，**不调 Chat API**
- ❌ dept code 原样写进 brief — 不可读
- ❌ 把 manager 写成"manager: A → B → C"完整 chain — 一跳够，太深噪音
- ❌ talking points 写成 generic 的"了解最新进展" — 必须基于 brief 里的具体 context 推荐
- ❌ emoji 装饰 — 见 [chat-reply skill](../chat-reply/SKILL.md) 默认不加

## 隐私 / 敏感

- prep brief 不上传外部，落用户指定路径
- 如果 attached doc 含 C3/C4（财务、合规、PII），输出建议落 `$WORKDOCS_PATH/` 而非 hub
- 邮件正文截断后只用 1 句摘要，不全文 dump

## 关联

- [meeting-minutes](../meeting-minutes/SKILL.md) — prep brief 输出可作为会后 minutes 的 prior context（手工传或 minutes skill 自己读）
- [demos/meeting-transcribe/scripts/build-context.py](../../../demos/meeting-transcribe/scripts/build-context.py) — Calendar + People + Drive helper
- [demos/google-workspace/](../../../demos/google-workspace/) — Gmail / Drive / Calendar API 客户端

## 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| event_id 找不到 | event 不在你的 calendar / 已删 / 私会 | 让用户检查 `gcal://...` 链接里的 eventid |
| Gmail search 0 结果 | 关键词太严 / 14 天内没邮件 | 加 `--days-ahead 30` 扩范围；或 `--no-emails` 跳过 |
| Drive doc export 失败 | doc 是 SharePoint / 外部链接 | 在 brief 里只列 URL，不导出正文 |
| attendees 多人没 title | external attendees / contractor | brief 里标 "(external)" 不强行编 title |
