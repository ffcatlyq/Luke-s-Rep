// Browser Cookie Bridge - background service worker (MV3)
//
// 职责:
//   1. 接收 popup 的 syncNow 消息 → 抓 cookie → POST receiver
//   2. 监听 chrome.cookies.onChanged → 配置启用 auto-sync 时自动推送
//   3. Keep-alive：周期性 fetch 目标应用的轻量 endpoint，让 ServiceNow 服务端
//      session 不 idle out。心跳触发 Set-Cookie，cookies.onChanged 自动续 sync。
//   4. POST 失败时把 action badge 染红，popup 打开时能看到状态
//
// 不做:
//   · 不存 cookie 值（chrome.cookies API 返回的就是当前浏览器状态）
//   · 不存 token 到任何持久层（token 在 chrome.storage.local，仅扩展自己读得到）

const STATE_KEY = "bridgeConfig";
const LAST_SYNC_KEY = "lastSync";
const LAST_KEEPALIVE_KEY = "lastKeepAlive";

// 简单的 per-service debounce，避免 onChanged 风暴
const debounceTimers = new Map();
const DEBOUNCE_MS = 500;

// Keep-alive 周期。20 分钟选择见 docs/ARCHITECTURE.md decision 11：
// ServiceNow 默认 idle timeout 30 分钟（glide.ui.session_timeout），20 留 10 分钟
// buffer 给 alarm jitter 和实例可能的非默认配置。
const KEEPALIVE_INTERVAL_MIN = 20;
const KEEPALIVE_ALARM_PREFIX = "keepalive:";

// keep-alive 的 endpoint 不再硬编码——从 receiver config 读，扩展通过 /health 拉到
// services_detail.{service}.keepAlivePath 后存到 chrome.storage.local。新增 service
// 加 keep-alive 不用改扩展代码，只改 receiver/config.json。
//
// 验证新 endpoint 的标准（在浏览器 F12 console 跑 fetch 一次）：
//   - status 200
//   - final URL 不含 logout_redirect / login.jsp / login.jsf / loginpage / saml 关键字
//   - 不含 /500.jsf / /exception.jsf（SailPoint 异常页）等"endpoint 不存在"的标记
//
// 已验证可用：
//   - servicenow → /now/nav/ui/classic/params/target/home_splash.do
//   - cidm → /identityiq/home.jsf

const CAPTURED_BEARER_KEY = "capturedBearer";

async function getConfig() {
  const obj = await chrome.storage.local.get([STATE_KEY]);
  return obj[STATE_KEY] || null;
}

// ── Bearer 捕获 ──────────────────────────────────────────────
// 部分应用（DevHub/Backstage）API 调用要短效 Bearer，cookie 不够，且 token 只在页面
// 内存（不在 localStorage，也不能靠脚本自己 refresh——refresh-token 是一次性轮换的）。
// 唯一干净抓法：观察页面自己发出的 API 请求，搭便车读 Authorization: Bearer 头。
// 页面负责续期，扩展只读不碰 refresh-token。captureBearer:true 的 service 才挂监听。
//
// 隐私：只在内存/storage.local 暂存最近一个 Bearer（仅扩展可读），随下次该 service 的
// sync 一起 POST 给本地 receiver；不持久化到别处、不发往 build.roche.com 以外。
function bearerListener(details) {
  const h = details.requestHeaders || [];
  for (const header of h) {
    if (header.name.toLowerCase() === "authorization" && /^Bearer\s+/i.test(header.value || "")) {
      const token = header.value.replace(/^Bearer\s+/i, "").trim();
      if (token.length > 20) {
        chrome.storage.local.set({
          [CAPTURED_BEARER_KEY]: { token, host: new URL(details.url).host, ts: Date.now() },
        });
      }
      break;
    }
  }
}

