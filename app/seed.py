"""Demo company setup: knowledge bases, documents, users and a few weeks of sample activity (clearly marked as sample)."""
from __future__ import annotations

import json
import random
import shutil
from datetime import datetime, timedelta, timezone

from . import db, ingest
from .config import DEMO_EMAIL, DEMO_PASSWORD, FILES_DIR, SAMPLE_DIR

KBS = [
    {"slug": "hr", "name": "HR Policies", "icon": "users", "description": "Leave, working hours, benefits and conduct",
     "docs": ["HR_Policy.pdf"], "visibility": "everyone", "public": 0,
     "suggested": ["How many casual leaves do I get?", "Can I work from home?", "How do I claim medical reimbursement?", "What are the office hours in Ramadan?"]},
    {"slug": "it", "name": "IT Help", "icon": "laptop", "description": "Passwords, VPN, laptops and security",
     "docs": ["IT_Help_Guide.pdf"], "visibility": "everyone", "public": 0,
     "suggested": ["How do I reset my password?", "How do I connect to the VPN from home?", "My laptop is broken. What should I do?"]},
    {"slug": "products", "name": "Products & Support", "icon": "box", "description": "Catalogue, delivery, returns and warranty",
     "docs": ["Product_Catalogue.pdf", "Refund_and_Warranty_Policy.pdf", "Shipping_and_Delivery_Policy.docx", "Company_FAQ.txt"],
     "visibility": "everyone", "public": 1,
     "suggested": ["What is the warranty on the AirCool AC?", "How long does a refund take?", "Do you offer installments?", "How much is delivery?"]},
    {"slug": "management", "name": "Management", "icon": "lock", "description": "Confidential: salary bands (admins only)",
     "docs": ["Salary_Bands_2026.pdf"], "visibility": "restricted", "public": 0,
     "suggested": ["What is the salary range for grade G3?"]},
]

# question pool for sample activity: (kb, question, weight)
ACTIVITY = [
    ("hr", "How many casual leaves do I get?", 14), ("hr", "Can I work from home?", 9), ("hr", "What are the office hours?", 7),
    ("hr", "How do I claim medical reimbursement?", 6), ("hr", "What is the notice period?", 5), ("hr", "How many sick leaves do I get?", 5),
    ("hr", "Can I carry forward annual leave?", 4), ("hr", "What is the fuel allowance?", 3), ("hr", "What is the maternity leave policy?", 2),
    ("hr", "Is there a gym membership benefit?", 3), ("hr", "What is the dress code on Fridays?", 2), ("hr", "Mujhe kitni casual chuttiyan milti hain?", 3),
    ("it", "How do I reset my password?", 11), ("it", "How do I connect to the VPN from home?", 6), ("it", "My laptop is broken. What should I do?", 5),
    ("it", "What is the guest Wi-Fi password?", 4), ("it", "How do I install software?", 3), ("it", "Can I use a USB drive?", 2),
    ("it", "How do I get a second monitor?", 2),
    ("products", "How long does a refund take?", 10), ("products", "What is the warranty on the AirCool AC?", 8),
    ("products", "Do you offer installments?", 7), ("products", "How much is delivery?", 6), ("products", "Do you deliver to Quetta?", 3),
    ("products", "Is cash on delivery available?", 5), ("products", "What is the price of the 18 cu ft refrigerator?", 4),
    ("products", "Do you sell televisions?", 3), ("products", "Refund kitne din mein milta hai?", 2),
]
DISLIKED = {"How do I get a second monitor?", "Do you deliver to Quetta?"}


def seed(force=False):
    db.init_schema()
    if db.one("SELECT id FROM knowledge_bases LIMIT 1") and not force:
        return
    now = db.now()
    users = [(DEMO_EMAIL, "Demo Admin", "admin", DEMO_PASSWORD), ("sara@nimbus-appliances.example", "Sara Ahmed", "member", None),
             ("bilal@nimbus-appliances.example", "Bilal Khan", "editor", None)]
    for email, name, role, pw in users:
        db.execute("INSERT OR IGNORE INTO users(email, name, role, password_hash, created_at) VALUES(?,?,?,?,?)",
                   (email, name, role, db.hash_password(pw) if pw else None, now))
    for kb in KBS:
        kb_id = db.execute("INSERT INTO knowledge_bases(slug, name, description, icon, visibility, is_public, suggested_json, created_at) VALUES(?,?,?,?,?,?,?,?)",
                           (kb["slug"], kb["name"], kb["description"], kb["icon"], kb["visibility"], kb["public"], json.dumps(kb["suggested"]), now))
        for fname in kb["docs"]:
            src = SAMPLE_DIR / fname
            dest = FILES_DIR / f"sample_{fname}"
            shutil.copy(src, dest)
            ext = src.suffix.lower().lstrip(".")
            doc_id = db.execute("INSERT INTO documents(kb_id, filename, title, file_type, stored_path, status, is_sample, uploaded_by, created_at, updated_at) "
                                "VALUES(?,?,?,?,?,?,?,?,?,?)", (kb_id, fname, src.stem.replace("_", " "), "txt" if ext == "md" else ext, str(dest),
                                                                 "queued", 1, "Demo Admin", now, now))
            ingest.ingest_document(doc_id)


