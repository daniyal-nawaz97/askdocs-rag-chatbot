"""Hybrid search: keyword (BM25) + meaning (local embedding model), per knowledge base."""
from __future__ import annotations

import logging
import math
import re
import threading

import numpy as np

from . import db
from .config import EMBED_MODEL, MODEL_DIR, USE_EMBEDDINGS

log = logging.getLogger("askdocs.search")

STOP = set("""a an the is are was were be been being am do does did to of in on at for from by with and or but if then than
so as it its this that these those i me my we our you your he she they them their what which who whom whose when where why how
can could should would will shall may might must have has had not no yes please tell about any some there here get got give
into out up down over under again also just only very much many more most such own same other each all both few one
kya hai hain ka ki ke ko se mein main mujhe hum aap ap koi bhi kar karna take takes need needs quickly soon
long often happen happens come comes use using make want know allowed possible able""".split())

# Roman Urdu / Urdu words -> English search terms (used for retrieval; the AI mode also understands them directly)
ROMAN = {
    "chutti": "leave", "chuttiyan": "leave", "chutiyan": "leave", "chhutti": "leave", "chhuttiyan": "leave", "chutti's": "leave",
    "kitni": "how many", "kitne": "how many", "kitna": "how much", "saal": "year", "sal": "year", "mahina": "month", "mahine": "month",
    "milti": "entitled", "milta": "entitled", "milte": "entitled", "tankhwah": "salary", "tankhwa": "salary", "tankha": "salary",
    "wapsi": "refund return", "wapas": "return", "paise": "refund", "paisay": "refund", "din": "days", "dino": "days", "dinon": "days",
    "kab": "when", "kahan": "where", "waqt": "hours time", "timing": "hours", "timings": "hours", "daftar": "office",
    "bimari": "sick", "beemari": "sick", "bemari": "sick", "shadi": "marriage", "bacha": "child", "bachay": "child",
    "qist": "installments", "qiston": "installments", "kharab": "broken damaged repair", "toota": "damaged", "tuta": "damaged",
    "bhool": "forgot reset", "bhul": "forgot reset", "ghar": "home remote", "kaam": "work", "naukri": "job careers",
    "garanti": "warranty", "guarantee": "warranty", "bijli": "electricity", "keemat": "price", "qeemat": "price",
    "chahiye": "", "hoti": "", "hota": "", "karta": "", "karte": "", "sakta": "", "sakte": "", "liye": "", "wala": "", "wali": "",
    "چھٹی": "leave", "چھٹیاں": "leave", "چھٹیوں": "leave", "تنخواہ": "salary", "واپسی": "refund return", "کتنی": "how many",
    "کتنے": "how many", "سال": "year", "دن": "days", "وارنٹی": "warranty", "قیمت": "price", "ڈیلیوری": "delivery",
    "پاس": "", "ورڈ": "", "بیماری": "sick", "دفتر": "office", "اوقات": "hours",
}
SYNONYMS = {
    "leaves": "leave", "holiday": "leave", "holidays": "leave public", "vacation": "annual leave", "off": "leave",
    "wfh": "remote work home", "salary": "salary pay", "pay": "salary", "paid": "salary", "refund": "refund refunds", "money": "refund",
    "broken": "damaged repair", "fix": "repair", "shipping": "delivery", "ship": "delivery", "deliver": "delivery", "cost": "price charge",
    "price": "price", "phone": "helpline", "contact": "helpline email support", "timing": "hours", "open": "hours",
    "ac": "aircool air-conditioner conditioner", "drive": "storage device", "usb": "usb storage", "fridge": "refrigerator", "washer": "washing machine washpro", "pwd": "password",
    "login": "password sign", "internet": "wi-fi wifi", "wifi": "wi-fi", "claim": "claim warranty", "expenses": "reimbursement",
    "expense": "reimbursement", "reimburse": "reimbursement", "installment": "installments", "emi": "installments",
}


def stem(w: str) -> str:
    """Light English stemmer so 'changed/changes/change' and 'arrives/arrived' match."""
    if not w.isascii() or w.isdigit():
        return w
    if len(w) > 5 and w.endswith("ied"):
        w = w[:-3] + "y"
    elif len(w) > 5 and w.endswith("ing"):
        w = w[:-3]
    elif len(w) > 4 and w.endswith("ed"):
        w = w[:-2]
    if len(w) > 4 and w.endswith("ies"):
        w = w[:-3] + "y"
    elif len(w) > 4 and w.endswith("es") and w[-3] in "sxz":
        w = w[:-2]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    if len(w) > 4 and w.endswith("e"):
        w = w[:-1]
    return w


def tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?|[؀-ۿ]+", text.lower().replace("'s ", " ").replace("’s ", " "))
    return [stem(t) for t in raw if t not in STOP and (len(t) > 1 or t.isdigit())]


def query_groups(q: str) -> list[set[str]]:
    """One group per meaningful word of the question: the word plus its synonyms / translations (any of them counts)."""
    words = re.findall(r"\w+(?:-\w+)+|[\w']+|[؀-ۿ]+", q.lower())  # keep "part-time", "two-step" whole
    groups = []
    for w in words:
        if w in ROMAN:
            alts = ROMAN[w]
        elif not w.isascii():
            continue  # Urdu words we don't know yet would only dilute the search
        else:
            alts = f"{w} {SYNONYMS.get(w, '')}"
        g = set(tokens(alts))
        if g:
            groups.append(g)
    return groups


def expand_query(q: str) -> str:
    return " ".join(t for g in query_groups(q) for t in sorted(g))


# --------------------------------------------------------------------------- embeddings
_model = None
_model_lock = threading.Lock()
_model_failed = False


