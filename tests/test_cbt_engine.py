"""
Automated Test Suite for CBT Engine:
- Models and JSON Paper Loading
- Strict GATE Evaluation Criteria
- Virtual Calculator Mathematical Functions
- Security Manager Logic
"""

import sys
import os
import unittest
import math

# Ensure parent directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.models import ExamPaper, Question, QuestionType, QuestionStatus, Option
from core.evaluator import ExamEvaluator
from core.storage import StorageManager
from ui.widgets.calculator import GateCalculator


class TestCbtEngine(unittest.TestCase):

    def setUp(self):
        self.storage = StorageManager(BASE_DIR)

    def test_paper_loading(self):
        papers = self.storage.load_all_papers("GATE")
        self.assertGreater(len(papers), 0, "Should load at least one GATE paper")
        
        # Check GATE EC 2024 paper
        p1 = next((p for p in papers if p.paper_id == "GATE_EC_2024"), None)
        self.assertIsNotNone(p1, "Should find GATE_EC_2024")
        self.assertEqual(len(p1.sections), 2)
        self.assertEqual(p1.sections[0].section_id, "GA")
        self.assertEqual(p1.sections[1].section_id, "EC")
        self.assertEqual(p1.total_questions_count, 65)

    def test_mcq_evaluation(self):
        # 1-mark MCQ: correct = +1, wrong = -0.33
        q1 = Question(
            question_id=1,
            question_number=1,
            type=QuestionType.MCQ,
            section_id="GA",
            section_name="General Aptitude",
            question_text="Sample MCQ",
            positive_marks=1.0,
            negative_marks=0.33,
            options=[Option("A", "Opt A"), Option("B", "Opt B")],
            correct_answer="A",
            status=QuestionStatus.ANSWERED,
            candidate_answer="A"
        )
        paper = ExamPaper(
            paper_id="TEST",
            title="Test Paper",
            exam_type="GATE",
            duration_minutes=60,
            total_marks=1.0,
            sections=[]
        )
        from core.models import Section
        paper.sections.append(Section("GA", "General Aptitude", [q1]))

        # Test correct
        res = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res.score_obtained, 1.0)
        self.assertEqual(res.correct_count, 1)
        self.assertEqual(res.incorrect_count, 0)

        # Test incorrect
        q1.candidate_answer = "B"
        res2 = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res2.score_obtained, -0.33)
        self.assertEqual(res2.incorrect_count, 1)

    def test_msq_evaluation(self):
        # MSQ: full marks only on exact match, NO negative marking
        q_msq = Question(
            question_id=2,
            question_number=2,
            type=QuestionType.MSQ,
            section_id="CS",
            section_name="Computer Science",
            question_text="Sample MSQ",
            positive_marks=2.0,
            negative_marks=0.0,
            options=[Option("A", "Opt A"), Option("B", "Opt B"), Option("C", "Opt C")],
            correct_answer=["A", "C"],
            status=QuestionStatus.ANSWERED,
            candidate_answer=["A", "C"]
        )
        from core.models import Section
        paper = ExamPaper("TEST_MSQ", "Test MSQ", "GATE", 60, 2.0, sections=[Section("CS", "Computer Science", [q_msq])])

        # Exact match -> +2.0
        res = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res.score_obtained, 2.0)
        self.assertEqual(res.correct_count, 1)

        # Partial match ["A"] -> 0 marks (not correct, but no negative marking)
        q_msq.candidate_answer = ["A"]
        res_partial = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res_partial.score_obtained, 0.0)
        self.assertEqual(res_partial.incorrect_count, 1)
        self.assertEqual(res_partial.negative_marks, 0.0)

        # Extra wrong choice ["A", "B", "C"] -> 0 marks, 0 penalty
        q_msq.candidate_answer = ["A", "B", "C"]
        res_wrong = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res_wrong.score_obtained, 0.0)
        self.assertEqual(res_wrong.negative_marks, 0.0)

    def test_msq_string_and_mta_evaluation(self):
        from core.models import Section
        # Test string formatted correct answers e.g. "A, D"
        q_str_msq = Question(
            question_id=201,
            question_number=1,
            type=QuestionType.MSQ,
            section_id="EC",
            section_name="Electronics",
            question_text="Sample String MSQ",
            positive_marks=2.0,
            negative_marks=0.0,
            options=[Option("A", "Opt A"), Option("B", "Opt B"), Option("C", "Opt C"), Option("D", "Opt D")],
            correct_answer="A, D",
            status=QuestionStatus.ANSWERED,
            candidate_answer=["A", "D"]
        )
        paper = ExamPaper("TEST_STR_MSQ", "Test String MSQ", "GATE", 60, 2.0, sections=[Section("EC", "Electronics", [q_str_msq])])
        res = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res.score_obtained, 2.0)
        self.assertEqual(res.correct_count, 1)

        # Test string candidate answer e.g. "A, D" matching ["A", "D"]
        q_str_msq.correct_answer = ["A", "D"]
        q_str_msq.candidate_answer = "A, D"
        res2 = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res2.score_obtained, 2.0)

        # Test MTA in MSQ
        q_str_msq.correct_answer = ["MTA"]
        q_str_msq.candidate_answer = ["A"]
        res_mta = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res_mta.score_obtained, 2.0)
        self.assertEqual(res_mta.correct_count, 1)

    def test_nat_evaluation(self):
        # NAT: numeric range or exact
        q_nat = Question(
            question_id=3,
            question_number=3,
            type=QuestionType.NAT,
            section_id="CS",
            section_name="Computer Science",
            question_text="Sample NAT",
            positive_marks=2.0,
            negative_marks=0.0,
            correct_answer=15.0,
            tolerance_min=14.8,
            tolerance_max=15.2,
            status=QuestionStatus.ANSWERED,
            candidate_answer="15.1"
        )
        from core.models import Section
        paper = ExamPaper("TEST_NAT", "Test NAT", "GATE", 60, 2.0, sections=[Section("CS", "Computer Science", [q_nat])])

        # Inside tolerance -> +2.0
        res = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res.score_obtained, 2.0)
        self.assertEqual(res.correct_count, 1)

        # Outside tolerance -> 0.0
        q_nat.candidate_answer = "15.5"
        res_wrong = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res_wrong.score_obtained, 0.0)
        self.assertEqual(res_wrong.negative_marks, 0.0)

    def test_answered_and_marked_for_review_evaluated(self):
        # In GATE, ANSWERED_AND_MARKED is evaluated!
        q = Question(
            question_id=4,
            question_number=4,
            type=QuestionType.MCQ,
            section_id="GA",
            section_name="General Aptitude",
            question_text="Sample Review Question",
            positive_marks=2.0,
            negative_marks=0.67,
            correct_answer="B",
            status=QuestionStatus.ANSWERED_AND_MARKED,
            candidate_answer="B"
        )
        from core.models import Section
        paper = ExamPaper("TEST_AM", "Test AM", "GATE", 60, 2.0, sections=[Section("GA", "General Aptitude", [q])])

        res = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res.score_obtained, 2.0)
        self.assertEqual(res.correct_count, 1)

        # But MARKED_FOR_REVIEW without answering is NOT evaluated (0 marks, 0 penalty)
        q.status = QuestionStatus.MARKED_FOR_REVIEW
        q.candidate_answer = None
        res2 = ExamEvaluator.evaluate_paper(paper)
        self.assertEqual(res2.score_obtained, 0.0)
        self.assertEqual(res2.unattempted_count, 1)


if __name__ == "__main__":
    unittest.main()
