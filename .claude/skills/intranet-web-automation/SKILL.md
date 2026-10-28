---
name: intranet-web-automation
description: >
  给罗氏内网 Web 系统(GSD 项目申请、审批、各类 apps.*.roche.com 应用)做浏览器自动化：
  监控某状态、到点自动提交/操作、轮询等待前置完成。核心手法是"在页面自身控制台里跑 JS，
  复用浏览器已有的 SSO/NTLM 登录态"——绕开 cookie、端口转发、密码等一切坑。
  Use when the user wants to auto-submit / monitor / poll / retry an action on a
  Roche intranet web app (GSD, apps.sha.roche.com, 内网 SSO 系统), especially
  "等前置完成自动提交""每 N 分钟重试""监控某状态变化就通知/操作".
  Triggers on "GSD", "自动提交", "内网系统自动化", "轮询提交", "等审批完成自动",
  "apps.sha.roche.com", "监控状态自动操作", "浏览器控制台脚本自动化".
---

# 内网 Web 系统浏览器自动化（Intranet Web Automation）

给罗氏内网 Web 应用(GSD 等)做"监控某状态 → 到点自动操作"的自动化。
本 skill 是从一次真实 GSD 全自动提交任务沉淀的——**记录了正确路径，也记录了
所有走过的弯路**，让下次一步到位，不再踩坑。

---

## 0. 一句话结论（最重要，先看这个）

> **罗氏内网系统绝大多数走 Windows 集成认证(NTLM/Kerberos)，不是 cookie。
> 唯一可靠的自动化路径 = 在【页面自身的 F12 控制台】里跑 JS，用页面的
> `fetch(..., {credentials:"include"})` 复用浏览器已有的 SSO 登录态。**

不要碰 cookie 同步、不要碰端口转发、不要交域密码。这些在这次任务里全部失败或被否决，
详见第 4 节踩坑记录。

---

## 1. 决策树：接到"内网系统自动化"需求先走这个

```
需求：监控 X / 到点自动做 Y（内网 Web 系统）
│
├─ 第 0 步【必做】：先定性认证方式，别猜！
│    在目标域发一个请求，看 WWW-Authenticate 响应头：
│      curl -sI <url> 里有 "WWW-Authenticate: Negotiate, NTLM"
│      或浏览器 Network 里请求 401 且带该头
│    → 有 NTLM/Negotiate  = Windows 集成认证 → 直接走【页面内控制台脚本】
│    → 是 Set-Cookie 会话  = 传统 cookie 认证 → cookie 方案才可能可行
│
├─ 用户环境判断：
│    纯浏览器用 Ona / 无本地 VSCode-SSH 端口转发
│    → 容器里的 Python 脚本够不到内网、也复用不了登录态
│    → 放弃"容器里跑脚本"，改"浏览器里跑 JS"
│
└─ 落地：页面内控制台 JS
     · 监控：定时 fetch 只读接口，读状态
     · 操作：调页面自身的 JS 函数 / 模拟点击其按钮
     · 提醒：红横幅 + 标题闪烁 + 系统通知（声音常被浏览器策略挡，别依赖）
```

---

## 2. 标准工作流（页面内控制台脚本）

### 2.1 逆向 API / 函数（在目标页 F12 → Network / Console）

1. **抓只读接口**：在页面操作，Network 里找 `PostProcess` 之类的 XHR。
   GSD 的模式是统一入口 `POST /GSD/main/PostProcess`，body 里
   `{OwnerClass, OPID, Content}` 区分操作。`Get*` 是读，`Save*`/`Submit*` 是写。
2. **抓写操作对应的页面函数**：右键按钮 → 检查，看 `onclick`。
   往往能拿到形如 `SomePage.Save.SubmitXxx()` 的**页面内部函数**——
   **调函数比模拟点击更稳**（不受弹窗动画/渲染时机影响）。
3. **读函数源码定成功判断**：
   `console.log(SomePage.Save.SomeFn.toString())`，看它：
   - 校验逻辑在哪、什么开关控制"只校验 vs 真提交"
   - 提交回调里**成功/失败的判断字段**（这是"成功即停"的锚点）
   - 成功后的副作用（跳转某页 / 弹某 alert）——最硬的成功信号

### 2.2 写监控脚本（只读，先跑通这个）

用 `scripts/monitor_template.js` 改：定时 `fetch` 只读接口读状态，
状态达标就三重提醒。**这一步 100% 安全，务必先验证能正确读出状态再谈自动操作。**

### 2.3 写自动操作脚本（写操作，务必加护栏）

用 `scripts/auto_action_template.js` 改。必须内置：
- **闸门**：`submitted` 布尔，触发前置 true，**杜绝重复执行写操作**
- **成功即停**：多重探测（拦 alert 文案 / 监听页面跳转 / 闸门），命中即 `clearInterval`
- **防假成功**：执行后若又弹校验错误框，判定未成功 → 重置闸门、恢复轮询
- **失败不乱来**：校验没过 / 返回失败 → 停下等人，不盲目重试
- **前置只靠只读判断**：绝不靠"硬点提交撞报错"来判断前置——那会弹报错打扰用户

### 2.4 上线

用户把脚本整段贴进**目标页**控制台。叮嘱：
- 别关标签页（关了脚本就停）；F12 可关
- 登录过期会打印 401，重新登录后重跑
- 手动停：`clearInterval(window.__xxxTimer)`

---

## 3. 提醒手段（实测有效性排序）

