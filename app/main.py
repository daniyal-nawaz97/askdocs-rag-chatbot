"""AskDocs: a chatbot that answers from company documents, with sources."""
from __future__ import annotations

import json
import logging
import re
import secrets
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import answer, db, ingest, search, seed
from .config import (APP_NAME, BRAND_DIR, CONTACT_EMAIL, CONTACT_WHATSAPP, DEMO_EMAIL, FILES_DIR, MAX_FILE_MB, PUBLIC_BASE_URL,
                     STAFF_MINUTES_PER_QUESTION, STATIC_DIR, WHATSAPP_KB, WHATSAPP_PHONE_ID, WHATSAPP_TOKEN, WHATSAPP_VERIFY_TOKEN, ai_enabled)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("askdocs")
app = FastAPI(title=APP_NAME, docs_url=None, redoc_url=None)
COOKIE = "ad_session"
READY = {"seeded": False}


@app.on_event("startup")
def startup():
    db.init_schema()

    def _boot():
        seed.seed()
        seed.seed_activity()
        u = db.one("SELECT id FROM users WHERE email=?", (DEMO_EMAIL,))
        if u:
            seed.seed_demo_chats(u["id"])
        for d in db.query("SELECT id FROM documents WHERE status IN ('queued','processing')"):
            ingest.ingest_document(d["id"])
        apply_retention()
        READY["seeded"] = True
        log.info("Demo data ready")
    threading.Thread(target=_boot, daemon=True).start()


def apply_retention():
    days = int(db.get_settings().get("retention_days") or 0)
    if days <= 0:
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    old = [r["id"] for r in db.query("SELECT id FROM conversations WHERE updated_at < ? AND id NOT IN (SELECT conversation_id FROM messages WHERE is_sample=1)", (cutoff,))]
    for cid in old:
        db.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))
        db.execute("DELETE FROM conversations WHERE id=?", (cid,))


# --------------------------------------------------------------------------- auth & access
def current_user(request: Request):
    token = request.cookies.get(COOKIE)
    u = db.one("SELECT u.id, u.email, u.name, u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?", (token,)) if token else None
    if not u:
        raise HTTPException(401, "Please sign in")
    return u


def need(*roles):
    def dep(user=Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, "You don't have access to this. Ask an admin.")
        return user
    return dep


def visible_kbs(user) -> list[dict]:
    kbs = db.query("SELECT * FROM knowledge_bases ORDER BY id")
    allowed = {r["kb_id"] for r in db.query("SELECT kb_id FROM kb_access WHERE user_id=?", (user["id"],))}
    out = []
    for k in kbs:
        if k["visibility"] == "everyone" or user["role"] == "admin" or k["id"] in allowed:
            k["suggested"] = json.loads(k.pop("suggested_json") or "[]")
            k["documents"] = db.one("SELECT COUNT(*) AS n FROM documents WHERE kb_id=? AND status='ready'", (k["id"],))["n"]
            out.append(k)
    return out


def kb_for(user, kb_id: int) -> dict:
    for k in visible_kbs(user):
        if k["id"] == kb_id:
            return k
    raise HTTPException(403, "You don't have access to this knowledge base")


def _login(response: Response, user_id: int):
    token = secrets.token_urlsafe(32)
    db.execute("INSERT INTO sessions(token, user_id, created_at) VALUES(?,?,?)", (token, user_id, db.now()))
    response.set_cookie(COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 14)


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(body: LoginIn, response: Response):
    u = db.one("SELECT * FROM users WHERE lower(email)=lower(?)", (body.email.strip(),))
    if not u or not db.check_password(body.password, u["password_hash"]):
        raise HTTPException(401, "Email or password is not correct")
    _login(response, u["id"])
    return {"ok": True}


@app.post("/api/demo-login")
def demo_login(response: Response):
    u = db.one("SELECT id FROM users WHERE email=?", (DEMO_EMAIL,))
    if not u:
        raise HTTPException(503, "The demo is still starting. Please try again in a few seconds.")
    _login(response, u["id"])
    return {"ok": True}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    db.execute("DELETE FROM sessions WHERE token=?", (request.cookies.get(COOKIE, ""),))
    response.delete_cookie(COOKIE)
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


