"""
Official GATE / TCS iON Virtual Scientific Calculator.
Expression-based scientific calculator that writes full equations as typed
and evaluates upon pressing '='.
Includes high-precision trigonometry (Deg/Rad), powers, roots, logarithms,
factorials, memory functions, and responsive draggable title bar.
"""

import math
import re
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLineEdit, QLabel, QRadioButton, QButtonGroup, QWidget
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QKeyEvent


class CalculatorTitleBar(QWidget):
    """Custom title bar that handles window dragging without blocking button clicks."""
    def __init__(self, parent_dialog: QDialog, title: str = "TCS iON / GATE Virtual Calculator"):
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog
        self._drag_pos = QPoint()
        self.setObjectName("calcTitleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 6, 4)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("calcTitle")
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #ffffff; background: transparent;")

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("calcCloseBtn")
        self.btn_close.setFixedSize(32, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Close Calculator")
        self.btn_close.clicked.connect(self.parent_dialog.hide)

        layout.addWidget(lbl_title)
        layout.addStretch()
        layout.addWidget(self.btn_close)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_dialog.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.parent_dialog.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()


class GateCalculator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GATE Virtual Scientific Calculator")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(510, 490)
        
        # State
        self.is_deg = True
        self.memory_val = 0.0
        self.evaluated = False
        self.last_result = 0.0
        
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(4)

        # 1. Custom Title Bar with working Close Button & Dragging
        self.title_bar = CalculatorTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # 2. Display Area (History Line + Main Equation/Answer Line)
        disp_container = QWidget()
        disp_container.setObjectName("calcDispContainer")
        disp_layout = QVBoxLayout(disp_container)
        disp_layout.setContentsMargins(10, 6, 10, 6)
        disp_layout.setSpacing(2)

        # Top line: Expression history (e.g. "sin(30) + 12 =")
        self.history_line = QLabel("")
        self.history_line.setObjectName("calcHistory")
        self.history_line.setAlignment(Qt.AlignmentFlag.AlignRight)
        disp_layout.addWidget(self.history_line)

        # Main expression / result display
        self.display = QLineEdit("0")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setObjectName("calcDisplay")
        disp_layout.addWidget(self.display)

        main_layout.addWidget(disp_container)

        # 3. Angle Mode Radio Bar (Deg / Rad) & Memory status
        mode_bar = QHBoxLayout()
        mode_bar.setContentsMargins(10, 2, 10, 2)
        
        self.deg_rad_group = QButtonGroup(self)
        self.rad_deg_btn = QRadioButton("Deg")
        self.rad_rad_btn = QRadioButton("Rad")
        self.rad_deg_btn.setChecked(True)
        self.deg_rad_group.addButton(self.rad_deg_btn)
        self.deg_rad_group.addButton(self.rad_rad_btn)
        self.rad_deg_btn.toggled.connect(self._on_angle_mode_changed)

        self.mem_indicator = QLabel("")
        self.mem_indicator.setObjectName("calcMemIndicator")

        lbl_mode = QLabel("Angle Mode:")
        lbl_mode.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        mode_bar.addWidget(lbl_mode)
        mode_bar.addWidget(self.rad_deg_btn)
        mode_bar.addWidget(self.rad_rad_btn)
        mode_bar.addStretch()
        mode_bar.addWidget(self.mem_indicator)
        main_layout.addLayout(mode_bar)

        # 4. Calculator Keypad Grid
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(6, 4, 6, 6)
        grid.setSpacing(4)

        # Buttons matching GATE TCS iON layout
        buttons = [
            # Row 0: Memory & Edit
            ("MC", 0, 0, "mem", "mc"),
            ("MR", 0, 1, "mem", "mr"),
            ("MS", 0, 2, "mem", "ms"),
            ("M+", 0, 3, "mem", "m+"),
            ("M-", 0, 4, "mem", "m-"),
            ("←", 0, 5, "edit", "backspace"),
            ("C", 0, 6, "edit", "clear"),

            # Row 1: Hyperbolic & Basic functions
            ("sinh", 1, 0, "func", "sinh("),
            ("cosh", 1, 1, "func", "cosh("),
            ("tanh", 1, 2, "func", "tanh("),
            ("(", 1, 3, "text", "("),
            (")", 1, 4, "text", ")"),
            ("n!", 1, 5, "func", "!"),
            ("mod", 1, 6, "op", " % "),

            # Row 2: Trig & Digits 7,8,9
            ("sin", 2, 0, "func", "sin("),
            ("cos", 2, 1, "func", "cos("),
            ("tan", 2, 2, "func", "tan("),
            ("7", 2, 3, "digit", "7"),
            ("8", 2, 4, "digit", "8"),
            ("9", 2, 5, "digit", "9"),
            ("/", 2, 6, "op", " / "),

            # Row 3: Inverse Trig & Digits 4,5,6
            ("sin⁻¹", 3, 0, "func", "asin("),
            ("cos⁻¹", 3, 1, "func", "acos("),
            ("tan⁻¹", 3, 2, "func", "atan("),
            ("4", 3, 3, "digit", "4"),
            ("5", 3, 4, "digit", "5"),
            ("6", 3, 5, "digit", "6"),
            ("*", 3, 6, "op", " * "),

            # Row 4: Powers, Roots & Digits 1,2,3
            ("ln", 4, 0, "func", "ln("),
            ("log₁₀", 4, 1, "func", "log10("),
            ("√x", 4, 2, "func", "sqrt("),
            ("1", 4, 3, "digit", "1"),
            ("2", 4, 4, "digit", "2"),
            ("3", 4, 5, "digit", "3"),
            ("-", 4, 6, "op", " - "),

            # Row 5: Exponents, Constants & 0, ., =, +
            ("eˣ", 5, 0, "func", "exp("),
            ("10ˣ", 5, 1, "func", "10^("),
            ("1/x", 5, 2, "func", "1/("),
            ("0", 5, 3, "digit", "0"),
            (".", 5, 4, "digit", "."),
            ("=", 5, 5, "eval", "="),
            ("+", 5, 6, "op", " + "),

            # Row 6: Additional GATE functions
            ("π", 6, 0, "text", "π"),
            ("e", 6, 1, "text", "e"),
            ("x²", 6, 2, "func", "^2"),
            ("x³", 6, 3, "func", "^3"),
            ("xʸ", 6, 4, "op", "^"),
            ("+/-", 6, 5, "edit", "negate"),
            ("|x|", 6, 6, "func", "abs(")
        ]

        for label, row, col, btype, val in buttons:
            btn = QPushButton(label)
            btn.setObjectName(f"calcBtn_{btype}")
            btn.setFixedSize(64, 34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=btype, v=val: self._handle_input(t, v))
            grid.addWidget(btn, row, col)

        main_layout.addWidget(grid_widget)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f1f5f9;
                border: 2px solid #1a56a5;
                border-radius: 6px;
            }
            #calcTitleBar {
                background-color: #1a56a5;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            #calcTitle {
                color: #ffffff;
                font-weight: bold;
            }
            #calcCloseBtn {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 13px;
            }
            #calcCloseBtn:hover {
                background-color: #dc2626;
            }
            #calcDispContainer {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 4px;
            }
            #calcHistory {
                color: #64748b;
                font-size: 12px;
                min-height: 16px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            #calcDisplay {
                background-color: transparent;
                border: none;
                font-size: 20px;
                font-family: 'Consolas', 'Segoe UI', monospace;
                font-weight: bold;
                color: #0f172a;
            }
            #calcMemIndicator {
                color: #2563eb;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton[objectName^="calcBtn_"] {
                font-family: 'Segoe UI', Arial;
                font-size: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: #ffffff;
                color: #1e293b;
            }
            QPushButton[objectName="calcBtn_digit"] {
                background-color: #ffffff;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton[objectName="calcBtn_digit"]:hover {
                background-color: #eff6ff;
                border-color: #3b82f6;
            }
            QPushButton[objectName="calcBtn_op"] {
                background-color: #f8fafc;
                color: #1d4ed8;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton[objectName="calcBtn_op"]:hover {
                background-color: #dbeafe;
            }
            QPushButton[objectName="calcBtn_func"] {
                background-color: #f1f5f9;
                color: #1e3a8a;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton[objectName="calcBtn_func"]:hover {
                background-color: #e2e8f0;
            }
            QPushButton[objectName="calcBtn_text"] {
                background-color: #f8fafc;
                color: #334155;
                font-weight: bold;
            }
            QPushButton[objectName="calcBtn_mem"] {
                background-color: #f1f5f9;
                color: #475569;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton[objectName="calcBtn_edit"] {
                background-color: #fee2e2;
                color: #b91c1c;
                font-weight: bold;
            }
            QPushButton[objectName="calcBtn_edit"]:hover {
                background-color: #fecaca;
            }
            QPushButton[objectName="calcBtn_eval"] {
                background-color: #16a34a;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #15803d;
            }
            QPushButton[objectName="calcBtn_eval"]:hover {
                background-color: #15803d;
            }
            QPushButton:pressed {
                background-color: #bfdbfe;
            }
        """)

    def _on_angle_mode_changed(self):
        self.is_deg = self.rad_deg_btn.isChecked()

    def keyPressEvent(self, event: QKeyEvent):
        """Allow closing via Escape and typing numbers/operators via keyboard."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._evaluate()
            return
        elif event.key() == Qt.Key.Key_Backspace:
            self._handle_backspace()
            return

        text = event.text()
        if text in "0123456789.":
            self._handle_input("digit", text)
        elif text in "+-*/%^()":
            self._handle_input("op" if text in "+-*/%^" else "text", text)

    def _handle_input(self, btype: str, val: str):
        curr = self.display.text()

        if btype == "digit":
            if self.evaluated or curr in ("0", "Error"):
                self.display.setText(val)
                self.evaluated = False
            else:
                self.display.setText(curr + val)

        elif btype in ("op", "text", "func"):
            if self.evaluated:
                # Continuing from previous evaluation
                if btype == "op":
                    self.display.setText(f"{self.last_result}{val}")
                else:
                    self.display.setText(val)
                self.evaluated = False
            else:
                if curr in ("0", "Error") and btype != "op":
                    self.display.setText(val)
                else:
                    self.display.setText(curr + val)

        elif btype == "edit":
            if val == "clear":
                self.display.setText("0")
                self.history_line.setText("")
                self.evaluated = False
            elif val == "backspace":
                self._handle_backspace()
            elif val == "negate":
                self._handle_negate()

        elif btype == "mem":
            self._handle_mem(val)

        elif btype == "eval":
            self._evaluate()

    def _handle_backspace(self):
        curr = self.display.text()
        if len(curr) > 1 and curr != "Error":
            # If ends with spaces e.g. " + ", remove the whole token
            if curr.endswith(" "):
                self.display.setText(curr.rstrip()[:-1].rstrip())
            else:
                self.display.setText(curr[:-1])
        else:
            self.display.setText("0")
            self.evaluated = False

    def _handle_negate(self):
        curr = self.display.text().strip()
        if curr in ("0", "Error"):
            return
        if curr.startswith("-"):
            self.display.setText(curr[1:])
        elif curr.startswith("(-") and curr.endswith(")"):
            self.display.setText(curr[2:-1])
        else:
            self.display.setText(f"-({curr})")

    def _handle_mem(self, op: str):
        try:
            curr_val = self._evaluate_expression(self.display.text())
        except Exception:
            curr_val = self.last_result

        if op == "mc":
            self.memory_val = 0.0
            self.mem_indicator.setText("")
        elif op == "ms":
            self.memory_val = curr_val
            self.mem_indicator.setText("M")
        elif op == "mr":
            val_str = self._format_number(self.memory_val)
            curr = self.display.text()
            if self.evaluated or curr in ("0", "Error"):
                self.display.setText(val_str)
            else:
                self.display.setText(curr + val_str)
            self.evaluated = False
        elif op == "m+":
            self.memory_val += curr_val
            self.mem_indicator.setText("M")
        elif op == "m-":
            self.memory_val -= curr_val
            self.mem_indicator.setText("M")

    def _evaluate(self):
        raw_expr = self.display.text().strip()
        if not raw_expr or raw_expr == "Error":
            return

        try:
            # Auto-close open parentheses
            open_count = raw_expr.count("(")
            close_count = raw_expr.count(")")
            if open_count > close_count:
                raw_expr += ")" * (open_count - close_count)

            result = self._evaluate_expression(raw_expr)
            self.last_result = result
            formatted_res = self._format_number(result)

            self.history_line.setText(f"{raw_expr} =")
            self.display.setText(formatted_res)
            self.evaluated = True
        except Exception as e:
            self.history_line.setText(f"{raw_expr} =")
            self.display.setText("Error")
            self.evaluated = True

    def _evaluate_expression(self, expr_str: str) -> float:
        """Safely parses and evaluates an expression string with Deg/Rad trig."""
        s = expr_str.strip()
        if not s:
            return 0.0

        # Replace constants and operators
        s = s.replace("π", str(math.pi))
        s = s.replace("^", "**")

        # Handle factorials like 5! -> math.factorial(5)
        s = re.sub(r"(\d+)\s*!", r"math.factorial(\1)", s)
        s = re.sub(r"fact\s*\(\s*(\d+)\s*\)", r"math.factorial(\1)", s)

        is_deg = self.is_deg

        def deg_sin(x): return math.sin(math.radians(x) if is_deg else x)
        def deg_cos(x): return math.cos(math.radians(x) if is_deg else x)
        def deg_tan(x): return math.tan(math.radians(x) if is_deg else x)
        def deg_asin(x):
            r = math.asin(x)
            return math.degrees(r) if is_deg else r
        def deg_acos(x):
            r = math.acos(x)
            return math.degrees(r) if is_deg else r
        def deg_atan(x):
            r = math.atan(x)
            return math.degrees(r) if is_deg else r

        safe_env = {
            "__builtins__": {},
            "math": math,
            "sin": deg_sin,
            "cos": deg_cos,
            "tan": deg_tan,
            "asin": deg_asin,
            "acos": deg_acos,
            "atan": deg_atan,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "ln": math.log,
            "log": math.log,
            "log10": math.log10,
            "sqrt": math.sqrt,
            "exp": math.exp,
            "abs": abs,
            "e": math.e,
            "pi": math.pi,
        }

        val = eval(s, safe_env, {})
        return float(val)

    def _format_number(self, val: float) -> str:
        if isinstance(val, int) or (isinstance(val, float) and val.is_integer()):
            return str(int(val))
        formatted = f"{val:.8f}".rstrip("0").rstrip(".")
        return formatted
