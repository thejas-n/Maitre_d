from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ConciergeProfile:
    id: str
    display_name: str
    description: str
    model: str = "gemini-2.5-flash"
    tts_voice: str = "en-IN-Standard-E"
    avatars: Dict[str, str] = field(default_factory=dict)


DEFAULT_PROFILE_ID = "mg_cafe"

_PROFILES: Dict[str, ConciergeProfile] = {
    "mg_cafe": ConciergeProfile(
        id="mg_cafe",
        display_name="MG Cafe Concierge",
        description="Friendly host for MG Cafe.",
        model="gemini-2.5-flash",
        tts_voice="en-IN-Standard-E",
        avatars={
            "idle": "avatar-idle.mp4",
            "listening": "avatar-listening.mp4",
            "speaking": "avatar-speaking.mp4",
        },
    ),
}


def get_profile(profile_id: str | None) -> ConciergeProfile:
    if profile_id and profile_id in _PROFILES:
        return _PROFILES[profile_id]
    return _PROFILES[DEFAULT_PROFILE_ID]
