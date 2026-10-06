import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from pymongo.errors import ServerSelectionTimeoutError

from backend.app.database import (
    COLLECTION_NAMES,
    MongoSettings,
    ensure_collections,
)
from backend.app.main import create_app


class MongoSettingsTests(unittest.TestCase):
    def test_reads_mongodb_configuration_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "MONGODB_URI": "mongodb://mongo.example:27017",
                "MONGODB_DB": "itsm_test",
                "MONGODB_SERVER_SELECTION_TIMEOUT_MS": "2500",
            },
        ):
            settings = MongoSettings.from_env()

        self.assertEqual(settings.uri, "mongodb://mongo.example:27017")
        self.assertEqual(settings.database_name, "itsm_test")
        self.assertEqual(settings.server_selection_timeout_ms, 2500)


class MongoCollectionTests(unittest.TestCase):
    def test_creates_missing_collections_and_returns_handles(self):
        database = MagicMock()
        database.list_collection_names.return_value = ["tickets", "knowledge"]
        database.__getitem__.side_effect = lambda name: f"collection:{name}"

        collections = ensure_collections(database)

        self.assertEqual(set(collections), set(COLLECTION_NAMES))
        self.assertEqual(
            collections["software_requests"], "collection:software_requests"
        )
        database.create_collection.assert_has_calls(
            [
                unittest.mock.call("chat"),
                unittest.mock.call("audit"),
                unittest.mock.call("software_requests"),
            ],
            any_order=True,
        )
        self.assertEqual(database.create_collection.call_count, 3)


class MongoLifespanTests(unittest.TestCase):
    def test_api_starts_when_mongodb_is_unavailable(self):
        client = MagicMock()
        client.__getitem__.return_value = MagicMock()
        settings = MongoSettings(
            uri="mongodb://localhost:27017",
            database_name="itsm_test",
            server_selection_timeout_ms=100,
        )

        with (
            patch("backend.app.main.MongoSettings.from_env", return_value=settings),
            patch("backend.app.main.create_mongo_client", return_value=client),
            patch(
                "backend.app.main.ensure_collections",
                side_effect=ServerSelectionTimeoutError("unavailable"),
            ),
        ):
            with TestClient(create_app()) as test_client:
                response = test_client.get("/api/v1/health")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(test_client.app.state.mongodb_status, "unavailable")

        client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
