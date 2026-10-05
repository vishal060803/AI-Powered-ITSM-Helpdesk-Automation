import unittest

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.routers.knowledge import get_knowledge_vector_store


class StubKnowledgeStore:
    def __init__(self):
        self.search_arguments = None

    def search(self, query, category=None, topic=None, limit=5):
        self.search_arguments = {
            "query": query,
            "category": category,
            "topic": topic,
            "limit": limit,
        }
        return [
            {
                "chunk_id": "KB-NET-001-chunk-001",
                "article_id": "KB-NET-001",
                "title": "VPN connection help",
                "category": "Network",
                "sub_category": "VPN",
                "source_file": "vpn.md",
                "text": "Check the approved VPN client.",
                "distance": 0.1,
            },
            {
                "chunk_id": "KB-NET-001-chunk-002",
                "article_id": "KB-NET-001",
                "title": "VPN connection help",
                "category": "Network",
                "sub_category": "VPN",
                "source_file": "vpn.md",
                "text": "Confirm the internet connection first.",
                "distance": 0.25,
            },
        ]


class KnowledgeRetrievalApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.store = StubKnowledgeStore()
        self.app.dependency_overrides[get_knowledge_vector_store] = (
            lambda: self.store
        )
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()

    def test_retrieval_returns_ranked_chunks_and_source_metadata(self):
        response = self.client.post(
            "/api/v1/knowledge/search",
            json={
                "question": "  How do I fix VPN?  ",
                "category": "Network",
                "topic": "VPN",
                "top_k": 3,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["question"], "How do I fix VPN?")
        self.assertEqual(len(payload["results"]), 2)
        self.assertEqual(payload["results"][0]["rank"], 1)
        self.assertEqual(payload["results"][0]["score"], 0.9)
        self.assertEqual(payload["results"][1]["rank"], 2)
        self.assertEqual(payload["results"][0]["source_file"], "vpn.md")
        self.assertEqual(payload["sources"][0]["article_id"], "KB-NET-001")
        self.assertEqual(len(payload["sources"]), 1)
        self.assertEqual(
            self.store.search_arguments,
            {
                "query": "How do I fix VPN?",
                "category": "Network",
                "topic": "VPN",
                "limit": 3,
            },
        )

    def test_rejects_blank_questions(self):
        response = self.client.post(
            "/api/v1/knowledge/search", json={"question": "   "}
        )

        self.assertEqual(response.status_code, 422)
        self.assertIsNone(self.store.search_arguments)


if __name__ == "__main__":
    unittest.main()
