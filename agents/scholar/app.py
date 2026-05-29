import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import AsyncGroq
import uvicorn

# Setup Logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [Scholar]: %(message)s")
logger = logging.getLogger("scholar")

app = FastAPI()

# Global client to reuse the connection pool
GROQ_MODEL = os.environ.get("SCHOLAR_MODEL", "llama3-8b-8192")
api_key = os.environ.get('GROQ_API_KEY', '')
client = AsyncGroq(api_key=api_key)


@app.on_event("startup")
async def startup_event():
    if not api_key:
        logger.error("GROQ_API_KEY is missing.")
        raise RuntimeError("GROQ_API_KEY is required for Scholar service.")


class ScholarRequest(BaseModel):
    query: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "scholar", "ready": True}

@app.head("/")
@app.get("/")
async def root():
    return {"status": "ok", "service": "scholar", "ready": True}


@app.post("/solve")
async def solve_query(data: ScholarRequest):
    try:
        logger.info(f"🔍 Scholar is solving: {data.query[:50]}...")

        async def generate():
            stream = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{'role': 'user', 'content': data.query}],
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
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
