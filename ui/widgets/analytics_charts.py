"""
Interactive Visual Analytics and Chart Widgets for Student Dashboard.
Custom lightweight vector-rendered charts using QPainter:
- AccuracyBreakdownBar: Proportional segmented bar for Correct / Incorrect / Unattempted.
- PerformanceTrendChart: Multi-test score trend line chart with grid lines and benchmarks.
- ScoreGaugeCard: Prominent circular / gradient visual score card with performance tier.
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath


class AccuracyBreakdownBar(QWidget):
    """Visual segmented bar showing percentage of Correct, Incorrect, and Unattempted questions."""

    def __init__(self, correct: int = 0, incorrect: int = 0, unattempted: int = 0, parent=None):
        super().__init__(parent)
        self.correct = correct
        self.incorrect = incorrect
        self.unattempted = unattempted
        self.setFixedHeight(32)

    def set_counts(self, correct: int, incorrect: int, unattempted: int):
        self.correct = correct
        self.incorrect = incorrect
        self.unattempted = unattempted
        self.update()

    def paintEvent(self, event):
        total = self.correct + self.incorrect + self.unattempted
        if total <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        radius = 6.0

        p_corr = self.correct / total
        p_inc = self.incorrect / total
        p_un = self.unattempted / total

        w_corr = w * p_corr
        w_inc = w * p_inc
        w_un = w * p_un

        # Clip whole bar to rounded rectangle
        clip_path = QPainterPath()
        clip_path.addRoundedRect(0, 0, w, h, radius, radius)
        painter.setClipPath(clip_path)

        x = 0.0

        # 1. Correct (Emerald Green)
        if w_corr > 0:
            painter.fillRect(QRectF(x, 0, w_corr, h), QColor("#16a34a"))
            x += w_corr

        # 2. Incorrect (Red)
        if w_inc > 0:
            painter.fillRect(QRectF(x, 0, w_inc, h), QColor("#dc2626"))
            x += w_inc

        # 3. Unattempted (Slate Grey)
        if w_un > 0:
            painter.fillRect(QRectF(x, 0, w_un, h), QColor("#cbd5e1"))

        # Text labels on segments if wide enough
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        if w_corr >= 50:
            painter.drawText(QRectF(0, 0, w_corr, h), Qt.AlignmentFlag.AlignCenter, f"{int(p_corr*100)}%")
        if w_inc >= 50:
            painter.drawText(QRectF(w_corr, 0, w_inc, h), Qt.AlignmentFlag.AlignCenter, f"{int(p_inc*100)}%")
        if w_un >= 50:
            painter.setPen(QColor("#475569"))
            painter.drawText(QRectF(w_corr + w_inc, 0, w_un, h), Qt.AlignmentFlag.AlignCenter, f"{int(p_un*100)}%")


class PerformanceTrendChart(QWidget):
    """Vector-painted line & gradient trend chart showing test scores over past attempts."""

    def __init__(self, scores: Optional[List[float]] = None, titles: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.scores = scores or []
        self.titles = titles or []
        self.setMinimumHeight(190)

    def set_data(self, scores: List[float], titles: Optional[List[str]] = None):
        self.scores = scores
        self.titles = titles or [f"T{i+1}" for i in range(len(scores))]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # Margins
        left = 46.0
        right = 24.0
        top = 24.0
        bottom = 34.0

        chart_w = w - left - right
        chart_h = h - top - bottom

        # Background frame
        painter.fillRect(QRectF(0, 0, w, h), QColor("#ffffff"))

        # Grid lines (0, 25, 50, 75, 100%)
        grid_pen = QPen(QColor("#f1f5f9"), 1, Qt.PenStyle.SolidLine)
        label_pen = QPen(QColor("#94a3b8"), 1)
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        levels = [0, 25, 50, 75, 100]
        for lvl in levels:
            y = top + chart_h - (lvl / 100.0) * chart_h
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(left, y), QPointF(left + chart_w, y))
            painter.setPen(label_pen)
            painter.drawText(QRectF(0, y - 8, left - 8, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{lvl}%")

        # Benchmark line at 50% (Qualified threshold)
        y_bench = top + chart_h - 0.50 * chart_h
        bench_pen = QPen(QColor("#f59e0b"), 1, Qt.PenStyle.DashLine)
        painter.setPen(bench_pen)
        painter.drawLine(QPointF(left, y_bench), QPointF(left + chart_w, y_bench))
        painter.setPen(QColor("#d97706"))
        painter.drawText(QRectF(left + 6, y_bench - 14, 150, 14), Qt.AlignmentFlag.AlignLeft, "Qualifying Benchmark (50%)")

        if not self.scores:
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(QRectF(left, top, chart_w, chart_h), Qt.AlignmentFlag.AlignCenter, "No past test data available yet to render trend chart.")
            return

        # Plot data points
        n = len(self.scores)
        points: List[QPointF] = []

        for i, score in enumerate(self.scores):
            x = left + (i / max(1, n - 1)) * chart_w if n > 1 else left + chart_w / 2.0
            clamped_score = max(0.0, min(100.0, score))
            y = top + chart_h - (clamped_score / 100.0) * chart_h
            points.append(QPointF(x, y))

        # 1. Fill gradient under the curve
        if len(points) > 1:
            poly_path = QPainterPath()
            poly_path.moveTo(QPointF(points[0].x(), top + chart_h))
            for pt in points:
                poly_path.lineTo(pt)
            poly_path.lineTo(QPointF(points[-1].x(), top + chart_h))
            poly_path.closeSubpath()

            grad = QLinearGradient(0, top, 0, top + chart_h)
            grad.setColorAt(0, QColor(59, 130, 246, 60))
            grad.setColorAt(1, QColor(59, 130, 246, 5))
            painter.fillPath(poly_path, QBrush(grad))

        # 2. Draw line
        line_pen = QPen(QColor("#2563eb"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # 3. Draw dots and score values
        for i, pt in enumerate(points):
            # Outer white ring
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.setBrush(QBrush(QColor("#1e40af")))
            painter.drawEllipse(pt, 5, 5)

            # Score text above point
            painter.setPen(QColor("#1e3a8a"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            val_txt = f"{self.scores[i]:.1f}%"
            painter.drawText(QRectF(pt.x() - 25, pt.y() - 20, 50, 16), Qt.AlignmentFlag.AlignCenter, val_txt)

            # X-axis label below
            if i < len(self.titles):
                painter.setPen(QColor("#64748b"))
                painter.setFont(QFont("Segoe UI", 8))
                lbl_title = self.titles[i]
                painter.drawText(QRectF(pt.x() - 40, top + chart_h + 6, 80, 18), Qt.AlignmentFlag.AlignCenter, lbl_title[:10])


class ScoreCardBanner(QFrame):
    """High-visibility scorecard banner with score badge and performance tier."""

    def __init__(self, score: float, total: float, percentage: float, accuracy: float, parent=None):
        super().__init__(parent)
        self.setObjectName("scoreCardBanner")
        self._init_ui(score, total, percentage, accuracy)

    def _init_ui(self, score: float, total: float, percentage: float, accuracy: float):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Determine Tier
        if percentage >= 65.0:
            tier_title = "🏆 TOP PERCENTILE (EXCELLENT)"
            tier_color = "#16a34a"
            bg_color = "#f0fdf4"
            border_color = "#86efac"
            tier_desc = "Outstanding mastery. Consistently clearing top IIT / PSU cutoff criteria."
        elif percentage >= 45.0:
            tier_title = "⭐ QUALIFIED (GOOD STANDING)"
            tier_color = "#2563eb"
            bg_color = "#eff6ff"
            border_color = "#93c5fd"
            tier_desc = "Clear GATE qualification zone with solid accuracy. Target higher speed for rank boost."
        elif percentage >= 25.0:
            tier_title = "📈 MODERATE (PRACTICE REQUIRED)"
            tier_color = "#d97706"
            bg_color = "#fffbeb"
            border_color = "#fde68a"
            tier_desc = "On track. Focus on negative marks reduction and chapter-wise topic tests."
        else:
            tier_title = "⚠️ FOUNDATION BUILDING"
            tier_color = "#dc2626"
            bg_color = "#fef2f2"
            border_color = "#fca5a5"
            tier_desc = "Identify weak topics through the question review and attempt topic-wise tests."

        self.setStyleSheet(f"""
            QFrame#scoreCardBanner {{
                background-color: {bg_color};
                border: 1.5px solid {border_color};
                border-radius: 10px;
            }}
        """)

        # Left: Big circular Score Badge
        score_box = QFrame()
        score_box.setFixedSize(110, 85)
        score_box.setStyleSheet(f"""
            background-color: #ffffff;
            border: 2px solid {tier_color};
            border-radius: 8px;
        """)
        sb_layout = QVBoxLayout(score_box)
        sb_layout.setContentsMargins(4, 6, 4, 6)
        sb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_s = QLabel(f"{score}")
        lbl_s.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl_s.setStyleSheet(f"color: {tier_color}; margin: 0;")
        
        lbl_tot = QLabel(f"/ {total} Marks")
        lbl_tot.setStyleSheet("color: #64748b; font-size: 11px;")

        sb_layout.addWidget(lbl_s, alignment=Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(lbl_tot, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(score_box)

        # Center: Performance Tier Details
        mid_v = QVBoxLayout()
        mid_v.setSpacing(3)
        
        lbl_tier = QLabel(tier_title)
        lbl_tier.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_tier.setStyleSheet(f"color: {tier_color};")
        
        lbl_pct = QLabel(f"Percentage Score: <b>{percentage:.1f}%</b>  |  Overall Accuracy: <b>{accuracy:.1f}%</b>")
        lbl_pct.setStyleSheet("color: #334155; font-size: 12px;")

        lbl_advice = QLabel(tier_desc)
        lbl_advice.setStyleSheet("color: #475569; font-size: 11px;")

        mid_v.addWidget(lbl_tier)
        mid_v.addWidget(lbl_pct)
        mid_v.addWidget(lbl_advice)
        layout.addLayout(mid_v)
        layout.addStretch()
