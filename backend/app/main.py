import os
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.routes import api_router
from app.core.config import settings
from app.core.vector_db import ensure_trade_policies_collection
from app.models import document_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(database=client.get_default_database(), document_models=document_models)
    await ensure_trade_policies_collection()
    yield
    client.close()


app = FastAPI(title="Dhandha.com API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

app.include_router(api_router)


@app.get("/api/health")
async def health():
    return {"success": True, "status": "ok"}


# Single-origin deployment: serve the built frontend (frontend/dist, from
# `npm run build`) directly off this same FastAPI app, so there's no separate
# frontend host, no CORS setup, and the frontend's existing relative `/api`
# and `/uploads` fetch paths keep working unchanged. Registered last so the
# API routes and /uploads mount above always take precedence. No-op in local
# dev if the frontend hasn't been built yet.
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        # Anything else (client-side routes like /marketplace, direct deep
        # links) falls back to index.html so React Router can take over.
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
