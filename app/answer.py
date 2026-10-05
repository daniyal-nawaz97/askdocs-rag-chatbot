"""Answer a question from the knowledge base, always with sources, and say so when the answer is not there."""
from __future__ import annotations

import json
import logging
import re
import time

from . import search
from .config import GROQ_API_KEY, GROQ_MODEL, ai_enabled

log = logging.getLogger("askdocs.answer")

# Offline "is the answer in the documents?" thresholds (tuned with scripts/evaluate.py)
MIN_COVERAGE = 0.5
MIN_COS = 0.6
QUANTITY = re.compile(r"\b(how many|how much|how long|how soon|how quickly|when|what time|kitni|kitne|kitna|kab|price|cost|limit|minimum|maximum)\b|کتنی|کتنے", re.I)

_client = None


def _groq():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=GROQ_API_KEY, timeout=45, max_retries=1)
    return _client


def _sentences(hit):
    text = hit["text"]
    out = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        if len(block) < 140 and not re.search(r"[.!?]$", block):
            out.append(block)  # table row or short line
            continue
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", block) if s.strip()]
    return out


def _source(hit, passage=None):
    return {"chunk_id": hit["id"], "doc_id": hit["doc_id"], "filename": hit["filename"], "title": hit["title"],
            "page": hit["page"], "heading": hit["heading"], "file_type": hit["file_type"],
            "passage": passage or hit["text"][:400]}


def is_found(hits) -> bool:
    if not hits:
        return False
    top = hits[0]
    if top["coverage"] >= 0.75:
        return True
    if top["coverage"] >= MIN_COVERAGE and (top["cos"] is None or top["cos"] >= MIN_COS):
        return True
    if top["coverage"] >= 0.65 and top["cos"] is not None and top["cos"] >= 0.55:
        return True
    return top["cos"] is not None and top["cos"] >= 0.78 and top["coverage"] >= 0.3


def offline_answer(question: str, hits: list[dict], focus: str | None = None):
    """Pick the one or two sentences that best answer the question. Returns (text, sources)."""
    if not hits:
        return None, []
    groups, weights = hits[0]["q_groups"], hits[0]["group_weights"]
    total = sum(weights) or 1.0
    wants_number = bool(QUANTITY.search(question))
    focus_groups = search.query_groups(focus) if focus and focus != question else []
    cands = []
    for rank, h in enumerate(hits[:4]):
        head_toks = set(search.tokens(f"{h['heading'] or ''} {h['title'] or ''}"))
        for pos, s in enumerate(_sentences(h)):
            st = set(search.tokens(s)) | head_toks  # the section heading gives a sentence its context
            overlap = frozenset(i for i, g in enumerate(groups) if g & st)
            if not any(g & set(search.tokens(s)) for g in groups):
                continue
            cov = sum(weights[i] for i in overlap) / total  # rare words count more than common ones or digits
            score = cov + 0.45 * h["score"] - 0.06 * rank
            if focus_groups:  # follow-up: what the person just asked matters most
                score += 0.4 * sum(1 for g in focus_groups if g & st) / len(focus_groups)
            if wants_number and re.search(r"\d", s):
                score += 0.15
            if len(s) > 320:
                score -= 0.12
            score -= 0.015 * min(pos, 8)  # the rule usually comes before its exceptions
            if re.match(r"^(\d+\.\s|[A-Z][A-Za-z ]+$)", s) and len(s) < 45:
                score -= 0.3  # a heading, not an answer
            cands.append((score, s, h, overlap))
    if focus_groups:
        # a follow-up ("And for part-time staff?") must be answered by a sentence about what was just asked
        on_topic = [c for c in cands if any(g & set(search.tokens(c[1])) for g in focus_groups)]
        literal = set(search.tokens(focus))  # the exact words they used beat synonyms ("claim" over "warranty")
        exact = [c for c in on_topic if literal & set(search.tokens(c[1]))]
        cands = exact or on_topic or cands
    if not cands:
        return None, []
    cands.sort(key=lambda c: -c[0])
    best = cands[0]
    chosen = [best]
    for c in cands[1:8]:
        new_terms = {i for i in c[3] - best[3] if weights[i] > 0.3}
        shared = {i for i in c[3] & best[3] if weights[i] > 0.3}
        # a second sentence must add something the question asked AND be about the same thing as the first
        if c[1] != best[1] and new_terms and shared and c[0] >= best[0] * 0.6:
            chosen.append(c)
            break
    answered = set().union(*(c[3] for c in chosen))
    if sum(weights[i] for i in answered) / total < 0.45:
        return None, []  # the best sentences don't really answer this question
    text = " ".join(c[1] if c[1].endswith((".", "!", "?")) else c[1] + "." for c in chosen)
    sources, seen = [], set()
    for c in chosen:
        if c[2]["id"] not in seen:
            seen.add(c[2]["id"])
            sources.append(_source(c[2], c[1]))
    return text, sources


