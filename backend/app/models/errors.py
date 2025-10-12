from fastapi import HTTPException, status

class LLMError(HTTPException):
    """
    Error related to LLM service (OpenAI API).
    """
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {detail}"
        )

class StorageError(HTTPException):
    """
    Error related to file or vector storage.
    """
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage error: {detail}"
        )

class JournalNotFoundError(HTTPException):
    """
    Journal entry not found.
    """
    def __init__(self, journal_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal not found: {journal_id}"
        )

class ValidationError(HTTPException):
    """
    Validation error for invalid input.
    """
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

