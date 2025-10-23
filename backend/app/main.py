import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.error_handler import error_handler_middleware
from app.api.v1 import chat, journals
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
    logger.info("Starting A Penny For My Thought backend...")
    
    # Create storage directories
    settings.vector_db_directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created storage directory: {settings.vector_db_directory}")
    
    # Validate OpenAI API key
    if not settings.openai_api_key or settings.openai_api_key == "sk-your-api-key-here":
        logger.warning("OPENAI_API_KEY not configured! Set it in .env file.")
    else:
        logger.info("OpenAI API key configured")
    
    logger.info(f"Backend started successfully on {settings.api_host}:{settings.api_port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down A Penny For My Thought backend...")


# Create FastAPI application
app = FastAPI(
    title="A Penny For My Thought API",
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

# Add error handling middleware
app.middleware("http")(error_handler_middleware)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "a-penny-for-my-thought-backend",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LLM Journal Webapp API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "/api/v1/chat",
            "chat_stream": "/api/v1/chat/stream",
            "journals": "/api/v1/journals"
        }
    }


# Include API routers
app.include_router(chat.router, prefix="/api/v1")
app.include_router(journals.router, prefix="/api/v1")

