from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.company import router as company_router
from app.api.routes.explanation import router as explanation_router
from app.api.routes.match import router as match_router
from app.api.routes.product import orders_router, router as product_router
from app.api.routes.rci import router as rci_router
from app.api.routes.upload import documents_router, router as upload_router
from app.api.routes.whatsapp import router as whatsapp_router

api_router = APIRouter()

for router in (
    auth_router,
    company_router,
    product_router,
    orders_router,
    upload_router,
    documents_router,
    rci_router,
    match_router,
    explanation_router,
    admin_router,
    whatsapp_router,
):
    api_router.include_router(router)
