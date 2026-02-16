from typing import List

class ChunkerService:
    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Simple overlapping character-based chunker.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - chunk_overlap)
            
        return chunks

chunker = ChunkerService()
