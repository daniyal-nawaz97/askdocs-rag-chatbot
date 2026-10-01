import hashlib
import json
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import DB_PATH

_lock = threading.RLock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member', password_hash TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL, description TEXT,
    icon TEXT DEFAULT 'book', visibility TEXT NOT NULL DEFAULT 'everyone', is_public INTEGER NOT NULL DEFAULT 0,
    suggested_json TEXT DEFAULT '[]', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS kb_access (kb_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY (kb_id, user_id));
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT, kb_id INTEGER NOT NULL, filename TEXT NOT NULL, title TEXT, file_type TEXT,
    stored_path TEXT, pages INTEGER DEFAULT 0, chunks INTEGER DEFAULT 0, status TEXT NOT NULL, error TEXT,
    version INTEGER NOT NULL DEFAULT 1, is_sample INTEGER NOT NULL DEFAULT 0, uploaded_by TEXT,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER NOT NULL, kb_id INTEGER NOT NULL, position INTEGER NOT NULL,
    page INTEGER, heading TEXT, text TEXT NOT NULL, boxes_json TEXT, page_w REAL, page_h REAL, embedding BLOB);
CREATE INDEX IF NOT EXISTS idx_chunks_kb ON chunks(kb_id);
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, kb_id INTEGER NOT NULL, title TEXT, channel TEXT NOT NULL DEFAULT 'app',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL,
    question TEXT, sources_json TEXT DEFAULT '[]', not_found INTEGER DEFAULT 0, feedback INTEGER, feedback_note TEXT,
    latency_ms INTEGER, engine TEXT, kb_id INTEGER, channel TEXT DEFAULT 'app', is_sample INTEGER DEFAULT 0, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);
CREATE TABLE IF NOT EXISTS handoffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER, message_id INTEGER, user_name TEXT, question TEXT,
    contact TEXT, status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

DEFAULT_SETTINGS = {
    "company_name": "Nimbus Home Appliances",
    "bot_name": "Nimbus Assistant",
    "welcome_message": "Hi! I answer questions from Nimbus company documents: HR policies, IT help and products. Every answer shows its source.",
    "tone": "friendly",                # friendly | formal
    "languages": ["en", "ur", "roman_ur"],
    "fallback_message": "I couldn't find this in the documents.",
    "human_contact": "HR at hr@nimbus-appliances.example or extension 210",
    "accent_color": "#0f766e",
    "logo_url": "",
    "retention_days": 90,              # chat history kept for this many days (0 = forever)
    "widget_greeting": "Hi there! Ask me about products, delivery, returns or warranty.",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def tx():
    global _conn
    with _lock:
        if _conn is None:
            _conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield _conn
            _conn.commit()
        except Exception:
            _conn.rollback()
            raise


def query(sql, params=()):
    with tx() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def one(sql, params=()):
    r = query(sql, params)
    return r[0] if r else None


def execute(sql, params=()):
    with tx() as c:
        return c.execute(sql, params).lastrowid


def hash_password(pw: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 120_000).hex()}"


def check_password(pw: str, stored: str | None) -> bool:
    if not stored or "$" not in stored:
        return False
    return secrets.compare_digest(hash_password(pw, stored.split("$", 1)[0]), stored)


def get_settings() -> dict:
    out = dict(DEFAULT_SETTINGS)
    for r in query("SELECT key, value FROM settings"):
        out[r["key"]] = json.loads(r["value"])
    return out


def set_settings(values: dict):
    with tx() as c:
        for k, v in values.items():
            if k in DEFAULT_SETTINGS:
                c.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, json.dumps(v)))


def init_schema():
    with tx() as c:
        c.executescript(SCHEMA)
