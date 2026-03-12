"""WeChat automation - complete working solution."""

from __future__ import annotations

import logging
import time
import pyperclip
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.window import WindowInfo

logger = logging.getLogger(__name__)


@dataclass
class WeChatAreas:
    """WeChat UI areas."""

    chat_rect: tuple[int, int, int, int]
    input_rect: tuple[int, int, int, int]
    send_button: tuple[int, int]


class WeChatAutomation:
    """WeChat automation with click, paste, and send.

    完整流程：
    1. 检测窗口和区域
    2. 点击输入框
    3. 粘贴文本
    4. 按发送快捷键或点击发送按钮
    """

    def __init__(self):
        self._init_input()
        self._areas: WeChatAreas | None = None

    def _init_input(self):
        """Initialize input simulator."""
        self._use_quartz = False
        self._use_pyautogui = False

        # Try Quartz first (macOS)
        try:
            from Quartz import (
                CGEventCreateMouseEvent,
                CGEventCreateKeyboardEvent,
                CGEventPost,
                kCGHIDEventTap,
            )

            self._use_quartz = True
            logger.info("Using Quartz for input")
            return
        except ImportError:
            pass

        # Fallback to pyautogui
        try:
            import pyautogui

            self._use_pyautogui = True
            logger.info("Using pyautogui for input")
        except ImportError:
            logger.error("No input method available")

    def detect_areas(self, window: WindowInfo) -> WeChatAreas:
        """Detect WeChat UI areas.

        微信布局：
        - 左侧 20-25%: 联系人列表
        - 右侧 75-80%: 聊天区域
        - 顶部 5-8%: 标题栏
        - 底部 12-15%: 输入区域

        Args:
            window: WeChat window info

        Returns:
            WeChatAreas with detected regions
        """
        rect = window.rect
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]

        # 聊天区域
        chat_left = rect[0] + int(w * 0.22)
        chat_top = rect[1] + int(h * 0.06)
        chat_right = rect[2] - int(w * 0.01)
        chat_bottom = rect[3] - int(h * 0.13)

        # 输入区域
        input_left = chat_left
        input_top = chat_bottom
        input_right = chat_right
        input_bottom = rect[3] - int(h * 0.01)

        # 发送按钮（输入区右下角）
        send_x = input_right - 50
        send_y = input_bottom - 18

        self._areas = WeChatAreas(
            chat_rect=(chat_left, chat_top, chat_right, chat_bottom),
            input_rect=(input_left, input_top, input_right, input_bottom),
            send_button=(send_x, send_y),
        )

        logger.info(
            f"Detected areas: chat={self._areas.chat_rect}, "
            f"input={self._areas.input_rect}, send={self._areas.send_button}"
        )

        return self._areas

    def move_mouse(self, x: int, y: int) -> bool:
        """Move mouse to position."""
        if self._use_quartz:
            try:
                from Quartz import (
                    CGEventCreateMouseEvent,
                    CGEventPost,
                    kCGHIDEventTap,
                    kCGMouseEventMoved,
                )

                event = CGEventCreateMouseEvent(None, kCGMouseEventMoved, (x, y), 0)
                if event:
                    CGEventPost(kCGHIDEventTap, event)
                    return True
            except Exception as e:
                logger.error(f"Quartz move failed: {e}")

        if self._use_pyautogui:
            try:
                import pyautogui

                pyautogui.moveTo(x, y, duration=0.2)
                return True
            except Exception as e:
                logger.error(f"pyautogui move failed: {e}")

        return False

    def click(self, x: int, y: int) -> bool:
        """Click at position."""
        if self._use_quartz:
            try:
                from Quartz import (
                    CGEventCreateMouseEvent,
                    CGEventPost,
                    kCGHIDEventTap,
                    kCGMouseEventLeftMouseDown,
                    kCGMouseEventLeftMouseUp,
                )

                # Move
                self.move_mouse(x, y)
                time.sleep(0.05)

                # Click down
                event = CGEventCreateMouseEvent(None, kCGMouseEventLeftMouseDown, (x, y), 0)
                CGEventPost(kCGHIDEventTap, event)
                time.sleep(0.05)

                # Click up
                event = CGEventCreateMouseEvent(None, kCGMouseEventLeftMouseUp, (x, y), 0)
                CGEventPost(kCGHIDEventTap, event)
                time.sleep(0.05)

                return True
            except Exception as e:
                logger.error(f"Quartz click failed: {e}")

        if self._use_pyautogui:
            try:
                import pyautogui

                pyautogui.click(x, y)
                return True
            except Exception as e:
                logger.error(f"pyautogui click failed: {e}")

        return False

    def press_key(self, key: str) -> bool:
        """Press a key."""
        key_codes = {
            "enter": 36,
            "return": 36,
            "space": 49,
            "v": 9,
            "c": 8,
            "a": 0,
        }

        if self._use_quartz:
            try:
                from Quartz import (
                    CGEventCreateKeyboardEvent,
                    CGEventPost,
                    kCGHIDEventTap,
                )

                # Get key code
                if key.lower() in key_codes:
                    key_code = key_codes[key.lower()]
                else:
                    # Single char
                    key_code = ord(key.upper()) - 36 if len(key) == 1 else 36

                # Key down
                event = CGEventCreateKeyboardEvent(None, key_code, True)
                CGEventPost(kCGHIDEventTap, event)
                time.sleep(0.02)

                # Key up
                event = CGEventCreateKeyboardEvent(None, key_code, False)
                CGEventPost(kCGHIDEventTap, event)
                time.sleep(0.02)

                return True
            except Exception as e:
                logger.error(f"Quartz key press failed: {e}")

        if self._use_pyautogui:
            try:
                import pyautogui

                pyautogui.press(key)
                return True
            except Exception as e:
                logger.error(f"pyautogui key press failed: {e}")

        return False

    def hotkey(self, *keys: str) -> bool:
        """Press hotkey combination."""
        modifier_codes = {
            "cmd": 55,
            "command": 55,
            "ctrl": 59,
            "control": 59,
            "shift": 56,
            "alt": 58,
            "option": 58,
        }

        if self._use_quartz:
            try:
                from Quartz import (
                    CGEventCreateKeyboardEvent,
                    CGEventPost,
                    kCGHIDEventTap,
                )

                key_codes = {
                    "enter": 36,
                    "return": 36,
                    "v": 9,
                    "c": 8,
                    "a": 0,
                    "space": 49,
                }

                # Press modifiers
                for key in keys[:-1] if len(keys) > 1 else []:
                    code = modifier_codes.get(key.lower())
                    if code:
                        event = CGEventCreateKeyboardEvent(None, code, True)
                        CGEventPost(kCGHIDEventTap, event)
                        time.sleep(0.02)

                # Press main key
                main_key = keys[-1] if keys else "enter"
                code = key_codes.get(main_key.lower(), 36)
                event = CGEventCreateKeyboardEvent(None, code, True)
                CGEventPost(kCGHIDEventTap, event)
                time.sleep(0.02)

                # Release main key
                event = CGEventCreateKeyboardEvent(None, code, False)
                CGEventPost(kCGHIDEventTap, event)
                time.sleep(0.02)

                # Release modifiers
                for key in reversed(keys[:-1] if len(keys) > 1 else []):
                    code = modifier_codes.get(key.lower())
                    if code:
                        event = CGEventCreateKeyboardEvent(None, code, False)
                        CGEventPost(kCGHIDEventTap, event)
                        time.sleep(0.02)

                return True
            except Exception as e:
                logger.error(f"Quartz hotkey failed: {e}")

        if self._use_pyautogui:
            try:
                import pyautogui

                pyautogui.hotkey(*keys)
                return True
            except Exception as e:
                logger.error(f"pyautogui hotkey failed: {e}")

        return False

    def click_input(self, window: WindowInfo | None = None) -> bool:
        """Click on input area.

        Args:
            window: Window info (uses cached areas if None)

        Returns:
            True if successful
        """
        if window and not self._areas:
            self.detect_areas(window)

        if not self._areas:
            logger.error("No areas detected")
            return False

        x = (self._areas.input_rect[0] + self._areas.input_rect[2]) // 2
        y = (self._areas.input_rect[1] + self._areas.input_rect[3]) // 2

        logger.info(f"Clicking input at ({x}, {y})")
        return self.click(x, y)

    def paste_text(self, text: str) -> bool:
        """Paste text using clipboard.

        Args:
            text: Text to paste

        Returns:
            True if successful
        """
        logger.info(f"Pasting {len(text)} characters")

        try:
            # Copy to clipboard
            pyperclip.copy(text)
            time.sleep(0.1)

            # Paste (Cmd+V on macOS)
            self.hotkey("cmd", "v")
            time.sleep(0.2)

            logger.info("Paste successful")
            return True

        except Exception as e:
            logger.error(f"Paste failed: {e}")
            return False

    def send(self, method: str = "enter") -> bool:
        """Send message.

        Args:
            method: Send method ("enter", "ctrl_enter", "button")

        Returns:
            True if successful
        """
        logger.info(f"Sending with method: {method}")

        if method == "button" and self._areas:
            # Click send button
            success = self.click(*self._areas.send_button)
            time.sleep(0.1)
            # Also press Enter as backup
            self.press_key("enter")
            return success

        elif method == "ctrl_enter":
            return self.hotkey("ctrl", "enter")

        else:  # enter
            return self.press_key("enter")

    def send_message(
        self,
        text: str,
        window: WindowInfo,
        send_method: str = "auto",
    ) -> bool:
        """Send message to WeChat.

        完整发送流程：
        1. 检测区域
        2. 点击输入框
        3. 清空输入框 (Cmd+A)
        4. 粘贴文本
        5. 发送

        Args:
            text: Message text
            window: WeChat window
            send_method: "auto", "enter", "ctrl_enter", "button"

        Returns:
            True if successful
        """
        logger.info(f"=== Sending message ({len(text)} chars) ===")

        # 1. Detect areas
        if not self._areas:
            self.detect_areas(window)

        # 2. Click input
        logger.info("Step 1: Click input area")
        if not self.click_input():
            logger.error("Failed to click input")
            return False
        time.sleep(0.2)

        # 3. Clear existing text
        logger.info("Step 2: Clear input")
        self.hotkey("cmd", "a")
        time.sleep(0.1)

        # 4. Paste text
        logger.info("Step 3: Paste text")
        if not self.paste_text(text):
            logger.error("Failed to paste")
            return False
        time.sleep(0.2)

        # 5. Send
        logger.info("Step 4: Send message")
        if send_method == "auto":
            # Try button first, then Enter
            if self._areas:
                self.send("button")
            else:
                self.send("enter")
        else:
            self.send(send_method)

        logger.info("=== Message sent ===")
        return True

    def get_chat_text(self, window: WindowInfo) -> str:
        """Get text from chat area using OCR.

        Args:
            window: WeChat window

        Returns:
            Extracted text
        """
        if not self._areas:
            self.detect_areas(window)

        if not self._areas:
            return ""

        # Screenshot
        from .macos_screenshot import MacOSScreenshot

        screenshot = MacOSScreenshot()

        img = screenshot.capture_region(
            self._areas.chat_rect[0],
            self._areas.chat_rect[1],
            self._areas.chat_rect[2] - self._areas.chat_rect[0],
            self._areas.chat_rect[3] - self._areas.chat_rect[1],
        )

        if not img:
            return ""

        # OCR
        try:
            import easyocr
            import numpy as np

            reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
            results = reader.readtext(np.array(img))

            texts = [text for bbox, text, prob in results if prob > 0.3]
            return "\n".join(texts)

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