// 给配了 captureBearer 的 service 的域装 webRequest 监听（幂等：先移除再加）。
async function setupBearerCapture() {
  const cfg = await getConfig();
  try {
    chrome.webRequest.onBeforeSendHeaders.removeListener(bearerListener);
  } catch (_) { /* 没装过 */ }
  if (!cfg || !cfg.services) return;
  const urls = [];
  for (const svc of Object.values(cfg.services)) {
    if (svc.captureBearer) {
      for (const d of svc.domains || []) {
        urls.push(`https://${d.replace(/^\./, "")}/api/*`);
      }
    }
  }
  if (urls.length === 0) return;
  chrome.webRequest.onBeforeSendHeaders.addListener(
    bearerListener,
    { urls },
    ["requestHeaders"],
  );
}

async function getCapturedBearer(maxAgeMs = 30 * 60 * 1000) {
  const obj = await chrome.storage.local.get([CAPTURED_BEARER_KEY]);
  const b = obj[CAPTURED_BEARER_KEY];
  if (!b || !b.token) return null;
  if (Date.now() - (b.ts || 0) > maxAgeMs) return null; // 太旧不用，避免发过期 token
  return b.token;
}

async function setBadge(text, color) {
  try {
    await chrome.action.setBadgeText({ text });
    if (color) await chrome.action.setBadgeBackgroundColor({ color });
  } catch (e) {
    // ignore badge errors
  }
}

async function recordLastSync(service, ok, info) {
  const obj = await chrome.storage.local.get([LAST_SYNC_KEY]);
  const last = obj[LAST_SYNC_KEY] || {};
  last[service] = { ok, ts: Date.now(), info };
  await chrome.storage.local.set({ [LAST_SYNC_KEY]: last });
}

// 把 chrome.cookies API 返回的对象转成 receiver 期望的 schema
function normalizeCookie(c) {
  return {
    name: c.name,
    value: c.value,
    domain: c.domain,
    path: c.path,
    secure: !!c.secure,
    httpOnly: !!c.httpOnly,
    sameSite: c.sameSite || "no_restriction",
    expires: c.session ? null : (c.expirationDate ? Math.floor(c.expirationDate) : null),
  };
}

// 抓某个 service 配置下所有目标域的 cookie。
//
// 用 {url} 而非 {domain}：url 模式让 Chrome 按 RFC cookie matching 决定哪些 cookie 属于该 URL，
// 包括子域和父域设的 cookie（如 ".service-now.com" 顶级域 cookie 也能被 https://roche.service-now.com/ 拿到）。
// 对应做一次去重，因为同一 cookie 可能在多个 url 里都返回。
//
// 三层抓取（互补，处理 chrome.cookies API 的盲区）：
//   1. {url} 模式：含父域，按 RFC path-prefix 匹配
//   2. {domain} 模式：拿 path-restricted（如 JSESSIONID path=/identityiq）
//   3. content script document.cookie：补 partitioned cookie（CHIPS）—— Chrome 的
//      chrome.cookies API 系统性不返回 partitioned cookie，但页面 JS 用 document.cookie
//      能看到。SailPoint Angular 的 XSRF-TOKEN 走这条路才能拿到。需要 service 的 tab 打开。
async function collectCookies(service, cfg) {
  const svc = (cfg.services || {})[service];
  if (!svc) throw new Error(`unknown service: ${service}`);
  const seen = new Map();  // key: name|domain|path → cookie
  for (const domain of svc.domains) {
    const url = `https://${domain.replace(/^\./, "")}/`;
    const items = await chrome.cookies.getAll({ url });
    for (const it of items) {
      const key = `${it.name}|${it.domain}|${it.path}`;
      if (!seen.has(key)) seen.set(key, normalizeCookie(it));
    }
    const more = await chrome.cookies.getAll({ domain });
    for (const it of more) {
      const key = `${it.name}|${it.domain}|${it.path}`;
      if (!seen.has(key)) seen.set(key, normalizeCookie(it));
    }
    // content script fallback —— 只补 chrome.cookies API 没拿到的 name，避免覆盖更准的元数据
    try {
      const fromPage = await collectCookiesFromPage(domain);
      const knownNames = new Set(Array.from(seen.values()).map((c) => c.name));
      for (const c of fromPage) {
        if (knownNames.has(c.name)) continue;
        const key = `${c.name}|${c.domain}|${c.path}`;
        seen.set(key, c);
      }
    } catch (_) {
      // tab 不存在 / 注入失败 / 页面无 document.cookie 都不致命，主体仍由 chrome.cookies API 提供
    }
  }
  return Array.from(seen.values());
}

