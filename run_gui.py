#!/usr/bin/env python3
"""Test script to launch Liao GUI."""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

print("Starting Liao GUI...")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# macOS specific: ensure high DPI support
if sys.platform == "darwin":
    try:
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    except AttributeError:
        pass

from liao.gui.main_window import MainWindow
from liao.gui.i18n import set_locale

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setApplicationName("Liao")

# Optional: set language
# set_locale("zh_CN")

window = MainWindow()
window.show()

print("GUI launched successfully!")

sys.exit(app.exec())
