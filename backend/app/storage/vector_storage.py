import logging
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.models import RetrievedContext, StorageError
from app.utils.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)

class VectorStorage:
    """
    Handles vector database operations using ChromaDB.
    This is used for semantic search (RAG).
    """
    
    def __init__(self, persist_directory: Path, embedding_manager: EmbeddingManager):
        """
        Initialize vector storage with ChromaDB persistent client.
        
        Args:
            persist_directory: Directory for ChromaDB persistent storage
            embedding_manager: Manager for generating embeddings
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_manager = embedding_manager
        
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            # Get or create collection for journal conversations
            self.collection = self.client.get_or_create_collection(
                name="journal_conversations",
                metadata={
                    "hnsw:space": "cosine",  # Similarity metric
                    "hnsw:construction_ef": 200,  # Index quality
                    "hnsw:M": 16  # Connectivity
                }
            )
            
            logger.info(f"ChromaDB initialized at {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise StorageError(f"Vector database initialization failed: {e}")
    
    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """
        Add documents to vector store with embeddings.
        
        Args:
            documents: List of text content to store
            metadatas: List of metadata dicts for each document
            ids: List of unique IDs for each document
        
        Raises:
            StorageError: If documents cannot be added
        """
        try:
            # Generate embeddings
            embeddings = await self.embedding_manager.embed_documents(documents)
            
            # Add to ChromaDB collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise StorageError(f"Failed to index documents: {e}")
    
    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[RetrievedContext]:
        """
        Perform similarity search for relevant context.
        
        Used during chat to find semantically similar past conversations.
        NOT used for loading conversations into the UI.
        
        Args:
            query: Query string to search for
            top_k: Number of results to return
            filter: Optional metadata filter
        
        Returns:
            List of retrieved context chunks with similarity scores
        
        Raises:
            StorageError: If search fails
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_manager.embed_query(query)
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter
            )
            
            # Convert to RetrievedContext objects
            retrieved_contexts = []
            
            if results and results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
                distances = results['distances'][0] if results['distances'] else [0.0] * len(documents)
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    # Convert distance to similarity score (cosine distance -> similarity)
                    # ChromaDB returns distance (0 = identical, 2 = opposite)
                    # Convert to similarity (1 = identical, 0 = opposite)
                    similarity_score = 1.0 - (distance / 2.0)
                    
                    retrieved_contexts.append(
                        RetrievedContext(
                            content=doc,
                            metadata=metadata or {},
                            similarity_score=similarity_score
                        )
                    )
            
            logger.info(f"Found {len(retrieved_contexts)} relevant contexts for query")
            return retrieved_contexts
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            # Don't raise - graceful degradation for RAG
            # Return empty list to allow chat to continue without context
            return []
    
    async def delete_by_metadata(self, filter: Dict) -> None:
        """
        Delete documents matching metadata filter.
        
        Used when deleting journals to also remove from vector store.
        
        Args:
            filter: Metadata filter (e.g., {"session_id": "abc-123"})
        
        Raises:
            StorageError: If deletion fails
        """
        try:
            # Get IDs matching filter
            results = self.collection.get(where=filter)
            
            if results and results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} documents from vector store")
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise StorageError(f"Failed to delete from vector store: {e}")

