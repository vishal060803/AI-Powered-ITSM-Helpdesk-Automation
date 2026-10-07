import logging
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from app.chat_assistant import (
        build_assistant_reply,
        build_grounded_answer,
        build_incident_payload,
        classify_request,
    )
    from app.knowledge_vector_store import KnowledgeVectorStore
    from app.routers.servicenow import create_service_now_incident_record
    from app.schemas import (
        AIAnalysis,
        ChatRequest,
        ChatResponse,
        IncidentCreateRequest,
        IncidentCreateResponse,
        KnowledgeRetrievalRequest,
        KnowledgeRetrievalResponse,
        KnowledgeRetrievalResult,
        KnowledgeSource,
        Ticket,
    )
except ImportError:  # pragma: no cover - fallback for repo-root imports during tests
    from backend.app.chat_assistant import (
        build_assistant_reply,
        build_grounded_answer,
        build_incident_payload,
        classify_request,
    )
    from backend.app.knowledge_vector_store import KnowledgeVectorStore
    from backend.app.routers.servicenow import create_service_now_incident_record
    from backend.app.schemas import (
        AIAnalysis,
        ChatRequest,
        ChatResponse,
        IncidentCreateRequest,
        IncidentCreateResponse,
        KnowledgeRetrievalRequest,
        KnowledgeRetrievalResponse,
        KnowledgeRetrievalResult,
        KnowledgeSource,
        Ticket,
    )

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_ticket_store(request: Request) -> dict[str, Any]:
    store = getattr(request.app.state, "ticket_store", None)
    if store is None:
        store = {}
        request.app.state.ticket_store = store
    return store


def _load_tickets(request: Request) -> list[dict[str, Any]]:
    tickets_by_id = dict(_resolve_ticket_store(request))
    tickets_collection = getattr(request.app.state, "mongo_collections", {}).get("tickets")
    if tickets_collection is not None:
        try:
            for ticket in tickets_collection.find({}, {"_id": False}):
                ticket_id = ticket.get("ticket_id")
                if ticket_id:
                    tickets_by_id.setdefault(ticket_id, ticket)
        except Exception as error:
            logger.exception("Could not load tickets from MongoDB; returning in-memory tickets.")
            if not tickets_by_id:
                raise HTTPException(
                    status_code=503,
                    detail="Ticket records are temporarily unavailable.",
                ) from error

    return sorted(
        tickets_by_id.values(),
        key=lambda ticket: str(ticket.get("created_at", "")),
        reverse=True,
    )


def _is_resolved_ticket(ticket: dict[str, Any]) -> bool:
    return str(ticket.get("status", "")).strip().lower() in {
        "resolved",
        "auto-resolved",
        "closed",
    }


def _generate_ticket_sequence(request: Request) -> str:
    counter = getattr(request.app.state, "ticket_counter", 0) + 1
    request.app.state.ticket_counter = counter
    return f"INC-{counter:04d}"


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

    grounded = build_grounded_answer(payload.question, [result.model_dump() for result in results])
    return KnowledgeRetrievalResponse(
        question=payload.question,
        results=results,
        sources=list(sources_by_article.values()),
        answer=grounded["answer"],
        confidence=grounded["confidence"],
        is_supported=grounded["is_supported"],
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
    analysis = classify_request(
        question,
        [item.model_dump() for item in retrieval_response.results],
        employee_id=payload.employee_id,
        context=payload.context,
    )
    if not retrieval_response.is_supported and analysis.category not in {"Security", "Automation"}:
        analysis.intent = "knowledge_question"
        analysis.category = "General"
        analysis.sub_category = "Unknown"
        analysis.priority = "P3"
        analysis.urgency = "Medium"
        analysis.assignment_group = "End User Support"
        analysis.summary = "Unsupported or low-confidence knowledge request"

    analysis.suggested_resolution = answer
    analysis.sources = retrieval_response.sources
    analysis.confidence = retrieval_response.confidence if retrieval_response.confidence is not None else analysis.confidence

    return ChatResponse(
        response=answer,
        analysis=analysis,
        ticket_created=False,
        ticket_id=None,
        automation_executed=False,
        software_request_id=None,
    )


@router.post("/incidents", response_model=IncidentCreateResponse)
def create_incident(
    payload: IncidentCreateRequest,
    request: Request,
) -> IncidentCreateResponse:
    description = (payload.description or "").strip()
    if not description:
        raise HTTPException(status_code=422, detail="Incident description must not be blank.")

    analysis = payload.analysis
    incident_payload = build_incident_payload(analysis, description)
    ticket_id = _generate_ticket_sequence(request)
    servicenow_response = create_service_now_incident_record(incident_payload, request)
    service_now_ref = str(servicenow_response["service_now_ref"])

    ticket = Ticket(
        ticket_id=ticket_id,
        employee_id=payload.employee_id,
        title=analysis.summary or description[:80],
        description=description,
        intent=analysis.intent,
        category=analysis.category,
        sub_category=analysis.sub_category,
        priority=analysis.priority,
        impact=analysis.impact,
        urgency=analysis.urgency,
        assignment_group=analysis.assignment_group,
        confidence=analysis.confidence,
        ai_analysis=analysis,
        service_now_ref=service_now_ref,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    ticket_store = _resolve_ticket_store(request)
    ticket_store[ticket_id] = ticket.model_dump(mode="json")

    tickets_collection = getattr(request.app.state, "mongo_collections", {}).get("tickets")
    if tickets_collection is not None:
        try:
            tickets_collection.insert_one(ticket.model_dump(mode="json"))
        except Exception:
            logger.exception("Falling back to in-memory ticket storage because MongoDB persistence failed.")

    return IncidentCreateResponse(
        ticket_id=ticket_id,
        service_now_ref=service_now_ref,
        status="open",
        message=(
            f"Incident {ticket_id} created and routed to {analysis.assignment_group}. "
            f"ServiceNow reference: {service_now_ref}."
        ),
    )


@router.get("/incidents/{ticket_id}")
def get_incident(ticket_id: str, request: Request) -> dict[str, Any]:
    ticket_store = _resolve_ticket_store(request)
    ticket = ticket_store.get(ticket_id)
    if ticket is None:
        tickets_collection = getattr(request.app.state, "mongo_collections", {}).get("tickets")
        if tickets_collection is not None:
            try:
                ticket = tickets_collection.find_one(
                    {"ticket_id": ticket_id},
                    {"_id": False},
                )
            except Exception as error:
                logger.exception("Could not load ticket %s from MongoDB.", ticket_id)
                raise HTTPException(
                    status_code=503,
                    detail="Ticket details are temporarily unavailable.",
                ) from error
    if ticket is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return ticket


@router.get("/incidents", response_model=list[Ticket])
def list_incidents(
    request: Request,
    status: Literal["open", "resolved"] | None = None,
) -> list[dict[str, Any]]:
    tickets = _load_tickets(request)
    if status == "open":
        return [ticket for ticket in tickets if not _is_resolved_ticket(ticket)]
    if status == "resolved":
        return [ticket for ticket in tickets if _is_resolved_ticket(ticket)]
    return tickets
