from __future__ import annotations

from typing import Any


SAFE_AUTOMATION_CASES: dict[str, dict[str, Any]] = {
    "password_expired": {
        "automation_name": "password_expired",
        "title": "Password expired",
        "category": "Identity",
        "sub_category": "Password Reset",
        "assignment_group": "Identity Support",
        "risk_level": "low",
        "description": "Reset an expired password using approved identity verification.",
    },
    "account_lockout": {
        "automation_name": "account_lockout",
        "title": "Account lockout",
        "category": "Identity",
        "sub_category": "Account Unlock",
        "assignment_group": "Identity Support",
        "risk_level": "low",
        "description": "Unlock a locked account after approved user verification.",
    },
    "vpn_status_check": {
        "automation_name": "vpn_status_check",
        "title": "VPN status check",
        "category": "Network",
        "sub_category": "VPN",
        "assignment_group": "Network Support",
        "risk_level": "low",
        "description": "Run a safe diagnostic status check for corporate VPN connectivity.",
    },
    "service_restart": {
        "automation_name": "service_restart",
        "title": "Service restart",
        "category": "Endpoint",
        "sub_category": "Service Management",
        "assignment_group": "Endpoint Support",
        "risk_level": "medium",
        "description": "Restart an approved endpoint service to restore normal operation.",
    },
    "cache_clearing": {
        "automation_name": "cache_clearing",
        "title": "Cache clearing",
        "category": "Endpoint",
        "sub_category": "Performance",
        "assignment_group": "Endpoint Support",
        "risk_level": "low",
        "description": "Clear safe temporary cache locations for supported applications.",
    },
    "application_restart": {
        "automation_name": "application_restart",
        "title": "Application restart",
        "category": "Applications",
        "sub_category": "Runtime Recovery",
        "assignment_group": "Application Support",
        "risk_level": "low",
        "description": "Restart an approved business application process safely.",
    },
}

AUTOMATION_SAFETY_CONFIDENCE_THRESHOLD = 0.75
_UNSAFE_AUTOMATION_KEYWORDS = (
    "hack",
    "exploit",
    "bypass",
    "disable antivirus",
    "drop database",
    "format disk",
    "shutdown server",
    "delete user",
)
_AUTOMATION_INTENT_HINTS = (
    "reset",
    "unlock",
    "restart",
    "cache",
    "clear",
    "flush",
    "self-heal",
    "self heal",
    "runbook",
    "automate",
    "automation",
)


def list_safe_automation_cases() -> list[dict[str, Any]]:
    return [dict(case) for case in SAFE_AUTOMATION_CASES.values()]


def detect_safe_automation_case(question: str) -> str | None:
    normalized = (question or "").strip().lower()
    if not normalized:
        return None

    if "password" in normalized and "expire" in normalized:
        return "password_expired"
    if "locked out" in normalized or "account lock" in normalized:
        return "account_lockout"
    if "vpn" in normalized and "status" in normalized:
        return "vpn_status_check"
    if "restart" in normalized and "service" in normalized:
        return "service_restart"
    if "cache" in normalized and any(token in normalized for token in ["clear", "clearing", "flush"]):
        return "cache_clearing"
    if "restart" in normalized and any(token in normalized for token in ["application", "app"]):
        return "application_restart"
    return None


def assess_automation_safety(question: str) -> dict[str, Any]:
    normalized = (question or "").strip().lower()
    if not normalized:
        return {
            "case_name": None,
            "is_safe": False,
            "should_block": False,
            "is_unsafe": False,
            "confidence": 0.0,
            "reason": "No actionable request found.",
        }

    if any(keyword in normalized for keyword in _UNSAFE_AUTOMATION_KEYWORDS):
        return {
            "case_name": None,
            "is_safe": False,
            "should_block": True,
            "is_unsafe": True,
            "confidence": 0.2,
            "reason": "Unsafe automation request detected.",
        }

    case_name = detect_safe_automation_case(normalized)
    if case_name is not None:
        risk_level = str(SAFE_AUTOMATION_CASES[case_name].get("risk_level", "low"))
        confidence = 0.92 if risk_level == "low" else 0.78
        return {
            "case_name": case_name,
            "is_safe": True,
            "should_block": False,
            "is_unsafe": False,
            "confidence": confidence,
            "reason": "Request matches an approved safe automation case.",
        }

    if any(keyword in normalized for keyword in _AUTOMATION_INTENT_HINTS):
        return {
            "case_name": None,
            "is_safe": False,
            "should_block": True,
            "is_unsafe": False,
            "confidence": 0.35,
            "reason": "Automation request is unclear or outside approved safe cases.",
        }

    return {
        "case_name": None,
        "is_safe": False,
        "should_block": False,
        "is_unsafe": False,
        "confidence": 0.0,
        "reason": "No automation intent detected.",
    }
