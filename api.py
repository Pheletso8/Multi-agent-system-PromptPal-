import os
import logging
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(message)s")
logger = logging.getLogger("api")

app = FastAPI(title="Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prompt-pal-six.vercel.app"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["content-type"],
)

SCHOLAR_URL = os.getenv("SCHOLAR_URL", "http://localhost:8001/solve")
COACH_URL = os.getenv("COACH_URL", "http://localhost:8002/process")
FORMATTER_URL = os.getenv("FORMATTER_URL", "http://localhost:8003/format")


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask")
async def ask_tutor(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question required")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            logger.info(f"Question: {question[:50]}...")

            # Get solution from Scholar
            scholar_response = await client.post(
                SCHOLAR_URL,
                json={"query": question}
            )
            scholar_response.raise_for_status()
            scholar_data = scholar_response.json()
            scholar_solution = scholar_data.get("content", "")

            # Get coaching from Coach
            coach_response = await client.post(
                COACH_URL,
                json={"query": question, "solution": scholar_solution}
            )
            coach_response.raise_for_status()
            coach_data = coach_response.json()
            coach_hint = coach_data.get("content", "")

            # Format output
            formatter_response = await client.post(
                FORMATTER_URL,
                json={"hint": coach_hint, "solution": scholar_solution}
            )
            formatter_response.raise_for_status()
            payload = formatter_response.json()

            return JSONResponse({
                "content": payload["data"].get("hint", ""),
                "diagram": payload["data"].get("diagram", ""),
            })

        except httpx.HTTPStatusError as e:
            logger.error(f"Service error: {e}")
            raise HTTPException(status_code=502, detail="Service error")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
