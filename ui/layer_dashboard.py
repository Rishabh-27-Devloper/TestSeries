"""
Student Performance Dashboard and Analytics.
Highly interactive visual dashboard featuring:
- Live ScoreCard Banner with performance tier ratings
- Segmented Accuracy Breakdown Bar
- Interactive Question-by-Question Review with expandable whole-question diagram slices
- Native Vector-painted Performance Trend Chart
- Historical test attempts with 1-click 'View Complete Analysis' loading
- Permanent User Profile management (Name, Roll Number, Phone, Target Year)
"""

import os
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QTabWidget, QScrollArea, QFrame, QComboBox, 
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from core.models import ExamResult, QuestionType, QuestionStatus
from core.storage import StorageManager
from ui.widgets.analytics_charts import (
    AccuracyBreakdownBar, PerformanceTrendChart, ScoreCardBanner
)
from ui.widgets.profile_dialog import UserProfileDialog


class StatCard(QFrame):
    def __init__(self, title: str, value: str, sub: str = "", color: str = "#1e3a8a", icon: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        top_h = QHBoxLayout()
        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        top_h.addWidget(t_lbl)
        top_h.addStretch()
        if icon:
            ic_lbl = QLabel(icon)
            ic_lbl.setStyleSheet("font-size: 14px;")
            top_h.addWidget(ic_lbl)
        layout.addLayout(top_h)
        
        v_lbl = QLabel(value)
        v_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        v_lbl.setStyleSheet(f"color: {color};")
        layout.addWidget(v_lbl)

        if sub:
            s_lbl = QLabel(sub)
            s_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            layout.addWidget(s_lbl)

        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #94a3b8;
                background-color: #f8fafc;
            }
        """)


class StudentDashboardWindow(QWidget):
    back_requested = pyqtSignal()
    candidate_profile_updated = pyqtSignal(dict)

    def __init__(
        self,
        storage_manager: Optional[StorageManager] = None,
        latest_result: Optional[ExamResult] = None,
        student_name: str = "Candidate",
        roll_number: str = "GATE25-EC001",
        phone_number: str = "",
        parent=None
    ):
        super().__init__(parent)
        self.storage_manager = storage_manager or StorageManager()
        self.latest_result = latest_result
        self.student_name = student_name
        self.roll_number = roll_number
        self.phone_number = phone_number

        self._init_ui()

    def set_candidate_profile(self, name: str, roll: str, phone: str = ""):
        self.student_name = name
        self.roll_number = roll
        self.phone_number = phone
        phone_part = f" | 📱 {phone}" if phone else ""
        self.lbl_profile_badge.setText(f"👤 <b>{self.student_name}</b> ({self.roll_number}){phone_part}")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 18, 24, 18)
        main_layout.setSpacing(12)

        # 1. Header Bar with Profile Controls
        top_bar = QHBoxLayout()
        btn_back = QPushButton("← Return to Examination Portal")
        btn_back.setObjectName("btnDashBack")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.back_requested.emit)

        title = QLabel("<h2>GATE Student Performance Dashboard</h2>")
        title.setStyleSheet("color: #1e3a8a; margin: 0;")

        top_bar.addWidget(btn_back)
        top_bar.addSpacing(12)
        top_bar.addWidget(title)
        top_bar.addStretch()

        # Candidate Info & Edit Button
        phone_part = f" | 📱 {self.phone_number}" if self.phone_number else ""
        self.lbl_profile_badge = QLabel(f"👤 <b>{self.student_name}</b> ({self.roll_number}){phone_part}")
        self.lbl_profile_badge.setStyleSheet("background-color: #e2e8f0; padding: 6px 12px; border-radius: 4px; color: #1e293b; font-size: 11px;")
        top_bar.addWidget(self.lbl_profile_badge)

        btn_edit = QPushButton("✎ Edit Profile")
        btn_edit.setObjectName("btnEditProfileDash")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(self._open_profile_dialog)
        top_bar.addWidget(btn_edit)

        main_layout.addLayout(top_bar)

        # 2. Main Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("dashTabs")

        self.tab_analytics = QWidget()
        self.tab_review = QWidget()
        self.tab_trends = QWidget()

        self._build_analytics_tab()
        self._build_review_tab()
        self._build_trends_tab()

        self.tabs.addTab(self.tab_analytics, "🎯 Latest Test Analytics & Scorecard")
        self.tabs.addTab(self.tab_review, "📝 Question-by-Question Solution Review")
        self.tabs.addTab(self.tab_trends, "📈 Progress Trends & Past Attempts")

        main_layout.addWidget(self.tabs, 1)

        self._apply_styles()

    def _open_profile_dialog(self):
        dlg = UserProfileDialog(self.storage_manager, self)
        if dlg.exec():
            prof = self.storage_manager.load_user_profile()
            self.set_candidate_profile(
                prof.get("name", "Candidate"),
                prof.get("roll_number", "GATE25-EC001"),
                prof.get("phone_number", "")
            )
            self.candidate_profile_updated.emit(prof)

    def set_result(self, result: ExamResult):
        self.latest_result = result
        self._build_analytics_tab()
        self._build_review_tab()
        self._build_trends_tab()
        self.tabs.setCurrentIndex(0)

    # =========================================================================
    # TAB 1: Analytics & Scorecard
    # =========================================================================
    def _build_analytics_tab(self):
        outer_layout = self.tab_analytics.layout()
        if outer_layout is None:
            outer_layout = QVBoxLayout(self.tab_analytics)
            outer_layout.setContentsMargins(0, 0, 0, 0)
            outer_layout.setSpacing(0)
        else:
            while outer_layout.count():
                item = outer_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("analyticsScroll")
        scroll.setStyleSheet("QScrollArea#analyticsScroll { background-color: #f8fafc; border: none; }")

        container = QWidget()
        container.setObjectName("analyticsContainer")
        container.setStyleSheet("QWidget#analyticsContainer { background-color: transparent; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        if not self.latest_result:
            empty = QLabel("📭 No test has been completed in this session yet.<br>Select any exam from the <b>Paper Inventory</b> or click on past attempts in the <b>Progress Trends</b> tab to inspect your detailed scorecard.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #64748b; font-size: 13px; padding: 60px;")
            layout.addWidget(empty)
            scroll.setWidget(container)
            outer_layout.addWidget(scroll, 1)
            return

        res = self.latest_result

        # Title Card
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px;")
        tf_layout = QHBoxLayout(title_frame)
        
        tl = QLabel(f"<h3>{res.paper_title}</h3>")
        tl.setStyleSheet("color: #1e3a8a; margin: 0;")
        
        mins = res.duration_taken_seconds // 60
        secs = res.duration_taken_seconds % 60
        meta = QLabel(f"Submitted: <b>{res.timestamp}</b>  |  Time Taken: <b>{mins}m {secs}s</b>  |  Total Questions: <b>{res.total_questions}</b>")
        meta.setStyleSheet("color: #475569; font-size: 12px;")

        tf_layout.addWidget(tl)
        tf_layout.addStretch()
        tf_layout.addWidget(meta)
        layout.addWidget(title_frame)

        # 1. Performance Tier Scorecard Banner
        banner = ScoreCardBanner(
            score=res.score_obtained,
            total=res.total_marks,
            percentage=res.percentage_score,
            accuracy=res.accuracy_percentage
        )
        layout.addWidget(banner)

        # 2. Accuracy Breakdown Segmented Bar
        acc_frame = QFrame()
        acc_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px;")
        af_layout = QVBoxLayout(acc_frame)
        af_layout.setSpacing(8)

        bar_head = QHBoxLayout()
        lbl_ah = QLabel("<b>Question Attempt & Accuracy Distribution:</b>")
        lbl_ah.setStyleSheet("color: #1e293b; font-size: 12px;")
        bar_head.addWidget(lbl_ah)
        bar_head.addStretch()

        leg_c = QLabel(f"● Correct: {res.correct_count}")
        leg_c.setStyleSheet("color: #16a34a; font-weight: bold; font-size: 11px;")
        leg_i = QLabel(f"● Incorrect: {res.incorrect_count}")
        leg_i.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 11px;")
        leg_u = QLabel(f"● Unattempted: {res.unattempted_count}")
        leg_u.setStyleSheet("color: #64748b; font-weight: bold; font-size: 11px;")
        bar_head.addWidget(leg_c)
        bar_head.addWidget(leg_i)
        bar_head.addWidget(leg_u)
        af_layout.addLayout(bar_head)

        acc_bar = AccuracyBreakdownBar(
            correct=res.correct_count,
            incorrect=res.incorrect_count,
            unattempted=res.unattempted_count
        )
        af_layout.addWidget(acc_bar)
        layout.addWidget(acc_frame)

        # 3. High-Impact KPI Stat Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)

        avg_speed = round(res.duration_taken_seconds / max(1, res.attempted_count), 1)
        stats_row.addWidget(StatCard("Net Score", f"{res.score_obtained}", f"of {res.total_marks} Marks", color="#15803d", icon="🎯"))
        stats_row.addWidget(StatCard("Accuracy", f"{res.accuracy_percentage}%", f"{res.correct_count} of {res.attempted_count} attempted", color="#0284c7", icon="📊"))
        stats_row.addWidget(StatCard("Gross Positive", f"+{res.positive_marks}", f"{res.correct_count} correct answers", color="#16a34a", icon="➕"))
        stats_row.addWidget(StatCard("Negative Marks", f"-{res.negative_marks}", f"{res.incorrect_count} incorrect penalties", color="#dc2626", icon="➖"))
        stats_row.addWidget(StatCard("Avg Speed", f"{avg_speed}s", "per attempted question", color="#7c3aed", icon="⏱"))

        layout.addLayout(stats_row)

        # 4. Section-wise Performance Breakdown Table
        sec_label = QLabel("<b>Section-wise Performance Breakdown:</b>")
        sec_label.setStyleSheet("color: #1e293b; font-size: 12px; margin-top: 4px;")
        layout.addWidget(sec_label)

        sec_table = QTableWidget()
        sec_table.setColumnCount(6)
        sec_table.setHorizontalHeaderLabels(["Section Name", "Total Questions", "Attempted", "Correct", "Incorrect", "Marks Obtained"])
        sec_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        sec_table.verticalHeader().setVisible(False)
        sec_table.setMinimumHeight(140)
        sec_table.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; font-size: 12px; border-radius: 6px;")

        sec_table.setRowCount(len(res.section_scores))
        for r, (sec_name, stats) in enumerate(res.section_scores.items()):
            sec_table.setItem(r, 0, QTableWidgetItem(sec_name))
            sec_table.setItem(r, 1, QTableWidgetItem(str(stats["total_questions"])))
            sec_table.setItem(r, 2, QTableWidgetItem(str(stats["attempted"])))
            sec_table.setItem(r, 3, QTableWidgetItem(str(stats["correct"])))
            sec_table.setItem(r, 4, QTableWidgetItem(str(stats["incorrect"])))
            sec_table.setItem(r, 5, QTableWidgetItem(f"{round(stats['score'], 2)} / {stats['max_marks']}"))

        layout.addWidget(sec_table)
        layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll, 1)

    # =========================================================================
    # TAB 2: Interactive Question Review with Whole-Question Images
    # =========================================================================
    def _build_review_tab(self):
        layout = self.tab_review.layout()
        if layout is None:
            layout = QVBoxLayout(self.tab_review)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(10)
        else:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        if not self.latest_result:
            empty = QLabel("No test questions available for review yet. Submit an exam to inspect question-by-question solutions.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #64748b; font-size: 13px; padding: 60px;")
            layout.addWidget(empty)
            return

        # Control Bar: Filters
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(10)

        ctrl_bar.addWidget(QLabel("<b>Filter Questions:</b>"))
        self.review_filter = QComboBox()
        self.review_filter.addItems(["All Questions", "Correct Only", "Incorrect Only", "Unattempted Only"])
        self.review_filter.currentTextChanged.connect(self._render_question_reviews)
        ctrl_bar.addWidget(self.review_filter)

        ctrl_bar.addSpacing(16)
        ctrl_bar.addWidget(QLabel("<b>Section:</b>"))
        self.sec_filter = QComboBox()
        self.sec_filter.addItem("All Sections")
        for s in self.latest_result.section_scores.keys():
            self.sec_filter.addItem(s)
        self.sec_filter.currentTextChanged.connect(self._render_question_reviews)
        ctrl_bar.addWidget(self.sec_filter)

        ctrl_bar.addStretch()

        btn_expand_all = QPushButton("👁 Toggle All Diagrams")
        btn_expand_all.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #1e3a8a;
                font-weight: 600;
                font-size: 11px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        btn_expand_all.clicked.connect(self._toggle_all_diagrams)
        ctrl_bar.addWidget(btn_expand_all)

        layout.addLayout(ctrl_bar)

        # Scrollable Question Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: 1px solid #e2e8f0; border-radius: 6px;")

        self.review_container = QWidget()
        self.review_layout = QVBoxLayout(self.review_container)
        self.review_layout.setContentsMargins(8, 8, 8, 8)
        self.review_layout.setSpacing(12)

        self._all_diagram_labels: List[QLabel] = []
        self._all_diagrams_visible = False

        self._render_question_reviews()

        scroll.setWidget(self.review_container)
        layout.addWidget(scroll, 1)

    def _toggle_all_diagrams(self):
        self._all_diagrams_visible = not self._all_diagrams_visible
        for lbl in self._all_diagram_labels:
            lbl.setVisible(self._all_diagrams_visible)

    def _render_question_reviews(self):
        if not self.latest_result:
            return

        while self.review_layout.count():
            item = self.review_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._all_diagram_labels = []
        filter_mode = self.review_filter.currentText()
        sec_mode = self.sec_filter.currentText()

        shown_count = 0
        for ev in self.latest_result.evaluations:
            if filter_mode == "Correct Only" and not ev.is_correct:
                continue
            if filter_mode == "Incorrect Only" and (not ev.is_attempted or ev.is_correct):
                continue
            if filter_mode == "Unattempted Only" and ev.is_attempted:
                continue
            if sec_mode != "All Sections" and ev.section_name != sec_mode:
                continue

            shown_count += 1
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(8)

            # Top Badge Row
            top_h = QHBoxLayout()
            title_text = ev.question_text or f"Question {ev.question_number}"
            q_num_lbl = QLabel(f"<b>Q{ev.question_number}.</b> {title_text}  <span style='color:#64748b;'>[{ev.type.value} | {ev.section_name}]</span>")
            q_num_lbl.setStyleSheet("color: #1e3a8a; font-size: 13px;")
            top_h.addWidget(q_num_lbl)
            top_h.addStretch()

            if ev.is_correct:
                status_chip = QLabel(f"✓ CORRECT  +{ev.marks_awarded}")
                status_chip.setStyleSheet("background-color: #dcfce7; color: #15803d; font-weight: bold; padding: 3px 10px; border-radius: 4px; font-size: 11px;")
            elif ev.is_attempted:
                status_chip = QLabel(f"✕ INCORRECT  {ev.marks_awarded}")
                status_chip.setStyleSheet("background-color: #fee2e2; color: #b91c1c; font-weight: bold; padding: 3px 10px; border-radius: 4px; font-size: 11px;")
            else:
                status_chip = QLabel("○ NOT ATTEMPTED  0.0")
                status_chip.setStyleSheet("background-color: #f1f5f9; color: #64748b; font-weight: bold; padding: 3px 10px; border-radius: 4px; font-size: 11px;")
            top_h.addWidget(status_chip)
            c_layout.addLayout(top_h)

            # Embedded Question Image Slice if exists
            img_path = ev.image_url
            if img_path and os.path.exists(img_path):
                img_toggle_btn = QPushButton("👁 Show / Hide Question Diagram & Options")
                img_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                img_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #eff6ff;
                        color: #2563eb;
                        font-weight: 600;
                        font-size: 11px;
                        border: 1px solid #bfdbfe;
                        border-radius: 4px;
                        padding: 4px 10px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #dbeafe;
                    }
                """)
                img_lbl = QLabel()
                pix = QPixmap(img_path)
                if not pix.isNull():
                    # Scale to max width 850
                    max_w = 850
                    if pix.width() > max_w:
                        pix = pix.scaledToWidth(max_w, Qt.TransformationMode.SmoothTransformation)
                    img_lbl.setPixmap(pix)
                    img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    img_lbl.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; background-color: #ffffff;")
                    img_lbl.setVisible(self._all_diagrams_visible)

                    img_toggle_btn.clicked.connect(lambda _, l=img_lbl: l.setVisible(not l.isVisible()))
                    self._all_diagram_labels.append(img_lbl)

                    c_layout.addWidget(img_toggle_btn)
                    c_layout.addWidget(img_lbl)

            # Response Comparison Row
            ans_frame = QFrame()
            ans_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px;")
            af_layout = QHBoxLayout(ans_frame)
            af_layout.setContentsMargins(8, 4, 8, 4)

            if ev.candidate_answer is not None and ev.is_attempted:
                if isinstance(ev.candidate_answer, list):
                    cand_ans_str = ", ".join(f"Option ({x})" for x in ev.candidate_answer)
                elif ev.type == QuestionType.MCQ:
                    cand_ans_str = f"Option ({ev.candidate_answer})"
                else:
                    cand_ans_str = str(ev.candidate_answer)
            else:
                cand_ans_str = "<i>None (Unattempted)</i>"

            if isinstance(ev.correct_answer, list):
                corr_ans_str = ", ".join(f"Option ({x})" for x in ev.correct_answer)
            elif ev.type == QuestionType.MCQ:
                corr_ans_str = f"Option ({ev.correct_answer})"
            else:
                corr_ans_str = str(ev.correct_answer)

            lbl_c = QLabel(f"Your Response: <b>{cand_ans_str}</b>")
            lbl_c.setStyleSheet("color: #334155; font-size: 12px;")
            lbl_ok = QLabel(f"Official Answer: <b style='color:#16a34a;'>{corr_ans_str}</b>")
            lbl_ok.setStyleSheet("font-size: 12px;")
            lbl_t = QLabel(f"⏱ Time: {ev.time_spent}s")
            lbl_t.setStyleSheet("color: #64748b; font-size: 11px;")

            af_layout.addWidget(lbl_c)
            af_layout.addSpacing(24)
            af_layout.addWidget(lbl_ok)
            af_layout.addStretch()
            af_layout.addWidget(lbl_t)
            c_layout.addWidget(ans_frame)

            # Solution / Explanation if present
            if ev.explanation:
                exp_box = QFrame()
                exp_box.setStyleSheet("background-color: #f0fdf4; border-left: 3px solid #16a34a; padding: 6px 10px; border-radius: 4px;")
                eb_layout = QVBoxLayout(exp_box)
                exp_title = QLabel("<b>Official Solution / Notes:</b>")
                exp_title.setStyleSheet("color: #166534; font-size: 11px;")
                exp_body = QLabel(ev.explanation.replace("\n", "<br>"))
                exp_body.setWordWrap(True)
                exp_body.setStyleSheet("color: #14532d; font-size: 12px;")
                eb_layout.addWidget(exp_title)
                eb_layout.addWidget(exp_body)
                c_layout.addWidget(exp_box)

            self.review_layout.addWidget(card)

        if shown_count == 0:
            lbl_none = QLabel("No questions match your selected filter criteria.")
            lbl_none.setStyleSheet("color: #64748b; font-size: 12px; padding: 20px;")
            self.review_layout.addWidget(lbl_none)

        self.review_layout.addStretch()

    # =========================================================================
    # TAB 3: Trends & Historical Attempts
    # =========================================================================
    def _build_trends_tab(self):
        outer_layout = self.tab_trends.layout()
        if outer_layout is None:
            outer_layout = QVBoxLayout(self.tab_trends)
            outer_layout.setContentsMargins(0, 0, 0, 0)
            outer_layout.setSpacing(0)
        else:
            while outer_layout.count():
                item = outer_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("trendsScroll")
        scroll.setStyleSheet("QScrollArea#trendsScroll { background-color: #f8fafc; border: none; }")

        container = QWidget()
        container.setObjectName("trendsContainer")
        container.setStyleSheet("QWidget#trendsContainer { background-color: transparent; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        attempts = self.storage_manager.load_all_attempts()

        # Cumulative Metrics Row
        cum_frame = QFrame()
        cum_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px;")
        cf_layout = QHBoxLayout(cum_frame)
        cf_layout.setSpacing(16)

        total_tests = len(attempts)
        avg_score = round(sum(a.get("percentageScore", 0) for a in attempts) / max(1, total_tests), 1) if attempts else 0.0
        best_score = round(max((a.get("percentageScore", 0) for a in attempts), default=0.0), 1)
        avg_acc = round(sum(a.get("accuracyPercentage", 0) for a in attempts) / max(1, total_tests), 1) if attempts else 0.0

        cf_layout.addWidget(StatCard("Total Tests Taken", str(total_tests), "attempts saved", color="#1e3a8a", icon="📚"))
        cf_layout.addWidget(StatCard("Average Score", f"{avg_score}%", "across all papers", color="#0284c7", icon="📈"))
        cf_layout.addWidget(StatCard("Peak Score", f"{best_score}%", "all-time record", color="#16a34a", icon="🏆"))
        cf_layout.addWidget(StatCard("Average Accuracy", f"{avg_acc}%", "correct / attempted", color="#7c3aed", icon="🎯"))
        layout.addWidget(cum_frame)

        # Performance Trend Vector Chart
        chart_frame = QFrame()
        chart_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
        ch_layout = QVBoxLayout(chart_frame)
        ch_layout.setSpacing(6)

        c_title = QLabel("<b>Score Progression Trend (Last 10 Tests):</b>")
        c_title.setStyleSheet("color: #1e3a8a; font-size: 12px;")
        ch_layout.addWidget(c_title)

        # Take last 10 attempts in chronological order
        recent_10 = list(reversed(attempts[:10]))
        scores_10 = [float(a.get("percentageScore", 0.0)) for a in recent_10]
        titles_10 = [str(a.get("timestamp", ""))[:10] for a in recent_10]

        trend_chart = PerformanceTrendChart(scores=scores_10, titles=titles_10)
        ch_layout.addWidget(trend_chart)
        layout.addWidget(chart_frame)

        # All Attempts Table with 'View Complete Analysis' button
        t_head = QLabel("<b>All Past Test Attempts (Click 'Load Analysis' to inspect full scorecard):</b>")
        t_head.setStyleSheet("color: #1e293b; font-size: 13px; margin-top: 6px;")
        layout.addWidget(t_head)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(["Date & Time", "Paper Title", "Score Obtained", "Total Marks", "Accuracy", "Time Taken", "Percentile", "Action"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(attempts))
        table.setAlternatingRowColors(True)

        # Generous minimum height so all attempt rows are clearly visible and comfortable
        table_height = max(260, len(attempts) * 44 + 50)
        table.setMinimumHeight(table_height)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                font-size: 12px;
                border-radius: 6px;
                gridline-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #1e293b;
                font-weight: bold;
                padding: 7px;
                border: 1px solid #e2e8f0;
            }
        """)

        for r, att in enumerate(attempts):
            table.setItem(r, 0, QTableWidgetItem(att.get("timestamp", "")))
            table.setItem(r, 1, QTableWidgetItem(att.get("paperTitle", "")))
            table.setItem(r, 2, QTableWidgetItem(str(att.get("scoreObtained", 0.0))))
            table.setItem(r, 3, QTableWidgetItem(str(att.get("totalMarks", 100.0))))
            table.setItem(r, 4, QTableWidgetItem(f"{att.get('accuracyPercentage', 0.0)}%"))
            
            secs = att.get("durationTakenSeconds", 0)
            table.setItem(r, 5, QTableWidgetItem(f"{secs // 60}m {secs % 60}s"))
            table.setItem(r, 6, QTableWidgetItem(f"{att.get('percentageScore', 0.0)}%"))

            # View Report Button
            btn_view = QPushButton("🔍 Load Analysis")
            btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_view.setStyleSheet("""
                QPushButton {
                    background-color: #1a56a5;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 11px;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #1e40af;
                }
            """)
            fp = att.get("_filePath")
            btn_view.clicked.connect(lambda _, path=fp: self._load_past_attempt(path))
            table.setCellWidget(r, 7, btn_view)

        layout.addWidget(table)
        layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll, 1)

    def _load_past_attempt(self, file_path: Optional[str]):
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Attempt Not Found", "Unable to locate the attempt file on disk.")
            return

        res = self.storage_manager.load_attempt_result(file_path)
        if res:
            self.set_result(res)
        else:
            QMessageBox.warning(self, "Load Error", "Failed to reconstruct attempt data.")

    def _apply_styles(self):
        self.setStyleSheet("""
            QPushButton#btnDashBack {
                background-color: #ffffff;
                color: #334155;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton#btnDashBack:hover {
                background-color: #f1f5f9;
            }
            QPushButton#btnEditProfileDash {
                background-color: #ffffff;
                color: #1e3a8a;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton#btnEditProfileDash:hover {
                background-color: #f1f5f9;
            }
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                background-color: #f8fafc;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e2e8f0;
                color: #334155;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e3a8a;
                color: #ffffff;
            }
        """)
