import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "verse"
DEFAULT_TTS_FORMAT = "mp3"


class OpenAITTSError(RuntimeError):
    """Raised when OpenAI TTS synthesis fails."""


def synthesize_speech(
    text: str,
    *,
    model: Optional[str] = None,
    voice: Optional[str] = None,
    audio_format: str = DEFAULT_TTS_FORMAT,
    timeout: int = 120,
) -> bytes:
    """Generate speech audio from text using OpenAI's audio endpoint."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise OpenAITTSError("OPENAI_API_KEY not configured")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model_name = model or os.getenv("OPENAI_TTS_MODEL", DEFAULT_TTS_MODEL)
    voice_name = voice or os.getenv("OPENAI_TTS_VOICE", DEFAULT_TTS_VOICE)

    endpoint = f"{base_url}/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "input": text,
        "voice": voice_name,
        "format": audio_format,
    }

    logger.debug("Requesting TTS audio", extra={"model": model_name, "voice": voice_name})

    response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # noqa: BLE001
        logger.error("OpenAI TTS request failed: %s", exc)
        if response.content:
            logger.debug("TTS error payload: %s", response.content[:500])
        raise OpenAITTSError(str(exc)) from exc

    return response.content


__all__ = ["synthesize_speech", "OpenAITTSError"]
