from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Table:
    table_id: str
    seats: int
    table_type: str
    status: str = "free"
    guest_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.table_id,
            "seats": self.seats,
            "type": self.table_type,
            "status": self.status,
            "guest_name": self.guest_name,
        }


@dataclass
class WaitlistEntry:
    name: str
    party_size: int


@dataclass
class HotelManager:
    tables: List[Table] = field(default_factory=list)
    waitlist: List[WaitlistEntry] = field(default_factory=list)
    last_event: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.tables:
            return
        # Bar seats
        for i in range(5):
            self.tables.append(Table(f"BAR-{i+1}", 1, "bar"))
        # 2,4,6 seaters
        for prefix, count, seats in (("T2", 5, 2), ("T4", 5, 4), ("T6", 2, 6)):
            for i in range(count):
                self.tables.append(Table(f"{prefix}-{i+1}", seats, "standard"))

    # --- Helpers -----------------------------------------------------------------
    def _find_table(self, table_id: str) -> Optional[Table]:
        return next((t for t in self.tables if t.table_id == table_id), None)

    def _record_event(self, event: Dict[str, Any]) -> None:
        self.last_event = event

    def consume_event(self) -> Optional[Dict[str, Any]]:
        event, self.last_event = self.last_event, None
        return event

    # --- Public API ---------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        return {
            "tables": [t.to_dict() for t in self.tables],
            "waitlist": [entry.__dict__ for entry in self.waitlist],
        }

    def check_availability(self, party_size: int) -> Optional[Table]:
        return next(
            (t for t in self.tables if t.status == "free" and t.seats >= party_size),
            None,
        )

    def assign_table(self, table: Table, guest_name: str) -> str:
        table.status = "occupied"
        table.guest_name = guest_name
        self._record_event(
            {
                "type": "table_assigned",
                "table": table.table_id,
                "name": guest_name,
                "party_size": table.seats,
            }
        )
        return table.table_id

    def add_to_waitlist(self, name: str, party_size: int) -> int:
        self.waitlist.append(WaitlistEntry(name=name, party_size=party_size))
        position = len(self.waitlist)
        self._record_event(
            {
                "type": "waitlist",
                "name": name,
                "party_size": party_size,
                "position": position,
            }
        )
        return position

    def checkout_and_fill_waitlist(self, table_id: str) -> Dict[str, Any]:
        table = self._find_table(table_id)
        if not table:
            return {"success": False, "message": "Table not found."}

        previous_guest = table.guest_name
        table.status = "free"
        table.guest_name = None

        assigned_guest: Optional[WaitlistEntry] = None
        for idx, entry in enumerate(list(self.waitlist)):
            if entry.party_size <= table.seats:
                assigned_guest = self.waitlist.pop(idx)
                table.status = "occupied"
                table.guest_name = assigned_guest.name
                break

        result: Dict[str, Any] = {
            "success": True,
            "table": table.table_id,
            "cleared_guest": previous_guest,
            "assigned_guest": assigned_guest.__dict__ if assigned_guest else None,
        }

        if assigned_guest:
            self._record_event(
                {
                    "type": "table_assigned",
                    "table": table.table_id,
                    "name": assigned_guest.name,
                    "party_size": assigned_guest.party_size,
                }
            )
            result["announcement"] = (
                f"Party for {assigned_guest.name}, your table {table.table_id} is ready!"
            )

        return result

