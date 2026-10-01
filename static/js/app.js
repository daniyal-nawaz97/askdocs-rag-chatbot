/* AskDocs front-end: chat, documents, insights, settings, document viewer. */
Object.assign(ICONS, {
  thumbsUp: '<path d="M7 10v11"/><path d="M15 5.9 14 10h5.8a2 2 0 0 1 2 2.3l-1.4 7A2 2 0 0 1 18.4 21H7V10l4-8a2.5 2.5 0 0 1 4 3.9z"/>',
  thumbsDown: '<path d="M17 14V3"/><path d="M9 18.1 10 14H4.2a2 2 0 0 1-2-2.3l1.4-7A2 2 0 0 1 5.6 3H17v11l-4 8a2.5 2.5 0 0 1-4-3.9z"/>',
  send: '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
  bot: '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 8V4"/><circle cx="12" cy="3" r="1"/><path d="M9 13h.01"/><path d="M15 13h.01"/><path d="M9.5 16.5h5"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
  box: '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>',
  laptop: '<rect x="4" y="4" width="16" height="11" rx="2"/><path d="M2 20h20"/>',
  message: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
  chart: '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  headset: '<path d="M3 14v-3a9 9 0 0 1 18 0v3"/><rect x="2" y="14" width="5" height="7" rx="2"/><rect x="17" y="14" width="5" height="7" rx="2"/>',
  code: '<path d="m16 18 6-6-6-6"/><path d="m8 6-6 6 6 6"/>',
  panel: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/>',
  quote: '<path d="M3 21c3 0 7-1 7-8V5c0-1.2-.8-2-2-2H4c-1.2 0-2 .8-2 2v6c0 1.2.8 2 2 2h3c0 3-1 5-4 5z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.2-.8-2-2-2h-4c-1.2 0-2 .8-2 2v6c0 1.2.8 2 2 2h3c0 3-1 5-4 5z"/>',
});

const App = { user: null, info: null, kbs: [], settings: null, kbId: null, convId: null, messages: [], activeSources: [], activeMsg: null };
const isAdmin = () => App.user?.role === "admin";
const canManage = () => ["admin", "editor"].includes(App.user?.role);
const KB_ICON = { users: "users", laptop: "laptop", box: "box", lock: "lock", book: "book" };
const FILE_LABEL = { pdf: "PDF", docx: "DOC", txt: "TXT" };

function brandHTML() {
  const i = App.info || {};
  const name = i.company_name ? `${i.company_name.split(" ")[0]} AskDocs` : "AskDocs";
  return `<a class="brand" href="#/">${i.logo_url ? `<img src="${esc(i.logo_url)}" alt="logo">` : `<span class="brand-mark">${icon("message")}</span>`}<span>${esc(name)}</span></a>`;
}

function shell(active, html, { flush = false } = {}) {
  const nav = [["chat", "#/", "message", "Chat"]];
  if (canManage()) nav.push(["documents", "#/documents", "files", "Documents"], ["insights", "#/insights", "chart", "Insights"]);
  if (isAdmin()) nav.push(["settings", "#/settings", "settings", "Settings"]);
  const isDemo = App.user?.email === "demo@askdocs.app";
  $("#app").innerHTML = `
    ${isDemo ? `<div class="demo-banner">Demo company: Nimbus Home Appliances is fictitious. All documents and activity are sample data.</div>` : ""}
    <header class="topbar">${brandHTML()}
      <nav class="nav" aria-label="Main">${nav.map(([k, h, ic, l]) => `<a href="${h}" class="${active === k ? "active" : ""}">${icon(ic)}${l}</a>`).join("")}</nav>
      <div class="spacer"></div>
      <div class="profile"><button class="avatar" id="avatarBtn" aria-label="Profile menu">${esc(initials(App.user?.name))}</button>
        <div class="menu hidden" id="profileMenu"><div class="menu-head"><div style="font-weight:600">${esc(App.user?.name)}</div><div class="muted small">${esc(App.user?.email)}</div>
          <div class="tiny muted" style="text-transform:capitalize">${esc(App.user?.role)}</div></div>
          <a href="/privacy" target="_blank">${icon("shield")} Privacy &amp; security</a>
          <button id="logoutBtn">${icon("logout")} Sign out</button></div></div>
    </header>
    <main id="main" class="${flush ? "" : "page"}">${html}</main>
    <nav class="bottom-nav" aria-label="Main">${nav.map(([k, h, ic, l]) => `<a href="${h}" class="${active === k ? "active" : ""}">${icon(ic)}${l}</a>`).join("")}</nav>`;
  document.body.style.setProperty("--banner-h", isDemo ? "32px" : "0px");
  $("#avatarBtn").onclick = (e) => { e.stopPropagation(); $("#profileMenu").classList.toggle("hidden"); };
  document.addEventListener("click", () => $("#profileMenu")?.classList.add("hidden"));
  $("#logoutBtn").onclick = async () => { await api("/api/logout", { method: "POST" }); App.user = null; location.hash = "#/login"; };
  return $("#main");
}

async function ensureUser() {
  if (!App.info) App.info = await api("/api/app-info");
  setAccent(App.info.accent_color);
  if (!App.user) App.user = await api("/api/me");
  return App.user;
}

const tip = (text) => `<div class="tip">${icon("lightbulb")}<span>${text}</span></div>`;

/* ---------- answer formatting: bullets, bold, [n] citations ---------- */
function formatAnswer(text, sources = []) {
  const refs = {};
  sources.forEach((s, i) => (refs[s.ref || i + 1] = i));
  const lines = esc(text).split(/\n+/);
  let html = "", inList = false;
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const li = /^[-*•]\s+(.*)/.exec(line) || /^\d+\.\s+(.*)/.exec(line);
    if (li) { if (!inList) { html += "<ul>"; inList = true; } html += `<li>${li[1]}</li>`; }
    else { if (inList) { html += "</ul>"; inList = false; } html += `<p>${line}</p>`; }
  }
  if (inList) html += "</ul>";
  return html.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\[(\d+)\]/g, (_, n) => (refs[n] !== undefined ? `<span class="cite" data-src="${refs[n]}">${n}</span>` : ""));
}

function srcLabel(s) { return `${s.filename}${s.page ? ` · p.${s.page}` : s.heading ? ` · ${s.heading}` : ""}`; }

