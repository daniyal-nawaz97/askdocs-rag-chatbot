FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8002 DATA_DIR=/app/data
# run as a normal user (uid 1000), as Hugging Face Spaces and most hosts expect
RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV MODEL_DIR=/app/models
# download the search model at build time so the container starts fast and works offline
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5', cache_dir='/app/models')"
COPY . .
RUN mkdir -p /app/data && chown -R user:user /app
USER user
EXPOSE 8002
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