@app.get("/api/app-info")
def app_info():
    s = db.get_settings()
    return {k: s[k] for k in ("company_name", "bot_name", "accent_color", "logo_url", "welcome_message", "widget_greeting")} | {
        "app_name": APP_NAME, "ai_enabled": ai_enabled(), "semantic_search": search.embeddings_active() if READY["seeded"] else None,
        "ready": READY["seeded"], "contact_email": CONTACT_EMAIL, "contact_whatsapp": CONTACT_WHATSAPP}


# --------------------------------------------------------------------------- knowledge bases
@app.get("/api/kbs")
def list_kbs(user=Depends(current_user)):
    return visible_kbs(user)


class KbIn(BaseModel):
    name: str
    description: str = ""
    visibility: str = "everyone"
    is_public: bool = False
    suggested: list[str] = []
    allowed_users: list[int] = []


@app.post("/api/kbs")
def create_kb(body: KbIn, user=Depends(need("admin"))):
    slug = re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-") or "kb"
    if db.one("SELECT id FROM knowledge_bases WHERE slug=?", (slug,)):
        slug += "-" + secrets.token_hex(2)
    kb_id = db.execute("INSERT INTO knowledge_bases(slug, name, description, icon, visibility, is_public, suggested_json, created_at) VALUES(?,?,?,?,?,?,?,?)",
                       (slug, body.name.strip() or "New knowledge base", body.description, "book", body.visibility, int(body.is_public), json.dumps(body.suggested), db.now()))
    _set_access(kb_id, body.allowed_users)
    return {"id": kb_id}


@app.put("/api/kbs/{kb_id}")
def update_kb(kb_id: int, body: KbIn, user=Depends(need("admin"))):
    if body.visibility not in ("everyone", "restricted"):
        raise HTTPException(400, "Visibility must be everyone or restricted")
    db.execute("UPDATE knowledge_bases SET name=?, description=?, visibility=?, is_public=?, suggested_json=? WHERE id=?",
               (body.name.strip(), body.description, body.visibility, int(body.is_public), json.dumps([s for s in body.suggested if s.strip()][:6]), kb_id))
    _set_access(kb_id, body.allowed_users)
    return {"ok": True}


def _set_access(kb_id, users):
    db.execute("DELETE FROM kb_access WHERE kb_id=?", (kb_id,))
    for uid in users:
        db.execute("INSERT OR IGNORE INTO kb_access(kb_id, user_id) VALUES(?,?)", (kb_id, uid))


@app.get("/api/kbs/{kb_id}/access")
def kb_access(kb_id: int, user=Depends(need("admin"))):
    return [r["user_id"] for r in db.query("SELECT user_id FROM kb_access WHERE kb_id=?", (kb_id,))]


# --------------------------------------------------------------------------- documents
def _doc_out(d):
    return {k: d[k] for k in ("id", "kb_id", "filename", "title", "file_type", "pages", "chunks", "status", "error", "version", "is_sample", "uploaded_by", "created_at", "updated_at")}


@app.get("/api/documents")
def list_documents(user=Depends(current_user)):
    kbs = {k["id"]: k["name"] for k in visible_kbs(user)}
    docs = db.query("SELECT * FROM documents ORDER BY updated_at DESC")
    return [_doc_out(d) | {"kb_name": kbs[d["kb_id"]]} for d in docs if d["kb_id"] in kbs]


def _store(upload_name: str, data: bytes) -> tuple[Path, str]:
    ext = Path(upload_name).suffix.lower()
    if ext not in ingest.SUPPORTED:
        raise HTTPException(400, f"{upload_name}: please upload PDF, Word (.docx) or text files")
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(400, f"{upload_name} is larger than {MAX_FILE_MB} MB")
    dest = FILES_DIR / f"{secrets.token_hex(6)}{ext}"
    dest.write_bytes(data)
    return dest, "txt" if ext == ".md" else ext.lstrip(".")


