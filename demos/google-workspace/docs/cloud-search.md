# Cloud Search 集成 — RocheHome 内网搜索

通过 Google Cloud Search API 搜索 RocheHome 索引的内容（Google Sites、Drive 文档、Wiki 等），无需浏览器登录。

## 能做什么

- 搜索 Roche 内部系统的官方介绍页（gSite）
- 查找内部文档、培训材料、公告
- 检索 Roche Wiki (Confluence) 内容

## 前置条件

### 1. GCP 项目启用 Cloud Search API

在 [GCP Console](https://console.cloud.google.com/apis/library/cloudsearch.googleapis.com) 启用 Cloud Search API。

### 2. OAuth Consent Screen 添加 scope

在 [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent) → Edit App → Scopes 中添加：

```
https://www.googleapis.com/auth/cloud_search.query
```

### 3. 重新授权

scope 变更后必须重新授权（旧 token 不覆盖新 scope）：

```bash
cd demos/google-workspace
rm /tmp/google_token.json
python3 scripts/auth.py
```

授权完成后将新 token 更新到 Ona Secret `GOOGLE_TOKEN_JSON`。

## 认证机制

认证和 Token 管理的通用机制见 [架构文档](architecture.md)。

## 使用示例

```python
from scripts.gw_client import get_credentials
import requests

creds = get_credentials()

resp = requests.post(
    'https://cloudsearch.googleapis.com/v1/query/search',
    headers={'Authorization': f'Bearer {creds.token}'},
    json={
        'query': 'ROMINE Roche literature',
        'pageSize': 5,
        'requestOptions': {
            'searchApplicationId': 'searchapplications/default'
        }
    }
)

for item in resp.json().get('results', []):
    title = item.get('title', '?')
    snippet = item.get('snippet', {}).get('snippet', '')[:200]
    # 从 Google redirect URL 提取实际链接
    import urllib.parse
    raw_url = item.get('url', '')
    params = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
    url = params.get('url', [raw_url])[0]
    
    print(f'{title}\n  {url}\n  {snippet}\n')
```

## Scope 管理

新增 scope 的完整流程见 [管理员手册 → Scope 管理](admin-guide.md#scope-管理)。

## 局限

- Cloud Search 只能搜索 RocheHome 已索引的内容（Google Sites、Drive、Wiki），不覆盖所有 Roche 内部系统
- 搜索结果的 URL 是 Google redirect 链接，需要解析 `url` 参数获取实际地址
- 返回的 snippet 是 HTML 片段（含 `&nbsp;`、`&#39;` 等），需要清理
