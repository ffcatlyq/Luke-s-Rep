# 威胁模型与安全注意

本文档列明本组件的攻击面、威胁假设、缓解措施、未解决的风险。**部署前请通读**。

## 我们假设什么是安全的

| 边界 | 假设 |
|---|---|
| 浏览器进程 | 浏览器本身没被恶意进程注入，渲染进程沙箱有效 |
| OS 文件权限 | mode 600 文件其他用户读不到（同用户进程能读，这是 Linux/Windows OS 模型决定的） |
| Loopback 接口 | 127.0.0.1 流量不出本机网卡（OS 路由保证） |
| Edge / Chrome 扩展 store 不被劫持 | 你装的扩展确实是这个 repo 的代码，没被中间人替换 |
| 用户机器 | 没被 root / Administrator 级别攻击者控制 |

如果上述任一假设被打破，本组件提供的保护几乎全部失效。

## 攻击面

### 1. 浏览器扩展本身

扩展持有 `cookies` API + `host_permissions` 列表里所有域的读权限。一旦扩展代码被替换（git 仓库被入侵、依赖污染、本地文件被篡改），攻击者可以：

- 读所有 host_permissions 列表里域的 cookie
- 把 cookie 推到任意 URL（不一定是 127.0.0.1）

**缓解**:
- `host_permissions` 用具体域名而非 `<all_urls>` —— 限制 cookie 读取范围
- 扩展代码 ~300 行，全部 review-able；建议 git 提交后定期 diff
- 不引入第三方 npm 依赖（当前实现 0 依赖）—— 消除供应链攻击面

**未解决**:
- 浏览器扩展更新机制（如果通过企业 store 上架）可能引入恶意更新
- popup 里的 token 存在 `chrome.storage.local`，扩展进程能读 —— 扩展被劫持 = token 泄漏

### 2. Receiver HTTP 端口

receiver bind `127.0.0.1:<port>`，理论上只有同机进程能连。但同机其他用户进程也能连。

**缓解**:
- Bearer token 认证（32 字节 base64url，通过 `secrets.compare_digest` 比对避免 timing attack）
- token 起法两种：`cookie_receiver.py` 直跑=每次随机、不落盘；`start.sh`=持久化 PORT+TOKEN 到 `~/.config/cookie-bridge/env`（mode 600、不进 git）跨重启不变。多容器扇出时用 `COOKIE_BRIDGE_RECEIVER_TOKEN` env 让多个 receiver 共享同一 token——**仅限同一个人名下的容器**（blast radius 不跨人；跨人共享 token = 越权，禁止）
- Origin 检查：`Access-Control-Allow-Origin` 只放给 `chrome-extension://*` / `moz-extension://*`（防同机其他网页 fetch）

**未解决**:
- 同机其他用户能 `netstat -an` 看到端口号，然后暴力试 token —— 32 字节空间足够大，但不是无懈可击
- 同用户另一进程能 `lsof` 拿到端口和监听进程，理论上能 ptrace 读 token —— 这种威胁场景下整套都不安全
- token 不过期，receiver 跑多久 token 就有效多久

### 3. Cookie 文件

落到 `~/.config/<service>/cookies.json`，mode 600。

**缓解**:
- mode 600 防其他用户读
- 原子写（tmp + rename）防读到半截

**未解决**:
- 同用户进程都能读，包括其他 AI agent（Claude Code 自己的进程也能 `cat` 这个文件）
- 进程崩溃 dump、OS swap 文件可能含 cookie 内容
- 备份系统（Time Machine、Windows File History）可能把 cookie 文件备份到不受控的位置

### 4. Cookie 的 blast radius

对比 SSO 密码方案的 blast radius 大幅减小，但不是零：

| 方案 | 凭据泄漏后影响 |
|---|---|
| SSO 密码 | 整个 Roche 内网所有 SSO 应用 + 90 天有效期 |
| 浏览器 cookie | 单个应用 + 几小时到几天 expiry |

cookie 泄漏依然能让攻击者：
- 模拟你在该应用的所有操作（包括 GSD approve / reject、ServiceNow 提单、Confluence 写入）
- 看到该应用的所有数据

### 5. gdrive transport 攻击面（Drive 静态密文）

gdrive transport（ARCHITECTURE 决策 12）让 cookie 多走一趟 Google Drive，比「内存 token + 本地文件」多一个静态环节。诚实列出新增面 + 缓解：

