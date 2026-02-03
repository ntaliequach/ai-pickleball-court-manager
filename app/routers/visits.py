from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import schemas, crud
from ..db import SessionLocal

router = APIRouter(prefix="/visits", tags=["visits"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.VisitOut)
def create_visit(v: schemas.VisitCreate, db: Session = Depends(get_db)):
    court = crud.get_court(db, v.court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Court not found")
    return crud.create_visit(db, v)

@router.get("/", response_model=List[schemas.VisitOut])
def list_visits(court_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.list_visits(db, court_id)

@router.get("/most-visited")
def most_visited(db: Session = Depends(get_db)):
    rows = crud.most_visited(db)
    return [{"court": r["court"].id, "name": r["court"].name, "visits_count": r["visits_count"]} for r in rows]