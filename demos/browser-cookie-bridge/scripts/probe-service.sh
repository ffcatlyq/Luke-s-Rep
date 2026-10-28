#!/usr/bin/env bash
# probe-service.sh —— 探测目标域属于哪类企业应用，给出 client 适配建议。
#
# 用法:
#   ./probe-service.sh <url>
#   ./probe-service.sh https://roche.service-now.com/
#   ./probe-service.sh https://cidm.roche.com/identityiq/home.jsf
#   ./probe-service.sh https://www.chs-ihssc.cn/my-sign
#
# 不需要登录态——根据未登录状态下的响应特征推断协议类型。
# 输出指向 docs/RECIPES.md 里对应的 client 模板。
#
# 退出码:
#   0  能识别为已知类（含"明确不适用"）
#   1  无法识别（未知 / 第一次见的协议）

set -euo pipefail

URL="${1:-}"
if [[ -z "$URL" ]]; then
  echo "用法: $0 <url>" >&2
  exit 2
fi

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36'
TMP_HEADERS=$(mktemp)
TMP_BODY=$(mktemp)
trap 'rm -f "$TMP_HEADERS" "$TMP_BODY"' EXIT

# -L 跟 redirect，-D 存 response headers，-o 存 body
# curl 失败（DNS / TCP / TLS）时 -w '%{http_code}' 自己会输出 "000"，
# 不要用 `|| echo "000"` 否则会追加成 "000000"
HTTP_CODE=$(curl -sL -m 15 \
  -A "$UA" \
  -D "$TMP_HEADERS" \
  -o "$TMP_BODY" \
  -w '%{http_code}' \
  "$URL" 2>/dev/null) || HTTP_CODE="000"

FINAL_URL=$(curl -sL -m 10 -A "$UA" -o /dev/null -w '%{url_effective}' "$URL" 2>/dev/null || true)
[[ -z "$FINAL_URL" ]] && FINAL_URL="$URL"

echo "── Probe $URL"
if [[ "$HTTP_CODE" == "000" ]]; then
  echo "   HTTP 000 (curl failed — 多半 WSL 出不到 Roche 内网；后续靠 URL 模式判断)"
else
  echo "   HTTP $HTTP_CODE  →  $FINAL_URL"
fi
echo ""

# 识别规则（按特征强度排序，越靠前匹配优先）。
# 检查的信号：
#   - response headers 里的 Server / X-Powered-By / X-Generator / Set-Cookie 模式
#   - body 里的 meta tag / 全局 JS 变量 / 已知字符串
#   - final URL 的路径模式（如 /identityiq/、/now/、/_layouts/、/wiki/、/jira/）

verdict=""
recipe=""
notes=""

# ─ ServiceNow ─
if grep -qiE 'X-Is-Logged-In|X-Forwarded-Server.*service-now|servicenow' "$TMP_HEADERS" \
   || grep -qiE 'window\.NOW|g_ck|glide_session_store' "$TMP_BODY" \
   || [[ "$URL" == *"service-now.com"* ]]; then
  verdict="ServiceNow"
  recipe="servicenow"
  notes="g_ck (X-UserToken) 是页面 JS 全局变量，需脚本 fetch home_splash.do 抓"

# ─ SailPoint IdentityIQ ─
elif grep -qiE 'identityiq' "$TMP_HEADERS" \
     || [[ "$URL" == *"/identityiq/"* ]] \
     || [[ "$FINAL_URL" == *"/identityiq/"* ]] \
     || grep -qiE 'sailpoint|identityiq' "$TMP_BODY"; then
  verdict="SailPoint IdentityIQ"
  recipe="sailpoint-iiq"
  notes="partitioned cookie (CHIPS) → 扩展端要 content script fallback；X-XSRF-TOKEN double-submit"

