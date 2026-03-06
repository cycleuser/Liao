"""
Comprehensive tests for Liao unified API, tools, and CLI flags.
"""

import json
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestToolResult:
    def test_success_result(self):
        from liao.api import ToolResult
        r = ToolResult(success=True, data={"windows": []})
        assert r.success is True

    def test_failure_result(self):
        from liao.api import ToolResult
        r = ToolResult(success=False, error="not found")
        assert r.error == "not found"

    def test_to_dict(self):
        from liao.api import ToolResult
        d = ToolResult(success=True, data="x").to_dict()
        assert d == {"success": True, "data": "x", "error": None, "metadata": {}}

    def test_default_metadata_isolation(self):
        from liao.api import ToolResult
        r1 = ToolResult(success=True)
        r2 = ToolResult(success=True)
        r1.metadata["a"] = 1
        assert "a" not in r2.metadata


class TestListWindowsAPI:
    @patch("liao.core.window_manager.WindowManager")
    def test_list_returns_toolresult(self, mock_wm_cls):
        from liao.api import list_windows
        instance = MagicMock()
        instance.get_all_visible_windows.return_value = []
        mock_wm_cls.return_value = instance

        result = list_windows()
        assert result.success is True
        assert result.data == []
        assert result.metadata["count"] == 0

    @patch("liao.core.window_manager.WindowManager")
    def test_list_with_chat_filter(self, mock_wm_cls):
        from liao.api import list_windows
        mock_win = MagicMock()
        mock_win.hwnd = 123
        mock_win.title = "WeChat"
        mock_win.app_type = "wechat"
        instance = MagicMock()
        instance.get_all_visible_windows.return_value = [mock_win]
        mock_wm_cls.return_value = instance

        result = list_windows(chat_only=True)
        assert result.success is True
        assert len(result.data) == 1


class TestRunAutomationAPI:
    def test_missing_hwnd_and_title(self):
        from liao.api import run_automation
        result = run_automation()
        assert result.success is False
        assert "Specify hwnd or title" in result.error


class TestToolsSchema:
    def test_tools_count(self):
        from liao.tools import TOOLS
        assert len(TOOLS) == 2

    def test_tool_names(self):
        from liao.tools import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        assert "liao_list_windows" in names
        assert "liao_run_automation" in names

    def test_structure(self):
        from liao.tools import TOOLS
        for tool in TOOLS:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func


class TestToolsDispatch:
    def test_unknown_tool(self):
        from liao.tools import dispatch
        with pytest.raises(ValueError):
            dispatch("bad", {})

    @patch("liao.core.window_manager.WindowManager")
    def test_dispatch_list_windows(self, mock_wm_cls):
        from liao.tools import dispatch
        instance = MagicMock()
        instance.get_all_visible_windows.return_value = []
        mock_wm_cls.return_value = instance

        result = dispatch("liao_list_windows", {})
        assert isinstance(result, dict)
        assert result["success"] is True

    def test_dispatch_automation_no_target(self):
        from liao.tools import dispatch
        result = dispatch("liao_run_automation", {})
        assert result["success"] is False


class TestCLIFlags:
    def _run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "liao"] + list(args),
            capture_output=True, text=True, timeout=15,
        )

    def test_version_flag(self):
        r = self._run_cli("-V")
        assert r.returncode == 0
        assert "liao" in r.stdout.lower()

    def test_help_has_unified_flags(self):
        r = self._run_cli("--help")
        assert "--json" in r.stdout
        assert "--quiet" in r.stdout or "-q" in r.stdout
        assert "--verbose" in r.stdout or "-v" in r.stdout


class TestPackageExports:
    def test_version(self):
        import liao
        assert hasattr(liao, "__version__")

    def test_toolresult(self):
        from liao import ToolResult
        assert callable(ToolResult)

    def test_list_windows(self):
        from liao import list_windows
        assert callable(list_windows)

    def test_run_automation(self):
        from liao import run_automation
        assert callable(run_automation)

    def test_vision_agent(self):
        from liao import VisionAgent
        assert VisionAgent is not None
