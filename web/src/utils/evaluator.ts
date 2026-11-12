import type { ExamPaper, ExamResult, QuestionEvaluation } from '../types';

export function evaluateExam(
  paper: ExamPaper,
  studentName: string,
  durationTakenSeconds: number
): ExamResult {
  const evaluations: QuestionEvaluation[] = [];
  const sectionScores: ExamResult['sectionScores'] = {};

  let totalScore = 0.0;
  let totalPositive = 0.0;
  let totalNegative = 0.0;
  let attemptedCount = 0;
  let correctCount = 0;
  let incorrectCount = 0;

  for (const section of paper.sections) {
    let sAttempted = 0;
    let sCorrect = 0;
    let sIncorrect = 0;
    let sScore = 0.0;
    const sMaxMarks = section.questions.reduce((sum, q) => sum + (q.positiveMarks || 1.0), 0);

    for (const q of section.questions) {
      const isAns = isQuestionAnswered(q.candidateAnswer);
      const isEvaluated =
        isAns &&
        q.status !== 'MARKED_FOR_REVIEW' &&
        q.status !== 'NOT_ANSWERED' &&
        q.status !== 'NOT_VISITED';

      let isCorrect = false;
      let marksAwarded = 0.0;
      let penalty = 0.0;

      if (isEvaluated) {
        sAttempted++;
        attemptedCount++;

        if (q.type === 'MCQ') {
          const evalMcq = evaluateMcq(q.candidateAnswer, q.correctAnswer, q.positiveMarks, q.negativeMarks);
          isCorrect = evalMcq.isCorrect;
          marksAwarded = evalMcq.marks;
          penalty = evalMcq.penalty;
        } else if (q.type === 'MSQ') {
          const evalMsq = evaluateMsq(q.candidateAnswer, q.correctAnswer, q.positiveMarks);
          isCorrect = evalMsq.isCorrect;
          marksAwarded = evalMsq.marks;
          penalty = 0.0;
        } else if (q.type === 'NAT') {
          const evalNat = evaluateNat(q.candidateAnswer, q.correctAnswer, q.toleranceMin, q.toleranceMax, q.positiveMarks);
          isCorrect = evalNat.isCorrect;
          marksAwarded = evalNat.marks;
          penalty = 0.0;
        }

        if (isCorrect) {
          sCorrect++;
          correctCount++;
          totalPositive += marksAwarded;
        } else {
          sIncorrect++;
          incorrectCount++;
          totalNegative += penalty;
        }

        sScore += marksAwarded;
        totalScore += marksAwarded;
      }

      evaluations.push({
        questionId: q.questionId,
        questionNumber: q.questionNumber,
        type: q.type,
        sectionName: q.sectionName,
        status: q.status,
        candidateAnswer: q.candidateAnswer ?? null,
        correctAnswer: q.correctAnswer,
        isCorrect,
        isAttempted: isEvaluated,
        marksAwarded: round2(marksAwarded),
        maxMarks: q.positiveMarks,
        penalty: round2(penalty),
        timeSpent: q.timeSpent || 0,
        explanation: '',
        imageUrl: q.imageUrl,
        questionText: q.questionText,
        isOutOfSyllabus: q.isOutOfSyllabus,
      });
    }

    sectionScores[section.sectionName] = {
      total_questions: section.questions.length,
      attempted: sAttempted,
      correct: sCorrect,
      incorrect: sIncorrect,
      score: round2(sScore),
      max_marks: round2(sMaxMarks),
    };
  }

  const unattemptedCount = Math.max(0, evaluations.length - attemptedCount);
  const accuracy = attemptedCount > 0 ? round2((correctCount / attemptedCount) * 100) : 0.0;
  const percentage = paper.totalMarks > 0 ? round2((totalScore / paper.totalMarks) * 100) : 0.0;

  const now = new Date();
  const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(
    now.getDate()
  ).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(
    2,
    '0'
  )}:${String(now.getSeconds()).padStart(2, '0')}`;

  return {
    paperId: paper.paperId,
    paperTitle: paper.title,
    examType: paper.examType || 'GATE',
    studentName: studentName || 'Candidate',
    timestamp,
    durationTakenSeconds,
    totalMarks: round2(paper.totalMarks),
    scoreObtained: round2(totalScore),
    positiveMarks: round2(totalPositive),
    negativeMarks: round2(totalNegative),
    totalQuestions: evaluations.length,
    attemptedCount,
    correctCount,
    incorrectCount,
    unattemptedCount,
    accuracyPercentage: accuracy,
    percentageScore: percentage,
    sectionScores,
    evaluations,
  };
}

export function isQuestionAnswered(answer: any): boolean {
  if (answer === null || answer === undefined) return false;
  if (typeof answer === 'string') return answer.trim().length > 0;
  if (Array.isArray(answer)) return answer.length > 0;
  if (typeof answer === 'number') return !isNaN(answer);
  return false;
}

function evaluateMcq(
  cand: any,
  corr: any,
  posMarks: number,
  negMarks: number
): { isCorrect: boolean; marks: number; penalty: number } {
  const cStr = String(cand || '').trim().toUpperCase();
  const keyStr = String(corr || '').trim().toUpperCase();

  if (keyStr === 'MTA' || keyStr.includes('MTA')) {
    return { isCorrect: true, marks: posMarks, penalty: 0 };
  }

  // Check tokenized match if multiple valid choices allowed (e.g. "A; B")
  const validKeys = keyStr.split(/[,;\s/]+/).map((k) => k.trim().toUpperCase());
  if (validKeys.includes(cStr)) {
    return { isCorrect: true, marks: posMarks, penalty: 0 };
  }

  return { isCorrect: false, marks: -negMarks, penalty: negMarks };
}

function evaluateMsq(
  cand: any,
  corr: any,
  posMarks: number
): { isCorrect: boolean; marks: number } {
  let cList: string[] = [];
  if (Array.isArray(cand)) {
    cList = cand.map((x) => String(x).trim().toUpperCase()).sort();
  } else if (typeof cand === 'string') {
    cList = [cand.trim().toUpperCase()];
  }

  let kList: string[] = [];
  if (Array.isArray(corr)) {
    kList = corr.map((x) => String(x).trim().toUpperCase()).sort();
  } else if (typeof corr === 'string') {
    const raw = corr.trim().toUpperCase();
    if (raw === 'MTA' || raw.includes('MTA')) {
      return { isCorrect: true, marks: posMarks };
    }
    kList = raw.split(/[,;\s]+/).map((x) => x.trim().toUpperCase()).sort();
  }

  const isMatch = cList.length > 0 && cList.length === kList.length && cList.every((v, i) => v === kList[i]);
  return { isCorrect: isMatch, marks: isMatch ? posMarks : 0 };
}

function evaluateNat(
  cand: any,
  corr: any,
  tMin?: number | null,
  tMax?: number | null,
  posMarks = 1.0
): { isCorrect: boolean; marks: number } {
  const cVal = parseFloat(String(cand || '').trim());
  if (isNaN(cVal)) {
    return { isCorrect: false, marks: 0 };
  }

  if (tMin !== undefined && tMin !== null && tMax !== undefined && tMax !== null) {
    if (cVal >= tMin - 1e-4 && cVal <= tMax + 1e-4) {
      return { isCorrect: true, marks: posMarks };
    }
  }

  const kVal = parseFloat(String(corr || '').trim());
  if (!isNaN(kVal)) {
    if (Math.abs(cVal - kVal) <= 0.05) {
      return { isCorrect: true, marks: posMarks };
    }
  }

  return { isCorrect: false, marks: 0 };
}

function round2(num: number): number {
  return Math.round((num + Number.EPSILON) * 100) / 100;
}
