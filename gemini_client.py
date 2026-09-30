"""Thin wrapper around the Google Gen AI SDK shared by all generators."""
from google import genai
from google.genai import types

from app import config


class GeminiError(RuntimeError):
    """Raised for any problem talking to Gemini (missing key, network, empty reply)."""


_client = None


def _get_client() -> "genai.Client":
    global _client
    if not config.GEMINI_API_KEY:
        raise GeminiError(
            "Gemini API key is missing. Add GEMINI_API_KEY to your .env file and restart the server."
        )
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def generate_text(model: str, prompt: str, temperature: float = 0.7) -> str:
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
    except Exception as exc:  # SDK raises several error types; surface one clean error
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    text = (response.text or "").strip()
    if not text:
        raise GeminiError("Gemini returned an empty response. Please try again.")
    return text
