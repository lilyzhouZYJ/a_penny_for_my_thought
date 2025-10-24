import logging
from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from app.models import Message, RetrievedContext
from app.storage.vector_storage import VectorStorage
from app.utils.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(
        self,
        vector_storage: VectorStorage,
        embeddings: EmbeddingManager
    ):
        """
        Initialize RAG service.
        
        Args:
            vector_storage: Vector database for storing/searching embeddings
            embeddings: Embedding manager for generating vectors
        """
        self.vector_storage = vector_storage
        self.embeddings = embeddings
    
    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[RetrievedContext]:
        """
        Retrieve relevant past conversation chunks for RAG context.
        Used during chat to find semantically similar past discussions.
        
        Args:
            query: User's query/message
            top_k: Maximum number of context chunks to retrieve
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
        
        Returns:
            List of relevant context chunks with metadata
        """
        try:
            # Perform similarity search
            results = await self.vector_storage.similarity_search(
                query=query,
                top_k=top_k
            )
            
            # Filter by similarity threshold
            filtered_results = [
                ctx for ctx in results
                if ctx.similarity_score >= similarity_threshold
            ]
            
            logger.info(
                f"Retrieved {len(filtered_results)}/{len(results)} contexts "
                f"above threshold {similarity_threshold}"
            )
            
            return filtered_results
            
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            # Return empty list for graceful degradation
            return []
    
    async def index_conversation(
        self,
        messages: List[Message],
        session_id: str,
        metadata: Dict
    ) -> None:
        """
        Index conversation in vector store for future semantic search.
        
        Called when a conversation is saved to disk.
        Chunks messages into user+assistant pairs and generates embeddings.
        
        Args:
            messages: List of messages from the conversation
            session_id: Session UUID
            metadata: Additional metadata (date, title, etc.)
        """
        try:
            # Chunk conversation into user+assistant pairs
            chunks = self._chunk_conversation(messages)
            
            if not chunks:
                logger.warning("No chunks created from conversation")
                return
            
            # Prepare data for vector store
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk['content'])
                
                # Combine metadata
                chunk_metadata = {
                    **metadata,
                    'session_id': session_id,
                    'chunk_index': i,
                    'message_ids': chunk['message_ids']
                }
                metadatas.append(chunk_metadata)
                
                # Generate unique ID for this chunk
                chunk_id = f"{session_id}_chunk_{i}_{uuid4().hex[:8]}"
                ids.append(chunk_id)
            
            # Add to vector store
            await self.vector_storage.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Indexed {len(chunks)} chunks from session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to index conversation: {e}")
            # Don't raise - indexing failure shouldn't prevent saving
            # Conversation is still saved to disk (source of truth)
    
    def _chunk_conversation(self, messages: List[Message]) -> List[Dict]:
        """
        Chunk conversation into semantic units (user+assistant message pairs).
        
        Strategy: Each chunk contains one user message + corresponding assistant response.
        This preserves the question-answer context for better retrieval.
        
        Args:
            messages: List of messages from conversation
        
        Returns:
            List of chunks, each with 'content' and 'message_ids'
        """
        chunks = []
        
        # Process messages in pairs (user + assistant)
        i = 0
        while i < len(messages) - 1:
            current = messages[i]
            next_msg = messages[i + 1]
            
            # Look for user+assistant pairs
            if current.role == "user" and next_msg.role == "assistant":
                chunk_content = (
                    f"User: {current.content}\n\n"
                    f"Assistant: {next_msg.content}"
                )
                
                chunks.append({
                    'content': chunk_content,
                    'message_ids': [current.id, next_msg.id]
                })
                
                i += 2  # Skip both messages
            else:
                # Skip mismatched messages (shouldn't happen normally)
                i += 1
        
        return chunks
    
    async def index_write_content(
        self,
        content: str,
        session_id: str,
        metadata: Dict
    ) -> None:
        """
        Index write mode content in vector store for future semantic search.
        
        Args:
            content: Write mode journal content
            session_id: Session UUID
            metadata: Additional metadata (date, title, mode, etc.)
        """
        try:
            if not content.strip():
                logger.warning("No content to index for write mode")
                return
            
            # Chunk the content into smaller pieces for better retrieval
            chunks = self._chunk_write_content(content)
            
            if not chunks:
                logger.warning("No chunks created from write content")
                return
            
            # Prepare data for vector store
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                
                # Combine metadata
                chunk_metadata = {
                    **metadata,
                    'session_id': session_id,
                    'chunk_index': i,
                    'content_type': 'write_mode'
                }
                metadatas.append(chunk_metadata)
                
                # Generate unique ID for this chunk
                chunk_id = f"{session_id}_write_chunk_{i}_{uuid4().hex[:8]}"
                ids.append(chunk_id)
            
            # Add to vector store
            await self.vector_storage.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Indexed {len(chunks)} chunks from write content session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to index write content: {e}")
            # Don't raise - indexing failure shouldn't prevent saving
    
    def _chunk_write_content(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Chunk write mode content into semantic units.
        
        Strategy: Split content by paragraphs and sentences to create meaningful chunks.
        
        Args:
            content: Write mode journal content
            max_chunk_size: Maximum characters per chunk
        
        Returns:
            List of content chunks
        """
        if not content.strip():
            return []
        
        chunks = []
        
        # Split by double newlines (paragraphs) first
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If paragraph is small enough, use it as-is
            if len(paragraph) <= max_chunk_size:
                chunks.append(paragraph)
            else:
                # Split large paragraphs by sentences
                sentences = paragraph.split('. ')
                current_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    # Add period back if it was removed by split
                    if not sentence.endswith('.') and not sentence.endswith('!') and not sentence.endswith('?'):
                        sentence += '.'
                    
                    # If adding this sentence would exceed max size, save current chunk
                    if len(current_chunk) + len(sentence) + 1 > max_chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
                
                # Add the last chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
        
        return chunks

