"""Tests for OpenCode integration module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from liao.opencode.models import (
    OpenCodeSession,
    OpenCodeMessage,
    OpenCodeEvent,
    OpenCodeProject,
    OpenCodeStatus,
    OpenCodeTodo,
    SessionStatus,
)


class TestOpenCodeModels:
    """Tests for OpenCode data models."""

    def test_session_from_dict(self):
        """Test creating session from API response."""
        data = {
            "id": "test-123",
            "projectID": "proj-1",
            "title": "Test Session",
            "status": "running",
            "model": {"providerID": "anthropic", "modelID": "claude-3"},
        }
        session = OpenCodeSession.from_dict(data)

        assert session.id == "test-123"
        assert session.project_id == "proj-1"
        assert session.title == "Test Session"
        assert session.status == SessionStatus.RUNNING
        assert session.model == "claude-3"
        assert session.provider == "anthropic"

    def test_session_status_enum(self):
        """Test session status values."""
        assert SessionStatus.IDLE.value == "idle"
        assert SessionStatus.RUNNING.value == "running"
        assert SessionStatus.COMPLETED.value == "completed"

    def test_message_from_dict(self):
        """Test creating message from API response."""
        data = {
            "info": {
                "id": "msg-1",
                "sessionID": "sess-1",
                "role": "user",
            },
            "parts": [
                {"id": "p1", "type": "text", "text": "Hello"},
            ],
        }
        message = OpenCodeMessage.from_dict(data)

        assert message.id == "msg-1"
        assert message.role == "user"
        assert message.is_user is True
        assert message.is_assistant is False
        assert message.text == "Hello"

    def test_message_text_property(self):
        """Test message text combines all parts."""
        data = {
            "info": {"id": "m1", "role": "assistant"},
            "parts": [
                {"id": "p1", "type": "text", "text": "Hello"},
                {"id": "p2", "type": "text", "text": "World"},
            ],
        }
        message = OpenCodeMessage.from_dict(data)

        assert message.text == "Hello\nWorld"

    def test_event_from_sse(self):
        """Test creating event from SSE data."""
        event = OpenCodeEvent.from_sse("session.created", {"id": "sess-1", "title": "New"})

        assert event.type == "session.created"
        assert event.properties["id"] == "sess-1"
        assert event.is_session_event is True
        assert event.is_message_event is False

    def test_event_is_message_event(self):
        """Test event message detection."""
        event = OpenCodeEvent.from_sse("message.created", {})
        assert event.is_message_event is True

        event = OpenCodeEvent.from_sse("part.updated", {})
        assert event.is_message_event is True

    def test_project_from_dict(self):
        """Test creating project from API response."""
        project = OpenCodeProject.from_dict(
            {
                "id": "proj-1",
                "path": "/home/user/project",
                "name": "My Project",
            }
        )

        assert project.id == "proj-1"
        assert project.path == "/home/user/project"
        assert project.name == "My Project"

    def test_status_from_dict(self):
        """Test creating status from API response."""
        status = OpenCodeStatus.from_dict(
            {
                "healthy": True,
                "version": "1.0.0",
            }
        )

        assert status.healthy is True
        assert status.version == "1.0.0"
        assert status.connected is True

    def test_todo_from_dict(self):
        """Test creating todo from API response."""
        todo = OpenCodeTodo.from_dict(
            {
                "id": "todo-1",
                "content": "Write tests",
                "status": "in_progress",
                "priority": "high",
            }
        )

        assert todo.id == "todo-1"
        assert todo.content == "Write tests"
        assert todo.status == "in_progress"
        assert todo.priority == "high"


class TestOpenCodeClient:
    """Tests for OpenCode client."""

    def test_client_initialization(self):
        """Test client initialization."""
        from liao.opencode import OpenCodeClient

        client = OpenCodeClient()
        # Client may or may not find CLI depending on system
        assert hasattr(client, "is_available")
        assert hasattr(client, "list_sessions")

    @patch("subprocess.run")
    def test_is_available_with_cli(self, mock_run):
        """Test is_available when CLI is found."""
        from liao.opencode.client import OpenCodeClient

        # Mock the ps command for server detection
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        client = OpenCodeClient()
        # The result depends on whether CLI is found on the system
        assert isinstance(client.is_available(), bool)

    def test_get_status(self):
        """Test getting OpenCode status."""
        from liao.opencode import OpenCodeClient

        client = OpenCodeClient()
        status = client.get_status()

        assert hasattr(status, "healthy")
        assert hasattr(status, "connected")


class TestOpenCodeInfo:
    """Tests for OpenCode info function."""

    def test_get_opencode_info(self):
        """Test getting OpenCode info."""
        from liao.opencode.client import get_opencode_info

        info = get_opencode_info()

        assert "available" in info
        assert "cli_path" in info
        assert "server_running" in info
        assert isinstance(info["available"], bool)
