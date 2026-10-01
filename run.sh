#!/usr/bin/env bash
# Start AskDocs locally: ./run.sh   then open http://localhost:8002
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Creating virtual environment and installing packages (first run only)..."
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip -q
  .venv/bin/pip install -r requirements.txt
fi
[ -f .env ] || cp .env.example .env
[ -n "$(ls sample_data/docs 2>/dev/null)" ] || .venv/bin/python -m scripts.make_samples
echo "AskDocs running at http://localhost:${PORT:-8002}  (landing: /landing, website widget demo: /demo-site)"
echo "First start downloads the search model (~70 MB) and loads the demo company; give it a minute."
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8002}"
