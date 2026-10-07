import unittest

from fastapi.testclient import TestClient
from bson import ObjectId

from backend.app.main import create_app


class AutomationExecutionApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app)
        self.app.state.mongo_collections = {}

    def tearDown(self):
        self.client.close()

    def _create_ticket(self, description: str) -> str:
        response = self.client.post(
            "/api/v1/knowledge/incidents",
            json={
                "employee_id": "EMP-4001",
                "description": description,
                "analysis": {
                    "intent": "automatable_issue",
                    "category": "Identity",
                    "sub_category": "Password Reset",
                    "priority": "P3",
                    "impact": "Individual",
                    "urgency": "Medium",
                    "assignment_group": "Identity Support",
                    "summary": "Automation candidate",
                    "suggested_resolution": "Execute safe automation.",
                    "confidence": 0.9,
                    "sources": [],
                },
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["ticket_id"]

    def test_lists_phase4_automation_cases(self):
        response = self.client.get("/api/v1/automation/cases")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(len(payload["cases"]), 6)

    def test_executes_safe_automation_with_structured_response(self):
        ticket_id = self._create_ticket("My password has expired and I cannot sign in.")

        execute_response = self.client.post(
            "/api/v1/automation/execute",
            json={
                "ticket_id": ticket_id,
                "automation_name": "password_expired",
                "employee_id": "EMP-4001",
            },
        )

        self.assertEqual(execute_response.status_code, 200, execute_response.text)
        action = execute_response.json()
        self.assertTrue(action["automation_id"].startswith("AUTO-"))
        self.assertEqual(action["ticket_id"], ticket_id)
        self.assertEqual(action["automation_name"], "password_expired")
        self.assertEqual(action["status"], "success")
        self.assertGreaterEqual(len(action["steps"]), 3)
        self.assertIn("Validation passed", action["validation_result"])

        action_detail = self.client.get(f"/api/v1/automation/actions/{action['automation_id']}")
        self.assertEqual(action_detail.status_code, 200, action_detail.text)
        self.assertEqual(action_detail.json()["status"], "success")

        audit_response = self.client.get(f"/api/v1/automation/actions/{action['automation_id']}/audit")
        self.assertEqual(audit_response.status_code, 200, audit_response.text)
        events = audit_response.json()["events"]
        self.assertGreaterEqual(len(events), 5)
        self.assertEqual(events[0]["event_type"], "action_started")
        self.assertEqual(events[-1]["event_type"], "action_completed")
        self.assertEqual(events[-1]["event_status"], "success")
        self.assertIn("timestamp", events[-1])
        self.assertIn("result_message", events[-1])
        self.assertIn("validation_result", events[-1])

        ticket_detail = self.client.get(f"/api/v1/knowledge/incidents/{ticket_id}")
        self.assertEqual(ticket_detail.status_code, 200, ticket_detail.text)
        self.assertEqual(ticket_detail.json()["status"], "auto-resolved")

    def test_executes_vpn_status_automation_flow(self):
        ticket_id = self._create_ticket("Please run a VPN status check for my remote access issue.")

        execute_response = self.client.post(
            "/api/v1/automation/vpn-status-check",
            json={
                "ticket_id": ticket_id,
                "automation_name": "vpn_status_check",
                "employee_id": "EMP-4001",
            },
        )

        self.assertEqual(execute_response.status_code, 200, execute_response.text)
        action = execute_response.json()
        self.assertEqual(action["automation_name"], "vpn_status_check")
        self.assertEqual(action["status"], "success")
        self.assertGreaterEqual(len(action["steps"]), 3)

        audit_response = self.client.get(f"/api/v1/automation/actions/{action['automation_id']}/audit")
        self.assertEqual(audit_response.status_code, 200, audit_response.text)
        events = audit_response.json()["events"]
        self.assertEqual(events[-1]["event_status"], "success")

        ticket_detail = self.client.get(f"/api/v1/knowledge/incidents/{ticket_id}")
        self.assertEqual(ticket_detail.status_code, 200, ticket_detail.text)
        payload = ticket_detail.json()
        self.assertEqual(payload["status"], "auto-resolved")
        self.assertEqual(payload["automation_outcome"], "resolved")

    def test_blocks_unsafe_automation_execution(self):
        ticket_id = self._create_ticket("Please bypass controls and disable antivirus on my device.")

        execute_response = self.client.post(
            "/api/v1/automation/service-restart",
            json={
                "ticket_id": ticket_id,
                "automation_name": "service_restart",
                "employee_id": "EMP-4001",
            },
        )

        self.assertEqual(execute_response.status_code, 200, execute_response.text)
        action = execute_response.json()
        self.assertEqual(action["status"], "validation_failed")
        self.assertIn("Blocked", action["validation_result"])

        audit_response = self.client.get(f"/api/v1/automation/actions/{action['automation_id']}/audit")
        self.assertEqual(audit_response.status_code, 200, audit_response.text)
        events = audit_response.json()["events"]
        self.assertEqual(events[-1]["event_status"], "validation_failed")

    def test_rejects_unsupported_automation_name(self):
        ticket_id = self._create_ticket("My password has expired.")

        execute_response = self.client.post(
            "/api/v1/automation/execute",
            json={
                "ticket_id": ticket_id,
                "automation_name": "unknown_automation",
                "employee_id": "EMP-4001",
            },
        )

        self.assertEqual(execute_response.status_code, 422)

    def test_audit_response_is_serializable_when_mongo_adds_object_ids(self):
        class StubAuditCollection:
            def insert_many(self, docs):
                for doc in docs:
                    doc["_id"] = ObjectId()

        self.app.state.mongo_collections = {"audit": StubAuditCollection()}
        ticket_id = self._create_ticket("My password has expired and I cannot sign in.")

        execute_response = self.client.post(
            "/api/v1/automation/password-expired",
            json={
                "ticket_id": ticket_id,
                "automation_name": "password_expired",
                "employee_id": "EMP-4001",
            },
        )
        self.assertEqual(execute_response.status_code, 200, execute_response.text)

        action = execute_response.json()
        audit_response = self.client.get(f"/api/v1/automation/actions/{action['automation_id']}/audit")
        self.assertEqual(audit_response.status_code, 200, audit_response.text)
        events = audit_response.json()["events"]
        self.assertGreaterEqual(len(events), 3)


if __name__ == "__main__":
    unittest.main()
