from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi import HTTPException
from typing import List, Optional
import os, json, datetime, statistics, re
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
    """Extract user preferences from chat messages"""
    prefs = {}
    t = text.lower()
    if "prefer indoor" in t or "i prefer indoor" in t or "like indoor" in t:
        prefs["prefer_indoor"] = True
    if "prefer outdoor" in t or "i prefer outdoor" in t or "like outdoor" in t:
        prefs["prefer_indoor"] = False
    if "weekend" in t or "saturdays" in t or "sundays" in t:
        prefs["plays_weekends"] = True
    if "free" in t or "no cost" in t or "cheap" in t:
        prefs["prefer_free"] = True
    if "reservation" in t or "book" in t:
        prefs["likes_reservations"] = True
    return prefs

def _generate_conversational_reply(user_message: str, user_prefs: dict, user_history: list) -> str:
    """Generate a conversational response based on message content and user history"""
    msg_lower = user_message.lower()
    
    # Check conversation history for context
    previous_messages = [m.get("text", "") for m in user_history[-4:] if m.get("role") == "user"]
    
    # Greeting responses
    if msg_lower in ["hi", "hello", "hey", "what's up", "yo"]:
        greetings = [
            "Hey there! 👋 I'm your pickleball court assistant. I can help you find courts, answer questions about them, and remember your preferences. What would you like to know?",
            "Hello! 🏐 Looking for pickleball courts? I can help you find the perfect one based on your needs. What are you looking for?",
            "Hi! 👋 Welcome to your pickleball court guide. Try asking me about courts near you, free courts, indoor facilities, or anything else pickleball-related!",
        ]
        return greetings[len(user_history) % len(greetings)]
    
    # Questions about finding courts
    if any(keyword in msg_lower for keyword in ["find", "search", "looking for", "recommend", "suggest", "best", "good"]):
        if "free" in msg_lower:
            return "Looking for free courts? 🎾 I can help! Let me search our database for free pickleball courts. Which location are you interested in? (e.g., Huntington Beach, Newport Beach, Gardena)"
        elif "indoor" in msg_lower:
            return "Want to play indoors? 🏢 Great choice! I can find indoor courts for you. Are you looking for courts with specific amenities like food, lessons, or wheelchair accessibility?"
        elif "outdoor" in msg_lower:
            return "Prefer outdoor play? 🌳 Excellent! I can find outdoor courts. Are you looking for any specific amenities like lights, free play, or a certain number of courts?"
        else:
            return "I'd be happy to help you find pickleball courts! 🏐 Tell me what you're looking for:\n• Location (city or area)\n• Indoor or outdoor\n• Free or pay\n• Any specific amenities?"
    
    # Questions about features/amenities
    if any(keyword in msg_lower for keyword in ["food", "restaurant", "amenities", "parking", "lights", "wheelchair", "accessible", "lessons", "trainers", "pro shop"]):
        amenity = "that amenity"
        if "food" in msg_lower or "restaurant" in msg_lower:
            amenity = "food/dining"
        elif "lights" in msg_lower:
            amenity = "lighted courts"
        elif "wheelchair" in msg_lower or "accessible" in msg_lower:
            amenity = "wheelchair accessibility"
        elif "lesson" in msg_lower or "trainer" in msg_lower:
            amenity = "lessons/trainers"
        elif "pro shop" in msg_lower:
            amenity = "a pro shop"
            
        return f"Looking for courts with {amenity}? 🔍 Let me search for facilities that offer that. Would you like me to find courts in a specific location?"
    
    # Questions about specific courts or locations
    if any(city in msg_lower for city in ["huntington beach", "newport beach", "gardena", "fountain valley", "costa mesa", "irvine"]):
        return "Great choice! I found several courts in that area. 🎾 Would you like to know more about specific courts, or do you have other preferences? (free/paid, indoor/outdoor, etc.)"
    
    # Questions about preferences/playing style
    if "prefer" in msg_lower or "usually" in msg_lower or "like to" in msg_lower:
        return "Thanks for sharing your preferences! 📝 I'll remember that for future recommendations. Is there anything specific about courts you'd like to know right now?"
    
    # Questions about pricing
    if "price" in msg_lower or "cost" in msg_lower or "pay" in msg_lower or "free" in msg_lower:
        return "Pricing varies by court! 💰 Some are completely free (no reservations), while others charge per hour. Would you like me to find free courts or courts with specific pricing in your area?"
    
    # Questions about hours/schedule
    if "hour" in msg_lower or "open" in msg_lower or "time" in msg_lower or "schedule" in msg_lower:
        return "Court hours vary by location. ⏰ Most public courts are open from dawn to dusk, while some indoor facilities have extended evening hours. Which location are you interested in?"
    
    # Help/information requests
    if any(keyword in msg_lower for keyword in ["help", "what can you do", "how do i", "tell me"]):
        return """I can help you with several things! 🏐
        
✨ **Find Courts** - Ask me to find pickleball courts in your area
🔍 **Search by Features** - Looking for free, indoor, outdoor, wheelchair accessible, etc.
💾 **Remember Preferences** - Tell me your playing style and I'll remember it
📊 **Get Recommendations** - Based on your preferences and history
❓ **Answer Questions** - About specific courts, amenities, hours, pricing

What would you like to do?"""
    
    # Generic fallback - ask them to search
    return f"That's interesting! 🤔 I'd love to help you find the perfect pickleball court. Why don't you tell me:\n• What location you're interested in\n• Whether you prefer indoor or outdoor\n• If you're looking for free or paid courts\n\nThen I can give you specific recommendations!"

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
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            relevant_sentence = sentences[0] if sentences else text[:200]
            summary_parts.append(f"- {relevant_sentence}")
        
        court_info.append(" ".join(summary_parts))
    
    # Generate natural language answer
    if "free" in query_lower:
        answer = "🎾 Free courts: " + "; ".join([info for info in court_info if "Free" in info])
    elif "indoor" in query_lower:
        answer = "🏢 Indoor courts: " + "; ".join([info for info in court_info if "Indoor" in info])
    elif "wheelchair" in query_lower or "accessible" in query_lower:
        answer = "♿ Accessible courts: " + "; ".join([info for info in court_info if "wheelchair" in info.lower() or "accessible" in info.lower()])
    elif "lesson" in query_lower or "trainer" in query_lower:
        answer = "🏆 Courts with trainers/lessons: " + "; ".join([info for info in court_info if "trainer" in info.lower() or "lesson" in info.lower()])
    else:
        answer = "🏐 Relevant courts: " + "; ".join(court_info[:3])
    
    if not answer or answer.endswith(": "):
        answer = "🏐 Based on your query, here are the top matches: " + "; ".join(court_info[:3])
    
    combined = "\n\n".join([f"{d.get('name', 'Unknown')}: {d.get('text', '')}" for d in docs[:3]])
    
    return {
        "grounded": combined,
        "concise": answer
    }

