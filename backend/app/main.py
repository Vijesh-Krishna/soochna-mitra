# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.db.database import Base, engine
from app.models.dataset import RawSnapshot, DistrictMonthly

# Create tables on startup (safe, idempotent)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SoochnaMitra API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod restrict to your front-end domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "SoochnaMitra API running"}
