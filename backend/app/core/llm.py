import asyncio
from functools import lru_cache

from google import genai
from google.genai import errors as genai_errors

from app.core.config import settings

MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 1.5


@lru_cache
def get_genai_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return genai.Client(api_key=settings.gemini_api_key)


async def generate_content_with_retry(**kwargs):
    """Thin wrapper around client.aio.models.generate_content that retries once or
    twice on Gemini's transient 5xx errors — observed occasionally in practice —
    before giving up and letting the caller handle the failure."""
    client = get_genai_client()

    for attempt in range(MAX_RETRIES + 1):
        try:
            return await client.aio.models.generate_content(**kwargs)
        except genai_errors.ServerError:
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
