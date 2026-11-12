"""
Layer 1: Exam Selection Portal.
Students select which Examination portal to enter (GATE, JEE Main, NEET, etc.).
Designed for seamless extensibility.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QFrame, QScrollArea, QInputDialog, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.storage import StorageManager
from ui.widgets.profile_dialog import UserProfileDialog


class ExamCard(QFrame):
    selected = pyqtSignal(str)   # Emits exam_type

    def __init__(
        self,
        exam_id: str,
        title: str,
        subtitle: str,
        badge_text: str,
        color_theme: str,
        features: List[str],
        paper_count: int,
        is_active: bool = True,
        chips: Optional[List[tuple]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.exam_id = exam_id
        self.title = title
        self.color_theme = color_theme
        self.is_active = is_active
        self.chips = chips
        self.setObjectName("examPortalCard")

        # Constrain dimensions so the card does not take up all horizontal/vertical space
        self.setMaximumWidth(580)
        self.setMinimumWidth(440)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._init_ui(subtitle, badge_text, features, paper_count)

    def _init_ui(self, subtitle: str, badge_text: str, features: List[str], paper_count: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        # Top Badge & Count
        top_h = QHBoxLayout()
        badge = QLabel(badge_text)
        badge.setStyleSheet(f"""
            background-color: {self.color_theme}15;
            color: {self.color_theme};
            font-size: 11px;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid {self.color_theme}40;
        """)
        top_h.addWidget(badge)
        top_h.addStretch()

        cnt_lbl = QLabel(f"<b>{paper_count}</b> Papers Available")
        cnt_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        top_h.addWidget(cnt_lbl)
        layout.addLayout(top_h)

        # Title
        t_lbl = QLabel(self.title)
        t_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        t_lbl.setStyleSheet(f"color: {self.color_theme};")
        layout.addWidget(t_lbl)

        # Subtitle
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: #475569; font-size: 12px;")
        sub_lbl.setWordWrap(True)
        layout.addWidget(sub_lbl)

        # Quick Overview Chips
        chips_h = QHBoxLayout()
        chips_h.setSpacing(8)
        if self.chips:
            for chip_text, text_col, bg_col in self.chips:
                c = QLabel(chip_text)
                c.setStyleSheet(f"background-color: {bg_col}; color: {text_col}; font-weight: 600; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
                chips_h.addWidget(c)
        else:
            c1 = QLabel("⏱ 31 Full-Length PYQs")
            c1.setStyleSheet("background-color: #f1f5f9; color: #1e3a8a; font-weight: 600; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
            c2 = QLabel("📑 72 Topic-Wise Tests")
            c2.setStyleSheet("background-color: #f1f5f9; color: #0284c7; font-weight: 600; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
            c3 = QLabel("🎯 4,780+ Questions")
            c3.setStyleSheet("background-color: #f1f5f9; color: #15803d; font-weight: 600; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
            chips_h.addWidget(c1)
            chips_h.addWidget(c2)
            chips_h.addWidget(c3)
        chips_h.addStretch()
        layout.addLayout(chips_h)

        # Features List
        feat_v = QVBoxLayout()
        feat_v.setSpacing(4)
        for f in features:
            lbl_f = QLabel(f"✓  {f}")
            lbl_f.setStyleSheet("color: #334155; font-size: 11px;")
            feat_v.addWidget(lbl_f)
        layout.addLayout(feat_v)

        layout.addSpacing(6)

        # Enter Button
        btn_enter = QPushButton(f"Enter {self.exam_id} Portal  ➔")
        btn_enter.setObjectName("btnEnterExam")
        btn_enter.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_enter.setStyleSheet(f"""
            QPushButton#btnEnterExam {{
                background-color: {self.color_theme};
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
            }}
            QPushButton#btnEnterExam:hover {{
                opacity: 0.9;
                background-color: #1e3a8a;
            }}
        """)
        btn_enter.clicked.connect(lambda: self.selected.emit(self.exam_id))
        layout.addWidget(btn_enter)

        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#examPortalCard {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
            }}
            QFrame#examPortalCard:hover {{
                border-color: {self.color_theme};
                background-color: #f8fafc;
            }}
        """)


