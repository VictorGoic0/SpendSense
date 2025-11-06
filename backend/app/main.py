from fastapi import FastAPI
from app.database import init_db, Base
from app import models  # Import models to register them with Base

app = FastAPI(title="SpendSense API", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    return {"message": "SpendSense API"}

