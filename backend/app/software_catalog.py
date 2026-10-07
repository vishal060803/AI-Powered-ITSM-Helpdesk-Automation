from __future__ import annotations

from typing import Any


SOFTWARE_REQUEST_STATUS_LIFECYCLE = [
    "requested",
    "queued",
    "approved",
    "provisioning",
    "completed",
    "failed",
    "rejected",
]


SOFTWARE_CATALOG_ITEMS: list[dict[str, Any]] = [
    {
        "software_id": "SW-VSCODE",
        "name": "Visual Studio Code",
        "category": "Developer Tools",
        "version": "latest-approved",
        "license_type": "freeware",
        "approval_required": False,
        "supported_os": ["Windows", "Linux", "macOS"],
        "default_assignment_group": "Software Support",
        "estimated_fulfillment_hours": 2,
        "request_metadata_fields": ["business_justification", "device_id"],
    },
    {
        "software_id": "SW-TEAMS",
        "name": "Microsoft Teams",
        "category": "Collaboration",
        "version": "latest-approved",
        "license_type": "enterprise",
        "approval_required": False,
        "supported_os": ["Windows", "macOS"],
        "default_assignment_group": "Unified Communications",
        "estimated_fulfillment_hours": 4,
        "request_metadata_fields": ["business_justification", "manager_approval"],
    },
    {
        "software_id": "SW-ADOBE-READER",
        "name": "Adobe Reader",
        "category": "Productivity",
        "version": "latest-approved",
        "license_type": "freeware",
        "approval_required": False,
        "supported_os": ["Windows", "macOS"],
        "default_assignment_group": "Desktop Support",
        "estimated_fulfillment_hours": 6,
        "request_metadata_fields": ["device_id"],
    },
    {
        "software_id": "SW-VPN-CLIENT",
        "name": "Corporate VPN Client",
        "category": "Network Security",
        "version": "latest-approved",
        "license_type": "enterprise",
        "approval_required": True,
        "supported_os": ["Windows", "macOS"],
        "default_assignment_group": "Network Support",
        "estimated_fulfillment_hours": 8,
        "request_metadata_fields": ["business_justification", "manager_approval", "location"],
    },
]

SOFTWARE_NAME_ALIASES: dict[str, list[str]] = {
    "Visual Studio Code": ["visual studio code", "vs code", "vscode"],
    "Microsoft Teams": ["microsoft teams", "teams"],
    "Adobe Reader": ["adobe reader", "acrobat reader"],
    "Corporate VPN Client": ["vpn client", "corporate vpn", "vpn"],
}


def get_software_catalog_response() -> dict[str, Any]:
    return {
        "status_lifecycle": list(SOFTWARE_REQUEST_STATUS_LIFECYCLE),
        "items": [dict(item) for item in SOFTWARE_CATALOG_ITEMS],
    }


def extract_software_name(question: str) -> str | None:
    normalized = (question or "").strip().lower()
    if not normalized:
        return None

    for software_name, aliases in SOFTWARE_NAME_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return software_name
    return None


def find_catalog_item(software_name: str) -> dict[str, Any] | None:
    normalized = (software_name or "").strip().lower()
    if not normalized:
        return None

    for item in SOFTWARE_CATALOG_ITEMS:
        name = str(item.get("name") or "").strip().lower()
        if name == normalized:
            return dict(item)

    extracted = extract_software_name(software_name)
    if extracted is None:
        return None

    for item in SOFTWARE_CATALOG_ITEMS:
        if item.get("name") == extracted:
            return dict(item)
    return None
