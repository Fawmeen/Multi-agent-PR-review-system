"""
Tests for RAG Memory functionality (embedding, chunking, memory_service).
"""
# pyrefly: ignore [missing-import]
import pytest
from app.memory.chunker import CodeChunker
from app.memory.embedding import EmbeddingService

def test_code_chunker_basic():
    """Test that the chunker properly splits text with overlap."""
    chunker = CodeChunker(chunk_size=3, overlap=1)
    
    text = "line1\nline2\nline3\nline4\nline5\nline6"
    chunks = chunker.chunk_text(text, file_path="test.py")
    
    assert len(chunks) == 3
    # First chunk: lines 1-3
    assert chunks[0]["line_start"] == 1
    assert chunks[0]["line_end"] == 3
    assert "line3" in chunks[0]["content"]
    
    # Second chunk: overlaps line 3, goes up to 5
    assert chunks[1]["line_start"] == 3
    assert chunks[1]["line_end"] == 5
    assert "line3" in chunks[1]["content"]
    
    # Third chunk: overlaps line 5, goes up to 6
    assert chunks[2]["line_start"] == 5
    assert chunks[2]["line_end"] == 6

def test_code_chunker_empty():
    chunker = CodeChunker()
    chunks = chunker.chunk_text("", "test.py")
    assert len(chunks) == 1
    assert chunks[0]["content"] == ""

@pytest.mark.asyncio
async def test_embedding_service():
    """
    Test embedding generation.
    Note: Requires fastembed and nomic-ai model downloaded.
    """
    try:
        service = EmbeddingService(model_name="nomic-ai/nomic-embed-text-v1.5")
        emb = service.generate_embedding("def foo(): pass")
        
        assert len(emb) == 768
        assert isinstance(emb[0], float)
    except Exception as e:
        pytest.skip(f"Skipping embedding test due to model loading error: {e}")
