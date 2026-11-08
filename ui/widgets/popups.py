"""
CBT Exam Popups and Modal Dialogs:
- Question Paper View (Scrollable all-question preview)
- Instructions Modal
- Exam Submission Summary Dialog (Official TCS iON table)
"""

from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QWidget, QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from core.models import ExamPaper, Question, QuestionType, QuestionStatus, Section


class QuestionPaperDialog(QDialog):
    """Displays all questions of the paper in one continuous scrollable view."""

    def __init__(self, paper: ExamPaper, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Question Paper - {paper.title}")
        self.resize(850, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header
        header = QLabel(f"<h3>{paper.title} - Question Paper</h3>")
        header.setStyleSheet("color: #1e3a8a;")
        layout.addWidget(header)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(16)

        for q in paper.all_questions:
            q_box = QFrame()
            q_box.setStyleSheet("""
                QFrame {
                    background-color: #f8fafc;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            qb_layout = QVBoxLayout(q_box)
            qb_layout.setSpacing(6)

            # Top label
            top_lbl = QLabel(f"<b>Question {q.question_number}</b> | {q.section_name} | Type: {q.type.value} | Marks: +{q.positive_marks} / -{q.negative_marks}")
            top_lbl.setStyleSheet("color: #0284c7; font-size: 12px;")
            qb_layout.addWidget(top_lbl)

            # Question Text
            q_txt = QLabel(f"<div>{q.question_text.replace(chr(10), '<br>')}</div>")
            q_txt.setWordWrap(True)
            q_txt.setStyleSheet("color: #0f172a; font-size: 13px;")
            qb_layout.addWidget(q_txt)

            # Options
            if q.options:
                opt_txt = "<br>".join([f"&nbsp;&nbsp;<b>({opt.id})</b> {opt.text}" for opt in q.options])
                opt_lbl = QLabel(f"<div>{opt_txt}</div>")
                opt_lbl.setStyleSheet("color: #334155; font-size: 12px; margin-top: 4px;")
                qb_layout.addWidget(opt_lbl)

            c_layout.addWidget(q_box)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(100)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #005a9e;
                color: #ffffff;
                font-weight: bold;
                padding: 6px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #004578; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)


class InstructionsDialog(QDialog):
    """Displays exam instructions and palette symbol definitions."""

    def __init__(self, exam_type: str = "GATE", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exam Instructions")
        self.resize(750, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(f"<h2>{exam_type} Computer Based Test (CBT) Instructions</h2>")
        title.setStyleSheet("color: #1e3a8a;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        c_layout = QVBoxLayout(container)

        text = f"""
        <div style="font-family: 'Segoe UI', Arial; font-size: 13px; line-height: 1.6; color: #1e293b;">
            <b>General Instructions:</b>
            <ol>
                <li>Total duration of the examination is <b>180 minutes</b> (3 hours).</li>
                <li>The clock will be set at the server. The countdown timer at the top right corner of screen will display the remaining time available for you to complete the examination. When the timer reaches zero, the examination will end by itself. You will not be required to end or submit your examination.</li>
                <li>The Question Palette displayed on the right side of screen will show the status of each question using one of the following symbols:
                    <ul>
                        <li><span style="color:#6b7280; font-weight:bold;">Gray Box:</span> You have not visited the question yet.</li>
                        <li><span style="color:#e05342; font-weight:bold;">Red/Orange Shield:</span> You have not answered the question.</li>
                        <li><span style="color:#22c55e; font-weight:bold;">Green Shield:</span> You have answered the question.</li>
                        <li><span style="color:#7c3aed; font-weight:bold;">Purple Circle:</span> You have NOT answered the question, but have marked the question for review.</li>
                        <li><span style="color:#7c3aed; font-weight:bold;">Purple with Green Dot:</span> The question(s) "Answered and Marked for Review" will be considered for evaluation.</li>
                    </ul>
                </li>
            </ol>
            <b>Navigating to a Question:</b>
            <ul>
                <li>To answer a question, click on the question number in the Question Palette to go to that question directly.</li>
                <li>Click on <b>Save & Next</b> to save your answer for the current question and then go to the next question.</li>
                <li>Click on <b>Mark for Review & Next</b> to save your answer if selected, mark it for review, and go to the next question.</li>
            </ul>
            <b>Answering Questions:</b>
            <ul>
                <li><b>MCQ (Multiple Choice Questions):</b> Each question has 4 options with only ONE correct answer. Negative marking applies (-1/3 for 1 mark, -2/3 for 2 marks).</li>
                <li><b>MSQ (Multiple Select Questions):</b> Each question has 4 options with ONE OR MORE correct answers. Full marks are awarded only if all correct choices and NO wrong choices are selected. ZERO negative marking.</li>
                <li><b>NAT (Numerical Answer Type):</b> For each question, candidate must enter numeric answer. On-screen numeric keypad or keyboard may be used. ZERO negative marking.</li>
            </ul>
            <b>Security & Proctoring:</b>
            <ul>
                <li>Exam runs in <b>Strict Fullscreen Kiosk Mode</b>.</li>
                <li>Switching windows (Alt+Tab, Windows key, clicking out) is monitored. Max 3 warnings allowed before auto-submission!</li>
            </ul>
        </div>
        """
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        c_layout.addWidget(lbl)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        btn_close = QPushButton("I Understand")
        btn_close.setFixedWidth(120)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #005a9e;
                color: #ffffff;
                font-weight: bold;
                padding: 6px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #004578; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)


class SubmitConfirmationDialog(QDialog):
    """Official TCS iON Exam Submission Summary Table Dialog with Detailed Selection & Status View."""

    def __init__(self, paper: ExamPaper, parent=None):
        super().__init__(parent)
        self.paper = paper
        self.setWindowTitle("Exam Summary & Submission")
        self.resize(860, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header Title
        title = QLabel(f"<h3>{paper.title} - Exam Summary & Submission</h3>")
        title.setStyleSheet("color: #1e3a8a; margin: 0;")
        layout.addWidget(title)

        # Tabs: Section Summary vs Detailed Question Status
        self.tabs = QTabWidget()
        self.tabs.setObjectName("submitDialogTabs")
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 18px;
                border: 1px solid #cbd5e1;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1e3a8a;
                border-bottom: 2px solid #1e3a8a;
            }
        """)

        # Tab 1: Section Summary (Official TCS iON)
        tab_section = QWidget()
        ts_layout = QVBoxLayout(tab_section)
        ts_layout.setContentsMargins(10, 10, 10, 10)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Section Name", "No. of Questions", "Answered", 
            "Not Answered", "Marked for Review", 
            "Ans & Marked (Evaluated)", "Not Visited"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #cbd5e1;
                font-family: 'Segoe UI', Arial;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #e2e8f0;
                color: #1e293b;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #cbd5e1;
            }
        """)

        self.table.setRowCount(len(paper.sections) + 1)
        tot_q = tot_ans = tot_not_ans = tot_m = tot_am = tot_nv = 0

        for r, sec in enumerate(paper.sections):
            q_cnt = len(sec.questions)
            ans = sum(1 for q in sec.questions if q.status == QuestionStatus.ANSWERED)
            not_ans = sum(1 for q in sec.questions if q.status == QuestionStatus.NOT_ANSWERED)
            m_rev = sum(1 for q in sec.questions if q.status == QuestionStatus.MARKED_FOR_REVIEW)
            am_rev = sum(1 for q in sec.questions if q.status == QuestionStatus.ANSWERED_AND_MARKED)
            nv = sum(1 for q in sec.questions if q.status == QuestionStatus.NOT_VISITED)

            tot_q += q_cnt
            tot_ans += ans
            tot_not_ans += not_ans
            tot_m += m_rev
            tot_am += am_rev
            tot_nv += nv

            self._set_cell(self.table, r, 0, sec.section_name, bold=True)
            self._set_cell(self.table, r, 1, str(q_cnt))
            self._set_cell(self.table, r, 2, str(ans), color="#15803d")
            self._set_cell(self.table, r, 3, str(not_ans), color="#b91c1c")
            self._set_cell(self.table, r, 4, str(m_rev), color="#6d28d9")
            self._set_cell(self.table, r, 5, str(am_rev), color="#6d28d9")
            self._set_cell(self.table, r, 6, str(nv), color="#4b5563")

        # Total row
        last_r = len(paper.sections)
        self._set_cell(self.table, last_r, 0, "TOTAL", bold=True)
        self._set_cell(self.table, last_r, 1, str(tot_q), bold=True)
        self._set_cell(self.table, last_r, 2, str(tot_ans), bold=True, color="#15803d")
        self._set_cell(self.table, last_r, 3, str(tot_not_ans), bold=True, color="#b91c1c")
        self._set_cell(self.table, last_r, 4, str(tot_m), bold=True, color="#6d28d9")
        self._set_cell(self.table, last_r, 5, str(tot_am), bold=True, color="#6d28d9")
        self._set_cell(self.table, last_r, 6, str(tot_nv), bold=True, color="#4b5563")

        ts_layout.addWidget(self.table, 1)
        self.tabs.addTab(tab_section, "📊 Section Summary (TCS iON)")

        # Tab 2: Detailed Question Selection & Response Status
        tab_detail = QWidget()
        td_layout = QVBoxLayout(tab_detail)
        td_layout.setContentsMargins(10, 10, 10, 10)
        td_layout.setSpacing(8)

        # Filter bar
        filt_h = QHBoxLayout()
        filt_h.addWidget(QLabel("<b>Filter Questions:</b>"))
        self.cb_filter = QComboBox()
        self.cb_filter.addItems([
            "All Questions",
            "MSQ Questions Only",
            "MCQ Questions Only",
            "NAT Questions Only",
            "Answered Questions Only",
            "Unattempted Questions Only"
        ])
        self.cb_filter.currentTextChanged.connect(self._populate_detail_table)
        filt_h.addWidget(self.cb_filter)
        filt_h.addStretch()
        td_layout.addLayout(filt_h)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(6)
        self.detail_table.setHorizontalHeaderLabels([
            "Q No.", "Section", "Type", "Status", "Candidate Selection / Response", "Marks (+ / -)"
        ])
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.detail_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #cbd5e1;
                font-family: 'Segoe UI', Arial;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #e2e8f0;
                color: #1e293b;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #cbd5e1;
            }
        """)
        td_layout.addWidget(self.detail_table, 1)

        self._populate_detail_table()
        self.tabs.addTab(tab_detail, "📋 Detailed Question Selection & Responses")

        layout.addWidget(self.tabs, 1)

        # Warning text
        warn = QLabel("<b>Are you sure you want to submit the examination?</b><br>You will NOT be able to modify your answers after final submission.")
        warn.setStyleSheet("color: #b91c1c; font-size: 13px;")
        warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warn)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_cancel = QPushButton("No, Back to Exam")
        btn_cancel.setFixedSize(140, 36)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Yes, Submit Paper")
        btn_confirm.setFixedSize(140, 36)
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #15803d;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #166534; }
        """)
        btn_confirm.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_confirm)
        btn_row.addStretch()

        layout.addLayout(btn_row)

    def _populate_detail_table(self):
        filt = self.cb_filter.currentText()
        all_q = self.paper.all_questions
        matched = []

        for q in all_q:
            if filt == "MSQ Questions Only" and q.type != QuestionType.MSQ:
                continue
            if filt == "MCQ Questions Only" and q.type != QuestionType.MCQ:
                continue
            if filt == "NAT Questions Only" and q.type != QuestionType.NAT:
                continue
            if filt == "Answered Questions Only" and not q.is_answered():
                continue
            if filt == "Unattempted Questions Only" and q.is_answered():
                continue
            matched.append(q)

        self.detail_table.setRowCount(len(matched))
        for r, q in enumerate(matched):
            # Q num
            self._set_cell(self.detail_table, r, 0, str(q.question_number), bold=True)
            # Section
            self._set_cell(self.detail_table, r, 1, q.section_name)
            # Type
            type_color = "#1e3a8a" if q.type == QuestionType.MCQ else ("#7c3aed" if q.type == QuestionType.MSQ else "#b45309")
            self._set_cell(self.detail_table, r, 2, q.type.value, bold=True, color=type_color)
            
            # Status
            stat_str = q.status.value.replace("_", " ").title()
            stat_color = "#15803d" if q.is_answered() else "#b91c1c"
            self._set_cell(self.detail_table, r, 3, stat_str, bold=True, color=stat_color)

            # Response Selection
            if q.candidate_answer is not None and q.is_answered():
                if isinstance(q.candidate_answer, list):
                    resp_str = ", ".join(f"Option ({x})" for x in q.candidate_answer)
                elif q.type == QuestionType.MCQ:
                    resp_str = f"Option ({q.candidate_answer})"
                else:
                    resp_str = str(q.candidate_answer)
                resp_color = "#15803d"
            else:
                resp_str = "(Unattempted)"
                resp_color = "#94a3b8"
            self._set_cell(self.detail_table, r, 4, resp_str, bold=bool(q.is_answered()), color=resp_color)

            # Marks
            marks_str = f"+{q.positive_marks} / -{q.negative_marks}"
            self._set_cell(self.detail_table, r, 5, marks_str)

    def _set_cell(self, table: QTableWidget, row: int, col: int, text: str, bold: bool = False, color: str = "#0f172a"):
        item = QTableWidgetItem(text)
        align = Qt.AlignmentFlag.AlignCenter if col not in (0, 1, 4) else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        item.setTextAlignment(align)
        font = QFont("Segoe UI", 10)
        font.setBold(bold)
        item.setFont(font)
        item.setForeground(QColor(color))
        table.setItem(row, col, item)
