#!/usr/bin/env bash
# ServiceNow demo - WSL2 直连 ServiceNow 不通时的 fallback。
#
# 通过 powershell.exe 反向调 Windows 侧 curl（Windows 网络栈走 RCN/ZScaler，
# 通常能 reach ServiceNow），cookie 文件从 WSL2 ~/.config/servicenow/cookies.json
# 读，转换成 Cookie header 后塞给 Windows curl。
#
# 用法:
#   ./servicenow_via_windows.sh                          # 默认 whoami
#   ./servicenow_via_windows.sh "/api/now/table/incident?sysparm_limit=1"

set -euo pipefail

COOKIE_FILE="${HOME}/.config/servicenow/cookies.json"
ENDPOINT="${1:-/api/now/table/sys_user?sysparm_query=user_name%3Djavascript%3Ags.getUserName%28%29&sysparm_limit=1&sysparm_fields=user_name%2Cname%2Cemail}"

if [[ ! -f "$COOKIE_FILE" ]]; then
  echo "❌ cookie file not found: $COOKIE_FILE" >&2
  echo "   浏览器登录 ServiceNow 后扩展 popup 点 Sync Now" >&2
  exit 1
fi

# 拼 Cookie header: name1=value1; name2=value2
COOKIE_HEADER=$(python3 -c "
import json
data = json.load(open('$COOKIE_FILE'))
parts = [f\"{c['name']}={c['value']}\" for c in data['cookies']]
print('; '.join(parts))
")

if [[ -z "$COOKIE_HEADER" ]]; then
  echo "❌ no cookies in $COOKIE_FILE" >&2
  exit 1
fi

URL="https://roche.service-now.com${ENDPOINT}"
echo "[demo] GET $URL  via Windows curl" >&2

# Windows curl 用单引号传 cookie header，避免 PowerShell 转义混乱
# Invoke-WebRequest 比 curl.exe 的 cookie 处理更稳
RESP=$(powershell.exe -NoProfile -Command "
\$headers = @{ 'Cookie' = '$COOKIE_HEADER'; 'Accept' = 'application/json' }
try {
  \$r = Invoke-WebRequest -Uri '$URL' -Headers \$headers -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 30
  Write-Host 'STATUS:' \$r.StatusCode
  Write-Host '---BODY---'
  Write-Host \$r.Content
} catch {
  if (\$_.Exception.Response) {
    Write-Host 'STATUS:' \$_.Exception.Response.StatusCode.value__
    Write-Host 'LOCATION:' \$_.Exception.Response.Headers['Location']
  } else {
    Write-Host 'ERROR:' \$_.Exception.Message
  }
}
" 2>&1)

echo "$RESP"

if echo "$RESP" | grep -q "STATUS: 302\|LOCATION:.*saml\|LOCATION:.*sso"; then
  echo "" >&2
  echo "❌ 被踢去 SSO 重新登录 → cookie 已失效，浏览器重新登录 ServiceNow 后 Sync Now" >&2
  exit 2
fi