// 在 service 的某个打开 tab 内执行 document.cookie，parse 后返回。
// 用于补 chrome.cookies API 看不到的 partitioned cookie（CHIPS）。
async function collectCookiesFromPage(domain) {
  const host = domain.replace(/^\./, "");
  const tabs = await chrome.tabs.query({ url: `https://${host}/*` });
  if (tabs.length === 0) return [];
  let scriptResults;
  try {
    scriptResults = await chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: () => document.cookie,
    });
  } catch (_) {
    return [];
  }
  const raw = scriptResults?.[0]?.result;
  if (!raw || typeof raw !== "string") return [];
  const out = [];
  for (const part of raw.split(/;\s*/)) {
    const idx = part.indexOf("=");
    if (idx <= 0) continue;
    const name = part.slice(0, idx).trim();
    const value = part.slice(idx + 1);
    if (!name) continue;
    // document.cookie 不给元数据，只能用页面 host 做 domain 标记。这样 receiver
    // 端 RFC 6265 matching 一定通过。secure 假定 true（cidm 这类内网站点都是 https）。
    out.push({
      name,
      value,
      domain: host,
      path: "/",
      secure: true,
      httpOnly: false,
      sameSite: "no_restriction",
      expires: null,
    });
  }
  return out;
}

// ── Transports ──────────────────────────────────────────────────
// cookie-bridge 有两条数据出口，是「路由」不是「failover」：
//   · local  —— POST 127.0.0.1:36984 receiver → ~/.config。receiver 跑在哪都行：
//               build-cli 本地（WSL/mac），或 VSCode-SSH 连 Ona 时容器里的 receiver
//               （VSCode 把容器 36984 转发到 Windows localhost，浏览器 POST 直穿隧道）
//   · gdrive —— AES-GCM 加密 → Drive .cookie-bridge/<service>.enc → Ona 容器消费（gdrive_cookie_sync.py）
//               纯浏览器用 Ona（无 SSH 端口转发）时走这条
// 两条独立成败、互不阻塞：一端挂不影响另一端（修复了「任一目的地失败=整体失败」的旧根因）。
// 默认只开 local（向后兼容）；gdrive 由用户在 popup 勾选 + 配 passphrase。

// 兼容未迁移的老配置（用户升级后没开过 popup、auto-sync 用 getConfig 读原始 schema）：
// 无 localReceivers 但有旧 receiverUrl → 合成一条，enabled 沿用旧 transports.local。
function effectiveLocalReceivers(cfg) {
  if (Array.isArray(cfg.localReceivers)) return cfg.localReceivers;
  if (cfg.receiverUrl) {
    const en = !cfg.transports || cfg.transports.local !== false;
    return [{ url: cfg.receiverUrl, enabled: en, label: "default" }];
  }
  return [];
}

function getEnabledTransports(cfg) {
  const t = cfg.transports || {};
  // local 出口 = 有任一启用的 local receiver（不再靠单独的 transports.local 开关）
  const anyLocal = effectiveLocalReceivers(cfg).some((r) => r && r.enabled && r.url);
  return { local: anyLocal, gdrive: !!t.gdrive };
}

// ── gdrive transport：加密信封（与 receiver/cookie_crypto.py 同契约）─────
// AES-256-GCM + PBKDF2-SHA256 + 固定 AAD。WebCrypto 输出 = ciphertext||tag，Python 端直接吃。
const GDRIVE_AAD = "cookie-bridge-v1";
const GDRIVE_ITER = 200000;
const GDRIVE_FOLDER = ".cookie-bridge";
const GDRIVE_FOLDER_MIME = "application/vnd.google-apps.folder";

function _b64(buf) {
  const bytes = new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}

