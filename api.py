import os
import httpx
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import re
from fastapi.responses import StreamingResponse


# --- 1. DEFINE LOGGER PROPERLY ---
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("api-gateway")

app = FastAPI(title="Grade 7 Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs (Docker internal DNS names)
# these are injected via environment variables in Docker Compose, but
# fall back to sensible defaults so the module can run outside of Docker.
SCHOLAR_URL = os.getenv("SCHOLAR_URL", "http://scholar:8001/solve")
COACH_URL = os.getenv("COACH_URL", "http://coach:8002/process")
FORMATTER_URL = os.getenv("FORMATTER_URL", "http://formatter:8003/format")


class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_tutor(request: QuestionRequest):
    async def event_generator():
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # 1. Scholar Agent (Collect full solution for Coach)
                logger.info(f"🚀 Step 1: Calling Scholar for: {request.question[:30]}...")
                scholar_solution = ""
                async with client.stream("POST", SCHOLAR_URL, json={"query": request.question}) as r:
                    r.raise_for_status()
                    async for chunk in r.aiter_bytes():
                        decoded = chunk.decode()
                        scholar_solution += decoded
                        # Optional: yield status or interim progress
                        # yield f"data: {json.dumps({'type': 'status', 'msg': 'Scholar is thinking...'})}\n\n"

                # 2. Coach Agent (Streaming directly to user)
                logger.info("🧠 Step 2: Calling Coach for Socratic logic...")
                full_hint = ""
                async with client.stream("POST", COACH_URL, json={
                    "query": request.question,
                    "solution": scholar_solution
                }) as r:
                    r.raise_for_status()
                    async for chunk in r.aiter_bytes():
                        decoded = chunk.decode()
                        full_hint += decoded
                        yield f"data: {json.dumps({'type': 'hint_delta', 'delta': decoded})}\n\n"

                # 3. Formatter Agent (Final clean-up)
                logger.info("🎨 Step 3: Calling Formatter...")
                formatter_res = await client.post(FORMATTER_URL, json={
                    "hint": full_hint,
                    "solution": scholar_solution
                })
                formatter_res.raise_for_status()
                final_json = formatter_res.json()

                yield f"data: {json.dumps({'type': 'complete', 'data': final_json['data']})}\n\n"

            except Exception as e:
                logger.error(f"❌ Pipeline Error: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    # Sharp-sharp! Make sure this port matches your Docker Compose
   uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