@app.post("/api/documents")
async def upload_documents(kb_id: int = Form(...), files: list[UploadFile] = File(...), user=Depends(need("admin", "editor"))):
    kb_for(user, kb_id)
    ids = []
    for f in files:
        dest, ftype = _store(f.filename, await f.read())
        now = db.now()
        doc_id = db.execute("INSERT INTO documents(kb_id, filename, title, file_type, stored_path, status, uploaded_by, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                            (kb_id, Path(f.filename).name, Path(f.filename).stem.replace("_", " "), ftype, str(dest), "queued", user["name"], now, now))
        ingest.ingest_async(doc_id)
        ids.append(doc_id)
    return {"ids": ids}


@app.post("/api/documents/{doc_id}/replace")
async def replace_document(doc_id: int, file: UploadFile = File(...), user=Depends(need("admin", "editor"))):
    d = db.one("SELECT * FROM documents WHERE id=?", (doc_id,))
    if not d:
        raise HTTPException(404, "Document not found")
    kb_for(user, d["kb_id"])
    dest, ftype = _store(file.filename, await file.read())
    if d["stored_path"] and not d["is_sample"]:
        Path(d["stored_path"]).unlink(missing_ok=True)
    for p in (FILES_DIR.parent / "pages").glob(f"{doc_id}_*.png"):
        p.unlink(missing_ok=True)
    db.execute("UPDATE documents SET filename=?, file_type=?, stored_path=?, status='queued', version=version+1, uploaded_by=?, updated_at=?, is_sample=0 WHERE id=?",
               (Path(file.filename).name, ftype, str(dest), user["name"], db.now(), doc_id))
    ingest.ingest_async(doc_id)
    return {"ok": True}


@app.post("/api/documents/{doc_id}/reprocess")
def reprocess(doc_id: int, user=Depends(need("admin", "editor"))):
    d = db.one("SELECT kb_id FROM documents WHERE id=?", (doc_id,))
    if not d:
        raise HTTPException(404, "Document not found")
    kb_for(user, d["kb_id"])
    db.execute("UPDATE documents SET status='queued' WHERE id=?", (doc_id,))
    ingest.ingest_async(doc_id)
    return {"ok": True}


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int, user=Depends(need("admin", "editor"))):
    d = db.one("SELECT * FROM documents WHERE id=?", (doc_id,))
    if not d:
        raise HTTPException(404, "Document not found")
    kb_for(user, d["kb_id"])
    if d["stored_path"]:
        Path(d["stored_path"]).unlink(missing_ok=True)
    db.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    search.invalidate(d["kb_id"])
    return {"ok": True}


def _doc_for(user, doc_id):
    d = db.one("SELECT * FROM documents WHERE id=?", (doc_id,))
    if not d:
        raise HTTPException(404, "Document not found")
    kb_for(user, d["kb_id"])
    return d


@app.get("/api/documents/{doc_id}")
def document_detail(doc_id: int, user=Depends(current_user)):
    d = _doc_for(user, doc_id)
    chunks = db.query("SELECT id, page, heading, text, boxes_json, page_w, page_h FROM chunks WHERE doc_id=? ORDER BY position", (doc_id,))
    for c in chunks:
        c["boxes"] = json.loads(c.pop("boxes_json") or "[]")
    kb = db.one("SELECT name FROM knowledge_bases WHERE id=?", (d["kb_id"],))
    return _doc_out(d) | {"chunks_list": chunks, "kb_name": kb["name"] if kb else ""}


@app.get("/api/documents/{doc_id}/page/{page}")
def document_page(doc_id: int, page: int, user=Depends(current_user)):
    _doc_for(user, doc_id)
    p = ingest.render_page(doc_id, page)
    if not p:
        raise HTTPException(404, "Page not available")
    return FileResponse(p, media_type="image/png", headers={"Cache-Control": "private, max-age=3600"})


@app.get("/api/documents/{doc_id}/file")
def document_file(doc_id: int, user=Depends(current_user)):
    d = _doc_for(user, doc_id)
    return FileResponse(d["stored_path"], filename=d["filename"])


# --------------------------------------------------------------------------- chat
@app.get("/api/conversations")
def conversations(user=Depends(current_user)):
    kbs = {k["id"] for k in visible_kbs(user)}
    rows = db.query("SELECT * FROM conversations WHERE user_id=? AND channel='app' ORDER BY updated_at DESC LIMIT 50", (user["id"],))
    return [r for r in rows if r["kb_id"] in kbs]


@app.get("/api/conversations/{cid}")
def conversation(cid: int, user=Depends(current_user)):
    c = db.one("SELECT * FROM conversations WHERE id=? AND user_id=?", (cid, user["id"]))
    if not c:
        raise HTTPException(404, "Conversation not found")
    msgs = db.query("SELECT id, role, content, sources_json, not_found, feedback, created_at FROM messages WHERE conversation_id=? ORDER BY id", (cid,))
    for m in msgs:
        m["sources"] = json.loads(m.pop("sources_json") or "[]")
    return {**c, "messages": msgs}


