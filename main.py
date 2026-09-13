from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader
import pdfplumber
import pypdfium2 as pdfium
import pytesseract
import io
from rag_pipeline import analyze_offer
import pytesseract
import platform
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'D:\ocr_installing\tesseract.exe'

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

def extract_text_with_ocr(file_bytes):
    text = ""
    try:
        pdf = pdfium.PdfDocument(file_bytes)
        for page in pdf:
            bitmap = page.render(scale=2.0)
            pil_image = bitmap.to_pil()
            page_text = pytesseract.image_to_string(pil_image)
            text += page_text + "\n"
    except Exception as e:
        print("OCR extraction failed:", e)
        text = ""
    return text

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

        if not text.strip():
            print("Falling back to OCR...")
            text = extract_text_with_ocr(contents)
    else:
        text = contents.decode("utf-8", errors="ignore")

    if not text.strip():
        return {
            "risk_score": 0,
            "risk_level": "Unknown",
            "flags": [],
            "company_check": {"company_name": "Unknown", "verification_summary": "Could not extract text from this file.", "found_concerns": False},
            "summary": "Could not extract any readable text from this file, even with OCR. The file may be corrupted or contain no visible text.",
            "confidence": "Low"
        }

    return analyze_offer(text)

app.mount("/", StaticFiles(directory="static", html=True), name="static")