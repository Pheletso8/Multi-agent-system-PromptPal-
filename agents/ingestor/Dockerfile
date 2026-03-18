FROM python:3.11-slim
WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

COPY . .

# Run as a persistent service on port 8004
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
