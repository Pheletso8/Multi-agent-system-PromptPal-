import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import uvicorn

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [Coach]: %(message)s")
logger = logging.getLogger("coach")

COACH_MODEL = os.environ.get("COACH_MODEL", "meta-llama/llama-3.1-8b-instruct")
OPENROUTER_API_KEY = os.environ.get(
    'OPENROUTER_API_KEY') or os.environ.get('GROQ_API_KEY', '')
OPENROUTER_API_BASE_URL = os.environ.get(
    "OPENROUTER_API_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY is missing")
    raise RuntimeError("OPENROUTER_API_KEY required")

app = FastAPI()


async def openrouter_chat_completion(model: str, messages: list[dict], temperature: float = 0.7) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "PromptPal/1.0",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OPENROUTER_API_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"]


class CoachRequest(BaseModel):
    query: str
    solution: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "coach"}


@app.post("/process")
async def process_coach(data: CoachRequest):
    try:
        logger.info(f"Coaching: {data.query[:40]}...")

        prompt = (
            f"You are a helpful tutor. Guide the student through this problem.\n\n"
            f"Question: {data.query}\n\n"
            f"Rules:\n"
            f"1. Ask 2-3 guiding questions to help them think through it\n"
            f"2. Don't reveal the answer\n"
            f"3. ALWAYS include a Mermaid flowchart diagram at the end\n\n"
            f"Example format:\n"
            f"[Your guiding questions]\n\n"
            f"```mermaid\n"
            f"flowchart TD\n"
            f"    A[Step 1] --> B[Step 2] --> C[Step 3]\n"
            f"```\n"
        )

        full_response = await openrouter_chat_completion(
            model=COACH_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful tutor. Guide the student through the problem without giving the direct answer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        return {"content": full_response}

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
