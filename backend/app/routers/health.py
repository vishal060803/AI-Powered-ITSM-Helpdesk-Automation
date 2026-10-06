from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["health"])
async def api_root():
    return {
        "status": "ok",
        "app": "ai-itsm-backend",
        "message": "API is ready.",
    }


@router.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "service": "ai-itsm-backend",
        "message": "Backend is up and running.",
    }
