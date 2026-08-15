"""
Memory Service for RAG orchestration.
"""
from typing import List
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from app.memory.embedding import EmbeddingService
from app.memory.chunker import CodeChunker
from app.database.rag_repository import RAGRepository
from app.database.models import CodeChunkModel

class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = EmbeddingService()
        self.chunker = CodeChunker(chunk_size=100, overlap=20)
        self.repo = RAGRepository(session)

    async def ingest_file(self, content: str, file_path: str, repository: str) -> None:
        """
        Chunks a file, generates embeddings, and saves to database.
        """
        chunks_data = self.chunker.chunk_text(content, file_path=file_path)
        if not chunks_data:
            return
            
        # Extract texts for batch embedding
        texts = [chunk["content"] for chunk in chunks_data]
        
        # This is a blocking CPU-bound call, ideally it should run in a thread pool (run_in_executor)
        # For simplicity, we just call it directly here.
        embeddings = self.embedding_service.generate_embeddings(texts)
        
        # Build models
        code_chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk_model = CodeChunkModel(
                repository=repository,
                file_path=chunk_data["file_path"],
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                embedding=embeddings[i],
                extra_data={
                    "line_start": chunk_data["line_start"],
                    "line_end": chunk_data["line_end"]
                }
            )
            code_chunks.append(chunk_model)
            
        await self.repo.insert_chunks(code_chunks)

    async def retrieve_context(self, query: str, repository: str, limit: int = 5) -> str:
        """
        Retrieves relevant context for a query and formats it as a string.
        """
        query_embedding = self.embedding_service.generate_embedding(query)
        
        results = await self.repo.hybrid_search(
            query_embedding=query_embedding,
            query_text=query,
            repository=repository,
            limit=limit
        )
        
        if not results:
            return "No relevant context found."
            
        context_parts = []
        for chunk in results:
            context_parts.append(
                f"File: {chunk.file_path} (Lines {chunk.extra_data.get('line_start')}-{chunk.extra_data.get('line_end')})\n"
                f"```\n{chunk.content}\n```"
            )
            
        return "\n\n---\n\n".join(context_parts)