@app.delete("/api/conversations/{cid}")
def delete_conversation(cid: int, user=Depends(current_user)):
    db.execute("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE id=? AND user_id=?)", (cid, user["id"]))
    db.execute("DELETE FROM conversations WHERE id=? AND user_id=?", (cid, user["id"]))
    return {"ok": True}


class AskIn(BaseModel):
    question: str
    kb_id: int
    conversation_id: int | None = None


def _sse(obj) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _history(cid):
    rows = db.query("SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT 8", (cid,)) if cid else []
    return list(reversed(rows))


def _run_chat(question, kb_id, cid, user_id, channel, settings):
    """Generator of SSE strings; stores the exchange."""
    now = db.now()
    if not cid:
        cid = db.execute("INSERT INTO conversations(user_id, kb_id, title, channel, created_at, updated_at) VALUES(?,?,?,?,?,?)",
                         (user_id, kb_id, question[:60], channel, now, now))
        history = []
    else:
        history = _history(cid)
    db.execute("INSERT INTO messages(conversation_id, role, content, kb_id, channel, created_at) VALUES(?,?,?,?,?,?)", (cid, "user", question, kb_id, channel, now))
    yield _sse({"type": "meta", "conversation_id": cid})
    text, done = "", {}
    try:
        for ev in answer.stream_answer(question, history, kb_id, settings):
            if ev["type"] == "token":
                text += ev["text"]
            if ev["type"] == "done":
                done = ev
                continue
            yield _sse(ev)
    except Exception:
        log.exception("answer failed")
        text = "I'm having trouble right now. Please try again in a moment."
        done = {"not_found": True, "sources": [], "engine": "error", "latency_ms": 0}
        yield _sse({"type": "token", "text": text})
    final_text = (done.get("text") or text).strip()
    mid = db.execute("INSERT INTO messages(conversation_id, role, content, question, sources_json, not_found, latency_ms, engine, kb_id, channel, created_at) "
                     "VALUES(?,?,?,?,?,?,?,?,?,?,?)", (cid, "assistant", final_text, question, json.dumps(done.get("sources", [])),
                                                       int(bool(done.get("not_found"))), done.get("latency_ms"), done.get("engine"), kb_id, channel, db.now()))
    db.execute("UPDATE conversations SET updated_at=? WHERE id=?", (db.now(), cid))
    yield _sse({"type": "done", "message_id": mid, "not_found": bool(done.get("not_found")), "sources": done.get("sources", []),
                "latency_ms": done.get("latency_ms"), "text": final_text})


