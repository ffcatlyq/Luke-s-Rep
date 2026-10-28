---
name: google-workspace
description: 以编程方式访问 Google Workspace API（Drive、Docs、Sheets、Gmail、Calendar、Slides、Forms、Chat、Cloud Search），通过 demo 脚本、`gws` CLI 或直接调 API。当用户要求"访问 Google Drive"、"读取 Google Docs"、"操作 Sheets"、"清理 Drive"、"扫描 Drive"、"导出 Drive 文件"、"Google Workspace 集成"、"看下今天日程"、"未读邮件"、"用 gws"、"Workspace 一次性查询"时触发。也在用户给出 Roche 内网 URL（*.roche.com gSite、Drive 链接、Docs 链接）时触发——不要用 web_read，用 Google API 读取。
user-invocable: true
---

# Google Workspace 集成

## Roche 内网 URL 处理规则

**当用户给出 `*.roche.com` 或 `*.gene.com` 的 URL 时，不要用 `web_read`。** 这些地址需要 Roche SSO 登录，`web_read` 只会拿到登录页。

正确做法，按 URL 类型分：

| URL 模式 | 用什么 API | 怎么做 |
|----------|-----------|--------|
| `sites.google.com/...` (gSite) | **`gsite_read.py`** | 见下方「gSite 两路径」——先 Drive export，失败回退 cookie-bridge |
| `docs.google.com/document/d/...` | Docs API | `get_docs_service().documents().get(documentId=ID)` 读全文 |
| `docs.google.com/spreadsheets/d/...` | Sheets API | `get_sheets_service().spreadsheets().values().get(...)` |
| `docs.google.com/presentation/d/...` | Slides API | `get_slides_service().presentations().get(...)` |
| `drive.google.com/...open?id=...` | Drive API | `get_drive_service().files().get(fileId=ID)` + export |
| 其他 `*.roche.com` 内网页面 | Cloud Search API | 搜索关键词，从结果 snippet 拼凑内容 |

**绝对不要**让用户截图或复制粘贴内网页面内容——你有 API 能读。

### gSite 两路径（实测 2026-06-16）

gSite 有两套独立访问控制，**先试 Drive，列不到再 cookie**。统一入口 `gsite_read.py`（自动选路径）：

```bash
cd demos/google-workspace/scripts
python3 gsite_read.py --list                 # 列 Drive 可见的 gSite（A 类）
python3 gsite_read.py "罗氏制药中国"           # 按名读（A 类，秒读）
python3 gsite_read.py "https://sites.google.com/roche.com/<name>/..."  # 自动：Drive 找不到→cookie
```

- **A 类（源文件共享给你）**：Drive API 列得到（`mimeType='application/vnd.google-apps.site'`），`drive.files().export(fileId,'text/plain')` 直接拿全文，零额外配置。`--list` 能列出的都属此类。
- **B 类（没共享、按组织/AD 组发布的 published named site，如 IEP）**：Drive 列不到本体，OAuth token 也进不去（`sites.google.com` 网页只吃浏览器 SSO cookie，Bearer token 被重定向到登录页）。**读完整正文**唯一路径是 cookie-bridge 同步 google 登录 cookie（receiver `gsite` service，域 `sites.google.com` + `accounts.google.com`）。首次：**在该 site 页面上**登录 → 扩展 service=gsite Sync → `chrome://extensions` 重载扩展（host_permissions 变更过）→ 重跑（注意：在别的 google 页如 RocheHome 同步，抓不全 sites.google.com 的会话 cookie，会被弹登录）。

> **先用 Cloud Search 定位再决定怎么读**：Cloud Search（`searchApplicationId='searchapplications/default'`，不需 admin，见 `demos/google-workspace/docs/cloud-search.md`）能跨内网**搜到** gSite/Drive/Wiki 页（返回 title/url/snippet），是找「某内网页/文档在哪」的正解——不要再说它"卡 searchApplicationId / 用不了"。但它只给 snippet 不给完整正文：定位到具体 gSite 后，**A 类走 Drive export、B 类走 cookie-bridge** 读全文。

## 工具选择优先级

操作 Workspace 时按这个顺序决策：

| 任务类型 | 用什么 | 例子 |
|---------|--------|------|
| 一次性查询、临时探索 | **`gws` CLI** | "看下今天日程"、"列 Drive 前 10 个文件"、"未读邮件几封" |
| 标准工作流（议程/邮件摘要/周报） | **`gws` helper** | `gws calendar +agenda`、`gws gmail +triage`、`gws workflow +weekly-digest` |
| Drive 治理（重复/大文件/清理） | **`drive_scan.py` / `drive_cleanup.py`** | 业务逻辑已封装，gws 要重新组装 |
| Gmail 分流归档 | **`gmail_triage.py`** | 同上 |
| Chat 摘要 | **`chat_digest.py`** | 同上 |
| Forms 读取 | **`forms_responses.py`** | 同上 |
| Cloud Search (RocheHome) | **直接调 API**（`gw_client.py`） | gws 不支持 |
| 复杂场景、跨 API 编排 | **直接调 API**（`gw_client.py`） | 写脚本时用 |

**默认行为**：用户问简单查询时，先想能不能一行 `gws` 解决，能就别写 Python。Python 脚本会留下临时文件、需要 5-10 倍时间。

**`gw_client.py` 定位**：薄 auth SSOT，不是 API 全覆盖层。一次性查询走 `gws`，`gw_client` 只在三种情况用——①长任务（token 自动 refresh，gws 的 access token 1h 就死）②跨 API 编排 ③gws 没有的 service（Cloud Search）。别用 Python 重造 gws 已有的能力。

### Shared Drive（共享云端硬盘）文件

