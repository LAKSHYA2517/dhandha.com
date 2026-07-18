import asyncio
import json
import re
import uuid

from google.genai import types
from qdrant_client.models import PointStruct

from app.ai_services.json_utils import parse_json_response
from app.core.config import settings
from app.core.llm import generate_content_with_retry
from app.core.vector_db import TRADE_POLICIES_COLLECTION, get_embedding_model, get_qdrant_client

CHUNK_SIZE = 500
TOP_K = 3

EVALUATION_PROMPT = """Based on this trade policy:
{context}

Does this vendor comply?

Vendor profile:
{vendor_data}

Trade route: {trade_route}

Provide a 'Regulatory Fit Score' (0.0 to 1.0) and a brief 2-sentence explanation of why.
Respond as raw JSON only, matching this schema:
{{"regulatory_fit_score": <float 0.0-1.0>, "explanation": "<brief 2-sentence explanation>"}}"""


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks = []
    for paragraph in paragraphs:
        for i in range(0, len(paragraph), chunk_size):
            chunks.append(paragraph[i:i + chunk_size])
    return chunks


async def _embed(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = await asyncio.to_thread(model.encode, texts)
    return [embedding.tolist() for embedding in embeddings]


async def ingest_policy(text: str) -> int:
    chunks = _chunk_text(text)
    vectors = await _embed(chunks)

    points = [
        PointStruct(id=uuid.uuid4().hex, vector=vector, payload={"text": chunk})
        for chunk, vector in zip(chunks, vectors)
    ]

    client = get_qdrant_client()
    await client.upsert(collection_name=TRADE_POLICIES_COLLECTION, points=points)
    return len(points)


async def _retrieve_context(trade_route: str, top_k: int = TOP_K) -> list[str]:
    [query_vector] = await _embed([trade_route])

    client = get_qdrant_client()
    response = await client.query_points(
        collection_name=TRADE_POLICIES_COLLECTION,
        query=query_vector,
        limit=top_k,
    )
    return [point.payload["text"] for point in response.points]


async def evaluate_compliance(vendor_data: dict, trade_route: str) -> dict:
    context_chunks = await _retrieve_context(trade_route)
    context = "\n---\n".join(context_chunks) if context_chunks else "No specific trade policy on file for this route."

    prompt = EVALUATION_PROMPT.format(
        context=context,
        vendor_data=json.dumps(vendor_data),
        trade_route=trade_route,
    )

    response = await generate_content_with_retry(
        model=settings.gemini_text_model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    result = parse_json_response(response.text)
    return {
        "regulatory_fit_score": float(result["regulatory_fit_score"]),
        "explanation": str(result["explanation"]),
    }
