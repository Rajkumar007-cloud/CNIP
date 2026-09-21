from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from app.core.config import settings
from app.db.neo4j import db, get_db
from app.api.routes import router as api_router


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("application_starting")
    try:
        # Verify Neo4j connection
        get_db().driver.verify_connectivity()
        logger.info("neo4j_verified")
    except Exception as e:
        logger.error("neo4j_verification_failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    db.close()


app = FastAPI(
    title="Criminal Network Intelligence Platform",
    description="AI-Powered Criminal Network Analysis System - Project PS26189",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Criminal Network Intelligence Platform API",
        "version": "1.0.0",
        "project": "PS26189",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        get_db().driver.verify_connectivity()
        neo4j_status = "healthy"
    except Exception:
        neo4j_status = "unhealthy"
    
    from datetime import datetime
    return {
        "status": "healthy" if neo4j_status == "healthy" else "degraded",
        "neo4j": neo4j_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_config=None
    )