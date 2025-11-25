from __future__ import annotations

from typing import Callable, List, Optional, Tuple, Dict, Any

import google.generativeai as genai

from .config import settings


class ConciergeAgent:
    """Thin wrapper around the Gemini model with function-calling tools."""

    def __init__(self, manager) -> None:
        self.manager = manager
        self.model: Optional[genai.GenerativeModel] = None
        self.chat_session = None
        self._init_model()

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
                return f"Added {name} to waitlist at position {position}."
            return "Invalid action. Use 'check_in' to assign a table or 'waitlist' to add to waitlist."

        def get_status_tool() -> str:
            return str(manager.get_status())

        return [check_availability_tool, add_guest_tool, get_status_tool]

    # ------------------------------------------------------------------ lifecycle
    def _init_model(self) -> None:
        genai.configure(api_key=settings.google_api_key)
        tools = self._build_tools()

        for model_name in ("gemini-2.0-flash-exp", "gemini-1.5-flash-latest", "gemini-1.5-flash"):
            try:
                self.model = genai.GenerativeModel(model_name=model_name, tools=tools)
                self.chat_session = self.model.start_chat(enable_automatic_function_calling=True)
                self.chat_session.send_message(
                    """
                    You are the Concierge at MG Cafe. Follow this protocol:
                    1. Greet the guest warmly.
                    2. Ask for their name and party size.
                    3. Use check_availability_tool to check if a table is available for their party size.
                    4. If a table is available: Use add_guest_tool with action='check_in' to assign the table.
                    5. If NO table is available: Use add_guest_tool with action='waitlist' to add them to the waitlist. Always add guests to waitlist when no tables are available - do not just tell them there are no tables.
                    6. After assigning a table or adding to waitlist, confirm the action politely and end the interaction.
                    7. Keep responses brief, friendly, and speak as the on-screen avatar.
                    
                    IMPORTANT: When no tables are available, you MUST call add_guest_tool with action='waitlist' to add the guest to the waitlist. Never just say "no tables available" without adding them to the waitlist.
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
        response = self.chat_session.send_message(message)
        event = self.manager.consume_event()
        return response.text, event

