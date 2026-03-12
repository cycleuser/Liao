"""Data models for OpenCode integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SessionStatus(str, Enum):
    """OpenCode session status."""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class EventType(str, Enum):
    """OpenCode event types."""

    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    SESSION_DELETED = "session.deleted"
    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    PART_CREATED = "part.created"
    PART_UPDATED = "part.updated"
    SERVER_CONNECTED = "server.connected"
    STATUS_CHANGED = "status.changed"


@dataclass
class OpenCodeProject:
    """OpenCode project information."""

    id: str
    path: str
    name: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenCodeProject:
        return cls(
            id=data.get("id", ""),
            path=data.get("path", ""),
            name=data.get("name", ""),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
        )


@dataclass
class OpenCodeSession:
    """OpenCode session information."""

    id: str
    project_id: str
    title: str = ""
    status: SessionStatus = SessionStatus.IDLE
    model: str = ""
    provider: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    parent_id: str | None = None
    is_shared: bool = False
    share_url: str | None = None
    message_count: int = 0
    cost: float = 0.0
    tokens_used: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenCodeSession:
        status_str = data.get("status", "idle").lower()
        try:
            status = SessionStatus(status_str)
        except ValueError:
            status = SessionStatus.IDLE

        return cls(
            id=data.get("id", ""),
            project_id=data.get("projectID", ""),
            title=data.get("title", ""),
            status=status,
            model=data.get("model", {}).get("modelID", "")
            if isinstance(data.get("model"), dict)
            else data.get("model", ""),
            provider=data.get("model", {}).get("providerID", "")
            if isinstance(data.get("model"), dict)
            else data.get("provider", ""),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
            parent_id=data.get("parentID"),
            is_shared=data.get("shared", False),
            share_url=data.get("shareURL"),
            message_count=data.get("messageCount", 0),
            cost=data.get("cost", 0.0),
            tokens_used=data.get("tokensUsed", 0),
        )


@dataclass
class OpenCodeMessagePart:
    """Part of an OpenCode message."""

    id: str
    type: str
    text: str = ""
    status: str = ""
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenCodeMessagePart:
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "text"),
            text=data.get("text", ""),
            status=data.get("status", ""),
            error=data.get("error"),
        )


@dataclass
class OpenCodeMessage:
    """OpenCode message."""

    id: str
    session_id: str
    role: str
    parts: list[OpenCodeMessagePart] = field(default_factory=list)
    created_at: datetime | None = None
    model: str = ""
    provider: str = ""
    cost: float = 0.0
    tokens_used: int = 0

    @property
    def text(self) -> str:
        """Get combined text from all parts."""
        return "\n".join(p.text for p in self.parts if p.text)

    @property
    def is_user(self) -> bool:
        return self.role == "user"

    @property
    def is_assistant(self) -> bool:
        return self.role == "assistant"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenCodeMessage:
        info = data.get("info", data)
        parts_data = data.get("parts", [])
        parts = [OpenCodeMessagePart.from_dict(p) for p in parts_data]

        return cls(
            id=info.get("id", ""),
            session_id=info.get("sessionID", ""),
            role=info.get("role", ""),
            parts=parts,
            created_at=_parse_datetime(info.get("createdAt")),
            model=info.get("model", {}).get("modelID", "")
            if isinstance(info.get("model"), dict)
            else info.get("model", ""),
            provider=info.get("model", {}).get("providerID", "")
            if isinstance(info.get("model"), dict)
            else "",
            cost=info.get("cost", 0.0),
            tokens_used=info.get("tokensUsed", 0),
        )


@dataclass
class OpenCodeEvent:
    """OpenCode real-time event."""

    type: str
    properties: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None

    @classmethod
    def from_sse(cls, event_type: str, data: dict[str, Any]) -> OpenCodeEvent:
        return cls(
            type=event_type,
            properties=data,
            timestamp=datetime.now(),
        )

    @property
    def is_message_event(self) -> bool:
        return self.type.startswith("message.") or self.type.startswith("part.")

    @property
    def is_session_event(self) -> bool:
        return self.type.startswith("session.")


@dataclass
class OpenCodeStatus:
    """OpenCode server status."""

    healthy: bool = False
    version: str = ""
    connected: bool = False
    running_sessions: int = 0
    current_project: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenCodeStatus:
        return cls(
            healthy=data.get("healthy", False),
            version=data.get("version", ""),
            connected=True,
        )


@dataclass
class OpenCodeTodo:
    """Todo item from OpenCode session."""

    id: str
    content: str
    status: str = "pending"
    priority: str = "medium"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenCodeTodo:
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
        )


def _parse_datetime(value: Any) -> datetime | None:
    """Parse datetime from various formats."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return None
