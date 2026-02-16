import os
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi_limiter.depends import RateLimiter
from celery.result import AsyncResult
from celery import chain
from app.api.schemas import SearchRequest, SearchResponse, TaskResponse, ChunkRequest, ChunkResponse, ExtractRequest
from app.worker import scrape_task, embed_task
from app.utils.logger import logger
from app.services.chunker import chunker

router: APIRouter = APIRouter(prefix="/v1")

RATE_LIMIT_TIMES = int(os.getenv("RATE_LIMIT_TIMES", "5"))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "60"))

@router.post("/search", response_model=TaskResponse, status_code=202, dependencies=[Depends(RateLimiter(times=RATE_LIMIT_TIMES, seconds=RATE_LIMIT_SECONDS))])
async def search_endpoint(request: SearchRequest) -> TaskResponse:
    try:
        # Chain the tasks: Scrape -> Embed -> Score
        from app.worker import scrape_task, embed_task, score_task
        task_chain = chain(
            scrape_task.s(
                query=request.query,
                region=request.region,
                language=request.language,
                limit=request.limit,
                mode=request.mode
            ),
            embed_task.s(
                region=request.region,
                language=request.language,
                limit=request.limit,
                output_format=request.output_format
            ),
            score_task.s()
        )

        task = task_chain.apply_async()

        return TaskResponse(
            task_id=task.id,
            status="pending"
        )

    except Exception as e:
        logger.error("Search endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str) -> TaskResponse:
    try:
        task_result = AsyncResult(task_id)

        response = TaskResponse(
            task_id=task_id,
            status=task_result.status.lower()
        )

        if task_result.ready():
            if task_result.successful():
                result_data = task_result.get()
                if "error" in result_data:
                    response.status = "failed"
                    response.error = result_data["error"]
                else:
                    response.status = "completed"
                    response.result = SearchResponse(**result_data, cached=False)
            else:
                response.status = "failed"
                response.error = str(task_result.result)

        return response

    except Exception as e:
        logger.error("Task status error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/extract", response_model=TaskResponse, status_code=202)
async def extract_endpoint(request: ExtractRequest) -> TaskResponse:
    """Standalone endpoint for content extraction (Fast Mode)"""
    try:
        task = scrape_task.apply_async(args=[request.url, "us", "en", 1, "scrape"])
        return TaskResponse(task_id=task.id, status="pending")
    except Exception as e:
        logger.error("Extract endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/deep_scrape", response_model=TaskResponse, status_code=202)
async def deep_scrape_endpoint(request: ExtractRequest) -> TaskResponse:
    """Standalone endpoint for deep scraping (Headless Mode)"""
    try:
        # Currently same worker, but mode='scrape' trigger the extraction pipeline
        task = scrape_task.apply_async(args=[request.url, "us", "en", 1, "scrape"])
        return TaskResponse(task_id=task.id, status="pending")
    except Exception as e:
        logger.error("Deep scrape endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/chunk", response_model=ChunkResponse)
async def chunk_endpoint(request: ChunkRequest) -> ChunkResponse:
    """Synchronous utility for text chunking"""
    try:
        chunks = chunker.chunk_text(
            request.text, 
            request.chunk_size or 1000, 
            request.chunk_overlap or 200
        )
        return ChunkResponse(chunks=chunks, count=len(chunks))
    except Exception as e:
        logger.error("Chunk endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="Chunking Failed")
