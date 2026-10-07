import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request

try:
    from app.automation_cases import SAFE_AUTOMATION_CASES, assess_automation_safety, list_safe_automation_cases
    from app.schemas import AutomationAction, AutomationExecutionRequest, AutomationExecutionResponse
except ImportError:  # pragma: no cover - fallback for repo-root imports during tests
    from backend.app.automation_cases import SAFE_AUTOMATION_CASES, assess_automation_safety, list_safe_automation_cases
    from backend.app.schemas import AutomationAction, AutomationExecutionRequest, AutomationExecutionResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_automation_store(request: Request) -> dict[str, Any]:
    store = getattr(request.app.state, "automation_store", None)
    if store is None:
        store = {}
        request.app.state.automation_store = store
    return store


def _resolve_ticket_store(request: Request) -> dict[str, Any]:
    store = getattr(request.app.state, "ticket_store", None)
    if store is None:
        store = {}
        request.app.state.ticket_store = store
    return store


def _resolve_audit_store(request: Request) -> list[dict[str, Any]]:
    store = getattr(request.app.state, "audit_store", None)
    if store is None:
        store = []
        request.app.state.audit_store = store
    return store


def _build_execution_steps(automation_name: str) -> list[str]:
    if automation_name == "password_expired":
        return [
            "Validate employee identity challenge status.",
            "Trigger approved password reset workflow.",
            "Confirm the account can authenticate with the new password.",
        ]
    if automation_name == "account_lockout":
        return [
            "Validate lockout policy and employee identity.",
            "Run approved account unlock automation.",
            "Confirm the account lock state is cleared.",
        ]
    if automation_name == "vpn_status_check":
        return [
            "Collect VPN gateway reachability and auth status.",
            "Run corporate VPN diagnostic checks.",
            "Validate tunnel status and endpoint policy compliance.",
        ]
    if automation_name == "service_restart":
        return [
            "Check service eligibility for automated restart.",
            "Restart approved endpoint service.",
            "Verify service state returns to healthy.",
        ]
    if automation_name == "cache_clearing":
        return [
            "Check supported cache path and running process state.",
            "Clear approved cache directories only.",
            "Validate application performance health signals.",
        ]
    if automation_name == "application_restart":
        return [
            "Check application process ownership and eligibility.",
            "Restart approved application process.",
            "Confirm application responds after restart.",
        ]
    return [
        "Validate automation preconditions.",
        "Execute approved automation workflow.",
        "Run post-execution validation checks.",
    ]


def _create_action_id(request: Request) -> str:
    counter = getattr(request.app.state, "automation_counter", 0) + 1
    request.app.state.automation_counter = counter
    return f"AUTO-{counter:04d}"


def _load_ticket(ticket_id: str, request: Request) -> dict[str, Any] | None:
    ticket = _resolve_ticket_store(request).get(ticket_id)
    if ticket is not None:
        return ticket

    tickets_collection = getattr(request.app.state, "mongo_collections", {}).get("tickets")
    if tickets_collection is not None:
        try:
            return tickets_collection.find_one({"ticket_id": ticket_id}, {"_id": False})
        except Exception:
            logger.exception("Could not load ticket %s for automation execution.", ticket_id)
    return None


