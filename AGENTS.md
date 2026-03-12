# AGENTS.md - Coding Agent Guidelines for Liao

This document provides guidance for AI coding agents working on the Liao codebase.

## Project Overview

Liao is a vision-based GUI interaction assistant with LLM integration. It automates desktop chat applications using OCR and large language models. Key components:
- `src/liao/core/` - Core modules (window management, screenshot, input simulation, smart automation)
- `src/liao/llm/` - LLM client implementations (Ollama, OpenAI, Anthropic)
- `src/liao/agent/` - Agent workflow, conversation parsing, prompts
- `src/liao/gui/` - PySide6 GUI components
- `src/liao/models/` - Data models (WindowInfo, ChatMessage, etc.)
- `src/liao/knowledge/` - Knowledge base integration (ChromaDB)
- `src/liao/opencode/` - OpenCode integration (session management, real-time events)

## Build/Test/Lint Commands

```bash
# Install development dependencies
pip install -e ".[all,dev]"

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_core.py -v

# Run a single test class
pytest tests/test_core.py::TestWindowInfo -v

# Run a single test method
pytest tests/test_core.py::TestWindowInfo::test_properties -v

# Run tests matching a pattern
pytest tests/ -k "conversation" -v

# Run tests with coverage
pytest tests/ --cov=src/liao --cov-report=term-missing

# Lint check
ruff check .

# Format code
black .

# Type check (if mypy is installed)
mypy src/liao

# Build package
python -m build
```

## Code Style Guidelines

### Python Version and Type Hints

- Target Python 3.9+
- Use modern type hints:
  ```python
  # Correct
  def get_windows() -> list[WindowInfo]:
  def find_window(name: str) -> WindowInfo | None:
  
  # Incorrect
  def get_windows() -> List[WindowInfo]:
  def find_window(name: str) -> Optional[WindowInfo]:
  ```
- Use `from __future__ import annotations` at the top of files with forward references
- Use `TYPE_CHECKING` block for imports that are only needed for type hints

### Imports

Standard import order with blank lines between groups:
```python
"""Module docstring."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from .models.window import WindowInfo

if TYPE_CHECKING:
    from .llm.base import BaseLLMClient
```

### Line Length and Formatting

- Maximum line length: 100 characters
- Use Black for automatic formatting
- Use Ruff for linting
- Indent continuation lines with 4 spaces

### Naming Conventions

- **Modules**: `snake_case.py` (e.g., `window_manager.py`)
- **Classes**: `PascalCase` (e.g., `WindowManager`, `VisionAgent`)
- **Functions/Methods**: `snake_case` (e.g., `get_all_visible_windows`)
- **Variables**: `snake_case` (e.g., `window_list`, `chat_rect`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `CHAT_APP_PATTERNS`, `IS_WINDOWS`)
- **Private attributes**: Prefix with underscore (e.g., `_window`, `_running`)
- **Properties**: No prefix, use `@property` decorator

### Data Models

Use `@dataclass` for data-carrying classes:
```python
from dataclasses import dataclass

@dataclass
class WindowInfo:
    hwnd: int
    title: str
    class_name: str
    rect: tuple[int, int, int, int]
    app_type: str

    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]
```

### Error Handling

- Use specific exception types
- Log errors using the module logger
- Return `None` or empty collections for recoverable errors
- Raise exceptions for programming errors

```python
logger = logging.getLogger(__name__)

def get_window(hwnd: int) -> WindowInfo | None:
    try:
        # ... platform-specific code ...
        return window
    except FileNotFoundError:
        logger.warning("Window tool not found")
        return None
    except Exception as e:
        logger.error(f"Failed to get window: {e}")
        return None
```

### Logging

- Get module-level logger: `logger = logging.getLogger(__name__)`
- Use appropriate log levels: `debug`, `info`, `warning`, `error`
- Include context in log messages

### Docstrings

Use Google-style docstrings:
```python
def find_window_by_title(self, title_substring: str) -> WindowInfo | None:
    """Find first window containing title substring.
    
    Args:
        title_substring: Substring to search for in window titles
        
    Returns:
        First matching WindowInfo or None
    """
```

### Testing

- Use pytest framework
- Organize tests by class: `class TestWindowInfo:`
- Use descriptive test names: `def test_properties(self):`
- Use fixtures from `conftest.py` for common test data
- Use `@patch` for mocking external dependencies
- Use `pytest.raises` for exception testing

