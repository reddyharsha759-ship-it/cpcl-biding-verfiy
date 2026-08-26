from fastapi import APIRouter
from app.api.v1.endpoints import gem_webhook, health, rulebook, verification

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(verification.router)
api_router.include_router(rulebook.router)
api_router.include_router(gem_webhook.router)
