import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class BackendAppShellTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_exists(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("service", payload)

    def test_api_root_endpoint_exists(self):
        response = self.client.get("/api/v1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("app", payload)

    def test_server_root_endpoint_exists(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("docs", payload)


if __name__ == "__main__":
    unittest.main()
