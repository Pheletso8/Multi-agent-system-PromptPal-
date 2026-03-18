import re
import time
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI()


class FormatRequest(BaseModel):
    hint: str
    solution: str


@app.post("/format")
async def format_output(data: FormatRequest):
    hint_content = data.hint

    # Extract Mermaid code
    mermaid_match = re.search(
        r"```mermaid\n(.*?)\n```", hint_content, re.DOTALL)
    mermaid_code = mermaid_match.group(1).strip() if mermaid_match else ""

    # Remove mermaid block for clean UI
    clean_hint = re.sub(r"```mermaid.*?```", "",
                        hint_content, flags=re.DOTALL).strip()

    return {
        "status": "success",
        "timestamp": time.time(),
        "data": {
            "hint": clean_hint if clean_hint else "Sharp-sharp! Let's look at this...",
            "diagram": mermaid_code,
            "original_solution": data.solution
        }
    }
if __name__ == "__main__":
    # Render provides the port via the PORT environment variable
    # Fallback to 8003 if running locally
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)