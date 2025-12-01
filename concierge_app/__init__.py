from __future__ import annotations

import logging
import time
from pathlib import Path

from flask import Flask, g, request

from .agent import ConciergeAgent
from .config import settings
from services.hotel import HotelManager
from .observability import ObservabilityConfig, init_logging, setup_request_hooks
from .profiles import get_profile
from .routes import create_blueprint
from .tts import SpeechService


BASE_PATH = Path(__file__).resolve().parent


def create_app() -> Flask:
    logs_dir = BASE_PATH.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    request_logger = init_logging(
        ObservabilityConfig(
            requests_log_path=str(logs_dir / "requests.log"),
            level=logging.INFO,
        )
    )

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
    setup_request_hooks(app, request_logger)

    return app


__all__ = ["create_app", "settings"]
