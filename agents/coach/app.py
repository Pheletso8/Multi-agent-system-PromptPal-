import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ollama import AsyncClient

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [Coach]: %(message)s")
logger = logging.getLogger("coach")

app = FastAPI()

# Make sure your OLLAMA_HOST is correct for your cloud provider
client = AsyncClient(
    host="https://ollama.com",
    headers={'Authorization': f"Bearer {os.environ.get('OLLAMA_API_KEY', '')}"}
)


class CoachRequest(BaseModel):
    query: str
    solution: str


from fastapi.responses import StreamingResponse

@app.post("/process")
async def process_coach(data: CoachRequest):
    try:
        logger.info(f"🧠 Coaching student on: {data.query[:50]}...")

        # --- Modular Prompt Components ---
        persona = (
            "You are 'Coach Pal', a Grade 7 tutor from South Africa. "
            "Vibe: Encouraging, sharp-sharp, and direct. 🇿🇦\n"
            "Goal: Lead the student to the answer using Socratic questioning. "
            "Focus on 'making the child understand' above all else."
        )

        constraints = (
            "### STRICT RULES:\n"
            "1. NEVER reveal the final answer or the 'Internal Solution'.\n"
            "2. If the student asks for the answer, say: 'Aowa! I can't give you the full kota, I can only show you the recipe.'\n"
            "3. Use 1 natural South African analogy ONLY if it helps simplify the concept (e.g., sharing vetkoek, taxi seating, or airtime top-ups).\n"
            "4. Keep explanations short, punchy, and 'Grade 7 friendly'. No jargon."
        )

        task_logic = (
            "### TASK 1: THE SOCRATIC GUIDANCE\n"
            "1. Give a 1-sentence playful observation. Use LaTeX for any numbers or formulas, e.g., instead of 5, use $5$.\n"
            "2. Ask 2 short questions. If mentioning the 'Internal Solution' logic, wrap it in a LaTeX block for a premium feel. "
            "Example: 'What happens if we look at $$\\text{Area} = L \\times W$$?'\n\n"
            "### TASK 2: THE VISUAL MAP\n"
            "Create a 'flowchart TD' with 3-4 steps. Use the provided styles. "
            "Do NOT include the final answer calculation.\n"
            "flowchart TD\n"
            "A[\"🚀 Start\"]:::start --> B[\"Step 1\"]:::step\n"
            "classDef start fill:#FFD700,stroke:#333,stroke-width:2px;\n"
            "classDef step fill:#FF69B4,stroke:#333,stroke-width:2px;"
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
                model="gpt-oss:120b-cloud",
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

    except Exception as e:
        logger.error(f"❌ Coach failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Make sure this port is 8002 to match your working network config
    uvicorn.run(app, host="0.0.0.0", port=8002)
