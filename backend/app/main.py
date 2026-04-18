from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.routes import public
from app.database import engine, Base
from app.config import get_settings
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

# Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request duration")

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

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    REQUEST_DURATION.observe(duration)
    return response

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Serve frontend frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("frontend/index.html") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>AusClean Pro API</h1><p>Visit /docs for API documentation</p>")

# Routes
app.include_router(public.router, prefix="/api/v1", tags=["public"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
