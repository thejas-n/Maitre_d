from __future__ import annotations

import base64
from typing import Optional

from google.cloud import texttospeech


class SpeechService:
    """Wrapper around Google Cloud Text-to-Speech."""

    def __init__(self) -> None:
        try:
            self._client = texttospeech.TextToSpeechClient()
        except Exception as exc:  # pragma: no cover - depends on credentials
            print(f"TTS Init failed: {exc}")
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def synthesize(self, text: str, voice: str = "en-US-Chirp-HD-F") -> Optional[str]:
        if not self._client:
            return None

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = self._client.synthesize_speech(
            input=synthesis_input, voice=voice_params, audio_config=audio_config
        )
        return base64.b64encode(response.audio_content).decode("utf-8")

