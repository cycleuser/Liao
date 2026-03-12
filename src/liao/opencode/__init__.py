"""OpenCode integration module.

Provides client for interacting with OpenCode server, enabling:
- Session management
- Real-time event streaming
- Message sending and receiving
- Progress monitoring
"""

from .client import OpenCodeClient
from .models import (
    OpenCodeSession,
    OpenCodeMessage,
    OpenCodeEvent,
    OpenCodeProject,
    OpenCodeStatus,
)

__all__ = [
    "OpenCodeClient",
    "OpenCodeSession",
    "OpenCodeMessage",
    "OpenCodeEvent",
    "OpenCodeProject",
    "OpenCodeStatus",
]
