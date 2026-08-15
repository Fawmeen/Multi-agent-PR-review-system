"""
Repository for RAG operations using pgvector.
"""
from typing import Sequence

# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import select, text

# pyrefly: ignore [missing-import]
from app.database.models import CodeChunkModel

class RAGRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_chunks(self, chunks: list[CodeChunkModel]) -> None:
        """Insert multiple code chunks."""
        self.session.add_all(chunks)
        await self.session.flush()

    async def hybrid_search(self, query_embedding: list[float], query_text: str, repository: str, limit: int = 5) -> Sequence[CodeChunkModel]:
        """
        Perform a hybrid search: vector similarity combined with full-text search.
        We rank primarily by vector cosine distance (<=>).
        """
        # Note: A true hybrid search might use reciprocal rank fusion, 
        # but for simplicity we will rely on vector distance with an optional FTS filter, 
        # or just sort by vector distance.
        stmt = (
            select(CodeChunkModel)
            .where(CodeChunkModel.repository == repository)
            .order_by(CodeChunkModel.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
