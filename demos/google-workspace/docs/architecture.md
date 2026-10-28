# Google Workspace 集成架构

> 面向想了解原理的开发者。跳过不影响使用。

## OAuth 认证流程

`auth.py` 在本地起 HTTP server（端口 19876）接 OAuth 回调，按 runtime 分两轨：

**build-cli（WSL2 / macOS）**：

```
auth.py 起 HTTP server (localhost:19876)
    → WSL2 调起 Windows 默认浏览器（localhost 与 Windows 共享，无需 SSH 隧道）
    → 用户完成 Google OAuth consent
    → Google redirect 到 localhost:19876/callback，server 直接捕获 authorization code
    → 交换为 access_token + refresh_token
```

**Ona（FlexDev）**：

```
auth.py 起 HTTP server (容器内 19876)
    → VS Code SSH 端口转发映射到本地浏览器
    → 用户完成 Google OAuth consent
    → Google redirect 到 localhost:19876/callback
    → SSH 隧道将请求转发回 Ona 容器，server 捕获 authorization code
    → 交换为 access_token + refresh_token
```

首次授权需要浏览器交互（一次性），之后调用自动用 refresh_token 刷新，无需浏览器。

## 数据隔离

所有成员共用同一个 OAuth Client（"应用注册"），但每个人用自己的 Google 账号授权，获得独立的 Token。

| 共享 | 隔离 |
|------|------|
| OAuth Client JSON（应用凭证） | Token（每人独立） |
| GCP Project（应用注册平台） | 数据访问（只能访问自己的 Drive/Gmail 等） |

成员 A 的 token 只能访问 A 的数据。GCP Project owner 也看不到任何人的具体数据。

## Token 生命周期

| Token | 有效期 | 说明 |
|-------|--------|------|
| Access Token | 1 小时 | 过期后自动用 Refresh Token 刷新，用户无感 |
| Refresh Token | 不过期 | 只要不主动 revoke，一直有效 |

### 加载优先级（文件优先）

`gw_client.py:_load_token_data` 的逻辑（以代码为准）：

1. **文件 `/tmp/google_token.json`**（优先）— `auth.py` 授权后写入，永远最新
2. **环境变量 `GOOGLE_TOKEN_JSON`**（回退）— 环境重建 / 新 shell 后用（build-cli 来自 `~/.bashrc`，Ona 来自 Project Secret）

文件优先的原因：revoke + re-consent 后只有 `/tmp` 文件是新 token，环境变量可能仍是旧的——优先文件避免用旧 token 刷新时的 `invalid_grant`。

## 环境变量

| 环境变量 | 用途 | 修改后是否需要重启 | 原因 |
|---------|------|-------------------|------|
| `GOOGLE_OAUTH_CLIENT_JSON` | OAuth 应用凭证 | **Ona 需重启 / build-cli 不需** | Ona 的 Project Secret 在容器启动时注入，运行中添加的不生效；build-cli 写 `~/.bashrc` + 开新 shell 即可 |
| `GOOGLE_TOKEN_JSON` | 用户 Token | **不需要** | `auth.py` 成功后会写入 `/tmp/google_token.json`，代码优先读文件 |

## 已验证的 API

| API | Scope | 状态 |
|-----|-------|------|
| Google Drive | 读写 | 可用 |
| Google Docs | 读写 | 可用 |
| Google Sheets | 读写 | 可用 |
| Gmail | 读写 + settings | 可用 |
| Google Calendar | 读写 | 可用 |
| Google Slides | 读写 | 可用 |
| Google Chat | 消息/空间/成员 | 可用 |
| Cloud Search | 内网搜索（RocheHome） | 可用 |

完整 scope 列表以代码为准：`scripts/gw_client.py` 中的 `SCOPES` 变量。