/* ---------- screen 1: login ---------- */
Router.add("/login", async () => {
  if (!App.info) App.info = await api("/api/app-info");
  setAccent(App.info.accent_color);
  $("#app").innerHTML = `
    <div class="auth-wrap"><div class="card auth-card">
      ${brandHTML()}
      <h1>Ask your company documents</h1>
      <p class="lead">Answers from your policies, guides and FAQs, with the source shown every time.</p>
      <form id="loginForm" class="stack" novalidate>
        <label class="field">Email<input class="input" type="email" name="email" autocomplete="username" required placeholder="you@company.com"></label>
        <label class="field">Password<input class="input" type="password" name="password" autocomplete="current-password" required placeholder="••••••••"></label>
        <div id="loginErr" class="alert err hidden" role="alert"></div>
        <button class="btn btn-primary btn-lg btn-block" type="submit">Sign in</button>
      </form>
      <div class="divider">or</div>
      <button class="btn btn-block btn-lg" id="demoBtn">${icon("sparkles")} Try the demo</button>
      <p class="tiny muted" style="text-align:center;margin-top:10px">Opens a fictitious demo company with sample HR, IT and product documents.</p>
      <div class="privacy-line">${icon("lock")}<span>Each company's documents are private and separate. <a href="/privacy" target="_blank">Privacy</a></span></div>
    </div></div>`;
  $("#loginForm").onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.target);
    try {
      await api("/api/login", { method: "POST", body: { email: f.get("email"), password: f.get("password") } });
      App.user = null; location.hash = sessionStorage.getItem("afterLogin") || "#/"; sessionStorage.removeItem("afterLogin");
    } catch (err) { $("#loginErr").textContent = err.message; $("#loginErr").classList.remove("hidden"); }
  };
  $("#demoBtn").onclick = async () => {
    $("#demoBtn").disabled = true; $("#demoBtn").innerHTML = `<span class="spinner"></span> Opening demo…`;
    for (let i = 0; i < 20; i++) {
      try { await api("/api/demo-login", { method: "POST" }); App.user = null; location.hash = "#/"; return; }
      catch (e) { if (e.status !== 503) { toast(e.message, "err"); break; } await new Promise((r) => setTimeout(r, 1500)); }
    }
    $("#demoBtn").disabled = false; $("#demoBtn").innerHTML = `${icon("sparkles")} Try the demo`;
  };
});

/* ---------- screen 2: chat ---------- */
Router.add("/", async (_, query) => chatScreen(query));
Router.add("/c/:id", async ({ id }) => chatScreen({ c: id }));

