from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CourtBase(BaseModel):
    name: str
    address: Optional[str] = None
    num_courts: Optional[int] = 1
    indoor: Optional[bool] = False
    notes: Optional[str] = ""
    hours: Optional[str] = None  # human-readable hours/schedule field

class CourtCreate(CourtBase):
    pass

class CourtUpdate(CourtBase):
    pass

class CourtOut(CourtBase):
    id: int
    class Config:
        orm_mode = True

class VisitBase(BaseModel):
    visited_at: datetime
    crowdedness: Optional[int] = None
    notes: Optional[str] = ""

class VisitCreate(VisitBase):
    court_id: int

class VisitOut(VisitBase):
    id: int
    court_id: int
    class Config:
        orm_mode = True