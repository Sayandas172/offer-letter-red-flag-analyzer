import os
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./vectorstore")

try:
    client.delete_collection("offers")
except Exception:
    pass
collection = client.create_collection("offers")

SEVERITY = {
    "pay_to_participate.txt": 95,
    "exclusivity_clause.txt": 55,
    "vague_company_info.txt": 65,
    "no_fixed_format.txt": 40,
    "pressure_tactics.txt": 70,
}

def load_and_chunk(folder, doc_type):
    chunks = []
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
            for i, para in enumerate(text.split('\n\n')):
                if para.strip():
                    chunks.append({
                        "id": f"{fname}_{i}",
                        "text": para.strip(),
                        "source": fname,
                        "type": doc_type,
                        "severity": SEVERITY.get(fname, 0)
                    })
    return chunks

all_chunks = load_and_chunk("data/redflags", "redflag") + load_and_chunk("data/offers", "legit")

for c in all_chunks:
    embedding = model.encode(c["text"]).tolist()
    collection.add(
        ids=[c["id"]],
        embeddings=[embedding],
        documents=[c["text"]],
        metadatas=[{"source": c["source"], "type": c["type"], "severity": c["severity"]}]
    )

print(f"Ingested {len(all_chunks)} chunks with metadata.")