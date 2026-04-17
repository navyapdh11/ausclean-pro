from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import public
from app.database import engine, Base
from app.config import get_settings
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AusClean Pro - Enterprise Australian Cleaning Services Platform (2026)",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(public.router, prefix="/api/v1", tags=["public"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