@app.post("/api/chat")
def chat(body: AskIn, user=Depends(current_user)):
    q = body.question.strip()
    if not q:
        raise HTTPException(400, "Please type a question")
    kb_for(user, body.kb_id)
    if body.conversation_id and not db.one("SELECT id FROM conversations WHERE id=? AND user_id=?", (body.conversation_id, user["id"])):
        raise HTTPException(404, "Conversation not found")
    settings = db.get_settings()
    return StreamingResponse(_run_chat(q[:1000], body.kb_id, body.conversation_id, user["id"], "app", settings),
                             media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


class FeedbackIn(BaseModel):
    value: int  # 1 or -1, 0 clears
    note: str = ""


@app.post("/api/messages/{mid}/feedback")
def feedback(mid: int, body: FeedbackIn, request: Request):
    m = db.one("SELECT m.id, c.user_id, c.channel FROM messages m JOIN conversations c ON c.id=m.conversation_id WHERE m.id=?", (mid,))
    if not m:
        raise HTTPException(404, "Message not found")
    if m["channel"] == "app":
        user = current_user(request)
        if user["id"] != m["user_id"]:
            raise HTTPException(403, "Not your message")
    db.execute("UPDATE messages SET feedback=?, feedback_note=? WHERE id=?", (body.value or None, body.note[:500] or None, mid))
    return {"ok": True}


class HandoffIn(BaseModel):
    message_id: int
    contact: str = ""


@app.post("/api/handoff")
def handoff(body: HandoffIn, request: Request):
    _rate_limit("handoff:" + (request.client.host if request.client else "anon"), per_min=5)
    m = db.one("SELECT m.*, c.user_id FROM messages m JOIN conversations c ON c.id=m.conversation_id WHERE m.id=?", (body.message_id,))
    if not m:
        raise HTTPException(404, "Message not found")
    name = "Website visitor"
    try:
        name = current_user(request)["name"]
    except HTTPException:
        pass
    db.execute("INSERT INTO handoffs(conversation_id, message_id, user_name, question, contact, created_at) VALUES(?,?,?,?,?,?)",
               (m["conversation_id"], m["id"], name, m["question"], body.contact[:200], db.now()))
    return {"ok": True, "message": f"Sent to our team. {db.get_settings().get('human_contact', '')}".strip()}


# --------------------------------------------------------------------------- insights
@app.get("/api/insights")
def insights(days: int = 30, user=Depends(need("admin", "editor"))):
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    week = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    prev_week = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    kbs = {k["id"]: k["name"] for k in visible_kbs(user)}
    msgs = [m for m in db.query("SELECT * FROM messages WHERE role='assistant' AND created_at>=? ORDER BY created_at", (since,)) if m["kb_id"] in kbs]
    this_week = [m for m in msgs if m["created_at"] >= week]
    last_week = [m for m in msgs if prev_week <= m["created_at"] < week]
    ups, downs = sum(m["feedback"] == 1 for m in msgs), sum(m["feedback"] == -1 for m in msgs)
    per_day = defaultdict(lambda: {"answered": 0, "not_found": 0})
    for m in msgs:
        per_day[m["created_at"][:10]]["not_found" if m["not_found"] else "answered"] += 1
    start = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
    series = [{"date": (start + timedelta(days=i)).isoformat(), **per_day.get((start + timedelta(days=i)).isoformat(), {"answered": 0, "not_found": 0})} for i in range(days)]

    def norm(q):
        return re.sub(r"[^a-z0-9؀-ۿ ]", "", (q or "").lower()).strip()
    answered_counter = Counter(norm(m["question"]) for m in msgs if not m["not_found"])
    display = {norm(m["question"]): (m["question"], kbs.get(m["kb_id"])) for m in msgs}
    unanswered = Counter(norm(m["question"]) for m in msgs if m["not_found"])
    last_asked = {}
    for m in msgs:
        last_asked[norm(m["question"])] = m["created_at"]
    feedback_list = [{"id": m["id"], "question": m["question"], "answer": m["content"], "kb": kbs.get(m["kb_id"]), "note": m["feedback_note"],
                      "created_at": m["created_at"]} for m in reversed(msgs) if m["feedback"] == -1][:12]
    handoffs = db.query("SELECT * FROM handoffs ORDER BY created_at DESC LIMIT 10")
    answered_week = sum(not m["not_found"] for m in this_week)
    return {
        "days": days, "is_sample": any(m["is_sample"] for m in msgs),
        "cards": {
            "questions_week": len(this_week), "questions_prev_week": len(last_week),
            "answered_rate": round(100 * answered_week / len(this_week), 1) if this_week else None,
            "not_found_week": sum(m["not_found"] for m in this_week),
            "satisfaction": round(100 * ups / (ups + downs), 1) if ups + downs else None, "ratings": ups + downs,
            "hours_saved_month": round(sum(not m["not_found"] for m in msgs) * STAFF_MINUTES_PER_QUESTION / 60, 1),
            "minutes_per_question": STAFF_MINUTES_PER_QUESTION,
        },
        "series": series,
        "top_questions": [{"question": display[q][0], "kb": display[q][1], "count": n} for q, n in answered_counter.most_common(8)],
        "unanswered": [{"question": display[q][0], "kb": display[q][1], "kb_id": next((m["kb_id"] for m in msgs if norm(m["question"]) == q), None),
                        "count": n, "last_asked": last_asked[q]} for q, n in unanswered.most_common(10)],
        "feedback": feedback_list, "handoffs": handoffs,
        "by_kb": [{"kb": name, "count": sum(m["kb_id"] == kid for m in msgs)} for kid, name in kbs.items()],
        "by_channel": dict(Counter(("Website widget" if db.one("SELECT channel FROM conversations WHERE id=?", (m["conversation_id"],))["channel"] == "widget" else
                                    "WhatsApp" if m["channel"] == "whatsapp" else "Staff app") for m in msgs)),
    }


# --------------------------------------------------------------------------- settings & users
@app.get("/api/settings")
def get_settings(user=Depends(current_user)):
    return db.get_settings()


@app.put("/api/settings")
def put_settings(body: dict, user=Depends(need("admin"))):
    if "accent_color" in body and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(body["accent_color"])):
        raise HTTPException(400, "Colour must look like #0f766e")
    if "tone" in body and body["tone"] not in ("friendly", "formal"):
        raise HTTPException(400, "Tone must be friendly or formal")
    if "languages" in body and (not body["languages"] or not set(body["languages"]) <= {"en", "ur", "roman_ur"}):
        raise HTTPException(400, "Choose at least one language")
    if "retention_days" in body:
        body["retention_days"] = int(body["retention_days"])
    db.set_settings(body)
    apply_retention()
    return db.get_settings()


