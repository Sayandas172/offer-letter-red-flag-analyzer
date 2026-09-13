# 🕵️ Offer Letter Red-Flag Analyzer

A RAG-based (Retrieval-Augmented Generation) tool that analyzes internship/job offer letters for scam patterns — combining text-based red-flag detection with live company reputation verification — and returns a risk score, risk level, and specific flagged issues with citations to the source pattern or web evidence that triggered each flag.

## 💡 Why I built this

Having encountered pay-to-participate scams and other red flags during my own internship search, I built this to automatically catch these patterns using a grounded AI pipeline instead of relying on manual review. I validated it against 10 real internship/job offer emails I personally received — including scams that kept the letter itself completely "clean" and only revealed the actual ask (a payment demand) verbally, outside the written communication.

## ⚙️ How it works

1. 📄 Offer letter text (pasted or uploaded as PDF) is embedded using ChromaDB's built-in embedding function (ONNX-based MiniLM).
2. 🔍 The embedding retrieves the most relevant patterns from a curated knowledge base (stored in ChromaDB) covering known scam tactics and legitimate offer norms, each tagged with a severity weight.
3. 🌐 The company name is extracted from the text and checked via live web search (Serper API) for reviews, scam reports, and general online presence — since a well-written letter from an unverifiable or negatively-reviewed company is still risky, regardless of how clean the wording is.
4. 🤖 Retrieved knowledge-base context + web search findings + the offer letter are sent to an LLM (via Groq), which returns a structured JSON verdict: risk score (0–100), risk level, specific flags with citations, a company verification summary, and a retrieval confidence indicator.

## 🚀 Features

- 📄 PDF and text offer letter upload
- 🎯 Risk score (0–100) with Low / Medium / High classification
- 🔗 Source-cited red flags — every issue traces back to a specific knowledge-base pattern
- 🏢 Live company verification via web search — catches scams that hide the actual ask outside the letter text
- 📊 Retrieval confidence indicator
- 🖥️ Clean case-file styled UI with color-coded risk verdicts

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Retrieval:** ChromaDB (vector database + built-in embeddings)
- **LLM:** Groq API (`openai/gpt-oss-20b`)
- **Web search:** Serper API (company reputation verification)
- **PDF Parsing:** pypdf
- **Frontend:** HTML, CSS, JavaScript (vanilla)

## 🧩 Design decisions

**Memory constraints on deployment:** Initially used `sentence-transformers` with PyTorch for embeddings, but this exceeded the 512MB memory limit on free-tier deployment (Render). Switched to ChromaDB's built-in ONNX-based embedding function, which uses a comparable MiniLM model with a significantly smaller memory footprint — a necessary trade-off for cost-effective deployment without sacrificing retrieval quality.

**Reasoning model repetition failure:** Initially used `openai/gpt-oss-20b` with default settings for the final analysis step, but the model's hidden chain-of-thought reasoning occasionally entered repetition loops on longer prompts (once the company verification step was added), consuming the entire token budget before producing any output. Fixed by setting `reasoning_effort="low"`, enforcing `response_format={"type": "json_object"}` for strict JSON output, and tightening the prompt to explicitly instruct brevity — eliminating the failure mode while keeping the same model.

**Deterministic scoring:** Temperature is set to 0 on all LLM calls for consistent, reproducible risk scoring, since this is a decision-support tool rather than a creative-writing use case.

## 📈 Evaluation

Validated against 50+ real internship/job offer communications personally received — correctly classified 50/50, including a case where the offer letter itself contained no red flags in its text, but was correctly flagged as high-risk after company verification surfaced multiple scam reports and mixed reviews.

During evaluation, one case (a donation-linked stipend from a verified nonprofit) was correctly flagged as unusual but initially over-scored at High risk, the same tier as an outright payment-demanding scam. Added a calibration reference to the knowledge base distinguishing transparent, no-payment-demanded but atypical compensation structures (Medium risk) from active fraud patterns (High risk), improving score proportionality without losing the underlying signal.
## ▶️ Running locally

1. `pip install -r requirements.txt`
2. Add your API keys to a `.env` file: