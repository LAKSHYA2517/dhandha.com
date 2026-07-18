import logging

from app.core.config import settings
from app.core.llm import generate_content_with_retry

logger = logging.getLogger(__name__)

LOCALIZE_PROMPT = """Translate the following message into {language}. Keep it short, friendly, and natural — \
not a literal word-for-word translation. Respond with only the translated message text — no commentary, \
no quotation marks, no original-language text.

Message: {message}"""


async def localize_message(message: str, language: str | None) -> str:
    if not language or language.strip().lower() in {"english", "en"}:
        return message

    try:
        response = await generate_content_with_retry(
            model=settings.gemini_text_model,
            contents=LOCALIZE_PROMPT.format(language=language, message=message),
        )
        return response.text.strip()
    except Exception:
        # Translation is a nice-to-have on top of a message that must go out
        # regardless — fall back to the original (English) text rather than
        # let a transient LLM error silence the reply entirely.
        logger.exception("Failed to localize message into %s; sending original text", language)
        return message


TRANSLATE_TO_ENGLISH_PROMPT = """Translate the following text into English. If it's already in English, \
return it unchanged. Keep proper nouns (brand/company names) recognizable — transliterate to Latin script \
rather than translating their meaning. Respond with only the translated text — no commentary, no quotation marks.

Text: {text}"""


async def translate_to_english(text: str, source_language: str | None) -> str:
    """Used for anything a vendor types via WhatsApp (in whatever language they
    chose) that gets persisted and shown on the website — the website is
    English-only regardless of chat language."""
    if not text or not source_language or source_language.strip().lower() in {"english", "en"}:
        return text

    try:
        response = await generate_content_with_retry(
            model=settings.gemini_text_model,
            contents=TRANSLATE_TO_ENGLISH_PROMPT.format(text=text),
        )
        return response.text.strip()
    except Exception:
        logger.exception("Failed to translate '%s' to English; storing original text", text)
        return text
