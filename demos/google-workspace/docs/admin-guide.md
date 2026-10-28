# Google Workspace 管理员手册

> 面向管理员（维护 GCP 项目和 OAuth 配置的人）。下次忘了怎么操作时，打开这个文件。

## GCP 项目信息

| 项目 | 值 |
|------|---|
| Project ID | `rdsz-dw` |
| Project Name | Silicon Hitchhiker |
| OAuth Client Name | Silicon Hitchhiker CLI |
| OAuth Branding App Name | Silicon Hitchhiker |
| Organization | roche.com |
| OAuth Client Type | Desktop app |
| Consent Screen | Internal（roche.com 组织内用户直接可用） |
| Console 入口 | [console.cloud.google.com](https://console.cloud.google.com/?project=rdsz-dw) |

## OAuth Client 管理

### 创建 / 修改 OAuth Client

1. [GCP Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials?project=rdsz-dw)
2. 选择已有的 Desktop 类型 OAuth Client，或点 **Create Credentials → OAuth client ID**
3. Application type 选 **Desktop app**
4. 创建后下载 JSON，格式为 `{"installed": {...}}`

### Consent Screen 配置

1. [Google Auth Platform → Data Access](https://console.cloud.google.com/auth/scopes?project=rdsz-dw)（左侧菜单 Data Access，不是 Edit App）
2. User type: **Internal**（只有 roche.com 域内用户可授权，无需 Google 审核）
3. 点 **Add or remove scopes** 添加所需 scope

### Client Secret 存储

- Desktop 类型的 client_secret 不是机密（[RFC 8252 §8.5](https://datatracker.ietf.org/doc/html/rfc8252#section-8.5)）
- 当前做法：Client JSON 直接写在 README 快速开始中，所有成员共用
- 安全性由每人独立的 Google 账号授权保证

## Scope 管理

当前 scope 列表以代码为准：`scripts/gw_client.py` 中的 `SCOPES` 变量。文档不硬编码完整列表，避免不一致。

### 新增 scope 的完整流程

1. **代码**：在 `scripts/gw_client.py` 的 `SCOPES` 列表中添加新 scope
2. **GCP Console**：[APIs & Services → Library](https://console.cloud.google.com/apis/library?project=rdsz-dw) 启用对应 API
3. **Consent Screen**：[Google Auth Platform → Data Access](https://console.cloud.google.com/auth/scopes?project=rdsz-dw) → Add or remove scopes → 添加新 scope
4. **重新授权**：每个用户需要重新运行 `auth.py`（旧 token 不覆盖新 scope）
   ```bash
   rm /tmp/google_token.json
   cd demos/google-workspace/scripts
   python3 auth.py
   ```
5. **更新 token 到持久层**（按 runtime 分轨）：
   - **Ona / FlexDev**：把新 token 更新到 Project Secret `GOOGLE_TOKEN_JSON`
   - **build-cli (WSL2/macOS)**：`auth.py` 的 `sync_to_bashrc` 会自动更新 `~/.bashrc` 里的 `GOOGLE_TOKEN_JSON`（前提是该行已存在）；新 shell 生效
6. **（可选）让新 token 生效**：
   - **Ona**：重启容器（Project Secret 在容器启动时注入），或临时 `GOOGLE_TOKEN_JSON="" python3 script.py` 绕过旧 env
   - **build-cli**：`source ~/.bashrc` 或开新 shell

> **Consent Screen 未加 scope 的后果**：`auth.py` 的授权页面会一直转圈，不显示 scope 列表。这是因为 Internal 类型的 Consent Screen 不会显示未注册的 scope，Google 直接拒绝了请求但没有给出明确错误。

## Token 管理

Token 加载逻辑详见 [架构文档 → Token 生命周期](architecture.md#token-生命周期)。

### 手动 Revoke Token

```bash
# 获取当前 token
python3 -c "
from scripts.gw_client import get_credentials
creds = get_credentials()
print(creds.token)
"

# Revoke
curl -X POST "https://oauth2.googleapis.com/revoke?token=<ACCESS_TOKEN>"
```

Revoke 后用户需要重新运行 `auth.py` 授权。

### Token 迁移到新环境

Token 本体绝不进 git / 备份包（只存 Secret 或 `~/.bashrc`），换环境需手动带过去。按 runtime 分轨：

**Ona / FlexDev（换 class / 换 region / 重建容器）**
1. 从旧环境的 Project Secret 复制 `GOOGLE_TOKEN_JSON` 的值
2. 在新环境的 Project → Secrets 创建同名环境变量
3. 重启新环境即可，不需要重新授权

> ⚠️ **换 region / 新 project 的坑**：Secret 绑在 Project 上，换到不同 region 或新建 Project 时 **不会自动带过来**。迁移前务必确认新 Project 的 Secrets 里已有 `GOOGLE_TOKEN_JSON`——否则 `gws` 和任何调 Drive 的脚本（含 cc-migrate 的 `data_restore.py`）会 `sys.exit(1)`。这是 cc 容器迁移双轨最脆的一环，见 [cc-migrate README](../../../tools/cc-migrate/README.md)。

**build-cli (WSL2/macOS)**
- token 常驻 `~/.bashrc` 的 `GOOGLE_TOKEN_JSON` + `/tmp/google_token.json`，本地文件系统持久，换机器时把 `~/.bashrc` 那一行带过去即可；`/tmp` 那份丢了重跑 `auth.py` 会重建。

## 用户 Onboarding

新成员加入时的配置步骤：

1. 确认成员已加入 CIDM Group `silicon-hitchhiker-user`
2. 确认成员已 Fork hub 仓库并有自己的 Ona 环境
3. 让成员按 README 的「快速开始」5 步操作即可
4. 每人独立授权，获得自己的 Token——管理员不需要为每个人单独配置

## 踩坑记录

| 问题 | 原因 | 解决方式 |
|------|------|---------|
| 添加 Secret 后 `auth.py` 报"环境变量未设置" | Project Secret 在容器启动时注入 | **Ona**：添加 Secret 后**重启环境**；**build-cli**：确认 `~/.bashrc` 有 `export GOOGLE_TOKEN_JSON=...` 并 `source ~/.bashrc` |
| OAuth consent 页面卡住转圈 | callback 端口没有 HTTP server 监听 | 确保 `auth.py` 正在运行且 VS Code 端口 19876 已转发 |
| 浏览器跳转后页面空白 | VS Code 没有自动转发端口 | 检查 VS Code 底部 Ports 面板，手动添加 19876 |
| 点 Allow 后页面一直转圈 | SSH 端口转发通道空闲超时或网络波动 | 重启 VS Code，重新连接后运行 `auth.py`，打开新 URL |
| VS Code 端口转发 state mismatch | 重复点击授权 URL | 只打开一次 URL，不要重复点击 |
| Ona Web 端无法完成授权 | 端口共享被组织策略禁用 | 必须用本地 VS Code SSH 连接 |
| VS Code 连接 Ona 报"组策略阻止" | AppLocker 缺少 allow rule | 申请 [Temporary Admin Access](https://roche.service-now.com/rose?id=nr_sc_cat_item&sys_id=a99afbe44fa313c0605d451f0310c750&table=sc_cat_item&searchTerm=temporary%20admin) 后按 [troubleshooting 指南](../../../docs/guide/troubleshooting-gitpod-cli-blocked.md) 操作 |
| gcloud Drive scope 被拦截 | gcloud 内置 OAuth Client 被 Workspace 白名单拦截 | 使用自建 OAuth Client（本项目已提供） |
| 重新授权后 API 仍报 `invalid_scope` | 环境变量中的旧 token 覆盖了文件中的新 token | **Ona**：更新 Secret `GOOGLE_TOKEN_JSON` 后重启容器，或临时 `GOOGLE_TOKEN_JSON="" python3 script.py`；**build-cli**：`auth.py` 已自动更新 `~/.bashrc`，`source ~/.bashrc` 或开新 shell |
| Consent Screen 授权页转圈不显示 scope | Consent Screen 未添加对应 scope | 在 GCP Console 的 OAuth Consent Screen 中添加 scope 后重试 |

## 安全注意事项

- **Client Secret 不入库**：当前 Desktop 类型的 client_secret 不是机密（RFC 8252），但如果未来改用 Web 类型，必须从代码中移除
- **Token 不入库**：Token 只存在持久层（**Ona** = Project Secret 环境变量 + 容器临时文件 `/tmp/google_token.json`；**build-cli** = `~/.bashrc` env + `/tmp/google_token.json`），绝不进 git / 备份包
- **Refresh Token 不过期**：只要不主动 revoke，refresh token 一直有效。成员离开项目时应 revoke 其 token
- **Revoke 操作**：见上方「手动 Revoke Token」
