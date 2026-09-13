# 🕵️ Offer Letter Red-Flag Analyzer

A RAG-based (Retrieval-Augmented Generation) tool that analyzes internship/job offer letters for common scam patterns, returning a risk score, risk level, and specific flagged issues with citations to the source pattern that triggered each flag.

## 💡 Why I built this

Having encountered pay-to-participate scams and other red flags during my own internship search, I built this to automatically catch these patterns using a grounded AI pipeline instead of relying on manual review.

## ⚙️ How it works

1. 📄 Offer letter text (pasted or uploaded as PDF) is embedded using ChromaDB's built-in embedding function (ONNX-based MiniLM).
2. 🔍 The embedding retrieves the most relevant patterns from a curated knowledge base (stored in ChromaDB) covering known scam tactics and legitimate offer norms, each tagged with a severity weight.
3. 🤖 Retrieved context + the offer letter are sent to an LLM (via Groq), which returns a structured JSON verdict: risk score (0–100), risk level, specific flags with citations, and a retrieval confidence indicator.

## 🚀 Features

- 📄 PDF and text offer letter upload
- 🎯 Risk score (0–100) with Low / Medium / High classification
- 🔗 Source-cited red flags — every issue traces back to a specific knowledge-base pattern
- 📊 Retrieval confidence indicator
- 🖥️ Clean case-file styled UI with color-coded risk verdicts

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Retrieval:** ChromaDB (vector database + built-in embeddings)
- **LLM:** Groq API (`openai/gpt-oss-20b`)
- **PDF Parsing:** pypdf
- **Frontend:** HTML, CSS, JavaScript (vanilla)

## 🧩 Design decisions

Initially used `sentence-transformers` with PyTorch for embeddings, but this exceeded the 512MB memory limit on free-tier deployment (Render). Switched to ChromaDB's built-in ONNX-based embedding function, which uses a comparable MiniLM model with a significantly smaller memory footprint — a necessary trade-off for cost-effective deployment without sacrificing retrieval quality.

Temperature is set to 0 on the LLM call for consistent, reproducible risk scoring, since this is a decision-support tool rather than a creative-writing use case.

## ▶️ Running locally

1. `pip install -r requirements.txt`
2. Add your Groq API key to a `.env` file: `GROQ_API_KEY=your_key`
3. `python ingest.py` (builds the vector database)
4. `uvicorn main:app --reload`
5. Open `http://localhost:8000`

## 🔮 Future improvements

- Hybrid search (combining keyword + vector similarity)
- Re-ranking retrieved chunks with a cross-encoder for improved accuracy
- Batch analysis for comparing multiple offers at once
- Persistent history of past analyses