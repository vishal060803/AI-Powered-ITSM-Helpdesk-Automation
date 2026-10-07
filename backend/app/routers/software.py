from typing import Any

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

try:
    from app.schemas import (
        SoftwareCatalogResponse,
        SoftwareRequest,
        SoftwareRequestCreateRequest,
        SoftwareRequestCreateResponse,
        SoftwareRequestStatusUpdateRequest,
    )
    from app.software_catalog import (
        SOFTWARE_REQUEST_STATUS_LIFECYCLE,
        find_catalog_item,
        get_software_catalog_response,
    )
except ImportError:  # pragma: no cover - fallback for repo-root imports during tests
    from backend.app.schemas import (
        SoftwareCatalogResponse,
        SoftwareRequest,
        SoftwareRequestCreateRequest,
        SoftwareRequestCreateResponse,
        SoftwareRequestStatusUpdateRequest,
    )
    from backend.app.software_catalog import (
        SOFTWARE_REQUEST_STATUS_LIFECYCLE,
        find_catalog_item,
        get_software_catalog_response,
    )


router = APIRouter()


def _resolve_request_store(request: Request) -> dict[str, Any]:
    store = getattr(request.app.state, "software_request_store", None)
    if store is None:
        store = {}
        request.app.state.software_request_store = store
    return store


def _generate_request_ids(request: Request) -> tuple[str, str]:
    counter = getattr(request.app.state, "software_request_counter", 0) + 1
    request.app.state.software_request_counter = counter
    request_id = f"REQ-{counter:06d}"
    service_now_ref = f"RITM{counter + 1000000:07d}"
    return request_id, service_now_ref


def _can_transition_status(current_status: str, target_status: str) -> bool:
    current = str(current_status or "").strip().lower()
    target = str(target_status or "").strip().lower()
    if current == target:
        return True

    lifecycle = list(SOFTWARE_REQUEST_STATUS_LIFECYCLE)
    if current not in lifecycle or target not in lifecycle:
        return False
    return lifecycle.index(target) >= lifecycle.index(current)


@router.get("/catalog", response_model=SoftwareCatalogResponse)
def get_software_catalog() -> dict[str, Any]:
    return get_software_catalog_response()


@router.post("/requests", response_model=SoftwareRequestCreateResponse)
def create_software_request(
    payload: SoftwareRequestCreateRequest,
    request: Request,
) -> SoftwareRequestCreateResponse:
    software_name = (payload.software_name or "").strip()
    if not software_name:
        raise HTTPException(status_code=422, detail="software_name must not be blank.")

    catalog_item = find_catalog_item(software_name)
    if catalog_item is None:
        raise HTTPException(status_code=422, detail="Requested software is not in the approved catalog.")

    request_id, service_now_ref = _generate_request_ids(request)
    status = "queued" if bool(catalog_item.get("approval_required")) else "requested"
    summary = f"Provision {catalog_item['name']} for employee {payload.employee_id}."
    software_request = SoftwareRequest(
        request_id=request_id,
        employee_id=payload.employee_id,
        software_name=str(catalog_item["name"]),
        status=status,
        service_now_ref=service_now_ref,
        request_summary=summary,
        metadata={**payload.metadata, "software_id": catalog_item["software_id"]},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    store = _resolve_request_store(request)
    store[request_id] = software_request.model_dump(mode="json")

    collection = getattr(request.app.state, "mongo_collections", {}).get("software_requests")
    if collection is not None:
        try:
            collection.insert_one(software_request.model_dump(mode="json"))
        except Exception:
            pass

    return SoftwareRequestCreateResponse(
        request_id=request_id,
        service_now_ref=service_now_ref,
        status=status,
        message=f"Software request {request_id} created for {catalog_item['name']}.",
    )


@router.get("/requests", response_model=list[SoftwareRequest])
def list_software_requests(request: Request) -> list[dict[str, Any]]:
    store = dict(_resolve_request_store(request))
    collection = getattr(request.app.state, "mongo_collections", {}).get("software_requests")
    if collection is not None:
        try:
            for item in collection.find({}, {"_id": False}):
                request_id = item.get("request_id")
                if request_id:
                    store.setdefault(request_id, item)
        except Exception:
            pass

    return sorted(
        store.values(),
        key=lambda item: str(item.get("created_at", "")),
        reverse=True,
    )


@router.get("/requests/{request_id}", response_model=SoftwareRequest)
def get_software_request(request_id: str, request: Request) -> dict[str, Any]:
    store = _resolve_request_store(request)
    request_record = store.get(request_id)
    if request_record is None:
        collection = getattr(request.app.state, "mongo_collections", {}).get("software_requests")
        if collection is not None:
            try:
                request_record = collection.find_one({"request_id": request_id}, {"_id": False})
            except Exception:
                request_record = None

    if request_record is None:
        raise HTTPException(status_code=404, detail="Software request not found.")
    return request_record


@router.patch("/requests/{request_id}/status", response_model=SoftwareRequest)
def update_software_request_status(
    request_id: str,
    payload: SoftwareRequestStatusUpdateRequest,
    request: Request,
) -> dict[str, Any]:
    store = _resolve_request_store(request)
    request_record = store.get(request_id)
    if request_record is None:
        collection = getattr(request.app.state, "mongo_collections", {}).get("software_requests")
        if collection is not None:
            try:
                request_record = collection.find_one({"request_id": request_id}, {"_id": False})
            except Exception:
                request_record = None

    if request_record is None:
        raise HTTPException(status_code=404, detail="Software request not found.")

    current_status = str(request_record.get("status") or "")
    target_status = payload.status
    if not _can_transition_status(current_status, target_status):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status transition: {current_status} -> {target_status}.",
        )

    request_record["status"] = target_status
    request_record["updated_at"] = datetime.now(timezone.utc).isoformat()
    store[request_id] = request_record

    collection = getattr(request.app.state, "mongo_collections", {}).get("software_requests")
    if collection is not None:
        try:
            collection.update_one(
                {"request_id": request_id},
                {
                    "$set": {
                        "status": request_record["status"],
                        "updated_at": request_record["updated_at"],
                    }
                },
            )
        except Exception:
            pass

    return request_record
