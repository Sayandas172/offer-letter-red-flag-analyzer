import os
import json
import requests
import chromadb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = chromadb.PersistentClient(path="./vectorstore")
collection = client.get_collection("offers")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

SOURCE_LABELS = {
    "pay_to_participate.txt": "Payment Request Pattern",
    "exclusivity_clause.txt": "Exclusivity Clause Pattern",
    "vague_company_info.txt": "Company Verification Check",
    "no_fixed_format.txt": "Offer Format Standard",
    "pressure_tactics.txt": "Urgency Tactic Pattern",
    "sample_legit_offer_1.txt": "Legitimate Offer Reference",
    "sample_legit_offer_2.txt": "Legitimate Offer Reference",
}

def extract_company_name(offer_text):
    prompt = f"""Extract only the company name mentioned in this offer letter or communication. Respond with ONLY the company name, nothing else, no explanation. If no company name is found, respond with exactly: Unknown

Text:
{offer_text}"""
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=300,
        reasoning_effort="low"
    )
    content = response.choices[0].message.content or ""
    return content.strip()

def search_company(company_name):
    if not SERPER_API_KEY or company_name.lower() == "unknown":
        return None
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": f"{company_name} reviews scam complaints internship"},
            timeout=10
        )
        data = response.json()
        snippets = []
        for result in data.get("organic", [])[:5]:
            snippets.append(f"{result.get('title','')}: {result.get('snippet','')}")
        return "\n".join(snippets) if snippets else None
    except Exception:
        return None

def analyze_offer(offer_text):
    results = collection.query(
        query_texts=[offer_text],
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

    company_name = extract_company_name(offer_text)
    search_results = search_company(company_name)

    if search_results:
        company_context = f"\n\nWeb search results for company '{company_name}':\n{search_results}"
    elif company_name.lower() != "unknown":
        company_context = f"\n\nNo notable web search results found for company '{company_name}'. A lack of any online presence, reviews, or verifiable footprint for a company is itself a moderate risk signal, even if the letter text looks clean."
    else:
        company_context = "\n\nNo company name could be identified in this text."

    prompt = f"""You are a fraud-detection assistant. Be brief and direct. Do not repeat yourself. Analyze this internship/job offer letter or communication.
Use the reference context below (source labels in brackets) AND the web search findings about the company to make your assessment. A clean-sounding letter from an unverifiable or negatively-reviewed company should still be scored as risky.

Reference context:
{context}
{company_context}

Text to analyze:
{offer_text}

Output ONLY this JSON object, nothing else:
{{
  "risk_score": <integer 0-100>,
  "risk_level": "<Low, Medium, or High>",
  "flags": [
    {{"issue": "<short title>", "reasoning": "<1 sentence>", "source": "<source label or none>"}}
  ],
  "company_check": {{
    "company_name": "<name or Unknown>",
    "verification_summary": "<1 sentence>",
    "found_concerns": <true or false>
  }},
  "summary": "<1 sentence overall verdict>"
}}"""

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1200,
        reasoning_effort="low",
        response_format={"type": "json_object"}
    )

    raw = (response.choices[0].message.content or "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "risk_score": 50, "risk_level": "Medium", "flags": [],
            "company_check": {"company_name": company_name, "verification_summary": "Could not parse LLM response.", "found_concerns": False},
            "summary": "Analysis completed but response format was unexpected."
        }

    parsed["confidence"] = confidence
    return parsed