from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, Base
from app import models  # Import models to register them with Base
from app.routers import ingest, features, profile, users, operator, personas, recommendations, consent, products, evaluation
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
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port + React default
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
app.include_router(evaluation.router)


@app.get("/")
async def root():
    return {"message": "SpendSense API"}


# Lambda handler using Mangum
# This is only imported/used when running in Lambda
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    # Mangum not installed, likely running locally
    handler = None

