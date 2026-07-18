from fastapi import APIRouter

from app.api.routes import admin, auth, company, explanation, match, products, rci, upload, whatsapp

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(company.router)
api_router.include_router(upload.router)
api_router.include_router(upload.documents_router)
api_router.include_router(rci.router)
api_router.include_router(match.router)
api_router.include_router(explanation.router)
api_router.include_router(admin.router)
api_router.include_router(whatsapp.router)
api_router.include_router(products.router)
api_router.include_router(products.orders_router)
