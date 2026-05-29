FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn
COPY . .
# Cloud Run injects PORT env var (defaults to 8080)
CMD sh -c "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"
