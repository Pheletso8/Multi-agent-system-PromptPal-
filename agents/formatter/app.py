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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "formatter", "ready": True}


@app.head("/")
@app.get("/")
async def root():
    return {"status": "ok", "service": "formatter", "ready": True}


@app.post("/format")
async def format_output(data: FormatRequest):
    hint_content = data.hint

    # Extract Mermaid diagram
    mermaid_match = re.search(r"```mermaid\n(.*?)\n```", hint_content, re.DOTALL)
    mermaid_code = mermaid_match.group(1).strip() if mermaid_match else ""

    # Remove diagram from hint text
    clean_hint = re.sub(r"```mermaid.*?```", "", hint_content, flags=re.DOTALL).strip()

    return {
        "status": "success",
        "data": {
            "hint": clean_hint,
            "diagram": mermaid_code
        }
    }
if __name__ == "__main__":
    # Render provides the port via the PORT environment variable
    # Fallback to 8003 if running locally
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
