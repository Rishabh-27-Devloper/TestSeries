"""
Main Window Controller for CBT Examination System.
Orchestrates layer transitions:
- Layer 1: Exam Selection (GATE, JEE, etc.)
- Layer 2: Paper Inventory (Mocks, PYQs, Topic-wise)
- Layer 3: Candidate Instructions & Declaration
- Layer 3 (Live): Strict Fullscreen CBT Exam Environment
- Dashboard: Scorecard, Analytics & Solutions Review
"""

from typing import Optional
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from core.models import ExamPaper, ExamResult
from core.storage import StorageManager
from ui.layer1_exam_selection import ExamSelectionWindow
from ui.layer2_paper_selection import PaperSelectionWindow
from ui.layer3_instructions import InstructionsScreen
from ui.layer3_cbt_exam import CbtExamWindow
from ui.layer_dashboard import StudentDashboardWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CBT Examination Simulator - Offline Test Series (GATE EC & NEET UG)")
        self.resize(1280, 820)
        self.setMinimumSize(1024, 680)

        # Default student profile
        self.student_name = "Candidate"
        self.roll_number = "GATE24-C9801"

        # Storage
        self.storage_manager = StorageManager()

        # Persistent student profile
        profile = self.storage_manager.load_user_profile()
        self.student_name = profile.get("name", "Candidate")
        self.roll_number = profile.get("roll_number", "GATE25-EC001")
        self.phone_number = profile.get("phone_number", "")

        # Stacked Widget to hold layers
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # Layer instances
        self.layer1 = ExamSelectionWindow(
            storage_manager=self.storage_manager,
            student_name=self.student_name,
            roll_number=self.roll_number,
            parent=self
        )
        self.layer2 = PaperSelectionWindow(
            exam_type="GATE",
            storage_manager=self.storage_manager,
            parent=self
        )
        self.dashboard = StudentDashboardWindow(
            storage_manager=self.storage_manager,
            student_name=self.student_name,
            roll_number=self.roll_number,
            phone_number=self.phone_number,
            parent=self
        )

        self.stack.addWidget(self.layer1)       # Index 0
        self.stack.addWidget(self.layer2)       # Index 1
        self.stack.addWidget(self.dashboard)    # Index 2

        self._current_exam_window: Optional[CbtExamWindow] = None
        self._current_instructions: Optional[InstructionsScreen] = None
        self._active_paper: Optional[ExamPaper] = None

        self._connect_signals()

    def _connect_signals(self):
        # Layer 1 signals
        self.layer1.exam_selected.connect(self._on_exam_selected)
        self.layer1.open_dashboard_requested.connect(self._open_dashboard)
        self.layer1.candidate_profile_updated.connect(self._on_profile_updated)

        # Layer 2 signals
        self.layer2.back_to_exam_selection.connect(self._go_to_layer1)
        self.layer2.paper_selected.connect(self._on_paper_selected)
        self.layer2.open_dashboard_requested.connect(self._open_dashboard)

        # Dashboard signals
        self.dashboard.back_requested.connect(self._go_to_layer1)
        self.dashboard.candidate_profile_updated.connect(lambda prof: self._on_profile_updated(
            prof.get("name", "Candidate"),
            prof.get("roll_number", "GATE25-EC001"),
            prof.get("phone_number", "")
        ))

    def _on_profile_updated(self, name: str, roll: str, phone: str = ""):
        self.student_name = name
        self.roll_number = roll
        self.phone_number = phone
        self.storage_manager.save_user_profile({
            "name": name,
            "roll_number": roll,
            "phone_number": phone
        })
        self.dashboard.set_candidate_profile(name, roll, phone)
        self.layer1.set_candidate_profile(name, roll, phone)

    def _go_to_layer1(self):
        self._ensure_normal_window()
        self.layer1._populate_exam_cards()
        self.stack.setCurrentWidget(self.layer1)

    def _on_exam_selected(self, exam_type: str):
        self._ensure_normal_window()
        self.dashboard.active_exam_filter = exam_type
        self.layer2.set_exam_type(exam_type)
        self.stack.setCurrentWidget(self.layer2)

    def _on_paper_selected(self, paper: ExamPaper):
        """Transition to Layer 3 Pre-Exam Instructions & Declaration."""
        self._active_paper = paper
        self._ensure_normal_window()

        # Build fresh instructions screen
        if self._current_instructions:
            self.stack.removeWidget(self._current_instructions)
            self._current_instructions.deleteLater()

        self._current_instructions = InstructionsScreen(
            paper=paper,
            student_name=self.student_name,
            roll_number=self.roll_number,
            parent=self
        )
        self._current_instructions.start_exam_requested.connect(self._launch_live_cbt_exam)
        self._current_instructions.back_to_papers_requested.connect(lambda: self.stack.setCurrentWidget(self.layer2))

        self.stack.addWidget(self._current_instructions)
        self.stack.setCurrentWidget(self._current_instructions)

    def _launch_live_cbt_exam(self):
        """Enters FULLSCREEN KIOSK MODE and starts the Live CBT Exam."""
        if not self._active_paper:
            return

        # Build fresh exam window
        if self._current_exam_window:
            self.stack.removeWidget(self._current_exam_window)
            self._current_exam_window.deleteLater()

        self._current_exam_window = CbtExamWindow(
            paper=self._active_paper,
            student_name=self.student_name,
            roll_number=self.roll_number,
            storage_manager=self.storage_manager,
            parent=self
        )
        self._current_exam_window.exam_completed.connect(self._on_exam_finished)
        self._current_exam_window.exit_to_dashboard.connect(self._on_exam_exited)

        self.stack.addWidget(self._current_exam_window)
        self.stack.setCurrentWidget(self._current_exam_window)

        # Enforce FULLSCREEN only during the live exam!
        app = QApplication.instance()
        is_test = bool(self.property("is_test") or (app and app.property("is_test")))
        if not is_test:
            self.showFullScreen()
        self._current_exam_window.start_exam()

    def _on_exam_finished(self, result: ExamResult):
        """Exits fullscreen, displays dashboard with results."""
        self._ensure_normal_window()
        self.dashboard.set_result(result)
        self.stack.setCurrentWidget(self.dashboard)

    def _on_exam_exited(self):
        """Safely exits active examination without scoring or saving an attempt."""
        self._ensure_normal_window()
        self.stack.setCurrentWidget(self.layer2)


    def _open_dashboard(self):
        self._ensure_normal_window()
        self.dashboard._build_trends_tab()
        self.stack.setCurrentWidget(self.dashboard)

    def _ensure_normal_window(self):
        """Restores normal window mode outside of active examination."""
        if self.isFullScreen():
            self.showNormal()

    def closeEvent(self, event):
        # If in live exam, warn before quitting
        app = QApplication.instance()
        is_test = bool(self.property("is_test") or (app and app.property("is_test")))

        if self.stack.currentWidget() == self._current_exam_window and self._current_exam_window:
            if is_test:
                if self._current_exam_window.calculator.isVisible():
                    self._current_exam_window.calculator.close()
                sec = getattr(self._current_exam_window, "security_manager", None) or getattr(self._current_exam_window, "security_mgr", None)
                if sec:
                    sec.stop_exam_security()
                event.accept()
                return

            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "An examination is currently in progress! Quitting now will terminate your session without submitting. Are you sure?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self._current_exam_window.calculator.isVisible():
                    self._current_exam_window.calculator.close()
                sec = getattr(self._current_exam_window, "security_manager", None) or getattr(self._current_exam_window, "security_mgr", None)
                if sec:
                    sec.stop_exam_security()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
