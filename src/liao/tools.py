"""
Liao - OpenAI function-calling tool definitions.

Provides TOOLS list and dispatch() for LLM agent integration.
"""

from __future__ import annotations

import json
from typing import Any

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "liao_list_windows",
            "description": (
                "List visible desktop windows. Optionally filter to only "
                "show recognised chat application windows (WeChat, QQ, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_only": {
                        "type": "boolean",
                        "description": "Only return chat application windows.",
                        "default": False,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "liao_run_automation",
            "description": (
                "Run headless GUI automation on a target desktop window. "
                "Uses vision/screenshot analysis and an LLM to read the "
                "chat interface, generate responses, and send them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Target window handle (from liao_list_windows).",
                    },
                    "title": {
                        "type": "string",
                        "description": "Target window title (partial match).",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "System prompt for the conversation agent.",
                        "default": "You are a friendly assistant. Respond naturally and briefly.",
                    },
                    "rounds": {
                        "type": "integer",
                        "description": "Number of conversation rounds to run.",
                        "default": 5,
                    },
                    "provider": {
                        "type": "string",
                        "enum": ["ollama", "openai", "anthropic"],
                        "description": "LLM provider.",
                        "default": "ollama",
                    },
                    "model": {
                        "type": "string",
                        "description": "LLM model name.",
                    },
                    "base_url": {
                        "type": "string",
                        "description": "LLM API URL.",
                        "default": "http://localhost:11434",
                    },
                },
                "required": [],
            },
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any] | str) -> dict:
    """Dispatch a tool call to the appropriate API function."""
    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    if name == "liao_list_windows":
        from .api import list_windows

        result = list_windows(**arguments)
        return result.to_dict()

    if name == "liao_run_automation":
        from .api import run_automation

        result = run_automation(**arguments)
        return result.to_dict()

    raise ValueError(f"Unknown tool: {name}")
