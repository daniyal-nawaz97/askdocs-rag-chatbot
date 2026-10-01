"""Record the 2-3 minute demo video automatically (follows docs/demo-video-script.md).

Needs:  pip install playwright imageio-ffmpeg && playwright install chromium
Start the app with a fresh data folder (./run.sh), then:
    python -m scripts.record_demo --url http://localhost:8002
Output: docs/demo.mp4 and static/media/demo.webm (shown on the landing page).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
CAPTION_JS = """
(text) => {
  let el = document.getElementById('__cap');
  if (!el) {
    el = document.createElement('div'); el.id = '__cap';
    el.style.cssText = 'position:fixed;left:50%;bottom:36px;transform:translateX(-50%);z-index:2147483647;max-width:980px;' +
      'background:rgba(17,24,39,.92);color:#fff;font:600 24px/1.35 Inter,system-ui,sans-serif;padding:16px 26px;border-radius:14px;' +
      'box-shadow:0 10px 40px rgba(0,0,0,.35);text-align:center;transition:opacity .25s;pointer-events:none';
    document.body.appendChild(el);
  }
  el.style.opacity = text ? '1' : '0';
  if (text) el.innerHTML = text;
}
"""


def caption(page, text, ms=3000):
    page.evaluate(CAPTION_JS, text)
    page.wait_for_timeout(ms)


def ask(page, question, wait=2600):
    page.click("#q")
    page.type("#q", question, delay=35)
    page.keyboard.press("Enter")
    page.wait_for_timeout(wait)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8002")
    url = ap.parse_args().url
    tmp = Path(tempfile.mkdtemp())
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome") if shutil.which("google-chrome") else p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=str(tmp), record_video_size={"width": 1280, "height": 720})
        page = ctx.new_page()
        page.goto(url + "/#/login"); page.wait_for_timeout(1200)
        caption(page, "How many times a day does someone in your company ask the same question?", 3800)
        page.click("#demoBtn"); page.wait_for_timeout(1800)
        page.goto(url + "/#/documents"); page.wait_for_timeout(1500)
        caption(page, "The assistant reads your company's own documents: PDFs, Word files, FAQs", 3500)
        page.goto(url + "/#/"); page.wait_for_timeout(1500)
        caption(page, "", 100)
        ask(page, "How many casual leaves do I get?")
        caption(page, "Short answer, and the source is always shown", 3000)
        ask(page, "And for part-time staff?")
        caption(page, "Follow-up questions work: it remembers the conversation", 3200)
        caption(page, "", 100)
        page.locator(".src-card.active a").first.click()
        page.wait_for_timeout(1800)
        caption(page, "One click opens the document at the exact passage", 3500)
        page.go_back(); page.wait_for_timeout(1500)
        caption(page, "", 100)
        ask(page, "Mujhe saal mein kitni casual chuttiyan milti hain?")
        caption(page, "Staff can ask in English, Urdu or Roman Urdu", 3000)
        caption(page, "", 100)
        ask(page, "Is there a gym membership benefit?")
        caption(page, "Not in the documents? It says so honestly, and offers a human contact", 3800)
        page.goto(url + "/#/insights"); page.wait_for_timeout(2200)
        caption(page, "Insights: what people ask most, and how many answers were helpful", 3500)
        page.mouse.wheel(0, 650); page.wait_for_timeout(800)
        caption(page, "Unanswered questions show the gaps in your documents", 3500)
        caption(page, "", 100)
        page.goto(url + "/demo-site"); page.wait_for_timeout(1800)
        caption(page, "The same assistant on your website, in your brand colour", 2500)
        page.click("button[aria-label^=Chat]"); page.wait_for_timeout(1200)
        frame = page.frame_locator("iframe[title]")
        frame.locator("#q").click()
        frame.locator("#q").type("How long does a refund take?", delay=35)
        frame.locator("#q").press("Enter")
        page.wait_for_timeout(2500)
        caption(page, "Customers get answers with a link to the source document, 24/7", 3500)
        results = BASE / "docs" / "results.json"
        if results.exists():
            s = json.loads(results.read_text())["summary"]["headline"]
            caption(page, f"On held-out test questions: {s['answer_accuracy']}% correct, correct source {s['source_found']}% of the time,<br>"
                          f"{s['out_of_scope_refused']}% of out-of-scope questions refused", 5200)
        caption(page, "Let's set up a free demo on 5 of your documents", 3800)
        video = page.video.path()
        ctx.close(); browser.close()
    out_webm = BASE / "static" / "media" / "demo.webm"
    out_webm.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(video, out_webm)
    try:
        import imageio_ffmpeg
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(video), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "23", "-movflags", "+faststart", str(BASE / "docs" / "demo.mp4")], check=True)
        print("Saved docs/demo.mp4 and static/media/demo.webm")
    except Exception as e:
        print("Saved static/media/demo.webm (mp4 conversion skipped:", e, ")")


if __name__ == "__main__":
    main()
