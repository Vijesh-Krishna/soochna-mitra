from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.db.database import Base, engine
from app.models.dataset import RawSnapshot, DistrictMonthly
from sqlalchemy.exc import OperationalError

app = FastAPI(title="SoochnaMitra API", version="1.0")

# Try to create tables (safe)
try:
    Base.metadata.create_all(bind=engine)
except OperationalError as e:
    print("Database connection failed:", e)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your API routes
app.include_router(api_router)

# Root route
@app.get("/")
def root():
    return {"message": "SoochnaMitra backend is running successfully!"}