/* AskDocs clickable demo: replays prepared answers (with sources) word by word; keeps new chats until the page is closed. */
const ORIGIN = self.location.origin + BASE;
const STOP = new Set("a an the is are am do does did i me my we our you your to of for in on at and or how what when where which who can could should would will much many it this that be with from about there any have has get".split(" "));
const norm = (s) => (s || "").toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, " ").replace(/\s+/g, " ").trim();
const words = (s) => new Set(norm(s).split(" ").filter((w) => w && !STOP.has(w)));

function similarity(a, b) {
  const A = words(a), B = words(b);
  if (!A.size || !B.size) return 0;
  let n = 0; A.forEach((w) => B.has(w) && n++);
  return n / (A.size + B.size - n);
}

async function findAnswer(kbId, question, prev, ctx) {
  const all = (await ctx.getJSON("/api/_demo/answers"))[String(kbId)] || [];
  const q = norm(question), p = norm(prev);
  let best = null, score = 0;
  for (const a of all) {
    let s = norm(a.q) === q ? 1.01 : similarity(question, a.q);
    if (a.prev) s = norm(a.prev) === p ? s + 0.02 : s - 0.3; // follow-ups only count after their first question
    if (s > score) { score = s; best = a; }
  }
  if (best && score >= 0.5) return best;
  const sugg = all.filter((a) => !a.prev).slice(0, 4).map((a) => `• ${a.q}`).join("\n");
  return { text: `This clickable demo answers a set of prepared questions, so I can't search the documents for that one here. The live version answers any question about your documents.\n\nTry one of these:\n${sugg}`, sources: [], not_found: false, demo: true };
}

function stream(events) {
  const enc = new TextEncoder();
  return new Response(new ReadableStream({
    async start(c) {
      for (const ev of events) {
        if (ev.wait) await new Promise((r) => setTimeout(r, ev.wait));
        else c.enqueue(enc.encode("data: " + JSON.stringify(ev) + "\n\n"));
      }
      c.close();
    },
  }), { headers: { "content-type": "text/event-stream" } });
}

const newId = () => (STATE.nextId = (STATE.nextId || 900000) + 1);
async function chat(body, ctx, channel) {
  const question = (body?.question || "").trim();
  if (!question) return ctx.json({ detail: "Please type a question" }, 400);
  let kbId = body.kb_id;
  if (channel === "widget") {
    const map = await ctx.getJSON("/api/_demo/kbs");
    const cfg = await ctx.getJSON(ctx.normKey(ORIGIN + "/api/public/config?kb=" + encodeURIComponent(body.kb || ""))) || (await ctx.getJSON("/api/public/config"));
    kbId = map[cfg.kb];
  }
  const convs = (STATE.convs ||= {});
  let cid = body.conversation_id;
  if (!cid || !convs[cid]) {
    const base = cid ? await ctx.getJSON(`/api/conversations/${cid}`) : null;
    cid = cid || newId();
    convs[cid] = { ...(base || {}), id: cid, kb_id: kbId, title: base?.title || question.slice(0, 60), channel, messages: base ? base.messages.slice() : [], created_at: base?.created_at || new Date().toISOString() };
  }
  const conv = convs[cid];
  const prev = [...conv.messages].reverse().find((m) => m.role === "user")?.content || "";
  const a = await findAnswer(kbId, question, prev, ctx);
  const mid = newId();
  const now = new Date().toISOString();
  conv.messages.push({ id: newId(), role: "user", content: question, created_at: now },
    { id: mid, role: "assistant", content: a.text, sources: a.sources, not_found: a.not_found ? 1 : 0, feedback: null, created_at: now });
  conv.updated_at = now;
  const events = [{ wait: 350 }, { type: "meta", conversation_id: cid }, { type: "sources", sources: a.sources }];
  const parts = a.text.match(/\S+\s*/g) || [];
  for (let i = 0; i < parts.length; i += 3) events.push({ type: "token", text: parts.slice(i, i + 3).join("") }, { wait: 28 });
  events.push({ type: "done", message_id: mid, not_found: !!a.not_found, sources: a.sources, latency_ms: 900, text: a.text });
  return stream(events);
}

self.HOOKS = {
  async get(key, ctx) {
    const path = key.split("?")[0];
    let m;
    if (path === "/api/conversations") {
      const base = (await ctx.getJSON("/api/conversations")) || [];
      const mine = Object.values(STATE.convs || {}).filter((c) => c.channel === "app");
      const ids = new Set(mine.map((c) => c.id));
      const del = STATE.deleted || {};
      return ctx.json(mine.slice().reverse().map(({ messages, ...c }) => c).concat(base.filter((c) => !ids.has(c.id))).filter((c) => !del[c.id]));
    }
    if ((m = /^\/api\/conversations\/(\d+)$/.exec(path)) && STATE.convs?.[+m[1]]) return ctx.json(STATE.convs[+m[1]]);
    if ((m = /^\/api\/public\/documents\/(\d+)\/file$/.exec(path))) return ctx.serve(ctx.m.get[`/api/documents/${m[1]}/file`]);
    if (path === "/api/public/config" && !ctx.m.get[key]) return ctx.serve(ctx.m.get["/api/public/config"]);
    if (path === "/api/insights") return ctx.serve(ctx.m.get["/api/insights?days=30"]);
    if (path === "/api/settings" && STATE.settings) return ctx.json({ ...(await ctx.getJSON("/api/settings")), ...STATE.settings });
    return null;
  },
  async post(method, key, body, ctx) {
    const path = key.split("?")[0];
    let m;
    if (path === "/api/chat") return chat(body, ctx, "app");
    if (path === "/api/public/chat") return chat(body, ctx, "widget");
    if (/^\/api\/messages\/\d+\/feedback$/.test(path)) return ctx.json({ ok: true });
    if (path === "/api/handoff") return ctx.json({ ok: true, message: "Sent to our team. (In this demo nothing is actually sent.)" });
    if ((m = /^\/api\/conversations\/(\d+)$/.exec(path)) && method === "DELETE") { (STATE.deleted ||= {})[+m[1]] = 1; return ctx.json({ ok: true }); }
    if (path === "/api/settings" && method === "PUT") {
      STATE.settings = { ...(STATE.settings || {}), ...(body || {}) };
      return ctx.json({ ...(await ctx.getJSON("/api/settings")), ...STATE.settings });
    }
    if (/^\/api\/users\/\d+$/.test(path) && method === "PATCH") return ctx.json({ ok: true });
    return null;
  },
};