SYSTEM = """You are {bot}, the assistant for {company}. You answer questions using ONLY the numbered passages from company documents given below.
Rules:
- If the passages do not contain the answer, reply with exactly: NOT_FOUND
- Never use outside knowledge and never guess. Do not mention passages that don't help.
- Cite the passages you used with their numbers in square brackets, e.g. [1] or [1][3], right after the sentence they support.
- Keep answers short: 1-3 sentences, or a few bullet points only when listing several items.
- Tone: {tone}.
- Reply in the same language as the question ({langs}). For Roman Urdu questions, reply in Roman Urdu."""

REWRITE = """Rewrite the user's last question as one standalone search query in English, using the conversation for context.
Return only the query text, nothing else."""


def rewrite_question(question: str, history: list[dict]) -> str:
    if not history:
        return question
    try:
        convo = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in history[-6:])
        r = _groq().chat.completions.create(model=GROQ_MODEL, temperature=0, max_tokens=60, messages=[
            {"role": "system", "content": REWRITE}, {"role": "user", "content": f"{convo}\nuser: {question}"}])
        q = r.choices[0].message.content.strip().strip('"')
        return q or question
    except Exception as e:
        log.warning("rewrite failed: %s", e)
        return search.standalone_query(question, [m["content"] for m in history if m["role"] == "user"])


SMALL_TALK = [
    (r"how are (you|u)|how r u|how('?s| is) it going|kya hal|kia hal|kaise ho|kese ho|kaisay ho|aap kaise", "I'm doing well, thank you!"),
    (r"^(hi+|hello+|hey+|salam|salaam|a?s+alam\w*( ?[ou])? ?(alaikum|alykum|alaykum)|asalam|aoa|good (morning|afternoon|evening))\b", "Hello!"),
    (r"^(thanks?|thank you|thx|shukriya|jazakallah|great|ok(ay)?|nice|perfect|got it|cool)\b", "You're welcome!"),
    (r"^(bye|goodbye|allah hafiz|khuda hafiz|see you)\b", "Goodbye! Come back any time."),
    (r"who are you|what are you|what can you do|tum kaun|aap kaun|are you (a )?(bot|human|ai)", "I'm an assistant that answers from your company documents."),
]


def small_talk(question: str, settings: dict) -> str | None:
    """Greetings, thanks and 'how are you' get a friendly reply instead of a document search."""
    q = re.sub(r"[^\w\s']", " ", question.lower()).strip()
    q = re.sub(r"\s+(ha|na|yar|yaar|bro|please|pls|ji|sir|madam)$", "", re.sub(r"\s+", " ", q))
    if len(q.split()) > 7:
        return None
    for pat, reply in SMALL_TALK:
        if re.search(pat, q):
            if search.tokens(search.expand_query(re.sub(pat, " ", q))):
                return None  # "hi, how many leaves do I get?" is a real question
            name = settings.get("bot_name") or "the assistant"
            return f"{reply} I'm {name}. Ask me anything about the documents in this knowledge base, for example a policy, a product or a procedure, and I'll answer with the source."
    return None


