# Cookie Bridge 业务 Client 模板（RECIPES）

> 加完 service 拿到 cookie 之后**还要写业务 client**——cookie 抓取是 cookie-bridge 的职责，调 API 是各应用的协议差异。本文是已知协议类的 client 模板，照抄改 base_url 就能起步。
>
> 入口：[scripts/probe-service.sh](../scripts/probe-service.sh) 探测目标域，输出对应 RECIPE 锚点。
>
> 没识别出来？看最后一节"未知类的诊断流程"。

## 分类一览

| RECIPE | 适用 | 体量 | 实例 |
|--------|------|------|------|
| [servicenow](#servicenow) | ServiceNow 全家 | ~150 行 | [snow_client.py](../../servicenow/scripts/snow_client.py) |
| [sailpoint-iiq](#sailpoint-iiq) | SailPoint IdentityIQ（CIDM 类） | ~80 行 | `$WORKDOCS_PATH/silicon-hitchhiker-community/scripts/cidm_workitems.py`（含组 GUID 敏感，私 repo） |
| [atlassian](#atlassian) | Jira / Confluence Server / Cloud | ~80 行 | (待实现) |
| [sharepoint](#sharepoint) | SharePoint Online / On-prem | ~120 行 | (待实现) |
| [generic-jsessionid](#generic-jsessionid) | 普通 Java/Spring Boot 后端 | ~50 行 | (待实现) |
| [bearer-localstorage](#bearer-localstorage) | 现代 SPA + JWT/Bearer in localStorage | **cookie-bridge 不适用，独立实现** | [demos/bearer-localstorage/](../../bearer-localstorage/) |
| [connectrpc](#connectrpc) | ConnectRPC / protobuf-over-HTTP（Buf / Connect 生态、Gitpod Flex） | ~120 行（基类 + 实例） | [demos/connectrpc/](../../connectrpc/) |

---

## servicenow

**特征**：g_ck（X-UserToken）是页面 JS 全局变量 `window.g_ck`，**不在 cookie 里**——必须脚本 fetch home_splash.do 后从 HTML regex 抓出来。

**关键点**：
- cookie：`glide_session_store` + `glide_user_route` + `BIGipServerpool_*`（普通 cookie，chrome.cookies API 直接拿）
- CSRF：`X-UserToken: <g_ck>` 写头
- keep-alive endpoint：`/now/nav/ui/classic/params/target/home_splash.do`

**模板代码**：完整实现见 [demos/servicenow/scripts/snow_client.py](../../servicenow/scripts/snow_client.py)，核心结构：

```python
class SnowClient:
    def __init__(self, cookies_path):
        self.session = requests.Session()
        for c in json.load(open(cookies_path))["cookies"]:
            self.session.cookies.set(c["name"], c["value"], domain=c["domain"])
        self.base = "https://roche.service-now.com"
        self.session.headers["X-UserToken"] = self._fetch_g_ck()

    def _fetch_g_ck(self):
        # GET home_splash.do 后 regex 抓 window.g_ck = "..."
        r = self.session.get(f"{self.base}/now/nav/ui/classic/params/target/home_splash.do")
        m = re.search(r'window\.g_ck\s*=\s*[\'"]([^\'"]+)[\'"]', r.text)
        if not m:
            raise RuntimeError("g_ck 抓不到——cookie 失效，去浏览器 Sync Now")
        return m.group(1)

    def get(self, path, **kwargs):
        return self.session.get(f"{self.base}{path}", **kwargs)
```

---

## sailpoint-iiq

**特征**：partitioned cookie (CHIPS)——`XSRF-TOKEN` cookie 在 chrome.cookies API 里**看不到**，必须 cookie-bridge 扩展端跑 content script fallback（已实现）。前提：cidm tab 一直开着。

**关键点**：
- cookie：标准 + `XSRF-TOKEN`（partitioned，content script fallback 抓）
- CSRF：`X-XSRF-TOKEN: <XSRF-TOKEN cookie value>`（Angular 标准 double-submit）
- 双 JSON 解包：Roche IIQ 部分 endpoint 返回 `{"data": "<JSON 字符串>"}`，要 json.loads 两次
- keep-alive endpoint：`/identityiq/home.jsf`

**模板代码**：完整实现见 `$WORKDOCS_PATH/silicon-hitchhiker-community/scripts/cidm_workitems.py`（含 cd2-ai-hackathon-* 组 GUID + auto-approve 业务规则，因含敏感数据落私 repo 而非 hub innersource）。核心结构（鉴权层无敏感，可在公开 RECIPE 里展示）：

```python
def load_iiq_session(cookies_path, base_url):
    session = requests.Session()
    cookies = json.load(open(cookies_path))["cookies"]
    xsrf = None
    for c in cookies:
        session.cookies.set(c["name"], c["value"], domain=c["domain"])
        if c["name"] == "XSRF-TOKEN":
            xsrf = c["value"]
    if not xsrf:
        raise RuntimeError("XSRF-TOKEN 缺失——content script fallback 没生效，"
                           "确认浏览器 cidm tab 开着 + 重 Sync Now")
    session.headers["X-XSRF-TOKEN"] = xsrf
    session.headers["Accept"] = "application/json"
    return session
```

---

## atlassian

**特征**：`atl_token` cookie + `X-Atlassian-Token: no-check` header（防 XSRF），REST 路径一般 `/rest/api/2/` 或 `/rest/api/3/`。

**关键点**：
- cookie：`JSESSIONID` + `atl_token` + `_atlassian_token.<hash>`（Cloud 有更多）
- CSRF：写操作必须加 `X-Atlassian-Token: no-check`，读操作可省
- API 风格：分页用 `startAt` + `maxResults`

**模板**（待补充实现示例，结构示意）：

```python
def load_atlassian_session(cookies_path, base_url):
    session = requests.Session()
    for c in json.load(open(cookies_path))["cookies"]:
        session.cookies.set(c["name"], c["value"], domain=c["domain"])
    session.headers.update({
        "Accept": "application/json",
        "X-Atlassian-Token": "no-check",
    })
    return session
```

---

## sharepoint

**特征**：写操作必须先 POST `/_api/contextinfo` 拿 `FormDigestValue`，作为 `X-RequestDigest` 头。Digest 有效期 ~30min，要按需续。

**关键点**：
- cookie：`FedAuth` + `rtFa`（SP Online）/ `WSS_KeepSessionAuthenticated` 等
- CSRF：`X-RequestDigest: <FormDigestValue>` 写操作必带
- 读写不对称：GET 不要 digest，POST/MERGE/DELETE 要

**模板**（待补充实现示例）：

```python
def get_request_digest(session, base_url):
    r = session.post(
        f"{base_url}/_api/contextinfo",
        headers={"Accept": "application/json;odata=verbose"},
    )
    return r.json()["d"]["GetContextWebInformation"]["FormDigestValue"]
```

---

## generic-jsessionid

**特征**：Java / Spring Boot 后端，session 凭据是 `JSESSIONID` cookie，CSRF 看具体框架（Spring Security 默认是 `_csrf` 表单字段或 `XSRF-TOKEN` cookie + `X-XSRF-TOKEN` 头，跟 Angular 一致）。

**判断 CSRF 是否启用**：

- F12 看登录请求是否有 `_csrf` 参数 → 表单提交模式
- F12 看 cookie 是否有 `XSRF-TOKEN` → 走 sailpoint-iiq 同款 double-submit
- 都没有 → 该应用没启 CSRF，普通 GET/POST 即可

**模板**：

```python
def load_jsession(cookies_path, base_url):
    session = requests.Session()
    for c in json.load(open(cookies_path))["cookies"]:
        session.cookies.set(c["name"], c["value"], domain=c["domain"])
    # 按需加 CSRF——根据 F12 判断后选一种：
    # session.headers["X-XSRF-TOKEN"] = next(
    #     c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"
    # )
    return session
```

---

## bearer-localstorage

**特征**：现代 SPA（Vue / React + 阿里云 / 腾讯云后端），登录后服务端返 Bearer token，前端写到 `localStorage.AccessToken` 或类似 key。**完全不用 cookie 维持 session**。

**为什么 cookie-bridge 不适用**：
- cookie-bridge 抓 cookie，但该类站凭据不在 cookie 里
- 即使 cookie 拿到（如阿里云 WAF 的 `acw_tc`），也不是业务凭据，调 API 仍 401

**独立 demo + 通用 client base**：

完整实现见 [demos/bearer-localstorage/](../../bearer-localstorage/)，含：

- [scripts/bearer_client.py](../../bearer-localstorage/scripts/bearer_client.py) —— 通用 base（load token + Authorization 注入 + 401 提示重抓 token + GET/POST 包装）
- [examples/nihsc/nihsc_client.py](../../bearer-localstorage/examples/nihsc/nihsc_client.py) —— chs-ihssc.cn 应用级 client，继承 BearerClient 绑 base_url

**正确流程**：

1. 不接入 cookie-bridge（确认 manifest host_permissions + config.json 都没该 service）
2. 浏览器 F12 console 跑 `copy(localStorage.AccessToken)`
3. WSL: `echo -n '<paste>' > ~/.config/<service>/token && chmod 600 ~/.config/<service>/token`
4. `examples/<app>/<app>_client.py` 继承 BearerClient 调 API

**最小用法**（继承 BearerClient 三行起步）：

```python
from bearer_client import BearerClient

class MyClient(BearerClient):
    BASE_URL = "https://your-app.com"
    DEFAULT_TOKEN_PATH = "~/.config/myapp/token"

    def __init__(self, token_path=None):
        super().__init__(token_path or self.DEFAULT_TOKEN_PATH, self.BASE_URL)

client = MyClient()
data = client.get_json("/api/something")
```

**已知实例**：[chs-ihssc.cn](https://www.chs-ihssc.cn/)（2026 全国智慧医保大赛官网，阿里云 + Spring Boot opaque token，无 refreshToken）。

---

## connectrpc

**特征**：现代前端（Buf / Connect 生态）走 ConnectRPC（protobuf-over-HTTP），不是 REST。判别信号：

- XHR URL 形如 `/api/<package>.<Service>/<Method>`（包名.服务/方法，不是 REST 路径）
- 请求头 `Connect-Protocol-Version: 1`
- 前端 bundle 里一堆 `*_pb-XXXX.js`（protobuf 生成代码）
- body 是 JSON（`useBinaryFormat=false`），错误是 `{"code","message"}`

**关键点**：
- cookie：浏览器 SSO session cookie（cookie-bridge 普通同步即可，无特殊 CSRF）
- endpoint：`POST <base>/<package>.<Service>/<Method>`，`base` 常是 origin + `/api`
- **逆出契约**：ConnectRPC 无公开文档，但前端 bundle 内联 base64 编码的 FileDescriptorProto——解出来拿到所有 service/method/字段名。用 [decode_protobuf_descriptor.py](../../connectrpc/scripts/decode_protobuf_descriptor.py)
- **鉴权头因实例而异**：纯协议无特殊头，但具体后端可能要 principal/CSRF 头（如 Gitpod Flex 的 `X-Gitpod-Principal`）——在子类处理

**模板代码**：完整实现见 [demos/connectrpc/scripts/connectrpc_client.py](../../connectrpc/scripts/connectrpc_client.py)，分两层（纯协议基类 + 实例子类，体例同 bearer 的 BearerClient + nihsc）：

```python
from connectrpc_client import ConnectRpcClient

c = ConnectRpcClient(base_url="https://<host>/api",
                     cookie_file="~/.config/<service>/cookies.json")
resp = c.call("acme.v1.WidgetService/GetWidget", {"id": "..."})
widgets = c.paginate("acme.v1.WidgetService/ListWidgets", {}, items_key="widgets")
```

**已知实例**：Gitpod Flex / Ona（`flexdev.roche.com`），鉴权怪癖：`X-Gitpod-Principal: user/<userId>` 头 + 用 `AccountService/GetAccount` 引导取身份（principal 用 `memberships[].userId` 不是 `account.id`）。见 `GitpodFlexClient` 子类。

---

## 未知类的诊断流程

`probe-service.sh` 没识别 → 用户手动判断。打开 F12 → Network → 任意 XHR 请求，看：

| 看到 | 大概率属于 |
|------|----------|
| Request Header `Cookie:` 含 session-like cookie + 有 `X-CSRF-Token` / `X-XSRF-TOKEN` 头 | 自定义 cookie + double-submit CSRF，参考 sailpoint-iiq |
| Request Header `Authorization: Bearer xxx` 且 cookie 里没看到关键 session | bearer-localstorage（cookie-bridge 不适用） |
| URL 形如 `/api/pkg.v1.Service/Method` + `Connect-Protocol-Version` 头 + bundle 有 `*_pb*.js` | connectrpc |
| Request Header `Authorization: Basic xxx` | 该站走 HTTP Basic，cookie-bridge 不适用，用 GA 凭据 |
| 只有 `Cookie: JSESSIONID=...` 没其他凭据 | generic-jsessionid（最简单） |
| `Cookie:` 含 `__RequestVerificationToken` | ASP.NET MVC 默认 anti-forgery，要拼 form digest |

判断完后**把发现补到本文件**，让下一个人不用重新挖。补的格式照抄上面任一节即可。
