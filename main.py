from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader
import pdfplumber
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
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            text = ""

        if not text.strip():
            try:
                reader = PdfReader(io.BytesIO(contents))
                for page in reader.pages:
                    text += page.extract_text() or ""
            except Exception:
                text = ""
    else:
        text = contents.decode("utf-8", errors="ignore")

    if not text.strip():
        return {
            "risk_score": 0,
            "risk_level": "Unknown",
            "flags": [],
            "company_check": {"company_name": "Unknown", "verification_summary": "Could not extract text from this file.", "found_concerns": False},
            "summary": "Could not extract any readable text from this file. This can happen with heavily stylized or image-based PDFs. Try pasting the text directly instead.",
            "confidence": "Low"
        }

    return analyze_offer(text)

app.mount("/", StaticFiles(directory="static", html=True), name="static")