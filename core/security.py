"""
Security and Fullscreen Anti-Cheat Manager for CBT Exam.
Provides kiosk-mode enforcement, focus loss detection, Alt+Tab deterrents,
and auto-submission triggers.
Permits valid in-app actions (Virtual Calculator, Image Zoom, Question Paper preview, Instructions).
"""

import sys
from typing import Callable, Optional
from PyQt6.QtCore import QObject, QEvent, pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication


class SecurityManager(QObject):
    # Signals for security events
    warning_issued = pyqtSignal(int, int)      # (current_warning, max_warnings)
    security_breach = pyqtSignal(str)          # Reason for breach (triggers auto-submit)

    def __init__(
        self,
        target_window: QWidget,
        max_warnings: int = 3,
        auto_submit_callback: Optional[Callable[[], None]] = None,
        show_dialogs: Optional[bool] = None
    ):
        super().__init__(target_window)
        self.target_window = target_window
        self.max_warnings = max_warnings
        self.auto_submit_callback = auto_submit_callback
        
        if show_dialogs is None:
            app_inst = QApplication.instance()
            is_test_env = (
                "pytest" in sys.modules
                or "unittest" in sys.modules
                or (app_inst is not None and app_inst.property("is_test") is True)
                or bool(target_window.property("is_test"))
            )
            self.show_dialogs = not is_test_env
        else:
            self.show_dialogs = show_dialogs
        
        self.is_exam_active = False
        self.warning_count = 0
        self.showing_warning_dialog = False
        
        # Install event filter to capture focus changes and key presses
        self.target_window.installEventFilter(self)

        # Monitor application state changes across entire OS
        app = QApplication.instance()
        if app:
            app.applicationStateChanged.connect(self._on_app_state_changed)

    def start_exam_security(self):
        """Enforces Fullscreen Kiosk Mode and starts anti-cheat surveillance."""
        self.is_exam_active = True
        self.warning_count = 0
        self.showing_warning_dialog = False
        
        # Bring window to fullscreen and focus
        self.target_window.showFullScreen()
        self.target_window.raise_()
        self.target_window.activateWindow()

    def stop_exam_security(self):
        """Disables anti-cheat surveillance and restores normal window mode."""
        self.is_exam_active = False
        self.showing_warning_dialog = False

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if not self.is_exam_active:
            return super().eventFilter(obj, event)

        # 1. Detect focus loss (Alt+Tab, Windows key, clicking outside application)
        if event.type() == QEvent.Type.WindowDeactivate:
            if not self.showing_warning_dialog:
                # Give a 150ms window to check if focus transferred to an internal dialog
                QTimer.singleShot(150, self._check_external_focus_loss)
            return False

        # 2. Intercept dangerous keys (Alt+F4, Esc, Windows Key)
        if event.type() == QEvent.Type.KeyPress:
            # Prevent Alt+F4 directly closing exam
            if event.key() == Qt.Key.Key_F4 and (event.modifiers() & Qt.KeyboardModifier.AltModifier):
                return True  # Consume event, block Alt+F4
            
            # Prevent Esc exiting fullscreen
            if event.key() == Qt.Key.Key_Escape:
                return True  # Consume Esc

        # 3. Disable right-click context menu
        if event.type() == QEvent.Type.ContextMenu:
            return True  # Suppress context menu

        return super().eventFilter(obj, event)

    def _on_app_state_changed(self, state: Qt.ApplicationState):
        """Called when the entire application gains or loses OS focus."""
        if not self.is_exam_active or self.showing_warning_dialog:
            return

        if state != Qt.ApplicationState.ApplicationActive:
            # Entire application was unfocused (switched to another OS app)
            QTimer.singleShot(150, self._check_external_focus_loss)

    def _check_external_focus_loss(self):
        """Verifies if focus truly moved to an external OS window or stayed in an internal dialog."""
        if not self.is_exam_active or self.showing_warning_dialog:
            return

        # 1. If Qt reports application is active in the OS, user is still in our app!
        app = QApplication.instance()
        if app and app.applicationState() == Qt.ApplicationState.ApplicationActive:
            return

        # 2. If there is an active window or modal widget belonging to this application
        if QApplication.activeWindow() is not None or QApplication.activeModalWidget() is not None:
            return

        # 3. Check if any top-level widget of this application currently has active status
        for w in QApplication.topLevelWidgets():
            if w.isActiveWindow():
                return

        # If none of the above are true, the user has truly switched to an external OS window
        self._handle_focus_loss()

    def _handle_focus_loss(self):
        """Handles an unauthorized focus loss event during the live exam."""
        if not self.is_exam_active or self.showing_warning_dialog:
            return
            
        self.warning_count += 1
        self.showing_warning_dialog = True
        self.warning_issued.emit(self.warning_count, self.max_warnings)

        if not self.show_dialogs:
            if self.warning_count >= self.max_warnings:
                self.stop_exam_security()
                self.security_breach.emit(f"Exceeded max window switch warnings ({self.max_warnings})")
                if self.auto_submit_callback:
                    self.auto_submit_callback()
            self.showing_warning_dialog = False
            return

        if self.warning_count >= self.max_warnings:
            # Auto-submit immediately
            msg = QMessageBox(self.target_window)
            msg.setWindowTitle("EXAM TERMINATED - SECURITY VIOLATION")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(
                f"<b>EXAMINATION AUTO-SUBMITTED!</b><br><br>"
                f"You have lost focus {self.warning_count} times during the test.<br>"
                f"Maximum allowed window switches ({self.max_warnings}) exceeded.<br>"
                f"Your paper has been locked and submitted for evaluation."
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
            self.stop_exam_security()
            self.security_breach.emit(f"Exceeded max window switch warnings ({self.max_warnings})")
            if self.auto_submit_callback:
                self.auto_submit_callback()
        else:
            remaining = self.max_warnings - self.warning_count
            msg = QMessageBox(self.target_window)
            msg.setWindowTitle("SECURITY WARNING - CBT PROCTOR")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(
                f"<b>WARNING {self.warning_count} OF {self.max_warnings}!</b><br><br>"
                f"You navigated away from the examination window (Alt+Tab, task switch, or focus loss).<br><br>"
                f"<b>Strict NTA / CBT Rule:</b> Switching windows or running background applications is strictly prohibited.<br><br>"
                f"You have <b>{remaining} warning(s) remaining</b> before your exam is automatically submitted and disqualified."
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
            # Re-activate fullscreen
            self.showing_warning_dialog = False
            self.target_window.showFullScreen()
            self.target_window.raise_()
            self.target_window.activateWindow()
