from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import anthropic
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
claude_client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.get("/", response_class=HTMLResponse)
async def root():
    return Path("app/static/index.html").read_text()

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.form()
    user_message = data.get("text")
    
    try:
        response = claude_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": user_message}]
        )
        return {"analysis": response.content}
    except Exception as e:
        return {"error": str(e)}
