from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base
from .routers import courts, visits
# NEW: include ai router
from .routers import ai

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["http://localhost"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

app.include_router(courts.router, prefix="/api")
app.include_router(visits.router, prefix="/api")
# NEW: mount AI endpoints under /api/ai
app.include_router(ai.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Pickleball Court Manager"}