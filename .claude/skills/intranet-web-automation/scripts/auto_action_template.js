/* ============================================================
 * 内网系统"监控 → 到点自动执行写操作"模板（含全套安全护栏）
 * ============================================================
 * ⚠️ 写操作不可逆。上线前务必：①先 dry-run 验证；②取得用户明确授权。
 *    见 SKILL.md §5 合规护栏。
 *
 * 在【目标页自身的 F12 控制台】运行。复用浏览器 SSO/NTLM 登录态。
 * 每 N 分钟只读检查前置；前置一达标就走"官方操作路径"执行写操作，成功即停。
 *
 * 用法：把所有【占位】按目标系统实际值替换（逆向方法见 SKILL.md §2），
 *       默认 ARMED=false（dry-run）。确认流程无误再改 true 上线。
 *       手动停：clearInterval(window.__actTimer)
 *
 * ── 本模板体现的关键机制（来自 GSD 真实案例，务必理解后再改）──
 *  · 前置判断只靠只读接口，绝不靠"硬点提交撞报错"
 *  · 走系统官方函数/按钮路径，不跳校验（如 ValidateAndShowConfirm → 确认按钮）
 *  · 成功即停：拦 alert 文案 + 监听页面跳转 + submitted 闸门，三重
 *  · 防假成功：执行后若又弹校验错误框，判定未成功 → 重置闸门、恢复轮询
 *  · 只执行一次：submitted 闸门 + 执行前先停轮询
 * ============================================================ */
