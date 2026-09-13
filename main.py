from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader
import io
from rag_pipeline import analyze_offer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class OfferRequest(BaseModel):
    offer_text: str

@app.post("/analyze-offer")
def analyze(req: OfferRequest):
    return analyze_offer(req.offer_text)

@app.post("/analyze-offer-file")
async def analyze_file(file: UploadFile = File(...)):
    contents = await file.read()

    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(contents))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    else:
        text = contents.decode("utf-8", errors="ignore")

    if not text.strip():
        return {
            "risk_score": 0,
            "risk_level": "Unknown",
            "flags": [],
            "summary": "Could not extract any text from this file. Try a different file or paste the text directly.",
            "confidence": "Low"
        }

    return analyze_offer(text)

app.mount("/", StaticFiles(directory="static", html=True), name="static")