from functools import lru_cache

from app.config import settings
from app.services.chat_service import ChatService
from app.services.journal_service import JournalService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.storage.file_storage import FileStorage
from app.storage.vector_storage import VectorStorage
from app.utils.embeddings import EmbeddingManager

# Storage layer (singletons)

@lru_cache()
def get_file_storage() -> FileStorage:
    """Get FileStorage singleton instance."""
    return FileStorage(base_directory=settings.journals_directory)


@lru_cache()
def get_embedding_manager() -> EmbeddingManager:
    """Get EmbeddingManager singleton instance."""
    return EmbeddingManager(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key
    )


@lru_cache()
def get_vector_storage() -> VectorStorage:
    """Get VectorStorage singleton instance."""
    embedding_manager = get_embedding_manager()
    return VectorStorage(
        persist_directory=settings.vector_db_directory,
        embedding_manager=embedding_manager
    )


# Service layer

@lru_cache()
def get_llm_service() -> LLMService:
    """Get LLMService singleton instance."""
    return LLMService(
        openai_api_key=settings.openai_api_key,
        model_name=settings.openai_model
    )


def get_rag_service() -> RAGService:
    """Get RAGService instance."""
    return RAGService(
        vector_storage=get_vector_storage(),
        embeddings=get_embedding_manager()
    )


def get_journal_service() -> JournalService:
    """Get JournalService instance."""
    return JournalService(
        file_storage=get_file_storage(),
        vector_storage=get_vector_storage(),
        rag_service=get_rag_service(),
        llm_service=get_llm_service()
    )


def get_chat_service() -> ChatService:
    """Get ChatService instance."""
    print("GET CHAT SERVICE")
    return ChatService(
        llm_service=get_llm_service(),
        rag_service=get_rag_service(),
        journal_service=get_journal_service()
    )

