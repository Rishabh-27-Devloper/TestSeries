"""
User Profile Dialog.
Allows candidate to edit and permanently persist their Name, Roll Number, Phone Number, and Exam details.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.storage import StorageManager


class UserProfileDialog(QDialog):
    profile_updated = pyqtSignal(dict) # Emits updated profile dict

    def __init__(self, storage_manager: Optional[StorageManager] = None, parent=None):
        super().__init__(parent)
        self.storage_manager = storage_manager or StorageManager()
        self.setWindowTitle("Candidate Profile & Identification")
        self.setFixedSize(460, 440)
        self.setModal(True)

        self._init_ui()
        self._load_current_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Banner
        header = QFrame()
        header.setStyleSheet("background-color: #f1f5f9; border-radius: 8px; padding: 12px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(8, 6, 8, 6)
        h_layout.setSpacing(2)

        t_lbl = QLabel("<h3>👤 Candidate Profile & Registration</h3>")
        t_lbl.setStyleSheet("color: #1e3a8a; margin: 0;")
        s_lbl = QLabel("Enter your personal details. These are saved permanently on this computer and will appear on all your official test scorecards and reports.")
        s_lbl.setWordWrap(True)
        s_lbl.setStyleSheet("color: #475569; font-size: 11px;")
        h_layout.addWidget(t_lbl)
        h_layout.addWidget(s_lbl)
        layout.addWidget(header)

        # Form Fields Container
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 14px;
            }
            QLabel {
                color: #334155;
                font-weight: 600;
                font-size: 12px;
                margin-top: 4px;
            }
            QLineEdit, QComboBox {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                color: #0f172a;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        f_layout = QVBoxLayout(form_frame)
        f_layout.setSpacing(10)

        # Name
        f_layout.addWidget(QLabel("Full Name:"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Anand Shukla")
        f_layout.addWidget(self.txt_name)

        # Roll Number / Registration ID
        f_layout.addWidget(QLabel("Roll / Registration Number:"))
        self.txt_roll = QLineEdit()
        self.txt_roll.setPlaceholderText("e.g. GATE25-EC001")
        f_layout.addWidget(self.txt_roll)

        # Phone Number
        f_layout.addWidget(QLabel("Contact / Mobile Number:"))
        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("e.g. +91 9876543210")
        f_layout.addWidget(self.txt_phone)

        # Target GATE Year
        f_layout.addWidget(QLabel("Target Exam Year:"))
        self.cmb_year = QComboBox()
        self.cmb_year.addItems(["GATE 2025", "GATE 2026", "GATE 2027", "GATE 2028"])
        f_layout.addWidget(self.cmb_year)

        layout.addWidget(form_frame)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                font-weight: 600;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Save & Apply Details")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #15803d;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
        """)
        btn_save.clicked.connect(self._save_profile)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _load_current_values(self):
        profile = self.storage_manager.load_user_profile()
        self.txt_name.setText(profile.get("name", "Candidate"))
        self.txt_roll.setText(profile.get("roll_number", "GATE25-EC001"))
        self.txt_phone.setText(profile.get("phone_number", ""))
        
        target_yr = profile.get("target_year", "2025")
        for i in range(self.cmb_year.count()):
            if target_yr in self.cmb_year.itemText(i):
                self.cmb_year.setCurrentIndex(i)
                break

    def _save_profile(self):
        name = self.txt_name.text().strip()
        roll = self.txt_roll.text().strip()
        phone = self.txt_phone.text().strip()
        yr_text = self.cmb_year.currentText()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Candidate Name cannot be empty.")
            self.txt_name.setFocus()
            return

        if not roll:
            roll = "GATE25-EC001"

        profile_data = {
            "name": name,
            "roll_number": roll,
            "phone_number": phone,
            "target_year": yr_text,
            "branch": "Electronics & Communication (ECE)"
        }

        # Save to storage immediately
        self.storage_manager.save_user_profile(profile_data)
        self.profile_updated.emit(profile_data)
        self.accept()
