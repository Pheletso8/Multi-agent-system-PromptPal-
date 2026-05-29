from fastapi.responses import StreamingResponse
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ollama import AsyncClient
import uvicorn

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [Coach]: %(message)s")
logger = logging.getLogger("coach")

app = FastAPI()

# Global client to reuse the connection pool
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
COACH_MODEL = os.environ.get("COACH_MODEL", "gpt-oss:120b-cloud")
api_key = os.environ.get('OLLAMA_API_KEY', '')
client = AsyncClient(
    host=OLLAMA_HOST,
    headers={'Authorization': f"Bearer {api_key}"}
)


@app.on_event("startup")
async def startup_event():
    if not api_key:
        logger.error("OLLAMA_API_KEY is missing.")
        raise RuntimeError("OLLAMA_API_KEY is required for Coach service.")


class CoachRequest(BaseModel):
    query: str
    solution: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "coach", "ready": True}

@app.head("/")
@app.get("/")
async def root():
    return {"status": "ok", "service": "coach", "ready": True}


@app.post("/process")
async def process_coach(data: CoachRequest):
    try:
        logger.info(f"🧠 Coaching student on: {data.query[:50]}...")

        persona = (
            "You are Coach Pal, a Grade 7 tutor from South Africa. "
            "You are warm, encouraging, and direct. 🇿🇦\n"
            "Goal: Support the student by guiding their thinking for every question, not by giving the answer."
        )

        constraints = (
            "### STRICT RULES:\n"
            "1. ALWAYS guide the student with questions and explanations, even for simple arithmetic like 7 + 7.\n"
            "2. NEVER reveal the final answer or the internal solution.\n"
            "3. If the student asks for the answer, say: 'Aowa! I can't give you the full kota, I can only show you the recipe.'\n"
            "4. If the input is only a greeting, reply with a short friendly South African greeting and ask what they need help with.\n"
            "5. Use at most one South African analogy when it helps, such as vetkoek, taxi seating, airtime top-ups, or school sports.\n"
            "6. Keep the language Grade 7 friendly and avoid unnecessary jargon.\n"
        )

        task_logic = (
            "### YOUR TASK:\n"
            "1. If the student greeted you, reply with a friendly greeting and ask what they want help with. Do not include a Mermaid diagram in that case.\n"
            "2. Otherwise, start with a short encouraging observation and then ask exactly 2 guiding questions.\n"
            "3. Then include a Mermaid diagram in a fenced code block using 'flowchart TD'.\n"
            "4. Do NOT reveal the final numeric answer.\n\n"
            "Example 1 (arithmetic):\n"
            "Question: 'What is 7 + 7?'\n"
            "Say something like 'Nice question! Let's think about how to split 7 sweets into two equal groups...' and ask:\n"
            " - 'How many sweets are in one group if there are two groups?'\n"
            " - 'What do we do next once we know one group size?'\n"
            "Then show a simple flowchart for the method.\n\n"
            "Example 2 (area):\n"
            "Question: 'How do I find the area of a rectangle?'\n"
            "Use a school sports field or classroom floor example, then ask:\n"
            " - 'What two measurements do we need first?'\n"
            " - 'How do we use those measurements together?'\n\n"
            "Example 3 (greeting):\n"
            "If the student says 'Hi' or 'Hello', reply: 'Howzit! I'm Coach Pal. What do you want to work through today?'\n\n"
            "Example diagram for a real question:\n"
            "```mermaid\n"
            "flowchart TD\n"
            "    A[\"🚀 Start\"] --> B[\"Step 1: Understand the question\"]\n"
            "    B --> C[\"Step 2: Break it into smaller parts\"]\n"
            "    C --> D[\"Step 3: Check your method\"]\n"
            "```\n"
        )

        prompt = (
            f"{persona}\n\n"
            f"Student Question: {data.query}\n"
            f"Internal Solution: {data.solution}\n\n"
            f"{constraints}\n\n"
            f"{task_logic}"
        )

        async def generate():
            async for chunk in await client.chat(
                model=COACH_MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            ):
                content = chunk['message']['content']
                if content:
                    yield content

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        logger.error(f"❌ Coach failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Make sure this port is 8002 to match your working network config
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