| 手段 | 可靠性 | 说明 |
|---|---|---|
| **页面红色横幅** | ★★★ 几乎必成 | `position:fixed;z-index:2147483647` 插 body 顶部 |
| **标题闪烁** | ★★★ | `document.title` 定时切换，切到别的标签也能余光看到 |
| **系统通知** | ★★☆ 需授权一次 | `Notification.requestPermission()`，用户在别的窗口也能收到 |
| **声音 Beep** | ★ 常失败 | 企业 Chrome 音频自动播放策略常挡；**不要依赖** |

到点提醒 = 红横幅 + 标题闪烁 + 系统通知 三管齐下，任一场景都收得到。

---

## 4. 踩坑记录（这次真实走过的弯路，别重蹈覆辙）

> 这一节是本 skill 最大价值。以下路径**全部试过并失败/被否**，写清是为了下次直接跳过。

### ❌ 弯路 1：cookie 同步（cookie bridge）——根本性不适用
- 试图用浏览器扩展把 GSD cookie 同步到容器，让 Python 脚本带 cookie 调 API。
- **失败**：GSD 是 IIS + Windows 集成认证，返回 `401.2` + `WWW-Authenticate: Negotiate, NTLM`。
  cookie 再全也被挡在 IIS 认证层之外（`document.cookie` 还读不到 HttpOnly 会话 cookie）。
- **教训**：**接需求第一步就该发个请求看 `WWW-Authenticate` 头定性认证**，
  10 秒能省几小时。NTLM/Negotiate = cookie 路线直接出局。

### ❌ 弯路 2：本地 receiver + 端口转发
- 想让浏览器扩展把 cookie 推到容器里 `127.0.0.1` 的 receiver。
- **失败**：①用户纯浏览器用 Ona，无 VSCode-SSH 端口转发，Windows 的 127.0.0.1 ≠ 容器的 127.0.0.1；
  ②组织策略限制端口对外（`port access restricted to organization`）。
- **教训**：判断用户怎么连环境。纯浏览器/网页版 = 容器端口用户够不到。

### ❌ 弯路 3：gdrive transport（扩展加密传 Drive → 容器解密）
- 绕开端口，改用 Google Drive 中转 cookie。
- **失败**：扩展打包版 manifest 的 OAuth `client_id` 是占位符，报 `bad client id`。
  且**就算通了，cookie 对 NTLM 系统也没用**（弯路 1 的根因没解决）。
- **教训**：别在错误的大方向上优化细节。

### ❌ 弯路 4：手动导出 cookie（document.cookie / chrome.cookies）
- 直接从页面/扩展导出 cookie 贴进容器。
- **失败**：`document.cookie` 读不到 HttpOnly；`chrome.cookies` 抓到的是 SSO 网关
  (`PF`=PingFederate 等)cookie，不是应用会话；且拿去请求仍 `401.2`（NTLM）。
- **教训**：同弯路 1。

### ❌ 弯路 5：Playwright 本机方案
- 方向对了（本机浏览器复用登录态），但要求用户本机装 Python + Playwright。
- **失败**：用户 Windows **没装 Python**（`python --version` 无输出），且 PowerShell 闪退。
- **教训**：**别假设用户本机有开发环境**。业务用户电脑常无 Python。
  → 最终改用**零安装**的"页面内控制台 JS"，一举绕开所有环境依赖。

### ✅ 正解：页面内控制台 JS
- 在 GSD 页面 F12 控制台跑 JS，`fetch(...,{credentials:"include"})` 自动带 NTLM 登录态。
- 一次成功读出状态。零安装、零 cookie、零端口、零密码。

---

## 5. 合规护栏（写操作类自动化必守）

内网系统的"提交/审批/确认"往往有**法律/合规分量**，不是普通按钮。

1. **确认弹窗有分量**：如 GSD 提交前的"本人已充分阅读并理解…合规要求"。
   自动点它 = **以用户名义做出合规声明**。
2. **写操作前必须显式知情授权**：动手做"自动提交/审批"前，
   在正文里讲清"脚本会代你做出 XX 声明/操作，不可逆"，
   拿到用户**明确授权**再上 armed 模式。默认应是 dry-run（只监控只提醒）。
3. **只做一次、成功即停**：写操作绝不重复执行（防重复建单/重复审批）。
4. **不替用户判断业务规则**：脚本只做"到点执行用户已决定的操作"，
   不替用户决定是否该提交、是否合规。
5. **不碰密码/凭据**：只复用浏览器已有登录态，绝不索取或存储域密码、cookie。

对齐仓库 `compliance/guardrails.md`（数据分级、不与处方挂钩等）。

---

## 6. 文件

| 文件 | 用途 |
|---|---|
| `scripts/monitor_template.js` | 监控模板：定时读状态 + 三重提醒（只读，安全） |
| `scripts/auto_action_template.js` | 自动操作模板：监控 + 到点执行写操作 + 全套护栏 |

用法：把模板里的 `【占位】`（接口路径、OwnerClass/OPID、donee/记录 id、
提交函数、确认按钮选择器、成功/错误判断）按目标系统实际值替换。
逆向方法见第 2.1 节。

---

## 7. 快速检查清单（每次任务自查）

- [ ] 已发请求看 `WWW-Authenticate` 头，定性了认证方式？
- [ ] NTLM/Negotiate → 走页面内控制台 JS，没在 cookie/端口上浪费时间？
- [ ] 监控（只读）先跑通、正确读出状态，再谈自动操作？
- [ ] 写操作前，把不可逆性讲清并拿到用户明确授权？
- [ ] 脚本有：闸门防重复、成功即停、防假成功、失败不重试？
- [ ] 前置判断只靠只读接口，不靠硬撞报错？
- [ ] 提醒用红横幅+标题+通知，没依赖声音？
- [ ] 交付时叮嘱：别关标签页、登录过期重跑、手动停命令？
