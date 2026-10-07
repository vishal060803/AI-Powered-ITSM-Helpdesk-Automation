import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class IncidentCreationFlowTests(unittest.TestCase):
    def test_create_incident_endpoint_returns_ticket_and_servicenow_reference(self):
        client = TestClient(app)
        app.state.mongo_collections = {}
        payload = {
            "employee_id": "EMP-1024",
            "description": "I cannot connect to VPN since this morning. Authentication keeps failing.",
            "analysis": {
                "intent": "incident",
                "category": "Network",
                "sub_category": "VPN",
                "priority": "P2",
                "impact": "Individual",
                "urgency": "High",
                "assignment_group": "Network Support",
                "summary": "VPN authentication failure",
                "suggested_resolution": "Verify VPN configuration and MFA.",
                "confidence": 0.93,
                "sources": [],
            },
        }

        response = client.post("/api/v1/knowledge/incidents", json=payload)

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ticket_id"].startswith("INC-"))
        self.assertTrue(body["service_now_ref"].startswith("INC"))
        self.assertEqual(body["status"], "open")
        self.assertIn("Network Support", body["message"])

        service_now_response = client.get(f"/api/servicenow/incidents/{body['service_now_ref']}")
        self.assertEqual(service_now_response.status_code, 200, service_now_response.text)
        incident = service_now_response.json()
        self.assertEqual(incident["number"], body["service_now_ref"])
        self.assertEqual(incident["category"], "Network")
        self.assertEqual(incident["sub_category"], "VPN")


if __name__ == "__main__":
    unittest.main()
