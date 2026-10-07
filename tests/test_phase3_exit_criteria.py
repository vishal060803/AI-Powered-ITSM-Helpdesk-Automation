import unittest

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.routers.knowledge import get_knowledge_vector_store


EXPECTED_ANALYSIS_FIELDS = {
    "intent",
    "category",
    "sub_category",
    "priority",
    "impact",
    "urgency",
    "assignment_group",
    "summary",
    "suggested_resolution",
    "confidence",
    "sources",
}


class StubKnowledgeStore:
    def search(self, query, category=None, topic=None, limit=5):
        return [
            {
                "chunk_id": "KB-NET-001-chunk-001",
                "article_id": "KB-NET-001",
                "title": "VPN connection help",
                "category": "Network",
                "sub_category": "VPN",
                "source_file": "vpn.md",
                "text": "Check the approved VPN client and retry authentication with MFA.",
                "distance": 0.1,
            }
        ]


class Phase3ExitCriteriaTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.store = StubKnowledgeStore()
        self.app.dependency_overrides[get_knowledge_vector_store] = lambda: self.store
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.app.state.mongo_collections = {}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.app.dependency_overrides.clear()

    def _chat_analyze(self, message):
        response = self.client.post(
            "/api/v1/knowledge/chat",
            json={
                "employee_id": "EMP-2001",
                "message": message,
                "context": {"channel": "phase3-test"},
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def _create_incident_from_analysis(self, description, analysis):
        response = self.client.post(
            "/api/v1/knowledge/incidents",
            json={
                "employee_id": "EMP-2001",
                "description": description,
                "analysis": analysis,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_phase3_exit_criteria_end_to_end(self):
        incident_inputs = [
            "VPN tunnel fails after connection attempt with timeout error.",
            "Cannot reach internal resources over corporate VPN since morning.",
            "Remote access VPN keeps disconnecting every few minutes.",
    ]

        created_ticket_ids = []
        first_analysis = None

        for message in incident_inputs:
            chat_payload = self._chat_analyze(message)
            analysis = chat_payload["analysis"]

            self.assertEqual(analysis["intent"], "incident")
            self.assertTrue(EXPECTED_ANALYSIS_FIELDS.issubset(set(analysis.keys())))
            self.assertEqual(analysis["category"], "Network")
            self.assertEqual(analysis["sub_category"], "VPN")
            self.assertIn(analysis["priority"], {"P1", "P2", "P3", "P4"})
            self.assertIn(analysis["urgency"], {"Low", "Medium", "High"})
            self.assertGreaterEqual(float(analysis["confidence"]), 0.5)

            created = self._create_incident_from_analysis(message, analysis)
            created_ticket_ids.append(created["ticket_id"])
            self.assertTrue(created["ticket_id"].startswith("INC-"))
            self.assertTrue(created["service_now_ref"].startswith("INC"))

            detail_response = self.client.get(f"/api/v1/knowledge/incidents/{created['ticket_id']}")
            self.assertEqual(detail_response.status_code, 200, detail_response.text)
            detail = detail_response.json()
            self.assertEqual(detail["ticket_id"], created["ticket_id"])
            self.assertEqual(detail["description"], message)
            self.assertEqual(detail["ai_analysis"]["intent"], "incident")
            self.assertEqual(detail["ai_analysis"]["category"], "Network")
            self.assertEqual(detail["ai_analysis"]["sub_category"], "VPN")

            if first_analysis is None:
                first_analysis = analysis

        list_response = self.client.get("/api/v1/knowledge/incidents")
        self.assertEqual(list_response.status_code, 200, list_response.text)
        records = list_response.json()
        record_ids = {record["ticket_id"] for record in records}
        for ticket_id in created_ticket_ids:
            self.assertIn(ticket_id, record_ids)

        dashboard_ticket = next(record for record in records if record["ticket_id"] == created_ticket_ids[0])
        self.assertEqual(dashboard_ticket["intent"], first_analysis["intent"])
        self.assertEqual(dashboard_ticket["priority"], first_analysis["priority"])
        self.assertEqual(dashboard_ticket["assignment_group"], first_analysis["assignment_group"])
        self.assertEqual(dashboard_ticket["ai_analysis"]["intent"], first_analysis["intent"])
        self.assertEqual(dashboard_ticket["ai_analysis"]["suggested_resolution"], first_analysis["suggested_resolution"])


if __name__ == "__main__":
    unittest.main()
