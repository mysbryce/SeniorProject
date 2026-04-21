from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

MessageRole = Literal["user", "assistant"]


def _now_iso() -> str:
    # AI generated comment: ใช้เวลา UTC เพื่อให้เรียงห้องและข้อความได้เสถียร
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Message:
    role: MessageRole
    content: str
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }


@dataclass
class Room:
    id: str
    name: str
    messages: list[Message] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def preview(self) -> str:
        if not self.messages:
            return "No messages yet"
        return self.messages[-1].content

    def summary(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "message_count": len(self.messages),
            "last_message_preview": self.preview(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class RoomManager:
    def __init__(self) -> None:
        # AI generated comment: เก็บห้องไว้ใน memory ก่อน ยังไม่ผูก database เพื่อให้แอปเบาและเรียบง่าย
        self._rooms: dict[str, Room] = {}
        self._create_default_room()

    def _create_default_room(self) -> Room:
        return self.create_room("New Chat")

    def get_rooms(self) -> list[dict[str, object]]:
        rooms = sorted(
            self._rooms.values(),
            key=lambda room: room.updated_at,
            reverse=True,
        )
        return [room.summary() for room in rooms]

    def create_room(self, name: str | None = None) -> dict[str, object]:
        room_name = (name or "New Chat").strip() or "New Chat"
        room = Room(id=uuid4().hex, name=room_name)
        self._rooms[room.id] = room
        return room.summary()

    def delete_room(self, room_id: str) -> bool:
        if room_id not in self._rooms:
            raise KeyError("Room not found")

        del self._rooms[room_id]
        if not self._rooms:
            self._create_default_room()
        return True

    def rename_room(self, room_id: str, new_name: str) -> dict[str, object]:
        room = self._get_room(room_id)
        room.name = new_name.strip() or "Untitled Chat"
        room.updated_at = _now_iso()
        return room.summary()

    def get_messages(self, room_id: str) -> list[dict[str, str]]:
        room = self._get_room(room_id)
        return [message.to_dict() for message in room.messages]

    def add_message(self, room_id: str, role: MessageRole, content: str) -> dict[str, str]:
        room = self._get_room(room_id)
        message = Message(role=role, content=content)
        room.messages.append(message)
        room.updated_at = _now_iso()
        return message.to_dict()

    def clear_room(self, room_id: str) -> bool:
        room = self._get_room(room_id)
        room.messages.clear()
        room.updated_at = _now_iso()
        return True

    def _get_room(self, room_id: str) -> Room:
        try:
            return self._rooms[room_id]
        except KeyError as exc:
            raise KeyError("Room not found") from exc