# ─ Atlassian (Jira / Confluence) ─
elif grep -qiE 'X-AREQUESTID|X-Confluence|X-Jira-|atlassian' "$TMP_HEADERS" \
     || grep -qiE 'AJS\.|atl_token|X-Atlassian-Token' "$TMP_BODY" \
     || [[ "$URL" == *"atlassian.net"* ]] \
     || [[ "$URL" == *"jira."* ]] || [[ "$URL" == *"wiki."* ]] || [[ "$URL" == *"confluence."* ]]; then
  verdict="Atlassian (Jira / Confluence)"
  recipe="atlassian"
  notes="atl_token / X-Atlassian-Token: no-check 头，REST v2/v3 端点"

# ─ SharePoint / Microsoft 365 ─
elif grep -qiE 'MicrosoftSharePointTeamServices|X-SharePointHealthScore|SPRequestGuid' "$TMP_HEADERS" \
     || [[ "$URL" == *"sharepoint.com"* ]] \
     || [[ "$FINAL_URL" == *"/_layouts/"* ]] \
     || grep -qiE '_spPageContextInfo|RequestDigest' "$TMP_BODY"; then
  verdict="SharePoint"
  recipe="sharepoint"
  notes="POST /_api/contextinfo 拿 RequestDigest，写操作要 X-RequestDigest header"

# ─ ConnectRPC / protobuf-over-HTTP (Buf / Connect 生态、Gitpod Flex) ─
elif grep -qiE 'Connect-Protocol-Version|connect-protocol-version' "$TMP_HEADERS" \
     || grep -qiE '_pb-[A-Za-z0-9_-]+\.js|connectrpc|@connectrpc|Connect-Protocol-Version' "$TMP_BODY" \
     || [[ "$URL" == *"flexdev."* ]] || [[ "$URL" == *"gitpod."* ]]; then
  verdict="ConnectRPC (protobuf-over-HTTP)"
  recipe="connectrpc"
  notes="endpoint /<pkg>.<Service>/<Method>；契约在前端 *_pb*.js bundle（base64 descriptor，用 decode_protobuf_descriptor.py 解）；鉴权头因实例而异"

# ─ 阿里云 / 腾讯云 SPA + localStorage Bearer ─
elif grep -qiE 'Server: Tengine|Ali-Swift|X-Cache.*TCP_HIT' "$TMP_HEADERS" \
     && grep -qiE '<div id="app"|<div id="root"' "$TMP_BODY" \
     && ! grep -qiE 'Set-Cookie:.*JSESSIONID|Set-Cookie:.*PHPSESSID' "$TMP_HEADERS"; then
  verdict="阿里云 SPA + localStorage Bearer（如 nihsc）"
  recipe="bearer-localstorage"
  notes="cookie-bridge 不适用——业务凭据在 localStorage，跳出本框架"

# ─ Generic Spring Boot / Java with JSESSIONID + Bearer ─
elif grep -qiE 'Set-Cookie:.*JSESSIONID' "$TMP_HEADERS" \
     && grep -qiE 'Spring|java' "$TMP_HEADERS"; then
  verdict="Java/Spring Boot 后端"
  recipe="generic-jsessionid"
  notes="JSESSIONID 即 session 凭据；CSRF 看具体框架（Spring Security 默认 _csrf 表单字段）"

# ─ 未识别 ─
else
  verdict="未知"
  echo "── 协议未识别"
  echo "   Server: $(grep -i '^server:' "$TMP_HEADERS" | head -1 | tr -d '\r')"
  echo "   Set-Cookie: $(grep -ic '^set-cookie:' "$TMP_HEADERS") 个"
  echo "   X-Powered-By: $(grep -i '^x-powered-by:' "$TMP_HEADERS" | head -1 | tr -d '\r')"
  echo ""
  echo "   建议: 用 F12 Network 看 XHR 请求的 Authorization header 模式 + Application →"
  echo "         Cookies/LocalStorage 看凭据存哪。如确认是 cookie session，先用 RECIPE"
  echo "         模板 generic-cookie-session 起步，按需加 CSRF 处理。"
  echo "         若属新协议类，请把发现补到 docs/RECIPES.md。"
  exit 1
fi

echo "── 识别为 $verdict"
echo "   RECIPE: $recipe"
echo "   特征: $notes"
echo ""
echo "   client 模板见: demos/browser-cookie-bridge/docs/RECIPES.md#$recipe"
exit 0
