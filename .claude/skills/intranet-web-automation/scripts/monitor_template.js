/* ============================================================
 * 内网系统状态监控模板（只读，安全）
 * ============================================================
 * 在【目标页自身的 F12 控制台】运行。复用浏览器 SSO/NTLM 登录态。
 * 定时读某状态，达标就三重提醒（红横幅+标题闪烁+系统通知）。
 *
 * 用法：把所有【占位】按目标系统实际值替换（逆向方法见 SKILL.md §2.1），
 *       粘进目标页控制台回车。手动停：clearInterval(window.__monTimer)
 * ============================================================ */
(() => {
  // ── 配置：按目标系统替换 ──────────────────────────────
  const API_URL   = "/GSD/main/PostProcess";              // 【占位】只读接口路径
  const REQ_BODY  = {                                     // 【占位】只读请求 body
    OwnerClass: "GrantManager", OPID: "GetDoneeInfoByID",
    Content: JSON.stringify({ ID: "【占位:记录ID】" }),
    Token: "", FromFlag: 1, Files: null, IsOK: false, ErrorCode: null, ErrorMessage: ""
  };
  const INTERVAL_MS = 3 * 60 * 1000;                      // 轮询间隔（3 分钟）
  // 判断"达标"：从返回里取值并判定。按目标系统改这个函数。
  // 返回 {done:bool, label:string} —— done=true 表示达到提醒条件。
  function evaluate(content) {                            // 【占位】状态判断
    const huc = content.HasUnApprovedCapping;
    return { done: huc === false, label: "HasUnApprovedCapping=" + huc };
  }
  const ALERT_TEXT = "✅ 状态已达标！请去处理";              // 达标时提醒文案

  // ── 提醒（红横幅+标题闪烁+系统通知；不依赖声音）──────────
  const oldTitle = document.title;
  function fireAlerts(text) {
    const b = document.createElement("div");
    b.textContent = text + " — 点我关闭";
    b.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:2147483647;background:red;color:#fff;font-size:22px;font-weight:bold;text-align:center;padding:18px;cursor:pointer;box-shadow:0 2px 12px rgba(0,0,0,.5)";
    b.onclick = () => { b.remove(); if (window.__monTitle) clearInterval(window.__monTitle); document.title = oldTitle; };
    document.body.appendChild(b);
    let flip = false;
    if (window.__monTitle) clearInterval(window.__monTitle);
    window.__monTitle = setInterval(() => { document.title = flip ? "🔴 " + text : "⚪ " + text; flip = !flip; }, 800);
    try { if (Notification.permission === "granted") new Notification("监控提醒", { body: text, requireInteraction: true }); } catch (e) {}
  }

  // ── 轮询 ──────────────────────────────────────────────
  let round = 0;
  async function checkOnce() {
    round++;
    const ts = new Date().toLocaleTimeString();
    try {
      const r = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=UTF-8", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify(REQ_BODY),
        credentials: "include"   // ← 关键：复用浏览器 NTLM/SSO 登录态
      });
      if (!r.ok) { console.warn(`[#${round} ${ts}] ❌ HTTP ${r.status} — 可能登录过期`); return; }
      const data = await r.json();
      const c = data && data.Content;
      if (!c) { console.warn(`[#${round} ${ts}] ⚠️ 无 Content`, data); return; }
      const { done, label } = evaluate(c);
      console.log(`[#${round} ${ts}] ${label}`);
      if (done) {
        console.log("%c" + ALERT_TEXT, "color:red;font-size:22px;font-weight:bold");
        clearInterval(window.__monTimer); window.__monTimer = null;
        fireAlerts(ALERT_TEXT);
        console.log("监控已停止（已达标）。");
      }
    } catch (e) {
      console.warn(`[#${round} ${ts}] 探测异常:`, e.message);
    }
  }

  if (window.__monTimer) clearInterval(window.__monTimer);
  // 请求一次通知授权（首次会弹允许/阻止）
  try { if (Notification.permission === "default") Notification.requestPermission(); } catch (e) {}
  console.log("%c🟢 监控启动（每 " + (INTERVAL_MS/60000) + " 分钟，只读不写）", "color:green;font-size:15px;font-weight:bold");
  console.log("手动停止：clearInterval(window.__monTimer)");
  checkOnce();
  window.__monTimer = setInterval(checkOnce, INTERVAL_MS);
})();
