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
client = AsyncClient(
    host="https://ollama.com",
    headers={'Authorization': f"Bearer {os.environ.get('OLLAMA_API_KEY', '')}"}
)


class ScholarRequest(BaseModel):
    query: str

@app.post("/solve")
async def solve_query(data: ScholarRequest):
    try:
        logger.info(f"🔍 Scholar is solving: {data.query[:50]}...")

        async def generate():
            async for chunk in await client.chat(
                model='gpt-oss:120b-cloud',
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