import re
from typing import Any

try:
    from app.automation_cases import (
        AUTOMATION_SAFETY_CONFIDENCE_THRESHOLD,
        SAFE_AUTOMATION_CASES,
        assess_automation_safety,
    )
    from app.schemas import AIAnalysis
    from app.software_catalog import extract_software_name
except ImportError:  # pragma: no cover - fallback for repo-root imports during tests
    from backend.app.automation_cases import (
        AUTOMATION_SAFETY_CONFIDENCE_THRESHOLD,
        SAFE_AUTOMATION_CASES,
        assess_automation_safety,
    )
    from backend.app.schemas import AIAnalysis
    from backend.app.software_catalog import extract_software_name


def build_incident_payload(analysis: AIAnalysis, description: str) -> dict[str, Any]:
    normalized_description = _clean_text(description)
    service_now_fields = {
        "short_description": analysis.summary,
        "description": normalized_description,
        "category": analysis.category,
        "sub_category": analysis.sub_category,
        "priority": analysis.priority,
        "impact": analysis.impact,
        "urgency": analysis.urgency,
        "assignment_group": analysis.assignment_group,
        "confidence": analysis.confidence,
    }
    return {
        "short_description": analysis.summary,
        "description": normalized_description,
        "category": analysis.category,
        "sub_category": analysis.sub_category,
        "priority": analysis.priority,
        "impact": analysis.impact,
        "urgency": analysis.urgency,
        "assignment_group": analysis.assignment_group,
        "confidence": analysis.confidence,
        "service_now_fields": service_now_fields,
    }


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def build_grounded_answer(question: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    support_threshold = 0.6
    normalized_question = _clean_text(question)
    if not normalized_question:
        return {
            "answer": "I could not determine the issue from the request. Please provide a clearer description of the problem.",
            "sources": [],
            "confidence": 0.0,
            "is_supported": False,
        }

    if not results:
        return {
            "answer": "I cannot answer confidently because the request is not supported by the approved knowledge base. Please escalate the issue to the appropriate support team.",
            "sources": [],
            "confidence": 0.1,
            "is_supported": False,
        }

    primary = results[0]
    source_title = str(primary.get("title") or "Approved support article")
    source_category = str(primary.get("category") or "General")
    source_sub_category = str(primary.get("sub_category") or "Support")
    source_text = str(primary.get("text") or "")
    distance = float(primary.get("distance", 0.0) or 0.0)
    confidence = max(0.0, min(0.99, 1.0 - distance))

    cleaned_text = _clean_text(source_text)
    answer = (
        f"According to the approved {source_category} / {source_sub_category} guidance, "
        f"{source_title}, the recommended steps are: {cleaned_text}"
    )

    if not cleaned_text or confidence < support_threshold:
        return {
            "answer": "I cannot answer confidently because the request is not supported by the approved knowledge base. Please escalate the issue to the appropriate support team.",
            "sources": [source_title] if source_title else [],
            "confidence": round(confidence, 2),
            "is_supported": False,
        }

    return {
        "answer": answer,
        "sources": [source_title],
        "confidence": round(confidence, 2),
        "is_supported": True,
    }


def _is_password_issue(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in [
        "password",
        "reset password",
        "forgot password",
        "locked out",
        "account lock",
    ])


def _is_vpn_issue(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in [
        "vpn",
        "network",
        "connect to vpn",
        "authentication keeps failing",
        "cannot connect",
        "remote access",
    ])


def detect_software_provisioning_request(
    question: str,
    employee_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_question = _clean_text(question)
    normalized = normalized_question.lower()
    software_name = extract_software_name(normalized_question)

    request_keywords = [
        "install",
        "software",
        "provision",
        "setup",
        "set up",
        "download",
        "need",
        "request",
    ]
    has_request_keyword = any(keyword in normalized for keyword in request_keywords)
    is_provisioning_request = bool(software_name and has_request_keyword)

    context = context or {}
    employee_context: dict[str, Any] = {
        "employee_id": employee_id,
        "department": context.get("department"),
        "location": context.get("location"),
        "device_id": context.get("device_id"),
        "manager_approval": context.get("manager_approval"),
    }
    employee_context = {key: value for key, value in employee_context.items() if value not in (None, "")}

    summary = ""
    if is_provisioning_request:
        requester = employee_id or "employee"
        summary = f"Software provisioning request for {software_name} by {requester}."

    return {
        "is_provisioning_request": is_provisioning_request,
        "software_name": software_name,
        "employee_context": employee_context,
        "summary": summary,
    }


def classify_request(
    question: str,
    results: list[dict[str, Any]] | None = None,
    employee_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> AIAnalysis:
    normalized_question = _clean_text(question)
    normalized = normalized_question.lower()
    if not normalized:
        return AIAnalysis(
            intent="knowledge_question",
            category="General",
            sub_category="Unknown",
            priority="P4",
            impact="Individual",
            urgency="Low",
            assignment_group="End User Support",
            summary="Empty support request",
            suggested_resolution="Ask the user to provide a clear description of the issue.",
            confidence=0.0,
            sources=[],
        )

    primary = (results or [{}])[0]
    category = str(primary.get("category") or "General")
    sub_category = str(primary.get("sub_category") or "Support")
    base_confidence = 0.9

    automation_safety = assess_automation_safety(normalized)
    if automation_safety["should_block"]:
        if automation_safety["is_unsafe"]:
            return AIAnalysis(
                intent="knowledge_question",
                category="Security",
                sub_category="Automation Safety",
                priority="P2",
                impact="High",
                urgency="High",
                assignment_group="Security Operations",
                summary="Blocked unsafe automation request",
                suggested_resolution="This automation request is unsafe. Do not execute it and escalate to Security Operations.",
                confidence=float(automation_safety["confidence"]),
                sources=[],
            )

        return AIAnalysis(
            intent="knowledge_question",
            category="Automation",
            sub_category="Unclear Request",
            priority="P3",
            impact="Individual",
            urgency="Medium",
            assignment_group="End User Support",
            summary="Blocked unclear automation request",
            suggested_resolution="The automation request is unclear or outside approved safe cases. Ask for more details or escalate.",
            confidence=float(automation_safety["confidence"]),
            sources=[],
        )

    if automation_safety["is_safe"]:
        if float(automation_safety["confidence"]) < AUTOMATION_SAFETY_CONFIDENCE_THRESHOLD:
            return AIAnalysis(
                intent="knowledge_question",
                category="Automation",
                sub_category="Low Confidence",
                priority="P3",
                impact="Individual",
                urgency="Medium",
                assignment_group="End User Support",
                summary="Blocked low-confidence automation request",
                suggested_resolution="Automation safety confidence is below threshold. Collect more details and escalate if needed.",
                confidence=float(automation_safety["confidence"]),
                sources=[],
            )

        automation_case = SAFE_AUTOMATION_CASES[str(automation_safety["case_name"])]
        return AIAnalysis(
            intent="automatable_issue",
            category=str(automation_case["category"]),
            sub_category=str(automation_case["sub_category"]),
            priority="P3",
            impact="Individual",
            urgency="Medium",
            assignment_group=str(automation_case["assignment_group"]),
            summary=f"Safe automation case: {automation_case['title']}",
            suggested_resolution=str(automation_case["description"]),
            confidence=float(automation_safety["confidence"]),
            sources=[],
        )

    software_request = detect_software_provisioning_request(
        normalized_question,
        employee_id=employee_id,
        context=context,
    )
    if software_request["is_provisioning_request"]:
        software_name = str(software_request["software_name"])
        employee_context = software_request["employee_context"]
        context_summary = ""
        if employee_context:
            context_summary = (
                " Context captured: "
                + ", ".join(f"{key}={value}" for key, value in employee_context.items())
                + "."
            )

        return AIAnalysis(
            intent="service_request",
            category="Software",
            sub_category="Provisioning",
            priority="P3",
            impact="Individual",
            urgency="Medium",
            assignment_group="Software Support",
            summary=str(software_request["summary"]),
            suggested_resolution=(
                f"Create a provisioning request for {software_name}, validate catalog approval requirements, "
                f"and track fulfillment through the request lifecycle.{context_summary}"
            ),
            confidence=0.92,
            sources=[],
        )

    if _is_password_issue(normalized):
        return AIAnalysis(
            intent="automatable_issue",
            category="Identity",
            sub_category="Password Reset",
            priority="P3",
            impact="Individual",
            urgency="Medium",
            assignment_group="Identity Support",
            summary="Password reset or account unlock support",
            suggested_resolution="Use the approved password-reset portal, validate identity, and complete the reset or unlock workflow safely.",
            confidence=base_confidence,
            sources=[],
        )

    if _is_vpn_issue(normalized):
        return AIAnalysis(
            intent="incident",
            category="Network",
            sub_category="VPN",
            priority="P2",
            impact="Individual",
            urgency="High",
            assignment_group="Network Support",
            summary="VPN or network connectivity issue",
            suggested_resolution="Verify the vpn client, MFA, connection path, and network settings, then escalate with exact error details if the issue persists.",
            confidence=base_confidence,
            sources=[],
        )

    if any(keyword in normalized for keyword in ["install", "software", "teams", "vscode", "adobe", "provision", "download"]):
        return AIAnalysis(
            intent="service_request",
            category="Software",
            sub_category="Provisioning",
            priority="P3",
            impact="Individual",
            urgency="Medium",
            assignment_group="Software Support",
            summary="Software installation or provisioning request",
            suggested_resolution="Create the software provisioning request, validate the catalog item, and track its status until completion.",
            confidence=base_confidence,
            sources=[],
        )

    if any(keyword in normalized for keyword in ["outlook", "sync", "email", "mail"]):
        return AIAnalysis(
            intent="knowledge_question",
            category="Email",
            sub_category="Outlook",
            priority="P4",
            impact="Individual",
            urgency="Low",
            assignment_group="End User Support",
            summary="Outlook or email synchronization troubleshooting",
            suggested_resolution="Follow the approved Outlook troubleshooting guidance and verify account configuration before escalating.",
            confidence=0.86,
            sources=[],
        )

    if any(keyword in normalized for keyword in ["hack", "exploit", "bypass", "unauthorized", "secure server"]):
        return AIAnalysis(
            intent="knowledge_question",
            category="Security",
            sub_category="Unknown",
            priority="P2",
            impact="High",
            urgency="High",
            assignment_group="Security Operations",
            summary="Unsupported security question",
            suggested_resolution="Do not provide unsupported guidance; escalate to the security team and follow the approved escalation policy.",
            confidence=0.4,
            sources=[],
        )

    return AIAnalysis(
        intent="knowledge_question",
        category="General",
        sub_category="Unknown",
        priority="P3",
        impact="Individual",
        urgency="Medium",
        assignment_group="End User Support",
        summary=f"Knowledge-based support request: {question[:120]}".strip(),
        suggested_resolution="I cannot confidently classify this request using approved guidance. Ask clarifying questions and escalate to a human support agent if uncertainty remains.",
        confidence=0.45,
        sources=[],
    )


def _pick_steps(question: str, results: list[dict[str, Any]]) -> tuple[list[str], str]:
    if _is_password_issue(question):
        return (
            [
                "Use the forgot password option in the approved company portal.",
                "Verify your identity with the registered phone number, email, or MFA method and enter the OTP.",
                "Create a new password that matches the company policy and sign in again.",
            ],
            "If the portal cannot verify your identity or the account stays locked, contact the Identity Support team with the exact error and time.",
        )

    if _is_vpn_issue(question):
        return (
            [
                "Check that your internet connection is working and confirm the device date and time are correct.",
                "Open the approved VPN client, sign in with your corporate account, and complete the expected MFA step.",
                "Retry the connection and, if it still fails, share the exact VPN error with Network Support.",
            ],
            "If the VPN keeps failing after the standard checks, escalate with the exact error text, device type, VPN client version, and network type.",
        )

    if results:
        main_result = results[0].get("text", "")
        sentences = [
            sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", _clean_text(main_result))
            if len(sentence.strip()) > 18
        ]
        if len(sentences) >= 3:
            steps = [
                f"{sentences[0]}",
                f"{sentences[1]}",
                f"{sentences[2]}",
            ]
            return steps, "Follow the approved support steps and validate the fix before closing the case."

    return (
        [
            "Review the most relevant support guidance and follow the approved workflow exactly.",
            "Validate the issue using the correct settings, MFA prompt, or service checks before retrying.",
            "Escalate with the exact error, time, and impacted service if the issue persists.",
        ],
        "If the guidance does not resolve the issue, create or update the service request with the exact symptoms and outcome.",
    )


def build_assistant_reply(question: str, results: list[dict[str, Any]]) -> str:
    normalized_question = _clean_text(question)
    grounded = build_grounded_answer(normalized_question, results)
    steps, final_suggestion = _pick_steps(normalized_question, results)
    source_summary = ""
    if grounded["sources"]:
        source_names = ", ".join(grounded["sources"])
        source_summary = f" The relevant guidance is from the approved article(s): {source_names}."

    introduction = "Hi, I reviewed your issue and checked the approved guidance."
    if source_summary:
        introduction = f"Hi, I reviewed your issue and checked the approved guidance.{source_summary}"

    if not grounded["is_supported"]:
        return (
            f"{introduction}\n\n"
            f"I cannot answer confidently because the request is not supported by the approved knowledge base. "
            f"Please escalate the issue to the appropriate support team.\n\n"
            f"Final suggestion: {final_suggestion}"
        )

    reply = (
        f"{introduction}\n\n"
        f"1) {steps[0]}\n"
        f"2) {steps[1]}\n"
        f"3) {steps[2]}\n\n"
        f"Final suggestion: {final_suggestion}"
    )
    return reply
