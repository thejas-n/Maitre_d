from __future__ import annotations

import base64
import logging
import time
from pathlib import Path
from typing import Optional

from google.cloud import texttospeech

from .config import settings


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = logging.getLogger("concierge.tts")
if not _logger.handlers:
    handler = logging.FileHandler(LOG_DIR / "tts.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)


class SpeechService:
    """Wrapper around Google Cloud Text-to-Speech with timing/logging."""

    def __init__(self, default_voice: str = "en-IN-Standard-E") -> None:
        self._client: Optional[texttospeech.TextToSpeechClient] = None
        self.default_voice = default_voice

    def _init_client(self) -> None:
        try:
            self._client = texttospeech.TextToSpeechClient()
        except Exception as exc:  # pragma: no cover - depends on credentials
            _logger.error("TTS client init failed: %s", exc)
            self._client = None

    def _ensure_client(self) -> bool:
        if not self._client:
            self._init_client()
        return self._client is not None

    @property
    def available(self) -> bool:
        return self._ensure_client()

    def synthesize(self, text: str, voice: str | None = None) -> Optional[str]:
        if not self._ensure_client():
            return None

        try:
            start = time.perf_counter()
            voice = voice or self.default_voice
            synthesis_input = texttospeech.SynthesisInput(text=text)
            lang_parts = voice.split("-")
            language_code = "-".join(lang_parts[:2]) if len(lang_parts) >= 2 else "en-US"
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            response = self._client.synthesize_speech(
                input=synthesis_input, voice=voice_params, audio_config=audio_config
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
            _logger.info(
                "voice=%s lang=%s chars=%d audio_bytes=%d duration_ms=%.1f",
                voice,
                language_code,
                len(text),
                len(response.audio_content),
                elapsed_ms,
            )
            _logger.debug("audio_base64_first64=%s", audio_b64[:64])
            return audio_b64
        except Exception as exc:  # pragma: no cover - runtime
            _logger.error("TTS synth failed: %s", exc)
            return None
