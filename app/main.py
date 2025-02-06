from fastapi import FastAPI, Request, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import Optional
import anthropic, os, logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize Claude
claude = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))

SYSTEM_PROMPT = """You are Decidly, a specialized Canadian legal AI assistant. Structure your analysis as follows:

1. Summary (2-3 sentences)
2. Key Legal Points
   - Relevant laws/regulations
   - Your rights/obligations
3. Action Steps
   - Immediate actions
   - Next steps
   - Resources/contacts

Use clear headers and bullet points. Focus on Canadian law context."""

class LegalAnalyzer:
    @staticmethod
    async def analyze(query: str, context: Optional[str] = None) -> str:
        try:
            message_content = f"Query: {query}\n\nContext: {context}" if context else query
            
            response = claude.messages.create(
                model="claude-3-opus-20240229",
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": message_content}],
                temperature=0.3,
                max_tokens=2000
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise HTTPException(status_code=500, detail="Analysis failed")

@app.get("/", response_class=HTMLResponse)
async def root():
    return Path("app/static/index.html").read_text()

@app.post("/analyze")
async def analyze(request: Request):
    try:
        form = await request.form()
        query = form.get('text', '')
        
        # Process files
        file_contents = []
        for key, value in form.items():
            if isinstance(value, UploadFile):
                content = await value.read()
                file_contents.append(f"Document: {value.filename}\n{content.decode('utf-8')}")
        
        # Get analysis
        context = "\n---\n".join(file_contents) if file_contents else None
        analysis = await LegalAnalyzer.analyze(query, context)
        
        return {
            'analysis': analysis,
            'timestamp': datetime.now().isoformat(),
            'files_processed': len(file_contents)
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return JSONResponse(
            {"error": "Analysis failed. Please try again."},
            status_code=500
        )