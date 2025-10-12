import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ThisIsMyJournal backend...")
    
    # Create storage directories
    settings.journals_directory.mkdir(parents=True, exist_ok=True)
    settings.vector_db_directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created storage directories: {settings.journals_directory}, {settings.vector_db_directory}")
    
    # Validate OpenAI API key
    if not settings.openai_api_key or settings.openai_api_key == "sk-your-api-key-here":
        logger.warning("OPENAI_API_KEY not configured! Set it in .env file.")
    else:
        logger.info("OpenAI API key configured")
    
    logger.info(f"Backend started successfully on {settings.api_host}:{settings.api_port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend...")


# Create FastAPI application
app = FastAPI(
    title="LLM Journal Webapp API",
    description="Backend API for LLM-powered journaling application with RAG",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "llm-journal-webapp-backend",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LLM Journal Webapp API",
        "docs": "/docs",
        "health": "/health",
    }


# TODO: Add API routers here in later tasks
# from app.api.v1 import chat, journals
# app.include_router(chat.router, prefix="/api/v1")
# app.include_router(journals.router, prefix="/api/v1")

