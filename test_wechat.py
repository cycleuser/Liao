#!/usr/bin/env python3
"""WeChat automation test script.

Usage:
    python test_wechat.py              # 检测窗口和区域
    python test_wechat.py --send       # 发送测试消息
    python test_wechat.py --text "消息内容"  # 发送指定消息
"""

import sys
import argparse

from liao.core.wechat_automation import WeChatAutomation
from liao.core.window_manager import WindowManager


def main():
    parser = argparse.ArgumentParser(description="WeChat automation test")
    parser.add_argument("--send", action="store_true", help="Send test message")
    parser.add_argument("--text", type=str, default="【测试消息】", help="Message to send")
    parser.add_argument(
        "--method", choices=["enter", "button", "ctrl_enter"], default="button", help="Send method"
    )
    args = parser.parse_args()

    print("=== 微信自动化测试 ===\n")

    # 初始化
    auto = WeChatAutomation()
    wm = WindowManager()

    # 找微信窗口
    wechat = wm.find_window_by_title("WeChat")
    if not wechat:
        print("❌ 未找到微信窗口")
        print("请确保微信窗口已打开且可见")
        return 1

    print(f"✅ 找到微信窗口: {wechat.rect}")

    # 检测区域
    areas = auto.detect_areas(wechat)
    print(f"✅ 检测到区域:")
    print(f"   对话区域: {areas.chat_rect}")
    print(f"   输入区域: {areas.input_rect}")
    print(f"   发送按钮: {areas.send_button}")

    if not args.send:
        # 获取对话内容
        print("\n📖 对话内容:")
        text = auto.get_chat_text(wechat)
        if text:
            print(text[:500])
            if len(text) > 500:
                print(f"... (共 {len(text)} 字符)")
        else:
            print("未识别到内容")

        print("\n提示: 使用 --send 参数发送测试消息")
        print('      使用 --text "消息" 发送指定消息')
        return 0

    # 发送消息
    print(f"\n📤 发送消息: {args.text}")
    print(f"   方式: {args.method}")

    import time

    print("\n3秒后开始...")
    time.sleep(1)
    print("2秒后开始...")
    time.sleep(1)
    print("1秒后开始...")
    time.sleep(1)

    success = auto.send_message(args.text, wechat, send_method=args.method)

    if success:
        print("\n✅ 消息已发送!")
    else:
        print("\n❌ 发送失败")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
