from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from .. import schemas, crud, models
from ..db import SessionLocal

router = APIRouter(prefix="/courts", tags=["courts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.CourtOut)
def create_court(court: schemas.CourtCreate, db: Session = Depends(get_db)):
    return crud.create_court(db, court)

@router.get("/", response_model=List[schemas.CourtOut])
def read_courts(indoor: Optional[bool] = Query(None), q: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.list_courts(db, indoor=indoor, q=q)

@router.get("/{court_id}", response_model=schemas.CourtOut)
def read_court(court_id: int, db: Session = Depends(get_db)):
    c = crud.get_court(db, court_id)
    if not c:
        raise HTTPException(status_code=404, detail="Court not found")
    return c

@router.put("/{court_id}", response_model=schemas.CourtOut)
def update_court(court_id: int, patch: schemas.CourtUpdate, db: Session = Depends(get_db)):
    updated = crud.update_court(db, court_id, patch.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Court not found")
    return updated

@router.delete("/{court_id}")
def delete_court(court_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_court(db, court_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Court not found")
    return {"deleted": bool(deleted)}