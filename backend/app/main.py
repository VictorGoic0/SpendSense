from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, Base
from app import models  # Import models to register them with Base
from app.routers import ingest, features, profile, users, operator, personas, recommendations, consent, products  # , evaluation - disabled for Railway deployment
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SpendSense API",
    description="Personalized financial education platform with behavioral pattern detection and AI-generated recommendations",
    version="1.0.0",
    redirect_slashes=False  # Prevent redirect issues with Railway HTTPS
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:3000",  # React dev
        "https://spend-sense-goico.netlify.app"  # Netlify
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


# Include routers
app.include_router(ingest.router)
app.include_router(features.router)
app.include_router(profile.router)
app.include_router(users.router)
app.include_router(operator.router)
app.include_router(personas.router)
app.include_router(recommendations.router)
app.include_router(consent.router)
app.include_router(products.router)
# app.include_router(evaluation.router)  # Disabled for Railway deployment - requires pandas/numpy


@app.get("/")
async def root():
    return {"message": "SpendSense API"}



# Standard startup for local development and Railway deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