@router.post("/rag")
async def rag(query: str = Form(...), k: int = Form(5)):
    docs = vector_store.semantic_search(query, k=k)
    result = _llm_fallback_answer(query, docs)
    return {"answer": result["concise"], "source_docs": docs, "grounded_text": result["grounded"]}

@router.post("/chat")
async def chat(user_id: str = Form("default"), message: str = Form(...)):
    """Conversational chat endpoint that responds contextually"""
    mem = _load_memory()
    _ensure_user(mem, user_id)
    
    # Store user message
    mem[user_id]["messages"].append({
        "role": "user", 
        "text": message, 
        "ts": datetime.datetime.utcnow().isoformat()
    })
    
    # Extract and update preferences
    prefs = _extract_preferences_from_text(message)
    mem[user_id]["prefs"].update(prefs)
    
    # Generate conversational reply
    reply = _generate_conversational_reply(message, mem[user_id]["prefs"], mem[user_id]["messages"])
    
    # Store assistant response
    mem[user_id]["messages"].append({
        "role": "assistant", 
        "text": reply, 
        "ts": datetime.datetime.utcnow().isoformat()
    })
    
    _save_memory(mem)
    
    return {
        "reply": reply, 
        "memory": mem[user_id]
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/visit-summary")
def visit_summary(period: str = "weekly", db: Session = Depends(get_db)):
    visits = crud.list_visits(db)
    if not visits:
        return {"summary": "No visits recorded."}
    
    now = datetime.datetime.utcnow()
    if period == "weekly":
        cutoff = now - datetime.timedelta(days=7)
    else:
        cutoff = now - datetime.timedelta(days=30)
    
    recent = [v for v in visits if v.visited_at and v.visited_at >= cutoff]
    if not recent:
        return {"summary": f"No visits in the last {period} period."}
    
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
    
    narration = f"In the last {period}, you visited {len(recent)} times. You visited court {most_played_court} most ({per_court[most_played_court]} times)."
    if avg_crowd is not None:
        narration += f" Average crowdedness: {avg_crowd:.1f}/10."
    
    return {"summary": summary, "narration": narration}