(() => {
  // ── 配置：按目标系统替换 ──────────────────────────────
  const ARMED = false;                                   // ← false=dry-run 只提醒；true=真执行写操作
  const INTERVAL_MS = 3 * 60 * 1000;

  // 只读接口（判前置）
  const READ_URL = "/GSD/main/PostProcess";              // 【占位】
  const READ_BODY = {                                    // 【占位】
    OwnerClass: "GrantManager", OPID: "GetDoneeInfoByID",
    Content: JSON.stringify({ ID: "【占位:记录ID】" }),
    Token: "", FromFlag: 1, Files: null, IsOK: false, ErrorCode: null, ErrorMessage: ""
  };
  // 前置是否达标（返回 true 才执行写操作）
  function preconditionMet(content) {                    // 【占位】
    return content.HasUnApprovedCapping === false;
  }

  // 写操作：官方路径。GSD 案例是"调校验入口 → 等确认弹窗 → 点确认按钮"
  const VALIDATE_FN = () => GrantEditPage.Save.ValidateAndShowConfirm(); // 【占位】校验+弹确认框的官方入口
  const CONFIRM_SELECTOR = "#btnConfirmNotice";         // 【占位】确认按钮（其 onclick 触发真提交）
  const ERROR_MODAL_SELECTOR = "#errorMessage";         // 【占位】校验错误弹窗（用于防假成功）
  const SUCCESS_ALERT_KEYWORD = "操作成功";              // 【占位】成功 alert 关键词
  const FAIL_ALERT_KEYWORD = "提交失败";                // 【占位】失败 alert 关键词
  const SUCCESS_URL_KEYWORD = "gsdlist.html";           // 【占位】成功后跳转的 URL 片段
  const ACTION_LABEL = "自动提交项目申请";               // 日志/提醒用

  // ── 状态 ──────────────────────────────────────────────
  let round = 0, submitted = false;
  const oldTitle = document.title;

  // ── 成功探测：拦 alert ────────────────────────────────
  const origAlert = window.alert;
  window.alert = function (msg) {
    try {
      const s = String(msg || "");
      if (s.includes(SUCCESS_ALERT_KEYWORD)) { console.log("%c🎉 成功！", "color:green;font-size:20px;font-weight:bold"); stopAll("成功(alert)"); }
      else if (s.includes(FAIL_ALERT_KEYWORD)) { console.warn("⚠️ 失败。停止不重试。"); stopAll("失败(alert)"); }
    } catch (e) {}
    return origAlert.apply(window, arguments);
  };
  window.addEventListener("beforeunload", () => { if (submitted) console.log("🎉 页面跳转中（应为成功）。"); });
  function errorModalVisible() { const em = document.querySelector(ERROR_MODAL_SELECTOR); return !!(em && em.offsetParent); }

  function stopAll(reason) {
    if (window.__actTimer) { clearInterval(window.__actTimer); window.__actTimer = null; }
    console.log("已停止：" + reason + "。不会再执行写操作。");
    fireAlerts("✅ " + reason);
  }

  // ── 提醒 ──────────────────────────────────────────────
  function fireAlerts(text) {
    const b = document.createElement("div");
    b.textContent = text + " — 点我关闭";
    b.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:2147483647;background:red;color:#fff;font-size:22px;font-weight:bold;text-align:center;padding:18px;cursor:pointer;box-shadow:0 2px 12px rgba(0,0,0,.5)";
    b.onclick = () => { b.remove(); if (window.__actTitle) clearInterval(window.__actTitle); document.title = oldTitle; };
    document.body.appendChild(b);
    let flip = false;
    if (window.__actTitle) clearInterval(window.__actTitle);
    window.__actTitle = setInterval(() => { document.title = flip ? "🔴 " + text : "⚪ " + text; flip = !flip; }, 800);
    try { if (Notification.permission === "granted") new Notification(ACTION_LABEL, { body: text, requireInteraction: true }); } catch (e) {}
  }

  function waitFor(sel, timeoutMs) {
    return new Promise((resolve) => {
      const t0 = Date.now();
      const iv = setInterval(() => {
        const el = document.querySelector(sel);
        if (el && el.offsetParent) { clearInterval(iv); resolve(el); }
        else if (Date.now() - t0 > timeoutMs) { clearInterval(iv); resolve(null); }
      }, 200);
    });
  }

  // ── 执行写操作（官方路径）──────────────────────────────
  async function doAction() {
    if (submitted) return;
    submitted = true; // 闸门先落，防重入重复执行
    console.log("%c🚀 前置达标，开始 " + ACTION_LABEL + " …", "color:blue;font-size:16px;font-weight:bold");
    try { VALIDATE_FN(); }
    catch (e) { submitted = false; stopAll("校验入口调用失败: " + e.message); return; }

    const btn = await waitFor(CONFIRM_SELECTOR, 8000);
    if (!btn) {
      // 没弹确认框 = 校验没过（前置可能没真达标/字段缺失）→ 不硬执行
      submitted = false;
      console.warn("⚠️ 未出现确认框——校验未过，脚本停止不强行执行。请手动检查。");
      stopAll("校验未过/未弹确认框");
      return;
    }
    console.log("点击确认：" + btn.innerText.slice(0, 30) + "…");
    btn.click(); // 触发真正写操作
    console.log("已确认。等待结果（成功会 alert『" + SUCCESS_ALERT_KEYWORD + "』并跳转 " + SUCCESS_URL_KEYWORD + "）…");

    // 防假成功：3 秒内若又弹校验错误框 → 未真执行 → 重置闸门恢复轮询
    setTimeout(() => {
      if (submitted && errorModalVisible()) {
        console.warn("⚠️ 确认后又现校验错误框——未真正执行。重置闸门，恢复轮询。");
        submitted = false;
        if (!window.__actTimer) window.__actTimer = setInterval(checkOnce, INTERVAL_MS);
      }
    }, 3000);
  }

  // ── 轮询前置 ──────────────────────────────────────────
  async function checkOnce() {
    if (submitted) return;
    round++;
    const ts = new Date().toLocaleTimeString();
    try {
      const r = await fetch(READ_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=UTF-8", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify(READ_BODY), credentials: "include"
      });
      if (!r.ok) { console.warn(`[#${round} ${ts}] ❌ HTTP ${r.status} — 可能登录过期`); return; }
      const data = await r.json();
      const c = data && data.Content;
      if (!c) { console.warn(`[#${round} ${ts}] ⚠️ 无 Content`, data); return; }
      const met = preconditionMet(c);
      console.log(`[#${round} ${ts}] 前置达标=${met}`);
      if (met) {
        clearInterval(window.__actTimer); window.__actTimer = null; // 先停轮询防重入
        if (ARMED) await doAction();
        else { console.log("%c✅ 前置达标（DRY-RUN，不执行）。请手动处理。", "color:red;font-size:20px;font-weight:bold"); fireAlerts("前置已达标！"); }
      }
    } catch (e) { console.warn(`[#${round} ${ts}] 探测异常:`, e.message); }
  }

  // ── 启动 ──────────────────────────────────────────────
  if (window.__actTimer) clearInterval(window.__actTimer);
  try { if (Notification.permission === "default") Notification.requestPermission(); } catch (e) {}
  console.log("%c🟢 启动 " + (ARMED ? "🔴 ARMED(会真执行，仅一次)" : "🟢 DRY-RUN(只提醒)"), "color:green;font-size:15px;font-weight:bold");
  console.log("手动停止：clearInterval(window.__actTimer)");
  checkOnce();
  window.__actTimer = setInterval(checkOnce, INTERVAL_MS);
})();
