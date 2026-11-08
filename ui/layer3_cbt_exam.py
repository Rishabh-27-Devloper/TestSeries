"""
Layer 3 CBT Examination Screen.
The complete, high-fidelity replica of TCS iON / GATE examination interface:
- Top Header with Exam Title, Calculator button, and Countdown Timer.
- Section switcher tabs.
- Question area with MCQ, MSQ, and NAT support.
- Navigation action footer ("Save & Next", "Mark for Review & Next", "Clear Response").
- Right-hand collapsible Question Palette with official TCS iON Legend and real-time counts.
- Virtual Scientific Calculator integration.
- Fullscreen enforcement and focus loss proctoring.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.models import ExamPaper, Question, QuestionStatus, Section, ExamResult
from core.evaluator import ExamEvaluator
from core.security import SecurityManager
from core.storage import StorageManager
from ui.widgets.calculator import GateCalculator
from ui.widgets.palette import PaletteWidget
from ui.widgets.question_display import QuestionDisplayWidget
from ui.widgets.timer_widget import ExamTimerWidget
from ui.widgets.popups import QuestionPaperDialog, InstructionsDialog, SubmitConfirmationDialog


class CbtExamWindow(QWidget):
    exam_completed = pyqtSignal(object)   # Emits ExamResult
    exit_to_dashboard = pyqtSignal()

    def __init__(
        self,
        paper: ExamPaper,
        student_name: str = "Candidate",
        roll_number: str = "GATE24-C9801",
        storage_manager: Optional[StorageManager] = None,
        parent=None
    ):
        super().__init__(parent)
        self.paper = paper
        self.student_name = student_name
        self.roll_number = roll_number
        self.storage_manager = storage_manager or StorageManager()

        self.all_questions: List[Question] = paper.all_questions
        self.current_index = 0
        self.sec_tab_buttons: List[QPushButton] = []
        self.is_palette_collapsed = False

        # Virtual Scientific Calculator
        self.calculator = GateCalculator(self)

        # Anti-Cheat Security Manager
        self.security_mgr = SecurityManager(
            target_window=self,
            max_warnings=3,
            auto_submit_callback=self._auto_submit_on_breach
        )

        self._init_ui()
        self._load_active_question()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. TCS iON Top Header Bar
        header = QFrame()
        header.setObjectName("cbtHeader")
        header.setFixedHeight(54)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 6, 12, 6)
        h_layout.setSpacing(12)

        # Exam Title
        lbl_exam_title = QLabel(f"<b>{self.paper.title}</b>")
        lbl_exam_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_exam_title.setStyleSheet("background-color: transparent; color: #ffffff;")
        h_layout.addWidget(lbl_exam_title)

        h_layout.addStretch()

        # Virtual Scientific Calculator Toggle Button
        self.btn_calc = QPushButton("🖩  Virtual Calculator")
        self.btn_calc.setObjectName("btnHeaderCalc")
        self.btn_calc.setFixedHeight(34)
        self.btn_calc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_calc.clicked.connect(self._toggle_calculator)
        h_layout.addWidget(self.btn_calc)

        # Countdown Timer Widget
        self.timer_widget = ExamTimerWidget(duration_minutes=self.paper.duration_minutes, parent=self)
        self.timer_widget.time_expired.connect(self._on_time_expired)
        self.timer_widget.second_ticked.connect(self._on_second_ticked)
        h_layout.addWidget(self.timer_widget)

        # Candidate System Info
        sys_info = QLabel(f"System: <b>C98-01</b><br><span style='font-size:10px;'>{self.student_name}</span>")
        sys_info.setStyleSheet("background-color: transparent; color: #ffffff; font-size: 11px;")
        sys_info.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h_layout.addWidget(sys_info)

        # Exit Exam Button
        self.btn_exit = QPushButton("🚪 Exit Exam")
        self.btn_exit.setObjectName("btnExitExam")
        self.btn_exit.setFixedHeight(34)
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setToolTip("Exit the examination without submitting")
        self.btn_exit.clicked.connect(self._on_exit_exam)
        h_layout.addWidget(self.btn_exit)

        main_layout.addWidget(header)

        # 2. Section Navigation Tabs Bar
        sec_bar = QFrame()
        sec_bar.setObjectName("secTabBar")
        sec_bar.setFixedHeight(40)
        s_layout = QHBoxLayout(sec_bar)
        s_layout.setContentsMargins(10, 4, 10, 4)
        s_layout.setSpacing(6)

        sec_label = QLabel("<b>SECTIONS:</b>")
        sec_label.setStyleSheet("color: #1e3a8a; font-size: 11px; margin-right: 6px;")
        s_layout.addWidget(sec_label)

        for sec in self.paper.sections:
            s_btn = QPushButton(f"{sec.section_name} ({len(sec.questions)})")
            s_btn.setObjectName("secTabButton")
            s_btn.setCheckable(True)
            s_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            s_btn.clicked.connect(lambda checked, s_id=sec.section_id: self._on_section_tab_clicked(s_id))
            self.sec_tab_buttons.append(s_btn)
            s_layout.addWidget(s_btn)

        s_layout.addStretch()
        main_layout.addWidget(sec_bar)

        # 3. Main Central Area (Question display on left, Question Palette on right)
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Left Column: Question Area & Action Footer
        left_col = QWidget()
        l_layout = QVBoxLayout(left_col)
        l_layout.setContentsMargins(6, 6, 6, 6)
        l_layout.setSpacing(6)

        # Question Display
        self.q_display = QuestionDisplayWidget(self)
        self.q_display.response_changed.connect(self._on_candidate_response_changed)
        l_layout.addWidget(self.q_display, 1)

        # Action Footer Bar
        footer = QFrame()
        footer.setObjectName("cbtFooter")
        footer.setFixedHeight(50)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(10, 6, 10, 6)
        f_layout.setSpacing(10)

        # Left Action Buttons
        self.btn_mark_review = QPushButton("Mark for Review & Next")
        self.btn_mark_review.setObjectName("btnMarkReview")
        self.btn_mark_review.clicked.connect(self._on_mark_for_review_next)

        self.btn_clear = QPushButton("Clear Response")
        self.btn_clear.setObjectName("btnClearResponse")
        self.btn_clear.clicked.connect(self._on_clear_response)

        f_layout.addWidget(self.btn_mark_review)
        f_layout.addWidget(self.btn_clear)
        f_layout.addStretch()

        # Right Action Buttons
        self.btn_prev = QPushButton("<< Previous")
        self.btn_prev.setObjectName("btnNav")
        self.btn_prev.clicked.connect(self._on_previous_question)

        self.btn_save_next = QPushButton("Save & Next")
        self.btn_save_next.setObjectName("btnSaveNext")
        self.btn_save_next.clicked.connect(self._on_save_and_next)

        f_layout.addWidget(self.btn_prev)
        f_layout.addWidget(self.btn_save_next)
        l_layout.addWidget(footer)

        center_layout.addWidget(left_col, 1)

        # Palette Collapse/Expand Toggle Strip
        self.btn_toggle_palette = QPushButton("▶")
        self.btn_toggle_palette.setObjectName("btnTogglePalette")
        self.btn_toggle_palette.setFixedWidth(18)
        self.btn_toggle_palette.setSizePolicy(self.btn_toggle_palette.sizePolicy().horizontalPolicy(), self.btn_toggle_palette.sizePolicy().verticalPolicy())
        self.btn_toggle_palette.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_palette.setToolTip("Toggle Side Palette")
        self.btn_toggle_palette.clicked.connect(self._toggle_palette)
        center_layout.addWidget(self.btn_toggle_palette)

        # Right Column: Question Palette
        self.palette = PaletteWidget(self)
        self.palette.set_candidate_info(self.student_name, self.roll_number)
        self.palette.populate_questions(self.all_questions, active_idx=0)
        self.palette.question_clicked.connect(self._on_palette_question_clicked)
        self.palette.question_paper_clicked.connect(self._open_question_paper_dialog)
        self.palette.instructions_clicked.connect(self._open_instructions_dialog)
        self.palette.submit_clicked.connect(self._prompt_submit_confirmation)
        center_layout.addWidget(self.palette)

        main_layout.addWidget(center_widget, 1)

        self._apply_styles()
        self._update_section_tabs_highlight()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#cbtHeader {
                background-color: #1a56a5;
                border-bottom: 2px solid #103a71;
            }
            QPushButton#btnHeaderCalc {
                background-color: #ffffff;
                color: #1a56a5;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ffffff;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton#btnHeaderCalc:hover {
                background-color: #e0f2fe;
            }
            QFrame#secTabBar {
                background-color: #e2e8f0;
                border-bottom: 1px solid #cbd5e1;
            }
            QPushButton#secTabButton {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #94a3b8;
                border-radius: 3px;
                font-weight: 600;
                font-size: 11px;
                padding: 4px 10px;
            }
            QPushButton#secTabButton:checked {
                background-color: #1a56a5;
                color: #ffffff;
                border: 1px solid #1a56a5;
            }
            QPushButton#btnTogglePalette {
                background-color: #cbd5e1;
                color: #334155;
                border: none;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton#btnTogglePalette:hover {
                background-color: #94a3b8;
                color: #ffffff;
            }
            QFrame#cbtFooter {
                background-color: #f1f5f9;
                border-top: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            QPushButton#btnMarkReview {
                background-color: #7c3aed;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #6d28d9;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton#btnMarkReview:hover {
                background-color: #6d28d9;
            }
            QPushButton#btnClearResponse {
                background-color: #ffffff;
                color: #dc2626;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ef4444;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton#btnClearResponse:hover {
                background-color: #fee2e2;
            }
            QPushButton#btnNav {
                background-color: #ffffff;
                color: #1e3a8a;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #3b82f6;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton#btnNav:hover {
                background-color: #eff6ff;
            }
            QPushButton#btnSaveNext {
                background-color: #16a34a;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #15803d;
                border-radius: 4px;
                padding: 6px 20px;
            }
            QPushButton#btnSaveNext:hover {
                background-color: #15803d;
            }
        """)

    def start_exam(self):
        """Starts timer, enables proctoring security and fullscreen."""
        self.timer_widget.start()
        self.security_mgr.start_exam_security()

    def _toggle_calculator(self):
        if self.calculator.isVisible():
            self.calculator.hide()
        else:
            self.calculator.show()
            self.calculator.raise_()
            self.calculator.activateWindow()

    def _toggle_palette(self):
        self.is_palette_collapsed = not self.is_palette_collapsed
        if self.is_palette_collapsed:
            self.palette.hide()
            self.btn_toggle_palette.setText("◀")
            self.btn_toggle_palette.setToolTip("Expand Side Palette")
        else:
            self.palette.show()
            self.btn_toggle_palette.setText("▶")
            self.btn_toggle_palette.setToolTip("Collapse Side Palette")

    def _load_active_question(self):
        if 0 <= self.current_index < len(self.all_questions):
            q = self.all_questions[self.current_index]
            
            # If question was unvisited, mark it NOT_ANSWERED as per TCS iON rules once visited
            if q.status == QuestionStatus.NOT_VISITED:
                q.status = QuestionStatus.NOT_ANSWERED
                q.visited = True

            self.q_display.load_question(q)
            self.palette.set_active_question(self.current_index)
            self.palette.set_section_title(q.section_name)
            self.palette.update_question_state(self.current_index, q.status, is_current=True)
            self.palette.update_counts(self.all_questions)

            # Prev button disabled on first question
            self.btn_prev.setEnabled(self.current_index > 0)
            self._update_section_tabs_highlight()

    def _save_current_response(self):
        if 0 <= self.current_index < len(self.all_questions):
            q = self.all_questions[self.current_index]
            resp = self.q_display.get_candidate_response()
            q.candidate_answer = resp

            # Synchronize QuestionStatus based on whether candidate gave a response
            if q.is_answered():
                if q.status in (QuestionStatus.MARKED_FOR_REVIEW, QuestionStatus.ANSWERED_AND_MARKED):
                    q.status = QuestionStatus.ANSWERED_AND_MARKED
                else:
                    q.status = QuestionStatus.ANSWERED
            else:
                if q.status in (QuestionStatus.MARKED_FOR_REVIEW, QuestionStatus.ANSWERED_AND_MARKED):
                    q.status = QuestionStatus.MARKED_FOR_REVIEW
                else:
                    q.status = QuestionStatus.NOT_ANSWERED

            self.palette.update_question_state(self.current_index, q.status, is_current=True)
            self.palette.update_counts(self.all_questions)

    def _on_candidate_response_changed(self):
        """Immediately captures and synchronizes candidate answers (MSQ checkboxes, MCQs, NAT)."""
        self._save_current_response()

    def _on_save_and_next(self):
        """Saves current response and navigates to the next question."""
        if 0 <= self.current_index < len(self.all_questions):
            self._save_current_response()
            
            # Advance
            if self.current_index < len(self.all_questions) - 1:
                self.current_index += 1
                self._load_active_question()

    def _on_mark_for_review_next(self):
        """Marks current question for review and advances to next question."""
        if 0 <= self.current_index < len(self.all_questions):
            q = self.all_questions[self.current_index]
            resp = self.q_display.get_candidate_response()
            q.candidate_answer = resp

            if q.is_answered():
                # Evaluated in GATE
                q.status = QuestionStatus.ANSWERED_AND_MARKED
            else:
                # Not evaluated
                q.status = QuestionStatus.MARKED_FOR_REVIEW

            self.palette.update_question_state(self.current_index, q.status)
            self.palette.update_counts(self.all_questions)

            # Advance
            if self.current_index < len(self.all_questions) - 1:
                self.current_index += 1
                self._load_active_question()

    def _on_clear_response(self):
        """Clears chosen answer for the active question."""
        if 0 <= self.current_index < len(self.all_questions):
            q = self.all_questions[self.current_index]
            self.q_display.clear_response()
            q.candidate_answer = None
            q.status = QuestionStatus.NOT_ANSWERED
            self.palette.update_question_state(self.current_index, q.status, is_current=True)
            self.palette.update_counts(self.all_questions)

    def _on_previous_question(self):
        if self.current_index > 0:
            self._save_current_response()
            self.current_index -= 1
            self._load_active_question()

    def _on_palette_question_clicked(self, idx: int):
        if 0 <= idx < len(self.all_questions):
            self._save_current_response()
            self.current_index = idx
            self._load_active_question()

    def _on_section_tab_clicked(self, section_id: str):
        self._save_current_response()
        # Find first question with this section_id
        for i, q in enumerate(self.all_questions):
            if q.section_id == section_id:
                self.current_index = i
                self._load_active_question()
                break

    def _update_section_tabs_highlight(self):
        if 0 <= self.current_index < len(self.all_questions):
            curr_sec_id = self.all_questions[self.current_index].section_id
            for i, sec in enumerate(self.paper.sections):
                if i < len(self.sec_tab_buttons):
                    self.sec_tab_buttons[i].setChecked(sec.section_id == curr_sec_id)

    def _on_second_ticked(self, elapsed_seconds: int):
        if 0 <= self.current_index < len(self.all_questions):
            self.all_questions[self.current_index].time_spent_seconds += 1

    def _open_question_paper_dialog(self):
        dlg = QuestionPaperDialog(self.paper, self)
        dlg.exec()

    def _open_instructions_dialog(self):
        dlg = InstructionsDialog(self.paper.exam_type, self)
        dlg.exec()

    def _prompt_submit_confirmation(self):
        self._save_current_response()
        dlg = SubmitConfirmationDialog(self.paper, self)
        if dlg.exec():
            self._finalize_and_submit()

    def _on_exit_exam(self):
        """Allows safely exiting the exam without submitting."""
        reply = QMessageBox.question(
            self,
            "Exit Examination",
            "Are you sure you want to exit the examination without submitting?<br><br>"
            "<i>Your progress will not be saved and this attempt will not be scored.</i>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.timer_widget.stop()
            self.security_mgr.stop_exam_security()
            if self.calculator.isVisible():
                self.calculator.hide()
            self.exit_to_dashboard.emit()


    def _on_time_expired(self):
        QMessageBox.information(
            self,
            "TIME EXPIRED",
            "The exam duration has ended. Your paper is being automatically submitted for evaluation."
        )
        self._finalize_and_submit()

    def _auto_submit_on_breach(self):
        self._finalize_and_submit()

    def _finalize_and_submit(self):
        """Concludes the exam, turns off proctoring, evaluates paper, and emits result."""
        self.timer_widget.stop()
        self.security_mgr.stop_exam_security()
        if self.calculator.isVisible():
            self.calculator.hide()

        # Save last response
        self._save_current_response()

        # Evaluate
        result = ExamEvaluator.evaluate_paper(
            paper=self.paper,
            student_name=self.student_name,
            roll_number=self.roll_number,
            duration_taken_seconds=self.timer_widget.elapsed_seconds
        )

        # Persist to disk
        try:
            self.storage_manager.save_attempt(result)
        except Exception as e:
            print(f"Error saving attempt: {e}")

        # Emit completion
        self.exam_completed.emit(result)
