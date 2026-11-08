"""
TCS iON / GATE Question Palette & Legend Widget.
Displays candidate details, real-time status counts, legend badges,
and question navigation grid.
"""

from typing import List, Dict, Callable, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen

from core.models import Question, QuestionStatus, Section


class QuestionBadgeButton(QPushButton):
    """Custom styled button representing a question number with TCS iON badge graphics."""
    
    def __init__(self, q_num: int, parent=None):
        super().__init__(str(q_num), parent)
        self.q_num = q_num
        self.status = QuestionStatus.NOT_VISITED
        self.is_current = False
        self.setFixedSize(40, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_appearance()

    def set_status(self, status: QuestionStatus, is_current: bool = False):
        self.status = status
        self.is_current = is_current
        self._update_appearance()

    def _update_appearance(self):
        # Specific styling per status
        border = "2px solid #005a9e" if self.is_current else "1px solid #777777"
        
        if self.status == QuestionStatus.NOT_VISITED:
            bg = "#e5e7eb"
            color = "#1f2937"
            border_radius = "3px"
        elif self.status == QuestionStatus.NOT_ANSWERED:
            bg = "#e05342"
            color = "#ffffff"
            border_radius = "12px 12px 3px 3px"
        elif self.status == QuestionStatus.ANSWERED:
            bg = "#22c55e"
            color = "#ffffff"
            border_radius = "3px 3px 12px 12px"
        elif self.status == QuestionStatus.MARKED_FOR_REVIEW:
            bg = "#7c3aed"
            color = "#ffffff"
            border_radius = "18px"
        elif self.status == QuestionStatus.ANSWERED_AND_MARKED:
            bg = "#7c3aed"
            color = "#ffffff"
            border_radius = "18px"
        else:
            bg = "#e5e7eb"
            color = "#1f2937"
            border_radius = "3px"

        style = f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                font-family: 'Segoe UI', Arial;
                font-weight: bold;
                font-size: 13px;
                border: {border};
                border-radius: {border_radius};
            }}
            QPushButton:hover {{
                opacity: 0.85;
                border: 2px solid #2563eb;
            }}
        """
        self.setStyleSheet(style)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        # For ANSWERED_AND_MARKED, draw small green badge at bottom-right corner
        if self.status == QuestionStatus.ANSWERED_AND_MARKED:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor("#22c55e")))
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawEllipse(self.width() - 11, self.height() - 11, 9, 9)


class PaletteWidget(QWidget):
    question_clicked = pyqtSignal(int)      # Emits question index (0-based)
    question_paper_clicked = pyqtSignal()
    instructions_clicked = pyqtSignal()
    submit_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidePalette")
        self.setFixedWidth(310)
        
        self.buttons: List[QuestionBadgeButton] = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # 1. Candidate Info Card
        cand_card = QFrame()
        cand_card.setObjectName("paletteCandCard")
        cand_layout = QHBoxLayout(cand_card)
        cand_layout.setContentsMargins(8, 6, 8, 6)

        # Photo Box
        photo_box = QLabel("👤")
        photo_box.setFixedSize(46, 50)
        photo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_box.setObjectName("candPhoto")
        photo_box.setStyleSheet("""
            QLabel#candPhoto {
                background-color: #d1d5db;
                border: 1px solid #9ca3af;
                border-radius: 4px;
                font-size: 26px;
            }
        """)

        # Info Box
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        self.lbl_cand_name = QLabel("Candidate Name")
        self.lbl_cand_name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_roll = QLabel("Roll No: GATE24-CS01")
        self.lbl_roll.setStyleSheet("color: #4b5563; font-size: 11px;")
        info_layout.addWidget(self.lbl_cand_name)
        info_layout.addWidget(self.lbl_roll)

        cand_layout.addWidget(photo_box)
        cand_layout.addLayout(info_layout)
        cand_layout.addStretch()
        main_layout.addWidget(cand_card)

        # 2. TCS iON Official Legend Box
        legend_frame = QFrame()
        legend_frame.setObjectName("paletteLegendFrame")
        leg_layout = QGridLayout(legend_frame)
        leg_layout.setContentsMargins(6, 6, 6, 6)
        leg_layout.setHorizontalSpacing(8)
        leg_layout.setVerticalSpacing(4)

        # Helper to create legend item: [badge_lbl, count_lbl, desc_lbl]
        self.cnt_answered = QLabel("0")
        self.cnt_not_answered = QLabel("0")
        self.cnt_not_visited = QLabel("0")
        self.cnt_marked = QLabel("0")
        self.cnt_ans_marked = QLabel("0")

        # Row 0: Answered & Not Answered
        b1 = self._create_legend_badge("3", "#22c55e", "3px 3px 10px 10px")
        leg_layout.addWidget(b1, 0, 0)
        leg_layout.addWidget(self.cnt_answered, 0, 1)
        leg_layout.addWidget(QLabel("Answered"), 0, 2)

        b2 = self._create_legend_badge("2", "#e05342", "10px 10px 3px 3px")
        leg_layout.addWidget(b2, 0, 3)
        leg_layout.addWidget(self.cnt_not_answered, 0, 4)
        leg_layout.addWidget(QLabel("Not Answered"), 0, 5)

        # Row 1: Not Visited & Marked for Review
        b3 = self._create_legend_badge("1", "#9ca3af", "3px")
        leg_layout.addWidget(b3, 1, 0)
        leg_layout.addWidget(self.cnt_not_visited, 1, 1)
        leg_layout.addWidget(QLabel("Not Visited"), 1, 2)

        b4 = self._create_legend_badge("4", "#7c3aed", "14px")
        leg_layout.addWidget(b4, 1, 3)
        leg_layout.addWidget(self.cnt_marked, 1, 4)
        leg_layout.addWidget(QLabel("Marked for Review"), 1, 5)

        # Row 2: Answered & Marked for Review
        b5 = self._create_legend_badge("5", "#7c3aed", "14px", has_dot=True)
        leg_layout.addWidget(b5, 2, 0)
        leg_layout.addWidget(self.cnt_ans_marked, 2, 1)
        lbl_long = QLabel("Ans & Marked for Review\n(evaluated)")
        lbl_long.setStyleSheet("font-size: 10px; color: #374151;")
        leg_layout.addWidget(lbl_long, 2, 2, 1, 4)

        main_layout.addWidget(legend_frame)

        # 3. Section Title Header
        sec_header = QFrame()
        sec_header.setObjectName("secHeaderFrame")
        sec_h_layout = QHBoxLayout(sec_header)
        sec_h_layout.setContentsMargins(6, 4, 6, 4)
        self.lbl_active_section = QLabel("Section: All Questions")
        self.lbl_active_section.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_active_section.setStyleSheet("color: #1e3a8a;")
        sec_h_layout.addWidget(self.lbl_active_section)
        main_layout.addWidget(sec_header)

        # 4. Scrollable Question Grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("paletteScroll")
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(6)
        
        scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(scroll_area, 1)

        # 5. Bottom Action Buttons: Question Paper, Instructions, Submit
        btn_box = QVBoxLayout()
        btn_box.setSpacing(4)

        sub_h = QHBoxLayout()
        sub_h.setSpacing(4)
        
        self.btn_qp = QPushButton("Question Paper")
        self.btn_qp.setObjectName("btnQP")
        self.btn_qp.clicked.connect(self.question_paper_clicked.emit)

        self.btn_inst = QPushButton("Instructions")
        self.btn_inst.setObjectName("btnInst")
        self.btn_inst.clicked.connect(self.instructions_clicked.emit)

        sub_h.addWidget(self.btn_qp)
        sub_h.addWidget(self.btn_inst)
        btn_box.addLayout(sub_h)

        self.btn_submit = QPushButton("Submit Exam")
        self.btn_submit.setObjectName("btnSubmitExam")
        self.btn_submit.setFixedHeight(34)
        self.btn_submit.clicked.connect(self.submit_clicked.emit)
        btn_box.addWidget(self.btn_submit)

        main_layout.addLayout(btn_box)
        self._apply_styles()

    def _create_legend_badge(self, text: str, bg: str, radius: str, has_dot: bool = False) -> QLabel:
        lbl = QLabel(text)
        lbl.setFixedSize(22, 22)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl.setStyleSheet(f"""
            background-color: {bg};
            color: #ffffff;
            border-radius: {radius};
            border: 1px solid #4b5563;
        """)
        return lbl

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget#sidePalette {
                background-color: #e5eff9;
                border-left: 1px solid #b0c4de;
            }
            QFrame#paletteCandCard {
                background-color: #ffffff;
                border: 1px solid #c5d9ed;
                border-radius: 4px;
            }
            QFrame#paletteLegendFrame {
                background-color: #ffffff;
                border: 1px solid #c5d9ed;
                border-radius: 4px;
            }
            QFrame#secHeaderFrame {
                background-color: #cfe2f3;
                border-radius: 3px;
                border-left: 4px solid #1e3a8a;
            }
            QScrollArea#paletteScroll {
                background-color: #ffffff;
                border: 1px solid #c5d9ed;
                border-radius: 4px;
            }
            QPushButton#btnQP, QPushButton#btnInst {
                background-color: #3b82f6;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 4px;
                border: 1px solid #2563eb;
                border-radius: 3px;
            }
            QPushButton#btnQP:hover, QPushButton#btnInst:hover {
                background-color: #2563eb;
            }
            QPushButton#btnSubmitExam {
                background-color: #15803d;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #166534;
                border-radius: 4px;
            }
            QPushButton#btnSubmitExam:hover {
                background-color: #166534;
            }
        """)

    def set_candidate_info(self, name: str, roll_no: str):
        self.lbl_cand_name.setText(name)
        self.lbl_roll.setText(f"Roll No: {roll_no}")

    def populate_questions(self, questions: List[Question], active_idx: int = 0):
        """Populates the grid of question number buttons."""
        # Clear existing buttons
        for btn in self.buttons:
            btn.deleteLater()
        self.buttons.clear()

        cols = 5
        for i, q in enumerate(questions):
            btn = QuestionBadgeButton(q.question_number, self.grid_container)
            btn.set_status(q.status, is_current=(i == active_idx))
            btn.clicked.connect(lambda checked, idx=i: self.question_clicked.emit(idx))
            
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(btn, row, col)
            self.buttons.append(btn)

        self.update_counts(questions)

    def update_question_state(self, idx: int, status: QuestionStatus, is_current: bool = False):
        if 0 <= idx < len(self.buttons):
            self.buttons[idx].set_status(status, is_current)

    def set_active_question(self, active_idx: int):
        for i, btn in enumerate(self.buttons):
            btn.set_status(btn.status, is_current=(i == active_idx))

    def update_counts(self, questions: List[Question]):
        ans = sum(1 for q in questions if q.status == QuestionStatus.ANSWERED)
        not_ans = sum(1 for q in questions if q.status == QuestionStatus.NOT_ANSWERED)
        not_vis = sum(1 for q in questions if q.status == QuestionStatus.NOT_VISITED)
        m_rev = sum(1 for q in questions if q.status == QuestionStatus.MARKED_FOR_REVIEW)
        ans_m_rev = sum(1 for q in questions if q.status == QuestionStatus.ANSWERED_AND_MARKED)

        self.cnt_answered.setText(str(ans))
        self.cnt_not_answered.setText(str(not_ans))
        self.cnt_not_visited.setText(str(not_vis))
        self.cnt_marked.setText(str(m_rev))
        self.cnt_ans_marked.setText(str(ans_m_rev))

    def set_section_title(self, section_name: str):
        self.lbl_active_section.setText(f"Section: {section_name}")
