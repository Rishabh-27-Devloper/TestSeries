"""
Official TCS iON / NTA Light Theme Stylesheet & Color Tokens.
Pure crisp light theme for daytime CBT examination environments.
Zero dark theme - matches authentic examination center monitor aesthetics.
"""

TCS_LIGHT_STYLESHEET = """
/* Global Application Style */
QWidget {
    font-family: 'Segoe UI', Arial, 'Helvetica Neue', sans-serif;
    color: #1e293b;
    background-color: #f8fafc;
}

/* Main Windows and Containers */
QMainWindow, QDialog {
    background-color: #f1f5f9;
}

/* Headers and Navigation Bars */
QFrame#cbtHeader {
    background-color: #1a56a5;
    border-bottom: 2px solid #133e75;
}

QFrame#cbtHeader QLabel {
    background-color: transparent;
    color: #ffffff;
}

QPushButton#btnExitExam {
    background-color: #b91c1c;
    color: #ffffff;
    font-weight: bold;
    font-size: 11px;
    border: 1px solid #991b1b;
    border-radius: 4px;
    padding: 5px 12px;
}

QPushButton#btnExitExam:hover {
    background-color: #991b1b;
}

QFrame#secTabBar {
    background-color: #e2e8f0;
    border-bottom: 1px solid #cbd5e1;
}

/* Card Containers */
QFrame#portalBanner, QFrame#paperHeaderBanner, QFrame#instHeader, QFrame#paperCard {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}

/* Scroll Areas */
QScrollArea {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
}

QScrollBar:vertical {
    background: #f1f5f9;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Buttons */
QPushButton {
    font-family: 'Segoe UI', Arial;
    font-weight: 600;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    color: #1e293b;
}

QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}

/* Primary Action Buttons */
QPushButton#btnSaveNext {
    background-color: #16a34a;
    color: #ffffff;
    border: 1px solid #15803d;
    font-weight: bold;
    font-size: 13px;
    padding: 7px 22px;
}
QPushButton#btnSaveNext:hover {
    background-color: #15803d;
}

QPushButton#btnMarkReview {
    background-color: #7c3aed;
    color: #ffffff;
    border: 1px solid #6d28d9;
    font-weight: bold;
    font-size: 12px;
    padding: 7px 16px;
}
QPushButton#btnMarkReview:hover {
    background-color: #6d28d9;
}

QPushButton#btnClearResponse {
    background-color: #ffffff;
    color: #dc2626;
    border: 1px solid #ef4444;
    font-weight: bold;
    padding: 7px 16px;
}
QPushButton#btnClearResponse:hover {
    background-color: #fee2e2;
}

QPushButton#btnSubmitExam {
    background-color: #15803d;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #14532d;
    padding: 8px 18px;
}
QPushButton#btnSubmitExam:hover {
    background-color: #166534;
}

/* Radio Buttons & Checkboxes */
QRadioButton, QCheckBox {
    background-color: #ffffff;
    color: #0f172a;
    font-size: 13px;
    padding: 8px 12px;
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

/* Inputs and LineEdits */
QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #005a9e;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    color: #0f172a;
    gridline-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
}

QHeaderView::section {
    background-color: #e2e8f0;
    color: #1e293b;
    font-weight: bold;
    font-size: 12px;
    padding: 6px;
    border: 1px solid #cbd5e1;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #e2e8f0;
    color: #334155;
    font-weight: bold;
    font-size: 12px;
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}

QTabBar::tab:selected {
    background-color: #1a56a5;
    color: #ffffff;
}
"""
