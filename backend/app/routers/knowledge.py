import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from app.knowledge_vector_store import KnowledgeVectorStore
    from app.schemas import (
        KnowledgeRetrievalRequest,
        KnowledgeRetrievalResponse,
        KnowledgeRetrievalResult,
        KnowledgeSource,
    )
except ImportError:  # pragma: no cover - fallback for repo-root imports during tests
    from backend.app.knowledge_vector_store import KnowledgeVectorStore
    from backend.app.schemas import (
        KnowledgeRetrievalRequest,
        KnowledgeRetrievalResponse,
        KnowledgeRetrievalResult,
        KnowledgeSource,
    )

logger = logging.getLogger(__name__)
router = APIRouter()


def get_knowledge_vector_store(request: Request) -> KnowledgeVectorStore:
    store = getattr(request.app.state, "knowledge_vector_store", None)
    if store is None:
        try:
            store = KnowledgeVectorStore()
        except Exception as error:
            logger.exception("Could not initialize the knowledge vector store.")
            raise HTTPException(
                status_code=503,
                detail="Knowledge retrieval is unavailable because the vector store could not be initialized.",
            ) from error
        request.app.state.knowledge_vector_store = store
    return store


@router.post("/search", response_model=KnowledgeRetrievalResponse)
def search_knowledge(
    payload: KnowledgeRetrievalRequest,
    store: Any = Depends(get_knowledge_vector_store),
) -> KnowledgeRetrievalResponse:
    try:
        chunks = store.search(
            payload.question,
            category=payload.category,
            topic=payload.topic,
            limit=payload.top_k,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.exception("Knowledge vector search failed.")
        raise HTTPException(
            status_code=503,
            detail="Knowledge retrieval is temporarily unavailable.",
        ) from error

    results = []
    sources_by_article: dict[str, KnowledgeSource] = {}
    for rank, chunk in enumerate(chunks, start=1):
        distance = float(chunk["distance"])
        score = max(-1.0, min(1.0, 1.0 - distance))
        result = KnowledgeRetrievalResult(
            rank=rank,
            chunk_id=str(chunk["chunk_id"]),
            article_id=str(chunk["article_id"]),
            title=str(chunk["title"]),
            category=str(chunk["category"]),
            sub_category=str(chunk["sub_category"]),
            source_file=str(chunk["source_file"]),
            text=str(chunk["text"]),
            score=score,
            distance=distance,
        )
        results.append(result)

        existing_source = sources_by_article.get(result.article_id)
        if existing_source is None or score > (existing_source.score or -1.0):
            sources_by_article[result.article_id] = KnowledgeSource(
                article_id=result.article_id,
                title=result.title,
                category=result.category,
                sub_category=result.sub_category,
                source_file=result.source_file,
                chunk_id=result.chunk_id,
                score=score,
            )

    return KnowledgeRetrievalResponse(
        question=payload.question,
        results=results,
        sources=list(sources_by_article.values()),
    )
