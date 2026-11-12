"""
Evaluation Engine for CBT Examinations.
Implements official GATE evaluation rules and extensible exam criteria.
"""

import re
from datetime import datetime
from typing import Dict, Any, List
from core.models import ExamPaper, Question, QuestionType, QuestionStatus, QuestionEvaluation, ExamResult


class ExamEvaluator:
    @staticmethod
    def evaluate_paper(
        paper: ExamPaper,
        student_name: str = "Candidate",
        roll_number: str = "GATE2024-C9801",
        duration_taken_seconds: int = 0
    ) -> ExamResult:
        """
        Evaluates a completed exam paper according to official exam rules.
        For GATE:
        - Only questions in ANSWERED or ANSWERED_AND_MARKED status are evaluated.
        - MCQ: positive marks for correct; negative marks deducted for incorrect.
        - MSQ: full marks only if all correct options are selected and no wrong option is selected.
               Zero negative marking.
        - NAT: positive marks if value matches or is within [tolerance_min, tolerance_max].
               Zero negative marking.
        """
        total_paper_marks = paper.total_marks
        score_obtained = 0.0
        positive_marks_total = 0.0
        negative_marks_total = 0.0
        
        attempted_count = 0
        correct_count = 0
        incorrect_count = 0
        unattempted_count = 0
        
        evaluations: List[QuestionEvaluation] = []
        section_stats: Dict[str, Dict[str, Any]] = {}
        
        for section in paper.sections:
            section_stats[section.section_name] = {
                "total_questions": len(section.questions),
                "attempted": 0,
                "correct": 0,
                "incorrect": 0,
                "score": 0.0,
                "max_marks": sum(q.positive_marks for q in section.questions),
            }

        for q in paper.all_questions:
            # Check if this question counts as attempted for evaluation
            # In official GATE CBT:
            # 'ANSWERED' and 'ANSWERED_AND_MARKED' are evaluated.
            is_evaluated_status = (
                q.status in (
                    QuestionStatus.ANSWERED,
                    QuestionStatus.ANSWERED_AND_MARKED
                ) or (q.is_answered() and q.status != QuestionStatus.MARKED_FOR_REVIEW)
            ) and q.is_answered()
            
            is_attempted = is_evaluated_status
            is_correct = False
            marks_awarded = 0.0
            penalty = 0.0
            
            if is_attempted:
                attempted_count += 1
                sec_dict = section_stats[q.section_name]
                sec_dict["attempted"] += 1
                
                # Check correctness based on QuestionType
                if q.type == QuestionType.MCQ:
                    cand_ans = str(q.candidate_answer).strip().upper() if q.candidate_answer else ""
                    raw_corr = str(q.correct_answer).strip().upper() if q.correct_answer else ""
                    accepted_keys = [k.strip() for k in re.split(r'[,;]|\bOR\b', raw_corr) if k.strip()]
                    
                    if raw_corr in ("MTA", "MARKS TO ALL", "MARK TO ALL"):
                        is_correct = True
                        marks_awarded = float(q.positive_marks)
                    elif cand_ans in accepted_keys and cand_ans:
                        is_correct = True
                        marks_awarded = float(q.positive_marks)
                    else:
                        is_correct = False
                        penalty = float(q.negative_marks)
                        marks_awarded = -penalty
                        
                elif q.type == QuestionType.MSQ:
                    # Candidate answer is a list of options e.g. ["A", "C"]
                    cand_set = set()
                    if isinstance(q.candidate_answer, list):
                        cand_set = {str(opt).strip().upper() for opt in q.candidate_answer if str(opt).strip()}
                    elif isinstance(q.candidate_answer, str):
                        cand_set = {part.strip().upper() for part in re.split(r'[,;\s]+', q.candidate_answer) if part.strip()}
                        
                    corr_set = set()
                    if isinstance(q.correct_answer, list):
                        corr_set = {str(opt).strip().upper() for opt in q.correct_answer if str(opt).strip()}
                    elif isinstance(q.correct_answer, str):
                        corr_set = {part.strip().upper() for part in re.split(r'[,;\s]+', q.correct_answer) if part.strip()}
                        
                    if any(mta in corr_set for mta in ("MTA", "MARKS TO ALL", "MARK TO ALL")):
                        is_correct = True
                        marks_awarded = float(q.positive_marks)
                    elif cand_set == corr_set and len(corr_set) > 0:
                        is_correct = True
                        marks_awarded = float(q.positive_marks)
                    else:
                        is_correct = False
                        # GATE has ZERO negative marking for MSQ
                        penalty = 0.0
                        marks_awarded = 0.0
                        
                elif q.type == QuestionType.NAT:
                    # Candidate entered numeric string
                    is_correct = ExamEvaluator._check_nat_correctness(q)
                    if is_correct:
                        marks_awarded = float(q.positive_marks)
                    else:
                        # GATE has ZERO negative marking for NAT
                        penalty = 0.0
                        marks_awarded = 0.0
                        
                if is_correct:
                    correct_count += 1
                    positive_marks_total += marks_awarded
                    sec_dict["correct"] += 1
                else:
                    incorrect_count += 1
                    negative_marks_total += penalty
                    sec_dict["incorrect"] += 1
                    
                score_obtained += marks_awarded
                sec_dict["score"] += marks_awarded
            else:
                unattempted_count += 1
                
            evaluations.append(QuestionEvaluation(
                question_id=q.question_id,
                question_number=q.question_number,
                type=q.type,
                section_name=q.section_name,
                status=q.status,
                candidate_answer=q.candidate_answer,
                correct_answer=q.correct_answer,
                is_correct=is_correct,
                is_attempted=is_attempted,
                marks_awarded=round(marks_awarded, 2),
                max_marks=q.positive_marks,
                penalty=round(penalty, 2),
                time_spent=q.time_spent_seconds,
                explanation=q.explanation,
                image_url=q.image_url,
                question_text=q.question_text,
                is_out_of_syllabus=q.is_out_of_syllabus
            ))

        total_questions = len(paper.all_questions)
        accuracy = (correct_count / attempted_count * 100.0) if attempted_count > 0 else 0.0
        percentage_score = (score_obtained / total_paper_marks * 100.0) if total_paper_marks > 0 else 0.0

        return ExamResult(
            paper_id=paper.paper_id,
            paper_title=paper.title,
            exam_type=paper.exam_type,
            student_name=student_name,
            roll_number=roll_number,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration_taken_seconds=duration_taken_seconds,
            total_marks=total_paper_marks,
            score_obtained=round(score_obtained, 2),
            positive_marks=round(positive_marks_total, 2),
            negative_marks=round(negative_marks_total, 2),
            total_questions=total_questions,
            attempted_count=attempted_count,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unattempted_count=unattempted_count,
            accuracy_percentage=round(accuracy, 2),
            percentage_score=round(percentage_score, 2),
            section_scores=section_stats,
            evaluations=evaluations
        )

    @staticmethod
    def _check_nat_correctness(q: Question) -> bool:
        if q.candidate_answer is None or str(q.candidate_answer).strip() == "":
            return False
            
        try:
            cand_val = float(str(q.candidate_answer).strip())
        except (ValueError, TypeError):
            return False

        # Tolerance range specified?
        if q.tolerance_min is not None and q.tolerance_max is not None:
            return q.tolerance_min <= cand_val <= q.tolerance_max

        # Dict format in correct_answer e.g. {"min": 5.10, "max": 5.20}
        if isinstance(q.correct_answer, dict):
            min_v = float(q.correct_answer.get("min", -float("inf")))
            max_v = float(q.correct_answer.get("max", float("inf")))
            return min_v <= cand_val <= max_v

        # Single numeric value in correct_answer
        try:
            corr_val = float(q.correct_answer)
            # Default tolerance of 0.01 if not specified
            return abs(cand_val - corr_val) <= 0.01
        except (ValueError, TypeError):
            return False
