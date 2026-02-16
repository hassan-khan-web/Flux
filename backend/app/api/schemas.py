from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str
    region: Optional[str] = "us"
    language: Optional[str] = "en"
    output_format: Optional[str] = "markdown"
    mode: Optional[str] = "search"
    limit: Optional[int] = 10

class OrganicResult(BaseModel):
    title: str
    url: str
    snippet: str
    score: Optional[float] = 0.0
    full_content: Optional[str] = None
    embedding: Optional[List[float]] = None
    author: Optional[str] = None
    date: Optional[str] = None
    is_polished: bool = False

class SearchResponse(BaseModel):
    query: str
    ai_overview: Optional[str] = None
    organic_results: List[OrganicResult] = []
    formatted_output: str
    token_estimate: int
    deduplicated_count: int = 0
    provider_health: Dict[str, Any] = {}
    relevance_score: Optional[float] = 0.0
    relevance_reasoning: Optional[str] = None
    credibility_score: Optional[float] = 0.0
    credibility_reasoning: Optional[str] = None
    cached: bool

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[SearchResponse] = None
    error: Optional[str] = None

class ChunkRequest(BaseModel):
    text: str
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class ChunkResponse(BaseModel):
    chunks: List[str]
    count: int

class ExtractRequest(BaseModel):
    url: str
    mode: Optional[str] = "extract" # "extract" or "scrape" (deep)
