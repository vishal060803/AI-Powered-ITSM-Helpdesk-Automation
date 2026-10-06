import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError

try:
    from app.database import (
        MongoSettings,
        create_mongo_client,
        ensure_collections,
        get_collection_handles,
    )
    from app.routers import health as health_router
    from app.routers import knowledge as knowledge_router
except ImportError:  # pragma: no cover - fallback for repo-root imports during tests
    from backend.app.database import (
        MongoSettings,
        create_mongo_client,
        ensure_collections,
        get_collection_handles,
    )
    from backend.app.routers import health as health_router
    from backend.app.routers import knowledge as knowledge_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = None
    app.state.mongo_client = None
    app.state.mongo_database = None
    app.state.mongo_collections = {}
    app.state.mongodb_status = "unavailable"

    try:
        settings = MongoSettings.from_env()
        client = create_mongo_client(settings)
        database = client[settings.database_name]
        app.state.mongo_client = client
        app.state.mongo_database = database
        app.state.mongo_collections = get_collection_handles(database)

        try:
            app.state.mongo_collections = await asyncio.to_thread(
                ensure_collections, database
            )
        except PyMongoError as error:
            logger.warning(
                "MongoDB is unavailable; continuing without persistence (%s).",
                type(error).__name__,
            )
        else:
            app.state.mongodb_status = "connected"
    except (PyMongoError, ValueError) as error:
        logger.warning(
            "MongoDB configuration could not be initialized (%s).",
            type(error).__name__,
        )

    try:
        yield
    finally:
        if client is not None:
            client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI ITSM Backend",
        version="0.1.0",
        description="AI-powered IT Service Management backend for knowledge, tickets, and automation workflows.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router.router, prefix="/api/v1", tags=["health"])
    app.include_router(knowledge_router.router, prefix="/api/v1/knowledge", tags=["knowledge"])
    return app


app = create_app()


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": "ai-itsm-backend",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def legacy_health_check():
    return {
        "status": "ok",
        "service": "ai-itsm-backend",
        "message": "Backend is up and running.",
    }
