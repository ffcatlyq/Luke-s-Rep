# 安装与排错指南

> **两条transport，按你的runtime选**（可同时开，互不阻塞）：
> - **local**（build-cli本地，或VSCode-SSH连Ona）→ 下面「5步安装」。扩展 → `127.0.0.1:36984` receiver → `~/.config`。receiver跑在哪都行：build-cli的WSL/mac，**或Ona容器里**——VSCode连Ona时会把容器的36984端口转发到Windows localhost，浏览器POST直穿SSH隧道到容器receiver（2026-07实测跑通）。**多个容器可各配一个receiver、共用一个token，一份cookie扇出到全部**（按项目隔离开发时用；popup里Local receivers加多行）。
> - **gdrive**（纯浏览器用Ona、无SSH端口转发时）→ 跳到 [gdrive transport（让Ona容器拿cookie）](#gdrive-transportona-runtime让-ona-容器拿-cookie)。扩展加密 → Google Drive → Ona消费。不依赖SSH会话。
>
> 原理见 [ARCHITECTURE.md决策12](ARCHITECTURE.md)。安全面见 [SECURITY.md §5](SECURITY.md)。

## 前置检查：企业浏览器策略

Roche域机器的Chrome通常受企业策略管控，先确认能装自定义扩展。

地址栏访问 `chrome://policy/`，看以下几项：

| 策略 | 状态 | 影响 |
|---|---|---|
| `ExtensionInstallBlocklist` | 含 `*` | sideload全禁，只能从企业store装 |
| `ExtensionInstallAllowlist` | 有列表 | 只允许列表内扩展 |
| `DeveloperToolsAvailability` | `2`（Disabled）| 装扩展的Developer mode开不了 |
| `BlockExternalExtensions` | `true` | 第三方扩展全禁 |

**没有这些策略 → 走下面5步**。
**有限制** → 联系IT，把扩展上架到Edge for Business内部store（参考 [Edge for Business Add-ons](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-manage-extensions-webstore)）。Roche内部流程通常1-2周。

## 5步安装

### 1. 起receiver（build-cli本地 / WSL2）

> **在Ona容器里？** 可用automations托管（面板勾开 `cookie-bridge` service，`manual` opt-in），见 [1.6 Ona容器起receiver](#16-ona-容器自动起-receiverautomations)。下面是build-cli本地（WSL2 / macOS）的手动起法。

```bash
cd demos/browser-cookie-bridge/receiver
# 想自定义 service 就 cp 一份改；不改的话可跳过——config.json 不存在时 start.sh 自动回退 config.example.json
cp config.example.json config.json   # 可选
./start.sh
```

`start.sh` 是带持久化的wrapper：第一次跑生成固定PORT + TOKEN写到 `~/.config/cookie-bridge/env`（mode 600），之后每次启动都读同一份。**popup配一次Local receiver + Token永久不变**，receiver重启不用改。多容器共享token：`export COOKIE_BRIDGE_RECEIVER_TOKEN=<同一个>` 再跑 `start.sh`，各容器receiver用同一token起。给receiver起个名（多容器辨识用）：`export COOKIE_BRIDGE_RECEIVER_NAME=<项目 slug>`，popup点 ↻ 后每行显示「端口 → name」。

启动后看到：

```
[start] generated /home/<你>/.config/cookie-bridge/env
[start]   PORT=36984
[start]   TOKEN=lwFjgIZKJiw8tXSdN2KxoHy6c6C1MAlbh45TnF2WNrE
[start] Receiver URL: http://127.0.0.1:36984

[bridge 2026-05-21T12:14:26+08:00] listening on http://127.0.0.1:36984
[bridge 2026-05-21T12:14:26+08:00] token: lwFjgIZKJiw8tXSdN2KxoHy6c6C1MAlbh45TnF2WNrE
[bridge 2026-05-21T12:14:26+08:00] services: servicenow, test
[bridge 2026-05-21T12:14:26+08:00] ready. Ctrl+C to stop.
```

记下URL和token（之后popup配置用）。**保持终端开着**，关掉receiver就死——不想每次手动起、也不想守着终端，见 [1.5让receiver常驻](#15-让-receiver-常驻wsl2--本地-build-cli可选)。

**重置token**（怀疑泄漏 / 想轮换）：删 `~/.config/cookie-bridge/env` 再跑 `./start.sh`，会重新生成。

**不想落盘token**（每次重启随机生成）：直接跑 `python3 cookie_receiver.py --config config.json`，跳过wrapper。trade-off详见 [ARCHITECTURE.md决策5](ARCHITECTURE.md)。

### 1.5让receiver常驻（WSL2 / 本地build-cli，可选）

> 仅适用于本地shell（WSL2、macOS build-cli）。Ona / FlexDev dev container没有持久后台、容器重启即重置，不要在Ona里装systemd service——在Ona用直接 `./start.sh` 或随项目脚本拉起即可。

每次手动 `./start.sh` 还要守着终端很烦。WSL2启用了systemd（`/etc/wsl.conf` 含 `[boot] systemd=true`）时，可以把receiver装成 **systemd user service**：开机自启、崩溃自愈、登出不死。

先确认systemd可用：

```bash
ps -p 1 -o comm=          # 输出 systemd 才行；输出 init 说明没启用 systemd
loginctl show-user "$USER" | grep Linger   # Linger=yes 才能登出后继续跑
```

`Linger=no` 时开启（一次性）：

```bash
loginctl enable-linger "$USER"
```

安装service（unit文件随repo提供，已用 `%h` 写成相对home的路径模板）：

```bash
mkdir -p ~/.config/systemd/user
cp demos/browser-cookie-bridge/receiver/cookie-bridge.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now cookie-bridge.service
systemctl --user status cookie-bridge      # 应看到 active (running)
curl -s http://127.0.0.1:36984/health      # 应返回 {"ok": true, ...}
```

> unit文件假设repo在 `~/projects/silicon-hitchhiker`。repo在别处时，编辑 `~/.config/systemd/user/cookie-bridge.service` 的 `WorkingDirectory` 和 `ExecStart` 两行改成实际路径，再 `daemon-reload` + `restart`。

日常操作：

```bash
systemctl --user restart cookie-bridge     # 改了 config.json 后重启（加 service 等）
systemctl --user daemon-reload && systemctl --user restart cookie-bridge   # 改了 unit 文件本身
journalctl --user -u cookie-bridge -f      # 看实时日志
systemctl --user disable --now cookie-bridge   # 停用并停止
```

装了service后就**不要再手动 `./start.sh`**——两个进程会抢同一个端口。

### 1.6 Ona容器自动起receiver（automations）

> 仅适用于Ona / FlexDev dev container。本地build-cli走 §1 / §1.5。

Ona容器重启即重置、没有systemd，但可以用 **automations** 拉起receiver。repo已在 [`.ona/automations.yaml`](../../../.ona/automations.yaml) 注册了 `cookie-bridge` service，但 **`triggeredBy: manual`（opt-in，默认不启）**——在Ona面板的Automations里手动勾开，或 `gitpod automations service start cookie-bridge`。设成manual而非开机自启是有意的：不默认占算力、不默认碰cookie（想每次开机零手动自启，走个人dotfiles，别改成 `postEnvironmentStart` 强加给全社区）。勾开后它会：

- 固定端口起（默认 `36984`，VSCode自动把它转发到Windows localhost）；
- token从 **Ona Secret** `COOKIE_BRIDGE_RECEIVER_TOKEN` 读——多容器设成同一个，扩展一个token扇出打全部；
- config.json不存在时自动回退config.example.json，fresh容器零配置即用。

配一次（在 [flexdev.roche.com](https://flexdev.roche.com) 的环境Secret里，rebuild生效）：

| Secret / env | 必填 | 作用 |
|---|---|---|
| `COOKIE_BRIDGE_RECEIVER_TOKEN` | 是（要跨容器共享token / fan-out时） | 所有容器receiver用同一token起；不设则每容器随机token，扩展要各配各的 |
| `COOKIE_BRIDGE_RECEIVER_PORT` | 否 | 覆盖默认 `36984`（每项目pin一个固定端口） |
| `COOKIE_BRIDGE_RECEIVER_NAME` | 否 | receiver标识（如项目slug），popup ↻ 后显示「端口 → name」认得出容器；不设则兜底hostname |

> Secret值不要外发；`COOKIE_BRIDGE_RECEIVER_NAME` 是明文标识，别塞secret进去（`/health` 无认证会返回它）。automations功能对部分成员仍在灰度（见hub AGENTS.md「Ona Automations权限」）——没入口时退回 §1在容器里手动 `./start.sh`。

> **容器早于本service合并时**（automations.yaml只在环境启动时读一次，老容器没吃到）：不用rebuild，用CLI灌进运行中的环境——`gitpod automations update .ona/automations.yaml` + `gitpod automations service start cookie-bridge`。`.ona/automations.yaml` 用的是 `services.<name>.commands.start` 格式（`gitpod automations init` 生成的模板即此格式）。托管service比裸 `./start.sh &` 稳——进程死了平台会重启。

### 2. 装扩展到Chrome（关键：选对路径）

WSL2 + Windows Chrome装扩展有两条路径，**Roche域机器只能走第二条**：

#### 路径A：直接从WSL2路径加载（一般环境用）

Chrome `chrome://extensions/` → 右上角Developer mode → Load unpacked → 选：

```
\\wsl.localhost\Ubuntu-24.04\home\<你>\projects\silicon-hitchhiker\demos\browser-cookie-bridge\extension
```

#### 路径B：通过C盘加载（Roche域机器必走）

Roche域机器装的端点安全软件（NetSkope / ZScaler / Crowdstrike类）会拦 `\\wsl$\` 和 `\\wsl.localhost\` 的SMB共享，加载时报"找不到网络名"。绕过：

```bash
# WSL2 终端跑（不要关 receiver 那个终端，新开一个）
mkdir -p /mnt/c/tools
cp -r /home/<你>/projects/silicon-hitchhiker/demos/browser-cookie-bridge/extension /mnt/c/tools/cookie-bridge-extension
ls /mnt/c/tools/cookie-bridge-extension/    # 验证有 manifest.json、background.js、popup.* 等
```

然后Chrome Load unpacked选 `C:\tools\cookie-bridge-extension`。

加载成功后扩展卡片显示 "Roche Cookie Bridge"，无红色 "错误" 按钮。

**之后改了扩展代码必须重新cp + reload**：

```bash
cp -r /home/<你>/projects/silicon-hitchhiker/demos/browser-cookie-bridge/extension/* /mnt/c/tools/cookie-bridge-extension/
```

然后 `chrome://extensions/` → 卡片右下角 **↻** 圆箭头reload。否则改动不生效。

### 3. 配置扩展

1. 浏览器右上角拼图按钮 → 找到Cookie Bridge → 点图钉Pin
2. 点扩展图标打开popup
3. 填：
   - **Token**: 粘贴步骤1的token（所有receiver共用同一个）
   - **Local receivers**：点 **+ Add** 加一行，填 `http://127.0.0.1:<port>`（步骤1终端打印的）。多个Ona容器就加多行、各填各的转发端口——一份cookie会扇出到全部（各行左侧勾选框控制启用）。
4. 点Service旁 **↻** 按钮（**不是Save**，是从receiver拉service列表）
   - status应该绿色 `receiver OK: servicenow, test`
   - 每行receiver右侧会显示 `→ <name>`（该容器receiver的标识）——多容器时据此认哪个转发端口是哪个容器，不可达的行显示 `→ ✕`
5. **Service** 下拉选 `servicenow`
6. 勾 **Auto-sync on cookie change**（按需）
7. 点 **Save**

### 4. 登录目标应用 + 同步cookie

1. Chrome新tab访问 `https://roche.service-now.com/`
2. 走完整SAML SSO登录（含MFA / 设备验证）
3. 登录成功后回扩展popup
4. 点 **Sync Now**

预期：

| 位置 | 看什么 |
|---|---|
| popup status框 | 绿色 `OK: N cookies → /home/<你>/.config/servicenow/cookies.json`（N通常8-15）|
| receiver终端 | `sync ok service=servicenow domain=roche.service-now.com cookies=N` |

### 5. 业务脚本验证

```bash
cd demos/browser-cookie-bridge/examples
pip install -r ../receiver/requirements.txt   # 装 requests
python3 servicenow_cookie_demo.py --whoami
```

预期：

```
[demo] loaded 10 cookies (synced at 2026-05-20T...)
[demo] fetching g_ck from UI page...
[demo] g_ck obtained: 11c1801087058f50...
[demo] OK ✓ session 有效
  user_name: <你的工号>
  name:      <你的中英文名>
  email:     <你的 Roche 邮箱>
```

整条管道打通。后续ServiceNow用法见 [SERVICENOW.md](SERVICENOW.md)。

## gdrive transport（Ona runtime）：让Ona容器拿cookie

**纯浏览器**用Ona（没有VSCode SSH端口转发）时，容器够不到你Windows上的localhost receiver，走 **gdrive transport**：扩展把cookie客户端加密上传到你My Drive的 `.cookie-bridge/<service>.enc`，Ona容器里的 `gdrive_cookie_sync.py` 读取、解密、落到容器本机 `~/.config/<service>/cookies.json`，消费后即焚Drive密文。业务脚本零改动。

> **你要是用VSCode-SSH连Ona**，其实可以直接走上面的 **local transport**：在容器里起receiver（`./start.sh`），VSCode会把容器36984转发到Windows localhost，浏览器POST直达——不用配Drive OAuth/passphrase，更省事。gdrive适合纯浏览器Ona、或不想依赖SSH会话常开的场景。

这条轨**两端各配一次**：扩展侧（Windows Chrome，一次性配OAuth + passphrase）+ Ona侧（设passphrase + 跑消费脚本）。

### A. 扩展侧（Windows Chrome，一次性）

扩展走 `chrome.identity` + **社区共享的OAuth client** 调Drive API。client_id和扩展ID **都已内置在manifest里**（manifest pin了 `key`，所有人加载后扩展ID都是同一个固定值 `kkbpopgphokcnhkbkdngkdlmmacamjjl`，对应一个已配好的共享client）。**你不需要建任何GCP东西，加载即用**：

1. **加载扩展**：`chrome://extensions` → 开发者模式 → 加载已解压的扩展程序 → 选 `extension/`（路径B用户选 `C:\tools\cookie-bridge-extension`）。因为manifest pin了 `key`，扩展ID固定是 `kkbpopgphokcnhkbkdngkdlmmacamjjl`，不随加载路径变——这正是共享client能对全员生效的原因。
2. **popup配置**：打开popup → 「Sync destinations」勾上 **Google Drive (Ona)** → 填 **Passphrase**（自己设一个加密口令，记住，Ona侧要填同一个）→ Save。

> **维护者：换成自己的GCP项目**（fork或独立部署时才需要，普通用户跳过）。共享client在项目 `rdsz-dw`（`949346915220`）下，与google-workspace同项目、同意屏幕Internal。要换成你自己的：① 生成一对key（`openssl genrsa` → 取公钥DER的base64填manifest `key`；扩展ID = `SHA256(公钥DER)` 前32位hex逐字符 `0-f`→`a-p` 映射）② 在你项目建Chrome-Extension类型OAuth client，Item ID填这个派生ID ③ 把client_id填进 `oauth2.client_id`。**注意扩展用 `getAuthToken`，只认Chrome-Extension类型client，Desktop/Web类型的client_id填进去会被拒。**

### B. Ona侧（容器内）

1. **设passphrase**（与扩展popup里填的**完全一致**）：
   ```bash
   export COOKIE_BRIDGE_PASSPHRASE='你在 popup 里填的那个口令'
   ```
   常用就写进Ona Secret（重启容器生效）或 `~/.bashrc`。**绝不经聊天工具传**（见SECURITY.md）。

2. **config.json可跳过（零配置即用）**：消费端在 `config.json` 不存在时**自动回退读 `config.example.json`**（已含cidm/servicenow/bilibili/devhub等常用service）。所以fresh环境（Ona rebuild、新clone）**不用手动cp**，直接跑第4步即可。
   - 只有当你要**自定义**（加自建service、改output路径）时才 `cp config.example.json config.json` 后编辑——`config.json` 被gitignore（本地live配置，不进repo），存在时优先于example。

3. **前置**：Ona容器已配好google-workspace凭据（`gw_client` 能用，含 `drive` scope）。没配见 `demos/google-workspace` 的auth步骤。

4. **跑消费**（先在浏览器点过Sync Now，Drive上才有密文）：
   ```bash
   cd demos/browser-cookie-bridge/receiver
   python3 gdrive_cookie_sync.py                # 单次，消费所有 service（config.json 缺则自动用 example）
   python3 gdrive_cookie_sync.py --service cidm # 单次，仅 cidm
   ```
   预期日志：`ok service=cidm cookies=N -> ~/.config/cidm/cookies.json` + `即焚: deleted Drive cidm.enc`。（`config.json` 不存在时会先打一行 `回退用 config.example.json`。）

5. **业务脚本零改动**复用：cookie已落 `~/.config/<service>/cookies.json`（mode 600），照常 `shortlink_client.py` 等。

**默认on-demand单次**。`--watch` 轮询常驻是footgun（Ona容器ephemeral，watcher随rebuild死掉则即焚不再触发、密文堆积），低频场景别用；真要常驻它每轮附带TTL孤儿清理（`--ttl`，默认1h）作backstop。手动清孤儿：`gdrive_cookie_sync.py --reap`。

### gdrive排错

| 现象 | 含义 | 修 |
|---|---|---|
| popup gdrive ERR `getAuthToken: ...` | 没登录Google / EMU拦 / (维护者)扩展ID与client Item ID不匹配 | 确认Chrome登着Google；扩展ID应为 `kkbpopgphokcnhkbkdngkdlmmacamjjl`（`chrome://extensions` 看）、与共享client Item ID一致 |
| 消费端 `passphrase mismatch` | 两端口令不一致 | 改对 `COOKIE_BRIDGE_PASSPHRASE`（=popup里那个）重跑；**不会即焚**，密文还在可重试 |
| 消费端 `no .enc to consume` | Drive上没密文 | 先在浏览器点Sync Now（gdrive出口勾上）|
| 消费端 `skip service=X: not in config.services` | 配置缺该service | 在config.example.json（或你cp出的config.json）加该service的domains + output |
| Drive HTTP 403 | scope/host或Drive API没启用 | 确认scope `drive.file` + 项目enable Drive API |

## 排错

### 扩展加载报"找不到网络名"

走 [路径B](#路径-b通过-c-盘加载roche-域机器必走)。`\\wsl$\` 被企业SMB拦截策略拦了，搬 `C:\tools\` 绕过。

### popup ↻ 报 `receiver 不可达: Failed to fetch`

按以下顺序排查：

```bash
# 1. WSL2 自调
curl http://127.0.0.1:<port>/health
```

```powershell
# 2. Windows PowerShell 调（关键测试）
Invoke-WebRequest http://127.0.0.1:<port>/health -UseBasicParsing
# 别用 curl：Roche 域机的 curl.exe 常被 AppLocker 挡（报「程序已被组策略阻止」）
```

| 1通 + 2通 | popup配置错（URL多空格、含 `https://`）|
| 1通 + 2不通 | WSL2 localhost forwarding没生效（Ona容器则见下） |
| 1不通 | receiver进程挂了，回终端看 |

WSL2 localhost forwarding修复：编辑 `C:\Users\<你>\.wslconfig` 加：

```ini
[wsl2]
localhostForwarding=true
```

然后PowerShell跑 `wsl --shutdown` 后重启receiver。

**Ona容器场景（VSCode自动转发变绿点空壳）**：receiver跑在容器里，靠VSCode把容器端口转发到Windows localhost。这个自动转发**不可靠**——Ports面板显示36984在转发，但从Windows `Invoke-WebRequest http://127.0.0.1:36984/health -UseBasicParsing` 打过去超时，扩展Sync也timeout。先在容器里 `curl -s localhost:36984/health` 确认receiver本身健康（返200）——锅在转发不在receiver。

**别依赖Ports面板自动转发，也别用独立 `ssh -N -L <env-id>.gitpod.remote`**（2026-07实测不通：`*.gitpod.remote` 的ProxyCommand要VS Code会话上下文，独立ssh驱动会 `Connection timed out during banner exchange`）。**正解＝把 `LocalForward` 声明进Windows `~/.ssh/config` 的 `Host *.gitpod.remote` 块**——搭VSCode连接的ssh级硬转发，通配符不写死env-id、环境rebuild零维护：

```
Host *.gitpod.remote
    RemoteForward 127.0.0.1:2200 127.0.0.1:2200    # 若同时用反向隧道回连本机
    LocalForward  127.0.0.1:36984 127.0.0.1:36984
```

改完 **reload VSCode一次**即生效，之后随连接自动带上、断线自愈，不再逐次reload。机制、双向（`-R` 回连跑命令）、排查详见 [Ona反向SSH隧道](../../../docs/guide/ona-reverse-tunnel.md)。

### popup ↻ 报CSP错（fetch被default-src拦）

popup.html的 `Content-Security-Policy` meta缺 `connect-src http://127.0.0.1:*`。当前demo已修，但Chrome 132+ 对popup CSP越来越严，未来可能再撞。修法：编辑 [extension/popup.html](../extension/popup.html) 的meta标签加 `connect-src`，cp + reload。

### popup ↻ 报PNA错（Private Network Access）

Chrome 102+ 起，从 `chrome-extension://` fetch到127.0.0.1必须在preflight响应里带 `Access-Control-Allow-Private-Network: true` header。当前receiver已加（[cookie_receiver.py](../receiver/cookie_receiver.py) `_cors_headers`），但如果未来Chrome加更严的PNA校验，看官方文档：[chromium.org/blink/private-network-access](https://chromestatus.com/feature/5436853517811712)。

### `Sync Now` 后cookies = 0

最常见的诊断和修复：

#### A. domains配置错

receiver终端日志显示 `got N cookies but none match allowed domains {'xxx'}`：

- 浏览器F12 → Application → Cookies → 看实际cookie的Domain字段
- 对照 `receiver/config.json` 里该service的 `domains` 列表
- 注意cookie domain可能带前导 `.`（如 `.service-now.com`），config里两种写法都接受

#### B. Profile错位

扩展装在Profile A，登录目标应用在Profile B，cookie store不互通。诊断：

```bash
# WSL2 跑，看哪个 profile 装了扩展
python3 -c "
import json, os
root = '/mnt/c/Users/<你>/AppData/Local/Google/Chrome/User Data'
for p in os.listdir(root):
    pref = os.path.join(root, p, 'Secure Preferences')
    if not os.path.exists(pref): continue
    try:
        d = json.load(open(pref))
    except: continue
    for eid, meta in d.get('extensions', {}).get('settings', {}).items():
        if 'cookie-bridge' in str(meta.get('path', '')).lower():
            print(f'{p}: ext_id={eid}, path={meta.get(\"path\")}')"
```

修：在登录目标应用的那个profile里重新Load unpacked装扩展。

#### C. host_permissions不涵盖目标域

`extension/manifest.json` 的 `host_permissions` 列表没有目标域 → chrome.cookies API拒绝访问。修：加目标域，cp + reload。

#### D. chrome.cookies.getAll的RFC matching问题

Chrome 130+ 在某些情况下 `{domain: "..."}` 模式拿不到结果。当前demo用 `{url: "..."}` + `{domain: "..."}` 双重查询合并去重（[background.js](../extension/background.js) `collectCookies`），如果还是0 → 直接在service worker DevTools console跑：

```javascript
chrome.cookies.getAll({url: "https://<目标>/"}, c => console.log(c.length, c.slice(0,3)))
```

返回0 → 是权限或profile问题，不是API问题。

### `401 User Not Authenticated` (ServiceNow / 类似SAML应用)

不是cookie失效就是X-UserToken (g_ck) 没拿到。详见 [SERVICENOW.md § 排错](SERVICENOW.md#排错)。

### Cookie过期

cookie会过期（几小时到几天）。扩展开了auto-sync时浏览器重新登录会自动推送新cookie。没开auto-sync要手动Sync Now。

可以用 `stat` 看cookie文件mtime推断剩余时间：

```bash
stat -c '%Y' ~/.config/<service>/cookies.json
```

## 升级 / 卸载

**升级**：`git pull` 后：

```bash
# WSL2 内同步扩展代码（如果走路径 B）
cp -r /home/<你>/projects/silicon-hitchhiker/demos/browser-cookie-bridge/extension/* /mnt/c/tools/cookie-bridge-extension/
```

然后 `chrome://extensions/` → 卡片 **↻** reload。

receiver不需要单独升级（直接git pull后Ctrl+C重启即可）。

**卸载**：

- 扩展：`chrome://extensions/` → 卡片 "移除"
- receiver：终端Ctrl+C终止；装了systemd service的话 `systemctl --user disable --now cookie-bridge` 后删 `~/.config/systemd/user/cookie-bridge.service`
- cookie文件：手动删 `rm -rf ~/.config/<service>/`（不会自动清）
- Windows副本：`rm -rf /mnt/c/tools/cookie-bridge-extension/`（不会自动清）
