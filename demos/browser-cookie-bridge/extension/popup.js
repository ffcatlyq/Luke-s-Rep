// Browser Cookie Bridge - popup
//
// 职责:
//   - 显示/编辑配置（local receivers 列表、共享 token、service、autoSync、gdrive）
//   - 从 receiver /health 拿 service 列表（不绑死前端）
//   - 触发 syncNow 消息给 background
//   - 显示最近同步状态
//
// local 出口从「单个 receiverUrl」升级为「多个 receiver 扇出」：cfg.localReceivers = [{url,enabled,label}]，
// 共用一个 cfg.token（所有容器的 receiver 用同一 --token 起）。旧 cfg.receiverUrl 自动迁移。

const STATE_KEY = "bridgeConfig";
const LAST_SYNC_KEY = "lastSync";
const LAST_KEEPALIVE_KEY = "lastKeepAlive";
// receiver name 是实时从 /health 拉的、不入 cfg；但缓存上次结果(url→name)到 storage，
// popup 重开时先秒显缓存,再后台刷新——省得每次手动点 ↻ 才出名字。
const LAST_NAMES_KEY = "lastNames";

const $ = (id) => document.getElementById(id);

function setStatus(text, kind) {
  const el = $("status");
  el.textContent = text || "";
  el.className = "status" + (kind ? " " + kind : "");
}

function setKeepAliveStatus(text, kind) {
  const el = $("keepAliveStatus");
  el.textContent = text || "";
  el.className = "status keepalive" + (kind ? " " + kind : "");
}

// gdrive 没勾选时隐藏 passphrase 行
function updateGdriveRow() {
  const row = $("gdrivePassRow");
  if (row) row.style.display = $("tGdrive").checked ? "" : "none";
}

async function loadConfig() {
  const obj = await chrome.storage.local.get([STATE_KEY, LAST_SYNC_KEY, LAST_KEEPALIVE_KEY, LAST_NAMES_KEY]);
  const cfg = obj[STATE_KEY] || {
    localReceivers: [{ url: "http://127.0.0.1:", enabled: true, label: "default" }],
    token: "",
    services: {},
    selectedService: "",
    autoSync: false,
    keepAlive: false,
    transports: { gdrive: false },
    gdrivePassphrase: "",
  };
  // 老配置兼容
  if (cfg.keepAlive === undefined) cfg.keepAlive = false;
  if (!cfg.transports) cfg.transports = { gdrive: false };
  if (cfg.gdrivePassphrase === undefined) cfg.gdrivePassphrase = "";
  // 迁移：单个 receiverUrl → localReceivers 数组（enabled 沿用旧 transports.local）
  if (!Array.isArray(cfg.localReceivers)) {
    cfg.localReceivers = cfg.receiverUrl
      ? [{ url: cfg.receiverUrl, enabled: !cfg.transports || cfg.transports.local !== false, label: "default" }]
      : [];
  }
  return {
    cfg,
    lastSync: obj[LAST_SYNC_KEY] || {},
    lastKeepAlive: obj[LAST_KEEPALIVE_KEY] || {},
    lastNames: obj[LAST_NAMES_KEY] || {},
  };
}

async function saveConfig(cfg) {
  await chrome.storage.local.set({ [STATE_KEY]: cfg });
}

// local receivers 里第一个启用项的 URL —— 用于 /health 拉 service 列表（各 receiver 同 config 同 services）
function firstReceiverUrl(cfg) {
  const list = cfg.localReceivers || [];
  const r = list.find((x) => x && x.enabled && x.url) || list[0];
  return r ? r.url : "";
}

// —— local receivers 动态列表 ——
function addLocalRow(url, enabled, onChange, cachedName) {
  const box = $("localList");
  const row = document.createElement("div");
  row.className = "row check localrow";

  const cb = document.createElement("input");
  cb.type = "checkbox";
  cb.className = "lr-en";
  cb.checked = enabled !== false;

  const inp = document.createElement("input");
  inp.type = "text";
  inp.className = "lr-url";
  inp.placeholder = "http://127.0.0.1:36984";
  inp.value = url || "";

  // receiver 标识：显示「→ name」认得出哪个端口是哪个容器。开局先填缓存(秒显)，
  // 之后 refreshReceiverNames()(popup 打开时自动跑一次 + 点 ↻)从各行 /health 拉最新覆盖。
  const nameEl = document.createElement("span");
  nameEl.className = "lr-name";
  if (cachedName) nameEl.textContent = `→ ${cachedName}`;

  const rm = document.createElement("button");
  rm.type = "button";
  rm.className = "ghost lr-rm";
  rm.textContent = "✕";

  rm.addEventListener("click", () => { row.remove(); if (onChange) onChange(); });
  cb.addEventListener("change", () => { if (onChange) onChange(); });
  // url 改了就清掉旧 name（避免张冠李戴），等下次 ↻ 重新拉
  inp.addEventListener("change", () => { nameEl.textContent = ""; if (onChange) onChange(); });

  row.append(cb, inp, nameEl, rm);
  box.appendChild(row);
}

