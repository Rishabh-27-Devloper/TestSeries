"""
Core Data Models for CBT Examination System
Supports GATE, JEE, and extensible exam formats.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union, Dict, Any


class QuestionType(str, Enum):
    MCQ = "MCQ"   # Multiple Choice (Single correct option)
    MSQ = "MSQ"   # Multiple Select (One or more correct options)
    NAT = "NAT"   # Numerical Answer Type (Exact value or range)


class QuestionStatus(str, Enum):
    NOT_VISITED = "NOT_VISITED"                 # 1: Gray rounded rect
    NOT_ANSWERED = "NOT_ANSWERED"               # 2: Red/Orange shield
    ANSWERED = "ANSWERED"                       # 3: Green shield
    MARKED_FOR_REVIEW = "MARKED_FOR_REVIEW"     # 4: Purple circle
    ANSWERED_AND_MARKED = "ANSWERED_AND_MARKED" # 5: Purple circle with green dot (Evaluated)


@dataclass
class Option:
    id: str             # "A", "B", "C", "D"
    text: str           # Option text or markdown / HTML
    image: Optional[str] = None


@dataclass
class Question:
    question_id: int
    question_number: int                        # Display number within the paper (1..N)
    type: QuestionType                          # MCQ, MSQ, NAT
    section_id: str                             # "GA", "CS", etc.
    section_name: str                           # "General Aptitude", etc.
    question_text: str                          # Question description (supports text / html)
    positive_marks: float = 1.0                 # Positive marks (e.g. 1.0 or 2.0)
    negative_marks: float = 0.33                # Negative marks (e.g. 0.33, 0.67, 0.0)
    options: List[Option] = field(default_factory=list)
    image_url: Optional[str] = None             # Optional diagram / image path
    
    # Correct Answer definition
    # MCQ: "A" or "B"
    # MSQ: ["A", "C"]
    # NAT: 5.14 or {"min": 5.10, "max": 5.20} or "10"
    correct_answer: Any = None
    tolerance_min: Optional[float] = None       # For NAT range
    tolerance_max: Optional[float] = None       # For NAT range
    
    explanation: Optional[str] = None           # Detailed solution / explanation
    
    # Live exam state tracking
    status: QuestionStatus = QuestionStatus.NOT_VISITED
    candidate_answer: Any = None                # Student's response: "A", ["A","B"], or "12.5"
    time_spent_seconds: int = 0                 # Time spent on this question
    visited: bool = False

    def is_answered(self) -> bool:
        if self.candidate_answer is None:
            return False
        if isinstance(self.candidate_answer, str) and not self.candidate_answer.strip():
            return False
        if isinstance(self.candidate_answer, list) and len(self.candidate_answer) == 0:
            return False
        return True


@dataclass
class Section:
    section_id: str                             # e.g. "GA", "CS"
    section_name: str                           # "General Aptitude"
    questions: List[Question] = field(default_factory=list)
    cutoff_marks: Optional[float] = None


@dataclass
class ExamPaper:
    paper_id: str                               # Unique ID e.g. "GATE_CS_2024_MOCK1"
    title: str                                  # "GATE CS 2024 Full Length Mock 1"
    exam_type: str                              # "GATE", "JEE_MAIN", "NEET", etc.
    duration_minutes: int                       # 180 for GATE
    total_marks: float                          # 100
    category: str = "Mock Paper"                # "Mock Paper", "PYQ", "Topic-wise"
    year: Optional[int] = None                  # 2024
    description: Optional[str] = None           # Brief summary of paper
    sections: List[Section] = field(default_factory=list)
    instructions: Optional[List[str]] = None

    @property
    def all_questions(self) -> List[Question]:
        q_list = []
        for s in self.sections:
            q_list.extend(s.questions)
        return q_list

    @property
    def total_questions_count(self) -> int:
        return sum(len(s.questions) for s in self.sections)


@dataclass
class QuestionEvaluation:
    question_id: int
    question_number: int
    type: QuestionType
    section_name: str
    status: QuestionStatus
    candidate_answer: Any
    correct_answer: Any
    is_correct: bool
    is_attempted: bool
    marks_awarded: float
    max_marks: float
    penalty: float
    time_spent: int
    explanation: Optional[str] = None
    image_url: Optional[str] = None
    question_text: Optional[str] = None


@dataclass
class ExamResult:
    paper_id: str
    paper_title: str
    exam_type: str
    student_name: str
    roll_number: str
    timestamp: str
    duration_taken_seconds: int
    total_marks: float
    score_obtained: float
    positive_marks: float
    negative_marks: float
    total_questions: int
    attempted_count: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    accuracy_percentage: float
    percentage_score: float
    section_scores: Dict[str, Dict[str, Any]]
    evaluations: List[QuestionEvaluation]
