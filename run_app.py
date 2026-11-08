"""
Main Entrypoint for National CBT Examination Simulator.
Launch this file to run the full application:
python run_app.py
"""

import sys
import os

# Ensure current directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow
from ui.styles import TCS_LIGHT_STYLESHEET


def main():
    # Enable high-DPI scaling
    app = QApplication(sys.argv)
    app.setApplicationName("National CBT Examination Simulator")
    app.setOrganizationName("CBT Platform")

    # Set default clean font and global pure Light Theme stylesheet
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    app.setStyleSheet(TCS_LIGHT_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
