"""Tests for vector similarity search functionality."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent import AgentService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def agent_service(mock_db):
    """Create AgentService instance with mocked DB."""
    return AgentService(db=mock_db, user_id="test-user-id")


@pytest.mark.asyncio
async def test_vector_search_returns_relevant_results(agent_service, mock_db):
    """Test that vector search returns relevant document chunks."""
    # Mock OpenAI embedding response
    mock_embedding = [0.1] * 1536  # 1536-dimensional embedding

    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = mock_embedding

        # Mock database query result
        mock_result = Mock()
        mock_row = Mock()
        mock_row.id = "chunk-123"
        mock_row.content = "This listing is a coffee shop in downtown."
        mock_row.metadata = {"source": "cim"}
        mock_row.page_number = 1
        mock_row.document_type = "cim"
        mock_row.title = "Coffee Shop CIM"
        mock_row.distance = 0.15

        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        # Execute search
        results = await agent_service.search_listing_knowledge(
            listing_id="listing-123",
            query="Tell me about the coffee shop",
            limit=3
        )

        # Verify results
        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk-123"
        assert results[0]["content"] == "This listing is a coffee shop in downtown."
        assert results[0]["metadata"] == {"source": "cim"}
        assert results[0]["page_number"] == 1
        assert results[0]["document_type"] == "cim"
        assert results[0]["document_title"] == "Coffee Shop CIM"
        assert results[0]["distance"] == 0.15
        assert results[0]["similarity"] == pytest.approx(0.85, rel=1e-2)

        # Verify embedding was created
        mock_openai.create_embedding.assert_called_once_with("Tell me about the coffee shop")

        # Verify database query was executed
        mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_vector_search_handles_empty_embedding(agent_service, mock_db):
    """Test that vector search handles empty embedding gracefully."""
    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = None  # Simulate failure

        results = await agent_service.search_listing_knowledge(
            listing_id="listing-123",
            query="Test query",
            limit=3
        )

        # Should return empty list
        assert results == []

        # Should not execute database query
        mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_vector_search_handles_no_results(agent_service, mock_db):
    """Test that vector search handles case with no matching chunks."""
    mock_embedding = [0.1] * 1536

    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = mock_embedding

        # Mock empty result set
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        results = await agent_service.search_listing_knowledge(
            listing_id="listing-123",
            query="Non-existent information",
            limit=3
        )

        # Should return empty list
        assert results == []


@pytest.mark.asyncio
async def test_vector_search_respects_limit(agent_service, mock_db):
    """Test that vector search respects the limit parameter."""
    mock_embedding = [0.1] * 1536

    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = mock_embedding

        # Mock multiple results
        mock_result = Mock()
        mock_rows = []
        for i in range(5):
            mock_row = Mock()
            mock_row.id = f"chunk-{i}"
            mock_row.content = f"Content {i}"
            mock_row.metadata = {}
            mock_row.page_number = i + 1
            mock_row.document_type = "cim"
            mock_row.title = "Document"
            mock_row.distance = 0.1 * (i + 1)
            mock_rows.append(mock_row)

        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result

        # Execute with custom limit
        results = await agent_service.search_listing_knowledge(
            listing_id="listing-123",
            query="Test query",
            limit=5
        )

        # Verify all results returned
        assert len(results) == 5

        # Verify database query used correct limit
        call_args = mock_db.execute.call_args
        assert call_args[0][1]["limit"] == 5


@pytest.mark.asyncio
async def test_vector_search_formats_embedding_correctly(agent_service, mock_db):
    """Test that embedding is formatted correctly for pgvector."""
    mock_embedding = [0.1, 0.2, 0.3, 0.4]

    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = mock_embedding

        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await agent_service.search_listing_knowledge(
            listing_id="listing-123",
            query="Test",
            limit=3
        )

        # Verify embedding was formatted as pgvector string
        call_args = mock_db.execute.call_args
        embedding_param = call_args[0][1]["query_embedding"]
        assert embedding_param == "[0.1,0.2,0.3,0.4]"


@pytest.mark.asyncio
async def test_vector_search_uses_correct_listing_id(agent_service, mock_db):
    """Test that vector search filters by listing_id correctly."""
    mock_embedding = [0.1] * 1536

    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = mock_embedding

        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        listing_id = "listing-abc-123"
        await agent_service.search_listing_knowledge(
            listing_id=listing_id,
            query="Test",
            limit=3
        )

        # Verify listing_id parameter
        call_args = mock_db.execute.call_args
        assert call_args[0][1]["listing_id"] == listing_id


@pytest.mark.asyncio
async def test_vector_search_calculates_similarity_correctly(agent_service, mock_db):
    """Test that similarity score is calculated correctly from distance."""
    mock_embedding = [0.1] * 1536

    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = mock_embedding

        mock_result = Mock()
        mock_row = Mock()
        mock_row.id = "chunk-123"
        mock_row.content = "Content"
        mock_row.metadata = {}
        mock_row.page_number = 1
        mock_row.document_type = "cim"
        mock_row.title = "Doc"
        mock_row.distance = 0.25  # Distance of 0.25

        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        results = await agent_service.search_listing_knowledge(
            listing_id="listing-123",
            query="Test",
            limit=3
        )

        # Similarity should be 1 - distance = 0.75
        assert results[0]["similarity"] == pytest.approx(0.75, rel=1e-2)


@pytest.mark.asyncio
async def test_vector_search_handles_null_metadata(agent_service, mock_db):
    """Test that vector search handles null metadata gracefully."""
    mock_embedding = [0.1] * 1536

    with patch('app.services.agent.OpenAIService') as mock_openai_class:
        mock_openai = mock_openai_class.return_value
        mock_openai.create_embedding.return_value = mock_embedding

        mock_result = Mock()
        mock_row = Mock()
        mock_row.id = "chunk-123"
        mock_row.content = "Content"
        mock_row.metadata = None  # Null metadata
        mock_row.page_number = 1
        mock_row.document_type = "cim"
        mock_row.title = "Doc"
        mock_row.distance = 0.1

        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        results = await agent_service.search_listing_knowledge(
            listing_id="listing-123",
            query="Test",
            limit=3
        )

        # Should default to empty dict
        assert results[0]["metadata"] == {}
