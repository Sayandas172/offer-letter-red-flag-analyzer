import os
import json
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./vectorstore")
collection = client.get_collection("offers")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SOURCE_LABELS = {
    "pay_to_participate.txt": "Payment Request Pattern",
    "exclusivity_clause.txt": "Exclusivity Clause Pattern",
    "vague_company_info.txt": "Company Verification Check",
    "no_fixed_format.txt": "Offer Format Standard",
    "pressure_tactics.txt": "Urgency Tactic Pattern",
    "sample_legit_offer_1.txt": "Legitimate Offer Reference",
    "sample_legit_offer_2.txt": "Legitimate Offer Reference",
}

def analyze_offer(offer_text):
    query_embedding = model.encode(offer_text).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )

    docs = results['documents'][0]
    metas = results['metadatas'][0]
    distances = results['distances'][0]

    context_lines = [
        f"[Source: {SOURCE_LABELS.get(meta['source'], meta['source'])}] {doc}"
        for doc, meta in zip(docs, metas)
    ]
    context = "\n\n".join(context_lines)

    avg_distance = sum(distances) / len(distances) if distances else 1.0
    confidence = "High" if avg_distance < 0.8 else "Medium" if avg_distance < 1.2 else "Low"

    prompt = f"""You are a fraud-detection assistant analyzing an internship/job offer letter.
Use ONLY the reference context below, which includes source labels in brackets.

Reference context:
{context}

Offer letter to analyze:
{offer_text}

Respond with ONLY valid JSON, no markdown formatting, no backticks, in this exact structure:
{{
  "risk_score": <integer 0-100, where 0 is completely safe and 100 is certainly a scam>,
  "risk_level": "<Low, Medium, or High>",
  "flags": [
    {{"issue": "<short title>", "reasoning": "<1-2 sentence explanation>", "source": "<source label from context, or none>"}}
  ],
  "summary": "<1-2 sentence overall verdict>"
}}

If no red flags are found, return an empty flags array and a low risk_score."""

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"risk_score": 50, "risk_level": "Medium", "flags": [], "summary": raw}

    parsed["confidence"] = confidence
    return parsed