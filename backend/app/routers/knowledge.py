import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from app.chat_assistant import build_assistant_reply
    from app.knowledge_vector_store import KnowledgeVectorStore
    from app.schemas import (
        AIAnalysis,
        ChatRequest,
        ChatResponse,
        KnowledgeRetrievalRequest,
        KnowledgeRetrievalResponse,
        KnowledgeRetrievalResult,
        KnowledgeSource,
    )
except ImportError:  # pragma: no cover - fallback for repo-root imports during tests
    from backend.app.chat_assistant import build_assistant_reply
    from backend.app.knowledge_vector_store import KnowledgeVectorStore
    from backend.app.schemas import (
        AIAnalysis,
        ChatRequest,
        ChatResponse,
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


def _build_search_response(payload: KnowledgeRetrievalRequest, chunks: list[dict[str, Any]]) -> KnowledgeRetrievalResponse:
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

    return _build_search_response(payload, chunks)


@router.post("/chat", response_model=ChatResponse)
def chat_with_knowledge(
    payload: ChatRequest,
    store: Any = Depends(get_knowledge_vector_store),
) -> ChatResponse:
    question = payload.message.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Message must not be blank.")

    try:
        chunks = store.search(question, limit=3)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.exception("Knowledge chat search failed.")
        raise HTTPException(
            status_code=503,
            detail="Chat assistance is temporarily unavailable.",
        ) from error

    retrieval_response = _build_search_response(
        KnowledgeRetrievalRequest(question=question, top_k=3),
        chunks,
    )
    answer = build_assistant_reply(question, [item.model_dump() for item in retrieval_response.results])
    primary = retrieval_response.results[0] if retrieval_response.results else None
    category = primary.category if primary else "General"
    sub_category = primary.sub_category if primary else "Support"
    lowered_question = question.lower()

    if "password" in lowered_question or "reset" in lowered_question or "lock" in lowered_question:
        intent = "automatable_issue"
        priority = "P3"
        urgency = "Medium"
        assignment_group = "Identity Support"
        summary = "Password reset or account unlock support"
    elif "vpn" in lowered_question or "network" in lowered_question or "connect" in lowered_question:
        intent = "incident"
        priority = "P2"
        urgency = "High"
        assignment_group = "Network Support"
        summary = "VPN or network connectivity issue"
    else:
        intent = "knowledge_question"
        priority = "P4"
        urgency = "Low"
        assignment_group = "End User Support"
        summary = "Knowledge-based support request"

    analysis = AIAnalysis(
        intent=intent,
        category=category,
        sub_category=sub_category,
        priority=priority,
        impact="Individual",
        urgency=urgency,
        assignment_group=assignment_group,
        summary=summary,
        suggested_resolution=answer,
        confidence=0.92,
        sources=retrieval_response.sources,
    )

    return ChatResponse(
        response=answer,
        analysis=analysis,
        ticket_created=False,
        ticket_id=None,
        automation_executed=False,
        software_request_id=None,
    )
