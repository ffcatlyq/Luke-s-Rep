# Google Workspace 基建配置指南

打通 `meeting-prep` / `google-workspace` 技能所需的一次性授权。基建（脚本、依赖、gitignore 兜底）已搭好，**只差 OAuth 凭证与授权这一步——需你手动完成**（凭证不能入库，也不能由智能体代办）。

## 现状

| 组件 | 状态 |
|---|---|
| 脚本（`gw_client.py` / `find-meeting.py` / `build-context.py` 等） | ✅ 已就位 `demos/google-workspace/`、`demos/meeting-transcribe/` |
| Python 依赖安装 | ✅ 环境启动自动装（`.ona/automations.yaml` → `installGoogleWorkspaceDeps`） |
| OAuth 凭证 + 授权 | ⏳ **待你手动配置（本文档）** |

## 前置：确认依赖已装

```bash
python3 -c "import googleapiclient, google.oauth2, google_auth_oauthlib; print('OK')"
```
报 `ModuleNotFoundError` 就手动跑一次安装任务：
```bash
pip3 install --break-system-packages -r demos/google-workspace/requirements.txt
```

## 步骤 1：拿 OAuth Client 凭证（GCP Console）

1. 打开 [GCP Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)（选你/团队的 GCP 项目）。
2. 用已有的 **Desktop** 类型 OAuth Client，或 **Create Credentials → OAuth client ID → Application type: Desktop app**。
3. 创建后 **下载 JSON**，格式应为 `{"installed": {...}}`。
4. 把它放到环境里，命名为 `/tmp/oauth_client.json`（`auth.py` 默认读这个路径）：
   ```bash
   # 本地下载后，通过 VS Code 拖入环境，或直接粘贴内容：
   cat > /tmp/oauth_client.json   # 粘贴 JSON 内容，Ctrl-D 结束
   ```

> Desktop 类型的 client_secret 按 [RFC 8252 §8.5](https://datatracker.ietf.org/doc/html/rfc8252#section-8.5) 不算机密。即便如此，本仓 `.gitignore` 已兜底 `oauth_client.json` / `google_token.json`，**不要**把凭证 commit 进仓库。

## 步骤 2：Consent Screen 加 scope

技能用到的 scope 以代码为准：`demos/google-workspace/scripts/gw_client.py` 的 `SCOPES` 变量（含 Drive / Docs / Sheets / Gmail / Calendar / Slides / Chat / People 等）。

1. [Google Auth Platform → Data Access](https://console.cloud.google.com/auth/scopes) → **Add or remove scopes**，把 `SCOPES` 里的都加上。
2. 对应 API 需在 [APIs & Services → Library](https://console.cloud.google.com/apis/library) 启用（Calendar API、People API 等）。

> ⚠️ Consent Screen 未加的 scope，授权页会**一直转圈不显示 scope**——不是报错，是 Google 静默拒绝。

## 步骤 3：跑 auth.py 授权

`auth.py` 在环境内起本地 HTTP server（端口 19876），VS Code SSH 自动转发到你本地浏览器完成 OAuth。

```bash
cd demos/google-workspace/scripts && python3 auth.py
```
1. 复制打印的 URL，在**本地浏览器**打开。
2. Google consent 页点 **Allow**。
3. 浏览器跳转 `localhost:19876/callback`，脚本自动捕获 token，写入 `/tmp/google_token.json`。

## 步骤 4：验证打通

```bash
# 列最近日历事件（验证 Calendar + 授权）
cd demos/meeting-transcribe/scripts && python3 find-meeting.py --help
# 实际拉某会议上下文（换成真实 event id 或标题）
python3 build-context.py --help
```
能正常调用即基建打通，`meeting-prep` 技能可用。

## 常见问题

| 症状 | 原因 | 处理 |
|---|---|---|
| consent 页卡住转圈 | callback 端口无监听 / scope 未注册 | 确认 `auth.py` 在运行且端口 19876 已转发；确认 Consent Screen 加了 scope |
| 浏览器跳转后空白 | VS Code 未自动转发端口 | VS Code 底部 Ports 面板手动加 19876 |
| `invalid_scope` | 环境变量旧 token 覆盖新 token | 重新跑 `auth.py`；或临时 `GOOGLE_TOKEN_JSON="" python3 script.py` |
| `ModuleNotFoundError` | 依赖未装 | 跑前置的 `pip3 install ...` |

## 合规提醒

- OAuth 凭证与 token **绝不入库**（gitignore 已兜底，但你手动放置时也要留意）。
- Workspace 数据（邮件/日历/文档）含敏感信息，按数据分级处理；会前 brief 等产出若含 C3/C4 数据，标注"内部，勿外传"。
- 详细管理员指南见 `demos/google-workspace/docs/admin-guide.md`。