def _get_model():
    global _model, _model_failed
    if not USE_EMBEDDINGS or _model_failed:
        return None
    with _model_lock:
        if _model is None:
            try:
                from fastembed import TextEmbedding
                _model = TextEmbedding(EMBED_MODEL, cache_dir=str(MODEL_DIR))
            except Exception as e:
                log.warning("Embedding model unavailable, using keyword search only: %s", e)
                _model_failed = True
                return None
        return _model


def embeddings_active() -> bool:
    return _get_model() is not None


def embed_passages(texts: list[str]):
    m = _get_model()
    if m is None:
        return None
    with _model_lock:
        return np.array(list(m.embed(texts, batch_size=32)), dtype=np.float32)


def embed_query(text: str):
    m = _get_model()
    if m is None:
        return None
    with _model_lock:
        return np.array(list(m.query_embed([text]))[0], dtype=np.float32)


# --------------------------------------------------------------------------- index
class Index:
    def __init__(self, kb_id: int):
        from rank_bm25 import BM25Okapi
        rows = db.query("SELECT c.id, c.doc_id, c.page, c.heading, c.text, c.embedding, d.filename, d.title, d.file_type "
                        "FROM chunks c JOIN documents d ON d.id=c.doc_id WHERE c.kb_id=? AND d.status='ready' ORDER BY c.doc_id, c.position", (kb_id,))
        self.rows = rows
        self.toks = [tokens(f"{(r['title'] or r['filename']).replace('_', ' ')} {r['heading'] or ''} {r['heading'] or ''} {r['text']}") for r in rows]
        self.bm25 = BM25Okapi(self.toks) if rows else None
        embs = [np.frombuffer(r["embedding"], dtype=np.float32) for r in rows if r["embedding"]]
        self.emb = np.vstack(embs) if rows and len(embs) == len(rows) else None
        df = {}
        for t in self.toks:
            for w in set(t):
                df[w] = df.get(w, 0) + 1
        n = max(1, len(rows))
        self.idf = {w: math.log(1 + n / c) for w, c in df.items()}

    def knows(self, text: str) -> bool:
        """True if any meaningful word of the text appears in this knowledge base."""
        return any(g & self.idf.keys() for g in query_groups(text))

    def group_weights(self, groups):
        """Rare words matter more than common ones; bare numbers matter little."""
        return [0.3 if all(t.isdigit() for t in g) else max(self.idf.get(t, 2.5) for t in g) for g in groups]

    def coverage(self, groups, toks: set) -> float:
        w = self.group_weights(groups)
        total = sum(w) or 1.0
        return sum(wi for g, wi in zip(groups, w) if g & toks) / total

    def search(self, query: str, k: int = 5):
        if not self.rows:
            return []
        groups = query_groups(query)
        q_toks = [t for g in groups for t in sorted(g)]
        bm = np.array(self.bm25.get_scores(q_toks)) if q_toks else np.zeros(len(self.rows))
        bm_n = bm / bm.max() if bm.max() > 0 else bm
        cos = None
        if self.emb is not None:
            qv = embed_query(query)
            if qv is not None:
                cos = self.emb @ qv
        if cos is not None:
            cos_n = np.clip((cos - 0.45) / 0.35, 0, 1)
            score = 0.5 * bm_n + 0.5 * cos_n
        else:
            score = bm_n
        # keep variety: a document's 2nd, 3rd... passage counts a little less, so other documents get a chance
        ranked, per_doc = [], {}
        for i in np.argsort(-score)[: k * 3]:
            d = self.rows[i]["doc_id"]
            ranked.append((score[i] * (0.85 ** per_doc.get(d, 0)), i))
            per_doc[d] = per_doc.get(d, 0) + 1
        order = [i for _, i in sorted(ranked, key=lambda x: -x[0])[:k]]
        out = []
        for i in order:
            r = dict(self.rows[i])
            r.pop("embedding", None)
            chunk_toks = set(self.toks[i])
            r.update(score=float(score[i]), bm25=float(bm_n[i]), cos=float(cos[i]) if cos is not None else None,
                     coverage=self.coverage(groups, chunk_toks), q_tokens=q_toks, q_groups=groups, group_weights=self.group_weights(groups))
            out.append(r)
        return out


_indexes: dict[int, Index] = {}
_idx_lock = threading.Lock()


def get_index(kb_id: int) -> Index:
    with _idx_lock:
        if kb_id not in _indexes:
            _indexes[kb_id] = Index(kb_id)
        return _indexes[kb_id]


def invalidate(kb_id: int | None = None):
    with _idx_lock:
        if kb_id is None:
            _indexes.clear()
        else:
            _indexes.pop(kb_id, None)


FOLLOW_UP = re.compile(r"^\s*(and|also|what about|how about|for|aur|or|what if|same for|in that case|then)\b|\b(it|that|this|those|them|they|us|wo|woh|isk[aie]|unk[aie])\b", re.I)


def standalone_query(question: str, history: list[str]) -> str:
    """Offline follow-up handling: short or referring questions borrow the previous question's words."""
    if not history:
        return question
    content = [t for t in tokens(expand_query(question))]
    if len(content) <= 4 or FOLLOW_UP.search(question):
        prev = history[-1]
        q_toks = set(content)
        if q_toks & set(tokens(expand_query(prev))):
            # same subject, new detail ("How many casual leaves?" -> "and sick leaves?"): drop the old detail words
            prev = " ".join(w for w in re.findall(r"\S+", prev)
                            if not set(tokens(expand_query(w))) - q_toks)
        return f"{question} {prev}"
    return question
