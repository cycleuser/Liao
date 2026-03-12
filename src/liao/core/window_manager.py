"""Window management module with cross-platform support.

Uses Win32 APIs on Windows, xwininfo/wmctrl/xdotool on Linux,
and PyObjC/Quartz on macOS.
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from typing import TYPE_CHECKING

from ..models.window import WindowInfo

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform == "linux"
IS_MACOS = sys.platform == "darwin"

CHAT_APP_PATTERNS = {
    "wechat": ["WeChat", "微信"],
    "wecom": ["WeCom", "企业微信"],
    "qq": ["QQ"],
    "telegram": ["Telegram"],
    "dingtalk": ["钉钉", "DingTalk"],
    "feishu": ["飞书", "Lark", "Feishu"],
    "slack": ["Slack"],
    "discord": ["Discord"],
    "teams": ["Microsoft Teams", "Teams"],
}

_XWININFO_RE = re.compile(
    r"^\s+(0x[0-9a-fA-F]+)\s+"
    r'"([^"]*)"'
    r'(?::\s*\("([^"]*)")?'
    r'(?:\s+"([^"]*)")?\)?'
    r"\s+(\d+)x(\d+)\+(-?\d+)\+(-?\d+)"
)


class WindowManager:
    """Manages desktop windows with cross-platform support."""

    def __init__(self):
        self._win32gui = None
        self._win32con = None
        self._linux_xwininfo = False
        self._linux_wmctrl = False
        self._linux_xdotool = False
        self._macos_quartz = False
        self._macos_applescript = False
        self._load_win32()
        self._load_linux()
        self._load_macos()

    def _load_win32(self):
        if not IS_WINDOWS:
            return
        try:
            import win32con
            import win32gui

            self._win32gui = win32gui
            self._win32con = win32con
        except ImportError:
            logger.warning("pywin32 not available - window management disabled")

    def _load_linux(self):
        if not IS_LINUX:
            return
        try:
            subprocess.run(["xwininfo", "-version"], capture_output=True, timeout=2)
            self._linux_xwininfo = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._linux_xwininfo = True
        try:
            subprocess.run(["wmctrl", "--version"], capture_output=True, timeout=2)
            self._linux_wmctrl = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        try:
            subprocess.run(["xdotool", "version"], capture_output=True, timeout=2)
            self._linux_xdotool = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def _load_macos(self):
        if not IS_MACOS:
            return
        try:
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGNullWindowID,
                kCGWindowListOptionOnScreenOnly,
            )

            self._macos_quartz = True
            logger.debug("Using Quartz for macOS window management")
            return
        except ImportError:
            pass
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get name of every process',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._macos_applescript = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def is_available(self) -> bool:
        return (
            self._win32gui is not None
            or self._linux_xwininfo
            or self._linux_wmctrl
            or self._linux_xdotool
            or self._macos_quartz
            or self._macos_applescript
        )

    def get_all_visible_windows(self) -> list[WindowInfo]:
        if self._win32gui is not None:
            return self._get_windows_win32()
        elif IS_LINUX:
            return self._get_windows_linux()
        elif IS_MACOS:
            return self._get_windows_macos()
        return []

    def _get_windows_win32(self) -> list[WindowInfo]:
        windows: list[WindowInfo] = []

        def enum_callback(hwnd, _):
            try:
                if not self._win32gui.IsWindowVisible(hwnd):
                    return True
                title = self._win32gui.GetWindowText(hwnd)
                if not title or not title.strip():
                    return True
                rect = self._win32gui.GetWindowRect(hwnd)
                if (rect[2] - rect[0]) < 200 or (rect[3] - rect[1]) < 150:
                    return True
                cls = self._win32gui.GetClassName(hwnd) or ""
                app_type = self._detect_app_type(title, cls)
                windows.append(
                    WindowInfo(hwnd=hwnd, title=title, class_name=cls, rect=rect, app_type=app_type)
                )
            except Exception:
                pass
            return True

        self._win32gui.EnumWindows(enum_callback, None)
        windows.sort(key=lambda w: w.title.lower())
        return windows

    def _get_windows_macos(self) -> list[WindowInfo]:
        if self._macos_quartz:
            windows = self._get_windows_quartz()
            if windows:
                return windows
        if self._macos_applescript:
            windows = self._get_windows_applescript()
            if windows:
                return windows
        return []

    def _get_windows_quartz(self) -> list[WindowInfo]:
        windows: list[WindowInfo] = []
        try:
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGNullWindowID,
                kCGWindowListOptionOnScreenOnly,
            )

            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            )
            for win_info in window_list:
                try:
                    owner = win_info.get("kCGWindowOwnerName", "")
                    if not owner:
                        continue
                    if owner in ("Window Server", "SystemUIServer", "Dock"):
                        continue
                    name = win_info.get("kCGWindowName", "")
                    bounds = win_info.get("kCGWindowBounds", {})
                    x = int(bounds.get("X", 0))
                    y = int(bounds.get("Y", 0))
                    w = int(bounds.get("Width", 0))
                    h = int(bounds.get("Height", 0))
                    if w < 100 or h < 100:
                        continue
                    if x < -2000 or y < -2000:
                        continue
                    layer = win_info.get("kCGWindowLayer", 0)
                    if layer < -1000:
                        continue
                    window_id = win_info.get("kCGWindowNumber", 0)
                    rect = (x, y, x + w, y + h)
                    title = f"{owner}: {name}" if name else owner
                    app_type = self._detect_app_type(f"{owner} {name}", owner)
                    windows.append(
                        WindowInfo(
                            hwnd=window_id,
                            title=title,
                            class_name=owner,
                            rect=rect,
                            app_type=app_type,
                        )
                    )
                except Exception as e:
                    logger.debug(f"Error processing window: {e}")
            windows.sort(key=lambda w: w.title.lower())
        except Exception as e:
            logger.warning(f"Quartz window enumeration failed: {e}")
        return windows

    def _get_windows_applescript(self) -> list[WindowInfo]:
        windows: list[WindowInfo] = []
        try:
            script = """
            tell application "System Events"
                set output to ""
                repeat with theProcess in (every process whose visible is true)
                    try
                        set processName to name of theProcess
                        repeat with theWindow in windows of theProcess
                            set windowTitle to name of theWindow
                            set winPos to position of theWindow
                            set winSize to size of theWindow
                            set output to output & processName & "|||" & windowTitle & "|||" & (item 1 of winPos as text) & "," & (item 2 of winPos as text) & "," & (item 1 of winSize as text) & "," & (item 2 of winSize as text) & "~~~"
                        end repeat
                    end try
                end repeat
                return output
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for entry in result.stdout.strip().split("~~~"):
                    if not entry.strip():
                        continue
                    parts = entry.strip().split("|||")
                    if len(parts) >= 3:
                        owner = parts[0].strip()
                        title = parts[1].strip()
                        bounds_str = parts[2].strip()
                        if not title:
                            continue
                        try:
                            bounds_parts = bounds_str.split(",")
                            x, y, w, h = (
                                int(bounds_parts[0]),
                                int(bounds_parts[1]),
                                int(bounds_parts[2]),
                                int(bounds_parts[3]),
                            )
                        except (ValueError, IndexError):
                            continue
                        if w < 200 or h < 150:
                            continue
                        rect = (x, y, x + w, y + h)
                        full_title = f"{owner}: {title}" if owner else title
                        app_type = self._detect_app_type(f"{owner} {title}", owner)
                        windows.append(
                            WindowInfo(
                                hwnd=id(full_title),
                                title=full_title,
                                class_name=owner,
                                rect=rect,
                                app_type=app_type,
                            )
                        )
            windows.sort(key=lambda w: w.title.lower())
        except Exception as e:
            logger.warning(f"AppleScript window enumeration failed: {e}")
        return windows

    def _get_windows_linux(self) -> list[WindowInfo]:
        if self._linux_xwininfo:
            windows = self._get_windows_xwininfo()
            if windows is not None:
                return windows
        if self._linux_wmctrl:
            windows = self._get_windows_wmctrl()
            if windows is not None:
                return windows
        if self._linux_xdotool:
            windows = self._get_windows_xdotool()
            if windows is not None:
                return windows
        return []

    def _get_windows_xwininfo(self) -> list[WindowInfo] | None:
        try:
            result = subprocess.run(
                ["xwininfo", "-root", "-children"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        skip_patterns = {
            "mutter guard window",
            "mutter-x11-frames",
            "chromium clipboard",
            "qt selection owner",
            "gsd-xsettings",
            "ibus-x11",
            "ibus-xim",
            "gnome shell",
        }
        windows: list[WindowInfo] = []
        for line in result.stdout.splitlines():
            m = _XWININFO_RE.match(line)
            if not m:
                continue
            xid_str, title, wm_instance, wm_class, w_str, h_str, x_str, y_str = m.groups()
            if not title or not title.strip():
                continue
            if any(p in title.lower() for p in skip_patterns):
                continue
            try:
                xid = int(xid_str, 16)
                w, h, x, y = int(w_str), int(h_str), int(x_str), int(y_str)
            except ValueError:
                continue
            if w < 200 or h < 150:
                continue
            class_name = wm_class or wm_instance or ""
            rect = (x, y, x + w, y + h)
            app_type = self._detect_app_type(title, class_name)
            windows.append(
                WindowInfo(
                    hwnd=xid, title=title, class_name=class_name, rect=rect, app_type=app_type
                )
            )
        windows.sort(key=lambda w: w.title.lower())
        return windows

    def _get_windows_wmctrl(self) -> list[WindowInfo] | None:
        try:
            result = subprocess.run(["wmctrl", "-lG"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        windows: list[WindowInfo] = []
        for line in result.stdout.strip().splitlines():
            try:
                parts = line.split(None, 7)
                if len(parts) < 8:
                    continue
                xid = int(parts[0], 16)
                x, y, w, h = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
                title = parts[7].strip()
                if not title or w < 200 or h < 150:
                    continue
                rect = (x, y, x + w, y + h)
                app_type = self._detect_app_type(title, "")
                windows.append(
                    WindowInfo(hwnd=xid, title=title, class_name="", rect=rect, app_type=app_type)
                )
            except (ValueError, IndexError):
                continue
        windows.sort(key=lambda w: w.title.lower())
        return windows

    def _get_windows_xdotool(self) -> list[WindowInfo] | None:
        try:
            result = subprocess.run(
                ["xdotool", "search", "--onlyvisible", "--name", ""],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        xids = result.stdout.strip().splitlines()
        if not xids:
            return None
        windows: list[WindowInfo] = []
        for xid_str in xids:
            try:
                xid = int(xid_str.strip())
                name_result = subprocess.run(
                    ["xdotool", "getwindowname", str(xid)],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                title = name_result.stdout.strip() if name_result.returncode == 0 else ""
                if not title:
                    continue
                geo_result = subprocess.run(
                    ["xdotool", "getwindowgeometry", "--shell", str(xid)],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if geo_result.returncode != 0:
                    continue
                geo = {}
                for geo_line in geo_result.stdout.strip().splitlines():
                    if "=" in geo_line:
                        k, v = geo_line.split("=", 1)
                        geo[k] = v
                x, y, w, h = (
                    int(geo.get("X", 0)),
                    int(geo.get("Y", 0)),
                    int(geo.get("WIDTH", 0)),
                    int(geo.get("HEIGHT", 0)),
                )
                if w < 200 or h < 150:
                    continue
                rect = (x, y, x + w, y + h)
                app_type = self._detect_app_type(title, "")
                windows.append(
                    WindowInfo(hwnd=xid, title=title, class_name="", rect=rect, app_type=app_type)
                )
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, KeyError):
                continue
        windows.sort(key=lambda w: w.title.lower())
        return windows

    @staticmethod
    def _detect_app_type(title: str, class_name: str) -> str:
        tl, cl = title.lower(), class_name.lower()
        for app_type, patterns in CHAT_APP_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in tl or pattern.lower() in cl:
                    return app_type
        return "other"

    def get_window_by_hwnd(self, hwnd: int) -> WindowInfo | None:
        if self._win32gui is not None:
            return self._get_window_by_hwnd_win32(hwnd)
        else:
            for w in self.get_all_visible_windows():
                if w.hwnd == hwnd:
                    return w
        return None

    def _get_window_by_hwnd_win32(self, hwnd: int) -> WindowInfo | None:
        try:
            if not self._win32gui.IsWindow(hwnd):
                return None
            title = self._win32gui.GetWindowText(hwnd)
            cls = self._win32gui.GetClassName(hwnd) or ""
            rect = self._win32gui.GetWindowRect(hwnd)
            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=cls,
                rect=rect,
                app_type=self._detect_app_type(title, cls),
            )
        except Exception as e:
            logger.warning(f"Failed to get window by hwnd: {e}")
            return None

    def refresh_window_info(self, window: WindowInfo) -> WindowInfo | None:
        return self.get_window_by_hwnd(window.hwnd)

    def get_chat_windows(self) -> list[WindowInfo]:
        return [w for w in self.get_all_visible_windows() if w.app_type != "other"]

    def find_window_by_title(self, title_substring: str) -> WindowInfo | None:
        title_lower = title_substring.lower()
        for w in self.get_all_visible_windows():
            if title_lower in w.title.lower():
                return w
        return None
