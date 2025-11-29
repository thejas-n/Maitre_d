from __future__ import annotations

from pathlib import Path

from flask import Flask

from .agent import ConciergeAgent
from .config import settings
from services.hotel import HotelManager
from .profiles import get_profile
from .routes import create_blueprint
from .tts import SpeechService


BASE_PATH = Path(__file__).resolve().parent


def create_app() -> Flask:
    profile = get_profile(settings.concierge_id)
    app = Flask(
        __name__,
        static_folder=str(BASE_PATH / "static"),
        static_url_path="/static",
        template_folder=str(BASE_PATH / "templates"),
    )

    manager = HotelManager()
    agent = ConciergeAgent(manager, profile=profile)
    speech_service = SpeechService(default_voice=profile.tts_voice)

    app.register_blueprint(create_blueprint(manager, agent, speech_service, profile))
    return app


__all__ = ["create_app", "settings"]
