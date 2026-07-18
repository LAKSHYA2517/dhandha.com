from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer

from app.core.config import settings

TRADE_POLICIES_COLLECTION = "trade_policies"
EMBEDDING_DIM = 384
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    if settings.qdrant_url:
        return AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return AsyncQdrantClient(location=":memory:")


async def ensure_trade_policies_collection() -> None:
    client = get_qdrant_client()
    if not await client.collection_exists(TRADE_POLICIES_COLLECTION):
        await client.create_collection(
            collection_name=TRADE_POLICIES_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