```python
class TestWindowInfo:
    """Tests for WindowInfo model."""

    def test_properties(self, sample_window_info):
        """Test WindowInfo properties."""
        w = sample_window_info
        assert w.width == 700
        assert w.height == 500
```

### Cross-Platform Considerations

- Check platform with `sys.platform`:
  ```python
  IS_WINDOWS = sys.platform == "win32"
  IS_LINUX = sys.platform == "linux"
  ```
- Use conditional imports for platform-specific modules:
  ```python
  if IS_WINDOWS:
      import win32gui
  ```
- Handle both X11 and Wayland on Linux
- Test platform-specific code paths appropriately

### LLM Client Pattern

All LLM clients inherit from `BaseLLMClient` and must implement:
- `model` property (getter and setter)
- `chat(messages, temperature)` - Single response
- `chat_stream(messages, temperature)` - Streaming response (yields tokens)
- `is_available()` - Check backend connectivity
- `list_models()` - List available models

### GUI Components

- Use PySide6 (Qt for Python)
- Follow Qt naming conventions for signals/slots
- Use i18n for user-facing strings: `translator.tr("key")`
- Separate UI logic from business logic

## Important Files

- `pyproject.toml` - Project configuration, dependencies, tool settings
- `src/liao/__init__.py` - Public API exports
- `src/liao/api.py` - Main `VisionAgent` class
- `tests/conftest.py` - Shared test fixtures

## Common Tasks

### Adding a New LLM Provider

1. Create `src/liao/llm/new_provider.py` extending `BaseLLMClient`
2. Register in `src/liao/llm/factory.py`
3. Add optional dependencies in `pyproject.toml`
4. Add tests in `tests/test_llm.py`

### Adding a New GUI Page

1. Create `src/liao/gui/pages/new_page.py` extending the base pattern
2. Add i18n strings to `src/liao/gui/i18n/en_US.json` and `zh_CN.json`
3. Register in `src/liao/gui/pages/__init__.py`
4. Integrate with `MainWindow` in `main_window.py`

### OpenCode Integration

Liao integrates with OpenCode (https://opencode.ai) for real-time session monitoring and control:

**OpenCode Client (`src/liao/opencode/client.py`)**:
- Connect to OpenCode server (default: http://127.0.0.1:4096)
- Session management: create, list, delete, abort sessions
- Message sending: `send_message()`, `send_command()`, `run_shell()`
- Real-time events via SSE: `subscribe_events()`, `start_event_stream()`
- TUI control: `append_prompt()`, `submit_prompt()`, `execute_command()`

**OpenCode Page (`src/liao/gui/pages/opencode_page.py`)**:
- Connection panel with host/port configuration
- Session list with status indicators
- Message viewer with real-time updates
- Todo list display for running sessions
- Message/command input for interaction

**Usage Example**:
```python
from liao.opencode import OpenCodeClient

client = OpenCodeClient(host="127.0.0.1", port=4096)
if client.is_available():
    # List sessions
    sessions = client.list_sessions()
    
    # Subscribe to events
    client.subscribe_events(lambda e: print(f"Event: {e.type}"))
    client.start_event_stream()
    
    # Send message to session
    client.send_message(session_id, "Hello OpenCode!")
```

### Smart Automation

**SmartAutomationManager (`src/liao/core/smart_automation.py`)** provides intelligent detection and control:

- **Auto-detection**: Automatically detect chat areas, input fields, and send buttons
- **App-specific configs**: Pre-configured layouts for WeChat, QQ, Telegram, Slack, Discord, etc.
- **OCR + Heuristics**: Combines OCR text detection with app-specific heuristics
- **Send button detection**: Finds send button via OCR text recognition or heuristics

**Usage Example**:
```python
from liao.core.smart_automation import SmartAutomationManager
from liao.core.screenshot import ScreenshotReader

reader = ScreenshotReader()
manager = SmartAutomationManager(reader)

# Auto-detect all elements
config = manager.auto_detect(window_info)
if config:
    print(f"Chat area: {config.chat_area}")
    print(f"Input area: {config.input_area}")
    print(f"Send button: {config.send_button_pos}")
    
    # Send a message
    manager.send_message("Hello!", window_info, config)
```

**Supported Apps**: WeChat, WeCom, QQ, Telegram, DingTalk, Feishu, Slack, Discord, Microsoft Teams