from fastapi import APIRouter

from .health.health_handler import router as health_router
from .users.users_handler import router as users_router
from .prompts.prompts_handler import router as prompt_router

router: APIRouter = APIRouter(prefix="/au")
router.include_router(health_router)
router.include_router(users_router)
router.include_router(prompt_router)