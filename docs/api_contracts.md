# Shared API Contracts and Data Definitions

This document defines the main payload contracts for the AI ITSM prototype.

## 1. Chat request

```json
{
  "employee_id": "EMP-1024",
  "message": "I cannot connect to VPN since this morning.",
  "context": {
    "device": "Dell Latitude 7420",
    "location": "Remote"
  }
}
```

## 2. Chat response

```json
{
  "response": "I found a likely VPN authentication issue. I suggest checking the VPN client version and re-entering credentials.",
  "analysis": {
    "intent": "incident",
    "category": "Network",
    "sub_category": "VPN",
    "priority": "P2",
    "impact": "Individual",
    "urgency": "High",
    "assignment_group": "Network Support",
    "summary": "VPN authentication failure",
    "suggested_resolution": "VPN troubleshooting",
    "confidence": 0.91,
    "sources": [
      {
        "article_id": "KB-VPN-01",
        "title": "VPN Troubleshooting",
        "category": "Network",
        "sub_category": "VPN",
        "source_file": "vpn_troubleshooting.md",
        "score": 0.92
      }
    ]
  },
  "ticket_created": true,
  "ticket_id": "INC-1001",
  "automation_executed": false,
  "software_request_id": null
}
```

## 3. Ticket schema

```json
{
  "ticket_id": "INC-1001",
  "employee_id": "EMP-1024",
  "title": "VPN authentication failure",
  "description": "User cannot connect to VPN since this morning.",
  "intent": "incident",
  "category": "Network",
  "sub_category": "VPN",
  "priority": "P2",
  "impact": "Individual",
  "urgency": "High",
  "assignment_group": "Network Support",
  "status": "open",
  "confidence": 0.91,
  "ai_analysis": {
    "intent": "incident",
    "category": "Network",
    "sub_category": "VPN",
    "priority": "P2",
    "impact": "Individual",
    "urgency": "High",
    "assignment_group": "Network Support",
    "summary": "VPN authentication failure",
    "suggested_resolution": "VPN troubleshooting",
    "confidence": 0.91,
    "sources": []
  },
  "service_now_ref": "INC0001234",
  "created_at": "2026-10-05T12:00:00Z",
  "updated_at": "2026-10-05T12:00:00Z"
}
```

## 4. Knowledge article schema

```json
{
  "article_id": "KB-VPN-01",
  "title": "VPN Troubleshooting",
  "category": "Network",
  "sub_category": "VPN",
  "content": "If VPN authentication fails, verify credentials, ensure MFA is completed, and confirm VPN client version is supported.",
  "source_file": "vpn_troubleshooting.md",
  "tags": ["vpn", "authentication", "network"],
  "created_at": "2026-10-05T09:00:00Z"
}
```

## 5. Automation action schema

```json
{
  "action_id": "AUT-001",
  "ticket_id": "INC-1001",
  "automation_name": "password_reset",
  "status": "success",
  "steps": [
    "Identify expired password issue",
    "Check account status",
    "Trigger reset workflow",
    "Validate next login"
  ],
  "result_message": "Password reset completed successfully.",
  "validation_result": "User login validated.",
  "created_at": "2026-10-05T12:10:00Z"
}
```

## 6. Demo scenario examples

### VPN incident
- Input: "I cannot connect to VPN since this morning. Authentication keeps failing."
- Output: intent = incident, category = Network, sub_category = VPN, priority = P2

### Password expiry self-heal
- Input: "My password has expired."
- Output: intent = automatable_issue, category = Identity, sub_category = Password Reset

### RAG troubleshooting
- Input: "How do I troubleshoot Outlook synchronization?"
- Output: intent = knowledge_question

### Software provisioning
- Input: "I need Visual Studio Code installed on my laptop."
- Output: intent = service_request

### Unknown or unsupported request
- Input: "How do I hack into the secure file server?"
- Output: safe escalation or refusal with no hallucination

## 7. Notes

- All AI outputs should use structured schemas and confidence thresholds.
- All RAG responses must attribute sources.
- Automation actions must be auditable.
- Production ServiceNow integration should mirror these schemas.
