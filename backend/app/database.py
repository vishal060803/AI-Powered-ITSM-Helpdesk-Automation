import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

COLLECTION_NAMES = (
    "tickets",
    "knowledge",
    "chat",
    "audit",
    "software_requests",
)


@dataclass(frozen=True)
class MongoSettings:
    uri: str
    database_name: str
    server_selection_timeout_ms: int

    @classmethod
    def from_env(cls) -> "MongoSettings":
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017").strip()
        database_name = os.getenv("MONGODB_DB", "itsm_ai").strip()

        try:
            timeout_ms = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "2000"))
        except ValueError as error:
            raise ValueError(
                "MONGODB_SERVER_SELECTION_TIMEOUT_MS must be a positive integer."
            ) from error

        if not uri:
            raise ValueError("MONGODB_URI must not be empty.")
        if not database_name:
            raise ValueError("MONGODB_DB must not be empty.")
        if timeout_ms < 1:
            raise ValueError(
                "MONGODB_SERVER_SELECTION_TIMEOUT_MS must be a positive integer."
            )

        return cls(
            uri=uri,
            database_name=database_name,
            server_selection_timeout_ms=timeout_ms,
        )


def create_mongo_client(settings: MongoSettings) -> MongoClient:
    return MongoClient(
        settings.uri,
        serverSelectionTimeoutMS=settings.server_selection_timeout_ms,
        appname="ai-itsm-backend",
    )


def get_collection_handles(database: Database[Any]) -> dict[str, Any]:
    return {name: database[name] for name in COLLECTION_NAMES}


def ensure_collections(database: Database[Any]) -> dict[str, Any]:
    existing_collections = set(database.list_collection_names())
    for name in COLLECTION_NAMES:
        if name not in existing_collections:
            database.create_collection(name)

    return get_collection_handles(database)
