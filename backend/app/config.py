from pathlib import Path
from typing import List
import json

from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4.1"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Storage Configuration
    vector_db_directory: Path = Path("./chroma_db")
    database_path: Path = Path("./chat_history.db")
    
    # RAG Configuration
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000"]
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                return json.loads(v)
            except json.JSONDecodeError:
                # If not JSON, split by comma and strip whitespace
                return [origin.strip() for origin in v.split(',')]
        return v
    
    # LLM Configuration
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    streaming_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


