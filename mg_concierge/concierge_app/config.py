from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PORT = int(os.getenv("PORT", "5001"))
CONCIERGE_ID = os.getenv("CONCIERGE_ID", "mg_cafe")


class Settings:
    """Runtime configuration container."""

    def __init__(self) -> None:
        self.google_api_key = GOOGLE_API_KEY
        self.google_credentials = GOOGLE_APPLICATION_CREDENTIALS
        self.port = PORT
        self.concierge_id = CONCIERGE_ID

        if not self.google_api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is required. Please set it in the environment or .env file."
            )


settings = Settings()
