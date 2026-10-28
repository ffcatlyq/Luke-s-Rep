# Browser Cookie Bridge

通用基础设施：把"用户浏览器里 SAML SSO 登录后的 session cookie"自动同步到本地配置文件，让 Python 业务脚本零凭据落盘地复用浏览器认证态。

**支持浏览器**：Chrome（首选）。Edge 也能跑（同 Chromium 内核）。Firefox v0.5+。

替代两种现状：

- **F12 手工抠 cookie**（如 `assets/roche-brand/REFRESH.md` 的 Frontify 流程）—— 不可持续，用户会偷懒、会忘
- **SSO 域账号密码存 secret**（如 huy30 团队的 GSD 当前方案）—— blast radius 是整个 SSO 域，绕过 MFA / Conditional Access

## 架构

两条数据出口（transport），按 runtime 选，可同时开、独立成败：

```
[Edge / Chrome (用户已 SSO 登录)]
      │  chrome.cookies.getAll(domain)
      ▼
[扩展 (Manifest V3)]
      │
      ├──[local]── HTTP POST + Bearer ──> [cookie_receiver.py 127.0.0.1] ──┐
      │                                                                      │
      └──[gdrive]─ AES-GCM 加密 ──> [Drive .cookie-bridge/<svc>.enc]         │
                                          │ [Ona] gdrive_cookie_sync.py 读+解密+即焚
                                          ▼                                  ▼
                              写 ~/.config/<service>/cookies.json (mode 600)
                                          │
                                          ▼
                  [业务脚本：requests.Session() with cookies → 调目标 API]
```

- **local**（build-cli 本地，或 VSCode-SSH 连 Ona）：扩展 → `127.0.0.1` receiver → `~/.config`。可配**多个** receiver，一份 cookie 并行扇出到全部（多容器隔离开发用），共用一个 token
- **gdrive**（纯浏览器用 Ona、无 SSH 隧道时）：扩展加密 → Google Drive → Ona 容器消费端落盘

两条落盘到同一路径（业务脚本零改动），是路由不是 failover。原理见 [ARCHITECTURE.md 决策 12](docs/ARCHITECTURE.md)。

## 快速开始

