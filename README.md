\# Offer Letter Red-Flag Analyzer



A RAG-based (Retrieval-Augmented Generation) tool that analyzes internship/job offer letters for common scam patterns, returning a risk score, risk level, and specific flagged issues with citations to the source pattern that triggered each flag.



\## Why I built this

Having encountered pay-to-participate scams and other red flags during my own internship search, I built this to automatically catch these patterns using a grounded AI pipeline instead of relying on manual review.



\## How it works

1\. Offer letter text (pasted or uploaded as PDF) is embedded using sentence-transformers.

2\. The embedding is used to retrieve the most relevant patterns from a curated knowledge base (stored in ChromaDB) covering known scam tactics and legitimate offer norms.

3\. Retrieved context + the offer letter are sent to an LLM (via Groq), which returns a structured JSON verdict: risk score, risk level, and specific flags with citations back to the source pattern.



\## Tech stack

\- FastAPI (backend)

\- ChromaDB (vector database)

\- sentence-transformers (embeddings)

\- Groq API (LLM inference)

\- Vanilla HTML/CSS/JS (frontend)



\## Running locally

1\. `pip install -r requirements.txt`

2\. Add your Groq API key to a `.env` file: `GROQ\_API\_KEY=your\_key`

3\. `python ingest.py` (builds the vector database)

4\. `uvicorn main:app --reload`

5\. Open `http://localhost:8000`

