"""
Layer 2: Paper Inventory Browser.
Displays available Mock Papers, PYQs, and Topic-wise tests from JSON inventory.
Supports chapter/subject filters, search, paper inspection, and live attempt tracking.
"""

from typing import List, Optional, Dict, Any
import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QScrollArea, 
    QFrame, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.models import ExamPaper
from core.storage import StorageManager


class PaperCard(QFrame):
    start_clicked = pyqtSignal(object)      # Emits ExamPaper
    details_clicked = pyqtSignal(object)

    def __init__(
        self,
        paper: ExamPaper,
        last_attempt: Optional[Dict[str, Any]] = None,
        best_attempt: Optional[Dict[str, Any]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.paper = paper
        self.last_attempt = last_attempt
        self.best_attempt = best_attempt
        self.is_attempted = last_attempt is not None
        self.setObjectName("paperCardAttempted" if self.is_attempted else "paperCard")
        self.setMinimumHeight(215 if self.is_attempted else 165)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # 1. Top Category, Year & Attempt Status Row
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        cat_badge = QLabel(self.paper.category.upper())
        cat_badge.setObjectName("paperCatBadge")
        top_row.addWidget(cat_badge)

        if self.paper.year:
            year_badge = QLabel(str(self.paper.year))
            year_badge.setObjectName("paperYearBadge")
            top_row.addWidget(year_badge)

        # Attempt Status Badge
        if self.is_attempted:
            att_badge = QLabel("✓ ATTEMPTED")
            att_badge.setObjectName("badgeAttempted")
        else:
            att_badge = QLabel("○ NOT ATTEMPTED")
            att_badge.setObjectName("badgeNotAttempted")
        top_row.addWidget(att_badge)

        top_row.addStretch()

        type_lbl = QLabel(f"Exam: <b>{self.paper.exam_type}</b>")
        type_lbl.setStyleSheet("color: #475569; font-size: 11px;")
        top_row.addWidget(type_lbl)
        layout.addLayout(top_row)

        # 2. Title
        title_lbl = QLabel(self.paper.title)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #1e3a8a;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        # 3. Description
        desc_text = self.paper.description or "Official pattern mock paper adhering to exact NTA / GATE examination criteria."
        desc_lbl = QLabel(desc_text)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #4b5563; font-size: 11px;")
        layout.addWidget(desc_lbl)

        # 4. Metadata Chips Row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        chip_dur = QLabel(f"⏱ {self.paper.duration_minutes} Mins")
        chip_dur.setObjectName("metaChip")
        chip_marks = QLabel(f"🎯 {self.paper.total_marks} Marks")
        chip_marks.setObjectName("metaChip")
        chip_q = QLabel(f"❓ {self.paper.total_questions_count} Questions")
        chip_q.setObjectName("metaChip")
        chip_sec = QLabel(f"📑 {len(self.paper.sections)} Sections")
        chip_sec.setObjectName("metaChip")

        meta_row.addWidget(chip_dur)
        meta_row.addWidget(chip_marks)
        meta_row.addWidget(chip_q)
        meta_row.addWidget(chip_sec)
        meta_row.addStretch()
        layout.addLayout(meta_row)

        # 5. Two Subsections for Attempt Results (Only shown on already attempted exam cards)
        if self.is_attempted:
            results_row = QHBoxLayout()
            results_row.setSpacing(12)

            # Subsection 1: Last Attempt Result
            sub_last = QFrame()
            sub_last.setObjectName("attemptSubCardActive")
            sl_layout = QVBoxLayout(sub_last)
            sl_layout.setContentsMargins(10, 8, 10, 8)
            sl_layout.setSpacing(3)

            sl_title = QLabel("🕒 <b>Last Attempt Result</b>")
            sl_title.setStyleSheet("color: #1e3a8a; font-size: 11px;")
            sl_layout.addWidget(sl_title)

            sc = self.last_attempt.get("scoreObtained", 0.0) if self.last_attempt else 0.0
            tm = self.last_attempt.get("totalMarks", self.paper.total_marks) if self.last_attempt else self.paper.total_marks
            pct = self.last_attempt.get("percentageScore", 0.0) if self.last_attempt else 0.0
            acc = self.last_attempt.get("accuracyPercentage", 0.0) if self.last_attempt else 0.0
            ts = str(self.last_attempt.get("timestamp", ""))[:16] if self.last_attempt else ""

            sl_stats = QLabel(f"Score: <b>{sc} / {tm}</b> (<b style='color:#15803d;'>{pct}%</b>)  |  Accuracy: <b>{acc}%</b>")
            sl_stats.setStyleSheet("color: #0f172a; font-size: 12px;")
            sl_date = QLabel(f"Submitted on {ts}")
            sl_date.setStyleSheet("color: #64748b; font-size: 10px;")
            sl_layout.addWidget(sl_stats)
            sl_layout.addWidget(sl_date)
            results_row.addWidget(sub_last, 1)

            # Subsection 2: Best Attempt Result
            sub_best = QFrame()
            sub_best.setObjectName("attemptSubCardActive")
            sb_layout = QVBoxLayout(sub_best)
            sb_layout.setContentsMargins(10, 8, 10, 8)
            sb_layout.setSpacing(3)

            sb_title = QLabel("🏆 <b>Best Attempt Result</b>")
            sb_title.setStyleSheet("color: #1e3a8a; font-size: 11px;")
            sb_layout.addWidget(sb_title)

            bsc = self.best_attempt.get("scoreObtained", 0.0) if self.best_attempt else sc
            btm = self.best_attempt.get("totalMarks", self.paper.total_marks) if self.best_attempt else tm
            bpct = self.best_attempt.get("percentageScore", 0.0) if self.best_attempt else pct
            bacc = self.best_attempt.get("accuracyPercentage", 0.0) if self.best_attempt else acc

            sb_stats = QLabel(f"Score: <b>{bsc} / {btm}</b> (<b style='color:#15803d;'>{bpct}%</b>)  |  Accuracy: <b>{bacc}%</b>")
            sb_stats.setStyleSheet("color: #0f172a; font-size: 12px;")
            sb_rec = QLabel("★ All-Time Personal Best")
            sb_rec.setStyleSheet("color: #15803d; font-size: 10px; font-weight: 600;")
            sb_layout.addWidget(sb_stats)
            sb_layout.addWidget(sb_rec)
            results_row.addWidget(sub_best, 1)

            layout.addLayout(results_row)
            layout.addSpacing(4)

        # 6. Action Buttons Row
        btn_row = QHBoxLayout()
        btn_details = QPushButton("View Pattern")
        btn_details.setObjectName("btnCardDetails")
        btn_details.clicked.connect(lambda: self.details_clicked.emit(self.paper))

        start_btn_txt = "Retake Test  ➔" if self.is_attempted else "Start Test  ➔"
        btn_start = QPushButton(start_btn_txt)
        btn_start.setObjectName("btnCardStart")
        btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start.clicked.connect(lambda: self.start_clicked.emit(self.paper))

        btn_row.addWidget(btn_details)
        btn_row.addStretch()
        btn_row.addWidget(btn_start)
        layout.addLayout(btn_row)

        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#paperCard {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QFrame#paperCard:hover {
                border-color: #3b82f6;
                background-color: #f8fafc;
            }
            QFrame#paperCardAttempted {
                background-color: #ffffff;
                border: 2px solid #16a34a;
                border-radius: 8px;
            }
            QFrame#paperCardAttempted:hover {
                border-color: #15803d;
                background-color: #f0fdf4;
            }
            QLabel#paperCatBadge {
                background-color: #dbeafe;
                color: #1e40af;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
            }
            QLabel#paperYearBadge {
                background-color: #fef3c7;
                color: #92400e;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
            }
            QLabel#badgeAttempted {
                background-color: #dcfce7;
                color: #15803d;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid #86efac;
            }
            QLabel#badgeNotAttempted {
                background-color: #f1f5f9;
                color: #64748b;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid #e2e8f0;
            }
            QLabel#metaChip {
                color: #334155;
                font-size: 11px;
                font-weight: 500;
                background-color: #f1f5f9;
                padding: 2px 6px;
                border-radius: 4px;
            }
            QFrame#attemptSubCard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QFrame#attemptSubCardActive {
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 6px;
            }
            QPushButton#btnCardDetails {
                background-color: #f1f5f9;
                color: #334155;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton#btnCardDetails:hover {
                background-color: #e2e8f0;
            }
            QPushButton#btnCardStart {
                background-color: #16a34a;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #15803d;
                border-radius: 4px;
                padding: 6px 18px;
            }
            QPushButton#btnCardStart:hover {
                background-color: #15803d;
            }
        """)


class PaperSelectionWindow(QWidget):
    paper_selected = pyqtSignal(object)      # Emits ExamPaper
    back_to_exam_selection = pyqtSignal()
    open_dashboard_requested = pyqtSignal()

    def __init__(self, exam_type: str = "GATE", storage_manager: Optional[StorageManager] = None, parent=None):
        super().__init__(parent)
        self.exam_type = exam_type
        self.storage_manager = storage_manager or StorageManager()
        self.all_papers: List[ExamPaper] = []
        self.filtered_papers: List[ExamPaper] = []
        self.attempts_by_paper: Dict[str, List[Dict[str, Any]]] = {}

        self._init_ui()
        self.reload_papers()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Top Navigation & Action Bar (Import button removed)
        top_bar = QHBoxLayout()

        btn_back = QPushButton("← Change Exam")
        btn_back.setObjectName("btnTopBack")
        btn_back.clicked.connect(self.back_to_exam_selection.emit)

        top_bar.addWidget(btn_back)
        top_bar.addStretch()

        btn_dash = QPushButton("📊 Student Dashboard & Stats")
        btn_dash.setObjectName("btnTopDash")
        btn_dash.clicked.connect(self.open_dashboard_requested.emit)

        top_bar.addWidget(btn_dash)
        main_layout.addLayout(top_bar)

        # 2. Layer Title & Header Banner
        banner = QFrame()
        banner.setObjectName("paperHeaderBanner")
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(18, 14, 18, 14)
        b_layout.setSpacing(4)

        self.lbl_title = QLabel(f"<h2>{self.exam_type} Examination - Test Inventory</h2>")
        self.lbl_title.setStyleSheet("color: #1e3a8a; margin: 0;")
        
        lbl_sub = QLabel("Browse official Previous Year Examination Papers (PYQs) and Chapter-wise tests with live attempt analytics.")
        lbl_sub.setStyleSheet("color: #475569; font-size: 13px;")

        b_layout.addWidget(self.lbl_title)
        b_layout.addWidget(lbl_sub)
        main_layout.addWidget(banner)

        # 3. Search & Filter Bar (With Chapter / Subject Filter)
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search test by name, year (e.g. 2024), or topic...")
        self.search_box.setFixedHeight(36)
        self.search_box.textChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.search_box, 3)

        # Category Combobox
        self.cat_filter = QComboBox()
        self.cat_filter.addItems(["All Papers", "Full Length PYQ", "Topic-wise"])
        self.cat_filter.setFixedHeight(36)
        self.cat_filter.currentTextChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.cat_filter, 1)

        # Chapter / Subject Filter Combobox
        self.chapter_filter = QComboBox()
        self.chapter_filter.setFixedHeight(36)
        self.chapter_filter.setMinimumWidth(190)
        self.chapter_filter.setObjectName("chapterFilter")
        self.chapter_filter.currentTextChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.chapter_filter, 2)

        # Refresh button
        btn_refresh = QPushButton("⟳ Refresh")
        btn_refresh.setFixedHeight(36)
        btn_refresh.setObjectName("btnRefresh")
        btn_refresh.clicked.connect(self.reload_papers)
        filter_bar.addWidget(btn_refresh)

        main_layout.addLayout(filter_bar)

        # 4. Scrollable Cards Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("paperScroll")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setSpacing(12)

        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll, 1)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#paperHeaderBanner {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QPushButton#btnTopBack {
                background-color: #ffffff;
                color: #475569;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton#btnTopBack:hover {
                background-color: #f1f5f9;
            }
            QPushButton#btnTopDash {
                background-color: #3b82f6;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton#btnTopDash:hover {
                background-color: #2563eb;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QPushButton#btnRefresh {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 600;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 14px;
            }
            QPushButton#btnRefresh:hover {
                background-color: #e2e8f0;
            }
            QScrollArea#paperScroll {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

    def set_exam_type(self, exam_type: str):
        self.exam_type = exam_type
        self.lbl_title.setText(f"<h2>{self.exam_type} Examination - Test Inventory</h2>")
        self.reload_papers()

    def reload_papers(self):
        papers = self.storage_manager.load_all_papers(self.exam_type)
        all_attempts = self.storage_manager.load_all_attempts(self.exam_type)

        # Build attempt index by paperId
        self.attempts_by_paper = {}
        for att in all_attempts:
            pid = att.get("paperId", "")
            if pid:
                self.attempts_by_paper.setdefault(pid, []).append(att)

        full_length = [p for p in papers if "topic" not in p.category.lower()]
        topic_wise = [p for p in papers if "topic" in p.category.lower()]
        full_length.sort(key=lambda p: (p.year or 0), reverse=True)
        topic_wise.sort(key=lambda p: p.title)
        self.all_papers = full_length + topic_wise

        self._populate_chapter_filter()
        self._apply_filters()

    def _populate_chapter_filter(self):
        current_selection = self.chapter_filter.currentText()
        self.chapter_filter.blockSignals(True)
        self.chapter_filter.clear()

        # Core GATE EC Subjects first
        core_subjects = [
            "All Chapters / Subjects",
            "Digital Circuits",
            "Communications",
            "Signals & Systems",
            "Control Systems",
            "Networks",
            "Electronic Devices",
            "Analog Circuits",
            "Electromagnetics",
            "Engineering Mathematics",
            "General Aptitude"
        ]
        self.chapter_filter.addItems(core_subjects)

        # Extract distinct chapters from topic-wise papers
        chapters = set()
        for p in self.all_papers:
            if "topic" in p.category.lower():
                m = re.search(r'GATE EC - (.+?)(?: \((.+?)\))?$', p.title)
                if m:
                    ch_name = m.group(1).strip()
                    if ch_name:
                        chapters.add(ch_name)

        if chapters:
            self.chapter_filter.addItem("─── Specific Topic Chapters ───")
            for ch in sorted(chapters):
                self.chapter_filter.addItem(ch)

        # Restore previous selection if still valid
        idx = self.chapter_filter.findText(current_selection)
        if idx >= 0:
            self.chapter_filter.setCurrentIndex(idx)
        else:
            self.chapter_filter.setCurrentIndex(0)

        self.chapter_filter.blockSignals(False)

    def _matches_chapter_filter(self, paper: ExamPaper, ch_filter: str) -> bool:
        q = ch_filter.lower().strip()
        p_title = paper.title.lower()
        p_desc = (paper.description or "").lower()

        if q in p_title or q in p_desc:
            return True

        # Normalized subject synonyms
        if "signal" in q and ("signal" in p_title or "signal" in p_desc):
            return True
        if "communicat" in q and ("communicat" in p_title or "communicat" in p_desc):
            return True
        if "network" in q and ("network" in p_title or "two_port" in paper.paper_id or "network" in p_desc):
            return True
        if "digital" in q and ("digital" in p_title or "digital" in p_desc):
            return True
        if "control" in q and ("control" in p_title or "control" in p_desc):
            return True
        if "device" in q and ("device" in p_title or "semiconductor" in p_title or "device" in p_desc):
            return True
        if "analog" in q and ("analog" in p_title or "analog" in p_desc):
            return True
        if "electromagnet" in q and ("electromagnet" in p_title or "electromagnet" in p_desc):
            return True
        if "math" in q and ("math" in p_title or "math" in p_desc or "calculus" in p_title):
            return True
        if "aptitude" in q and ("aptitude" in p_title or "aptitude" in p_desc):
            return True

        return False

    def _apply_filters(self):
        query = self.search_box.text().strip().lower()
        cat = self.cat_filter.currentText()
        ch_filter = self.chapter_filter.currentText()

        self.filtered_papers = []
        for p in self.all_papers:
            # 1. Category match
            if cat not in ("All Papers", "All Categories"):
                if cat == "Full Length PYQ":
                    if "topic" in p.category.lower():
                        continue
                elif cat == "Topic-wise":
                    if "topic" not in p.category.lower():
                        continue
                elif cat.lower() not in p.category.lower():
                    continue

            # 2. Chapter / Subject filter
            if ch_filter and ch_filter not in ("All Chapters / Subjects", "─── Specific Topic Chapters ───"):
                if not self._matches_chapter_filter(p, ch_filter):
                    continue

            # 3. Search query
            if query:
                in_title = query in p.title.lower()
                in_desc = query in (p.description or "").lower()
                in_year = query in str(p.year or "")
                if not (in_title or in_desc or in_year):
                    continue

            self.filtered_papers.append(p)

        self._render_cards()

    def _render_cards(self):
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.filtered_papers:
            empty_box = QFrame()
            empty_box.setStyleSheet("background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 30px;")
            ev_layout = QVBoxLayout(empty_box)
            ev_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl_empty = QLabel("📭 No test papers found matching your criteria.")
            lbl_empty.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl_empty.setStyleSheet("color: #64748b;")
            lbl_sub = QLabel("Try searching with a different keyword or changing the chapter/category filter.")
            lbl_sub.setStyleSheet("color: #94a3b8; font-size: 11px;")

            ev_layout.addWidget(lbl_empty, alignment=Qt.AlignmentFlag.AlignCenter)
            ev_layout.addWidget(lbl_sub, alignment=Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty_box)
            return

        for paper in self.filtered_papers:
            attempts = self.attempts_by_paper.get(paper.paper_id, [])
            last_att = None
            best_att = None
            if attempts:
                last_att = sorted(attempts, key=lambda a: str(a.get("timestamp", "")), reverse=True)[0]
                best_att = sorted(attempts, key=lambda a: (float(a.get("scoreObtained", 0.0)), float(a.get("percentageScore", 0.0))), reverse=True)[0]

            card = PaperCard(paper, last_attempt=last_att, best_attempt=best_att, parent=self.cards_container)
            card.start_clicked.connect(self.paper_selected.emit)
            card.details_clicked.connect(self._show_paper_details)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _show_paper_details(self, paper: ExamPaper):
        sec_details = "<br>".join([
            f"• <b>{sec.section_name}</b>: {len(sec.questions)} Questions (Total {sum(q.positive_marks for q in sec.questions)} marks)"
            for sec in paper.sections
        ])

        q_types = {}
        for q in paper.all_questions:
            q_types[q.type.value] = q_types.get(q.type.value, 0) + 1
        q_type_str = ", ".join([f"{k}: {v}" for k, v in q_types.items()])

        msg = QMessageBox(self)
        msg.setWindowTitle(f"Pattern Details - {paper.title}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(
            f"<h3>{paper.title}</h3>"
            f"<b>Duration:</b> {paper.duration_minutes} Minutes<br>"
            f"<b>Total Marks:</b> {paper.total_marks}<br>"
            f"<b>Total Questions:</b> {paper.total_questions_count}<br>"
            f"<b>Question Distribution:</b> {q_type_str}<br><br>"
            f"<b>Sections:</b><br>{sec_details}<br><br>"
            f"<b>Evaluation:</b> Strict GATE marking criteria with virtual calculator support."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