def _build_audit_events(
    action_id: str,
    ticket_id: str,
    automation_name: str,
    steps: list[str],
    status: str,
    result_message: str,
    validation_result: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    events.append(
        {
            "action_id": action_id,
            "ticket_id": ticket_id,
            "automation_name": automation_name,
            "event_type": "action_started",
            "event_status": "running",
            "step_index": 0,
            "step": "Automation execution started.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result_message": "Automation execution initiated.",
            "validation_result": None,
        }
    )

    for index, step in enumerate(steps, start=1):
        events.append(
            {
                "action_id": action_id,
                "ticket_id": ticket_id,
                "automation_name": automation_name,
                "event_type": "step_executed",
                "event_status": "running",
                "step_index": index,
                "step": step,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result_message": f"Step {index} executed.",
                "validation_result": None,
            }
        )

    events.append(
        {
            "action_id": action_id,
            "ticket_id": ticket_id,
            "automation_name": automation_name,
            "event_type": "action_completed",
            "event_status": status,
            "step_index": len(steps) + 1,
            "step": "Automation execution completed.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result_message": result_message,
            "validation_result": validation_result,
        }
    )
    return events


def _persist_audit_events(events: list[dict[str, Any]], request: Request) -> None:
    audit_store = _resolve_audit_store(request)
    stored_events = [dict(event) for event in events]
    audit_store.extend(stored_events)

    audit_collection = getattr(request.app.state, "mongo_collections", {}).get("audit")
    if audit_collection is not None:
        try:
            mongo_events = [dict(event) for event in events]
            audit_collection.insert_many(mongo_events)
        except Exception:
            logger.exception("Could not persist automation audit events.")


def execute_automation(automation_name: str, payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    if automation_name not in SAFE_AUTOMATION_CASES:
        raise HTTPException(status_code=422, detail="Unsupported automation task.")

    ticket = _load_ticket(payload.ticket_id, request)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found for automation execution.")

    safety = assess_automation_safety(str(ticket.get("description") or ""))
    if safety["should_block"] or not safety["is_safe"]:
        validation_result = "Blocked: request failed automation safety checks."
        status = "validation_failed"
    else:
        validation_result = "Validation passed: post-execution checks succeeded."
        status = "success"

    action = AutomationAction(
        action_id=_create_action_id(request),
        ticket_id=payload.ticket_id,
        automation_name=automation_name,
        status=status,
        steps=_build_execution_steps(automation_name),
        result_message=(
            f"Automation {automation_name} completed with status {status}."
            if status == "success"
            else f"Automation {automation_name} was blocked by safety validation."
        ),
        validation_result=validation_result,
        created_at=datetime.now(timezone.utc),
    )

    audit_events = _build_audit_events(
        action_id=action.action_id,
        ticket_id=action.ticket_id,
        automation_name=automation_name,
        steps=action.steps,
        status=status,
        result_message=action.result_message,
        validation_result=validation_result,
    )
    _persist_audit_events(audit_events, request)

    automation_store = _resolve_automation_store(request)
    automation_store[action.action_id] = action.model_dump(mode="json")

    if status == "success":
        ticket["status"] = "auto-resolved"
        ticket["automation_outcome"] = "resolved"
    else:
        ticket["status"] = "escalated"
        ticket["automation_outcome"] = "escalated"

    ticket["last_automation_action_id"] = action.action_id
    ticket["last_automation_name"] = action.automation_name
    ticket["last_automation_status"] = action.status
    ticket["last_automation_steps"] = list(action.steps)
    ticket["last_automation_validation_result"] = action.validation_result
    ticket["updated_at"] = datetime.now(timezone.utc).isoformat()

    tickets_collection = getattr(request.app.state, "mongo_collections", {}).get("tickets")
    if tickets_collection is not None:
        try:
            tickets_collection.update_one(
                {"ticket_id": payload.ticket_id},
                {
                    "$set": {
                        "status": ticket["status"],
                        "automation_outcome": ticket["automation_outcome"],
                        "last_automation_action_id": ticket["last_automation_action_id"],
                        "last_automation_name": ticket["last_automation_name"],
                        "last_automation_status": ticket["last_automation_status"],
                        "last_automation_steps": ticket["last_automation_steps"],
                        "last_automation_validation_result": ticket["last_automation_validation_result"],
                        "updated_at": ticket["updated_at"],
                    }
                },
            )
        except Exception:
            logger.exception("Could not update ticket %s after automation execution.", payload.ticket_id)

    return AutomationExecutionResponse(
        automation_id=action.action_id,
        ticket_id=action.ticket_id,
        automation_name=automation_name,
        status=action.status,
        steps=action.steps,
        result_message=action.result_message,
        validation_result=action.validation_result,
    )


@router.get("/cases")
def list_automation_cases() -> dict[str, Any]:
    return {"cases": list_safe_automation_cases()}


@router.post("/execute", response_model=AutomationExecutionResponse)
def execute_automation_generic(payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    return execute_automation(payload.automation_name, payload, request)


@router.post("/password-expired", response_model=AutomationExecutionResponse)
def execute_password_expired(payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    return execute_automation("password_expired", payload, request)


@router.post("/account-lockout", response_model=AutomationExecutionResponse)
def execute_account_lockout(payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    return execute_automation("account_lockout", payload, request)


@router.post("/vpn-status-check", response_model=AutomationExecutionResponse)
def execute_vpn_status_check(payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    return execute_automation("vpn_status_check", payload, request)


@router.post("/service-restart", response_model=AutomationExecutionResponse)
def execute_service_restart(payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    return execute_automation("service_restart", payload, request)


@router.post("/cache-clearing", response_model=AutomationExecutionResponse)
def execute_cache_clearing(payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    return execute_automation("cache_clearing", payload, request)


@router.post("/application-restart", response_model=AutomationExecutionResponse)
def execute_application_restart(payload: AutomationExecutionRequest, request: Request) -> AutomationExecutionResponse:
    return execute_automation("application_restart", payload, request)


@router.get("/actions/{automation_id}")
def get_automation_action(automation_id: str, request: Request) -> dict[str, Any]:
    action = _resolve_automation_store(request).get(automation_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Automation action not found.")
    return action


@router.get("/actions/{automation_id}/audit")
def get_automation_audit_events(automation_id: str, request: Request) -> dict[str, Any]:
    events = [
        item
        for item in _resolve_audit_store(request)
        if str(item.get("action_id")) == automation_id
    ]
    if not events:
        raise HTTPException(status_code=404, detail="Automation audit events not found.")
    return {"action_id": automation_id, "events": events}
