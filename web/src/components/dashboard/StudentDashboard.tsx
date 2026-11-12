import React, { useState, useEffect, useMemo } from 'react';
import confetti from 'canvas-confetti';
import {
  Trophy,
  Award,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  ArrowLeft,
  RotateCcw,
  BookOpen,
  Filter,
  TrendingUp,
  ZoomIn,
  Target,
  AlertTriangle,
  Trash2,
  GraduationCap,
  Stethoscope,
} from 'lucide-react';
import type { ExamResult, QuestionEvaluation } from '../../types';
import {
  getAllAttempts,
  getUserProfile,
  clearUserAttempts,
  deleteSingleAttempt,
  resolveImageUrl,
  getFallbackImageUrl,
} from '../../utils/storage';
import { ImageZoomModal } from '../modals/ImageZoomModal';

interface StudentDashboardProps {
  currentResult: ExamResult;
  selectedExam?: 'GATE' | 'NEET' | string;
  onRetakeExam: (paperId: string) => void;
  onBackToInventory: () => void;
  onLoadPastAttempt?: (attempt: ExamResult) => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  currentResult: initialResult,
  selectedExam,
  onRetakeExam,
  onBackToInventory,
  onLoadPastAttempt,
}) => {
  const profile = getUserProfile();
  const [activeTab, setActiveTab] = useState<'SCORECARD' | 'SOLUTIONS' | 'TRENDS'>('SCORECARD');
  const [activeResult, setActiveResult] = useState<ExamResult>(initialResult);
  const [solutionFilter, setSolutionFilter] = useState<'ALL' | 'CORRECT' | 'INCORRECT' | 'UNATTEMPTED'>('ALL');
  const [zoomImage, setZoomImage] = useState<string | null>(null);

  const [historyExamFilter, setHistoryExamFilter] = useState<'GATE' | 'NEET'>(() => {
    const et = (initialResult?.examType || selectedExam || 'GATE').toUpperCase();
    return et === 'NEET' || et === 'NEET UG' ? 'NEET' : 'GATE';
  });

  const [allAttempts, setAllAttempts] = useState<ExamResult[]>(() => getAllAttempts());

  const gateAttempts = useMemo(() => {
    return allAttempts.filter((a) => (a.examType || '').toUpperCase() === 'GATE');
  }, [allAttempts]);

  const neetAttempts = useMemo(() => {
    return allAttempts.filter((a) => {
      const et = (a.examType || '').toUpperCase();
      return et === 'NEET' || et === 'NEET UG';
    });
  }, [allAttempts]);

  const currentExamAttempts = historyExamFilter === 'NEET' ? neetAttempts : gateAttempts;

  const handleClearHistory = () => {
    const examLabel = historyExamFilter === 'NEET' ? 'NEET UG' : 'GATE EC';
    if (confirm(`Are you sure you want to clear your ${examLabel} test attempt history? This will only remove your ${examLabel} attempts.`)) {
      clearUserAttempts(historyExamFilter);
      const remaining = getAllAttempts();
      setAllAttempts(remaining);
    }
  };

  const handleDeleteSingle = (att: ExamResult) => {
    if (
      confirm(
        `Are you sure you want to delete the attempt for "${att.paperTitle}" taken on ${att.timestamp}?`
      )
    ) {
      deleteSingleAttempt(att.timestamp, att.paperId);
      const remaining = getAllAttempts();
      setAllAttempts(remaining);
      if (remaining.length > 0) {
        if (activeResult.timestamp === att.timestamp && activeResult.paperId === att.paperId) {
          setActiveResult(remaining[0]);
        }
      } else {
        onBackToInventory();
      }
    }
  };

  // Launch confetti if percentage >= 50%
  useEffect(() => {
    if (activeResult.percentageScore >= 50) {
      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
        });
      } catch (e) {
        // Confetti fallback
      }
    }
  }, [activeResult]);

  // Sync if initialResult prop changes
  useEffect(() => {
    setActiveResult(initialResult);
  }, [initialResult]);

  // Filter solutions
  const filteredQuestions = activeResult.evaluations.filter((q: QuestionEvaluation) => {
    if (solutionFilter === 'CORRECT') return q.isCorrect === true;
    if (solutionFilter === 'INCORRECT') return q.isAttempted && !q.isCorrect;
    if (solutionFilter === 'UNATTEMPTED') return !q.isAttempted;
    return true;
  });

  // Calculate speed per question
  const avgSpeedSec =
    activeResult.attemptedCount > 0
      ? Math.round(activeResult.durationTakenSeconds / activeResult.attemptedCount)
      : 0;

  // Format seconds to mm:ss
  const formatSec = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}m ${s}s`;
  };

  // Performance badge tier
  const getTier = (pct: number) => {
    if (pct >= 75) return { label: 'Outstanding / GATE AIR < 100 Potential', color: 'from-emerald-600 to-teal-700', bg: 'bg-emerald-50 text-emerald-800' };
    if (pct >= 50) return { label: 'Qualified / Strong Technical Competence', color: 'from-blue-600 to-indigo-700', bg: 'bg-blue-50 text-blue-800' };
    if (pct >= 30) return { label: 'Moderate / Needs Targeted Revision', color: 'from-amber-600 to-orange-700', bg: 'bg-amber-50 text-amber-800' };
    return { label: 'Needs Comprehensive Concept Rebuilding', color: 'from-rose-600 to-red-700', bg: 'bg-rose-50 text-rose-800' };
  };

  const tier = getTier(activeResult.percentageScore);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans overflow-y-auto">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToInventory}
              className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition"
              title="Return to Paper Inventory"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-slate-900 text-base sm:text-lg">Student Performance Dashboard</h1>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  Evaluated Result
                </span>
              </div>
              <p className="text-xs text-slate-500 truncate max-w-sm sm:max-w-xl">
                {activeResult.paperTitle} • {new Date(activeResult.timestamp).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onRetakeExam(activeResult.paperId)}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#1a56a5] hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
            >
              <RotateCcw size={14} />
              <span className="hidden sm:inline">Retake This Test</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-4 sm:space-x-8 border-t border-slate-100 overflow-x-auto no-scrollbar">
          <button
            onClick={() => setActiveTab('SCORECARD')}
            className={`py-3 text-xs sm:text-sm font-semibold border-b-2 flex items-center gap-2 transition whitespace-nowrap ${
              activeTab === 'SCORECARD'
                ? 'border-[#1a56a5] text-[#1a56a5]'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Trophy size={16} />
            Scorecard &amp; Analytics
          </button>

          <button
            onClick={() => setActiveTab('SOLUTIONS')}
            className={`py-3 text-xs sm:text-sm font-semibold border-b-2 flex items-center gap-2 transition whitespace-nowrap ${
              activeTab === 'SOLUTIONS'
                ? 'border-[#1a56a5] text-[#1a56a5]'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <BookOpen size={16} />
            Question Solutions ({activeResult.evaluations.length})
          </button>

          <button
            onClick={() => setActiveTab('TRENDS')}
            className={`py-3 text-xs sm:text-sm font-semibold border-b-2 flex items-center gap-2 transition whitespace-nowrap ${
              activeTab === 'TRENDS'
                ? 'border-[#1a56a5] text-[#1a56a5]'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <TrendingUp size={16} />
            Past Attempts ({allAttempts.length})
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 space-y-6">
        {/* ========================================================================= */}
        {/* TAB 1: SCORECARD & ANALYTICS */}
        {/* ========================================================================= */}
        {activeTab === 'SCORECARD' && (
          <div className="space-y-6">
            {/* Hero Scorecard Banner */}
            <div
              className={`rounded-xl bg-gradient-to-r ${tier.color} text-white p-5 sm:p-8 shadow-md relative overflow-hidden`}
            >
              <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div className="space-y-2">
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-xs text-xs font-semibold">
                    <Award size={14} /> {tier.label}
                  </div>
                  <h2 className="text-xl sm:text-2xl md:text-3xl font-black">{activeResult.paperTitle}</h2>
                  <p className="text-xs sm:text-sm text-blue-100 max-w-xl">
                    Official GATE Scoring Scheme applied. Evaluated on{' '}
                    {new Date(activeResult.timestamp).toLocaleString()}.
                  </p>
                </div>

                <div className="w-full md:w-auto flex items-center justify-around sm:justify-start gap-4 sm:gap-6 bg-white/10 backdrop-blur-sm p-4 rounded-xl border border-white/20">
                  <div className="text-center">
                    <div className="text-2xl sm:text-3xl md:text-4xl font-black">
                      {activeResult.scoreObtained.toFixed(2)}
                    </div>
                    <div className="text-[10px] sm:text-[11px] uppercase tracking-wider text-blue-200">
                      Score / {activeResult.totalMarks}
                    </div>
                  </div>
                  <div className="h-10 w-px bg-white/30" />
                  <div className="text-center">
                    <div className="text-2xl sm:text-3xl md:text-4xl font-black">
                      {activeResult.percentageScore.toFixed(1)}%
                    </div>
                    <div className="text-[10px] sm:text-[11px] uppercase tracking-wider text-blue-200">Marks %</div>
                  </div>
                  <div className="h-10 w-px bg-white/30" />
                  <div className="text-center">
                    <div className="text-2xl sm:text-3xl md:text-4xl font-black">
                      {activeResult.accuracyPercentage.toFixed(0)}%
                    </div>
                    <div className="text-[10px] sm:text-[11px] uppercase tracking-wider text-blue-200">Accuracy</div>
                  </div>
                </div>
              </div>
            </div>

            {/* KPI Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-1">
                  <span className="text-xs font-semibold">Attempted</span>
                  <Target size={16} className="text-blue-600" />
                </div>
                <div className="text-2xl font-black text-slate-900">
                  {activeResult.attemptedCount}{' '}
                  <span className="text-xs font-normal text-slate-500">
                    / {activeResult.totalQuestions}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  {((activeResult.attemptedCount / activeResult.totalQuestions) * 100).toFixed(0)}% attempted
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-1">
                  <span className="text-xs font-semibold">Correct</span>
                  <CheckCircle2 size={16} className="text-emerald-600" />
                </div>
                <div className="text-2xl font-black text-emerald-700">
                  {activeResult.correctCount}
                </div>
                <div className="text-[11px] text-emerald-600 mt-1 font-medium">
                  +{activeResult.positiveMarks.toFixed(2)} pts earned
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-1">
                  <span className="text-xs font-semibold">Incorrect</span>
                  <XCircle size={16} className="text-rose-600" />
                </div>
                <div className="text-2xl font-black text-rose-700">
                  {activeResult.incorrectCount}
                </div>
                <div className="text-[11px] text-rose-600 mt-1 font-medium">
                  -{activeResult.negativeMarks.toFixed(2)} pts penalty
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-1">
                  <span className="text-xs font-semibold">Unattempted</span>
                  <HelpCircle size={16} className="text-slate-400" />
                </div>
                <div className="text-2xl font-black text-slate-700">
                  {activeResult.unattemptedCount}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">0 penalties</div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-1">
                  <span className="text-xs font-semibold">Time Spent</span>
                  <Clock size={16} className="text-indigo-600" />
                </div>
                <div className="text-2xl font-black text-slate-900">
                  {Math.round(activeResult.durationTakenSeconds / 60)}{' '}
                  <span className="text-xs font-normal text-slate-500">mins</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  {formatSec(activeResult.durationTakenSeconds)} total
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-1">
                  <span className="text-xs font-semibold">Avg Speed</span>
                  <TrendingUp size={16} className="text-amber-600" />
                </div>
                <div className="text-2xl font-black text-slate-900">
                  {avgSpeedSec}{' '}
                  <span className="text-xs font-normal text-slate-500">sec</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Per attempted Q</div>
              </div>
            </div>

            {/* Section-wise Breakdown Table */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <h3 className="font-bold text-slate-900 text-sm">Section-wise Performance Breakdown</h3>
                <span className="text-xs text-slate-500">
                  Detailed analysis across paper sections
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 uppercase font-semibold">
                    <tr>
                      <th className="px-6 py-3">Section Name</th>
                      <th className="px-4 py-3 text-center">Total Qs</th>
                      <th className="px-4 py-3 text-center">Attempted</th>
                      <th className="px-4 py-3 text-center text-emerald-700">Correct</th>
                      <th className="px-4 py-3 text-center text-rose-700">Incorrect</th>
                      <th className="px-4 py-3 text-center">Accuracy %</th>
                      <th className="px-6 py-3 text-right">Score Earned</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                    {Object.entries(activeResult.sectionScores).map(([secName, sec]) => {
                      const secAcc = sec.attempted > 0 ? (sec.correct / sec.attempted) * 100 : 0;
                      return (
                        <tr key={secName} className="hover:bg-slate-50/80 transition">
                          <td className="px-6 py-3.5 font-bold text-slate-900">{secName}</td>
                          <td className="px-4 py-3.5 text-center text-slate-600">{sec.total_questions}</td>
                          <td className="px-4 py-3.5 text-center">{sec.attempted}</td>
                          <td className="px-4 py-3.5 text-center font-bold text-emerald-700">
                            {sec.correct}
                          </td>
                          <td className="px-4 py-3.5 text-center font-bold text-rose-700">
                            {sec.incorrect}
                          </td>
                          <td className="px-4 py-3.5 text-center">
                            <span
                              className={`px-2 py-0.5 rounded font-bold ${
                                secAcc >= 70
                                ? 'bg-emerald-100 text-emerald-800'
                                : secAcc >= 40
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                            >
                              {secAcc.toFixed(0)}%
                            </span>
                          </td>
                          <td className="px-6 py-3.5 text-right font-black text-slate-900">
                            {sec.score.toFixed(2)}{' '}
                            <span className="text-[11px] text-slate-400 font-normal">
                              / {sec.max_marks}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Strategic Coaching Insights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
                  <CheckCircle2 size={18} className="text-emerald-600" />
                  Key Strengths
                </div>
                <p className="text-xs text-emerald-800 leading-relaxed">
                  You secured <strong>+{activeResult.positiveMarks.toFixed(2)} marks</strong> with{' '}
                  <strong>{activeResult.accuracyPercentage.toFixed(0)}% accuracy</strong> across attempted
                  questions.
                  {activeResult.accuracyPercentage >= 80
                    ? ' Exceptional accuracy rate; prioritize speed training while maintaining this precision.'
                    : ' Solid performance in core sections. Consistent revision will eliminate edge inaccuracies.'}
                </p>
              </div>

              <div className="p-5 bg-amber-50 border border-amber-200 rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                  <AlertTriangle size={18} className="text-amber-600" />
                  Negative Penalty Audit
                </div>
                <p className="text-xs text-amber-800 leading-relaxed">
                  Negative markings cost you{' '}
                  <strong className="text-rose-700">
                    -{activeResult.negativeMarks.toFixed(2)} marks
                  </strong>{' '}
                  from {activeResult.incorrectCount} incorrect answers.
                  {activeResult.examType === 'NEET'
                    ? ' In NEET UG (+4.0 / -1.0), each negative mark costs hundreds of state ranks. Eliminating speculative guesses is key to crossing 650+.'
                    : ' In GATE, avoiding 3 uncertain guesses often boosts AIR rank by 500+ positions.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: QUESTION-BY-QUESTION SOLUTIONS */}
        {/* ========================================================================= */}
        {activeTab === 'SOLUTIONS' && (
          <div className="space-y-6">
            {/* Filter Bar */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 flex-wrap text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1">
                  <Filter size={14} /> Filter Questions:
                </span>
                <button
                  onClick={() => setSolutionFilter('ALL')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                    solutionFilter === 'ALL'
                      ? 'bg-[#1a56a5] text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  All ({activeResult.evaluations.length})
                </button>
                <button
                  onClick={() => setSolutionFilter('CORRECT')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                    solutionFilter === 'CORRECT'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                  }`}
                >
                  Correct ({activeResult.correctCount})
                </button>
                <button
                  onClick={() => setSolutionFilter('INCORRECT')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                    solutionFilter === 'INCORRECT'
                      ? 'bg-rose-600 text-white'
                      : 'bg-rose-50 text-rose-800 hover:bg-rose-100'
                  }`}
                >
                  Incorrect ({activeResult.incorrectCount})
                </button>
                <button
                  onClick={() => setSolutionFilter('UNATTEMPTED')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                    solutionFilter === 'UNATTEMPTED'
                      ? 'bg-slate-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  Unattempted ({activeResult.unattemptedCount})
                </button>
              </div>

              <div className="text-xs text-slate-500">
                Showing {filteredQuestions.length} of {activeResult.evaluations.length} questions
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-4">
              {filteredQuestions.map((q: QuestionEvaluation) => {
                const imgSrc = q.imageUrl ? resolveImageUrl(q.imageUrl) : null;
                const isCorrect = q.isCorrect === true;
                const isIncorrect = q.isAttempted && !q.isCorrect;
                const isUnattempted = !q.isAttempted;

                return (
                  <div
                    key={q.questionId || q.questionNumber}
                    className={`bg-white rounded-xl border p-5 shadow-xs space-y-4 ${
                      isCorrect
                        ? 'border-emerald-300'
                        : isIncorrect
                        ? 'border-rose-300'
                        : 'border-slate-300'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between border-b pb-3">
                      <div className="flex items-center gap-2">
                        <span className="w-7 h-7 rounded bg-[#1a56a5] text-white font-bold flex items-center justify-center text-xs">
                          {q.questionNumber}
                        </span>
                        <span className="font-bold text-xs uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border">
                          {q.type}
                        </span>
                        <span className="text-xs text-slate-600">
                          Section: <strong>{q.sectionName}</strong>
                        </span>
                        {q.isOutOfSyllabus && (
                          <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded border border-amber-300">
                            ⚠️ Out of Syllabus
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3">
                        {isCorrect && (
                          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                            <CheckCircle2 size={13} /> +{q.marksAwarded} Marks (Correct)
                          </span>
                        )}
                        {isIncorrect && (
                          <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1">
                            <XCircle size={13} /> -{q.penalty.toFixed(2)} Marks (Incorrect)
                          </span>
                        )}
                        {isUnattempted && (
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                            Unattempted (0 Marks)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Question Image or Text */}
                    <div className="py-2 w-full space-y-2">
                      {imgSrc ? (
                        <div className="w-full block space-y-2">
                          <img
                            src={imgSrc}
                            alt={`Question ${q.questionNumber}`}
                            onError={(e) => {
                              const fb = getFallbackImageUrl(q.imageUrl);
                              if (fb && e.currentTarget.src !== fb) e.currentTarget.src = fb;
                            }}
                            className="w-full h-auto object-contain rounded border border-slate-200 bg-white shadow-xs block select-none pointer-events-none"
                          />
                          <div className="flex justify-end pt-1">
                            <button
                              type="button"
                              onClick={() => setZoomImage(imgSrc)}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-black text-white text-xs rounded-md shadow-sm transition font-medium"
                              title="Open full-screen diagram zoom modal"
                            >
                              <ZoomIn size={14} /> Zoom Image
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">{q.questionText}</p>
                      )}
                    </div>

                    {/* Response vs Answer Key Box */}
                    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-slate-500 font-semibold block mb-0.5">
                          Your Response:
                        </span>
                        <div className="font-bold text-sm">
                          {q.candidateAnswer !== null && q.candidateAnswer !== undefined ? (
                            <span
                              className={
                                isCorrect
                                  ? 'text-emerald-700 font-mono'
                                  : 'text-rose-700 font-mono line-through'
                              }
                            >
                              {Array.isArray(q.candidateAnswer)
                                ? q.candidateAnswer.join(', ')
                                : String(q.candidateAnswer)}
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">None (Unattempted)</span>
                          )}
                        </div>
                      </div>

                      <div>
                        <span className="text-slate-500 font-semibold block mb-0.5">
                          Official Answer Key:
                        </span>
                        <div className="font-mono font-bold text-emerald-800 text-sm">
                          {Array.isArray(q.correctAnswer)
                            ? q.correctAnswer.join(', ')
                            : String(q.correctAnswer)}
                        </div>
                      </div>
                    </div>

                    {/* Solution notes / explanation if present */}
                    {q.explanation && (
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-950 space-y-1">
                        <strong className="block font-semibold text-blue-900">
                          Solution Notes:
                        </strong>
                        <p className="leading-relaxed whitespace-pre-wrap">{q.explanation}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: PROGRESS TRENDS & PAST ATTEMPTS */}
        {/* ========================================================================= */}
        {activeTab === 'TRENDS' && (
          <div className="space-y-6">
            {/* Exam Separation Switcher */}
            <div className="flex items-center gap-2 p-1.5 bg-slate-200/70 rounded-2xl w-fit">
              <button
                onClick={() => setHistoryExamFilter('GATE')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
                  historyExamFilter === 'GATE'
                    ? 'bg-[#1a56a5] text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
                }`}
              >
                <GraduationCap size={15} />
                <span>GATE EC History ({gateAttempts.length})</span>
              </button>
              <button
                onClick={() => setHistoryExamFilter('NEET')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
                  historyExamFilter === 'NEET'
                    ? 'bg-teal-700 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
                }`}
              >
                <Stethoscope size={15} />
                <span>NEET UG History ({neetAttempts.length})</span>
              </button>
            </div>

            {/* Cumulative Stats for Current Exam Selection */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="text-xs font-semibold text-slate-500 uppercase">
                  {historyExamFilter === 'NEET' ? 'NEET Tests Taken' : 'GATE Tests Taken'}
                </div>
                <div className="text-3xl font-black text-slate-900 mt-1">{currentExamAttempts.length}</div>
                <div className="text-[11px] text-slate-400 mt-1">Recorded sessions</div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="text-xs font-semibold text-slate-500 uppercase">Average Marks %</div>
                <div className={`text-3xl font-black mt-1 ${historyExamFilter === 'NEET' ? 'text-teal-700' : 'text-[#1a56a5]'}`}>
                  {currentExamAttempts.length > 0
                    ? (
                        currentExamAttempts.reduce((s: number, a: ExamResult) => s + a.percentageScore, 0) /
                        currentExamAttempts.length
                      ).toFixed(1)
                    : 0}
                  %
                </div>
                <div className="text-[11px] text-slate-400 mt-1">In {historyExamFilter === 'NEET' ? 'NEET UG' : 'GATE EC'}</div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="text-xs font-semibold text-slate-500 uppercase">Highest Score</div>
                <div className="text-3xl font-black text-emerald-700 mt-1">
                  {currentExamAttempts.length > 0
                    ? Math.max(...currentExamAttempts.map((a: ExamResult) => a.scoreObtained)).toFixed(2)
                    : 0}
                </div>
                <div className="text-[11px] text-emerald-600 mt-1">Personal record</div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="text-xs font-semibold text-slate-500 uppercase">Total Practice</div>
                <div className="text-3xl font-black text-amber-600 mt-1">
                  {Math.round(
                    currentExamAttempts.reduce((s: number, a: ExamResult) => s + a.durationTakenSeconds, 0) /
                      60
                  )}{' '}
                  <span className="text-xs font-normal text-slate-500">mins</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1">Time spent in tests</div>
              </div>
            </div>

            {/* Past Attempts Table (Visible & Scrollable) */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                    <span>
                      {historyExamFilter === 'NEET' ? '🩺 NEET UG' : '🎓 GATE EC'} Attempt History for {profile.name}
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500">
                    {historyExamFilter === 'NEET' ? 'NEET UG (+4 / -1)' : 'GATE EC (+1/+2, -0.33/-0.67)'} test records stored securely in your browser's private local storage.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded ${
                    historyExamFilter === 'NEET' ? 'bg-teal-50 text-teal-800' : 'bg-blue-50 text-blue-800'
                  }`}>
                    {currentExamAttempts.length} Records
                  </span>
                  {currentExamAttempts.length > 0 && (
                    <button
                      onClick={handleClearHistory}
                      className="px-2.5 py-1 text-xs text-rose-600 hover:text-rose-800 hover:bg-rose-50 border border-rose-200 rounded transition font-medium"
                      title="Clear only your attempt history for this exam"
                    >
                      Clear {historyExamFilter === 'NEET' ? 'NEET' : 'GATE'} Log
                    </button>
                  )}
                </div>
              </div>

              {currentExamAttempts.length === 0 ? (
                <div className="p-12 text-center text-xs text-slate-500 space-y-2">
                  <div className="text-2xl">{historyExamFilter === 'NEET' ? '🩺' : '🎓'}</div>
                  <div className="font-semibold text-slate-700">
                    No {historyExamFilter === 'NEET' ? 'NEET UG' : 'GATE EC'} attempts recorded yet.
                  </div>
                  <p className="text-slate-400 max-w-sm mx-auto">
                    Start a test in the {historyExamFilter === 'NEET' ? 'NEET UG' : 'GATE EC'} portal to review your scorecard, solutions, and accuracy analytics here.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b sticky top-0 z-10">
                      <tr>
                        <th className="px-6 py-3">Date &amp; Time</th>
                        <th className="px-6 py-3">Exam Name</th>
                        <th className="px-4 py-3 text-center">Score / Max</th>
                        <th className="px-4 py-3 text-center">Marks %</th>
                        <th className="px-4 py-3 text-center">Accuracy %</th>
                        <th className="px-4 py-3 text-center">Time Spent</th>
                        <th className="px-6 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                      {currentExamAttempts.map((att: ExamResult) => {
                        const isCurrentActive =
                          att.timestamp === activeResult.timestamp &&
                          att.paperId === activeResult.paperId;

                        return (
                          <tr
                            key={att.timestamp + att.paperId}
                            className={`hover:bg-blue-50/50 transition ${
                              isCurrentActive ? 'bg-blue-50/70 font-semibold' : ''
                            }`}
                          >
                            <td className="px-6 py-3.5 whitespace-nowrap text-slate-600 font-mono text-[11px]">
                              {new Date(att.timestamp).toLocaleString()}
                            </td>
                            <td className="px-6 py-3.5">
                              <div className="font-bold text-slate-900 truncate max-w-xs">
                                {att.paperTitle}
                              </div>
                              <div className="text-[10px] text-slate-400 font-mono truncate">
                                {att.paperId}
                              </div>
                            </td>
                            <td className="px-4 py-3.5 text-center font-bold text-slate-900">
                              {att.scoreObtained.toFixed(2)}{' '}
                              <span className="text-[11px] text-slate-400 font-normal">
                                / {att.totalMarks}
                              </span>
                            </td>
                            <td className="px-4 py-3.5 text-center">
                              <span
                                className={`px-2 py-0.5 rounded font-bold ${
                                  att.percentageScore >= 50
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-amber-100 text-amber-800'
                                }`}
                              >
                                {att.percentageScore.toFixed(1)}%
                              </span>
                            </td>
                            <td className="px-4 py-3.5 text-center font-bold text-slate-700">
                              {att.accuracyPercentage.toFixed(0)}%
                            </td>
                            <td className="px-4 py-3.5 text-center text-slate-500 whitespace-nowrap">
                              {formatSec(att.durationTakenSeconds)}
                            </td>
                            <td className="px-6 py-3.5 text-right whitespace-nowrap space-x-2">
                              <button
                                onClick={() => {
                                  setActiveResult(att);
                                  setActiveTab('SCORECARD');
                                  if (onLoadPastAttempt) onLoadPastAttempt(att);
                                }}
                                className="px-3 py-1 bg-white hover:bg-slate-100 border border-slate-300 rounded font-semibold text-slate-700 text-xs shadow-xs transition"
                              >
                                Load Analysis
                              </button>
                              <button
                                onClick={() => onRetakeExam(att.paperId)}
                                className={`px-3 py-1 text-white rounded font-semibold text-xs shadow-xs transition ${
                                  historyExamFilter === 'NEET' ? 'bg-teal-700 hover:bg-teal-800' : 'bg-[#1a56a5] hover:bg-blue-700'
                                }`}
                              >
                                Retake
                              </button>
                              <button
                                onClick={() => handleDeleteSingle(att)}
                                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 rounded transition inline-flex items-center"
                                title="Delete this attempt record"
                              >
                                <Trash2 size={13} />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Image Zoom Modal */}
      {zoomImage && (
        <ImageZoomModal
          isOpen={true}
          imageUrl={zoomImage}
          onClose={() => setZoomImage(null)}
          title="Question Solution Diagram"
        />
      )}
    </div>
  );
};
