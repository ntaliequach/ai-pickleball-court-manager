from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi import HTTPException
from typing import List, Optional
import os, json, datetime, statistics
from ..services import vector_store
from ..db import SessionLocal
from sqlalchemy.orm import Session
from .. import crud

router = APIRouter(prefix="/ai", tags=["ai"])

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "memory.json")
os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)

def _load_memory() -> dict:
    if not os.path.exists(MEMORY_PATH):
        return {}
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_memory(mem: dict):
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def _ensure_user(mem: dict, user_id: str):
    if user_id not in mem:
        mem[user_id] = {"messages": [], "prefs": {}}

def _extract_preferences_from_text(text: str) -> dict:
    prefs = {}
    t = text.lower()
    if "prefer indoor" in t or "i prefer indoor" in t:
        prefs["prefer_indoor"] = True
    if "prefer outdoor" in t or "i prefer outdoor" in t:
        prefs["prefer_indoor"] = False
    if "weekend" in t or "saturdays" in t or "sundays" in t:
        prefs["plays_weekends"] = True
    return prefs

@router.post("/load-text")
async def load_text(file: UploadFile = File(...), source: Optional[str] = Form(None)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files accepted")
    text = (await file.read()).decode("utf-8")
    count = vector_store.ingest_text(text, metadata={"source": source or file.filename})
    return {"ingested_chunks": count}

@router.post("/semantic-search")
async def semantic_search(query: str = Form(...), k: int = Form(5)):
    results = vector_store.semantic_search(query, k=k)
    return {"query": query, "results": results}

def _llm_fallback_answer(query: str, docs: List[dict]):
    """Generate a grounded answer from retrieved documents"""
    if not docs:
        return {
            "grounded": "",
            "concise": f"No relevant information found for: {query}"
        }
    
    # Extract relevant info from top docs
    query_lower = query.lower()
    
    # Collect court info
    court_info = []
    for d in docs[:5]:
        name = d.get("name", "Unknown")
        text = d.get("text", "")
        metadata = d.get("metadata", {})
        
        # Build a summary for this court
        summary_parts = [name]
        
        # Extract key details from text
        if "free" in text.lower():
            summary_parts.append("(Free)")
        elif "pay" in text.lower():
            summary_parts.append("(Pay to play)")
            
        if "indoor" in metadata:
            indoor_str = "Indoor" if metadata["indoor"] == "true" else "Outdoor"
            summary_parts.append(indoor_str)
            
        if "location" in metadata:
            summary_parts.append(f"in {metadata['location']}")
        
        # Add relevant text snippet
        if text and len(text) > 20:
            # Try to find the most relevant sentence
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            relevant_sentence = sentences[0] if sentences else text[:200]
            summary_parts.append(f"- {relevant_sentence}")
        
        court_info.append(" ".join(summary_parts))
    
    # Generate natural language answer
    if "free" in query_lower:
        answer = "Free courts: " + "; ".join([info for info in court_info if "Free" in info])
    elif "indoor" in query_lower:
        answer = "Indoor courts: " + "; ".join([info for info in court_info if "Indoor" in info])
    elif "wheelchair" in query_lower or "accessible" in query_lower:
        answer = "Accessible courts: " + "; ".join([info for info in court_info if "wheelchair" in info.lower() or "accessible" in info.lower()])
    elif "lesson" in query_lower or "trainer" in query_lower:
        answer = "Courts with trainers/lessons: " + "; ".join([info for info in court_info if "trainer" in info.lower() or "lesson" in info.lower()])
    else:
        # General query - return top courts
        answer = "Relevant courts: " + "; ".join(court_info[:3])
    
    # Fallback if no specific matches
    if not answer or answer.endswith(": "):
        answer = "Based on your query, here are the top matches: " + "; ".join(court_info[:3])
    
    # Combine all text for grounded context
    combined = "\n\n".join([f"{d.get('name', 'Unknown')}: {d.get('text', '')}" for d in docs[:3]])
    
    return {
        "grounded": combined,
        "concise": answer
    }

@router.post("/rag")
async def rag(query: str = Form(...), k: int = Form(5)):
    docs = vector_store.semantic_search(query, k=k)
    # Use local extractive summarization / grounding — no external LLMs
    result = _llm_fallback_answer(query, docs)
    return {"answer": result["concise"], "source_docs": docs, "grounded_text": result["grounded"]}

@router.post("/chat")
async def chat(user_id: str = Form("default"), message: str = Form(...)):
    mem = _load_memory()
    _ensure_user(mem, user_id)
    # store message
    mem[user_id]["messages"].append({"role": "user", "text": message, "ts": datetime.datetime.utcnow().isoformat()})
    # extract simple prefs
    prefs = _extract_preferences_from_text(message)
    mem[user_id]["prefs"].update(prefs)
    _save_memory(mem)
    # form reply that references memory
    prefs_summary = ", ".join(f"{k}={v}" for k,v in mem[user_id]["prefs"].items()) or "no preferences yet"
    reply = f"Received. I have saved your preferences: {prefs_summary}. You said: {message}"
    mem[user_id]["messages"].append({"role": "assistant", "text": reply, "ts": datetime.datetime.utcnow().isoformat()})
    _save_memory(mem)
    return {"reply": reply, "memory": mem[user_id]}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/visit-summary")
def visit_summary(period: str = "weekly", db: Session = Depends(get_db)):
    # Gather recent visits
    visits = crud.list_visits(db)
    if not visits:
        return {"summary": "No visits recorded."}
    # convert visited_at datetimes
    now = datetime.datetime.utcnow()
    if period == "weekly":
        cutoff = now - datetime.timedelta(days=7)
    else:
        cutoff = now - datetime.timedelta(days=30)
    recent = [v for v in visits if v.visited_at and v.visited_at >= cutoff]
    if not recent:
        return {"summary": f"No visits in the last {period} period."}
    # stats
    per_court = {}
    crowded_vals = []
    for v in recent:
        cid = v.court_id
        per_court[cid] = per_court.get(cid, 0) + 1
        if v.crowdedness is not None:
            crowded_vals.append(v.crowdedness)
    most_played_court = max(per_court.items(), key=lambda x: x[1])[0]
    avg_crowd = statistics.mean(crowded_vals) if crowded_vals else None
    summary = {
        "visits_count": len(recent),
        "most_played_court_id": most_played_court,
        "visits_per_court": per_court,
        "average_crowdedness": avg_crowd
    }
    # simple natural language narration
    narration = f"In the last {period}, you visited {len(recent)} times. You visited court {most_played_court} most ({per_court[most_played_court]} times)."
    if avg_crowd is not None:
        narration += f" Average crowdedness: {avg_crowd:.1f}/10."
    return {"summary": summary, "narration": narration}