async function chatScreen(query) {
  await ensureUser();
  const [kbs, settings, convs] = await Promise.all([api("/api/kbs"), api("/api/settings"), api("/api/conversations")]);
  App.kbs = kbs; App.settings = settings;
  if (!kbs.length) {
    shell("chat", `<div class="empty"><div class="empty-icon">${icon("book")}</div><h3>No knowledge bases yet</h3><p>Ask an admin to add documents.</p></div>`);
    return;
  }
  App.convId = query.c ? +query.c : null;
  App.messages = [];
  if (App.convId) {
    try {
      const c = await api(`/api/conversations/${App.convId}`);
      App.kbId = c.kb_id; App.messages = c.messages;
    } catch { App.convId = null; }
  }
  if (query.kb && kbs.find((k) => k.id === +query.kb)) App.kbId = +query.kb;
  if (!App.kbId || !kbs.find((k) => k.id === App.kbId)) App.kbId = kbs[0].id;
  let streaming = false;
  shell("chat", `
    <div class="chat-layout">
      <aside class="side" id="side">
        <div class="side-section"><button class="btn btn-primary btn-block" id="newChat">${icon("plus")} New chat</button></div>
        <div class="side-section"><div class="side-title">Knowledge bases</div><div id="kbList"></div></div>
        <div class="side-section"><div class="side-title">Suggested questions</div><div id="suggList"></div></div>
        <div class="side-section" style="flex:1"><div class="side-title">Recent chats</div><div id="histList"></div></div>
      </aside>
      <section class="main-chat">
        <div class="chat-head">
          <div class="mobile-tabs"><button class="btn btn-ghost icon-btn btn-sm" id="openSide" aria-label="Knowledge bases and history">${icon("menu")}</button></div>
          <div class="grow"><h2 id="kbTitle"></h2><div class="small muted" id="kbDesc"></div></div>
          <span class="trust hide-sm">${icon("shield")} Answers only from company documents</span>
          <button class="btn btn-ghost icon-btn btn-sm" id="openSrc" aria-label="Show sources">${icon("panel")}</button>
        </div>
        <div class="messages" id="messages"><div class="messages-inner" id="msgInner"></div></div>
        <div class="composer">
          <form class="composer-inner" id="askForm">
            <textarea id="q" rows="1" placeholder="Ask about company documents…" aria-label="Your question" maxlength="1000"></textarea>
            <button class="btn btn-primary send" type="submit" aria-label="Send">${icon("send")}</button>
          </form>
          <div class="composer-note">Answers come only from the documents in this knowledge base. Check the source for anything important.</div>
        </div>
      </section>
      <aside class="src-panel" id="srcPanel"></aside>
    </div>`, { flush: true });

  const kb = () => App.kbs.find((k) => k.id === App.kbId);
  const renderSide = () => {
    $("#kbList").innerHTML = App.kbs.map((k) => `<button class="kb-item ${k.id === App.kbId ? "active" : ""}" data-kb="${k.id}">
      <span class="kb-ic">${icon(KB_ICON[k.icon] || "book")}</span><span class="grow"><span style="display:block">${esc(k.name)}</span>
      <span class="tiny muted" style="font-weight:400">${k.documents} document${k.documents !== 1 ? "s" : ""}${k.visibility === "restricted" ? " · restricted" : ""}</span></span></button>`).join("");
    $("#suggList").innerHTML = (kb().suggested || []).map((s) => `<button class="sugg">${esc(s)}</button>`).join("") || `<p class="small muted" style="margin:0 6px">No suggestions yet.</p>`;
    const hist = convs.filter((c) => c.kb_id === App.kbId || true);
    $("#histList").innerHTML = hist.length ? hist.slice(0, 15).map((c) => `<div class="hist-item ${c.id === App.convId ? "active" : ""}" data-c="${c.id}">${icon("message")}<span>${esc(c.title || "Chat")}</span>
      <button data-del="${c.id}" aria-label="Delete chat">${icon("trash")}</button></div>`).join("") : `<p class="small muted" style="margin:0 6px">Your chats will appear here.</p>`;
    $("#kbTitle").textContent = kb().name;
    $("#kbDesc").textContent = kb().description || "";
    $$("[data-kb]").forEach((b) => (b.onclick = () => { if (streaming) return; App.kbId = +b.dataset.kb; App.convId = null; App.messages = []; history.replaceState(null, "", "#/"); renderSide(); renderMessages(); renderSources([]); $("#side").classList.remove("mobile-open"); }));
    $$(".sugg").forEach((b) => (b.onclick = () => { ask(b.textContent); $("#side").classList.remove("mobile-open"); }));
    $$(".hist-item").forEach((h) => (h.onclick = (e) => { if (!e.target.closest("[data-del]")) location.hash = `#/c/${h.dataset.c}`; }));
    $$("#histList [data-del]").forEach((b) => (b.onclick = async (e) => {
      e.stopPropagation();
      await api(`/api/conversations/${b.dataset.del}`, { method: "DELETE" });
      const i = convs.findIndex((c) => c.id === +b.dataset.del); convs.splice(i, 1);
      if (App.convId === +b.dataset.del) { App.convId = null; App.messages = []; renderMessages(); history.replaceState(null, "", "#/"); }
      renderSide(); toast("Chat deleted");
    }));
  };

  const msgHTML = (m, i) => {
    if (m.role === "user") return `<div class="msg user"><div class="bubble">${esc(m.content)}</div></div>`;
    const sources = m.sources || [];
    const body = m.pending ? (m.content ? formatAnswer(m.content, sources) + `<span class="caret"></span>` : `<span class="row small muted" style="gap:8px"><span class="spinner"></span>Searching the documents…</span>`) : formatAnswer(m.content, sources);
    return `<div class="msg bot ${m.not_found ? "notfound" : ""}" data-i="${i}"><div class="bot-av">${icon(m.not_found ? "info" : "bot")}</div>
      <div class="bubble">${body}
        ${!m.pending ? `<div class="msg-meta">
          ${m.not_found ? `<button class="btn btn-sm" data-human="${m.id}">${icon("headset")} Ask a human</button>` :
            `${sources.map((s, j) => `<span class="src-chip" data-src="${j}" title="${esc(srcLabel(s))}">${icon("file")}<span>${esc(srcLabel(s))}</span></span>`).join("")}`}
          <div class="msg-actions">
            ${m.id ? `<button data-fb="1" data-id="${m.id}" class="${m.feedback === 1 ? "on" : ""}" aria-label="Helpful">${icon("thumbsUp")}</button>
            <button data-fb="-1" data-id="${m.id}" class="${m.feedback === -1 ? "on down" : ""}" aria-label="Not helpful">${icon("thumbsDown")}</button>` : ""}
            <button data-copy="${i}" aria-label="Copy answer">${icon("copy")}</button></div>
        </div>${!m.not_found && sources.length ? `<div class="based-on" style="margin-top:6px">${icon("checkCircle")} Based on company documents</div>` : ""}` : ""}
      </div></div>`;
  };

  const renderMessages = () => {
    const box = $("#msgInner");
    if (!App.messages.length) {
      box.innerHTML = `<div class="welcome"><div class="bot-av">${icon("bot")}</div><h1>${esc(App.settings.bot_name)}</h1>
        <p>${esc(App.settings.welcome_message)}</p>
        <div class="welcome-grid">${(kb().suggested || []).slice(0, 4).map((s) => `<button class="sugg-w">${icon("message")}<span>${esc(s)}</span></button>`).join("")}</div>
        <div style="margin-top:22px;display:flex;justify-content:center">${tip("Follow-up questions work too, e.g. “And for part-time staff?”. You can also ask in Urdu or Roman Urdu.")}</div></div>`;
      $$(".sugg-w").forEach((b) => (b.onclick = () => ask(b.textContent.trim())));
      return;
    }
    box.innerHTML = App.messages.map(msgHTML).join("");
    bindMessages();
  };

  const bindMessages = () => {
    $$(".src-chip, .cite").forEach((c) => (c.onclick = () => {
      const i = +c.closest(".msg").dataset.i;
      renderSources(App.messages[i].sources || [], +c.dataset.src, i);
      if (window.innerWidth <= 1200) $("#srcPanel").classList.add("mobile-open");
    }));
    $$("[data-fb]").forEach((b) => (b.onclick = async () => {
      const m = App.messages.find((x) => x.id === +b.dataset.id);
      const v = m.feedback === +b.dataset.fb ? 0 : +b.dataset.fb;
      let note = "";
      if (v === -1) {
        const ok = await modal({ title: "What was wrong?", body: `<p class="small muted" style="margin-bottom:10px">Optional. This helps the admin improve the documents.</p><textarea class="input" id="fbNote" placeholder="e.g. The answer was outdated"></textarea>`, confirm: "Send feedback", onConfirm: (el) => { note = $("#fbNote", el).value; } });
        if (!ok) return;
      }
      await api(`/api/messages/${m.id}/feedback`, { method: "POST", body: { value: v, note } });
      m.feedback = v || null; renderMessages(); if (v) toast("Thanks for the feedback");
    }));
    $$("[data-copy]").forEach((b) => (b.onclick = async () => {
      const m = App.messages[+b.dataset.copy];
      const text = m.content.replace(/\[\d+\]/g, "") + (m.sources?.length ? `\n\nSource: ${m.sources.map(srcLabel).join("; ")}` : "");
      try { await navigator.clipboard.writeText(text); toast("Answer copied"); } catch { toast("Couldn't copy", "err"); }
    }));
    $$("[data-human]").forEach((b) => (b.onclick = async () => {
      const r = await api("/api/handoff", { method: "POST", body: { message_id: +b.dataset.human, contact: App.user.email } });
      b.disabled = true; b.innerHTML = `${icon("check")} Sent to the team`; toast(r.message);
    }));
  };

  const renderSources = (sources, activeIdx = 0, msgIdx = null) => {
    const panel = $("#srcPanel");
    App.activeSources = sources;
    $$(".src-chip.active").forEach((c) => c.classList.remove("active"));
    if (msgIdx !== null) $(`.msg[data-i="${msgIdx}"] .src-chip[data-src="${activeIdx}"]`)?.classList.add("active");
    if (!sources.length) {
      panel.innerHTML = `<div class="panel-head row between"><h3>Sources</h3><button class="btn btn-ghost icon-btn btn-sm" id="closeSrc" aria-label="Close">${icon("x")}</button></div>
        <div class="src-empty">${icon("quote")}<div>The exact passage behind each answer appears here, so you can check it.</div></div>`;
    } else {
      panel.innerHTML = `<div class="panel-head row between"><h3>Sources</h3><button class="btn btn-ghost icon-btn btn-sm" id="closeSrc" aria-label="Close">${icon("x")}</button></div>` +
        sources.map((s, i) => `<div class="src-card ${i === activeIdx ? "active" : ""}" id="srccard${i}">
          <div class="src-card-head"><span class="fic ${s.file_type}">${FILE_LABEL[s.file_type] || "DOC"}</span><div style="min-width:0"><div style="font-weight:600;font-size:13.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.filename)}</div>
            <div class="tiny muted">${s.page ? `Page ${s.page}` : ""}${s.page && s.heading ? " · " : ""}${esc(s.heading || "")}</div></div></div>
          <div class="src-card-body">“<mark>${esc(s.passage)}</mark>”</div>
          <div class="src-card-foot"><a class="btn btn-sm btn-block" href="#/doc/${s.doc_id}?page=${s.page || ""}&chunk=${s.chunk_id}">${icon("external")} Open document${s.page ? ` at page ${s.page}` : ""}</a></div></div>`).join("");
      $(`#srccard${activeIdx}`)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
    $("#closeSrc").onclick = () => panel.classList.remove("mobile-open");
  };

  async function ask(text) {
    const question = (text ?? $("#q").value).trim();
    if (!question || streaming) return;
    streaming = true;
    $("#q").value = ""; $("#q").style.height = "auto";
    App.messages.push({ role: "user", content: question });
    const bot = { role: "assistant", content: "", sources: [], pending: true };
    App.messages.push(bot);
    renderMessages();
    const scroll = () => { const m = $("#messages"); m.scrollTop = m.scrollHeight; };
    scroll();
    try {
      const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin",
        body: JSON.stringify({ question, kb_id: App.kbId, conversation_id: App.convId }) });
      if (res.status === 401) { location.hash = "#/login"; return; }
      if (!res.ok) { let d = "Something went wrong."; try { d = (await res.json()).detail; } catch {} throw new Error(d); }
      const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = "";
      let last = 0;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf("\n\n")) >= 0) {
          const line = buf.slice(0, idx).replace(/^data: /, ""); buf = buf.slice(idx + 2);
          if (!line) continue;
          const ev = JSON.parse(line);
          if (ev.type === "meta") {
            if (!App.convId) { App.convId = ev.conversation_id; convs.unshift({ id: ev.conversation_id, title: question.slice(0, 60), kb_id: App.kbId }); history.replaceState(null, "", `#/c/${ev.conversation_id}`); renderSide(); }
          } else if (ev.type === "sources") { bot.sources = ev.sources; }
          else if (ev.type === "token") { bot.content += ev.text; }
          else if (ev.type === "done") {
            Object.assign(bot, { pending: false, id: ev.message_id, not_found: ev.not_found, sources: ev.sources, content: ev.text || bot.content });
          }
          if (Date.now() - last > 40 || ev.type === "done") { last = Date.now(); const el = $(`.msg[data-i="${App.messages.length - 1}"]`); if (el) el.outerHTML = msgHTML(bot, App.messages.length - 1); scroll(); }
        }
      }
      bot.pending = false;
      renderMessages(); scroll();
      if (bot.sources?.length && !bot.not_found) renderSources(bot.sources, 0, App.messages.length - 1);
    } catch (e) {
      bot.pending = false; bot.not_found = true; bot.content = "I'm having trouble right now. Please try again.";
      renderMessages(); toast(e.message || "Connection problem", "err");
    } finally { streaming = false; $("#q").focus(); }
  }

  $("#askForm").onsubmit = (e) => { e.preventDefault(); ask(); };
  $("#q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } });
  $("#q").addEventListener("input", (e) => { e.target.style.height = "auto"; e.target.style.height = Math.min(140, e.target.scrollHeight) + "px"; });
  $("#newChat").onclick = () => { App.convId = null; App.messages = []; history.replaceState(null, "", "#/"); renderSide(); renderMessages(); renderSources([]); $("#q").focus(); };
  $("#openSide").onclick = () => $("#side").classList.toggle("mobile-open");
  $("#openSrc").onclick = () => $("#srcPanel").classList.toggle("mobile-open");
  renderSide(); renderMessages();
  const lastBot = [...App.messages].reverse().find((m) => m.role === "assistant" && m.sources?.length);
  renderSources(lastBot ? lastBot.sources : [], 0, lastBot ? App.messages.indexOf(lastBot) : null);
  $("#messages").scrollTop = 1e9;
  if (window.innerWidth > 760) $("#q").focus();
  if (query.ask) ask(query.ask);
}

