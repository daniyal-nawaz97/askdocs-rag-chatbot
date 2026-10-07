"""Build the clickable demo (static site for GitHub Pages) from the real app and its demo data.

    python -m scripts.build_static_demo            # writes site/
    python -m scripts.build_static_demo --publish  # also pushes it to the gh-pages branch

The chatbot answers a prepared set of questions per knowledge base (the suggested questions plus the 70
evaluation questions, including follow-ups and Roman Urdu), replayed word by word with their sources. Other
questions get a polite note that the live version answers anything in the documents. The website widget
demo page works the same way.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "static_demo"))
from static_demo import Server, Site, publish, rewrite  # noqa: E402

REPO = "askdocs-rag-chatbot"


def sse_done(text: str) -> tuple[int | None, dict]:
    cid, done = None, {}
    for block in text.split("\n\n"):
        block = block.strip()
        if not block.startswith("data: "):
            continue
        ev = json.loads(block[6:])
        if ev["type"] == "meta":
            cid = ev["conversation_id"]
        elif ev["type"] == "done":
            done = ev
    return cid, done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    ap.add_argument("--port", type=int, default=8902)
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args()

    # same answers as the measured offline results (no AI service key in the demo build)
    with Server(ROOT, a.port, {"GROQ_API_KEY": "", "MODEL_DIR": str(ROOT / "data" / "models")}) as srv:
        s = Site(ROOT, Path(a.out), REPO, srv)
        s.post("POST /api/demo-login", "/api/demo-login")
        for u in ("/api/app-info", "/api/me", "/api/settings", "/api/users", "/api/documents", "/api/insights?days=30",
                  "/api/public/config", "/widget.js"):
            s.get(u, required=u != "/api/users")
        kbs = s.get("/api/kbs")
        for k in kbs:
            s.get(f"/api/kbs/{k['id']}/access", required=False)
            if k.get("is_public"):
                s.get(f"/api/public/config?kb={k['slug']}")
        for c in s.get("/api/conversations"):
            s.get(f"/api/conversations/{c['id']}")
        for d in s.get("/api/documents"):
            det = s.get(f"/api/documents/{d['id']}")
            s.get(f"/api/documents/{d['id']}/file")
            for p in range(1, (det.get("pages") or 0) + 1):
                s.get(f"/api/documents/{d['id']}/page/{p}", required=False)

        # prepared answers: suggested questions + evaluation questions (follow-ups asked after their first question)
        qs = json.loads((ROOT / "scripts" / "eval_questions.json").read_text()) + json.loads((ROOT / "scripts" / "eval_questions_holdout.json").read_text())
        slug_id = {k["slug"]: k["id"] for k in kbs}
        todo = [(k["id"], q, []) for k in kbs for q in k.get("suggested") or []]
        todo += [(slug_id[q["kb"]], q["q"], q.get("history") or []) for q in qs if q["kb"] in slug_id]
        answers, seen = {}, set()
        print(f"Preparing {len(todo)} answers…")
        for kb_id, q, hist in todo:
            key = (kb_id, q.strip().lower(), tuple(h.strip().lower() for h in hist))
            if key in seen:
                continue
            seen.add(key)
            cid = None
            for h in hist:
                cid, _ = sse_done(s.client.post("/api/chat", json={"question": h, "kb_id": kb_id, "conversation_id": cid}).text)
            _, done = sse_done(s.client.post("/api/chat", json={"question": q, "kb_id": kb_id, "conversation_id": cid}).text)
            answers.setdefault(str(kb_id), []).append({"q": q, "prev": hist[-1] if hist else "", "text": rewrite(done.get("text", ""), s.base),
                                                       "sources": done.get("sources", []), "not_found": done.get("not_found", False)})
        s.put_get("/api/_demo/answers", answers)
        s.put_get("/api/_demo/kbs", {k["slug"]: k["id"] for k in kbs})
        print(f"  {sum(len(v) for v in answers.values())} answers")

        hooks = (Path(__file__).resolve().parent / "static_demo" / "hooks.js").read_text()
        widget = ROOT / "static" / "widget"
        s.finish("AskDocs demo", hooks, extra_static=[(widget / "widget.html", "widget.html"), (widget / "demo-site.html", "demo-site.html")])
        # the embed script finds the app from its own address; on GitHub Pages that includes the /<repo> path
        js = (widget / "widget.js").read_text()
        js = js.replace("var origin = new URL(script.src).origin;", 'var origin = script.src.replace(/\\/widget\\.js.*$/, "");')
        js = js.replace("e.origin === origin", "e.origin === new URL(origin).origin")
        js = js.replace('origin + "/widget?kb="', 'origin + "/widget.html?kb="')
        assert js.count("new URL(origin).origin") == 1 and "widget.html?kb=" in js
        (Path(a.out) / "widget.js").write_text(js)
    if a.publish:
        publish(Path(a.out), ROOT)


if __name__ == "__main__":
    main()
