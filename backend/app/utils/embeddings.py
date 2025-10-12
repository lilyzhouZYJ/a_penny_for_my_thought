from typing import List
from langchain_openai import OpenAIEmbeddings

class EmbeddingManager:
    """
    Converts text into vector representations for semantic search.
    """
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: str = None):
        """
        Initialize embedding manager.
        
        Args:
            model: OpenAI embedding model to use
            api_key: OpenAI API key (optional, uses env var if not provided)
        """
        self.model = model
        self.embeddings = OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key
        )
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents (batch operation for efficiency).
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors (each is 1536-dimensional for text-embedding-3-small)
        """
        return await self.embeddings.aembed_documents(texts)
    
    async def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query string.
        
        Args:
            text: Query text to embed
        
        Returns:
            Embedding vector (1536-dimensional)
        """
        return await self.embeddings.aembed_query(text)

