export type QuestionType = 'MCQ' | 'MSQ' | 'NAT';

export type QuestionStatus =
  | 'NOT_VISITED'
  | 'NOT_ANSWERED'
  | 'ANSWERED'
  | 'MARKED_FOR_REVIEW'
  | 'ANSWERED_AND_MARKED';

export interface Option {
  id: string;
  text: string;
  image?: string;
}

export interface Question {
  questionId: number;
  questionNumber: number;
  sectionId: string;
  sectionName: string;
  type: QuestionType;
  questionText: string;
  imageUrl?: string;
  positiveMarks: number;
  negativeMarks: number;
  correctAnswer: string | string[] | number | null;
  toleranceMin?: number | null;
  toleranceMax?: number | null;
  options?: Option[];
  candidateAnswer?: any;
  status: QuestionStatus;
  visited?: boolean;
  timeSpent?: number;
  isOutOfSyllabus?: boolean;
}

export interface Section {
  sectionId: string;
  sectionName: string;
  totalQuestions: number;
  cutoffMarks?: number;
  questions: Question[];
  isOutOfSyllabus?: boolean;
}

export interface ExamPaper {
  paperId: string;
  title: string;
  category: string;
  year?: number | null;
  examType: string;
  durationMinutes: number;
  totalMarks: number;
  description?: string;
  instructions?: string[];
  sections: Section[];
  isOutOfSyllabus?: boolean;
  subject?: string;
  chapter?: string;
}

export interface PaperIndexItem {
  paperId: string;
  title: string;
  category: string;
  year?: number | null;
  examType: string;
  durationMinutes: number;
  totalMarks: number;
  totalQuestions: number;
  chapter: string;
  subject: string;
  sectionsCount: number;
  description?: string;
  jsonPath: string;
  isOutOfSyllabus?: boolean;
}

export interface QuestionEvaluation {
  questionId: number;
  questionNumber: number;
  type: QuestionType;
  sectionName: string;
  status: QuestionStatus;
  candidateAnswer: any;
  correctAnswer: any;
  isCorrect: boolean;
  isAttempted: boolean;
  marksAwarded: number;
  maxMarks: number;
  penalty: number;
  timeSpent: number;
  explanation?: string;
  imageUrl?: string;
  questionText?: string;
  isOutOfSyllabus?: boolean;
}

export interface ExamResult {
  paperId: string;
  paperTitle: string;
  examType: string;
  studentName: string;
  timestamp: string;
  durationTakenSeconds: number;
  totalMarks: number;
  scoreObtained: number;
  positiveMarks: number;
  negativeMarks: number;
  totalQuestions: number;
  attemptedCount: number;
  correctCount: number;
  incorrectCount: number;
  unattemptedCount: number;
  accuracyPercentage: number;
  percentageScore: number;
  sectionScores: Record<
    string,
    {
      total_questions: number;
      attempted: number;
      correct: number;
      incorrect: number;
      score: number;
      max_marks: number;
    }
  >;
  evaluations: QuestionEvaluation[];
  _filePath?: string;
}

export interface UserProfile {
  name: string;
  phoneNumber?: string;
  email?: string;
  targetYear: string;
  branch: string;
}