/* ---------- document viewer ---------- */
Router.add("/doc/:id", async ({ id }, query) => {
  await ensureUser();
  const d = await api(`/api/documents/${id}`);
  const chunk = d.chunks_list.find((c) => String(c.id) === String(query.chunk));
  const page = +(query.page || chunk?.page || 1);
  const main = shell("chat", `
    <div class="page-head"><div><div class="small muted" style="margin-bottom:6px"><a href="javascript:history.back()">← Back to chat</a></div>
      <h1 style="font-size:22px">${esc(d.filename)}</h1><p>${esc(d.kb_name || "")}${d.pages ? ` · ${d.pages} page${d.pages > 1 ? "s" : ""}` : ""} · version ${d.version} · updated ${fmt.when(d.updated_at)}</p></div>
      <a class="btn" href="/api/documents/${d.id}/file" target="_blank">${icon("download")} Download original</a></div>
    <div class="viewer-wrap"><div id="docBody"></div>
      <div class="card card-pad" style="position:sticky;top:80px">${chunk ? `<h3 style="margin-bottom:8px">Cited passage</h3><p class="small muted" style="margin-bottom:8px">${chunk.page ? `Page ${chunk.page}` : ""}${chunk.heading ? ` · ${esc(chunk.heading)}` : ""}</p>
        <div class="src-card-body" style="padding:0">“<mark>${esc(chunk.text)}</mark>”</div>` : `<p class="muted">Highlighted passages show where answers came from.</p>`}
        ${d.file_type === "pdf" && d.pages > 1 ? `<div class="row wrap" style="margin-top:14px;gap:6px">${Array.from({ length: d.pages }, (_, i) => `<a class="btn btn-sm ${i + 1 === page ? "btn-primary" : ""}" href="#pg${i + 1}">Page ${i + 1}</a>`).join("")}</div>` : ""}</div></div>`);
  if (d.file_type === "pdf") {
    $("#docBody").innerHTML = Array.from({ length: d.pages }, (_, i) => {
      const p = i + 1;
      const boxes = chunk && chunk.page === p ? chunk.boxes.map(([x0, y0, x1, y1]) => `<div class="doc-hl" style="left:${(x0 - 3) / chunk.page_w * 100}%;top:${(y0 - 2) / chunk.page_h * 100}%;width:${(x1 - x0 + 6) / chunk.page_w * 100}%;height:${(y1 - y0 + 4) / chunk.page_h * 100}%"></div>`).join("") : "";
      return `<div class="doc-page" id="pg${p}"><img src="/api/documents/${d.id}/page/${p}" alt="Page ${p}" loading="${Math.abs(p - page) <= 1 ? "eager" : "lazy"}">${boxes}</div><div class="page-label">Page ${p} of ${d.pages}</div>`;
    }).join("");
    setTimeout(() => {
      const target = $(".doc-page#pg" + page + " .doc-hl") || $("#pg" + page);
      target?.scrollIntoView({ block: "center" });
    }, 400);
  } else {
    let lastHeading = null;
    $("#docBody").innerHTML = `<div class="text-doc">${d.chunks_list.map((c) => {
      const h = c.heading && c.heading !== lastHeading ? `<h3>${esc(c.heading)}</h3>` : "";
      lastHeading = c.heading;
      return `${h}<p class="${chunk && c.id === chunk.id ? "hl-block" : ""}" id="ch${c.id}">${esc(c.text)}</p>`;
    }).join("")}</div>`;
    if (chunk) setTimeout(() => $("#ch" + chunk.id)?.scrollIntoView({ block: "center" }), 100);
  }
});

