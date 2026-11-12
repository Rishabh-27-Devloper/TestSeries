"""
Storage and Paper Inventory Manager for CBT Exam.
Handles loading JSON exam papers, saving student attempts, and caching statistics.
"""

import os
import json
import glob
from typing import List, Optional, Dict, Any
from core.models import (
    ExamPaper, Section, Question, Option, 
    QuestionType, QuestionStatus, ExamResult, QuestionEvaluation
)


class StorageManager:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Default to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.papers_dir = os.path.join(base_dir, "data", "papers")
        self.attempts_dir = os.path.join(base_dir, "data", "attempts")
        
        os.makedirs(self.papers_dir, exist_ok=True)
        os.makedirs(self.attempts_dir, exist_ok=True)

    def load_all_papers(self, exam_type: Optional[str] = None) -> List[ExamPaper]:
        """Loads all available exam papers from the papers directory."""
        papers: List[ExamPaper] = []
        json_files = glob.glob(os.path.join(self.papers_dir, "**", "*.json"), recursive=True)
        
        for file_path in json_files:
            try:
                paper = self.load_paper_from_file(file_path)
                if paper:
                    if exam_type is None or paper.exam_type.upper() == exam_type.upper():
                        papers.append(paper)
            except Exception as e:
                print(f"Error loading paper from {file_path}: {e}")
                
        return papers

    def load_paper_from_file(self, file_path: str) -> Optional[ExamPaper]:
        """Parses a JSON file into an ExamPaper instance."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        paper_id = data.get("paperId", os.path.splitext(os.path.basename(file_path))[0])
        title = data.get("title", "Exam Paper")
        exam_type = data.get("examType", "GATE")
        duration_mins = int(data.get("durationMinutes", 180))
        total_marks = float(data.get("totalMarks", 100))
        category = data.get("category", "Mock Paper")
        year = data.get("year")
        description = data.get("description", "")
        instructions = data.get("instructions", [])
        is_oos_paper = bool(data.get("isOutOfSyllabus") or data.get("is_out_of_syllabus", False))
        subject = data.get("subject")
        chapter = data.get("chapter")
        
        raw_sections = data.get("sections", [])
        sections: List[Section] = []
        global_q_num = 1
        
        for sec_data in raw_sections:
            sec_id = sec_data.get("sectionId", f"SEC_{len(sections)+1}")
            sec_name = sec_data.get("sectionName", f"Section {len(sections)+1}")
            cutoff = sec_data.get("cutoffMarks")
            
            questions: List[Question] = []
            for q_data in sec_data.get("questions", []):
                q_id = int(q_data.get("questionId", global_q_num))
                q_type_str = q_data.get("type", "MCQ").upper()
                try:
                    q_type = QuestionType(q_type_str)
                except ValueError:
                    q_type = QuestionType.MCQ
                    
                q_text = q_data.get("questionText", "")
                pos_marks = float(q_data.get("positiveMarks", q_data.get("positive marks", 1.0)))
                neg_marks = float(q_data.get("negativeMarks", q_data.get("negative marks", 0.33)))
                # Question diagram / image field detection
                image_url = (
                    q_data.get("imageUrl") or
                    q_data.get("ImageURL") or
                    q_data.get("image") or
                    q_data.get("Image") or
                    q_data.get("diagram") or
                    q_data.get("Diagram") or
                    q_data.get("questionImage") or
                    q_data.get("question_image")
                )
                
                # Resolve relative image paths against the JSON file's directory
                if image_url and not str(image_url).startswith("data:image"):
                    if not os.path.isabs(image_url):
                        candidate_path = os.path.join(os.path.dirname(file_path), image_url)
                        if os.path.exists(candidate_path):
                            image_url = candidate_path

                corr_ans = q_data.get("correctAnswer", q_data.get("correct_answer"))
                tol_min = q_data.get("toleranceMin")
                tol_max = q_data.get("toleranceMax")
                explanation = q_data.get("explanation", "")
                q_oos = bool(q_data.get("isOutOfSyllabus") or q_data.get("is_out_of_syllabus", False) or is_oos_paper)
                
                # Options for MCQ/MSQ
                options: List[Option] = []
                for opt_data in q_data.get("options", []):
                    if isinstance(opt_data, dict):
                        opt_img = (
                            opt_data.get("image") or
                            opt_data.get("imageUrl") or
                            opt_data.get("ImageURL") or
                            opt_data.get("diagram")
                        )
                        if opt_img and not str(opt_img).startswith("data:image"):
                            if not os.path.isabs(opt_img):
                                c_path = os.path.join(os.path.dirname(file_path), opt_img)
                                if os.path.exists(c_path):
                                    opt_img = c_path

                        options.append(Option(
                            id=opt_data.get("id", ""),
                            text=opt_data.get("text", ""),
                            image=opt_img
                        ))
                    elif isinstance(opt_data, str):
                        # Simple string option e.g. "Option A"
                        opt_id = chr(65 + len(options))
                        options.append(Option(id=opt_id, text=opt_data))
                        
                question = Question(
                    question_id=q_id,
                    question_number=global_q_num,
                    type=q_type,
                    section_id=sec_id,
                    section_name=sec_name,
                    question_text=q_text,
                    positive_marks=pos_marks,
                    negative_marks=neg_marks,
                    options=options,
                    image_url=image_url,
                    correct_answer=corr_ans,
                    tolerance_min=tol_min,
                    tolerance_max=tol_max,
                    explanation=explanation,
                    status=QuestionStatus.NOT_VISITED,
                    is_out_of_syllabus=q_oos
                )
                questions.append(question)
                global_q_num += 1
                
            sections.append(Section(
                section_id=sec_id,
                section_name=sec_name,
                questions=questions,
                cutoff_marks=cutoff
            ))
            
        return ExamPaper(
            paper_id=paper_id,
            title=title,
            exam_type=exam_type,
            duration_minutes=duration_mins,
            total_marks=total_marks,
            category=category,
            year=year,
            description=description,
            sections=sections,
            instructions=instructions,
            is_out_of_syllabus=is_oos_paper,
            subject=subject,
            chapter=chapter
        )

    def save_attempt(self, result: ExamResult) -> str:
        """Saves a student's completed exam result to disk as JSON."""
        timestamp_clean = result.timestamp.replace(" ", "_").replace(":", "-")
        filename = f"{result.paper_id}_{result.roll_number}_{timestamp_clean}.json"
        target_path = os.path.join(self.attempts_dir, filename)
        
        attempt_data = {
            "paperId": result.paper_id,
            "paperTitle": result.paper_title,
            "examType": result.exam_type,
            "studentName": result.student_name,
            "rollNumber": result.roll_number,
            "timestamp": result.timestamp,
            "durationTakenSeconds": result.duration_taken_seconds,
            "totalMarks": result.total_marks,
            "scoreObtained": result.score_obtained,
            "positiveMarks": result.positive_marks,
            "negativeMarks": result.negative_marks,
            "totalQuestions": result.total_questions,
            "attemptedCount": result.attempted_count,
            "correctCount": result.correct_count,
            "incorrectCount": result.incorrect_count,
            "unattemptedCount": result.unattempted_count,
            "accuracyPercentage": result.accuracy_percentage,
            "percentageScore": result.percentage_score,
            "sectionScores": result.section_scores,
            "evaluations": [
                {
                    "questionId": ev.question_id,
                    "questionNumber": ev.question_number,
                    "type": ev.type.value,
                    "sectionName": ev.section_name,
                    "status": ev.status.value,
                    "candidateAnswer": ev.candidate_answer,
                    "correctAnswer": ev.correct_answer,
                    "isCorrect": ev.is_correct,
                    "isAttempted": ev.is_attempted,
                    "marksAwarded": ev.marks_awarded,
                    "maxMarks": ev.max_marks,
                    "penalty": ev.penalty,
                    "timeSpent": ev.time_spent,
                    "explanation": ev.explanation,
                    "imageUrl": ev.image_url,
                    "questionText": ev.question_text,
                    "isOutOfSyllabus": ev.is_out_of_syllabus
                }
                for ev in result.evaluations
            ]
        }
        
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(attempt_data, f, indent=2, ensure_ascii=False)
            
        return target_path

    def load_all_attempts(self, exam_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Loads summary of past exam attempts for student dashboard."""
        attempts = []
        files = glob.glob(os.path.join(self.attempts_dir, "*.json"))
        
        for fp in sorted(files, key=os.path.getmtime, reverse=True):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if exam_type is None or data.get("examType", "").upper() == exam_type.upper():
                        data["_filePath"] = fp
                        attempts.append(data)
            except Exception as e:
                print(f"Error loading attempt from {fp}: {e}")
                
        return attempts

    def get_user_profile_path(self) -> str:
        return os.path.join(self.base_dir, "data", "user_profile.json")

    def load_user_profile(self) -> Dict[str, Any]:
        """Loads persistent user profile, or returns standard defaults."""
        p = self.get_user_profile_path()
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                print(f"Error loading user profile: {e}")
        return {
            "name": "Candidate",
            "roll_number": "GATE25-EC001",
            "phone_number": "",
            "category": "General",
            "target_year": "2025"
        }

    def save_user_profile(self, profile: Dict[str, Any]) -> str:
        """Persists candidate's profile to disk."""
        p = self.get_user_profile_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return p

    def load_attempt_result(self, file_path: str) -> Optional[ExamResult]:
        """Reconstructs an ExamResult instance from an attempt JSON file."""
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                d = json.load(f)

            evals = []
            for ev_d in d.get("evaluations", []):
                q_type = QuestionType.MCQ
                try:
                    q_type = QuestionType(ev_d.get("type", "MCQ"))
                except ValueError:
                    pass

                status = QuestionStatus.NOT_VISITED
                try:
                    status = QuestionStatus(ev_d.get("status", "NOT_VISITED"))
                except ValueError:
                    pass

                evals.append(QuestionEvaluation(
                    question_id=int(ev_d.get("questionId", 0)),
                    question_number=int(ev_d.get("questionNumber", 0)),
                    type=q_type,
                    section_name=ev_d.get("sectionName", "General"),
                    status=status,
                    candidate_answer=ev_d.get("candidateAnswer"),
                    correct_answer=ev_d.get("correctAnswer"),
                    is_correct=bool(ev_d.get("isCorrect", False)),
                    is_attempted=bool(ev_d.get("isAttempted", False)),
                    marks_awarded=float(ev_d.get("marksAwarded", 0.0)),
                    max_marks=float(ev_d.get("maxMarks", 1.0)),
                    penalty=float(ev_d.get("penalty", 0.0)),
                    time_spent=int(ev_d.get("timeSpent", 0)),
                    explanation=ev_d.get("explanation"),
                    image_url=ev_d.get("imageUrl"),
                    question_text=ev_d.get("questionText"),
                    is_out_of_syllabus=bool(ev_d.get("isOutOfSyllabus", False))
                ))

            return ExamResult(
                paper_id=d.get("paperId", ""),
                paper_title=d.get("paperTitle", "Exam Attempt"),
                exam_type=d.get("examType", "GATE"),
                student_name=d.get("studentName", "Candidate"),
                roll_number=d.get("rollNumber", "GATE25-EC001"),
                timestamp=d.get("timestamp", ""),
                duration_taken_seconds=int(d.get("durationTakenSeconds", 0)),
                total_marks=float(d.get("totalMarks", 100.0)),
                score_obtained=float(d.get("scoreObtained", 0.0)),
                positive_marks=float(d.get("positiveMarks", 0.0)),
                negative_marks=float(d.get("negativeMarks", 0.0)),
                total_questions=int(d.get("totalQuestions", len(evals))),
                attempted_count=int(d.get("attemptedCount", 0)),
                correct_count=int(d.get("correctCount", 0)),
                incorrect_count=int(d.get("incorrectCount", 0)),
                unattempted_count=int(d.get("unattemptedCount", 0)),
                accuracy_percentage=float(d.get("accuracyPercentage", 0.0)),
                percentage_score=float(d.get("percentageScore", 0.0)),
                section_scores=d.get("sectionScores", {}),
                evaluations=evals
            )
        except Exception as e:
            print(f"Error loading attempt result from {file_path}: {e}")
            return None
