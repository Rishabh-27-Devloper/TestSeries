"""
Offscreen Integration Test for GUI components:
- MainWindow creation and navigation between Layer 1, Layer 2, Layer 3, and Dashboard.
- GateCalculator math operations (Trig, Deg/Rad, Memory, Factorial, Exponents).
- QuestionDisplayWidget for MCQ, MSQ, and NAT.
- PaletteWidget and live counts.
"""

import sys
import os
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QFrame
from ui.main_window import MainWindow
from ui.widgets.calculator import GateCalculator
from ui.widgets.palette import PaletteWidget
from ui.widgets.question_display import QuestionDisplayWidget
from core.models import Question, QuestionType, QuestionStatus, Option
from core.storage import StorageManager


class TestGuiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(["cbt_test"])

    def test_main_window_layers(self):
        win = MainWindow()
        self.assertIsNotNone(win)
        self.assertEqual(win.stack.currentIndex(), 0, "Initial layer should be Layer 1 (Exam Selection)")

        # Switch to Layer 2
        win._on_exam_selected("GATE")
        self.assertEqual(win.stack.currentIndex(), 1, "Should switch to Layer 2 (Paper Inventory)")

        # Select a paper and switch to Layer 3 Instructions
        papers = win.storage_manager.load_all_papers("GATE")
        self.assertGreater(len(papers), 0)
        paper = papers[0]
        
        win._on_paper_selected(paper)
        self.assertEqual(win.stack.currentIndex(), 3, "Should switch to Layer 3 Instructions")

        # Agree to declaration and launch live exam
        win._current_instructions.chk_declare.setChecked(True)
        self.assertTrue(win._current_instructions.btn_begin.isEnabled())
        
        win._launch_live_cbt_exam()
        self.assertEqual(win.stack.currentIndex(), 4, "Should launch Live CBT Exam")
        self.assertIsNotNone(win._current_exam_window)

        # Finalize exam and check dashboard transition
        win._current_exam_window._finalize_and_submit()
        self.assertEqual(win.stack.currentIndex(), 2, "Should transition to Student Dashboard")
        self.assertIsNotNone(win.dashboard.latest_result)
        
        win.close()

    def test_topicwise_paper_selection_and_launch(self):
        win = MainWindow()
        win._on_exam_selected("GATE")
        self.assertEqual(win.stack.currentIndex(), 1)
        
        # Filter by Topic-wise
        win.layer2.cat_filter.setCurrentText("Topic-wise")
        self.assertEqual(len(win.layer2.filtered_papers), 72)
        
        # Filter by Full Length PYQ
        win.layer2.cat_filter.setCurrentText("Full Length PYQ")
        self.assertEqual(len(win.layer2.filtered_papers), 31)
        
        # Reset to Topic-wise and select 555 Timer
        win.layer2.cat_filter.setCurrentText("Topic-wise")
        topic_paper = [p for p in win.layer2.filtered_papers if "555" in p.paper_id][0]
        self.assertEqual(topic_paper.category, "Topic-wise")
        self.assertEqual(len(topic_paper.all_questions), 3)
        
        win._on_paper_selected(topic_paper)
        self.assertEqual(win.stack.currentIndex(), 3)
        
        win._current_instructions.chk_declare.setChecked(True)
        win._launch_live_cbt_exam()
        self.assertEqual(win.stack.currentIndex(), 4)
        self.assertIsNotNone(win._current_exam_window)
        self.assertEqual(len(win._current_exam_window.all_questions), 3)
        
        win._current_exam_window._finalize_and_submit()
        self.assertEqual(win.stack.currentIndex(), 2)
        win.close()

    def test_calculator_math(self):
        calc = GateCalculator()
        
        # Test number input
        calc._handle_input("digit", "4")
        calc._handle_input("digit", "5")
        self.assertEqual(calc.display.text(), "45")

        # Test Trig in Deg mode: sin(30) = 0.5
        calc.is_deg = True
        calc._handle_input("edit", "clear")
        calc._handle_input("func", "sin(")
        calc._handle_input("digit", "3")
        calc._handle_input("digit", "0")
        calc._handle_input("eval", "=")
        self.assertAlmostEqual(float(calc.display.text()), 0.5, places=4)

        # Test Sqrt: sqrt(144) = 12
        calc._handle_input("edit", "clear")
        calc._handle_input("func", "sqrt(")
        calc._handle_input("digit", "1")
        calc._handle_input("digit", "4")
        calc._handle_input("digit", "4")
        calc._handle_input("eval", "=")
        self.assertEqual(calc.display.text(), "12")

        # Test Factorial: 5! = 120
        calc._handle_input("edit", "clear")
        calc._handle_input("digit", "5")
        calc._handle_input("func", "!")
        calc._handle_input("eval", "=")
        self.assertEqual(calc.display.text(), "120")

        # Test Memory Store and Recall
        calc.display.setText("99")
        calc._handle_input("mem", "ms")
        self.assertEqual(calc.memory_val, 99.0)
        calc.display.setText("0")
        calc._handle_input("mem", "mr")
        self.assertEqual(calc.display.text(), "99")

        calc.close()

    def test_question_display_modes(self):
        qd = QuestionDisplayWidget()

        # Test MCQ
        q_mcq = Question(
            1, 1, QuestionType.MCQ, "GA", "GA", "Test MCQ",
            options=[Option("A", "Apple"), Option("B", "Banana")],
            correct_answer="A"
        )
        qd.load_question(q_mcq)
        self.assertIsNone(qd.get_candidate_response())
        # Simulate selecting B
        for btn in qd._mcq_group.buttons():
            if btn.property("optId") == "B":
                btn.setChecked(True)
        self.assertEqual(qd.get_candidate_response(), "B")

        # Test MSQ
        q_msq = Question(
            2, 2, QuestionType.MSQ, "CS", "CS", "Test MSQ",
            options=[Option("A", "One"), Option("B", "Two"), Option("C", "Three")],
            correct_answer=["A", "C"]
        )
        qd.load_question(q_msq)
        for cb in qd._msq_checkboxes:
            if cb.property("optId") in ["A", "C"]:
                cb.setChecked(True)
        self.assertEqual(qd.get_candidate_response(), ["A", "C"])

        # Test NAT
        q_nat = Question(
            3, 3, QuestionType.NAT, "CS", "CS", "Test NAT",
            correct_answer=42.5
        )
        qd.load_question(q_nat)
        qd._nat_input.setText("42.5")
        self.assertEqual(qd.get_candidate_response(), "42.5")


    def test_security_manager_permits_in_app_dialogs(self):
        from core.security import SecurityManager
        from PyQt6.QtWidgets import QDialog, QApplication
        
        target = QWidget()
        target.show()
        sec = SecurityManager(target_window=target, max_warnings=3, show_dialogs=False)
        sec.start_exam_security()
        self.assertTrue(sec.is_exam_active)
        self.assertEqual(sec.warning_count, 0)
        
        # Open an in-app dialog and simulate activation
        dlg = QDialog(target)
        dlg.show()
        QApplication.setActiveWindow(dlg)
        
        # Verify focus loss check passes without incrementing warnings
        sec._check_external_focus_loss()
        self.assertEqual(sec.warning_count, 0, "In-app dialog must not trigger security warning")
        
    def test_user_profile_persistence_and_visual_dashboard(self):
        storage = StorageManager()
        test_prof = {
            "name": "Test Candidate",
            "roll_number": "GATE25-TST01",
            "phone_number": "+91 9123456789",
            "target_year": "GATE 2025",
            "branch": "ECE"
        }
        storage.save_user_profile(test_prof)
        loaded = storage.load_user_profile()
        self.assertEqual(loaded["name"], "Test Candidate")
        self.assertEqual(loaded["roll_number"], "GATE25-TST01")
        self.assertEqual(loaded["phone_number"], "+91 9123456789")

        # Verify Dashboard tabs and attempt loading
        win = MainWindow()
        self.assertEqual(win.student_name, "Test Candidate")
        self.assertEqual(win.roll_number, "GATE25-TST01")
        self.assertEqual(win.phone_number, "+91 9123456789")
        self.assertEqual(win.dashboard.tabs.count(), 3)

        attempts = storage.load_all_attempts()
        if attempts:
            fp = attempts[0].get("_filePath")
            if fp and os.path.exists(fp):
                res = storage.load_attempt_result(fp)
                self.assertIsNotNone(res)
                win.dashboard.set_result(res)
                self.assertIsNotNone(win.dashboard.latest_result)

    def test_msq_multi_selection_palette_and_submission_details(self):
        from ui.layer3_cbt_exam import CbtExamWindow
        from ui.widgets.popups import SubmitConfirmationDialog

        storage = StorageManager()
        paper_file = os.path.join(storage.papers_dir, "gate_ec_topicwise", "gate_ec_topicwise_analog_communication_systems.json")
        paper = storage.load_paper_from_file(paper_file)
        self.assertIsNotNone(paper)

        # Q2 is an MSQ with correct answer ['A', 'D']
        q2 = next((q for q in paper.all_questions if q.question_number == 2), None)
        self.assertIsNotNone(q2)
        self.assertEqual(q2.type, QuestionType.MSQ)

        cbt = CbtExamWindow(paper=paper, storage_manager=storage)
        cbt.setProperty("is_test", True)

        # Go to Q2
        q2_idx = paper.all_questions.index(q2)
        cbt._on_palette_question_clicked(q2_idx)

        # Select Option A and Option D
        cb_a = next(cb for cb in cbt.q_display._msq_checkboxes if cb.property("optId") == "A")
        cb_d = next(cb for cb in cbt.q_display._msq_checkboxes if cb.property("optId") == "D")
        
        cb_a.setChecked(True)
        cb_d.setChecked(True)

        # Verify candidate response is multiple options
        resp = cbt.q_display.get_candidate_response()
        self.assertEqual(resp, ["A", "D"])

        # Verify auto-save immediately updated candidate_answer and status
        self.assertEqual(q2.candidate_answer, ["A", "D"])
        self.assertEqual(q2.status, QuestionStatus.ANSWERED)
        self.assertEqual(cbt.palette.buttons[q2_idx].status, QuestionStatus.ANSWERED)

        # Navigate away to Q1 via palette, then navigate back
        cbt._on_palette_question_clicked(0)
        self.assertEqual(cbt.current_index, 0)

        # Navigate back to Q2
        cbt._on_palette_question_clicked(q2_idx)
        self.assertEqual(cbt.current_index, q2_idx)
        cb_a_reloaded = next(cb for cb in cbt.q_display._msq_checkboxes if cb.property("optId") == "A")
        cb_d_reloaded = next(cb for cb in cbt.q_display._msq_checkboxes if cb.property("optId") == "D")
        self.assertTrue(cb_a_reloaded.isChecked(), "Option A should be restored checked")
        self.assertTrue(cb_d_reloaded.isChecked(), "Option D should be restored checked")

        # Inspect SubmitConfirmationDialog
        dlg = SubmitConfirmationDialog(paper=cbt.paper)
        self.assertEqual(dlg.tabs.count(), 2)

        # Tab 1: Section summary answered count >= 1
        ans_item = dlg.table.item(0, 2)
        self.assertIsNotNone(ans_item)
        self.assertGreaterEqual(int(ans_item.text()), 1)

        # Tab 2: Detailed Selection & Status View
        self.assertGreater(dlg.detail_table.rowCount(), 0)
        # Find Q2 row in detail table
        q2_row = None
        for r in range(dlg.detail_table.rowCount()):
            if dlg.detail_table.item(r, 0).text() == "2":
                q2_row = r
                break
        self.assertIsNotNone(q2_row, "Q2 should appear in detailed table")
        self.assertEqual(dlg.detail_table.item(q2_row, 2).text(), "MSQ")
        self.assertEqual(dlg.detail_table.item(q2_row, 3).text(), "Answered")
        self.assertIn("Option (A), Option (D)", dlg.detail_table.item(q2_row, 4).text())

        # Test Filter by MSQ only
        dlg.cb_filter.setCurrentText("MSQ Questions Only")
        for r in range(dlg.detail_table.rowCount()):
            self.assertEqual(dlg.detail_table.item(r, 2).text(), "MSQ")

    def test_layer2_chapter_filters_and_attempt_cards(self):
        win = MainWindow()
        win._on_exam_selected("GATE")
        layer2 = win.layer2

        # 1. Verify chapter filter combobox exists and has core subjects
        self.assertTrue(hasattr(layer2, "chapter_filter"))
        items = [layer2.chapter_filter.itemText(i) for i in range(layer2.chapter_filter.count())]
        self.assertIn("All Chapters / Subjects", items)
        self.assertIn("Digital Circuits", items)
        self.assertIn("Communications", items)
        self.assertIn("Signals & Systems", items)

        # 2. Filter by Digital Circuits
        layer2.chapter_filter.setCurrentText("Digital Circuits")
        self.assertGreaterEqual(len(layer2.filtered_papers), 8)
        for p in layer2.filtered_papers:
            matches_dc = "digital" in p.title.lower() or "boolean" in p.title.lower() or "combinational" in p.title.lower() or "sequential" in p.title.lower() or "logic" in p.title.lower() or "digital" in (p.description or "").lower()
            self.assertTrue(matches_dc, f"Paper {p.title} should match Digital Circuits")

        # 3. Filter by specific chapter 'Boolean Algebra'
        layer2.chapter_filter.setCurrentText("Boolean Algebra")
        self.assertEqual(len(layer2.filtered_papers), 1)
        ba_paper = layer2.filtered_papers[0]
        self.assertIn("Boolean Algebra", ba_paper.title)

        # 4. Verify Attempted Card styling and subsections
        card = None
        for i in range(layer2.cards_layout.count()):
            w = layer2.cards_layout.itemAt(i).widget()
            if w and hasattr(w, "paper") and w.paper.paper_id == ba_paper.paper_id:
                card = w
                break
        self.assertIsNotNone(card)
        self.assertTrue(card.is_attempted)
        self.assertEqual(card.objectName(), "paperCardAttempted")
        self.assertIsNotNone(card.last_attempt)
        self.assertIsNotNone(card.best_attempt)
        self.assertEqual(card.last_attempt.get("scoreObtained"), 28.34)
        self.assertGreater(len(card.findChildren(QFrame, "attemptSubCardActive")), 0)

        # 5. Check an unattempted card has NO attempt subsections
        layer2.chapter_filter.setCurrentText("Antennas")
        self.assertEqual(len(layer2.filtered_papers), 1)
        unatt_card = layer2.cards_layout.itemAt(0).widget()
        self.assertFalse(unatt_card.is_attempted)
        self.assertEqual(unatt_card.objectName(), "paperCard")
        self.assertEqual(len(unatt_card.findChildren(QFrame, "attemptSubCardActive")), 0)

        # 6. Verify import button is removed
        import_btn = win.findChild(QPushButton, "btnTopImport")
        self.assertIsNone(import_btn, "Import JSON Paper button must be removed")

        win.close()

    def test_dashboard_full_scrollability_and_past_attempts_table(self):
        from PyQt6.QtWidgets import QScrollArea
        win = MainWindow()
        dash = win.dashboard

        # Verify scroll area exists on Tab 1 (Analytics)
        dash.tabs.setCurrentIndex(0)
        scroll_analytics = dash.tab_analytics.findChild(QScrollArea, "analyticsScroll")
        self.assertIsNotNone(scroll_analytics, "Tab 1 should have a scroll area")

        # Verify scroll area exists on Tab 3 (Trends & Historical Attempts)
        dash.tabs.setCurrentIndex(2)
        scroll_trends = dash.tab_trends.findChild(QScrollArea, "trendsScroll")
        self.assertIsNotNone(scroll_trends, "Tab 3 should have a scroll area")

        win.close()


if __name__ == "__main__":
    unittest.main()


