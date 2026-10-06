from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class KnowledgeSource(BaseModel):
    article_id: str
    title: str
    category: str
    sub_category: str
    source_file: str
    chunk_id: Optional[str] = None
    score: Optional[float] = None


class AIAnalysis(BaseModel):
    intent: Literal["knowledge_question", "incident", "service_request", "automatable_issue"]
    category: str
    sub_category: str
    priority: Literal["P1", "P2", "P3", "P4"]
    impact: str
    urgency: str
    assignment_group: str
    summary: str
    suggested_resolution: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: list[KnowledgeSource] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Ticket(BaseModel):
    ticket_id: str
    employee_id: str
    title: str
    description: str
    intent: str
    category: str
    sub_category: str
    priority: str
    impact: str
    urgency: str
    assignment_group: str
    status: str = "open"
    confidence: float = Field(..., ge=0.0, le=1.0)
    ai_analysis: AIAnalysis
    service_now_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeArticle(BaseModel):
    article_id: str
    title: str
    category: str
    sub_category: str
    content: str
    source_file: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AutomationAction(BaseModel):
    action_id: str
    ticket_id: str
    automation_name: str
    status: Literal["queued", "running", "success", "failed", "validation_failed"]
    steps: list[str] = Field(default_factory=list)
    result_message: str
    validation_result: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SoftwareRequest(BaseModel):
    request_id: str
    employee_id: str
    software_name: str
    status: Literal["requested", "provisioning", "completed", "failed"]
    service_now_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    employee_id: str
    message: str
    context: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    analysis: AIAnalysis
    ticket_created: bool = False
    ticket_id: Optional[str] = None
    automation_executed: bool = False
    software_request_id: Optional[str] = None


class IncidentCreateRequest(BaseModel):
    employee_id: str
    description: str
    analysis: AIAnalysis


class IncidentCreateResponse(BaseModel):
    ticket_id: str
    service_now_ref: str
    status: str
    message: str


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=10)


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSource]
    answer: str
    confidence: float


class KnowledgeRetrievalRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    category: Optional[str] = None
    topic: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must not be blank.")
        return value


class KnowledgeRetrievalResult(BaseModel):
    rank: int = Field(ge=1)
    chunk_id: str
    article_id: str
    title: str
    category: str
    sub_category: str
    source_file: str
    text: str
    score: float = Field(ge=-1.0, le=1.0)
    distance: float


class KnowledgeRetrievalResponse(BaseModel):
    question: str
    results: list[KnowledgeRetrievalResult]
    sources: list[KnowledgeSource]


class AutomationExecutionRequest(BaseModel):
    ticket_id: str
    automation_name: str
    employee_id: str


class AutomationExecutionResponse(BaseModel):
    automation_id: str
    ticket_id: str
    status: str
    result_message: str
    validation_result: Optional[str] = None


DEMO_SCENARIOS = {
    "vpn_incident": {
        "input": "I cannot connect to VPN since this morning. Authentication keeps failing.",
        "output": {
            "intent": "incident",
            "category": "Network",
            "sub_category": "VPN",
            "priority": "P2",
            "impact": "Individual",
            "urgency": "High",
            "assignment_group": "Network Support",
            "summary": "VPN authentication failure",
            "suggested_resolution": "VPN troubleshooting"
        },
    },
    "password_self_heal": {
        "input": "My password has expired.",
        "output": {
            "intent": "automatable_issue",
            "category": "Identity",
            "sub_category": "Password Reset",
            "priority": "P3",
            "impact": "Individual",
            "urgency": "Medium",
            "assignment_group": "Identity Support",
            "summary": "Password expired",
            "suggested_resolution": "Password reset and unlock workflow"
        },
    },
    "outlook_rag": {
        "input": "How do I troubleshoot Outlook synchronization?",
        "output": {
            "intent": "knowledge_question",
            "category": "Email",
            "sub_category": "Outlook",
            "priority": "P4",
            "impact": "Individual",
            "urgency": "Low",
            "assignment_group": "End User Support",
            "summary": "Outlook sync troubleshooting",
            "suggested_resolution": "Follow approved Outlook troubleshooting guidance"
        },
    },
    "software_request": {
        "input": "I need Visual Studio Code installed on my laptop.",
        "output": {
            "intent": "service_request",
            "category": "Software",
            "sub_category": "Provisioning",
            "priority": "P3",
            "impact": "Individual",
            "urgency": "Medium",
            "assignment_group": "Software Support",
            "summary": "Visual Studio Code installation request",
            "suggested_resolution": "Create software request and provision through catalog"
        },
    },
    "unknown_question": {
        "input": "How do I hack into the secure file server?",
        "output": {
            "intent": "knowledge_question",
            "category": "Security",
            "sub_category": "Unknown",
            "priority": "P2",
            "impact": "High",
            "urgency": "High",
            "assignment_group": "Security Operations",
            "summary": "Unsupported security question",
            "suggested_resolution": "Escalate to security team; do not provide unsupported guidance"
        },
    },
}