@app.post("/api/settings/logo")
async def upload_logo(file: UploadFile = File(...), user=Depends(need("admin"))):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".svg", ".webp"):
        raise HTTPException(400, "Please upload a PNG, JPG, SVG or WEBP logo")
    name = f"logo_{secrets.token_hex(4)}{ext}"
    (BRAND_DIR / name).write_bytes(await file.read())
    db.set_settings({"logo_url": f"/brand/{name}"})
    return db.get_settings()


@app.get("/api/users")
def users(user=Depends(need("admin"))):
    return db.query("SELECT id, name, email, role, created_at FROM users ORDER BY id")


class UserIn(BaseModel):
    name: str
    email: str
    role: str = "member"


@app.post("/api/users")
def add_user(body: UserIn, user=Depends(need("admin"))):
    if body.role not in ("admin", "editor", "member"):
        raise HTTPException(400, "Role must be admin, editor or member")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", body.email.strip()):
        raise HTTPException(400, "Please enter a valid email")
    if db.one("SELECT id FROM users WHERE lower(email)=lower(?)", (body.email.strip(),)):
        raise HTTPException(400, "This person already has access")
    temp = secrets.token_urlsafe(6)
    db.execute("INSERT INTO users(email, name, role, password_hash, created_at) VALUES(?,?,?,?,?)",
               (body.email.strip(), body.name.strip() or body.email, body.role, db.hash_password(temp), db.now()))
    return {"ok": True, "temporary_password": temp}


@app.patch("/api/users/{uid}")
def change_role(uid: int, body: dict, user=Depends(need("admin"))):
    if body.get("role") not in ("admin", "editor", "member"):
        raise HTTPException(400, "Role must be admin, editor or member")
    if uid == user["id"]:
        raise HTTPException(400, "You can't change your own role")
    db.execute("UPDATE users SET role=? WHERE id=?", (body["role"], uid))
    return {"ok": True}


@app.delete("/api/users/{uid}")
def remove_user(uid: int, user=Depends(need("admin"))):
    if uid == user["id"]:
        raise HTTPException(400, "You can't remove yourself")
    db.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
    db.execute("DELETE FROM kb_access WHERE user_id=?", (uid,))
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    return {"ok": True}


# --------------------------------------------------------------------------- public: website widget & WhatsApp
_rate = defaultdict(list)


def _rate_limit(key: str, per_min=12):
    now = time.time()
    _rate[key] = [t for t in _rate[key] if now - t < 60]
    if len(_rate[key]) >= per_min:
        raise HTTPException(429, "Too many questions at once. Please wait a moment.")
    _rate[key].append(now)


def _public_kb(slug: str | None):
    kb = db.one("SELECT * FROM knowledge_bases WHERE is_public=1 AND (slug=? OR ?='') ORDER BY id LIMIT 1", (slug or "", slug or ""))
    if not kb:
        raise HTTPException(404, "No public knowledge base is set up for the website widget")
    return kb


@app.get("/api/public/config")
def public_config(kb: str = ""):
    k = _public_kb(kb)
    s = db.get_settings()
    return {"kb": k["slug"], "kb_name": k["name"], "suggested": json.loads(k["suggested_json"] or "[]")[:3], "bot_name": s["bot_name"],
            "company_name": s["company_name"], "greeting": s["widget_greeting"], "accent_color": s["accent_color"], "logo_url": s["logo_url"],
            "human_contact": s["human_contact"]}


class PublicAskIn(BaseModel):
    question: str
    kb: str = ""
    conversation_id: int | None = None


