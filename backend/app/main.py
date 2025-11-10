from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, Base, get_db
from app import models  # Import models to register them with Base
from app.routers import ingest, features, profile, users, operator, personas, recommendations, consent, products, evaluation
from app.utils.seed_data import seed_database
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    
    # Seed database with synthetic data if in Lambda environment and database is empty
    # This ensures data is available on cold starts
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        logger.info("Lambda environment detected, checking if database needs seeding...")
        db = next(get_db())
        try:
            seed_database(db)
        except Exception as e:
            logger.error(f"Error seeding database on startup: {e}", exc_info=True)
        finally:
            db.close()


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

