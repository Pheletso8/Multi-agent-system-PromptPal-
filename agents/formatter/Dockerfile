FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
# We force install uvicorn and fastapi in case requirements.txt is empty
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn ollama
COPY . .
# We use app:app because your files are named app.py
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"] 
