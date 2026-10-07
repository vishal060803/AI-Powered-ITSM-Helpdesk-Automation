import unittest

from fastapi.testclient import TestClient

from backend.app.main import create_app


class TicketDashboardApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.app.state.mongo_collections = {}

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def _create_ticket(self, description):
        response = self.client.post(
            "/api/v1/knowledge/incidents",
            json={
                "employee_id": "EMP-1024",
                "description": description,
                "analysis": {
                    "intent": "incident",
                    "category": "Network",
                    "sub_category": "VPN",
                    "priority": "P2",
                    "impact": "Individual",
                    "urgency": "High",
                    "assignment_group": "Network Support",
                    "summary": "VPN connection issue",
                    "suggested_resolution": "Verify VPN configuration and MFA.",
                    "confidence": 0.93,
                    "sources": [],
                },
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["ticket_id"]

    def test_ticket_list_filters_open_and_resolved_records(self):
        open_ticket_id = self._create_ticket("VPN authentication is failing.")
        resolved_ticket_id = self._create_ticket("VPN issue is now fixed.")
        self.app.state.ticket_store[resolved_ticket_id]["status"] = "resolved"

        open_response = self.client.get("/api/v1/knowledge/incidents?status=open")
        resolved_response = self.client.get("/api/v1/knowledge/incidents?status=resolved")

        self.assertEqual(open_response.status_code, 200)
        self.assertEqual([ticket["ticket_id"] for ticket in open_response.json()], [open_ticket_id])
        self.assertEqual(resolved_response.status_code, 200)
        self.assertEqual(
            [ticket["ticket_id"] for ticket in resolved_response.json()],
            [resolved_ticket_id],
        )

    def test_ticket_details_include_record_and_ai_analysis(self):
        ticket_id = self._create_ticket("VPN authentication is failing.")

        response = self.client.get(f"/api/v1/knowledge/incidents/{ticket_id}")

        self.assertEqual(response.status_code, 200)
        ticket = response.json()
        self.assertEqual(ticket["ticket_id"], ticket_id)
        self.assertEqual(ticket["ai_analysis"]["intent"], "incident")
        self.assertEqual(ticket["ai_analysis"]["category"], "Network")
        self.assertEqual(ticket["ai_analysis"]["suggested_resolution"], "Verify VPN configuration and MFA.")
        self.assertEqual(ticket["confidence"], 0.93)

    def test_ticket_details_return_not_found_for_unknown_id(self):
        response = self.client.get("/api/v1/knowledge/incidents/INC-DOES-NOT-EXIST")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