Drive API 默认只搜索用户的 My Drive。共享云端硬盘（Team Drive）中的文件必须加 `supportsAllDrives=True`，否则返回 404：

```python
# 漏 supportsAllDrives 会 404
drive.files().get(fileId=fid, fields='name,mimeType').execute()

# 正确
drive.files().get(fileId=fid, fields='name,mimeType', supportsAllDrives=True).execute()
drive.files().get_media(fileId=fid, supportsAllDrives=True)
```

**所有 Drive API 调用都应加 `supportsAllDrives=True`**，对 My Drive 文件无副作用。

## 工具链位置

所有脚本在 `demos/google-workspace/scripts/`：

| 文件 | 用途 |
|------|------|
| `auth.py` | OAuth 授权（首次使用，获取 token） |
| `gw_client.py` | API 客户端（自动 token 刷新，所有场景共享） |
| `drive_export.py` | Drive 文件遍历与导出 CLI |
| `drive_scan.py` | Drive 全量扫描 + 治理报告 |
| `drive_cleanup.py` | Drive 批量清理（dry-run + 执行） |
| `gmail_triage.py` | Gmail 收件箱治理：自动分类 + 归档噪音邮件（dry-run / execute / status） |
| `chat_digest.py` | Google Chat 群消息/私信摘要（按 thread 分组，支持 DM、关键词过滤） |
| `forms_responses.py` | Google Forms 工具：读取 form 结构（题目+选项）和回复（Markdown/JSON） |

## 前置条件

Token **文件优先**加载（`/tmp/google_token.json` → env `GOOGLE_TOKEN_JSON` fallback），过期 access_token 自动 refresh。机制详见 `demos/google-workspace/docs/architecture.md` §Token 生命周期（SSOT）。

验证 token 有效：

```bash
cd demos/google-workspace/scripts && python3 gw_client.py
```

**首次授权**（仅当 token 不存在）：见 `demos/google-workspace/README.md` 快速开始，按 runtime（environment block 的 `OS Version`）选 build-cli / Ona 分支。

## 关键约束

- Google 原生文件（Docs/Sheets/Slides）不占存储配额，无 size 字段
- Drive API 分页上限 1000/页，全量扫描 13 万文件约需 5 分钟
- 批量操作先 dry-run 确认，再 `--execute`；`--execute` 是移入回收站（30 天可恢复），非永久删除
- refresh_token 长期有效（不主动 revoke 则不过期），过期 access_token 由 `gw_client.py` 自动刷新

## 场景脚本

各脚本完整命令见 `demos/google-workspace/README.md`「有哪些工具可以用」表 或 `python3 <script> --help`。要点：

- **Drive 导出**：`drive_export.py list|tree|export|batch`（Docs→纯文本，Sheets→JSON，Slides→逐页文本）
- **Drive 治理/清理**：`drive_scan.py scan|report` + `drive_cleanup.py duplicates|big|stale|folder` —— **清理必须先 dry-run，用户同意后才 `--execute`**
- **Chat 摘要**：`chat_digest.py`（常用 Space：`AAQAJI8eMKw` CDE Community、`AAQAfOIdqx0` CD2-AI-Hackathon、`AAQA5x-JPxc` Build CLI）
- **Forms**：`forms_responses.py info|responses <form_id_or_url>`（接受完整 URL 或裸 Form ID）

### 在 Python 代码中使用

```python
from gw_client import get_drive_service, get_gmail_service, get_chat_service
# get_docs/sheets/calendar/slides/forms/people/tasks/admin_directory_service 同理

drive = get_drive_service()
files = drive.files().list(pageSize=10, supportsAllDrives=True).execute()
```

## 用 gws CLI 做一次性查询

一次性查询能一行 `gws` 解决就别写 Python（见上「工具选择优先级」；何时回 Python 那张表也在那）。**安装步骤、复用 demo token、95 内置 skills/recipes 说明**见 `demos/google-workspace/docs/api-scenarios.md` §九（SSOT）。

检查安装：`which gws || ls ~/.local/bin/gws`

**跑 gws 前先刷 token**（gws 用 1h 过期的 access token，这行幂等触发 refresh；别直接读 `/tmp/google_token.json` 的 token 字段，可能已过期）：

```bash
export GOOGLE_WORKSPACE_CLI_TOKEN=$(cd demos/google-workspace/scripts && python3 -c "from gw_client import get_credentials; print(get_credentials().token)")
```

**4 层 help**（method 的 `--help` 不告诉你 `--params` 填什么——必须看 `gws schema`）：

```bash
gws --help                                # 所有 service
gws <service> --help                      # resource
gws <service> <resource> --help           # method
gws <service> <resource> <method> --help  # 本地 flag（--params/--format/--page-all）
gws schema <service>.<resource>.<method>  # API 参数完整文档（description/enum/required）
```

常用：`gws calendar +agenda`、`gws gmail +triage --max 10`、`gws workflow +weekly-digest`、`gws drive files list --params '{"pageSize":5}' --format table`、`--dry-run` 只校验不发请求、`--page-all` 流式分页。

## 参考文档

- 完整探索记录：`demos/google-workspace/README.md`
- API 自动化场景：`demos/google-workspace/docs/api-scenarios.md`（§九有 gws 进阶用法的人类向说明）
- SSO 集成指南路径 8：`docs/guide/roche-sso-integration-guide.md` §10
- GCP Project: `rdsz-dw`（Silicon Hitchhiker）
- OAuth Client（GCP Project `rdsz-dw`）: build-cli 存 `~/.bashrc` 的 `GOOGLE_OAUTH_CLIENT_JSON`，Ona 存同名 Project Secret
- gws 官方仓库：https://github.com/googleworkspace/cli
