"""
Code chunking utilities for RAG ingestion.
"""
from typing import List, Dict, Any

class CodeChunker:
    """
    A simple line-based sliding window chunker.
    """
    def __init__(self, chunk_size: int = 100, overlap: int = 20):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, file_path: str = "") -> List[Dict[str, Any]]:
        """
        Splits text into overlapping chunks based on lines.
        Returns a list of dicts with chunk metadata.
        """
        lines = text.split('\n')
        chunks = []
        
        if not lines:
            return chunks
            
        start_line = 0
        chunk_index = 0
        
        while start_line < len(lines):
            end_line = min(start_line + self.chunk_size, len(lines))
            
            chunk_content = '\n'.join(lines[start_line:end_line])
            
            chunks.append({
                "chunk_index": chunk_index,
                "file_path": file_path,
                "content": chunk_content,
                "line_start": start_line + 1,  # 1-indexed
                "line_end": end_line
            })
            
            chunk_index += 1
            # Move forward by chunk_size - overlap
            start_line += (self.chunk_size - self.overlap)
            
            # Prevent infinite loop if overlap >= chunk_size
            if self.chunk_size <= self.overlap:
                break
                
        return chunks
