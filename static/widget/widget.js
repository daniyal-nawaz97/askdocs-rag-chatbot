/* AskDocs website widget. Usage:
   <script src="https://YOUR-DOMAIN/widget.js" data-kb="products" async></script> */
(function () {
  if (window.__askdocsWidget) return;
  window.__askdocsWidget = true;
  var script = document.currentScript || document.querySelector('script[src*="widget.js"]');
  var origin = new URL(script.src).origin;
  var kb = script.getAttribute("data-kb") || "";
  var color = script.getAttribute("data-color") || "";

  fetch(origin + "/api/public/config?kb=" + encodeURIComponent(kb)).then(function (r) { return r.json(); }).then(function (cfg) {
    var accent = color || cfg.accent_color || "#0f766e";
    var btn = document.createElement("button");
    btn.setAttribute("aria-label", "Chat with " + (cfg.bot_name || "us"));
    btn.style.cssText = "position:fixed;right:22px;bottom:22px;width:60px;height:60px;border-radius:50%;border:0;cursor:pointer;z-index:2147483000;" +
      "background:" + accent + ";color:#fff;box-shadow:0 8px 28px rgba(0,0,0,.25);display:grid;place-items:center;transition:transform .15s";
    btn.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg>';
    btn.onmouseenter = function () { btn.style.transform = "scale(1.06)"; };
    btn.onmouseleave = function () { btn.style.transform = "none"; };

    var frame = document.createElement("iframe");
    frame.title = cfg.bot_name || "Chat";
    frame.src = origin + "/widget?kb=" + encodeURIComponent(cfg.kb) + (color ? "&color=" + encodeURIComponent(color) : "");
    frame.style.cssText = "position:fixed;right:22px;bottom:94px;width:380px;height:580px;max-width:calc(100vw - 24px);max-height:calc(100vh - 120px);border:0;" +
      "border-radius:18px;box-shadow:0 18px 60px rgba(0,0,0,.28);z-index:2147483000;background:#fff;display:none";

    var open = false;
    btn.onclick = function () {
      open = !open;
      frame.style.display = open ? "block" : "none";
      btn.innerHTML = open
        ? '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>'
        : '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg>';
    };
    window.addEventListener("message", function (e) { if (e.origin === origin && e.data === "askdocs:close" && open) btn.onclick(); });
    document.body.appendChild(frame);
    document.body.appendChild(btn);
  }).catch(function () { /* widget stays hidden if the service is unreachable */ });
})();