class ExamSelectionWindow(QWidget):
    exam_selected = pyqtSignal(str)              # Emits exam_type (e.g. "GATE")
    open_dashboard_requested = pyqtSignal()
    candidate_profile_updated = pyqtSignal(str, str) # name, roll

    def __init__(
        self,
        storage_manager: Optional[StorageManager] = None,
        student_name: str = "Candidate",
        roll_number: str = "GATE24-C9801",
        parent=None
    ):
        super().__init__(parent)
        self.storage_manager = storage_manager or StorageManager()
        self.student_name = student_name
        self.roll_number = roll_number

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 24, 30, 24)
        main_layout.setSpacing(18)

        # 1. Top Header Banner
        banner = QFrame()
        banner.setObjectName("portalBanner")
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(20, 16, 20, 16)

        left_v = QVBoxLayout()
        logo_lbl = QLabel("<h1>CBT Examination Simulator</h1>")
        logo_lbl.setStyleSheet("color: #1e3a8a; margin: 0;")
        sub_lbl = QLabel("High-Fidelity Offline Computer Based Test (CBT) Simulator for GATE EC & NEET UG Medical Entrance")
        sub_lbl.setStyleSheet("color: #475569; font-size: 13px;")
        
        status_row = QHBoxLayout()
        lbl_offline = QLabel("● 100% Offline Mode")
        lbl_offline.setStyleSheet("color: #15803d; font-size: 11px; font-weight: bold;")
        lbl_sec = QLabel("● Kiosk Proctoring Security Active")
        lbl_sec.setStyleSheet("color: #0284c7; font-size: 11px; font-weight: bold;")
        status_row.addWidget(lbl_offline)
        status_row.addWidget(lbl_sec)
        status_row.addStretch()

        left_v.addWidget(logo_lbl)
        left_v.addWidget(sub_lbl)
        left_v.addLayout(status_row)
        b_layout.addLayout(left_v)
        b_layout.addStretch()

        # Right Candidate & Dashboard Box
        right_v = QVBoxLayout()
        right_v.setSpacing(6)
        
        btn_dash = QPushButton("📊 Student Dashboard & Past Stats")
        btn_dash.setObjectName("btnBannerDash")
        btn_dash.clicked.connect(self.open_dashboard_requested.emit)
        right_v.addWidget(btn_dash)

        self.lbl_profile = QLabel(f"Logged in as: <b>{self.student_name}</b> ({self.roll_number})")
        self.lbl_profile.setStyleSheet("color: #475569; font-size: 11px;")
        right_v.addWidget(self.lbl_profile)

        btn_edit_profile = QPushButton("✎ Edit Candidate Details")
        btn_edit_profile.setObjectName("btnEditProfile")
        btn_edit_profile.clicked.connect(self._edit_profile_dialog)
        right_v.addWidget(btn_edit_profile)

        b_layout.addLayout(right_v)
        main_layout.addWidget(banner)

        # 2. Section Heading
        sec_heading = QLabel("<h3>Examination Portal (Layer 1)</h3>")
        sec_heading.setStyleSheet("color: #0f172a;")
        main_layout.addWidget(sec_heading)

        # 3. Grid of Exam Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("portalScroll")

        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setContentsMargins(10, 20, 10, 20)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self._populate_exam_cards()

        scroll.setWidget(grid_widget)
        main_layout.addWidget(scroll, 1)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#portalBanner {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
            }
            QPushButton#btnBannerDash {
                background-color: #1e3a8a;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton#btnBannerDash:hover {
                background-color: #172554;
            }
            QPushButton#btnEditProfile {
                background-color: #f1f5f9;
                color: #334155;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QPushButton#btnEditProfile:hover {
                background-color: #e2e8f0;
            }
            QScrollArea#portalScroll {
                background-color: transparent;
                border: none;
            }
        """)

    def _populate_exam_cards(self):
        # Clear existing cards first if any
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Count available papers
        all_papers = self.storage_manager.load_all_papers()
        gate_cnt = sum(1 for p in all_papers if p.exam_type.upper() == "GATE")
        neet_cnt = sum(1 for p in all_papers if p.exam_type.upper() in ("NEET", "NEET UG"))

        exams_config = [
            {
                "id": "GATE",
                "title": "GATE (Graduate Aptitude Test in Engineering)",
                "subtitle": "Official Previous Year Papers (PYQ 2000–2026) and 72 Topic-wise Chapter Tests with full formulas, diagrams, calculator, and evaluation.",
                "badge": "★ PRIMARY & ACTIVE",
                "color": "#1a56a5",
                "chips": [
                    ("⏱ 31 Full-Length PYQs", "#1e3a8a", "#f1f5f9"),
                    ("📑 72 Topic-Wise Tests", "#0284c7", "#f1f5f9"),
                    ("🎯 4,780+ Questions", "#15803d", "#f1f5f9")
                ],
                "features": [
                    "Official GATE TCS iON Scientific Virtual Calculator",
                    "MCQ (+1/-0.33, +2/-0.67), MSQ (No neg), NAT (Virtual Keypad)",
                    "31 Full-Length PYQ Papers (2000–2026) & 72 Topic-wise Practice Tests (4,780+ Questions)",
                    "Exact Question Palette with Answered & Marked for Review dot badge",
                    "100% Offline Mode with Strict Fullscreen Proctoring"
                ],
                "count": gate_cnt
            },
            {
                "id": "NEET",
                "title": "NEET UG (National Eligibility cum Entrance Test)",
                "subtitle": "Official PYQs (AIPMT 1988–2015 & NEET 2013–2026) and 95 Topic-wise Physics, Chemistry, and Biology modules with official +4/-1 grading.",
                "badge": "★ NEW CBT SIMULATOR",
                "color": "#0d9488",
                "chips": [
                    ("⏱ 51 Full-Length PYQs", "#042f2e", "#ccfbf1"),
                    ("📑 95 Topic-Wise Tests", "#0f766e", "#f0fdfa"),
                    ("🎯 18,870+ Questions", "#15803d", "#f0fdf4"),
                    ("⚠️ 15 Out-of-Syllabus Tagged", "#b45309", "#fef3c7")
                ],
                "features": [
                    "Official NTA NEET CBT Exam Simulation Mode",
                    "Standard NEET +4 / -1 Marking Scheme (+4 Correct, -1 Incorrect, 0 Unattempted)",
                    "146 Total Papers: 51 Full-Length & 95 Topic-Wise Modules",
                    "15 Out-of-Syllabus Chapters clearly flagged and segregated for practice",
                    "Physics, Chemistry, Botany, and Zoology sections with full high-resolution diagrams",
                    "Complete local offline attempts tracking and comprehensive review"
                ],
                "count": neet_cnt
            }
        ]

        for i, conf in enumerate(exams_config):
            card = ExamCard(
                exam_id=conf["id"],
                title=conf["title"],
                subtitle=conf["subtitle"],
                badge_text=conf["badge"],
                color_theme=conf["color"],
                features=conf["features"],
                paper_count=conf["count"],
                chips=conf.get("chips")
            )
            card.selected.connect(self.exam_selected.emit)
            self.grid_layout.addWidget(card, 0, i, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

    def set_candidate_profile(self, name: str, roll: str, phone: str = ""):
        self.student_name = name
        self.roll_number = roll
        self.phone_number = phone
        phone_part = f" | 📱 {phone}" if phone else ""
        self.lbl_profile.setText(f"Logged in as: <b>{self.student_name}</b> ({self.roll_number}){phone_part}")

    def _edit_profile_dialog(self):
        dlg = UserProfileDialog(self.storage_manager, self)
        if dlg.exec():
            prof = self.storage_manager.load_user_profile()
            self.set_candidate_profile(
                prof.get("name", "Candidate"),
                prof.get("roll_number", "GATE25-EC001"),
                prof.get("phone_number", "")
            )
            self.candidate_profile_updated.emit(self.student_name, self.roll_number)
