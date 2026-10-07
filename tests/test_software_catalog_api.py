import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import create_app


class SoftwareCatalogApiTests(unittest.TestCase):
    def test_returns_catalog_items_and_status_lifecycle(self):
        with patch.dict(os.environ, {"SKIP_MONGODB_INIT": "1"}):
            app = create_app()
            client = TestClient(app)
            response = client.get("/api/v1/software/catalog")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertIn("items", payload)
        self.assertIn("status_lifecycle", payload)
        self.assertGreaterEqual(len(payload["items"]), 4)
        self.assertIn("provisioning", payload["status_lifecycle"])
        self.assertIn("approved", payload["status_lifecycle"])
        self.assertIn("failed", payload["status_lifecycle"])


if __name__ == "__main__":
    unittest.main()

