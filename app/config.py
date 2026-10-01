import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "AskDocs")
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
FILES_DIR = DATA_DIR / "files"
PAGES_DIR = DATA_DIR / "pages"
BRAND_DIR = DATA_DIR / "brand"
MODEL_DIR = Path(os.getenv("MODEL_DIR", DATA_DIR / "models"))
DB_PATH = DATA_DIR / "askdocs.db"
SAMPLE_DIR = BASE_DIR / "sample_data" / "docs"
STATIC_DIR = BASE_DIR / "static"

# Groq (free tier). Without a key, answers are quoted directly from the best matching passage.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Local embedding model for meaning-based search (downloaded once, ~70 MB). Set USE_EMBEDDINGS=0 to use keyword search only.
USE_EMBEDDINGS = os.getenv("USE_EMBEDDINGS", "1") != "0"
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@askdocs.app")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo1234")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "").strip()
CONTACT_WHATSAPP = os.getenv("CONTACT_WHATSAPP", "").strip()

# Optional WhatsApp Cloud API integration
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "").strip()
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "").strip()
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "askdocs-verify").strip()
WHATSAPP_KB = os.getenv("WHATSAPP_KB", "").strip()  # knowledge base slug used for WhatsApp questions
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")  # Render sets RENDER_EXTERNAL_URL

MAX_FILE_MB = 25
STAFF_MINUTES_PER_QUESTION = float(os.getenv("STAFF_MINUTES_PER_QUESTION", "4"))

for d in (FILES_DIR, PAGES_DIR, BRAND_DIR, MODEL_DIR):
    d.mkdir(parents=True, exist_ok=True)


def ai_enabled() -> bool:
    return bool(GROQ_API_KEY)
