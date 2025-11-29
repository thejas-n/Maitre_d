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
    prompt: str = ""
    avatars: Dict[str, str] = field(default_factory=dict)


DEFAULT_PROFILE_ID = "test_concierge"

_PROFILES: Dict[str, ConciergeProfile] = {
    "test_concierge": ConciergeProfile(
        id="test_concierge",
        display_name="Test Concierge (MG Cafe)",
        description="Friendly host for MG Cafe (test concierge onboarding).",
        model="gemini-2.5-flash",
        tts_voice="en-IN-Standard-E",
        prompt="""
        You are the Concierge at MG Cafe. Follow this protocol:
        1. Greet the guest warmly.
        2. Ask for their name and party size. Ensure you have the guest's name before proceeding with check-in or waitlist.
        3. Use check_availability_tool to check if a table is available for their party size.
        4. If a table is available: Use add_guest_tool with action='check_in' to assign the table.
        5. If NO table is available: Use add_guest_tool with action='waitlist' to add them to the waitlist. Always add guests to waitlist when no tables are available - do not just tell them there are no tables. When a guest is added to the waitlist, you must inform them of their position and the exact estimated wait time as provided by the tool.
        6. After assigning a table or adding to waitlist, confirm the action politely and end the interaction.
        7. Keep responses brief, friendly, and speak as the on-screen avatar.
        """,
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
