"""
Question Display Widget for CBT Exam.
Renders question text, marks info, question diagrams (with zoom dialog),
and handles response input with full option diagram support for:
- MCQ (Radio button single selection with optional diagrams)
- MSQ (Checkbox multiple selection with optional diagrams)
- NAT (Numerical input + Official On-Screen Numeric Keypad)
"""

import os
import base64
from typing import List, Optional, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QRadioButton, QCheckBox, QLineEdit, 
    QPushButton, QButtonGroup, QScrollArea, QFrame, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QByteArray
from PyQt6.QtGui import QFont, QPixmap, QCursor

from core.models import Question, QuestionType, Option


class ImageZoomDialog(QDialog):
    """High-resolution zoom dialog for inspecting circuit diagrams and graphs."""
    def __init__(self, pixmap: QPixmap, title: str = "Diagram Viewer", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.original_pixmap = pixmap
        self.scale_factor = 1.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Controls bar
        ctrl_bar = QHBoxLayout()
        btn_zoom_in = QPushButton("➕ Zoom In")
        btn_zoom_in.clicked.connect(self._zoom_in)
        btn_zoom_out = QPushButton("➖ Zoom Out")
        btn_zoom_out.clicked.connect(self._zoom_out)
        btn_reset = QPushButton("↺ Fit to Screen")
        btn_reset.clicked.connect(self._reset_zoom)
        btn_close = QPushButton("✕ Close")
        btn_close.clicked.connect(self.accept)

        ctrl_bar.addWidget(btn_zoom_in)
        ctrl_bar.addWidget(btn_zoom_out)
        ctrl_bar.addWidget(btn_reset)
        ctrl_bar.addStretch()
        ctrl_bar.addWidget(btn_close)
        layout.addLayout(ctrl_bar)

        # Scrollable image
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1;")

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.img_label)
        layout.addWidget(self.scroll, 1)

        self._update_display()
        self.setStyleSheet("""
            QDialog { background-color: #f8fafc; }
            QPushButton {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #f1f5f9; }
        """)

    def _update_display(self):
        w = int(self.original_pixmap.width() * self.scale_factor)
        h = int(self.original_pixmap.height() * self.scale_factor)
        scaled = self.original_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_label.setPixmap(scaled)

    def _zoom_in(self):
        self.scale_factor *= 1.25
        self._update_display()

    def _zoom_out(self):
        if self.scale_factor > 0.3:
            self.scale_factor /= 1.25
            self._update_display()

    def _reset_zoom(self):
        self.scale_factor = 1.0
        self._update_display()


def load_pixmap_from_source(source: Optional[str]) -> Optional[QPixmap]:
    """Helper to load a QPixmap from a file path or Base64 data string."""
    if not source:
        return None
        
    source_str = str(source).strip()
    
    # 1. Base64 data URI (e.g. data:image/png;base64,iVBOR...)
    if source_str.startswith("data:image"):
        try:
            header, b64data = source_str.split(",", 1)
            raw_bytes = base64.b64decode(b64data)
            pm = QPixmap()
            if pm.loadFromData(raw_bytes):
                return pm
        except Exception as e:
            print(f"Error loading base64 image: {e}")
            return None

    # 2. Local File Path
    if os.path.exists(source_str):
        pm = QPixmap(source_str)
        if not pm.isNull():
            return pm

    return None


