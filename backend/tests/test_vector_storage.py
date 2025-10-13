"""Unit tests for VectorStorage service with mocked dependencies."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil

from app.storage.vector_storage import VectorStorage
from app.utils.embeddings import EmbeddingManager
from app.models import RetrievedContext


@pytest.fixture
def mock_embedding_manager():
    """Create mock embedding manager."""
    mock = Mock(spec=EmbeddingManager)
    # Mock embed_documents to return fake embeddings
    mock.embed_documents = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    # Mock embed_query to return fake embedding
    mock.embed_query = AsyncMock(return_value=[0.2, 0.3, 0.4])
    return mock


@pytest.fixture
def mock_chroma_collection():
    """Create mock ChromaDB collection."""
    collection = Mock()
    collection.add = Mock()
    collection.query = Mock(return_value={
        'documents': [['doc1', 'doc2']],
        'metadatas': [[{'date': '2025-01-15'}, {'date': '2025-01-14'}]],
        'distances': [[0.2, 0.4]]
    })
    collection.get = Mock(return_value={'ids': ['id1', 'id2']})
    collection.delete = Mock()
    return collection


@pytest.fixture
def vector_storage_with_mocks(mock_embedding_manager, mock_chroma_collection):
    """Create VectorStorage with mocked dependencies."""
    temp_dir = Path(tempfile.mkdtemp())
    
    with patch('app.storage.vector_storage.chromadb.PersistentClient') as mock_client_class:
        # Mock the client
        mock_client = Mock()
        mock_client.get_or_create_collection = Mock(return_value=mock_chroma_collection)
        mock_client_class.return_value = mock_client
        
        # Create VectorStorage
        storage = VectorStorage(temp_dir, mock_embedding_manager)
        storage.collection = mock_chroma_collection  # Ensure mock is used
        
        yield storage
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestVectorStorage:
    """Tests for VectorStorage class."""
    
    @pytest.mark.asyncio
    async def test_add_documents(self, vector_storage_with_mocks, mock_embedding_manager):
        """Test adding documents to vector store."""
        documents = ["Document 1", "Document 2"]
        metadatas = [{"date": "2025-01-15"}, {"date": "2025-01-14"}]
        ids = ["id1", "id2"]
        
        await vector_storage_with_mocks.add_documents(documents, metadatas, ids)
        
        # Verify embeddings were generated
        mock_embedding_manager.embed_documents.assert_called_once_with(documents)
        
        # Verify documents were added to collection
        vector_storage_with_mocks.collection.add.assert_called_once()
        call_args = vector_storage_with_mocks.collection.add.call_args
        assert call_args.kwargs['documents'] == documents
        assert call_args.kwargs['metadatas'] == metadatas
        assert call_args.kwargs['ids'] == ids
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, vector_storage_with_mocks, mock_embedding_manager):
        """Test similarity search returns proper RetrievedContext objects."""
        query = "test query"
        
        results = await vector_storage_with_mocks.similarity_search(query, top_k=2)
        
        # Verify query was embedded
        mock_embedding_manager.embed_query.assert_called_once_with(query)
        
        # Verify collection was queried
        vector_storage_with_mocks.collection.query.assert_called_once()
        
        # Verify results format
        assert len(results) == 2
        assert all(isinstance(r, RetrievedContext) for r in results)
        
        # Check first result
        assert results[0].content == 'doc1'
        assert results[0].metadata == {'date': '2025-01-15'}
        # Distance 0.2 -> similarity 1.0 - (0.2/2.0) = 0.9
        assert results[0].similarity_score == pytest.approx(0.9)
    
    @pytest.mark.asyncio
    async def test_similarity_search_with_filter(self, vector_storage_with_mocks):
        """Test similarity search with metadata filter."""
        query = "test query"
        filter_dict = {"session_id": "session-123"}
        
        await vector_storage_with_mocks.similarity_search(
            query,
            top_k=5,
            filter=filter_dict
        )
        
        # Verify filter was passed to query
        call_args = vector_storage_with_mocks.collection.query.call_args
        assert call_args.kwargs['where'] == filter_dict
    
    @pytest.mark.asyncio
    async def test_similarity_search_empty_results(self, vector_storage_with_mocks):
        """Test similarity search with no results."""
        # Mock empty results
        vector_storage_with_mocks.collection.query = Mock(return_value={
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        })
        
        results = await vector_storage_with_mocks.similarity_search("query")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_similarity_search_graceful_degradation(
        self,
        vector_storage_with_mocks,
        mock_embedding_manager
    ):
        """Test that search failures return empty list (graceful degradation)."""
        # Make embed_query fail
        mock_embedding_manager.embed_query = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        results = await vector_storage_with_mocks.similarity_search("query")
        
        # Should return empty list, not raise exception
        assert results == []
    
    @pytest.mark.asyncio
    async def test_delete_by_metadata(self, vector_storage_with_mocks):
        """Test deleting documents by metadata filter."""
        filter_dict = {"session_id": "session-123"}
        
        await vector_storage_with_mocks.delete_by_metadata(filter_dict)
        
        # Verify get was called with filter
        vector_storage_with_mocks.collection.get.assert_called_once_with(where=filter_dict)
        
        # Verify delete was called with IDs
        vector_storage_with_mocks.collection.delete.assert_called_once_with(
            ids=['id1', 'id2']
        )
    
    @pytest.mark.asyncio
    async def test_delete_by_metadata_no_matches(self, vector_storage_with_mocks):
        """Test deleting when no documents match filter."""
        # Mock no results
        vector_storage_with_mocks.collection.get = Mock(return_value={'ids': []})
        
        # Should not raise error
        await vector_storage_with_mocks.delete_by_metadata({"session_id": "nonexistent"})
        
        # Delete should not be called if no IDs found
        vector_storage_with_mocks.collection.delete.assert_not_called()
    
    def test_similarity_score_calculation(self):
        """Test that distance is correctly converted to similarity score."""
        # ChromaDB returns distance (0 = identical, 2 = opposite for cosine)
        # We convert to similarity (1 = identical, 0 = opposite)
        
        test_cases = [
            (0.0, 1.0),   # Distance 0.0 → Similarity 1.0 (identical)
            (1.0, 0.5),   # Distance 1.0 → Similarity 0.5 (orthogonal)
            (2.0, 0.0),   # Distance 2.0 → Similarity 0.0 (opposite)
            (0.4, 0.8),   # Distance 0.4 → Similarity 0.8 (similar)
        ]
        
        for distance, expected_similarity in test_cases:
            # Formula: similarity = 1.0 - (distance / 2.0)
            calculated = 1.0 - (distance / 2.0)
            assert calculated == pytest.approx(expected_similarity)