| 维度 | 设计 | 守住什么 |
|------|------|---------|
| 静态加密 | 扩展端 **AES-256-GCM** 加密后才上 Drive；passphrase 两端各配一份，**永不进 Drive / 永不进 git** | cookie 等同密码绝不明文。文件误 share / Google admin 读到，得到的是密文 |
| 最小权限 | OAuth scope 用 `drive.file`（仅扩展自己创建的文件，非全 `drive`）；文件仅 owner，不 share；固定隐藏路径 `.cookie-bridge/<service>.enc` | 不引入新可达面 |
| 异步即焚 | Ona 消费落盘成功后立即删 Drive 密文；`--watch` 模式附 TTL 孤儿清理 backstop（容器 ephemeral 时密文不堆积） | 暴露窗口缩到「一次传输」 |
| blast radius 不变 | 仍单应用、短期 cookie（同上节表） | 与 local transport 一致 |
| 落盘一致 | 终点仍 `~/.config/<service>/cookies.json` mode 600（共用 `cookie_sink.py`） | 业务脚本零改动 |
| passphrase mismatch | 两端口令不一致 → GCM auth tag 校验失败 → 消费端**明确报 `passphrase mismatch`**（不静默、不即焚，留待改对重试） | 避免 opaque 失败把人引向错误排查方向 |

**新增攻击面的本质**：用「可达性」（让 Ona runtime 也能拿 cookie）换「cookie 多一个静态环节」。缓解靠加密 + 即焚 + owner-only + drive.file 最小权限。这是与决策 1（HTTP POST vs Native Messaging）同类的权衡。

**passphrase 分发铁律**：用户自己设、两端手动各配一次（扩展 popup 存 chrome.storage.local / Ona 存 env var `COOKIE_BRIDGE_PASSPHRASE`）。**绝不经聊天工具传**（见下「不要做的事」）。

**升级路径**：若要消除 cookie 静态落 Drive，正解是 RCP Secret Manager + KMS（KMS 托管加密消手配 passphrase、CloudTrail 补 non-repudiation）。当下卡在写入侧——浏览器扩展只有 Google 有 chrome 原生鉴权路径；Secret Manager 需 API Gateway + Lambda 接管写入。规模长大再上。

## Keep-alive 流量与 SOC 风险

启用 keep-alive（决策 11）后扩展每 20 分钟向 ServiceNow 发一个 GET `/now/nav/ui/classic/params/target/home_splash.do`。这一节专门讨论这个流量被 Roche SOC 标记的风险与应对。

**流量画像**

| 维度 | 值 |
|---|---|
| 频率 | 每 20 分钟一次（实际有 chrome.alarms jitter，可能 21-22 分钟）|
| 端点 | `https://roche.service-now.com/now/nav/ui/classic/params/target/home_splash.do` |
| Method | GET |
| User-Agent | 浏览器原生 UA（非 Python requests 之类）|
| Cookie | 浏览器自动带（cookie jar）|
| Referer / Sec-Fetch-* | 浏览器自动填 |
| 总量 | ~72 次/天/用户（仅在浏览器开着时）|

**跟"用户保持 ServiceNow 标签页打开"的差异**

| 维度 | 用户保持 tab 打开 | Keep-alive 扩展 |
|---|---|---|
| 流量来源 | Edge/Chrome 进程 | Edge/Chrome 进程（扩展跑在浏览器内）|
| 频率 | 每次用户切到该 tab + ServiceNow 自身 polling | 每 20 分钟固定 |
| 流量指纹 | 完整 UA / Referer / Sec-Fetch-* | 同左 |
| 端点 | 多种 UI / API endpoint | 仅 home_splash.do |
| ServiceNow 服务端日志 | 走标准 session 流量 | 走标准 session 流量 |

**关键**：从 Roche SOC 流量分析视角，扩展的 keep-alive 跟"用户主动保持 ServiceNow 标签页打开"在 TLS 流量层面**几乎无法区分**——都是浏览器进程发出的、带 cookie 的、用户身份的 HTTPS 请求。SOC 的网络层告警通常关注：

- 异常源 IP（不是企业网络段）
- 异常目标（不在白名单的外部域）
- 异常协议（非 HTTPS、明文凭据）
- 异常凭据用法（密码暴力破解、token 异地）

`/now/nav/ui/classic/params/target/home_splash.do` 是 ServiceNow 用户登录后的标准入口页（"my home" 一类），是用户在浏览器内最高频访问的 endpoint 之一，**单看流量不构成异常信号**。

**真被 SOC 问到怎么解释**

模板回复：

> 这是浏览器扩展 Cookie Bridge 的 session keep-alive 行为。扩展每 20 分钟 GET `home_splash.do` 防止 ServiceNow 因 idle timeout 失效，导致本地 AI agent 调用 ServiceNow API 时 401。背景：用户的 AI agent 跑长任务时常碰到 cookie 失效；本方案是替代"把 SSO 域账号密码存 Ona Project Secret 给 Python NTLM 用"这种更高风险做法的合规化升级。详见 `demos/browser-cookie-bridge/docs/ARCHITECTURE.md` 决策 11，频率和端点选择有明确的工程理由。

