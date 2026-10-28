# Cookie Bridge × ServiceNow

本文档讲 **Cookie Bridge 这个 demo 在 ServiceNow 场景下的具体使用**。完整的 ServiceNow 认证机制（含 g_ck / X-UserToken 原理、跟其他 auth 方案的对比）见 [demos/servicenow/docs/AUTHENTICATION.md](../../servicenow/docs/AUTHENTICATION.md)，本文档不重复机制层面的解释。

## 落地位置

```
~/.config/servicenow/cookies.json   # WSL2 内，mode 600
```

文件 schema 见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## demo 脚本：servicenow_cookie_demo.py

[examples/servicenow_cookie_demo.py](../examples/servicenow_cookie_demo.py)

```bash
cd demos/browser-cookie-bridge/examples
pip install requests

# 验证 session 有效（看你登录身份）
python3 servicenow_cookie_demo.py --whoami

# 查 incident 表（默认）
python3 servicenow_cookie_demo.py

# 查任意表 + query
python3 servicenow_cookie_demo.py --table sc_cat_item \
    --query "nameLIKETemporary^active=true" \
    --fields "sys_id,name,short_description" \
    --limit 10

# 查 catalog item
python3 servicenow_cookie_demo.py --table sc_req_item --query "opened_by.user_name=javascript:gs.getUserName()" --limit 5
```

## g_ck 在本 demo 怎么自动处理

`servicenow_cookie_demo.py` 第一次调 `/api/now/*` 时会自动：

1. GET `https://roche.service-now.com/now/nav/ui/classic/params/target/home_splash.do`
2. 用正则 `g_ck\s*=\s*["']([0-9a-f]{40,80})["']` 抓出 token
3. 缓存到 `session.headers["X-UserToken"]`，后续 API 调用复用

代码：[examples/servicenow_cookie_demo.py:60-75](../examples/servicenow_cookie_demo.py)（`fetch_g_ck()` 函数）。

g_ck 跟 cookie 是**配套的**——cookie 失效后旧 g_ck 也失效，要先 sync 新 cookie 再重新抓。机制详细看 [AUTHENTICATION.md § 4](../../servicenow/docs/AUTHENTICATION.md)。

## Cookie 失效怎么办

ServiceNow session cookie 通常 8-12 小时过期。失效表现：

- `--whoami` 报 `401 User Not Authenticated`
- 或者 ` /stats.do` 返回 302 → `logout_redirect.do`

**修复**：

1. Chrome 打开 `https://roche.service-now.com/`
2. 走一次 SAML SSO 登录（如果只是 session 过期不需要重新输密码，IDP 会直接放行）
3. 如果 popup 开了 **Auto-sync on cookie change**，cookie 自动推到 WSL2，无需手动操作
4. 没开 auto-sync → 手动点扩展 popup 的 **Sync Now**
5. 重跑脚本

可以把 cookie 文件改了之后 mtime 写到日志里，配合 cron 检测：

```bash
stat -c '%Y' ~/.config/servicenow/cookies.json
# 比当前时间晚于 8h → 大概率失效，提示重新登录
```

## 提交 Catalog Item

cookie 同步好之后，**用 [demos/servicenow/scripts/snow_catalog.py](../../servicenow/scripts/snow_catalog.py) 提单子，加 `--auth cookie` 即可**——业务逻辑（搜 item / 看 schema / mandatory 预检 / dry-run / order）跟 GA Basic Auth 模式共用一份代码：

```bash
cd demos/servicenow/scripts

# 看 mandatory 字段（递归走变量集）
python3 snow_catalog.py --auth cookie schema <sys_id>

# dry-run
python3 snow_catalog.py --auth cookie order <sys_id> --vars-file vars.json --dry-run

# 真提交（工单 created_by 显示你本人）
python3 snow_catalog.py --auth cookie order <sys_id> --vars-file vars.json
```

完整流程 + 嵌套变量集 mandatory 的踩坑（含 "Temporary admin rights" 实测案例）见 [AUTHENTICATION.md § 8](../../servicenow/docs/AUTHENTICATION.md)，本 demo 不重复维护。

## 进阶：Playwright 注入 cookie 做 UI 自动化

Cookie 方案独有能力 —— GA + Basic Auth 做不到的事。

适用场景：
- catalog item 表单有 UI Policy（动态字段、动态必填）—— REST API 提交容易漏字段，浏览器内提交触发完整 policy 链
- ServiceNow Workspace / Now Experience UI 操作（API 没暴露的功能）
- 需要触发 client-side validation 的附件上传

代码示例：

```python
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    data = json.loads(Path("~/.config/servicenow/cookies.json").expanduser().read_text())
    cookies_for_pw = [
        {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": c.get("sameSite", "Lax"),
        }
        for c in data["cookies"]
    ]

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(cookies_for_pw)
        page = await context.new_page()

        # 直接进 catalog item 表单页（已登录态）
        await page.goto(f"https://roche.service-now.com/sp/?id=sc_cat_item&sys_id={SYS_ID}")
        await page.wait_for_selector("input[name='computer_name']")

        # 填表（触发 UI Policy）
        await page.fill("input[name='computer_name']", "RSHMX030223")
        await page.fill("textarea[name='business_justification']", "PoC test")
        # 选了 duration_days 后某些字段才显示，UI Policy 自动跑
        await page.select_option("select[name='duration_days']", "7")

        # 抓动态显示出来的字段（API mode 看不到）
        dynamic_fields = await page.query_selector_all("[data-policy-controlled='true']")

        # 提交（生产前先 dry-run，截图保留）
        await page.screenshot(path="before_submit.png")
        # await page.click("button[type='submit']")  # 真提交

        await browser.close()

asyncio.run(main())
```

