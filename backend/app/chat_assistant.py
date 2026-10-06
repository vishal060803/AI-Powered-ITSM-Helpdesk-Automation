import re
from typing import Any

def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _is_password_issue(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in [
        "password",
        "reset password",
        "forgot password",
        "locked out",
        "account lock",
        "login",
        "otp",
        "mfa",
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
    steps, final_suggestion = _pick_steps(normalized_question, results)
    source_summary = ""
    if results:
        primary = results[0]
        category = primary.get("category") or "General"
        sub_category = primary.get("sub_category") or "Support"
        source_summary = f" The relevant guidance is from the {category} / {sub_category} article."

    introduction = "Hi, I reviewed your issue and checked the approved guidance."
    if source_summary:
        introduction = f"Hi, I reviewed your issue and checked the approved guidance.{source_summary}"

    reply = (
        f"{introduction}\n\n"
        f"1) {steps[0]}\n"
        f"2) {steps[1]}\n"
        f"3) {steps[2]}\n\n"
        f"Final suggestion: {final_suggestion}"
    )
    return reply
