"""
Layer 3 (Pre-Exam Step): Official Candidate Instructions and Declaration Screen.
Precedes the live fullscreen exam. Candidate must check the declaration
to enable 'I am ready to begin'.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QComboBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.models import ExamPaper


class InstructionsScreen(QWidget):
    start_exam_requested = pyqtSignal()
    back_to_papers_requested = pyqtSignal()

    def __init__(self, paper: ExamPaper, student_name: str = "Candidate", roll_number: str = "GATE24-C9801", parent=None):
        super().__init__(parent)
        self.paper = paper
        self.student_name = student_name
        self.roll_number = roll_number

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # 1. Header with Paper Title & Candidate profile preview
        header_card = QFrame()
        header_card.setObjectName("instHeader")
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(16, 12, 16, 12)

        v_left = QVBoxLayout()
        title_lbl = QLabel(f"<h2>{self.paper.title}</h2>")
        title_lbl.setStyleSheet("color: #1e3a8a; margin: 0;")
        meta_lbl = QLabel(f"Exam: <b>{self.paper.exam_type}</b> | Duration: <b>{self.paper.duration_minutes} Mins</b> | Total Marks: <b>{self.paper.total_marks}</b> | Total Questions: <b>{self.paper.total_questions_count}</b>")
        meta_lbl.setStyleSheet("color: #475569; font-size: 13px;")
        v_left.addWidget(title_lbl)
        v_left.addWidget(meta_lbl)

        h_layout.addLayout(v_left)
        h_layout.addStretch()

        # Candidate Box
        cand_frame = QFrame()
        cand_frame.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px;")
        cf_layout = QHBoxLayout(cand_frame)
        photo_lbl = QLabel("👤")
        photo_lbl.setStyleSheet("font-size: 28px;")
        info_v = QVBoxLayout()
        info_v.setSpacing(2)
        info_v.addWidget(QLabel(f"<b>{self.student_name}</b>"))
        info_v.addWidget(QLabel(f"Roll: {self.roll_number}"))
        cf_layout.addWidget(photo_lbl)
        cf_layout.addLayout(info_v)
        h_layout.addWidget(cand_frame)

        main_layout.addWidget(header_card)

        # 2. Scrollable Instructions Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("instScroll")
        
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(16, 16, 16, 16)
        c_layout.setSpacing(12)

        inst_html = f"""
        <div style="font-family: 'Segoe UI', Arial; font-size: 13px; line-height: 1.6; color: #1e293b;">
            <h3 style="color:#0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px;">General Examination Instructions</h3>
            <ol>
                <li>Total duration of this examination is <b>{self.paper.duration_minutes} minutes</b>.</li>
                <li>The clock will be set at the server. The countdown timer at the top right corner of the screen will display remaining time.</li>
                <li>When the timer reaches zero, the examination will end automatically.</li>
                <li>The Question Palette displayed on the right side of the screen shows the status of each question using official symbols:
                    <ul>
                        <li><b style="color:#64748b;">[1] Gray:</b> You have not visited the question yet.</li>
                        <li><b style="color:#e05342;">[2] Orange-Red:</b> You have not answered the question.</li>
                        <li><b style="color:#16a34a;">[3] Green:</b> You have answered the question.</li>
                        <li><b style="color:#7c3aed;">[4] Purple Circle:</b> You have NOT answered the question, but have marked it for review.</li>
                        <li><b style="color:#7c3aed;">[5] Purple with Green Dot:</b> The question(s) <b>Answered and Marked for Review</b> WILL BE EVALUATED.</li>
                    </ul>
                </li>
            </ol>

            <h3 style="color:#0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px;">Question Types & Marking Scheme</h3>
            <ul>
                <li><b>MCQ (Multiple Choice Questions):</b> Each question has four choices (A, B, C, D) with ONLY ONE correct answer.
                    <br>• Correct: Full marks awarded (+1 or +2)
                    <br>• Incorrect: Negative marking applies (-1/3 for 1-mark, -2/3 for 2-mark)
                </li>
                <li><b>MSQ (Multiple Select Questions):</b> Each question has four choices with ONE OR MORE correct answers.
                    <br>• Correct: Full marks awarded (+1 or +2) ONLY if all correct choices are selected and NO wrong choices are selected.
                    <br>• Incorrect / Partial: 0 marks. <b>NO NEGATIVE MARKING</b>.
                </li>
                <li><b>NAT (Numerical Answer Type):</b> Candidate must enter numerical answer using either keyboard or on-screen numeric keypad.
                    <br>• Correct: Full marks awarded (+1 or +2) if entered answer falls within acceptable range or matches exact value.
                    <br>• Incorrect: 0 marks. <b>NO NEGATIVE MARKING</b>.
                </li>
            </ul>

            <h3 style="color:#0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px;">Important Security & Proctoring Instructions</h3>
            <ul>
                <li>Once you click <b>'I am ready to begin'</b>, the exam will launch in <b>STRICT FULLSCREEN KIOSK MODE</b>.</li>
                <li>Pressing <b>Alt+Tab, Windows key, clicking outside the window, or launching external software</b> is strictly recorded as a security breach.</li>
                <li>Maximum <b>3 warnings</b> will be issued. On the 3rd breach, your test will be <b>TERMINATED AND AUTO-SUBMITTED IMMEDIATELY</b>.</li>
                <li>An authentic <b>GATE Virtual Scientific Calculator</b> is available on screen during the test via the top-bar button.</li>
            </ul>
        </div>
        """
        lbl_content = QLabel(inst_html)
        lbl_content.setWordWrap(True)
        lbl_content.setTextFormat(Qt.TextFormat.RichText)
        c_layout.addWidget(lbl_content)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # 3. Bottom Declaration & Action Controls
        decl_box = QFrame()
        decl_box.setObjectName("instDeclBox")
        d_layout = QVBoxLayout(decl_box)
        d_layout.setContentsMargins(14, 10, 14, 10)
        d_layout.setSpacing(10)

        # Language selection
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Choose your default language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Hindi"])
        self.lang_combo.setFixedWidth(140)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        d_layout.addLayout(lang_row)

        # Checkbox
        self.chk_declare = QCheckBox(
            "I have read and understood the instructions. All computer hardware allotted to me is in proper working condition. "
            "I agree that in case of not adhering to instructions or navigating away from the screen, I will be disqualified."
        )
        self.chk_declare.setStyleSheet("font-weight: 600; color: #0f172a;")
        self.chk_declare.stateChanged.connect(self._on_declaration_toggled)
        d_layout.addWidget(self.chk_declare)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_back = QPushButton("← Back to Paper List")
        self.btn_back.setObjectName("btnInstBack")
        self.btn_back.clicked.connect(self.back_to_papers_requested.emit)

        self.btn_begin = QPushButton("I AM READY TO BEGIN  ➔")
        self.btn_begin.setObjectName("btnBeginExam")
        self.btn_begin.setEnabled(False)  # Disabled until declaration checked
        self.btn_begin.clicked.connect(self.start_exam_requested.emit)

        btn_row.addWidget(self.btn_back)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_begin)
        d_layout.addLayout(btn_row)

        main_layout.addWidget(decl_box)
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#instHeader {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QScrollArea#instScroll {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QFrame#instDeclBox {
                background-color: #f8fafc;
                border: 1px solid #94a3b8;
                border-radius: 6px;
            }
            QPushButton#btnInstBack {
                background-color: #ffffff;
                color: #475569;
                font-weight: bold;
                border: 1px solid #94a3b8;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton#btnInstBack:hover {
                background-color: #f1f5f9;
            }
            QPushButton#btnBeginExam {
                background-color: #16a34a;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #15803d;
                border-radius: 4px;
                padding: 10px 24px;
            }
            QPushButton#btnBeginExam:hover {
                background-color: #15803d;
            }
            QPushButton#btnBeginExam:disabled {
                background-color: #94a3b8;
                border-color: #cbd5e1;
                color: #e2e8f0;
            }
        """)

    def _on_declaration_toggled(self, state):
        self.btn_begin.setEnabled(self.chk_declare.isChecked())