**注意点**：
- `headless=True` 行为可能跟 `headless=False` 略有差异（某些 ServiceNow widget 检测 headless），调试期用 `headless=False`
- cookie 注入后第一次访问可能仍需让 ServiceNow 完成 session bootstrap，加 `await page.wait_for_load_state("networkidle")`
- ServiceNow 的页面渲染慢，每个 selector 等待要给够时间（默认 30s 不够时显式 `timeout=60000`）

## 跟 demos/servicenow/（GA + Basic Auth）的关系

互补，不替代。

| 用 Cookie Bridge | 用 demos/servicenow/ (GA) |
|---|---|
| 个人提单 / 临时事务 | 周期性批处理 / cron |
| 工单归属你本人是 feature | 工单归属 GA 是 feature |
| 需要 UI Policy / Workspace 能力 | 仅 REST API 即可 |
| 没 GA 或 IT 没批 | 已有 GA + 权限 |

完整选型对比 + 决策树：[AUTHENTICATION.md § 5-6](../../servicenow/docs/AUTHENTICATION.md)。

## 排错

### `401 User Not Authenticated`

99% 是 cookie 失效。流程见上面"Cookie 失效怎么办"。

剩下 1%：g_ck 没正确抓到（HTML 结构变了）。debug：

```bash
python3 -c "
import requests, json
from pathlib import Path
data = json.loads(Path('~/.config/servicenow/cookies.json').expanduser().read_text())
s = requests.Session()
for c in data['cookies']:
    s.cookies.set(c['name'], c['value'], domain=c['domain'].lstrip('.'))
r = s.get('https://roche.service-now.com/now/nav/ui/classic/params/target/home_splash.do', timeout=15)
print('HTTP', r.status_code, 'size', len(r.text))
print('contains g_ck:', 'g_ck' in r.text)
import re
m = re.search(r'g_ck\s*=\s*[\"\\\']([0-9a-f]{40,80})[\"\\\']', r.text)
print('g_ck found:', bool(m), m.group(1)[:20] if m else None)
"
```

### `302 → logout_redirect.do`

ServiceNow 看到 cookie 但认为 session 已登出。原因之一：cookie 部分有效（只有部分关键 cookie），缺 `glide_user_session` / `JSESSIONID`。检查 cookie 文件：

```bash
python3 -c "
import json
from pathlib import Path
d = json.loads(Path('~/.config/servicenow/cookies.json').expanduser().read_text())
names = sorted(c['name'] for c in d['cookies'])
print('cookies:', names)
print('count:', len(names))
required = ['JSESSIONID', 'glide_session_store', 'glide_sso_id']
missing = [r for r in required if r not in names]
print('missing critical:', missing)
"
```

如果 missing 关键 cookie → 浏览器登录态不完整，可能在 SAML 跳转中间被打断。完整重新登录 + Sync Now。

### `400 Mandatory Variables are required`

ServiceNow 不告诉你缺哪个 mandatory 变量。`snow_catalog.py order` 在 POST 前会本地预检并指明，节省一轮试错：

```bash
cd demos/servicenow/scripts
python3 snow_catalog.py --auth cookie schema <sys_id>           # 看完整必填列表
python3 snow_catalog.py --auth cookie order <sys_id> \
    --vars-file vars.json --dry-run                              # 预检 + 不 POST
```

最常见的 root cause：mandatory 变量在嵌套变量集里。原理 + 实测案例见 [AUTHENTICATION.md § 8](../../servicenow/docs/AUTHENTICATION.md)。

### catalog item submit 后 RITM 被退回

ServiceNow UI Policy 在 API 提交时不跑，可能漏填动态字段。两条路：

1. 在 ServiceNow UI 上手动开一遍这个 catalog 表单（不 submit），看 UI 上必填的字段集，对比你 API payload
2. 或者改用 Playwright 注入 cookie 走 UI 提交

详见 [AUTHENTICATION.md § 7](../../servicenow/docs/AUTHENTICATION.md)。

## 快速命令参考

```bash
# 验证身份
python3 servicenow_cookie_demo.py --whoami

# 查我的工单
python3 servicenow_cookie_demo.py --table sc_req_item \
    --query "opened_by.user_name=javascript:gs.getUserName()" \
    --fields "number,short_description,state,sys_created_on" --limit 10

# 查我提的所有 catalog item
python3 servicenow_cookie_demo.py --table sc_request \
    --query "requested_for.user_name=javascript:gs.getUserName()" \
    --fields "number,description,request_state" --limit 10

# 找 catalog item by 名字
python3 servicenow_cookie_demo.py --table sc_cat_item \
    --query "nameLIKETemp Local Admin^active=true" \
    --fields "sys_id,name,short_description"

# 提单子（用 demos/servicenow/scripts/snow_catalog.py，加 --auth cookie 即可）
cd ../../servicenow/scripts
python3 snow_catalog.py --auth cookie schema <sys_id>
python3 snow_catalog.py --auth cookie order <sys_id> --vars-file vars.json

# 跑通后落地的 cookie 文件
ls -la ~/.config/servicenow/cookies.json
```
