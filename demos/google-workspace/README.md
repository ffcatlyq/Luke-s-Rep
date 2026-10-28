# Google Workspace AI 集成

让 AI 帮你操作 Google Drive、Gmail、Calendar、Chat 等——在 Ona 环境中用自然语言就能完成。

## 能做什么

| 场景 | 举例 |
|------|------|
| Drive 文件管理 | "帮我扫描 Drive，找出重复文件" "导出这个文件夹下所有文档" |
| Gmail 收件箱治理 | "帮我把 Jira 通知都归档" "创建自动分流规则" |
| Chat 消息摘要与发送 | "CDE 群最近 3 天聊了什么" "发个 chat 给 xxx" |
| 文档读写 | "读取这个 Google Doc 的内容" "往 Sheet 里写入数据" |
| 内网搜索 (Cloud Search) | "在 RocheHome 搜索 ROMINE" — 详见 [Cloud Search 集成](docs/cloud-search.md) |

这些操作通过 Google Workspace API 实现。你只需要完成一次授权，之后 AI 就能代你调用所有 API。

---

## 快速开始

### 你需要准备什么

- [x] 已加入社区（CIDM Group `silicon-hitchhiker-user`）
- [x] 已 Fork [hub 仓库](https://github.com/roche-innersource/silicon-hitchhiker) 到你的个人 org
- [x] 一个能跑这个 repo 的环境：**build-cli（WSL2 / macOS 本地 shell）** 或 **Ona（FlexDev dev container）**

下面每一步按这两种 runtime 分轨。**判断你在哪**：本地终端、`~/` 是你机器的 home → build-cli；浏览器里的 flexdev.roche.com dev container → Ona。

> **Ona 用户注意**：Ona Web 端的端口共享被组织安全策略禁用，Google OAuth 授权（需浏览器跳转 localhost）只能走**本地 VS Code 通过 SSH 连接 Ona**。还没配 VS Code 见 [社区指南 → 开始开发](../../docs/guide/community-guide.md#开始开发)；遇"组策略阻止"见 [troubleshooting 指南](../../docs/guide/troubleshooting-gitpod-cli-blocked.md)（可能需先申请 [Temporary Admin Access](https://roche.service-now.com/rose?id=nr_sc_cat_item&sys_id=a99afbe44fa313c0605d451f0310c750&table=sc_cat_item&searchTerm=temporary%20admin)，自动审批）。build-cli 本地直接开浏览器，无此限制。

---

### 第 1 步：配置 OAuth Client

把 OAuth Client JSON 配成环境变量 `GOOGLE_OAUTH_CLIENT_JSON`。

**build-cli**：写进 `~/.bashrc`（把下面那一整行 JSON 填进单引号），开新 shell 生效：

```bash
echo "export GOOGLE_OAUTH_CLIENT_JSON='<下面这一整行 JSON>'" >> ~/.bashrc
```

**Ona**：[flexdev.roche.com](https://flexdev.roche.com) → 你的 Project → **Secrets** → **New Secret** → Type **Environment variable** → Name `GOOGLE_OAUTH_CLIENT_JSON`，Value 粘贴下面这一整行。

JSON 格式（从 GCP Console 下载的 Desktop OAuth Client，占位符换成你自己的值）：

```
{"installed":{"client_id":"<YOUR_CLIENT_ID>.apps.googleusercontent.com","project_id":"<YOUR_PROJECT_ID>","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"<YOUR_CLIENT_SECRET>","redirect_uris":["http://localhost"]}}
```

> 凭证值不写进仓库——从 GCP Console 下载后放到 `/tmp/oauth_client.json`，
> 配置步骤见 `docs/google-workspace-setup.md`。

- **build-cli**：`source ~/.bashrc` 或开一个新终端即可生效。
- **Ona**：保存后**重启你的 Ona 环境**——Project Secret 在容器启动时注入，运行中添加的不会出现在当前进程，必须重启。

> **这个 JSON 是什么？安全吗？** 这是一个 OAuth 应用注册信息（Desktop 类型），所有社区成员共用。Desktop 类型的 client_secret 不是机密——[RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252#section-8.5) 明确规定这类 secret 不得视为机密。安全性由你自己的 Google 账号授权（下一步）保证，别人拿到这个 JSON 也访问不了你的数据。

---

### 第 2 步：安装依赖

Ona 环境会通过 `.ona/automations.yaml` 的 `installDeps` 任务在启动时自动安装。
如需手动安装（或在 build-cli / 本地环境），运行：

```bash
pip install -r demos/google-workspace/requirements.txt
```

> 依赖清单以 [`requirements.txt`](requirements.txt) 为准（SSOT）。
> 你也可以直接告诉 Ona AI："帮我安装 Google Workspace API 的 Python 依赖"，它会自动处理。

---

### 第 3 步：授权你的 Google 账号

```bash
cd demos/google-workspace/scripts
python3 auth.py
```

- **build-cli（WSL2 / macOS）**：脚本自动调起本机默认浏览器（WSL2 走 Windows 浏览器）。用 `xxx@roche.com` 登录 → consent 页点 **Allow** → 浏览器跳回 localhost，脚本自动完成。无需 SSH 隧道。
- **Ona**：脚本打印一个 OAuth URL，**复制到本地浏览器**打开 → 登录 → **Allow** → 经 VS Code SSH 端口转发跳回，脚本自动完成。

> **Ona 页面一直转圈圈？** 授权回调要经过 `浏览器 → localhost:19876 → VS Code SSH 隧道 → Ona 容器`，SSH 隧道空闲超时或网络波动会卡住。解决：**重启 VS Code** 重连 Ona，重跑 `python3 auth.py` 打开**新** URL（别重复点旧 URL，会 state mismatch）。确认 VS Code 已转发 **19876** 端口（看底部 **Ports** 面板）。build-cli 无端口转发问题。

---

### 第 4 步：持久化 Token

`auth.py` 成功后已把 token 写入 `/tmp/google_token.json`，代码**优先读文件**，当前会话即刻可用。持久化是为了环境重建 / `/tmp` 清空后免重新授权：

- **build-cli**：`auth.py` 会自动把 token sync 进 `~/.bashrc`（env `GOOGLE_TOKEN_JSON`），无需手动操作。
- **Ona**：手动存 Project Secret——Ona Web UI → Project → **Secrets** → **New Secret**（Environment variable）→ Name `GOOGLE_TOKEN_JSON`，Value 粘贴终端输出的 JSON（一行）。这次**不用重启**（代码优先读 `/tmp` 文件；Secret 是给下次环境重建用的回退）。

---

### 第 5 步：验证

```bash
cd demos/google-workspace/scripts && python3 gw_client.py
```

看到你的账号和 token 过期时间就 OK。或直接让 AI"验证下 Google Workspace API 是否可用，列我 Drive 前 5 个文件"——它会调 `gw_client.py`。

---

## 有哪些工具可以用

你不需要记住这些命令——直接用自然语言告诉 AI 你想做什么就行。以下列表供参考：

### Drive 文件管理

| 你想做的 | 对应工具 |
|---------|---------|
| 看看某个文件夹里有什么 | `scripts/drive_export.py list` |
| 显示文件夹树状结构 | `scripts/drive_export.py tree` |
| 导出一个文件的内容 | `scripts/drive_export.py export` |
| 批量导出整个文件夹 | `scripts/drive_export.py batch` |
| 全量扫描 Drive | `scripts/drive_scan.py scan` |
| 生成治理报告（重复文件、大文件、过期文件） | `scripts/drive_scan.py report` |
| 清理重复文件 | `scripts/drive_cleanup.py duplicates` |
| 清理大文件 / 过期文件 | `scripts/drive_cleanup.py big` / `stale` |

### Gmail 收件箱治理

| 你想做的 | 对应工具 |
|---------|---------|
| 看看收件箱状态 | `scripts/gmail_triage.py status` |
| 预览分流规则会匹配哪些邮件 | `scripts/gmail_triage.py dry-run` |
| 执行分流（创建 filter + 归档噪音邮件） | `scripts/gmail_triage.py execute` |

### Google Chat 摘要

| 你想做的 | 对应工具 |
|---------|---------|
| 看看最近的群消息 | `scripts/chat_digest.py --since 24h` |
| 查看与某人的私信 | `scripts/chat_digest.py --dm xxx@roche.com` |
| 按关键词过滤消息 | `scripts/chat_digest.py --keywords xxx,yyy` |

> 所有清理操作默认是 **dry-run**（只预览不执行），加 `--execute` 才会真正操作。清理是移入回收站，30 天内可恢复。

### 不需要脚本，直接对话就能做的

除了上面的 CLI 工具，AI 还能直接调用 Google Workspace 全部 8 个 API 帮你完成更多操作。常见场景举例：

- **Sheets**："把这个表的 B 列数据汇总一下" "标红所有缺失值"
- **Slides**："帮我看看这个 PPT 讲了什么" "用数据填充模板"
- **Docs**："根据会议纪要生成结构化报告" "用站点信息表填充合同模板"
- **Calendar**："下周找个大家都有空的 1 小时" "分析我这个月的会议时间占比"
- **Cloud Search**："在 RocheHome 搜索 ROMINE 相关文档"

> 完整的 8 个 API 能力全景、26+ 个自动化场景和跨 API 联动方案，详见 [API 场景全景](docs/api-scenarios.md)。

---

## 深入了解

| 文档 | 面向 | 内容 |
|------|------|------|
| [API 场景全景](docs/api-scenarios.md) | 所有人 | 8 个 API、26+ 个自动化场景、跨 API 联动方案 |
| [技术架构](docs/architecture.md) | 开发者 | OAuth 原理、Token 生命周期、环境变量机制、数据隔离 |
| [管理员手册](docs/admin-guide.md) | 管理员 | GCP 项目配置、scope 管理、踩坑记录、用户 onboarding |
| [Cloud Search 集成](docs/cloud-search.md) | 所有人 | RocheHome 内网搜索的使用和配置 |

---

## 目录结构

```
google-workspace/
├── README.md                      ← 你在这里
├── scripts/                       ← Python 工具脚本
│   ├── auth.py                    ← OAuth 授权（首次使用运行一次）
│   ├── gw_client.py               ← API 客户端（自动 token 刷新）
│   ├── drive_export.py            ← Drive 文件遍历与导出
│   ├── drive_scan.py              ← Drive 全量扫描 + 治理报告
│   ├── drive_cleanup.py           ← Drive 批量清理
│   ├── gmail_triage.py            ← Gmail 收件箱治理
│   └── chat_digest.py             ← Google Chat 群消息摘要
└── docs/                          ← 深入文档
    ├── admin-guide.md             ← 管理员手册（GCP 配置、scope 管理）
    ├── architecture.md            ← 技术架构（OAuth、Token、环境变量）
    ├── api-scenarios.md           ← API 自动化场景全景
    └── cloud-search.md            ← Cloud Search 集成
```

---

## 参考链接

| 资源 | 地址 |
|------|------|
| 社区指南 | [community-guide.md](../../docs/guide/community-guide.md) |
| VS Code 连接踩坑记录 | [troubleshooting-gitpod-cli-blocked.md](../../docs/guide/troubleshooting-gitpod-cli-blocked.md) |
| Roche SSO 集成指南 | [roche-sso-integration-guide.md](../../docs/guide/roche-sso-integration-guide.md) |
| Google Drive API 文档 | https://developers.google.com/drive/api/v3/reference |
| Google Chat API 文档 | https://developers.google.com/chat/api/reference/rest |
| GCP Console | https://console.cloud.google.com/?project=rdsz-dw |
