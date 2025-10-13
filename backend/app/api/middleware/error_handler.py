"""Global error handling middleware."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from openai import APIError, RateLimitError, APIConnectionError, AuthenticationError

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware.
    
    Catches exceptions and returns user-friendly error responses.
    """
    try:
        return await call_next(request)
        
    except RateLimitError as e:
        logger.error(f"OpenAI rate limit: {e}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Please try again in a moment."
            }
        )
    
    except AuthenticationError as e:
        logger.error(f"OpenAI authentication error: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "LLM service authentication failed. Please check configuration."
            }
        )
    
    except APIConnectionError as e:
        logger.error(f"OpenAI connection error: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Connection to LLM service failed. Please check internet connection."
            }
        )
    
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "LLM service temporarily unavailable."
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred."
            }
        )

