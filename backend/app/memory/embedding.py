"""
Service for generating embeddings using local fastembed.
"""
from typing import List
# pyrefly: ignore [missing-import]
from fastembed import TextEmbedding

class EmbeddingService:
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        """
        Initialize the embedding service.
        nomic-ai/nomic-embed-text-v1.5 produces 768-dimensional embeddings, which matches our VECTOR(768) in DB.
        """
        # Load model lazily or at initialization
        self.model = TextEmbedding(model_name=model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a 768-dimensional embedding for a given text.
        """
        # embed returns a generator of numpy arrays, we convert to list of floats
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts (batch processing).
        """
        embeddings = list(self.model.embed(texts))
        return [emb.tolist() for emb in embeddings]
