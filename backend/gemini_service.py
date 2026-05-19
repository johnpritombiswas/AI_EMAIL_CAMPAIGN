import logging
import time

from google import genai

from config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_MODEL

logger = logging.getLogger(__name__)

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in backend/.env")

client = genai.Client(api_key=GEMINI_API_KEY)
active_model = GEMINI_MODEL


def generate_text(contents: str, retries: int = 3, model: str | None = None) -> str:
    global active_model
    selected_model = model or active_model

    for attempt in range(retries):
        try:
            response = client.models.generate_content(model=selected_model, contents=contents)
            return response.text.strip()
        except Exception as exc:
            message = str(exc)
            logger.warning("Gemini call failed on attempt %s: %s", attempt + 1, message)
            if "UNAVAILABLE" in message and attempt < retries - 1:
                time.sleep(5)
                continue
            if "RESOURCE_EXHAUSTED" in message and selected_model != GEMINI_FALLBACK_MODEL:
                active_model = GEMINI_FALLBACK_MODEL
                logger.info("Switching Gemini requests to fallback model")
                return generate_text(contents, retries=1, model=GEMINI_FALLBACK_MODEL)
            raise


def list_model_names() -> list[str]:
    return [model.name for model in client.models.list()]