/* ---------- screen 3: documents ---------- */
Router.add("/documents", async (_, query) => {
  await ensureUser();
  if (!canManage()) { location.hash = "#/"; return; }
  const kbs = await api("/api/kbs");
  let filterKb = query.kb ? +query.kb : 0;
  const main = shell("documents", `
    <div class="page-head"><div><h1>Documents</h1><p>What the assistant knows. Upload new versions when a policy changes, and answers update automatically.</p></div></div>
    <div class="upload-zone" id="uz">
      <div class="row wrap" style="justify-content:center;gap:12px">
        <div style="text-align:left"><div style="font-weight:600">${icon("upload")} Drag and drop documents here</div><div class="small muted">PDF, Word (.docx) or text · up to 25 MB each</div></div>
        <select class="input" id="upKb" style="width:220px" aria-label="Knowledge base">${kbs.map((k) => `<option value="${k.id}" ${k.id === filterKb ? "selected" : ""}>${esc(k.name)}</option>`).join("")}</select>
        <label class="btn btn-primary">${icon("files")} Upload documents<input type="file" id="upIn" multiple accept=".pdf,.docx,.txt,.md" hidden></label>
      </div>
      ${query.gap ? `<div class="alert info" style="margin-top:14px;text-align:left">${icon("lightbulb")}<div>Staff asked: <b>“${esc(query.gap)}”</b> and the documents had no answer. Upload a document that covers it.</div></div>` : ""}
    </div>
    <div class="row between wrap" style="margin:20px 0 12px"><div class="seg" id="kbFilter"><button data-k="0" class="${!filterKb ? "active" : ""}">All</button>${kbs.map((k) => `<button data-k="${k.id}" class="${k.id === filterKb ? "active" : ""}">${esc(k.name)}</button>`).join("")}</div>
      ${tip("“Last updated” shows at a glance which documents may be outdated.")}</div>
    <div class="card" id="docTable"><div class="card-body"><div class="skeleton" style="height:18px"></div></div></div>`);
  let docs = [];
  const statusBadge = (d) => d.status === "ready" ? `<span class="badge ok">Ready</span>` : d.status === "failed" ? `<span class="badge err" title="${esc(d.error || "")}">Failed</span>` : `<span class="badge info pulse">Processing</span>`;
  const render = () => {
    const list = docs.filter((d) => !filterKb || d.kb_id === filterKb);
    $("#docTable").innerHTML = list.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>File</th><th class="hide-sm">Knowledge base</th><th class="right hide-sm">Pages</th><th class="hide-sm">Last updated</th><th>Status</th><th></th></tr></thead><tbody>
      ${list.map((d) => `<tr><td><div class="row" style="gap:10px"><span class="fic-sm ${d.file_type}">${FILE_LABEL[d.file_type] || "DOC"}</span><div style="min-width:0">
        <a href="#/doc/${d.id}" style="font-weight:600;color:var(--text)">${esc(d.filename)}</a>${d.is_sample ? ` <span class="badge info plain">Sample</span>` : ""}
        <div class="tiny muted">${d.status === "failed" ? `<span style="color:var(--err)">${esc(d.error)}</span>` : `${d.chunks} passage${d.chunks !== 1 ? "s" : ""} · v${d.version}${d.uploaded_by ? ` · by ${esc(d.uploaded_by)}` : ""}`}</div></div></div></td>
        <td class="hide-sm">${esc(d.kb_name)}</td><td class="right hide-sm num">${d.pages || "—"}</td><td class="hide-sm nowrap">${fmt.when(d.updated_at)}</td><td>${statusBadge(d)}</td>
        <td class="right nowrap"><label class="btn btn-ghost btn-sm" title="Replace with new version">${icon("refresh")}<span class="hide-sm">Replace</span><input type="file" data-rep="${d.id}" accept=".pdf,.docx,.txt,.md" hidden></label>
          ${d.status === "failed" ? `<button class="btn btn-ghost btn-sm" data-re="${d.id}">Re-process</button>` : ""}
          <button class="btn btn-ghost icon-btn btn-sm" data-del="${d.id}" aria-label="Delete">${icon("trash")}</button></td></tr>`).join("")}</tbody></table></div>`
      : `<div class="empty"><div class="empty-icon">${icon("files")}</div><h3>No documents here yet</h3><p>Upload the PDFs, Word files or FAQs this assistant should know.</p></div>`;
    $$("[data-rep]").forEach((inp) => (inp.onchange = async () => {
      const fd = new FormData(); fd.append("file", inp.files[0]);
      try { await api(`/api/documents/${inp.dataset.rep}/replace`, { method: "POST", form: fd }); toast("New version uploaded. Re-reading…"); load(); } catch (e) { toast(e.message, "err"); }
    }));
    $$("[data-re]").forEach((b) => (b.onclick = async () => { await api(`/api/documents/${b.dataset.re}/reprocess`, { method: "POST" }); load(); }));
    $$("[data-del]").forEach((b) => (b.onclick = async () => {
      if (!(await modal({ title: "Delete document?", body: "<p>The assistant will stop using it straight away.</p>", confirm: "Delete", danger: true }))) return;
      await api(`/api/documents/${b.dataset.del}`, { method: "DELETE" }); toast("Document deleted"); load();
    }));
  };
  let timer;
  const load = async () => {
    docs = await api("/api/documents"); render();
    clearTimeout(timer);
    if (docs.some((d) => ["queued", "processing"].includes(d.status))) timer = setTimeout(load, 1500);
  };
  const upload = async (files) => {
    if (!files.length) return;
    const fd = new FormData(); fd.append("kb_id", $("#upKb").value);
    [...files].forEach((f) => fd.append("files", f, f.name));
    try { await api("/api/documents", { method: "POST", form: fd }); toast(`Uploaded ${files.length} file${files.length > 1 ? "s" : ""}. Reading now…`); load(); }
    catch (e) { toast(e.message, "err"); }
  };
  $("#upIn").onchange = (e) => upload(e.target.files);
  const uz = $("#uz");
  ["dragenter", "dragover"].forEach((ev) => uz.addEventListener(ev, (e) => { e.preventDefault(); uz.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => uz.addEventListener(ev, (e) => { e.preventDefault(); uz.classList.remove("over"); }));
  uz.addEventListener("drop", (e) => upload(e.dataTransfer.files));
  $$("#kbFilter button").forEach((b) => (b.onclick = () => { filterKb = +b.dataset.k; $$("#kbFilter button").forEach((x) => x.classList.toggle("active", x === b)); render(); }));
  load();
  return () => clearTimeout(timer);
});

/* ---------- screen 4: insights ---------- */
Router.add("/insights", async () => {
  await ensureUser();
  if (!canManage()) { location.hash = "#/"; return; }
  const d = await api("/api/insights?days=30");
  const c = d.cards;
  const delta = c.questions_prev_week ? Math.round(((c.questions_week - c.questions_prev_week) / c.questions_prev_week) * 100) : null;
  const main = shell("insights", `
    <div class="page-head"><div><h1>Insights</h1><p>What staff and customers ask, what the documents can't answer yet, and how helpful the answers are.</p></div>
      ${d.is_sample ? `<span class="sample-note">${icon("info")} Includes sample activity for the demo company</span>` : ""}</div>
    <div class="grid grid-4" style="margin-bottom:16px">
      <div class="card stat"><div class="label">${icon("message")} Questions this week</div><div class="value">${c.questions_week}</div><div class="sub">${delta === null ? "&nbsp;" : `${delta >= 0 ? "+" : ""}${delta}% vs last week`}</div></div>
      <div class="card stat good"><div class="label">${icon("checkCircle")} Answered from documents</div><div class="value">${c.answered_rate ?? "—"}${c.answered_rate != null ? "%" : ""}</div><div class="sub">this week</div></div>
      <div class="card stat ${c.not_found_week ? "attention" : ""}"><div class="label">${icon("search")} Not found</div><div class="value">${c.not_found_week}</div><div class="sub">questions with no answer in the documents</div></div>
      <div class="card stat"><div class="label">${icon("thumbsUp")} Satisfaction</div><div class="value">${c.satisfaction ?? "—"}${c.satisfaction != null ? "%" : ""}</div><div class="sub">${c.ratings} ratings · about ${c.hours_saved_month} staff hours saved*</div></div>
    </div>
    <div class="card" style="margin-bottom:16px"><div class="card-head"><h2>Questions per day</h2><span class="small muted">Last 30 days</span></div><div class="chart-box"><canvas id="qChart" aria-label="Questions per day chart"></canvas></div></div>
    <div class="grid grid-2" style="margin-bottom:16px;align-items:start">
      <div class="card"><div class="card-head"><h2>Top questions</h2><span class="small muted">What people ask most</span></div>
        ${d.top_questions.length ? d.top_questions.map((q) => `<div class="qrow"><span class="count">${q.count}</span><div class="grow"><div style="font-weight:550">${esc(q.question)}</div><div class="tiny muted">${esc(q.kb)}</div></div></div>`).join("") : `<div class="empty" style="padding:24px"><p>No questions yet.</p></div>`}</div>
      <div class="card"><div class="card-head"><h2>Unanswered questions</h2><span class="small muted">Gaps in your documents</span></div>
        ${d.unanswered.length ? d.unanswered.map((q) => `<div class="qrow"><span class="count warn">${q.count}</span><div class="grow"><div style="font-weight:550">${esc(q.question)}</div><div class="tiny muted">${esc(q.kb)} · last asked ${fmt.when(q.last_asked)}</div></div>
          <a class="btn btn-sm" href="#/documents?kb=${q.kb_id}&gap=${encodeURIComponent(q.question)}">${icon("plus")} Add a document</a></div>`).join("") : `<div class="empty" style="padding:24px"><h3>No gaps</h3><p>Every question was answered from the documents.</p></div>`}</div>
    </div>
    <div class="grid grid-2" style="align-items:start">
      <div class="card"><div class="card-head"><h2>Answers marked not helpful</h2></div>
        ${d.feedback.length ? d.feedback.map((f) => `<div class="qrow" style="align-items:flex-start"><span class="count warn">${icon("thumbsDown")}</span><div class="grow"><div style="font-weight:550">${esc(f.question)}</div>
          <div class="small muted" style="margin-top:2px">${esc(f.answer.slice(0, 160))}${f.answer.length > 160 ? "…" : ""}</div>${f.note ? `<div class="small" style="margin-top:4px;color:var(--warn)">“${esc(f.note)}”</div>` : ""}</div></div>`).join("") : `<div class="empty" style="padding:24px"><p>No negative feedback. 👍</p></div>`}</div>
      <div class="stack">
        <div class="card"><div class="card-head"><h2>By knowledge base</h2></div><div class="card-body stack" style="gap:10px">
          ${d.by_kb.map((k) => { const max = Math.max(...d.by_kb.map((x) => x.count), 1); return `<div><div class="row between small"><span>${esc(k.kb)}</span><span class="num muted">${k.count}</span></div><div style="background:var(--surface-2);border-radius:99px;margin-top:4px"><div class="bar" style="width:${(k.count / max) * 100}%"></div></div></div>`; }).join("")}</div></div>
        <div class="card"><div class="card-head"><h2>By channel</h2></div><div class="card-body row wrap">${Object.entries(d.by_channel).map(([k, v]) => `<span class="badge info plain">${esc(k)}: ${v}</span>`).join("") || `<span class="muted small">No activity yet</span>`}</div></div>
        <div class="card"><div class="card-head"><h2>“Ask a human” requests</h2></div>${d.handoffs.length ? d.handoffs.map((h) => `<div class="qrow"><span class="count warn">${icon("headset")}</span><div class="grow"><div style="font-weight:550">${esc(h.question || "")}</div><div class="tiny muted">${esc(h.user_name)} · ${fmt.when(h.created_at)}${h.contact ? ` · ${esc(h.contact)}` : ""}</div></div></div>`).join("") : `<div class="card-body small muted">None yet.</div>`}</div>
      </div>
    </div>
    <p class="tiny muted" style="margin-top:14px">* Estimate: answered questions × ${c.minutes_per_question} minutes a colleague would otherwise spend finding the answer (last 30 days).</p>`);
  const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#0f766e";
  if (!window.Chart) await new Promise((r) => { window.addEventListener("load", r, { once: true }); setTimeout(r, 4000); });
  if (window.Chart && $("#qChart")) {
    new Chart($("#qChart"), {
      type: "bar",
      data: { labels: d.series.map((s) => s.date.slice(5).split("-").reverse().join("/")),
        datasets: [{ label: "Answered", data: d.series.map((s) => s.answered), backgroundColor: accent, borderRadius: 4, stack: "a" },
                   { label: "Not found", data: d.series.map((s) => s.not_found), backgroundColor: "#f59e0b", borderRadius: 4, stack: "a" }] },
      options: { maintainAspectRatio: false, animation: false, plugins: { legend: { position: "bottom", labels: { boxWidth: 12, usePointStyle: true } } },
        scales: { x: { stacked: true, grid: { display: false }, ticks: { maxTicksLimit: 10 } }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#eef0f3" } } } },
    });
  }
});

/* ---------- screen 5: settings (+ website widget, WhatsApp) ---------- */
Router.add("/settings", async (_, query) => {
  await ensureUser();
  if (!isAdmin()) { location.hash = "#/"; return; }
  let s = await api("/api/settings");
  let tab = query.tab || "assistant";
  const main = shell("settings", `<div class="settings-layout">
    <div class="page-head"><div><h1>Settings</h1><p>How the assistant talks, who can see what, and where it's available.</p></div></div>
    <div class="tabs" id="tabs">${[["assistant", "Assistant"], ["access", "Knowledge bases & access"], ["users", "Users & roles"], ["channels", "Website & WhatsApp"], ["branding", "Branding"], ["privacy", "Privacy"]]
      .map(([k, l]) => `<button data-t="${k}" class="${k === tab ? "active" : ""}">${l}</button>`).join("")}</div><div id="tabBody"></div></div>`);
  const save = async (patch) => {
    try { s = await api("/api/settings", { method: "PUT", body: patch }); App.info = await api("/api/app-info"); setAccent(s.accent_color); toast("Settings saved"); return true; }
    catch (e) { toast(e.message, "err"); return false; }
  };
  const tabs = {
    assistant: () => `<div class="card card-body stack" style="gap:18px">
      <div class="grid grid-2"><label class="field">Assistant name<input class="input" id="bName" value="${esc(s.bot_name)}"></label>
        <label class="field">Company name<input class="input" id="cName" value="${esc(s.company_name)}"></label></div>
      <label class="field">Welcome message<textarea class="input" id="welcome" rows="2">${esc(s.welcome_message)}</textarea></label>
      <div><div class="small" style="font-weight:600;color:var(--text-2);margin-bottom:8px">Tone</div><div class="chips" id="tone">${[["friendly", "Friendly"], ["formal", "Formal"]].map(([k, l]) => `<button class="chip ${s.tone === k ? "active" : ""}" data-v="${k}">${l}</button>`).join("")}</div></div>
      <div><div class="small" style="font-weight:600;color:var(--text-2);margin-bottom:8px">Languages people can ask in</div><div class="check-row">
        ${[["en", "English"], ["ur", "Urdu"], ["roman_ur", "Roman Urdu"]].map(([k, l]) => `<label><input type="checkbox" data-lang="${k}" ${s.languages.includes(k) ? "checked" : ""}> ${l}</label>`).join("")}</div></div>
      <div class="grid grid-2"><label class="field">When the answer isn't in the documents, say<input class="input" id="fallback" value="${esc(s.fallback_message)}"></label>
        <label class="field">…and point people to<input class="input" id="contact" value="${esc(s.human_contact)}" placeholder="e.g. HR at hr@company.com"></label></div>
      <div class="alert info">${icon(App.info.ai_enabled ? "sparkles" : "info")}<div>${App.info.ai_enabled ? "<b>AI answers are on (Groq).</b> Answers are written in the chosen tone and language, only from the documents, with numbered citations." : "<b>Quoted answers mode.</b> Without an AI key, the assistant replies with the exact sentences from the best-matching passage. Add a free Groq key to get written answers in any language."}
        Search ${App.info.semantic_search ? "understands meaning (local embedding model) plus keywords" : "uses keywords"}.</div></div>
      <div><button class="btn btn-primary" id="saveA">Save changes</button></div></div>`,
    access: () => `<div class="card" id="kbCards"><div class="card-body"><div class="skeleton" style="height:40px"></div></div></div>
      <div style="margin-top:12px">${tip("Restricted knowledge bases are only visible to admins and the people you pick. Only a “Public” knowledge base can be used by the website widget.")}</div>`,
    users: () => `<div class="card"><div class="card-head"><h2>Users</h2><button class="btn btn-primary btn-sm" id="addUser">${icon("plus")} Add user</button></div><div class="card-body" id="userList"></div></div>
      <div style="margin-top:12px">${tip("<b>Admins</b> manage everything. <b>Editors</b> manage documents and see insights. <b>Members</b> can chat.")}</div>`,
    channels: () => `<div class="stack" style="gap:16px">
      <div class="card card-body stack"><div class="row between wrap"><h3>Website chat widget</h3><a class="btn btn-sm" href="/demo-site" target="_blank">${icon("external")} See it on a sample website</a></div>
        <p class="muted small">Paste this before <code>&lt;/body&gt;</code> on the client's website. It answers from the public knowledge base only, in your brand colour.</p>
        <div class="code-box">&lt;script src="${location.origin}/widget.js" data-kb="products" async&gt;&lt;/script&gt;</div>
        <label class="field">Widget greeting<input class="input" id="wGreet" value="${esc(s.widget_greeting)}"></label><div><button class="btn btn-primary btn-sm" id="saveW">Save greeting</button></div></div>
      <div class="card card-body"><div class="row wrap" style="align-items:flex-start;gap:24px">
        <div class="grow stack" style="min-width:260px"><h3>WhatsApp <span class="badge info plain">Optional package</span></h3>
          <p class="muted small">Customers message your WhatsApp Business number and get the same short answers with a link to the source document. Try it on the right: it uses the real assistant.</p>
          <ol class="small" style="color:var(--text-2);padding-left:18px;margin:0;display:grid;gap:4px"><li>Create a WhatsApp Business app in Meta for Developers.</li><li>Set <code>WHATSAPP_TOKEN</code>, <code>WHATSAPP_PHONE_ID</code> and <code>WHATSAPP_KB=products</code> in <code>.env</code>.</li>
            <li>Webhook URL: <code>${location.origin}/api/whatsapp/webhook</code>, verify token from <code>WHATSAPP_VERIFY_TOKEN</code>.</li></ol></div>
        <div class="wa-phone"><div class="wa-top"><span class="av">${icon("message")}</span><div><div>${esc(s.company_name)}</div><div class="tiny" style="opacity:.8;font-weight:400">Preview · uses the live assistant</div></div></div>
          <div class="wa-body" id="waBody"><div class="wa-msg in">${esc(s.widget_greeting)}<span class="t">now</span></div></div>
          <form class="wa-input" id="waForm"><input id="waQ" placeholder="Type a message" value="How long does a refund take?" aria-label="WhatsApp preview question"><button aria-label="Send">${icon("send")}</button></form></div></div></div></div>`,
    branding: () => `<div class="card card-body stack" style="gap:20px">
      <div class="row wrap" style="gap:18px"><div class="card" style="width:180px;height:70px;display:grid;place-items:center;background:var(--surface-2)">${s.logo_url ? `<img src="${esc(s.logo_url)}" alt="Logo" style="max-height:48px;max-width:150px">` : `<span class="muted small">No logo yet</span>`}</div>
        <div class="stack" style="gap:8px"><label class="btn">${icon("upload")} Upload logo<input type="file" id="logoIn" accept=".png,.jpg,.jpeg,.svg,.webp" hidden></label>${s.logo_url ? `<button class="btn btn-ghost btn-sm" id="rmLogo">Remove logo</button>` : ""}</div></div>
      <div><div class="small" style="font-weight:600;color:var(--text-2);margin-bottom:8px">Brand colour (app and website widget)</div><div class="color-row"><input type="color" id="acc" value="${esc(s.accent_color)}">
        ${["#0f766e", "#1d4ed8", "#7c3aed", "#be123c", "#c2410c", "#111827"].map((c) => `<button class="swatch" data-c="${c}" style="background:${c}" aria-label="Use ${c}"></button>`).join("")}</div></div>
      <div><button class="btn btn-primary" id="saveB">Save branding</button></div></div>`,
    privacy: () => `<div class="card card-body stack" style="gap:14px"><h3>Chat history retention</h3><p class="muted small">Conversations older than this are deleted automatically. Documents stay until you delete them.</p>
      ${[[30, "30 days"], [90, "90 days"], [365, "1 year"], [0, "Keep until deleted"]].map(([v, l]) => `<label class="radio-card"><input type="radio" name="ret" value="${v}" ${+s.retention_days === v ? "checked" : ""}><div style="font-weight:600">${l}</div></label>`).join("")}
      <div class="alert ok">${icon("shield")}<div>Each client's documents are stored separately, restricted knowledge bases are enforced on the server, and documents are <b>never used to train AI models</b>. <a href="/privacy" target="_blank">Privacy statement</a></div></div>
      <div><button class="btn btn-primary" id="saveP">Save</button></div></div>`,
  };
  const render = () => {
    $("#tabBody").innerHTML = tabs[tab]();
    $$("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.t === tab));
    if (tab === "assistant") {
      let tone = s.tone;
      $$("#tone .chip").forEach((c) => (c.onclick = () => { tone = c.dataset.v; $$("#tone .chip").forEach((x) => x.classList.toggle("active", x === c)); }));
      $("#saveA").onclick = () => save({ bot_name: $("#bName").value.trim() || "Assistant", company_name: $("#cName").value.trim(), welcome_message: $("#welcome").value.trim(), tone,
        languages: $$("[data-lang]").filter((c) => c.checked).map((c) => c.dataset.lang), fallback_message: $("#fallback").value.trim() || "I couldn't find this in the documents.", human_contact: $("#contact").value.trim() });
    }
    if (tab === "access") loadKbs();
    if (tab === "users") loadUsers();
    if (tab === "channels") {
      $("#saveW").onclick = () => save({ widget_greeting: $("#wGreet").value.trim() });
      $("#waForm").onsubmit = async (e) => {
        e.preventDefault();
        const q = $("#waQ").value.trim(); if (!q) return;
        const t = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        $("#waBody").insertAdjacentHTML("beforeend", `<div class="wa-msg out">${esc(q)}<span class="t">${t} ✓✓</span></div><div class="wa-msg in" id="waPending">…</div>`);
        $("#waQ").value = ""; $("#waBody").scrollTop = 1e9;
        const res = await fetch("/api/public/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q, kb: "products" }) });
        const text = await res.text();
        const done = text.split("\n\n").map((l) => l.replace(/^data: /, "")).filter(Boolean).map((l) => JSON.parse(l)).find((e) => e.type === "done");
        let body = esc((done?.text || "Sorry, something went wrong.").replace(/\[\d+\]/g, "").trim());
        if (done?.sources?.length) { const src = done.sources[0]; body += `\n\nSource: ${esc(src.filename)}${src.page ? `, page ${src.page}` : ""}\n<a href="/api/public/documents/${src.doc_id}/file${src.page ? `#page=${src.page}` : ""}" target="_blank">${location.host}/doc/${src.doc_id}</a>`; }
        $("#waPending").outerHTML = `<div class="wa-msg in">${body}<span class="t">${t}</span></div>`;
        $("#waBody").scrollTop = 1e9;
      };
    }
    if (tab === "branding") {
      $("#acc").oninput = (e) => setAccent(e.target.value);
      $$(".swatch").forEach((b) => (b.onclick = () => { $("#acc").value = b.dataset.c; setAccent(b.dataset.c); }));
      $("#saveB").onclick = () => save({ accent_color: $("#acc").value });
      $("#logoIn").onchange = async (e) => { const fd = new FormData(); fd.append("file", e.target.files[0]); try { s = await api("/api/settings/logo", { method: "POST", form: fd }); App.info = await api("/api/app-info"); Router.go(); } catch (err) { toast(err.message, "err"); } };
      $("#rmLogo") && ($("#rmLogo").onclick = async () => { await save({ logo_url: "" }); App.info = await api("/api/app-info"); Router.go(); });
    }
    if (tab === "privacy") $("#saveP").onclick = () => save({ retention_days: +$("input[name=ret]:checked").value });
  };
  const loadKbs = async () => {
    const [kbs, users] = await Promise.all([api("/api/kbs"), api("/api/users")]);
    const access = Object.fromEntries(await Promise.all(kbs.map(async (k) => [k.id, await api(`/api/kbs/${k.id}/access`)])));
    $("#kbCards").innerHTML = kbs.map((k) => `<div class="kb-card" data-id="${k.id}">
      <div class="row between wrap"><div class="row"><span class="kb-ic" style="width:34px;height:34px;border-radius:9px;background:var(--accent-50);color:var(--accent);display:grid;place-items:center">${icon(KB_ICON[k.icon] || "book")}</span>
        <div><div style="font-weight:600">${esc(k.name)}</div><div class="small muted">${k.documents} document${k.documents !== 1 ? "s" : ""}</div></div></div>
        <div class="row wrap"><select class="input" data-vis style="width:190px;height:36px"><option value="everyone" ${k.visibility === "everyone" ? "selected" : ""}>Everyone in the company</option><option value="restricted" ${k.visibility === "restricted" ? "selected" : ""}>Restricted</option></select>
          <label class="row small" style="gap:8px"><span class="switch"><input type="checkbox" data-pub ${k.is_public ? "checked" : ""}><span></span></span>Public (website)</label></div></div>
      <div class="access ${k.visibility === "restricted" ? "" : "hidden"}" style="margin-top:12px"><div class="small muted" style="margin-bottom:6px">Who can see it (admins always can):</div><div class="check-row">
        ${users.filter((u) => u.role !== "admin").map((u) => `<label><input type="checkbox" data-u="${u.id}" ${access[k.id].includes(u.id) ? "checked" : ""}> ${esc(u.name)}</label>`).join("") || `<span class="small muted">No non-admin users yet.</span>`}</div></div>
      <label class="field" style="margin-top:12px">Suggested questions (one per line)<textarea class="input" data-sugg rows="3">${esc((k.suggested || []).join("\n"))}</textarea></label>
      <div style="margin-top:10px"><button class="btn btn-sm btn-primary" data-save>Save</button></div></div>`).join("");
    $$(".kb-card").forEach((card) => {
      $("[data-vis]", card).onchange = (e) => $(".access", card).classList.toggle("hidden", e.target.value !== "restricted");
      $("[data-save]", card).onclick = async () => {
        const k = kbs.find((x) => x.id === +card.dataset.id);
        try {
          await api(`/api/kbs/${k.id}`, { method: "PUT", body: { name: k.name, description: k.description || "", visibility: $("[data-vis]", card).value, is_public: $("[data-pub]", card).checked,
            suggested: $("[data-sugg]", card).value.split("\n").map((x) => x.trim()).filter(Boolean), allowed_users: $$("[data-u]", card).filter((c) => c.checked).map((c) => +c.dataset.u) } });
          toast("Access updated");
        } catch (e) { toast(e.message, "err"); }
      };
    });
  };
  const loadUsers = async () => {
    const users = await api("/api/users");
    $("#userList").innerHTML = users.map((u) => `<div class="member"><span class="avatar" style="cursor:default">${esc(initials(u.name))}</span>
      <div class="grow"><div style="font-weight:600">${esc(u.name)} ${u.id === App.user.id ? `<span class="muted small">(you)</span>` : ""}</div><div class="small muted">${esc(u.email)}</div></div>
      ${u.id !== App.user.id ? `<select class="input" style="width:130px;height:34px" data-role="${u.id}">${["admin", "editor", "member"].map((r) => `<option value="${r}" ${u.role === r ? "selected" : ""}>${r[0].toUpperCase() + r.slice(1)}</option>`).join("")}</select>
        <button class="btn btn-ghost icon-btn btn-sm" data-rm="${u.id}" aria-label="Remove">${icon("trash")}</button>` : `<span class="badge neutral plain" style="text-transform:capitalize">${esc(u.role)}</span>`}</div>`).join("");
    $$("[data-role]").forEach((sel) => (sel.onchange = async () => { await api(`/api/users/${sel.dataset.role}`, { method: "PATCH", body: { role: sel.value } }); toast("Role updated"); }));
    $$("#userList [data-rm]").forEach((b) => (b.onclick = async () => { if (await modal({ title: "Remove user?", body: "<p>They lose access immediately.</p>", confirm: "Remove", danger: true })) { await api(`/api/users/${b.dataset.rm}`, { method: "DELETE" }); loadUsers(); } }));
    $("#addUser").onclick = () => modal({ title: "Add user", confirm: "Add user",
      body: `<div class="stack"><label class="field">Name<input class="input" id="uName"></label><label class="field">Email<input class="input" id="uEmail" type="email"></label>
        <label class="field">Role<select class="input" id="uRole"><option value="member">Member (chat)</option><option value="editor">Editor (documents + insights)</option><option value="admin">Admin</option></select></label></div>`,
      onConfirm: async (m) => {
        const r = await api("/api/users", { method: "POST", body: { name: $("#uName", m).value, email: $("#uEmail", m).value, role: $("#uRole", m).value } });
        loadUsers(); setTimeout(() => modal({ title: "User added", body: `<p>Temporary password to share:</p><p style="margin-top:10px"><code style="font-size:16px;background:var(--surface-2);padding:6px 10px;border-radius:6px">${esc(r.temporary_password)}</code></p>`, confirm: "Done", cancel: null }), 50);
      } });
  };
  $$("#tabs button").forEach((b) => (b.onclick = () => { tab = b.dataset.t; render(); }));
  render();
});

/* ---------- boot ---------- */
(async () => {
  try { App.info = await api("/api/app-info"); setAccent(App.info.accent_color); } catch {}
  Router.start();
})();
