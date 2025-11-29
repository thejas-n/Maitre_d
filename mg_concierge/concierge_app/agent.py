from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Dict, Any

import google.generativeai as genai

from .config import settings
from .profiles import ConciergeProfile

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = logging.getLogger("concierge.agent")
if not _logger.handlers:
    handler = logging.FileHandler(LOG_DIR / "agent.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)


class ConciergeAgent:
    """Thin wrapper around the Gemini model with function-calling tools."""

    def __init__(self, manager, profile: ConciergeProfile) -> None:
        self.manager = manager
        self.profile = profile
        self.model: Optional[genai.GenerativeModel] = None
        self.chat_session = None

    # --------------------------------------------------------------------- tools
    def _build_tools(self) -> List[Callable]:
        manager = self.manager

        def check_availability_tool(party_size: int) -> str:
            table = manager.check_availability(party_size)
            if table:
                return f"Table {table.table_id} is available for {party_size} guests."
            return "No table available."

        def add_guest_tool(name: str, party_size: int, action: str = "check_in") -> str:
            action = (action or "check_in").lower()
            if action == "check_in":
                table = manager.check_availability(party_size)
                if not table:
                    return f"No table available for {party_size} guests. Use action='waitlist' to add them to the waitlist."
                table_id = manager.assign_table(table, name)
                return f"Assigned table {table_id} to {name}."
            if action == "waitlist":
                position = manager.add_to_waitlist(name, party_size)
                # Fetch the updated waitlist to get the ETA
                status = manager.get_status()
                eta = None
                for entry in status["waitlist"]:
                    if entry["name"] == name and entry["party_size"] == party_size:
                        eta = entry.get("eta_minutes")
                        break
                if eta is not None:
                    return f"Added {name} to waitlist at position {position}. Estimated wait time: {eta} minutes."
                return f"Added {name} to waitlist at position {position}."
            return "Invalid action. Use 'check_in' to assign a table or 'waitlist' to add to waitlist."

        def get_status_tool() -> str:
            return str(manager.get_status())

        return [check_availability_tool, add_guest_tool, get_status_tool]

    # ------------------------------------------------------------------ lifecycle
    def _init_model(self) -> None:
        genai.configure(api_key=settings.google_api_key)
        tools = self._build_tools()

        preferred = self.profile.model or "gemini-2.5-flash"
        tried = set()
        for model_name in (preferred, "gemini-1.5-flash-latest", "gemini-1.5-flash"):
            if model_name in tried:
                continue
            tried.add(model_name)
            try:
                self.model = genai.GenerativeModel(model_name=model_name, tools=tools)
                self.chat_session = self.model.start_chat(enable_automatic_function_calling=True)
                self.chat_session.send_message(
                    """
                    You are the Concierge at MG Cafe. Follow this protocol:
                    1. Greet the guest warmly.
                    2. Ask for their name and party size. Ensure you have the guest's name before proceeding with check-in or waitlist.
                    3. Use check_availability_tool to check if a table is available for their party size.
                    4. If a table is available: Use add_guest_tool with action='check_in' to assign the table.
                    5. If NO table is available: Use add_guest_tool with action='waitlist' to add them to the waitlist. Always add guests to waitlist when no tables are available - do not just tell them there are no tables. When a guest is added to the waitlist, **you MUST inform them of their position and the EXACT estimated wait time as provided by the tool.**
                    6. After assigning a table or adding to waitlist, confirm the action politely and end the interaction.
                    7. Keep responses brief, friendly, and speak as the on-screen avatar.
                    
                    IMPORTANT: When no tables are available, you MUST call add_guest_tool with action='waitlist' to add the guest to the waitlist. If the name is not provided, you MUST ask for it before calling add_guest_tool. Never just say "no tables available" without adding them to the waitlist. When providing waitlist information, **you MUST use the estimated wait time in minutes returned by the tool, do not invent or approximate times.**
                    """
                )
                return
            except Exception as exc:  # pragma: no cover - best effort
                print(f"Failed to init {model_name}: {exc}")

        raise RuntimeError("Unable to initialize any Gemini model.")

    # --------------------------------------------------------------------- public
    def respond(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        if not self.chat_session:
            self._init_model()
        start = time.perf_counter()
        response = self.chat_session.send_message(message)
        elapsed_ms = (time.perf_counter() - start) * 1000
        _logger.info(
            "model=%s chars=%d duration_ms=%.1f",
            getattr(self.model, "model_name", "unknown"),
            len(message or ""),
            elapsed_ms,
        )
        _logger.debug("user=%r reply=%r", message, response.text)
        event = self.manager.consume_event()
        return response.text, event