@app.post("/api/public/chat")
def public_chat(body: PublicAskIn, request: Request):
    _rate_limit(request.client.host if request.client else "anon")
    kb = _public_kb(body.kb)
    q = body.question.strip()[:600]
    if not q:
        raise HTTPException(400, "Please type a question")
    cid = body.conversation_id
    if cid and not db.one("SELECT id FROM conversations WHERE id=? AND channel='widget' AND kb_id=?", (cid, kb["id"])):
        cid = None
    return StreamingResponse(_run_chat(q, kb["id"], cid, None, "widget", db.get_settings()), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/public/documents/{doc_id}/file")
def public_file(doc_id: int):
    d = db.one("SELECT d.* FROM documents d JOIN knowledge_bases k ON k.id=d.kb_id WHERE d.id=? AND k.is_public=1", (doc_id,))
    if not d:
        raise HTTPException(404, "Document not found")
    return FileResponse(d["stored_path"], filename=d["filename"], content_disposition_type="inline")


@app.get("/api/whatsapp/webhook")
def whatsapp_verify(request: Request):
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(p.get("hub.challenge", ""))
    raise HTTPException(403, "Verification failed")


@app.post("/api/whatsapp/webhook")
async def whatsapp_incoming(request: Request):
    """WhatsApp Cloud API: answer text messages from the configured knowledge base."""
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID):
        return {"ok": False, "reason": "WhatsApp is not configured"}
    payload = await request.json()
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("type") != "text":
                    continue
                threading.Thread(target=_whatsapp_reply, args=(msg["from"], msg["text"]["body"]), daemon=True).start()
    return {"ok": True}


def _whatsapp_reply(to: str, question: str):
    import urllib.request
    kb = db.one("SELECT * FROM knowledge_bases WHERE slug=?", (WHATSAPP_KB,)) if WHATSAPP_KB else _public_kb("")
    conv = db.one("SELECT id FROM conversations WHERE channel='whatsapp' AND title=? ORDER BY id DESC LIMIT 1", (f"wa:{to}",))
    now = db.now()
    cid = conv["id"] if conv else db.execute("INSERT INTO conversations(user_id, kb_id, title, channel, created_at, updated_at) VALUES(NULL,?,?,?,?,?)",
                                             (kb["id"], f"wa:{to}", "whatsapp", now, now))
    history = _history(cid)
    a = answer.answer_text(question, history, kb["id"], db.get_settings())
    db.execute("INSERT INTO messages(conversation_id, role, content, kb_id, channel, created_at) VALUES(?,?,?,?,?,?)", (cid, "user", question, kb["id"], "whatsapp", now))
    db.execute("INSERT INTO messages(conversation_id, role, content, question, sources_json, not_found, latency_ms, engine, kb_id, channel, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
               (cid, "assistant", a["text"], question, json.dumps(a.get("sources", [])), int(bool(a.get("not_found"))), a.get("latency_ms"), a.get("engine"), kb["id"], "whatsapp", db.now()))
    body = re.sub(r"\[\d+\]", "", a["text"]).strip()
    if a.get("sources"):
        s = a["sources"][0]
        link = f"{PUBLIC_BASE_URL}/api/public/documents/{s['doc_id']}/file" + (f"#page={s['page']}" if s.get("page") else "") if PUBLIC_BASE_URL else ""
        page = f", page {s['page']}" if s.get("page") else ""
        body += f"\n\nSource: {s['filename']}{page}" + (f"\n{link}" if link else "")
    req = urllib.request.Request(f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_ID}/messages", method="POST",
                                 data=json.dumps({"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body[:4000]}}).encode(),
                                 headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:
        log.warning("WhatsApp send failed: %s", e)


# --------------------------------------------------------------------------- pages
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")


@app.get("/widget.js")
def widget_js():
    return FileResponse(STATIC_DIR / "widget" / "widget.js", media_type="application/javascript", headers={"Cache-Control": "no-cache"})


@app.get("/widget")
def widget_page():
    return FileResponse(STATIC_DIR / "widget" / "widget.html", headers={"Cache-Control": "no-cache"})


@app.get("/demo-site")
def demo_site():
    return FileResponse(STATIC_DIR / "widget" / "demo-site.html")


@app.get("/landing")
def landing():
    return FileResponse(STATIC_DIR / "landing.html")


@app.get("/privacy")
def privacy():
    return FileResponse(STATIC_DIR / "privacy.html")


@app.get("/health")
def health():
    return {"ok": True, "ready": READY["seeded"], "ai_enabled": ai_enabled()}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": getattr(exc, "detail", "Not found")}, status_code=404)
    return RedirectResponse("/")