def seed_activity(days=21, seed_value=7):
    """Real answers from the engine to a realistic question mix, spread over past days. Marked is_sample=1."""
    from .answer import answer_text
    if db.one("SELECT id FROM messages WHERE is_sample=1 LIMIT 1"):
        return
    rng = random.Random(seed_value)
    settings = db.get_settings()
    kbs = {k["slug"]: k["id"] for k in db.query("SELECT id, slug FROM knowledge_bases")}
    pool = [(kb, q) for kb, q, w in ACTIVITY for _ in range(w)]
    cache = {}
    member = db.one("SELECT id FROM users WHERE email='sara@nimbus-appliances.example'")
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    for day in range(days, 0, -1):
        date = today - timedelta(days=day)
        if date.weekday() == 6:
            continue
        n = rng.randint(4, 9) + (days - day) // 4  # usage grows as staff adopt it
        for _ in range(n):
            kb, q = rng.choice(pool)
            if (kb, q) not in cache:
                cache[(kb, q)] = answer_text(q, [], kbs[kb], settings)
            a = cache[(kb, q)]
            ts = (date + timedelta(hours=rng.randint(9, 17), minutes=rng.randint(0, 59))).isoformat(timespec="seconds")
            conv = db.execute("INSERT INTO conversations(user_id, kb_id, title, channel, created_at, updated_at) VALUES(?,?,?,?,?,?)",
                              (member["id"], kbs[kb], q[:60], "widget" if kb == "products" and rng.random() < 0.5 else "app", ts, ts))
            db.execute("INSERT INTO messages(conversation_id, role, content, kb_id, is_sample, created_at) VALUES(?,?,?,?,1,?)", (conv, "user", q, kbs[kb], ts))
            fb = None
            r = rng.random()
            if q in DISLIKED or a.get("not_found"):
                fb = -1 if r < 0.35 else None
            elif r < 0.45:
                fb = 1
            elif r < 0.49:
                fb = -1
            db.execute("INSERT INTO messages(conversation_id, role, content, question, sources_json, not_found, feedback, latency_ms, engine, kb_id, channel, is_sample, created_at) "
                       "VALUES(?,?,?,?,?,?,?,?,?,?,?,1,?)",
                       (conv, "assistant", a["text"], q, json.dumps(a.get("sources", [])), int(bool(a.get("not_found"))), fb,
                        rng.randint(700, 1900), a.get("engine", "offline"), kbs[kb], "app", ts))


def seed_demo_chats(user_id: int):
    """Two saved conversations for the demo user so chat history isn't empty."""
    from .answer import answer_text
    if db.one("SELECT id FROM conversations WHERE user_id=? LIMIT 1", (user_id,)):
        return
    settings = db.get_settings()
    kbs = {k["slug"]: k["id"] for k in db.query("SELECT id, slug FROM knowledge_bases")}
    for kb, qs, ago in [("it", ["How do I reset my password?"], 2), ("products", ["How long does a refund take?", "And for cash on delivery orders?"], 1)]:
        ts = (datetime.now(timezone.utc) - timedelta(days=ago)).isoformat(timespec="seconds")
        conv = db.execute("INSERT INTO conversations(user_id, kb_id, title, channel, created_at, updated_at) VALUES(?,?,?,?,?,?)",
                          (user_id, kbs[kb], qs[0][:60], "app", ts, ts))
        history = []
        for q in qs:
            a = answer_text(q, history, kbs[kb], settings)
            db.execute("INSERT INTO messages(conversation_id, role, content, kb_id, is_sample, created_at) VALUES(?,?,?,?,0,?)", (conv, "user", q, kbs[kb], ts))
            db.execute("INSERT INTO messages(conversation_id, role, content, question, sources_json, not_found, latency_ms, engine, kb_id, is_sample, created_at) "
                       "VALUES(?,?,?,?,?,?,?,?,?,0,?)", (conv, "assistant", a["text"], q, json.dumps(a.get("sources", [])), int(bool(a.get("not_found"))),
                                                          a.get("latency_ms"), a.get("engine"), kbs[kb], ts))
            history += [{"role": "user", "content": q}, {"role": "assistant", "content": a["text"]}]
