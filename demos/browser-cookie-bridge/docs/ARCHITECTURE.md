# 架构与设计决策

## 数据流

```
┌──────────────────────────────────────────────────────────┐
│ Browser (Edge / Chrome)                                  │
│                                                          │
│  ① 用户在浏览器打开目标应用 → SAML SSO → MFA → 登录成功    │
│      cookie 由浏览器持有 (HttpOnly + Secure + SameSite)   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Cookie Bridge Extension (MV3)                       │ │
│  │                                                     │ │
│  │  popup.js     用户配置 receiver URL + token         │ │
│  │       │      触发 syncNow                           │ │
│  │       ▼                                             │ │
│  │  background.js                                      │ │
│  │   - chrome.cookies.getAll(domain)                   │ │
│  │   - chrome.cookies.onChanged 监听                   │ │
│  │   - fetch POST /sync                                │ │
│  └────────┬─────────────────────────────────────────-─┘ │
└───────────┼──────────────────────────────────────────────┘
            │
            │ HTTP POST {service, cookies}
            │ Authorization: Bearer <token>
            │ 仅 127.0.0.1:<port>
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│ cookie_receiver.py (本地 Python HTTP server)              │
│                                                          │
│  ② 验证 Bearer token (secrets.compare_digest)             │
│  ③ 解析 service → 查 config.json 找 output 路径            │
│  ④ 过滤 cookies：只保留 service.domains 列表内的           │
│  ⑤ atomic write JSON 到 ~/.config/<service>/cookies.json  │
│  ⑥ 日志只记 metadata (count, domain, ts)                  │
└────────────┬─────────────────────────────────────────────┘
             │ filesystem (mode 600)
             ▼
┌──────────────────────────────────────────────────────────┐
│ 业务脚本 (examples/gsd_cookie_demo.py 等)                 │
│                                                          │
│  ⑦ 读 ~/.config/<service>/cookies.json                    │
│  ⑧ 注入到 requests.Session.cookies                        │
│  ⑨ 调目标 API (PostProcess / GraphQL / REST)              │
└──────────────────────────────────────────────────────────┘
```