async function _deriveAesKey(passphrase, salt) {
  const baseKey = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(passphrase), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: GDRIVE_ITER, hash: "SHA-256" },
    baseKey, { name: "AES-GCM", length: 256 }, false, ["encrypt"]);
}

async function encryptEnvelope(passphrase, plaintextBytes) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await _deriveAesKey(passphrase, salt);
  const ctWithTag = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv, additionalData: new TextEncoder().encode(GDRIVE_AAD), tagLength: 128 },
    key, plaintextBytes);
  return {
    v: 1, alg: "AES-256-GCM",
    kdf: { name: "PBKDF2", hash: "SHA-256", iter: GDRIVE_ITER },
    aad: GDRIVE_AAD, salt: _b64(salt), iv: _b64(iv), ct: _b64(ctWithTag),
  };
}

function getGoogleToken(interactive) {
  return new Promise((resolve, reject) => {
    chrome.identity.getAuthToken({ interactive: !!interactive }, (token) => {
      if (chrome.runtime.lastError || !token) {
        reject(new Error(chrome.runtime.lastError?.message || "no token (配 OAuth client_id + 登录 Google)"));
      } else resolve(token);
    });
  });
}

async function driveFetch(token, url, opts = {}) {
  const resp = await fetch(url, {
    ...opts,
    headers: { Authorization: `Bearer ${token}`, ...(opts.headers || {}) },
  });
  if (!resp.ok) {
    const t = await resp.text();
    throw new Error(`Drive HTTP ${resp.status}: ${t.slice(0, 160)}`);
  }
  return resp.json();
}

async function driveFindOrCreateFolder(token) {
  const q = encodeURIComponent(
    `name='${GDRIVE_FOLDER}' and mimeType='${GDRIVE_FOLDER_MIME}' and trashed=false and 'me' in owners`);
  const list = await driveFetch(token,
    `https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id)&spaces=drive`);
  if (list.files && list.files.length) return list.files[0].id;
  const created = await driveFetch(token,
    "https://www.googleapis.com/drive/v3/files?fields=id",
    { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: GDRIVE_FOLDER, mimeType: GDRIVE_FOLDER_MIME }) });
  return created.id;
}