> 下面是 **local transport**（build-cli 本地，或 VSCode-SSH 连 Ona——VSCode 把容器端口转发到 Windows localhost，浏览器直连容器 receiver）。**纯浏览器**用 Ona（无 SSH 隧道）走 **gdrive transport**——见 [INSTALL.md § gdrive transport](docs/INSTALL.md#gdrive-transportona-runtime让-ona-容器拿-cookie)。

### 1. 起 receiver

```bash
cd demos/browser-cookie-bridge/receiver
cp config.example.json config.json
# 按需编辑 config.json 加目标 service

python3 cookie_receiver.py --config config.json
```

启动后会打印 token 和端口，类似：

```
[bridge] listening on http://127.0.0.1:51343
[bridge] name: silicon-hitchhiker
[bridge] token: 7xK3pQ_aB...（复制此值到扩展 popup）
[bridge] services: gsd, frontify, servicenow
```

> 想要固定端口/token + 常驻，用 `./start.sh`（持久化 wrapper）而非直接跑脚本。**Ona 容器**可用 automations 托管 receiver（`.ona/automations.yaml` 已注册 `cookie-bridge` service，`manual` opt-in——面板勾开或 `gitpod automations service start cookie-bridge`，固定端口 + 走 Ona Secret 的共享 token）——见 [INSTALL.md §1.6](docs/INSTALL.md#16-ona-容器自动起-receiverautomations)。

### 2. 装扩展

Chrome 地址栏 `chrome://extensions/` → 右上角打开 **Developer mode** → 顶部 **Load unpacked** → 选 `demos/browser-cookie-bridge/extension/` 目录。

WSL2 路径在 Windows Chrome 里看是 `\\wsl$\Ubuntu-24.04\home\<user>\projects\silicon-hitchhiker\demos\browser-cookie-bridge\extension\`。如果 Chrome 加载这个路径失败（少数情况下 NTFS 跨 9P 协议处理 PNG 异常），把 `extension/` 整个复制到 Windows 本地（如 `C:\tools\cookie-bridge\`）再 Load unpacked。

### 3. 配置扩展

点扩展图标打开 popup：

- **Token**：粘贴终端打印的 token（所有 receiver 共用同一个）
- **Local receivers**：点 **+ Add** 加一行，填 `http://127.0.0.1:<port>`（终端打印的端口）。build-cli 本地就是 WSL2 localhost 自动转发；VSCode-SSH 连 Ona 则 VSCode 把容器端口转发到 Windows。多个容器就加多行、各填各的端口，一份 cookie 扇出到全部（每行左侧勾选控制启用）
- 点 **↻**（Service 旁）从 receiver 拉 service 列表 → **Service** 选 `servicenow`（或 `test` 走公开域 smoke test）。↻ 后每行 receiver 右侧显示 `→ <name>`，多容器据此认哪个转发端口是哪个容器
- Auto-sync on cookie change：按需开启
- 点 "Save" 保存配置

### 4. 同步 cookie

浏览器内登录目标应用（走完整 SAML SSO + MFA），然后：

- 手动模式：点扩展 popup 的 "Sync Now"
- 自动模式：开了 auto-sync 就不用管，cookie 一变化自动推送

cookie 落到 config 里配置的路径（默认 `~/.config/<service>/cookies.json`，mode 600）。

### 5. 业务脚本用 cookie

`examples/servicenow_cookie_demo.py` 是开箱即用的最小例子：

```bash
cd demos/browser-cookie-bridge/examples
pip install requests
python3 servicenow_cookie_demo.py --whoami         # 验证 cookie 身份
python3 servicenow_cookie_demo.py                  # 默认查 1 条 incident
```

WSL2 不通 ServiceNow（DNS 解析或 TCP 超时）时用 fallback 走 Windows 侧 curl：

```bash
./examples/servicenow_via_windows.sh                                # whoami
./examples/servicenow_via_windows.sh "/api/now/table/incident?sysparm_limit=3"
```

业务脚本核心 5 行：

```python
import json, requests
from pathlib import Path
data = json.loads(Path("~/.config/servicenow/cookies.json").expanduser().read_text())
session = requests.Session()
for c in data["cookies"]:
    session.cookies.set(c["name"], c["value"], domain=c["domain"].lstrip("."), path=c["path"])

resp = session.get("https://roche.service-now.com/api/now/table/incident", params={"sysparm_limit": 1})
```

## 复用到新应用

一条命令搞定（替代手工改 5 处）：

```bash
./scripts/add-service.sh confluence wiki.roche.com
```

脚本会：自动改 manifest.json + receiver/config.json + config.example.json，cp 到 Windows extension 目录，重启 receiver，最后跑 [probe-service.sh](scripts/probe-service.sh) 探测目标域属于哪类协议（ServiceNow / SailPoint IIQ / Atlassian / SharePoint / Bearer-localStorage / 未知），输出对应 [RECIPES.md](docs/RECIPES.md) 锚点指向 client 模板代码。

完成后还要做的两步：

1. `chrome://extensions` → Roche Cookie Bridge → 点刷新（让 host_permissions 生效）
2. 浏览器登录目标站 → popup 选 service → Sync Now

`host_permissions` 不走通配符，每个新域都要明确授权 —— 这是设计上的安全约束。

> **重要**：cookie 抓取通了 ≠ 业务能跑。每个应用的 CSRF / token / API 协议不同，加完 service 后**还要写业务 client**——参考 [RECIPES.md](docs/RECIPES.md) 各协议类的模板代码（servicenow.py / sailpoint-iiq.py 已有完整实现可 copy）。如果 probe 识别为 `bearer-localstorage`（如 nihsc 类站），cookie-bridge 不适用，直接走 localStorage token 路径。

## 文档

| 文档 | 内容 |
|---|---|
| [docs/INSTALL.md](docs/INSTALL.md) | 详细安装步骤，含企业策略检查 |
| [docs/SECURITY.md](docs/SECURITY.md) | 威胁模型、攻击面分析、缓解措施 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 数据流、设计决策记录 |
| [docs/RECIPES.md](docs/RECIPES.md) | 业务 client 模板（servicenow / sailpoint-iiq / atlassian / sharepoint / generic-jsessionid / bearer-localstorage 6 类） |

## 限制

- **企业 Edge/Chrome 策略可能禁 sideload 扩展**。装之前先查 `edge://policy/`，看 `ExtensionInstallBlocklist`、`DeveloperToolsAvailability` 是否生效。
- **目标应用必须有 session cookie 模型**。纯 NTLM 应用（如部分老 IIS）登录后不发 cookie，本方案不适用。
- **cookie 会过期**。短则几小时长则几天，过期后用户要重新走一次浏览器登录。
- **Non-repudiation 没解决**。审计日志看到的还是登录用户的身份，分不清是 AI 自动调还是人手动调。需要在业务脚本层加 audit log 区分。

## 后续升级路径（v0.2+）

- HTTP POST → Native Messaging（消除 localhost 端口风险）
- cookie 不落盘，receiver 直接 IPC 转发给业务脚本
- shared token → 短期 JWT
- 适配 Firefox