> 上图是 **local transport**（服务 build-cli / WSL runtime）。另有 **gdrive transport** 作第二条出口服务 Ona runtime（扩展加密 → Drive → Ona 容器消费），见下方[决策 12](#决策-12-gdrive-transport--第二条数据出口支持-ona-runtime)。两条 transport 独立成败、互不阻塞。

## 核心设计决策

### 决策 1: 数据出口选 HTTP POST 而非 Native Messaging

**选项**:

A. localhost HTTP POST (选中)
B. Native Messaging (Chrome stdio 协议)
C. 复制到剪贴板
D. 文件下载

**选 A 的理由**:

- 实现简单，全栈（扩展 + receiver）一天能跑通
- 跨平台无差异（Windows/Linux/macOS 一套代码）
- 调试友好（curl 能直接测 receiver）
- token + 127.0.0.1 + Origin 检查三层防护，对社区当前阶段够用

**B 的优势是更合规**：cookie 不走网络栈，扩展跟本地 helper 走 stdin/stdout 进程间通信，没有端口暴露。但代价：

- Windows 要在注册表 `HKCU\Software\Google\Chrome\NativeMessagingHosts\<name>` 注册 native host manifest
- macOS / Linux 要在特定路径放 manifest 文件
- 调试链路长（chrome.runtime.connectNative + helper 进程的 stdio 解析）
- Manifest 路径在企业策略下可能被锁

留作 v0.2 升级路径，写在 SECURITY.md。

### 决策 2: receiver 配置 service 列表，扩展不绑死

**选项**:

A. 扩展 manifest 硬编码 service 列表
B. receiver config.json 维护，扩展 GET /health 拉取 (选中)

**选 B 的理由**:

- 加新 service 只改 receiver config，扩展不需要重新打包
- 扩展只需要知道"有哪些 service 名"，具体 domains 由 receiver 决定，扩展不需要管
- 如果团队多人共用一个扩展但每个人 receiver 配置不同，B 模式自然支持

副作用：扩展 popup 加载时要等一次 /health 请求，UX 略慢。可接受。

### 决策 3: 输出路径跟 frontify_reader.py 对齐

`assets/roche-brand/REFRESH.md` 和 `demos/gslide-authoring/scripts/frontify_reader.py` 已经定下约定：

```
~/.config/frontify/cookies.json
```

新组件沿用：

```
~/.config/<service>/cookies.json
```

这样 frontify 现有脚本不需要改一行代码就能切换到本组件同步的 cookie。

不同的是 schema：

| 旧 schema (frontify) | 新 schema (本组件) |
|---|---|
| `{name: value}` | `{_meta: {...}, cookies: [{name, value, domain, path, secure, httpOnly, sameSite, expires}, ...]}` |

新 schema 更完整，frontify_reader.py 当前只读 name/value，从新 schema 转出来是 trivial 的（`{c.name: c.value for c in data.cookies}`），不破坏向后兼容。

### 决策 4: cookie domain 过滤在 receiver 端做

**选项**:

A. 扩展端过滤（chrome.cookies.getAll 已经按 domain 过滤，相当于已经做了）
B. receiver 端再过滤一次（选中，作为 defense in depth）

**理由**:

扩展可能被改坏（恶意更新或本地代码篡改），把不该传的域 cookie 也推过来。receiver 按 config.json 的 `domains` 列表二次过滤，是双层防护。日志里也会提示 `got N cookies but none match allowed domains`，便于排查配置错误。

### 决策 5: token 默认不落盘 + 持久化是 user-opt-in

**选项**:

A. token 持久化到磁盘文件，receiver 重启复用 (UX 好)
B. token 每次 receiver 启动重新生成 (选中作为 cookie_receiver.py 默认行为)
C. wrapper 脚本帮用户持久化到 ~/.config/cookie-bridge/env，default 关，user-opt-in（补充选项，**当前推荐入口**）

**选项 B 的理由**:

token 不落盘 = token 泄漏窗口跟 receiver 进程生命周期绑定。重启 receiver 自动失效。

**实际运行后引入选项 C 的理由**:

每次重启都要去 popup 里改 URL+token 体验很差，user 反复抱怨。compromise 是 wrapper `receiver/start.sh`：第一次跑生成 PORT+TOKEN 写到 `~/.config/cookie-bridge/env` (mode 600)，之后每次启动都读同一份。Trade-off：

| | B（默认 cookie_receiver.py） | C（start.sh wrapper） |
|---|---|---|
| 进程死后凭据失效 | ✓ | ✗（env 文件留着）|
| 同机其他进程能读 token | ✗（在内存）| △（mode 600，仅 owner 可读，OS 用户被攻陷才暴露）|
| popup 配一次永久不改 | ✗（每次重启都要改）| ✓ |
| 文件进 git 风险 | 不适用 | 在 ~/.config/，hub repo 之外，不会进 git |

cookie_receiver.py 的 default 仍然是 B（不落盘），保留给"我就要严格不落盘"的用户。**INSTALL.md 推荐入口是 start.sh**——多数用户更在意 UX。

**怀疑 token 泄漏 / 想轮换**：删 `~/.config/cookie-bridge/env` 再跑 start.sh 即重新生成。

### 决策 6: 不做"心跳保活"（已撤销，见决策 11）

**最初决策**：A. 扩展定时调目标域 API / B. 不做 → 选 B。

**最初理由**：扩展替用户后台跟内网应用持续通信，SOC 看流量可能觉得可疑。

**撤销原因**：实际运行后发现 cookie 失效（实测 ~30 分钟 idle timeout）频繁打断 agent 调用——agent 正在跑长任务时 401，用户体验差。重新评估两端：

- **解决问题** vs **SOC 告警风险** —— 前者优先级高
- 真要被 SOC 问，"防止 ServiceNow idle timeout 导致 agent 调用失败" 比"SSO 密码存 Ona Secret 给 Python 用 NTLM"好解释得多
- 不试不知道边界——实测才知道 SOC 阈值

详见决策 11。

### 决策 7: chrome.cookies.getAll 用 `{url}` 模式 + `{domain}` 模式合并

**选项**:

A. 只用 `{domain: "..."}`
B. 只用 `{url: "https://..."}`
C. 两个都跑、按 (name, domain, path) 去重 (选中)

**理由**:

Chrome 130+ 在某些情况下 `{domain}` 模式拿不到 cookie，但 `{url}` 模式能拿到（按 URL 让 Chrome 做完整 RFC cookie matching，包括父域 cookie）。反过来也存在极少数情况：cookie 设的 domain 不是子域而是 substring 匹配，`{url}` 拿不到但 `{domain}` 能拿。两个都跑做并集是 defense in depth，且性能影响可忽略（每个 service 多一次同步 API 调用）。

**重新评估时机**：Chrome cookies API 行为再变（看 Chrome release notes）。

### 决策 8: receiver `/health` 返回 `services_detail` 含 domains

**选项**:

A. `/health` 只返回 service 名字列表
B. `/health` 返回 `services_detail` 带每个 service 的 domains (选中，向后兼容旧字段)

**理由**:

最初版本 `/health` 只返 service 名字，扩展把 domains 当成空数组存到 chrome.storage —— 结果 background.js `chrome.cookies.getAll(domain)` 跑空循环，sync 永远 0 cookies。这是个低估"扩展端需要 domain 信息做 cookie 抓取"的设计错误。

修复后 receiver 返回：

```json
{
  "ok": true,
  "name": "silicon-hitchhiker",                 // receiver 标识（0.3.1+），多 receiver 辨识用
  "services": ["servicenow", "test"],          // 旧字段保留兼容
  "services_detail": {
    "servicenow": {"domains": ["roche.service-now.com"]},
    "test": {"domains": ["example.com"]}
  }
}
```

popup.js 优先用 `services_detail`，缺时降级到旧 `services` 字段（domains 空数组 → background 跑空循环 → cookies=0，但不会报错崩）。

**`name` 字段（0.3.1+）**：receiver 标识，来源优先级 `--name`（start.sh 从 `COOKIE_BRIDGE_RECEIVER_NAME` env 透传）> config 顶层 `"name"` 键 > `socket.gethostname()` 兜底。用途：多容器 VSCode-SSH 各把容器的 36984 转发到不同的 Windows localhost 端口，popup 逐行拉 `/health` 显示「端口 → name」，不用脑记哪个转发端口是哪个容器。`/health` 无认证（同 services/domains），`name` 是非敏感标识——别塞 secret。缺 `name` 的旧 receiver：popup 该行显示 `→ ?`，不影响 sync。

### 决策 9: receiver CORS 加 Access-Control-Allow-Private-Network

**选项**:

A. 不加 (默认)
B. 加 `Access-Control-Allow-Private-Network: true` 到 OPTIONS 响应 (选中)

**理由**:

Chrome 102+ 对 Private Network Access (PNA) 加了限制：`chrome-extension://` (public origin) fetch 到 127.0.0.1 (private IP) 必须在 preflight 响应里包含此 header，否则浏览器直接 block 给 `Failed to fetch`，跟 receiver 通不通无关。这是浏览器层面的安全策略。

**重新评估时机**：Chrome PNA 规则升级（看 chromestatus.com/feature/5436853517811712）。

### 决策 10: popup.html CSP `connect-src` 显式列 127.0.0.1

**选项**:

A. CSP 不写（用 manifest V3 默认 CSP）
B. 写严格 CSP `default-src 'self'; script-src 'self'; style-src 'self'`
C. 同 B 但显式 `connect-src http://127.0.0.1:* http://localhost:*` (选中)

**理由**:

最初写法是 B，结果 popup fetch 到 127.0.0.1 被 CSP 拦（default-src 'self' fallback）。Chrome popup 的 CSP 比 background.js 严，必须显式声明 `connect-src` 才能 fetch 跨 origin。

manifest V3 默认 CSP 不让 inline script 但允许 fetch，写不写都 OK。但显式严格 CSP 更安全（防止以后引入 inline script 之类）。这个决策是"写严格 CSP 但补 connect-src"的折中。

### 决策 11: 做 Keep-alive（撤销决策 6）

**选项**:

A. 不做（决策 6 原选项）
B. 扩展用 `chrome.alarms` 定时 fetch ServiceNow 一个登录用户能 200 的轻量 endpoint 维持 session (选中)

**周期**: **20 分钟**。

**理由**:

ServiceNow 默认 `glide.ui.session_timeout = 30` 分钟。Roche 实例的实际值因 admin 权限不够（普通 SAML 用户读不到 `sys_properties` 表）无法直接验证，但实测旁证支持 30 分钟（用户实际 401 间隔约 30+ 分钟）。

20 vs 25 vs 30 的权衡：

| 周期 | 真 timeout=30 | 真 timeout=25（admin 收紧）| 真 timeout=20 | alarm jitter（1-2min）|
|---|---|---|---|---|
| 30 | 0 buffer，必死 | 必死 | 必死 | 不容忍 |
| 25 | 5min buffer | 0 buffer，险 | 必死 | 边缘 |
| **20** | **10min buffer** | **5min buffer** | **0 buffer** | **容忍** |

20 分钟选择保守对 admin 可能改过的 timeout，且容忍 Chrome MV3 alarm 的 schedule drift。流量代价：~72 次/天/用户 = 跟用户多刷 72 次浏览器标签页同等指纹。

**心跳端点**: `/now/nav/ui/classic/params/target/home_splash.do`

实测在 Roche 实例上，这个 endpoint 普通用户 cookie auth 能 200，且 follow 后最终 URL 仍是它本身（不被踢）。它还是 `servicenow_cookie_demo.py fetch_g_ck()` 用的同一个 endpoint，跨工具复用同一份验证。

**踩坑记录**：第一版 `KEEPALIVE_PATHS = "/stats.do"`（基于"行业惯例"——多数 ServiceNow 集成 Slack/Teams 通知插件都用这个端点 keep-alive）。Roche 实例普通用户访问 `/stats.do` 会走 follow → 200 但 final URL 跳到 `logout_redirect.do?sysparm_url=navpage.do`——服务端用一种 `200 + 跳转回首页` 的方式礼貌拒绝，**单看 status code 看不出失败**。检测逻辑因此从"manual 模式 + 看 status"改成"follow 模式 + 看 final URL 关键字"（`logout_redirect` / `/login.do` / `saml` 等）。

教训：**新 service 加 keep-alive endpoint 前必须在 DevTools console 用 `redirect:"follow"` fetch 一次，确认 final URL 不被踢**，不要假设标准 endpoint 通用。

**触发链**:

```
chrome.alarms 触发 → background.js fetch home_splash.do (credentials: include, redirect: follow)
  → 200 + final URL 仍是 home_splash.do → ServiceNow Set-Cookie 续期 glide_session_store
  → chrome.cookies.onChanged 自动 fire (现有监听)
  → debounce 500ms → sync(service) 推新 cookie 到 receiver
  → ~/.config/servicenow/cookies.json 落盘新 cookie
```

Keep-alive 自己不写文件，借助现有 auto-sync 链路落盘。**所以 keep-alive 必须跟 auto-sync 一起开**（popup 勾 keep-alive 时自动勾 auto-sync）。

**失败处理**:

- `redirect:manual` 模式 fetch，type=opaqueredirect 表示 SAML 已踢人 → cookie 失效 → badge 染红 + popup 显示
- 401 同上
- 200 静默成功（不染绿 badge，避免跟 sync OK 混淆）

**浏览器关闭** → service worker 进程死亡 → alarm 暂停 → 下次浏览器启动时 `chrome.runtime.onStartup` 自动重建 alarm。这是 cookie 模式的根本天花板，cron / 长期无人值守不在本方案目标里。

**重新评估时机**:

- SOC 真的标了流量异常：拿到具体告警内容看是不是频率问题，能调
- 实测发现真实 idle timeout 远小于 20 分钟（如 10 分钟）：把 KEEPALIVE_INTERVAL_MIN 调到 5-7
- ServiceNow 改了 endpoint 路径或行为：换 `KEEPALIVE_PATHS` 配置

### 决策 12: gdrive transport —— 第二条数据出口（支持 Ona runtime）

**背景**：原数据流只有一条出口（扩展 → 127.0.0.1 → WSL receiver），只服务 build-cli / WSL runtime。Ona 容器是隔离 dev container，够不到用户 Windows 上的 localhost receiver，拿不到 cookie。AGENTS.md「hitchhiker runtime 多样化」要求 cookie-bridge 不应只支持一种 runtime。

**决策**：加 **gdrive transport** 作第二条出口——扩展把 cookie 客户端加密后写到用户 My Drive 的 `.cookie-bridge/<service>.enc`，Ona 容器用 `gdrive_cookie_sync.py`（复用 `gw_client` 的 Drive 凭据）读取、解密、落到本机 `~/.config/<service>/cookies.json`，消费后即焚 Drive 密文。

```
                    ┌─[transport: local]─> 127.0.0.1 receiver ─> WSL ~/.config  (决策 1，不变)
[扩展] 抓 cookie ─┤                         失败不阻塞另一路
                    └─[transport: gdrive]> AES-GCM 加密 ─> Drive .cookie-bridge/<service>.enc
                                                                │
                          [Ona] gdrive_cookie_sync.py 读 → 解密 → ~/.config/<service>/cookies.json (mode 600)
                                                                │ 落盘后异步即焚 Drive 密文
                                                业务脚本零改动（同一落盘路径）
```

**关键语义**：local 与 gdrive 是**路由关系不是 failover**——两个不同消费端（WSL runtime / Ona runtime），不能「一个通就 short-circuit」否则另一端饿死。故 per-transport 独立成败、互不阻塞（同时修复了旧扩展「任一目的地失败 = 整体 sync 失败」的根因）。

**local 扇出（0.3.0）**：local 从「单个 receiver」升为「多个 receiver，一份 cookie 并行扇出到全部、各自成败」，共用一个 pin 的 token（`cfg.localReceivers[]` + `cfg.token`）。动机：CD2 按项目开多个 Ona 容器隔离/核算，每容器一个转发端口，一个开发者的身份扇给自己名下全部容器（身份 1→N、不跨人）。gdrive 即焚喂不了多消费者，故多容器走 local 扇出。每个 local POST 带 5s 超时（`AbortSignal.timeout`），接不通快速报错不再永久挂。

**SSOT**：两条 transport 的落盘逻辑（域过滤 + `_meta` + mode 600 + bearer 旁路）共用 `receiver/cookie_sink.py`，不双写。加解密信封是扩展 `background.js`（WebCrypto）与 `receiver/cookie_crypto.py`（cryptography）的共享契约（AES-256-GCM + PBKDF2-SHA256 + 固定 AAD），格式见 `cookie_crypto.py` docstring。

**写入侧鉴权**：扩展走 `chrome.identity.getAuthToken` + **社区共享的 Chrome-Extension OAuth client**（scope `drive.file` 最小权限）。manifest pin `key` 使全员扩展 ID 统一为固定值，一个共享 client 即可服务所有成员（client_id 半公开、非机密，直接内置 manifest；社区成员零 GCP 操作）。实测 Roche EMU 放行。安全面分析见 SECURITY.md「gdrive transport 攻击面」。

**重新评估时机**：① IT Security 要求收紧 cookie 静态落 Drive → 转 RCP Secret Manager + KMS（API GW + Lambda 接管写入）② Drive `drive.file` / chrome.identity 企业策略变化 ③ cookie-bridge 长成共享基础设施，需真审计+rotation → 升级到 Secret Manager。

## 扩展性

### 加新 service

1. 修改 receiver `config.json`：
```json
"services": {
  "confluence": {
    "domains": ["confluence.roche.com"],
    "output": "~/.config/confluence/cookies.json"
  }
}
```

2. 修改扩展 `manifest.json` 的 `host_permissions`：
```json
"host_permissions": [
  "https://confluence.roche.com/*",
  ...
]
```

3. 重启 receiver、reload 扩展、popup 点 ↻ 刷新 service 列表。

无需改任何代码。

### 改数据出口

扩展端只有 `background.js` 的 `sync()` 函数是出口逻辑，把 fetch 换成 `chrome.runtime.sendNativeMessage(...)` 即可切到 Native Messaging。receiver 端独立一个进程，可以保留，或者整个换成 native host 程序。

业务脚本（`examples/`）零改动 —— 它们只读 `~/.config/<service>/cookies.json`。

## 跟其他 demo 的关系

| Demo | 关系 |
|---|---|
| `demos/gslide-authoring/scripts/frontify_reader.py` | 输出路径兼容，可直接用本组件同步的 cookie 替代 F12 手工抠 |
| `demos/servicenow/` | 当前走 Basic Auth + Generic Account，本组件可作为 cookie-based 备用路径（用于不开放 OAuth 的实例） |
| huy30 团队 `scripts/gsd_client.py` (外部 repo) | 当前走 NTLM，可基于 examples/gsd_cookie_demo.py 改成 cookie 路径，前提是 GSD 实测发 session cookie |

## 决策记录索引

| 决策 | 节 | 重新评估时机 |
|---|---|---|
| 数据出口选 HTTP POST | 决策 1 | 当 IT Security 要求消除 localhost 端口风险时 |
| Service 列表 receiver 维护 | 决策 2 | 当扩展上架企业 store 不能轻易改时 |
| 输出路径 ~/.config/<service>/ | 决策 3 | 暂不评估，约定已稳定 |
| Domain 二次过滤 | 决策 4 | 暂不评估 |
| Token 默认不落盘 + 持久化 wrapper opt-in | 决策 5 | wrapper trade-off 失效（如 mode 600 被绕过 / OS 用户被攻陷成常态）|
| 不做心跳保活（已撤销） | 决策 6 | 已被决策 11 撤销 |
| chrome.cookies.getAll url + domain 双查 | 决策 7 | Chrome cookies API 行为再变 |
| /health 返回 services_detail | 决策 8 | 暂不评估 |
| CORS 加 Allow-Private-Network | 决策 9 | Chrome PNA 规则升级 |
| popup CSP connect-src 显式列 127.0.0.1 | 决策 10 | manifest V3 CSP 默认行为变化 |
| Keep-alive (20min, home_splash.do) | 决策 11 | SOC 标流量 / 实测 timeout 远小于 20 / endpoint 变更 |
| gdrive transport（第二出口，支持 Ona） | 决策 12 | IT Security 收紧静态落 Drive / chrome.identity·drive.file 策略变 / 需升级 Secret Manager |
