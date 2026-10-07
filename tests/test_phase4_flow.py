import unittest
from types import SimpleNamespace

from backend.app.routers.automation import execute_automation
from backend.app.schemas import AutomationExecutionRequest


def _build_request_with_ticket(ticket_id: str, description: str) -> SimpleNamespace:
    ticket = {
        "ticket_id": ticket_id,
        "description": description,
        "status": "open",
        "updated_at": None,
    }
    state = SimpleNamespace(
        ticket_store={ticket_id: ticket},
        mongo_collections={},
        automation_store={},
        audit_store=[],
        automation_counter=0,
    )
    return SimpleNamespace(app=SimpleNamespace(state=state))


class Phase4FlowTests(unittest.TestCase):
    def test_password_reset_and_vpn_status_flows_succeed(self):
        password_request = _build_request_with_ticket(
            "INC-9001",
            "My password has expired and I cannot sign in.",
        )
        password_result = execute_automation(
            "password_expired",
            AutomationExecutionRequest(
                ticket_id="INC-9001",
                automation_name="password_expired",
                employee_id="EMP-9001",
            ),
            password_request,
        )
        self.assertEqual(password_result.status, "success")
        self.assertEqual(password_request.app.state.ticket_store["INC-9001"]["status"], "auto-resolved")
        self.assertEqual(
            password_request.app.state.ticket_store["INC-9001"]["automation_outcome"],
            "resolved",
        )

        vpn_request = _build_request_with_ticket(
            "INC-9002",
            "Please run a VPN status check for remote access.",
        )
        vpn_result = execute_automation(
            "vpn_status_check",
            AutomationExecutionRequest(
                ticket_id="INC-9002",
                automation_name="vpn_status_check",
                employee_id="EMP-9002",
            ),
            vpn_request,
        )
        self.assertEqual(vpn_result.status, "success")
        self.assertEqual(vpn_request.app.state.ticket_store["INC-9002"]["status"], "auto-resolved")

    def test_unsafe_request_fails_validation_and_escalates(self):
        request = _build_request_with_ticket(
            "INC-9003",
            "Bypass controls and disable antivirus immediately.",
        )
        result = execute_automation(
            "service_restart",
            AutomationExecutionRequest(
                ticket_id="INC-9003",
                automation_name="service_restart",
                employee_id="EMP-9003",
            ),
            request,
        )
        self.assertEqual(result.status, "validation_failed")
        self.assertIn("Blocked", result.validation_result or "")
        self.assertEqual(request.app.state.ticket_store["INC-9003"]["status"], "escalated")
        self.assertEqual(
            request.app.state.ticket_store["INC-9003"]["automation_outcome"],
            "escalated",
        )

    def test_audit_log_records_stepwise_events_and_timestamps(self):
        request = _build_request_with_ticket(
            "INC-9004",
            "Please run a VPN status check.",
        )
        result = execute_automation(
            "vpn_status_check",
            AutomationExecutionRequest(
                ticket_id="INC-9004",
                automation_name="vpn_status_check",
                employee_id="EMP-9004",
            ),
            request,
        )
        events = [
            event for event in request.app.state.audit_store
            if event.get("action_id") == result.automation_id
        ]
        self.assertGreaterEqual(len(events), 5)
        self.assertEqual(events[0]["event_type"], "action_started")
        self.assertEqual(events[-1]["event_type"], "action_completed")
        self.assertTrue(all(event.get("timestamp") for event in events))
        self.assertTrue(all("result_message" in event for event in events))


if __name__ == "__main__":
    unittest.main()