这个回答能站住的前提：

1. 决策 11 文档已 commit 在内部 repo（已做）
2. 频率 20 分钟在 ServiceNow idle timeout 范围内合理（已论证）
3. 替代方案（SSO 密码 NTLM）的风险更高，能列出具体（六维度风险分析见 [demos/agent-auth-patterns/](../../agent-auth-patterns/)）

**不要做的事**

- 不要为了"显得正常"故意加随机 jitter / 模拟用户操作模式 —— 反而可疑
- 不要 keep-alive 频率 < 5 分钟 —— 真异常
- 不要心跳到 `/api/now/*` 这类业务 API（既需要 g_ck，又看起来像 service 调用）；用 UI 入口页（`home_splash.do` 一类）流量指纹更接近真实用户
- 不要在浏览器关了之后用 receiver 替代心跳 —— 没意义（JSESSIONID 已丢）且制造真异常

**重新评估时机**

- SOC 实际告警：拿告警内容看具体阈值，调频率
- 实测 idle timeout 远小于 20 分钟：调到 5-7 分钟（仍合理）
- 多个 service 同时启用 keep-alive：评估总流量是否触发 cumulative 告警

## Non-repudiation 没解决

最重要的未解决问题：**审计层面分不清是 AI 还是人**。

GSD 审批日志、ServiceNow 工单变更日志、Confluence 编辑历史，看到的都是登录用户的身份。本方案让 AI 用你的 cookie 操作目标应用 —— 从应用日志视角，AI 的操作和你亲自的操作不可区分。

**应对**（不是技术层面的，是流程层面的）:

- **业务脚本必须自己加 audit log**：每次调写操作前写一条 `docs/logs/<date>.md`，记录调用方（AI agent 名 / 模型版本 / prompt SHA）、目标 endpoint、payload 摘要、结果
- **写操作必须人工 confirm**：AI 准备 payload，最终执行（点击 approve、提交工单）由人在浏览器内手动完成
- **服务账号才是终极解**：申请专门的 integration user，AI 走服务账号，人走个人账号，应用日志能区分。本方案不替代服务账号，只替代"AI 用人 SSO 密码"这种最差实践

## 不要做的事

- 不要用通配符 `host_permissions: ["<all_urls>"]`
- 不要把 token 通过聊天工具（Slack/Teams/微信）发给同事 —— token 重启 receiver 就失效，但泄漏期间是开放的
- 不要在多人共享的机器（共用账号）上跑 receiver
- 不要把 `~/.config/<service>/cookies.json` 放进 git
- 不要把 `--host 0.0.0.0` 用于真实场景（除非你明确知道在做什么并配套了防火墙规则）
- 不要把 receiver 跑成 systemd service / Windows service 长期常驻 —— token 长期有效是新攻击面

## 跟现有方案对比

| 维度 | SSO 密码（GSD 当前）| F12 手工 cookie（branding 当前）| 本方案 |
|---|---|---|---|
| 凭据形式 | 长期密码 | 短期 cookie | 短期 cookie |
| Blast radius | 全 SSO 域 | 单应用 | 单应用 |
| MFA / CA | 绕过 | 经过 | 经过 |
| 自动化能力 | 高 | 低（手抠）| 中（自动同步但要保持登录）|
| Token 落盘 | env var | 文件 mode 600 | 文件 mode 600 + receiver 内存 token |
| 新增常驻组件 | 无 | 无 | 浏览器扩展 + 本地端口 |
| Non-repudiation | 没解决 | 没解决 | 没解决（流程层解）|

本方案对 SSO 密码方案是**不同维度的全面改善**，对 F12 手工方案是**用户体验改善 + 引入新攻击面**的折中。

## 升级方向

各项升级要解决的具体问题：

| 升级 | 解决 |
|---|---|
| HTTP POST → Native Messaging | 消除 localhost 端口 + 同机进程蹭风险 |
| Cookie 不落盘 + IPC 直传业务脚本 | 消除文件被同用户进程读风险 |
| Token → 短期 JWT | 消除 token 长期有效风险 |
| 浏览器扩展上架企业 store | 消除自定义扩展被劫持风险 |
| 服务账号 + OAuth Client Credentials | 解决 non-repudiation |

每一项都对应一个具体威胁。优先级根据你的威胁模型自己排。

## 报告问题

发现安全问题不要走 GitHub issue（公开），联系 huy30 团队或 hub repo 维护者，私下沟通修复方案。
