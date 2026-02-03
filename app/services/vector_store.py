import os
import json
import math
import hashlib
import re
from typing import List, Dict, Any

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vector_docs.json")
os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)

def _load_store() -> List[Dict[str, Any]]:
    if not os.path.exists(STORE_PATH):
        return []
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_store(docs: List[Dict[str, Any]]):
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

def _tokenize(s: str) -> List[str]:
    return [w.lower() for w in "".join(ch if ch.isalnum() else " " for ch in s).split() if w]

def _vec_from_text(s: str) -> Dict[str, int]:
    v = {}
    for t in _tokenize(s):
        v[t] = v.get(t, 0) + 1
    return v

def _cosine(a: Dict[str,int], b: Dict[str,int]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a.get(k,0)*b.get(k,0) for k in a.keys() & b.keys())
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    if na==0 or nb==0:
        return 0.0
    return dot/(na*nb)

def _extract_name_from_chunk(text: str) -> str:
    """Extract court name from chunk text by looking for patterns"""
    lines = text.strip().split('\n')
    for line in lines[:5]:  # Check first few lines
        line = line.strip()
        # Skip metadata lines
        if line.startswith('===') or ':' in line and len(line.split(':')) == 2:
            continue
        # If line has text and doesn't look like a description, it's likely the name
        if line and len(line) < 100 and not line[0].islower():
            return line
    return "Unknown"

def ingest_text(text: str, metadata: Dict[str,Any]|None = None) -> int:
    text = text.strip()
    if not text:
        return 0
    
    # Split by metadata sections to keep court info together
    sections = re.split(r'\n=== METADATA ===\n', text)
    store = _load_store()
    ids = []
    
    for section in sections:
        if not section.strip():
            continue
            
        # Parse metadata from section
        section_metadata = metadata.copy() if metadata else {}
        lines = section.split('\n')
        court_name = None
        
        # Extract metadata fields and court name
        for i, line in enumerate(lines[:10]):
            if ':' in line and not line.startswith('==='):
                key, val = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                section_metadata[key] = val.strip()
            # Extract court name (usually first substantive line after metadata)
            elif not court_name and line.strip() and not line.startswith('===') and len(line.strip()) < 100:
                court_name = line.strip()
        
        if court_name:
            section_metadata['court_name'] = court_name
        
        # Chunk the section text
        chunks = [chunk.strip() for chunk in section.split('\n\n') if chunk.strip()]
        
        for chunk in chunks:
            h = hashlib.md5(chunk.encode("utf-8")).hexdigest()[:10]
            doc_id = f"doc_{h}"
            vec = _vec_from_text(chunk)
            
            # If no court_name in metadata yet, try to extract from chunk
            if 'court_name' not in section_metadata:
                extracted = _extract_name_from_chunk(chunk)
                if extracted != "Unknown":
                    section_metadata['court_name'] = extracted
            
            doc = {
                "id": doc_id,
                "text": chunk,
                "metadata": section_metadata,
                "vector": vec
            }
            store = [d for d in store if d.get("id") != doc_id]
            store.append(doc)
            ids.append(doc_id)
    
    _save_store(store)
    return len(ids)

def semantic_search(query: str, k: int = 5, collection: str | None = None) -> List[Dict[str,Any]]:
    qv = _vec_from_text(query)
    store = _load_store()
    scored = []
    for d in store:
        score = _cosine(qv, d.get("vector", {}))
        scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Deduplicate by court_name, keeping highest score chunk per court
    seen_courts = {}
    for score, d in scored:
        court_name = d.get("metadata", {}).get("court_name") or d.get("metadata", {}).get("name", "Unknown")
        if court_name not in seen_courts or score > seen_courts[court_name]["score"]:
            seen_courts[court_name] = {
                "id": d["id"],
                "name": court_name,
                "text": d["text"],
                "metadata": d.get("metadata", {}),
                "score": float(score)
            }
    
    # Return top k unique courts
    results = sorted(seen_courts.values(), key=lambda x: x["score"], reverse=True)[:k]
    return results

def clear_store():
    _save_store([])