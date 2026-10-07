import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_servicenow_store(request: Request) -> dict[str, Any]:
    store = getattr(request.app.state, "servicenow_incidents", None)
    if store is None:
        store = {}
        request.app.state.servicenow_incidents = store
    return store


def create_service_now_incident_record(
    payload: dict[str, Any],
    request: Request,
) -> dict[str, Any]:
    if not payload:
        raise HTTPException(status_code=422, detail="Incident payload is required.")

    summary = payload.get("short_description") or payload.get("summary") or "New incident"
    description = payload.get("description") or "No description provided."
    category = payload.get("category") or "General"
    sub_category = payload.get("sub_category") or "Support"
    priority = payload.get("priority") or "P3"
    impact = payload.get("impact") or "Individual"
    urgency = payload.get("urgency") or "Medium"
    assignment_group = payload.get("assignment_group") or "End User Support"
    confidence = float(payload.get("confidence", 0.8) or 0.8)

    counter = getattr(request.app.state, "servicenow_counter", 0) + 1
    request.app.state.servicenow_counter = counter
    reference = f"INC{(counter + 1000):07d}"
    incident = {
        "sys_id": reference,
        "number": reference,
        "short_description": summary,
        "description": description,
        "category": category,
        "sub_category": sub_category,
        "priority": priority,
        "impact": impact,
        "urgency": urgency,
        "assignment_group": assignment_group,
        "confidence": confidence,
        "state": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    store = _get_servicenow_store(request)
    store[reference] = incident
    return {"ok": True, "incident": incident, "service_now_ref": reference}


@router.post("/incidents")
def create_service_now_incident(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    return create_service_now_incident_record(payload, request)


@router.get("/incidents/{incident_id}")
def get_service_now_incident(incident_id: str, request: Request) -> dict[str, Any]:
    store = _get_servicenow_store(request)
    incident = store.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="ServiceNow incident not found.")
    return incident


@router.patch("/incidents/{incident_id}")
def update_service_now_incident(incident_id: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
    store = _get_servicenow_store(request)
    incident = store.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="ServiceNow incident not found.")

    incident.update({key: value for key, value in payload.items() if value is not None})
    return {"ok": True, "incident": incident}