class QuestionDisplayWidget(QWidget):
    response_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_question: Optional[Question] = None
        self._mcq_group = QButtonGroup(self)
        self._msq_checkboxes: List[QCheckBox] = []
        self._nat_input: Optional[QLineEdit] = None
        self._active_q_pixmap: Optional[QPixmap] = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 1. Question Meta Bar (Q No, Type, Marks)
        meta_bar = QFrame()
        meta_bar.setObjectName("qMetaBar")
        mb_layout = QHBoxLayout(meta_bar)
        mb_layout.setContentsMargins(12, 6, 12, 6)

        self.lbl_q_num = QLabel("Question No. 1")
        self.lbl_q_num.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_q_num.setStyleSheet("color: #1e3a8a;")

        self.lbl_q_type = QLabel("Question Type: MCQ")
        self.lbl_q_type.setStyleSheet("color: #4b5563; font-weight: 600;")

        self.lbl_marks = QLabel("Marks: +1.0  |  Negative: -0.33")
        self.lbl_marks.setStyleSheet("color: #15803d; font-weight: bold;")

        mb_layout.addWidget(self.lbl_q_num)
        mb_layout.addWidget(self.lbl_q_type)

        self.lbl_oos = QLabel("⚠️ Out of Syllabus")
        self.lbl_oos.setStyleSheet("""
            background-color: #fef3c7;
            color: #92400e;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #fde68a;
        """)
        self.lbl_oos.setVisible(False)
        mb_layout.addWidget(self.lbl_oos)

        mb_layout.addStretch()
        mb_layout.addWidget(self.lbl_marks)
        main_layout.addWidget(meta_bar)

        # 2. Scrollable Question Content Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("qContentScroll")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(18, 14, 18, 18)
        self.content_layout.setSpacing(12)

        # Question Text Label
        self.lbl_q_text = QLabel()
        self.lbl_q_text.setWordWrap(True)
        self.lbl_q_text.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_q_text.setFont(QFont("Segoe UI", 11))
        self.lbl_q_text.setStyleSheet("color: #0f172a; line-height: 1.6;")
        self.content_layout.addWidget(self.lbl_q_text)

        # Question Diagram Container (Clickable with zoom button)
        self.diagram_box = QFrame()
        self.diagram_box.setObjectName("diagramBox")
        diag_layout = QVBoxLayout(self.diagram_box)
        diag_layout.setContentsMargins(10, 8, 10, 8)
        diag_layout.setSpacing(6)

        self.lbl_q_image = QLabel()
        self.lbl_q_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_q_image.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lbl_q_image.mousePressEvent = lambda e: self._open_diagram_zoom()
        diag_layout.addWidget(self.lbl_q_image)

        # Zoom helper note
        lbl_zoom_hint = QLabel("🔍 Click diagram to open high-resolution zoom viewer")
        lbl_zoom_hint.setStyleSheet("color: #64748b; font-size: 11px; text-align: center;")
        lbl_zoom_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diag_layout.addWidget(lbl_zoom_hint)

        self.diagram_box.hide()
        self.content_layout.addWidget(self.diagram_box)

        # Options Container
        self.options_container = QWidget()
        self.options_layout = QVBoxLayout(self.options_container)
        self.options_layout.setContentsMargins(0, 8, 0, 8)
        self.options_layout.setSpacing(10)
        self.content_layout.addWidget(self.options_container)

        self.content_layout.addStretch()
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll, 1)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#qMetaBar {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            QScrollArea#qContentScroll {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            QFrame#diagramBox {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px;
            }
            QRadioButton, QCheckBox {
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                color: #0f172a;
                padding: 8px 12px;
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QRadioButton:hover, QCheckBox:hover {
                background-color: #eff6ff;
                border-color: #93c5fd;
            }
            QRadioButton:checked, QCheckBox:checked {
                background-color: #e0f2fe;
                border-color: #0284c7;
                font-weight: 600;
            }
        """)

    def load_question(self, question: Question):
        self.current_question = question
        
        # 1. Update Meta info
        self.lbl_q_num.setText(f"Question No. {question.question_number}")
        
        type_str = {
            QuestionType.MCQ: "MCQ (Multiple Choice - Single Correct)",
            QuestionType.MSQ: "MSQ (Multiple Select - One or More Correct)",
            QuestionType.NAT: "NAT (Numerical Answer Type)"
        }.get(question.type, question.type.value)
        self.lbl_q_type.setText(f"Type: {type_str}")
        
        pos_txt = f"+{question.positive_marks}"
        neg_txt = f"-{question.negative_marks}" if question.negative_marks > 0 else "0 (No negative marking)"
        self.lbl_marks.setText(f"Marks: {pos_txt}  |  Negative: {neg_txt}")

        is_oos = getattr(question, "is_out_of_syllabus", False)
        self.lbl_oos.setVisible(bool(is_oos))

        # 2. Update Question Text
        formatted_text = question.question_text.replace("\n", "<br>")
        self.lbl_q_text.setText(f"<div style='font-size: 14px; color: #0f172a;'>{formatted_text}</div>")

        # 3. Update Diagram / Image if present
        pixmap = load_pixmap_from_source(question.image_url)
        if pixmap and not pixmap.isNull():
            self._active_q_pixmap = pixmap
            # Scale preview nicely for question pane
            scaled = pixmap.scaledToWidth(min(850, pixmap.width()), Qt.TransformationMode.SmoothTransformation)
            self.lbl_q_image.setPixmap(scaled)
            self.diagram_box.show()
        else:
            self._active_q_pixmap = None
            self.diagram_box.hide()

        # 4. Render Options
        self._clear_options_ui()

        if question.type == QuestionType.MCQ:
            self._render_mcq(question)
        elif question.type == QuestionType.MSQ:
            self._render_msq(question)
        elif question.type == QuestionType.NAT:
            self._render_nat(question)

    def _open_diagram_zoom(self):
        if self._active_q_pixmap:
            dlg = ImageZoomDialog(
                pixmap=self._active_q_pixmap,
                title=f"Question {self.current_question.question_number} - Diagram Zoom",
                parent=self
            )
            dlg.exec()

    def _clear_options_ui(self):
        for btn in self._mcq_group.buttons():
            self._mcq_group.removeButton(btn)
            btn.deleteLater()
            
        for cb in self._msq_checkboxes:
            cb.deleteLater()
        self._msq_checkboxes.clear()

        # Clear layout
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _render_mcq(self, question: Question):
        saved_ans = str(question.candidate_answer).strip().upper() if question.candidate_answer else ""
        
        OPTION_STYLE = """
            QRadioButton {
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                color: #0f172a;
                padding: 10px 14px;
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 6px;
                spacing: 8px;
            }
            QRadioButton:hover {
                background-color: #eff6ff;
                border-color: #93c5fd;
            }
            QRadioButton:checked {
                background-color: #dbeafe;
                border: 2px solid #2563eb;
                font-weight: 600;
                color: #1e3a8a;
            }
        """
        
        for opt in question.options:
            t = opt.text.strip()
            if t.lower().startswith(f"option ({opt.id.lower()})") or t.lower() == f"({opt.id.lower()})":
                label = f"Option ({opt.id})"
            elif t.lower().startswith("option ") and len(t) <= 10:
                label = f"Option ({opt.id})"
            else:
                label = f"({opt.id})  {opt.text}"
            rb = QRadioButton(label)
            rb.setProperty("optId", opt.id)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setStyleSheet(OPTION_STYLE)
            
            if opt.id.upper() == saved_ans:
                rb.setChecked(True)
                
            rb.toggled.connect(self._on_mcq_toggled)
            self._mcq_group.addButton(rb)

            # Option Diagram if present
            if opt.image:
                opt_pixmap = load_pixmap_from_source(opt.image)
                if opt_pixmap and not opt_pixmap.isNull():
                    opt_card = QFrame()
                    opt_card.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; }")
                    oc_layout = QVBoxLayout(opt_card)
                    oc_layout.setContentsMargins(6, 4, 6, 4)
                    oc_layout.setSpacing(4)
                    oc_layout.addWidget(rb)
                    lbl_opt_img = QLabel()
                    lbl_opt_img.setPixmap(opt_pixmap.scaledToWidth(min(450, opt_pixmap.width()), Qt.TransformationMode.SmoothTransformation))
                    lbl_opt_img.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    lbl_opt_img.mousePressEvent = lambda e, pm=opt_pixmap, oid=opt.id: ImageZoomDialog(pm, f"Option ({oid}) Diagram", self).exec()
                    oc_layout.addWidget(lbl_opt_img)
                    self.options_layout.addWidget(opt_card)
                else:
                    self.options_layout.addWidget(rb)
            else:
                self.options_layout.addWidget(rb)

    def _render_msq(self, question: Question):
        note = QLabel("<i>Note: One or more options can be correct. Full marks given only if all correct choices and no wrong choices are selected. (Zero negative marking)</i>")
        note.setStyleSheet("color: #64748b; font-size: 11px; margin-bottom: 6px;")
        self.options_layout.addWidget(note)

        saved_list = []
        if isinstance(question.candidate_answer, list):
            saved_list = [str(x).strip().upper() for x in question.candidate_answer]
        elif isinstance(question.candidate_answer, str):
            saved_list = [question.candidate_answer.strip().upper()]

        CB_STYLE = """
            QCheckBox {
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                color: #0f172a;
                padding: 10px 14px;
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                spacing: 10px;
            }
            QCheckBox:hover {
                background-color: #f0fdf4;
                border-color: #86efac;
            }
            QCheckBox:checked {
                background-color: #dcfce7;
                border: 2px solid #16a34a;
                font-weight: 600;
                color: #14532d;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #94a3b8;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #16a34a;
            }
            QCheckBox::indicator:checked {
                border-color: #15803d;
                background-color: #16a34a;
            }
        """

        for opt in question.options:
            t = opt.text.strip()
            if t.lower().startswith(f"option ({opt.id.lower()})") or t.lower() == f"({opt.id.lower()})":
                label = f"Option ({opt.id})"
            elif t.lower().startswith("option ") and len(t) <= 10:
                label = f"Option ({opt.id})"
            else:
                label = f"({opt.id})  {opt.text}"
            cb = QCheckBox(label)
            cb.setProperty("optId", opt.id)
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.setStyleSheet(CB_STYLE)
            
            if opt.id.upper() in saved_list:
                cb.setChecked(True)
                
            cb.stateChanged.connect(self._on_input_changed)
            self._msq_checkboxes.append(cb)

            # Option Diagram if present
            if opt.image:
                opt_pixmap = load_pixmap_from_source(opt.image)
                if opt_pixmap and not opt_pixmap.isNull():
                    opt_card = QFrame()
                    opt_card.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; }")
                    oc_layout = QVBoxLayout(opt_card)
                    oc_layout.setContentsMargins(6, 4, 6, 4)
                    oc_layout.setSpacing(4)
                    oc_layout.addWidget(cb)
                    lbl_opt_img = QLabel()
                    lbl_opt_img.setPixmap(opt_pixmap.scaledToWidth(min(450, opt_pixmap.width()), Qt.TransformationMode.SmoothTransformation))
                    lbl_opt_img.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    lbl_opt_img.mousePressEvent = lambda e, pm=opt_pixmap, oid=opt.id: ImageZoomDialog(pm, f"Option ({oid}) Diagram", self).exec()
                    oc_layout.addWidget(lbl_opt_img)
                    self.options_layout.addWidget(opt_card)
                else:
                    self.options_layout.addWidget(cb)
            else:
                self.options_layout.addWidget(cb)



    def _render_nat(self, question: Question):
        nat_container = QWidget()
        nat_layout = QVBoxLayout(nat_container)
        nat_layout.setContentsMargins(0, 4, 0, 4)
        nat_layout.setSpacing(10)

        lbl_hint = QLabel("Enter your numerical answer below (using keyboard or the on-screen numeric keypad):")
        lbl_hint.setStyleSheet("color: #334155; font-weight: 500;")
        nat_layout.addWidget(lbl_hint)

        inp_row = QHBoxLayout()
        inp_label = QLabel("Answer:")
        inp_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        self._nat_input = QLineEdit()
        self._nat_input.setPlaceholderText("e.g. 25.5")
        self._nat_input.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self._nat_input.setFixedWidth(200)
        self._nat_input.setFixedHeight(34)
        self._nat_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #005a9e;
                border-radius: 4px;
                padding: 4px 8px;
                color: #0f172a;
            }
        """)
        
        saved_val = str(question.candidate_answer) if question.candidate_answer is not None else ""
        self._nat_input.setText(saved_val)
        self._nat_input.textChanged.connect(self._on_input_changed)

        inp_row.addWidget(inp_label)
        inp_row.addWidget(self._nat_input)
        inp_row.addStretch()
        nat_layout.addLayout(inp_row)

        # On-screen Numeric Keypad in Pure Light Theme
        keypad_frame = QFrame()
        keypad_frame.setFixedSize(220, 180)
        keypad_frame.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #94a3b8;
                border-radius: 3px;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                font-weight: bold;
                color: #0f172a;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
            QPushButton#btnKeypadClear, QPushButton#btnKeypadBack {
                background-color: #fee2e2;
                color: #b91c1c;
                font-size: 11px;
            }
            QPushButton#btnKeypadClear:hover, QPushButton#btnKeypadBack:hover {
                background-color: #fecaca;
            }
        """)
        kp_grid = QGridLayout(keypad_frame)
        kp_grid.setContentsMargins(6, 6, 6, 6)
        kp_grid.setSpacing(4)

        keys = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("0", 3, 0), (".", 3, 1), ("-", 3, 2),
            ("Backspace", 4, 0, 1, 2), ("Clear", 4, 2, 1, 1)
        ]

        for item in keys:
            label = item[0]
            row = item[1]
            col = item[2]
            row_span = item[3] if len(item) > 3 else 1
            col_span = item[4] if len(item) > 4 else 1

            btn = QPushButton(label)
            if label == "Backspace":
                btn.setObjectName("btnKeypadBack")
                btn.clicked.connect(self._nat_backspace)
            elif label == "Clear":
                btn.setObjectName("btnKeypadClear")
                btn.clicked.connect(self._nat_clear)
            else:
                btn.clicked.connect(lambda checked, char=label: self._nat_append(char))

            kp_grid.addWidget(btn, row, col, row_span, col_span)

        nat_layout.addWidget(keypad_frame)
        self.options_layout.addWidget(nat_container)

    def _nat_append(self, char: str):
        if self._nat_input:
            curr = self._nat_input.text()
            if char == ".":
                if "." in curr:
                    return
                # Allow dot on empty field → "0."
                self._nat_input.setText(("0" if not curr or curr == "-" else curr) + ".")
                return
            if char == "-":
                # Toggle minus sign at front
                if curr.startswith("-"):
                    self._nat_input.setText(curr[1:])  # remove leading minus
                else:
                    self._nat_input.setText("-" + curr)  # add leading minus
                return
            self._nat_input.setText(curr + char)


    def _nat_backspace(self):
        if self._nat_input:
            curr = self._nat_input.text()
            if curr:
                self._nat_input.setText(curr[:-1])

    def _nat_clear(self):
        if self._nat_input:
            self._nat_input.clear()

    def _on_input_changed(self):
        self.response_changed.emit()

    def _on_mcq_toggled(self, checked: bool):
        """Emit response_changed only when a radio is actually checked (not on uncheck)."""
        if checked:
            self.response_changed.emit()

    def get_candidate_response(self) -> Any:
        if not self.current_question:
            return None

        if self.current_question.type == QuestionType.MCQ:
            checked_btn = self._mcq_group.checkedButton()
            if checked_btn:
                return checked_btn.property("optId")
            return None

        elif self.current_question.type == QuestionType.MSQ:
            selected = []
            for cb in self._msq_checkboxes:
                if cb.isChecked():
                    selected.append(cb.property("optId"))
            return sorted(selected) if selected else None

        elif self.current_question.type == QuestionType.NAT:
            if self._nat_input:
                txt = self._nat_input.text().strip()
                return txt if txt else None
            return None

    def clear_response(self):
        if not self.current_question:
            return

        if self.current_question.type == QuestionType.MCQ:
            checked = self._mcq_group.checkedButton()
            if checked:
                self._mcq_group.setExclusive(False)
                checked.setChecked(False)
                self._mcq_group.setExclusive(True)

        elif self.current_question.type == QuestionType.MSQ:
            for cb in self._msq_checkboxes:
                cb.setChecked(False)

        elif self.current_question.type == QuestionType.NAT:
            if self._nat_input:
                self._nat_input.clear()