// 即焚契约下稳态恒为 create：消费端读完即删，下次 sync 时旧文件已不在。
// 但若上一份还没被消费（Ona 未跑），同名文件会残留 → 先删同名再 create，避免堆两份。
async function driveUploadEnc(token, folderId, service, envelopeStr) {
  const q = encodeURIComponent(
    `name='${service}.enc' and '${folderId}' in parents and trashed=false`);
  const existing = await driveFetch(token,
    `https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id)&spaces=drive`);
  for (const f of existing.files || []) {
    await fetch(`https://www.googleapis.com/drive/v3/files/${f.id}`,
      { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
  }
  const boundary = "cbBoundary" + Math.floor(performance.now());
  const metadata = { name: `${service}.enc`, parents: [folderId] };
  const body =
    `--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n` +
    `${JSON.stringify(metadata)}\r\n` +
    `--${boundary}\r\nContent-Type: application/octet-stream\r\n\r\n` +
    `${envelopeStr}\r\n--${boundary}--`;
  return driveFetch(token,
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name",
    { method: "POST",
      headers: { "Content-Type": `multipart/related; boundary=${boundary}` },
      body });
}

// 单个 local receiver 的 POST。带 5s 超时（AbortSignal.timeout）——接不通 / receiver 挂死时
// 快速报错，不再无限挂（旧 bug：无超时 → 卡死一个拖垮整次 sync、popup 永远 syncing）。
async function syncOneLocal(url, token, body) {
  let resp;
  try {
    resp = await fetch(`${url}/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    });
  } catch (e) {
    const msg = e.name === "TimeoutError"
      ? "timeout：receiver 未响应（没起 / 端口没转发？）"
      : `network: ${e.message}`;
    return { ok: false, error: msg };
  }
  let data = {};
  try { data = await resp.json(); } catch (_) { /* ignore */ }
  if (!resp.ok || !data.ok) {
    return { ok: false, error: data.error || `HTTP ${resp.status}` };
  }
  return { ok: true, cookie_count: data.cookie_count, written: data.written, token_written: data.token_written };
}

// 扇出到所有 enabled 的 local receiver（共享 cfg.token）。并行发、各自成败、互不阻塞。
// 返回数组 [{label, url, ok, ...}]。
async function syncLocalAll(cfg, body) {
  const list = effectiveLocalReceivers(cfg).filter((r) => r && r.enabled && r.url);
  if (!cfg.token) return [{ label: "local", ok: false, error: "缺 token" }];
  if (list.length === 0) return [{ label: "local", ok: false, error: "没有启用的 local receiver" }];
  return Promise.all(list.map(async (r) => {
    const res = await syncOneLocal(r.url, cfg.token, body);
    return { label: r.label || r.url, url: r.url, ...res };
  }));
}

async function syncGdrive(cfg, service, body, interactive) {
  const passphrase = cfg.gdrivePassphrase;
  if (!passphrase) return { ok: false, error: "gdrive 缺 passphrase（popup 里填）" };
  let token;
  try {
    token = await getGoogleToken(interactive);
  } catch (e) {
    return { ok: false, error: `getAuthToken: ${e.message}` };
  }
  try {
    const plaintext = new TextEncoder().encode(JSON.stringify(body));
    const envelope = await encryptEnvelope(passphrase, plaintext);
    const folderId = await driveFindOrCreateFolder(token);
    const res = await driveUploadEnc(token, folderId, service, JSON.stringify(envelope));
    return { ok: true, fileId: res.id, name: res.name };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

// sync：遍历启用的 transport，各自独立成败、互不阻塞。interactive 控制 gdrive 是否允许弹 Google 登录
// （popup 手动 Sync Now → true；auto-sync / keep-alive 后台触发 → false，拿缓存 token，没有就跳过 gdrive）。
async function sync(service, interactive = false) {
  const cfg = await getConfig();
  if (!cfg) {
    return { ok: false, error: "no config (open popup to set up)" };
  }
  if (!cfg.services || !cfg.services[service]) {
    return { ok: false, error: `service "${service}" not in config` };
  }

  const enabled = getEnabledTransports(cfg);
  if (!enabled.local && !enabled.gdrive) {
    return { ok: false, error: "no transport enabled（popup 勾选 Local / Google Drive）" };
  }

  let cookies;
  try {
    cookies = await collectCookies(service, cfg);
  } catch (e) {
    return { ok: false, error: `collect failed: ${e.message}` };
  }

  // captureBearer 的 service：把最近观察到的页面 Bearer 一起带上（两条 transport 都带，落盘端按 tokenOutput 决定写不写）
  const body = { service, cookies };
  if (cfg.services[service].captureBearer) {
    const bearer = await getCapturedBearer();
    if (bearer) body.bearer = bearer;
  }

  // 各 transport 独立跑、独立成败。local 可扇出多个 receiver（数组）、gdrive 单个。
  const results = {};
  if (enabled.local) results.local = await syncLocalAll(cfg, body);
  if (enabled.gdrive) results.gdrive = await syncGdrive(cfg, service, body, interactive);

  // 展平成一维 run 列表统计（local 是数组、gdrive 是单对象）
  const flat = [];
  if (results.local) flat.push(...results.local);
  if (results.gdrive) flat.push({ label: "gdrive", ...results.gdrive });
  const okCount = flat.filter((r) => r.ok).length;
  const allOk = flat.length > 0 && okCount === flat.length;
  const anyOk = okCount > 0;

  // badge：全绿 OK / 部分 PART / 全挂 ERR
  if (allOk) {
    await setBadge("OK", "#0b8043");
    setTimeout(() => setBadge("", null), 5000);
  } else if (anyOk) {
    await setBadge("PART", "#cc7700");
  } else {
    await setBadge("ERR", "#cc0000");
  }

  // per-service 状态行：每个目的地各报一段
  const info = flat.map((r) =>
    r.ok ? `${r.label} OK` : `${r.label} ERR: ${r.error}`).join(" · ");
  await recordLastSync(service, anyOk, `${cookies.length} cookies | ${info}`);

  return { ok: allOk, any: anyOk, cookie_count: cookies.length, results };
}

// ── Keep-alive ──────────────────────────────────────────────────
//
// 工作流：
//   alarm 触发 → fetch ServiceNow KEEPALIVE_PATHS[service]（带浏览器 cookie，无需 X-UserToken）
//     → 200 OK 且 final URL 不含 logout_redirect / login 关键字：服务端 session 续期，
//        Set-Cookie 滑动 glide_session_store → chrome.cookies.onChanged 自动触发现有
//        auto-sync → 本地文件刷新
//     → 401 / 403 / final URL 含失效关键字 / 异常：cookie 已废，标记失败 + 染红 badge

// 失效信号关键字。final URL 含这些 → cookie 失效或被踢出
const KEEPALIVE_LOGOUT_MARKERS = ["logout_redirect", "/login.do", "/login.jsp", "loginpage", "saml"];

async function runKeepAlive(service) {
  const cfg = await getConfig();
  if (!cfg || !cfg.keepAlive) return;
  const svc = (cfg.services || {})[service];
  if (!svc || !svc.domains || svc.domains.length === 0) return;
  const path = svc.keepAlivePath;
  if (!path) {
    await recordLastKeepAlive(service, false, `service "${service}" 没配 keepAlivePath`);
    return;
  }
  const url = `https://${svc.domains[0].replace(/^\./, "")}${path}`;

  let resp;
  try {
    // credentials: "include" 让浏览器把目标域 cookie 自动带上。
    // redirect: "follow" 让 fetch 跟完所有 redirect 拿最终 URL —— 用 final URL 判失效，
    // 比 manual + 看 status code 准（很多 SN endpoint 内部有合法 302 跳转，manual 模式会误判）。
    resp = await fetch(url, {
      method: "GET",
      credentials: "include",
      redirect: "follow",
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
  } catch (e) {
    // "Failed to fetch" 在 keep-alive 场景多半不是真网络故障——服务端发现
    // session 死了 302 到外部 IDP（accounts.google.com / wam.roche.com /
    // login.microsoftonline.com 等），fetch 默认 redirect:follow 跟过去后
    // 被 IDP CORS 拦截抛 TypeError("Failed to fetch")。chrome://extensions
    // 错误页会留 log，但语义其实是"session 已失效，需要重登 SSO"
    const msg = (e && e.message) || String(e);
    const isLikelySsoRedirect = /failed to fetch/i.test(msg);
    await setBadge("KA!", "#cc0000");
    await recordLastKeepAlive(
      service,
      false,
      isLikelySsoRedirect ? "SSO 失效：浏览器重登 + Sync Now" : `network: ${msg}`,
    );
    return;
  }

  if (resp.status === 401 || resp.status === 403) {
    await setBadge("KA!", "#cc0000");
    await recordLastKeepAlive(service, false, `HTTP ${resp.status}`);
    return;
  }
  // final URL 落在 logout / SAML 登录页 → 服务端 session 已废
  const finalUrl = (resp.url || "").toLowerCase();
  for (const marker of KEEPALIVE_LOGOUT_MARKERS) {
    if (finalUrl.includes(marker)) {
      await setBadge("KA!", "#cc0000");
      await recordLastKeepAlive(service, false, `logout-redirect (${marker})`);
      return;
    }
  }
  if (resp.status !== 200) {
    await setBadge("KA?", "#cc7700");
    await recordLastKeepAlive(service, false, `HTTP ${resp.status}`);
    return;
  }
  await recordLastKeepAlive(service, true, `${path} → 200`);
  // 不染绿 badge，避免跟 sync OK 混淆。badge 只在错误时染色。
}

async function recordLastKeepAlive(service, ok, info) {
  const obj = await chrome.storage.local.get([LAST_KEEPALIVE_KEY]);
  const last = obj[LAST_KEEPALIVE_KEY] || {};
  last[service] = { ok, ts: Date.now(), info };
  await chrome.storage.local.set({ [LAST_KEEPALIVE_KEY]: last });
}

// 同步现有 services 的 keep-alive alarms 跟 cfg.keepAlive 一致。
// 重启 service worker / 修改配置后都会调一次。
async function syncKeepAliveAlarms() {
  const cfg = await getConfig();
  const existing = await chrome.alarms.getAll();
  const wanted = new Set();
  if (cfg && cfg.keepAlive && cfg.services) {
    for (const [service, svc] of Object.entries(cfg.services)) {
      if (svc && svc.keepAlivePath) wanted.add(`${KEEPALIVE_ALARM_PREFIX}${service}`);
    }
  }
  // 清掉不该有的 alarm
  for (const a of existing) {
    if (a.name.startsWith(KEEPALIVE_ALARM_PREFIX) && !wanted.has(a.name)) {
      await chrome.alarms.clear(a.name);
    }
  }
  // 加上该有但还没建的 alarm
  const existingNames = new Set(existing.map((a) => a.name));
  for (const name of wanted) {
    if (!existingNames.has(name)) {
      // delayInMinutes: 让心跳在 KEEPALIVE_INTERVAL_MIN 后第一次跑（不立刻），
      // 避免 popup 频繁切换造成密集 fetch
      chrome.alarms.create(name, {
        delayInMinutes: KEEPALIVE_INTERVAL_MIN,
        periodInMinutes: KEEPALIVE_INTERVAL_MIN,
      });
    }
  }
}

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (!alarm.name.startsWith(KEEPALIVE_ALARM_PREFIX)) return;
  const service = alarm.name.slice(KEEPALIVE_ALARM_PREFIX.length);
  await runKeepAlive(service);
});

// 配置变化时刷新 alarms（popup 改 keep-alive 开关或 service 列表）+ 重挂 Bearer 捕获
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") return;
  if (changes[STATE_KEY]) {
    syncKeepAliveAlarms().catch(() => {});
    setupBearerCapture().catch(() => {});
  }
});

// service worker 启动 / 安装时初始化一次
chrome.runtime.onStartup.addListener(() => {
  syncKeepAliveAlarms().catch(() => {});
  setupBearerCapture().catch(() => {});
});
chrome.runtime.onInstalled.addListener(() => {
  syncKeepAliveAlarms().catch(() => {});
  setupBearerCapture().catch(() => {});
});
syncKeepAliveAlarms().catch(() => {});
setupBearerCapture().catch(() => {});

// popup 消息入口
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg && msg.action === "syncNow" && msg.service) {
    // popup 手动触发：interactive=true，允许 gdrive 首次弹 Google 登录窗
    sync(msg.service, true).then(sendResponse);
    return true; // async response
  }
  if (msg && msg.action === "keepAliveNow" && msg.service) {
    // popup 手动触发一次心跳（用来验证配置是否通）
    runKeepAlive(msg.service).then(() => sendResponse({ ok: true })).catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }
  if (msg && msg.action === "ping") {
    sendResponse({ ok: true });
    return false;
  }
  return false;
});

// cookie 变化监听 → auto-sync
chrome.cookies.onChanged.addListener(async (changeInfo) => {
  const cfg = await getConfig();
  if (!cfg || !cfg.autoSync) return;
  const cookieDomain = (changeInfo.cookie?.domain || "").replace(/^\./, "");
  if (!cookieDomain) return;

  // 找出受影响的 service
  for (const [service, svc] of Object.entries(cfg.services || {})) {
    const matched = (svc.domains || []).some((d) => {
      const norm = d.replace(/^\./, "");
      return cookieDomain === norm || cookieDomain.endsWith(`.${norm}`) || norm.endsWith(`.${cookieDomain}`);
    });
    if (!matched) continue;

    // debounce
    if (debounceTimers.has(service)) clearTimeout(debounceTimers.get(service));
    debounceTimers.set(
      service,
      setTimeout(() => {
        debounceTimers.delete(service);
        sync(service).catch(() => {});
      }, DEBOUNCE_MS),
    );
  }
});