def stream_answer(question: str, history: list[dict], kb_id: int, settings: dict, delay: float = 0.012):
    """Yields events: {'type': 'sources'|'token'|'done', ...}"""
    t0 = time.time()
    user_history = [m["content"] for m in history if m["role"] == "user"]
    use_ai = ai_enabled()
    index = search.get_index(kb_id)
    reply = small_talk(question, settings)
    if reply:
        yield from _emit(reply, delay)
        yield {"type": "done", "not_found": False, "sources": [], "engine": "chat", "latency_ms": int((time.time() - t0) * 1000), "text": reply}
        return
    if use_ai:
        query = rewrite_question(question, history)
    else:
        query = question
        borrowed = search.standalone_query(question, user_history)
        # borrow the previous question's words only for a real follow-up about something in these documents,
        # and only when the question doesn't already find its answer on its own
        if borrowed != question and index.knows(question) and (
                search.FOLLOW_UP.search(question) or not is_found(index.search(question, k=5))):
            query = borrowed
    hits = index.search(query, k=5)
    fallback = settings.get("fallback_message") or "I couldn't find this in the documents."
    contact = settings.get("human_contact")
    not_found_text = f"{fallback} You can contact {contact}." if contact else fallback

    if use_ai and hits:
        try:
            yield from _ai_stream(question, history, hits, settings, not_found_text, t0, delay)
            return
        except Exception as e:
            log.warning("Groq answer failed, falling back to offline: %s", e)

    if not is_found(hits):
        yield from _emit(not_found_text, delay)
        yield {"type": "done", "not_found": True, "sources": [], "engine": "offline", "latency_ms": int((time.time() - t0) * 1000)}
        return
    text, sources = offline_answer(query, hits, focus=question)
    if not text:
        yield from _emit(not_found_text, delay)
        yield {"type": "done", "not_found": True, "sources": [], "engine": "offline", "latency_ms": int((time.time() - t0) * 1000)}
        return
    yield {"type": "sources", "sources": sources}
    yield from _emit(text, delay)
    yield {"type": "done", "not_found": False, "sources": sources, "engine": "offline", "latency_ms": int((time.time() - t0) * 1000)}


def _label(h):
    parts = [h["filename"]]
    if h["page"]:
        parts.append(f"page {h['page']}")
    if h["heading"]:
        parts.append(h["heading"])
    return ", ".join(parts)


def _emit(text, delay=0.012):
    for piece in re.findall(r"\S+\s*", text):
        yield {"type": "token", "text": piece}
        if delay:
            time.sleep(delay)


def _ai_stream(question, history, hits, settings, not_found_text, t0, delay):
    passages = "\n\n".join(f"[{i + 1}] ({_label(h)})\n{h['text']}" for i, h in enumerate(hits))
    langs = ", ".join({"en": "English", "ur": "Urdu", "roman_ur": "Roman Urdu"}.get(l, l) for l in settings.get("languages", ["en"]))
    system = SYSTEM.format(bot=settings.get("bot_name", "Assistant"), company=settings.get("company_name", "the company"),
                           tone="warm and friendly" if settings.get("tone") == "friendly" else "formal and professional", langs=langs)
    msgs = [{"role": "system", "content": system}]
    for m in history[-6:]:
        msgs.append({"role": m["role"], "content": m["content"][:800]})
    msgs.append({"role": "user", "content": f"Passages:\n{passages}\n\nQuestion: {question}"})
    stream = _groq().chat.completions.create(model=GROQ_MODEL, temperature=0.1, max_tokens=600, stream=True, messages=msgs)
    buf, started, full = "", False, ""
    for ev in stream:
        piece = ev.choices[0].delta.content or ""
        if not piece:
            continue
        full += piece
        if not started:
            buf += piece
            if len(buf) < 10 and "NOT_FOUND".startswith(buf.strip()[:9]):
                continue
            started = True
            if buf.strip().startswith("NOT_FOUND"):
                break
            yield {"type": "sources", "sources": [_source(h) for h in hits]}
            yield {"type": "token", "text": buf}
        else:
            yield {"type": "token", "text": piece}
    if not started and buf and not buf.strip().startswith("NOT_FOUND"):
        yield {"type": "sources", "sources": [_source(h) for h in hits]}
        yield {"type": "token", "text": buf}
        started = True
    if full.strip().startswith("NOT_FOUND") or not full.strip():
        yield from _emit(not_found_text, delay / 2)
        yield {"type": "done", "not_found": True, "sources": [], "engine": "ai", "latency_ms": int((time.time() - t0) * 1000)}
        return
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", full) if 0 < int(n) <= len(hits)})
    used = [_source(hits[n - 1]) for n in cited] or [_source(hits[0])]
    for s, n in zip(used, cited or [1]):
        s["ref"] = n
    yield {"type": "done", "not_found": False, "sources": used, "engine": "ai", "latency_ms": int((time.time() - t0) * 1000), "text": full}


def answer_text(question: str, history: list[dict], kb_id: int, settings: dict) -> dict:
    """Non-streaming helper (WhatsApp, evaluation, seeding)."""
    text, done = "", {}
    for ev in stream_answer(question, history, kb_id, settings, delay=0):
        if ev["type"] == "token":
            text += ev["text"]
        elif ev["type"] == "done":
            done = ev
    if done.get("text"):
        text = done["text"]
    return {"text": text.strip(), **{k: v for k, v in done.items() if k != "text"}}
