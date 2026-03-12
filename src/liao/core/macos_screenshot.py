"""Screenshot capture for macOS using Quartz framework."""

from __future__ import annotations

import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from ..models.window import WindowInfo

logger = logging.getLogger(__name__)


class MacOSScreenshot:
    """Capture screenshots on macOS using Quartz or screencapture."""

    def __init__(self):
        self._quartz_available = self._check_quartz()
        self._screencapture_available = self._check_screencapture()

    def _check_quartz(self) -> bool:
        """Check if Quartz is available."""
        try:
            from Quartz import CGWindowListCreateImage, CGRectMake

            return True
        except ImportError:
            logger.debug("Quartz not available")
            return False

    def _check_screencapture(self) -> bool:
        """Check if screencapture CLI is available."""
        try:
            result = subprocess.run(
                ["which", "screencapture"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> Image.Image | None:
        """Capture a screen region.

        Args:
            x: Left coordinate
            y: Top coordinate
            width: Region width
            height: Region height

        Returns:
            PIL Image or None
        """
        if width <= 0 or height <= 0:
            logger.error(f"Invalid dimensions: {width}x{height}")
            return None

        # Try Quartz first
        if self._quartz_available:
            img = self._capture_quartz(x, y, width, height)
            if img:
                return img

        # Fallback to screencapture
        if self._screencapture_available:
            img = self._capture_screencapture(x, y, width, height)
            if img:
                return img

        # Last resort: pyautogui
        return self._capture_pyautogui(x, y, width, height)

    def _capture_quartz(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> Image.Image | None:
        """Capture using Quartz CGWindowListCreateImage."""
        try:
            from Quartz import (
                CGWindowListCreateImage,
                CGRectMake,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID,
            )

            # Create image from screen region
            rect = CGRectMake(x, y, width, height)
            cg_image = CGWindowListCreateImage(
                rect,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID,
                0,  # kCGWindowImageDefault
            )

            if not cg_image:
                logger.debug("Quartz returned None")
                return None

            # Get image dimensions and data
            from Quartz import (
                CGImageGetWidth,
                CGImageGetHeight,
                CGImageGetBytesPerRow,
                CGImageGetDataProvider,
                CGDataProviderCopyData,
            )

            w = CGImageGetWidth(cg_image)
            h = CGImageGetHeight(cg_image)

            if w == 0 or h == 0:
                return None

            # Get raw data
            data = CGDataProviderCopyData(CGImageGetDataProvider(cg_image))
            bytes_per_row = CGImageGetBytesPerRow(cg_image)

            # Create PIL Image from raw data
            # Quartz uses BGRA format
            from PIL import Image

            img = Image.frombytes(
                "RGBA",
                (w, h),
                bytes(data),
                "raw",
                "BGRA",
                bytes_per_row,
                0,
            )

            # Crop to exact size if needed
            if img.size != (width, height):
                img = img.crop((0, 0, width, height))

            return img

        except Exception as e:
            logger.debug(f"Quartz capture failed: {e}")
            return None

    def _capture_screencapture(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> Image.Image | None:
        """Capture using screencapture CLI."""
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        import os

        os.close(fd)

        try:
            # screencapture -x: no sound, -R: region
            geometry = f"{x},{y},{width},{height}"
            result = subprocess.run(
                ["screencapture", "-x", "-R", geometry, tmp_path],
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0 and Path(tmp_path).exists():
                img = Image.open(tmp_path)
                return img.copy()
            else:
                logger.debug(f"screencapture failed: {result.stderr.decode()}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("screencapture timed out")
            return None
        except Exception as e:
            logger.error(f"screencapture error: {e}")
            return None
        finally:
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass

    def _capture_pyautogui(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> Image.Image | None:
        """Capture using pyautogui (fallback)."""
        try:
            import pyautogui

            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return screenshot
        except Exception as e:
            logger.error(f"pyautogui capture failed: {e}")
            return None

    def capture_window(self, window_info: WindowInfo) -> Image.Image | None:
        """Capture a window.

        Args:
            window_info: Window to capture

        Returns:
            PIL Image or None
        """
        x, y, right, bottom = window_info.rect
        width = right - x
        height = bottom - y
        return self.capture_region(x, y, width, height)


# Re-export as main class
ScreenshotReader = MacOSScreenshot
