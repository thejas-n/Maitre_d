from __future__ import annotations

from pathlib import Path

from flask import Flask

from .agent import ConciergeAgent
from .config import settings
from .hotel import HotelManager
from .routes import create_blueprint
from .tts import SpeechService


BASE_PATH = Path(__file__).resolve().parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(BASE_PATH / "static"),
        static_url_path="/static",
        template_folder=str(BASE_PATH / "templates"),
    )

    manager = HotelManager()
    agent = ConciergeAgent(manager)
    speech_service = SpeechService()

    app.register_blueprint(create_blueprint(manager, agent, speech_service))
    return app


__all__ = ["create_app", "settings"]

