import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ollama import AsyncClient  # Use Async for better performance
import uvicorn

# Setup Logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [Scholar]: %(message)s")
logger = logging.getLogger("scholar")

app = FastAPI()

# Global client to reuse the connection pool
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com")
OLLAMA_MODEL = os.environ.get("SCHOLAR_MODEL", "gpt-oss:120b-cloud")
api_key = os.environ.get('OLLAMA_API_KEY', '')
client = AsyncClient(
    host=OLLAMA_HOST,
    headers={'Authorization': f"Bearer {api_key}"}
)


@app.on_event("startup")
async def startup_event():
    if not api_key:
        logger.error("OLLAMA_API_KEY is missing.")
        raise RuntimeError("OLLAMA_API_KEY is required for Scholar service.")


class ScholarRequest(BaseModel):
    query: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "scholar", "ready": True}


@app.post("/solve")
async def solve_query(data: ScholarRequest):
    try:
        logger.info(f"🔍 Scholar is solving: {data.query[:50]}...")

        async def generate():
            async for chunk in await client.chat(
                model=OLLAMA_MODEL,
                messages=[{'role': 'user', 'content': data.query}],
                stream=True
            ):
                content = chunk['message']['content']
                if content:
                    yield content

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        logger.error(f"❌ Scholar failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Render provides the port via the PORT environment variable
    # Fallback to 8001 if running locally
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
