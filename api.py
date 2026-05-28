import os
import logging
import re
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# --- 1. DEFINE LOGGER PROPERLY ---
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("api-gateway")

app = FastAPI(title="Grade 7 Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs (Docker internal DNS names or Render hostports)
scholar_env = os.getenv("SCHOLAR_URL", "http://scholar:8001/solve")
SCHOLAR_URL = scholar_env if scholar_env.startswith("http") else f"http://{scholar_env}/solve"

coach_env = os.getenv("COACH_URL", "http://coach:8002/process")
COACH_URL = coach_env if coach_env.startswith("http") else f"http://{coach_env}/process"

formatter_env = os.getenv("FORMATTER_URL", "http://formatter:8003/format")
FORMATTER_URL = formatter_env if formatter_env.startswith("http") else f"http://{formatter_env}/format"

GREETINGS = re.compile(
    r"^(hi|hello|howzit|hey|hiya|yo|good morning|good afternoon|good evening)\b.*$",
    re.I,
)


class QuestionRequest(BaseModel):
    question: str


def is_greeting(question: str) -> bool:
    return bool(GREETINGS.match(question.strip()))


def build_scholar_prompt(question: str) -> str:
    return (
        "You are Scholar Pal. Produce a complete internal reasoning path for a Grade 7 student. "
        "This output is internal only and should NOT be given to the student directly. "
        "Do not include the final numeric answer in the explanation.\n\n"
        f"Question: {question}"
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api", "ready": True}


@app.post("/ask")
async def ask_tutor(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=400, detail="Question must not be empty.")

    greeted = is_greeting(question)
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            if greeted:
                logger.info(f"👋 Greeting request: {question[:80]}")
                scholar_solution = ""
            else:
                logger.info(f"🧠 Tutoring request: {question[:80]}")
                scholar_response = await client.post(
                    SCHOLAR_URL,
                    json={"query": build_scholar_prompt(question)}
                )
                scholar_response.raise_for_status()
                scholar_solution = scholar_response.text.strip()
                if not scholar_solution:
                    raise ValueError("Scholar returned an empty solution.")

            logger.info("🧠 Passing request to Coach...")
            coach_response = await client.post(
                COACH_URL,
                json={"query": question, "solution": scholar_solution}
            )
            coach_response.raise_for_status()
            coach_hint = coach_response.text

            logger.info("🎨 Formatting coach output...")
            formatter_response = await client.post(
                FORMATTER_URL,
                json={"hint": coach_hint, "solution": scholar_solution}
            )
            formatter_response.raise_for_status()
            payload = formatter_response.json()

            return JSONResponse({
                "status": "success",
                "type": "greeting" if greeted else "guided",
                "question": question,
                "data": payload["data"],
            })

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in pipeline: {e}")
            raise HTTPException(status_code=502, detail=str(e))
        except Exception as e:
            logger.error(f"Pipeline Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
