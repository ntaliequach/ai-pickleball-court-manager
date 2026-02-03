from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from typing import List, Optional

def create_court(db: Session, court: schemas.CourtCreate):
    db_obj = models.Court(**court.dict())
    db.add(db_obj); db.commit(); db.refresh(db_obj)
    return db_obj

def get_court(db: Session, court_id: int):
    return db.query(models.Court).filter(models.Court.id == court_id).first()

def list_courts(db: Session, indoor: Optional[bool]=None, q: Optional[str]=None):
    query = db.query(models.Court)
    if indoor is not None:
        query = query.filter(models.Court.indoor == indoor)
    if q:
        like = f"%{q}%"
        query = query.filter((models.Court.name.ilike(like)) | (models.Court.address.ilike(like)))
    return query.all()

def update_court(db: Session, court_id: int, data: dict):
    db_obj = get_court(db, court_id)
    if not db_obj:
        return None
    for k, v in data.items():
        setattr(db_obj, k, v)
    db.add(db_obj); db.commit(); db.refresh(db_obj)
    return db_obj

def delete_court(db: Session, court_id: int):
    db_obj = get_court(db, court_id)
    if not db_obj:
        return 0
    db.delete(db_obj); db.commit()
    return 1

def create_visit(db: Session, visit: schemas.VisitCreate):
    db_obj = models.Visit(**visit.dict())
    db.add(db_obj); db.commit(); db.refresh(db_obj)
    return db_obj

def list_visits(db: Session, court_id: Optional[int]=None):
    q = db.query(models.Visit)
    if court_id:
        q = q.filter(models.Visit.court_id == court_id)
    return q.order_by(models.Visit.visited_at.desc()).all()

def most_visited(db: Session, limit: int = 10):
    q = (
        db.query(models.Court, func.count(models.Visit.id).label("visits_count"))
        .outerjoin(models.Visit)
        .group_by(models.Court.id)
        .order_by(func.count(models.Visit.id).desc())
        .limit(limit)
    )
    return [{"court": c, "visits_count": cnt} for c, cnt in q.all()]