function renderLocalReceivers(cfg, onChange, cachedNames) {
  const box = $("localList");
  box.innerHTML = "";
  const names = cachedNames || {};
  const list = (cfg.localReceivers && cfg.localReceivers.length)
    ? cfg.localReceivers
    : [{ url: "", enabled: true }];
  for (const r of list) addLocalRow(r.url || "", r.enabled !== false, onChange, names[r.url]);
}

function collectLocalReceivers() {
  const out = [];
  document.querySelectorAll("#localList .localrow").forEach((row) => {
    const url = row.querySelector(".lr-url").value.trim().replace(/\/+$/, "");
    const enabled = row.querySelector(".lr-en").checked;
    if (url) out.push({ url, enabled, label: url.replace(/^https?:\/\//, "") });
  });
  return out;
}

function renderServiceOptions(cfg) {
  const sel = $("service");
  sel.innerHTML = "";
  const names = Object.keys(cfg.services || {});
  if (names.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "(refresh from receiver)";
    sel.appendChild(opt);
    return;
  }
  for (const name of names) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    if (name === cfg.selectedService) opt.selected = true;
    sel.appendChild(opt);
  }
}

function renderKeepAliveLabel(cfg) {
  const el = $("keepAliveLabel");
  if (!el) return;
  const services = cfg.services || {};
  const enabled = Object.entries(services)
    .filter(([_, svc]) => svc && svc.keepAlivePath)
    .map(([name]) => name);
  if (enabled.length === 0) {
    el.textContent = "Keep-alive (20 min, no service configured)";
  } else {
    el.textContent = `Keep-alive (20 min: ${enabled.join(", ")})`;
  }
}

async function refreshServicesFromReceiver(cfg) {
  const base = firstReceiverUrl(cfg);
  if (!base) {
    setStatus("先加一个 local receiver（填 URL）", "err");
    return cfg;
  }
  try {
    const r = await fetch(`${base}/health`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    if (!Array.isArray(data.services)) throw new Error("bad /health response");
    const services = {};
    // 优先用 services_detail（含 domains + 可选 keepAlivePath），兼容旧 receiver 只返回 services 名字列表的情况。
    if (data.services_detail && typeof data.services_detail === "object") {
      for (const [name, meta] of Object.entries(data.services_detail)) {
        const entry = { domains: Array.isArray(meta.domains) ? meta.domains : [] };
        if (meta.keepAlivePath) entry.keepAlivePath = meta.keepAlivePath;
        if (meta.captureBearer) entry.captureBearer = true;
        services[name] = entry;
      }
    } else {
      for (const name of data.services) {
        services[name] = { domains: [] };
      }
    }
    cfg.services = services;
    if (!cfg.selectedService || !(cfg.selectedService in services)) {
      cfg.selectedService = data.services[0] || "";
    }
    await saveConfig(cfg);
    renderServiceOptions(cfg);
    renderKeepAliveLabel(cfg);
    setStatus(`receiver OK: ${data.services.join(", ")}`, "ok");
  } catch (e) {
    const msg = e.name === "TimeoutError" ? "timeout（receiver 没起 / 端口没转发？）" : e.message;
    setStatus(`receiver 不可达: ${msg}`, "err");
  }
  return cfg;
}

// 逐行拉各 receiver 的 /health.name，在行内显示「→ name」。
// service 列表只从首个 receiver 拉（各 receiver 同 config），但 name 每个容器不同，得逐行拉。
async function refreshReceiverNames() {
  const rows = document.querySelectorAll("#localList .localrow");
  const names = {};  // url→name，拉到的写回 storage 缓存供下次开局秒显
  await Promise.all(Array.from(rows).map(async (row) => {
    const nameEl = row.querySelector(".lr-name");
    const url = row.querySelector(".lr-url").value.trim().replace(/\/+$/, "");
    if (!nameEl) return;
    if (!url) { nameEl.textContent = ""; return; }
    // 有缓存就保留旧值(避免刷新瞬间闪成 …)，无缓存才显占位
    if (!nameEl.textContent) nameEl.textContent = "→ …";
    try {
      const r = await fetch(`${url}/health`, { signal: AbortSignal.timeout(5000) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      if (data && data.name) {
        nameEl.textContent = `→ ${data.name}`;
        names[url] = data.name;
      } else {
        nameEl.textContent = "→ ?";
      }
    } catch (_e) {
      nameEl.textContent = "→ ✕";
    }
  }));
  await chrome.storage.local.set({ [LAST_NAMES_KEY]: names });
}

function fmtAgo(ts) {
  if (!ts) return "";
  const sec = Math.floor((Date.now() - ts) / 1000);
  if (sec < 60) return `${sec}s ago`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  return `${Math.floor(sec / 3600)}h ago`;
}

function renderLastSync(service, lastSync) {
  const item = lastSync && lastSync[service];
  if (!item) {
    setStatus("");
    return;
  }
  const prefix = item.ok ? "OK" : "ERR";
  setStatus(`[${prefix}] ${fmtAgo(item.ts)}\n${item.info || ""}`, item.ok ? "ok" : "err");
}

function renderLastKeepAlive(service, lastKeepAlive) {
  const item = lastKeepAlive && lastKeepAlive[service];
  if (!item) {
    setKeepAliveStatus("");
    return;
  }
  const prefix = item.ok ? "KA OK" : "KA ERR";
  setKeepAliveStatus(`[${prefix}] ${fmtAgo(item.ts)}  ${item.info || ""}`, item.ok ? "ok" : "err");
}

async function init() {
  let { cfg, lastSync, lastKeepAlive, lastNames } = await loadConfig();

  $("token").value = cfg.token || "";
  $("autoSync").checked = !!cfg.autoSync;
  $("keepAlive").checked = !!cfg.keepAlive;
  $("tGdrive").checked = !!(cfg.transports && cfg.transports.gdrive);
  $("gdrivePass").value = cfg.gdrivePassphrase || "";
  updateGdriveRow();

  const persistLocal = async () => {
    cfg.localReceivers = collectLocalReceivers();
    await saveConfig(cfg);
  };
  renderLocalReceivers(cfg, persistLocal, lastNames);

  renderServiceOptions(cfg);
  renderKeepAliveLabel(cfg);
  if (cfg.selectedService) {
    renderLastSync(cfg.selectedService, lastSync);
    renderLastKeepAlive(cfg.selectedService, lastKeepAlive);
  }

  $("addReceiver").addEventListener("click", () => addLocalRow("http://127.0.0.1:", true, persistLocal));

  $("toggleToken").addEventListener("click", () => {
    const inp = $("token");
    inp.type = inp.type === "password" ? "text" : "password";
    $("toggleToken").textContent = inp.type === "password" ? "show" : "hide";
  });

  $("refreshServices").addEventListener("click", async () => {
    cfg.localReceivers = collectLocalReceivers();
    cfg.token = $("token").value.trim();
    cfg = await refreshServicesFromReceiver(cfg);   // service 列表（首个 receiver）
    await refreshReceiverNames();                    // 每行「端口 → name」（逐行）
  });

  $("service").addEventListener("change", async () => {
    cfg.selectedService = $("service").value;
    await saveConfig(cfg);
    const obj = await chrome.storage.local.get([LAST_SYNC_KEY, LAST_KEEPALIVE_KEY]);
    renderLastSync(cfg.selectedService, obj[LAST_SYNC_KEY] || {});
    renderLastKeepAlive(cfg.selectedService, obj[LAST_KEEPALIVE_KEY] || {});
  });

  $("autoSync").addEventListener("change", async () => {
    cfg.autoSync = $("autoSync").checked;
    await saveConfig(cfg);
    setStatus(cfg.autoSync ? "Auto-sync ON" : "Auto-sync OFF", "ok");
  });

  $("keepAlive").addEventListener("change", async () => {
    cfg.keepAlive = $("keepAlive").checked;
    if (cfg.keepAlive && !cfg.autoSync) {
      // keep-alive 强烈建议跟 auto-sync 一起用，否则心跳后续期的 cookie 不会落到本地文件
      cfg.autoSync = true;
      $("autoSync").checked = true;
    }
    await saveConfig(cfg);
    setKeepAliveStatus(cfg.keepAlive ? "Keep-alive ON (20 min)" : "Keep-alive OFF", "ok");
  });

  const persistGdrive = async () => {
    cfg.transports = { gdrive: $("tGdrive").checked };
    cfg.gdrivePassphrase = $("gdrivePass").value;
    await saveConfig(cfg);
  };

  $("tGdrive").addEventListener("change", async () => {
    updateGdriveRow();
    await persistGdrive();
    setStatus($("tGdrive").checked ? "Google Drive 出口 ON（填 passphrase）" : "Google Drive 出口 OFF", "ok");
  });

  $("gdrivePass").addEventListener("change", persistGdrive);

  $("toggleGdrivePass").addEventListener("click", () => {
    const inp = $("gdrivePass");
    inp.type = inp.type === "password" ? "text" : "password";
    $("toggleGdrivePass").textContent = inp.type === "password" ? "show" : "hide";
  });

  $("keepAliveNow").addEventListener("click", async () => {
    if (!cfg.selectedService) {
      setKeepAliveStatus("先选 service", "err");
      return;
    }
    setKeepAliveStatus("testing...", null);
    await chrome.runtime.sendMessage({ action: "keepAliveNow", service: cfg.selectedService });
    // 实际状态由 background 写入 lastKeepAlive，这里重新读
    const obj = await chrome.storage.local.get([LAST_KEEPALIVE_KEY]);
    renderLastKeepAlive(cfg.selectedService, obj[LAST_KEEPALIVE_KEY] || {});
  });

  // Save / Sync Now 都先把 UI 收拢进 cfg（local receivers 列表 + token + 各开关）
  const collectAll = () => {
    cfg.localReceivers = collectLocalReceivers();
    cfg.token = $("token").value.trim();
    cfg.autoSync = $("autoSync").checked;
    cfg.keepAlive = $("keepAlive").checked;
    cfg.transports = { gdrive: $("tGdrive").checked };
    cfg.gdrivePassphrase = $("gdrivePass").value;
  };

  $("save").addEventListener("click", async () => {
    collectAll();
    await saveConfig(cfg);
    setStatus("saved", "ok");
  });

  $("syncNow").addEventListener("click", async () => {
    collectAll();
    cfg.selectedService = $("service").value;
    await saveConfig(cfg);

    if (!cfg.selectedService) {
      setStatus("先选 service", "err");
      return;
    }
    setStatus("syncing...", null);
    const resp = await chrome.runtime.sendMessage({ action: "syncNow", service: cfg.selectedService });
    // 结果：local 是数组（多 receiver 扇出，各自成败）、gdrive 单个。分行展示。
    if (resp && resp.results) {
      const lines = [];
      for (const r of (resp.results.local || [])) {
        lines.push(r.ok ? `${r.label} OK → ${r.written || "ok"}` : `${r.label} ERR: ${r.error}`);
      }
      if (resp.results.gdrive) {
        const g = resp.results.gdrive;
        lines.push(g.ok ? `gdrive OK → Drive ${g.name || g.fileId || "ok"}` : `gdrive ERR: ${g.error}`);
      }
      const kind = resp.ok ? "ok" : (resp.any ? "warn" : "err");
      setStatus(`${resp.cookie_count} cookies\n${lines.join("\n")}`, kind);
    } else {
      setStatus(`ERR: ${(resp && resp.error) || "unknown"}`, "err");
    }
  });

  // popup 打开时如果还没拉过 service 列表，主动拉一次
  if (Object.keys(cfg.services || {}).length === 0 && firstReceiverUrl(cfg)) {
    cfg = await refreshServicesFromReceiver(cfg);
  }
  // popup 打开即自动拉一次各 receiver 的 name（缓存已先秒显，这里后台刷新覆盖），
  // 不用每次手动点 ↻。fire-and-forget，不阻塞 init。
  if (firstReceiverUrl(cfg)) refreshReceiverNames().catch(() => {});
}

init().catch((e) => setStatus(`init error: ${e.message}`, "err"));
