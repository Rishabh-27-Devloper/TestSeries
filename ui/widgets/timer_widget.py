"""
Countdown Timer Widget for CBT Exam.
Displays remaining time formatted as 'HH:MM:SS', warns when low,
and emits auto-submission signal on expiration.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont


class ExamTimerWidget(QWidget):
    time_expired = pyqtSignal()
    second_ticked = pyqtSignal(int)   # Emits total elapsed seconds

    def __init__(self, duration_minutes: int = 180, parent=None):
        super().__init__(parent)
        self.total_seconds = duration_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.elapsed_seconds = 0
        self.is_running = False

        self.timer = QTimer(self)
        self.timer.setInterval(1000)   # 1 second
        self.timer.timeout.connect(self._on_tick)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self.container = QFrame()
        self.container.setObjectName("timerContainer")
        c_layout = QHBoxLayout(self.container)
        c_layout.setContentsMargins(10, 4, 10, 4)
        c_layout.setSpacing(6)

        icon_lbl = QLabel("⏱")
        icon_lbl.setStyleSheet("font-size: 16px;")

        self.title_lbl = QLabel("Time Left :")
        self.title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #374151;")

        self.time_lbl = QLabel(self._format_time(self.remaining_seconds))
        self.time_lbl.setFont(QFont("Consolas", 15, QFont.Weight.Bold))
        self.time_lbl.setStyleSheet("color: #1e3a8a;")

        c_layout.addWidget(icon_lbl)
        c_layout.addWidget(self.title_lbl)
        c_layout.addWidget(self.time_lbl)
        layout.addWidget(self.container)

        self._apply_style("normal")

    def _apply_style(self, state: str):
        if state == "normal":
            self.container.setStyleSheet("""
                QFrame#timerContainer {
                    background-color: #f8fafc;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                }
            """)
            self.time_lbl.setStyleSheet("color: #1e3a8a; font-family: 'Consolas'; font-size: 16px; font-weight: bold;")
        elif state == "warning": # < 15 mins
            self.container.setStyleSheet("""
                QFrame#timerContainer {
                    background-color: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 4px;
                }
            """)
            self.time_lbl.setStyleSheet("color: #b45309; font-family: 'Consolas'; font-size: 16px; font-weight: bold;")
        elif state == "critical": # < 5 mins
            self.container.setStyleSheet("""
                QFrame#timerContainer {
                    background-color: #fee2e2;
                    border: 2px solid #ef4444;
                    border-radius: 4px;
                }
            """)
            self.time_lbl.setStyleSheet("color: #dc2626; font-family: 'Consolas'; font-size: 16px; font-weight: bold;")

    def start(self):
        self.is_running = True
        self.timer.start()

    def pause(self):
        self.is_running = False
        self.timer.stop()

    def resume(self):
        if not self.is_running and self.remaining_seconds > 0:
            self.is_running = True
            self.timer.start()

    def stop(self):
        self.is_running = False
        self.timer.stop()

    def reset(self, duration_minutes: int):
        self.total_seconds = duration_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.elapsed_seconds = 0
        self.time_lbl.setText(self._format_time(self.remaining_seconds))
        self._apply_style("normal")

    def _on_tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.elapsed_seconds += 1
            self.time_lbl.setText(self._format_time(self.remaining_seconds))
            self.second_ticked.emit(self.elapsed_seconds)

            # Styling triggers
            if self.remaining_seconds <= 300: # 5 mins
                self._apply_style("critical")
            elif self.remaining_seconds <= 900: # 15 mins
                self._apply_style("warning")
            else:
                self._apply_style("normal")
        else:
            self.stop()
            self.time_expired.emit()

    @staticmethod
    def _format_time(seconds: int) -> str:
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
