import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Calculator,
  FileText,
  BookOpen,
  Clock,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  AlertTriangle,
  Menu,
  X,
} from 'lucide-react';
import type { ExamPaper, Question, QuestionStatus, ExamResult } from '../../types';
import { evaluateExam } from '../../utils/evaluator';
import { saveAttempt, resolveImageUrl, getFallbackImageUrl, getUserProfile } from '../../utils/storage';
import { GateCalculatorModal } from '../calculator/GateCalculatorModal';
import { SubmitConfirmationModal } from '../modals/SubmitConfirmationModal';
import { QuestionPaperModal } from '../modals/QuestionPaperModal';
import { InstructionsModal } from '../modals/InstructionsModal';
import { ImageZoomModal } from '../modals/ImageZoomModal';

interface CbtExamWindowProps {
  paper: ExamPaper;
  onFinishExam: (result: ExamResult) => void;
  onExitExam: () => void;
}

export const CbtExamWindow: React.FC<CbtExamWindowProps> = ({
  paper,
  onFinishExam,
  onExitExam,
}) => {
  const profile = getUserProfile();

  // Flatten questions from all sections with sequential indices
  const allQuestions: Question[] = useMemo(() => {
    return paper.sections.flatMap((s) => s.questions);
  }, [paper]);

  // Current question index in flattened list
  const [currentIndex, setCurrentIndex] = useState(0);

  // Map of answers: { [questionId: number]: any }
  const [answers, setAnswers] = useState<{ [qId: number]: any }>(() => {
    const init: { [qId: number]: any } = {};
    allQuestions.forEach((q) => {
      if (q.candidateAnswer !== undefined && q.candidateAnswer !== null) {
        init[q.questionId] = q.candidateAnswer;
      }
    });
    return init;
  });

  // Map of statuses: { [questionId: number]: QuestionStatus }
  const [statuses, setStatuses] = useState<{ [qId: number]: QuestionStatus }>(() => {
    const init: { [qId: number]: QuestionStatus } = {};
    allQuestions.forEach((q, idx) => {
      init[q.questionId] = idx === 0 ? 'NOT_ANSWERED' : 'NOT_VISITED';
    });
    return init;
  });

  // Timer: Duration in seconds
  const [timeLeft, setTimeLeft] = useState<number>(paper.durationMinutes * 60);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Modals state
  const [showCalculator, setShowCalculator] = useState(false);
  const [showQuestionPaper, setShowQuestionPaper] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [zoomImage, setZoomImage] = useState<string | null>(null);

  // Proctoring tab-switch state
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [showTabWarning, setShowTabWarning] = useState(false);

  const currentQ: Question = allQuestions[currentIndex];

  // Group questions by section name
  const sections = useMemo(() => {
    const map = new Map<string, number[]>();
    allQuestions.forEach((q, idx) => {
      const sec = q.sectionName || 'General';
      if (!map.has(sec)) map.set(sec, []);
      map.get(sec)!.push(idx);
    });
    return Array.from(map.entries()).map(([name, indices]) => ({ name, indices }));
  }, [allQuestions]);

  const currentSectionName = currentQ?.sectionName || sections[0]?.name || 'General';

  // Format time HH:MM:SS
  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
  };

  // Build evaluated paper copy with user answers and statuses
  const buildPaperWithResponses = useCallback((): ExamPaper => {
    return {
      ...paper,
      sections: paper.sections.map((sec) => ({
        ...sec,
        questions: sec.questions.map((q) => ({
          ...q,
          candidateAnswer: answers[q.questionId] ?? null,
          status: statuses[q.questionId] || 'NOT_VISITED',
        })),
      })),
    };
  }, [paper, answers, statuses]);

  // Perform Final Submission
  const handleFinalSubmit = useCallback(() => {
    const timeSpentSeconds = paper.durationMinutes * 60 - timeLeft;
    const evaluatedPaper = buildPaperWithResponses();
    const result = evaluateExam(
      evaluatedPaper,
      profile.name,
      profile.rollNumber,
      timeSpentSeconds
    );
    saveAttempt(result);
    setShowSubmitModal(false);
    onFinishExam(result);
  }, [paper, timeLeft, buildPaperWithResponses, profile, onFinishExam]);

  // Timer Tick
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setTimeout(() => handleFinalSubmit(), 100);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [handleFinalSubmit]);

  // Tab switch focus listener
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitchCount((c) => {
          const next = c + 1;
          setShowTabWarning(true);
          return next;
        });
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  // Status counts for palette
  const statusCounts = useMemo(() => {
    let answered = 0;
    let notAnswered = 0;
    let notVisited = 0;
    let marked = 0;
    let answeredAndMarked = 0;

    allQuestions.forEach((q) => {
      const st = statuses[q.questionId];
      if (st === 'ANSWERED') answered++;
      else if (st === 'NOT_ANSWERED') notAnswered++;
      else if (st === 'MARKED_FOR_REVIEW') marked++;
      else if (st === 'ANSWERED_AND_MARKED') answeredAndMarked++;
      else notVisited++;
    });

    return { answered, notAnswered, notVisited, marked, answeredAndMarked };
  }, [allQuestions, statuses]);

  // Jump to Question handler
  const jumpToQuestion = (targetIndex: number) => {
    if (targetIndex < 0 || targetIndex >= allQuestions.length) return;

    const targetQ = allQuestions[targetIndex];
    setStatuses((prev) => {
      const updated = { ...prev };
      if (updated[targetQ.questionId] === 'NOT_VISITED') {
        updated[targetQ.questionId] = 'NOT_ANSWERED';
      }
      return updated;
    });

    setCurrentIndex(targetIndex);

    // Auto-close drawer on mobile when candidate selects a question
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  };

  // Action: Save & Next
  const handleSaveAndNext = () => {
    const hasAnswer =
      answers[currentQ.questionId] !== undefined &&
      answers[currentQ.questionId] !== '' &&
      (!Array.isArray(answers[currentQ.questionId]) || answers[currentQ.questionId].length > 0);

    const nextQ = currentIndex + 1 < allQuestions.length ? allQuestions[currentIndex + 1] : null;

    setStatuses((prev) => ({
      ...prev,
      [currentQ.questionId]: hasAnswer ? 'ANSWERED' : 'NOT_ANSWERED',
      ...(nextQ && prev[nextQ.questionId] === 'NOT_VISITED'
        ? { [nextQ.questionId]: 'NOT_ANSWERED' }
        : {}),
    }));

    if (currentIndex + 1 < allQuestions.length) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  // Action: Mark for Review & Next
  const handleMarkForReviewAndNext = () => {
    const hasAnswer =
      answers[currentQ.questionId] !== undefined &&
      answers[currentQ.questionId] !== '' &&
      (!Array.isArray(answers[currentQ.questionId]) || answers[currentQ.questionId].length > 0);

    const nextQ = currentIndex + 1 < allQuestions.length ? allQuestions[currentIndex + 1] : null;

    setStatuses((prev) => ({
      ...prev,
      [currentQ.questionId]: hasAnswer ? 'ANSWERED_AND_MARKED' : 'MARKED_FOR_REVIEW',
      ...(nextQ && prev[nextQ.questionId] === 'NOT_VISITED'
        ? { [nextQ.questionId]: 'NOT_ANSWERED' }
        : {}),
    }));

    if (currentIndex + 1 < allQuestions.length) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  // Action: Clear Response
  const handleClearResponse = () => {
    setAnswers((prev) => {
      const updated = { ...prev };
      delete updated[currentQ.questionId];
      return updated;
    });
    setStatuses((prev) => ({
      ...prev,
      [currentQ.questionId]: 'NOT_ANSWERED',
    }));
  };

  // Action: Previous
  const handlePrevious = () => {
    if (currentIndex > 0) {
      jumpToQuestion(currentIndex - 1);
    }
  };

  // Input handlers
  const handleSelectMCQ = (optionKey: string) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQ.questionId]: optionKey,
    }));
  };

  const handleToggleMSQ = (optionKey: string) => {
    const currentList = (answers[currentQ.questionId] as string[]) || [];
    const exists = currentList.includes(optionKey);
    let nextList: string[];
    if (exists) {
      nextList = currentList.filter((k) => k !== optionKey);
    } else {
      nextList = [...currentList, optionKey].sort();
    }
    setAnswers((prev) => ({
      ...prev,
      [currentQ.questionId]: nextList,
    }));
  };

  const handleNATInput = (char: string) => {
    const currentVal = (answers[currentQ.questionId] as string) || '';
    if (char === 'CLEAR') {
      handleClearResponse();
      return;
    }
    if (char === 'BACK') {
      const nextVal = currentVal.slice(0, -1);
      setAnswers((prev) => ({
        ...prev,
        [currentQ.questionId]: nextVal,
      }));
      return;
    }
    if (char === '-' && (currentVal.includes('-') || currentVal.length > 0)) return;
    if (char === '.' && currentVal.includes('.')) return;

    setAnswers((prev) => ({
      ...prev,
      [currentQ.questionId]: currentVal + char,
    }));
  };

  // Render question symbol for palette
  const renderPaletteButton = (idx: number) => {
    const q = allQuestions[idx];
    const st = statuses[q.questionId];
    const isCurrent = idx === currentIndex;

    let baseClass =
      'w-9 h-9 text-xs font-bold rounded flex items-center justify-center transition shadow-xs ';

    if (isCurrent) {
      baseClass += 'ring-2 ring-blue-500 ring-offset-1 font-black ';
    }

    if (st === 'ANSWERED') {
      return (
        <button
          key={idx}
          onClick={() => jumpToQuestion(idx)}
          className={baseClass + 'bg-[#27ae60] text-white hover:bg-emerald-600'}
        >
          {idx + 1}
        </button>
      );
    } else if (st === 'NOT_ANSWERED') {
      return (
        <button
          key={idx}
          onClick={() => jumpToQuestion(idx)}
          className={baseClass + 'bg-[#e74c3c] text-white hover:bg-red-600'}
        >
          {idx + 1}
        </button>
      );
    } else if (st === 'MARKED_FOR_REVIEW') {
      return (
        <button
          key={idx}
          onClick={() => jumpToQuestion(idx)}
          className={baseClass + 'bg-[#8e44ad] text-white rounded-full hover:bg-purple-700'}
        >
          {idx + 1}
        </button>
      );
    } else if (st === 'ANSWERED_AND_MARKED') {
      return (
        <button
          key={idx}
          onClick={() => jumpToQuestion(idx)}
          className={
            baseClass + 'relative bg-[#8e44ad] text-white rounded-full hover:bg-purple-700'
          }
        >
          {idx + 1}
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border border-white" />
        </button>
      );
    } else {
      return (
        <button
          key={idx}
          onClick={() => jumpToQuestion(idx)}
          className={
            baseClass + 'bg-slate-200 text-slate-800 border border-slate-300 hover:bg-slate-300'
          }
        >
          {idx + 1}
        </button>
      );
    }
  };

  const isTimeCritical = timeLeft < 15 * 60;
  const imgSrc = currentQ?.imageUrl ? resolveImageUrl(currentQ.imageUrl) : null;
  const negMarks =
    currentQ?.negativeMarks ||
    (currentQ?.type === 'MCQ' ? (currentQ.positiveMarks === 1 ? 0.33 : 0.67) : 0);

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-100 font-sans overflow-hidden select-none">
      {/* 1. Official TCS iON Top Bar */}
      <header className="bg-[#1a56a5] text-white h-14 px-4 flex items-center justify-between shrink-0 shadow-sm z-20">
        <div className="flex items-center gap-3">
          <div className="font-extrabold text-lg tracking-wide hidden sm:block">GATE CBT</div>
          <div className="h-5 w-px bg-white/20 hidden sm:block" />
          <div className="font-semibold text-sm truncate max-w-[200px] sm:max-w-md">
            {paper.title}
          </div>
        </div>

        {/* Tools and Live Timer */}
        <div className="flex items-center gap-2 sm:gap-4">
          <button
            onClick={() => setShowCalculator(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-xs font-medium text-white transition border border-white/20"
            title="Open Scientific Calculator"
          >
            <Calculator size={15} />
            <span className="hidden md:inline">Calculator</span>
          </button>

          <button
            onClick={() => setShowQuestionPaper(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-xs font-medium text-white transition border border-white/20"
            title="View Full Question Paper"
          >
            <FileText size={15} />
            <span className="hidden md:inline">Question Paper</span>
          </button>

          <button
            onClick={() => setShowInstructions(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-xs font-medium text-white transition border border-white/20"
            title="Read Instructions"
          >
            <BookOpen size={15} />
            <span className="hidden md:inline">Instructions</span>
          </button>

          {/* Countdown Clock */}
          <div
            className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 rounded font-mono font-bold text-xs sm:text-sm shadow-xs ${
              isTimeCritical
                ? 'bg-rose-600 text-white animate-pulse'
                : 'bg-white text-slate-900 border border-slate-300'
            }`}
          >
            <Clock size={14} className={isTimeCritical ? 'text-white' : 'text-[#1a56a5]'} />
            <span>{formatTime(timeLeft)}</span>
          </div>

          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-blue-800 hover:bg-blue-700 text-white text-xs font-semibold border border-white/30 lg:hidden shadow-xs"
            title="Toggle Question Palette"
          >
            <Menu size={16} />
            <span className="hidden xs:inline">Palette</span>
          </button>
        </div>
      </header>

      {/* 2. Section Navigation Tabs Bar */}
      <nav className="bg-slate-200 border-b border-slate-300 px-3 sm:px-4 py-1.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-0.5">
          <span className="text-xs font-bold text-slate-600 uppercase pr-1">Sections:</span>
          {sections.map((sec) => {
            const isActive = sec.name === currentSectionName;
            return (
              <button
                key={sec.name}
                onClick={() => jumpToQuestion(sec.indices[0])}
                className={`px-3 py-1 rounded text-xs font-bold transition whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-[#1a56a5] text-white shadow-xs'
                    : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-300'
                }`}
              >
                <span>{sec.name}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-blue-800 text-white' : 'bg-slate-200 text-slate-700'
                  }`}
                >
                  {sec.indices.length}
                </span>
              </button>
            );
          })}
        </div>

        <div className="hidden sm:flex items-center gap-3 text-xs text-slate-600">
          <span>
            Candidate: <strong className="text-slate-800">{profile.name}</strong>
          </span>
          <span className="font-mono text-[11px] text-slate-500">[{profile.rollNumber}]</span>
        </div>
      </nav>

      {/* 3. Main Split View: Question Area & Right Palette */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left: Question Viewer & Answer Area */}
        <div className="flex-1 flex flex-col bg-white overflow-hidden border-r border-slate-300">
          {/* Question Metadata Header */}
          <div className="px-3 sm:px-5 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between shrink-0 text-xs">
            <div className="flex items-center gap-2 sm:gap-3">
              <span className="font-black text-xs sm:text-sm text-[#1a56a5]">
                Q.{currentIndex + 1}
              </span>
              <span className="px-2 py-0.5 rounded font-bold uppercase tracking-wider bg-blue-100 text-[#1a56a5] border border-blue-200 text-[10px] sm:text-xs">
                {currentQ.type}
              </span>
              {currentQ.type === 'MSQ' && (
                <span className="hidden md:inline text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200 font-semibold text-[11px]">
                  One or more options correct
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 sm:gap-4 font-semibold text-[11px] sm:text-xs">
              <span className="text-emerald-700">+{currentQ.positiveMarks}</span>
              <span className="text-rose-700">-{negMarks.toFixed(2)}</span>
            </div>
          </div>

          {/* Question Content & Diagram Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
            <div className="space-y-3">
              {imgSrc ? (
                <div className="w-full block space-y-2">
                  <img
                    src={imgSrc}
                    alt={`Question ${currentIndex + 1}`}
                    onError={(e) => {
                      const fb = getFallbackImageUrl(currentQ.imageUrl);
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
                <div className="text-sm font-medium text-slate-800 whitespace-pre-wrap leading-relaxed">
                  {currentQ.questionText || 'Question description is loaded.'}
                </div>
              )}
            </div>

            {/* Answer Input Controls */}
            <div className="pt-4 border-t border-slate-200">
              {/* Case 1: Multiple Choice Question (MCQ) */}
              {currentQ.type === 'MCQ' && (
                <div className="space-y-3 max-w-xl">
                  <div className="text-xs font-bold text-slate-600 uppercase tracking-wide">
                    Choose one option:
                  </div>
                  {['A', 'B', 'C', 'D'].map((key) => {
                    const isSelected = answers[currentQ.questionId] === key;
                    const optObj = currentQ.options?.find((o) => o.id === key);
                    return (
                      <label
                        key={key}
                        onClick={() => handleSelectMCQ(key)}
                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition select-none ${
                          isSelected
                            ? 'bg-blue-50 border-[#1a56a5] text-[#1a56a5] shadow-xs'
                            : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800'
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                            isSelected ? 'border-[#1a56a5]' : 'border-slate-400'
                          }`}
                        >
                          {isSelected && <div className="w-2.5 h-2.5 bg-[#1a56a5] rounded-full" />}
                        </div>
                        <span className="font-bold text-sm">({key})</span>
                        {optObj && optObj.text && (
                          <span className="text-xs text-slate-700">{optObj.text}</span>
                        )}
                      </label>
                    );
                  })}
                </div>
              )}

              {/* Case 2: Multiple Select Question (MSQ) */}
              {currentQ.type === 'MSQ' && (
                <div className="space-y-3 max-w-xl">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-purple-900 uppercase tracking-wide">
                      Select one or more correct options (MSQ):
                    </span>
                    <span className="text-purple-700 font-semibold text-[11px]">
                      No partial marking
                    </span>
                  </div>

                  {['A', 'B', 'C', 'D'].map((key) => {
                    const currentList = (answers[currentQ.questionId] as string[]) || [];
                    const isSelected = currentList.includes(key);
                    const optObj = currentQ.options?.find((o) => o.id === key);

                    return (
                      <label
                        key={key}
                        onClick={() => handleToggleMSQ(key)}
                        className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition select-none ${
                          isSelected
                            ? 'bg-purple-50 border-purple-600 text-purple-900 shadow-xs'
                            : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 ${
                              isSelected
                                ? 'bg-purple-600 border-purple-600 text-white'
                                : 'border-slate-400 bg-white'
                            }`}
                          >
                            {isSelected && <span className="text-xs font-bold leading-none">✓</span>}
                          </div>
                          <span className="font-bold text-sm">({key})</span>
                          {optObj && optObj.text && (
                            <span className="text-xs text-slate-700">{optObj.text}</span>
                          )}
                        </div>

                        {isSelected && (
                          <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300">
                            [ ✓ SELECTED ]
                          </span>
                        )}
                      </label>
                    );
                  })}
                </div>
              )}

              {/* Case 3: Numerical Answer Type (NAT) */}
              {currentQ.type === 'NAT' && (
                <div className="space-y-4 max-w-md">
                  <div className="text-xs font-bold text-slate-600 uppercase tracking-wide">
                    Numerical Answer Type (Enter Real Number):
                  </div>

                  {/* Input Display Box */}
                  <div className="p-3 bg-slate-50 border-2 border-blue-400 rounded-lg flex items-center justify-between">
                    <span className="text-xs text-slate-500 font-semibold">Your Answer:</span>
                    <span className="text-xl font-mono font-bold text-slate-900 min-w-[80px] text-right">
                      {answers[currentQ.questionId] || <span className="text-slate-300">_</span>}
                    </span>
                  </div>

                  {/* Virtual Numeric Keypad */}
                  <div className="grid grid-cols-3 gap-2 bg-slate-100 p-3 rounded-lg border border-slate-300">
                    {['7', '8', '9', '4', '5', '6', '1', '2', '3', '0', '.', '-'].map((k) => (
                      <button
                        key={k}
                        onClick={() => handleNATInput(k)}
                        className="h-11 bg-white hover:bg-blue-50 border border-slate-300 rounded font-bold text-base text-slate-800 shadow-xs active:bg-blue-100 transition"
                      >
                        {k}
                      </button>
                    ))}
                    <button
                      onClick={() => handleNATInput('BACK')}
                      className="h-11 bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded font-semibold text-xs text-amber-900 col-span-1 shadow-xs transition"
                    >
                      Bksp
                    </button>
                    <button
                      onClick={() => handleNATInput('CLEAR')}
                      className="h-11 bg-rose-100 hover:bg-rose-200 border border-rose-300 rounded font-semibold text-xs text-rose-900 col-span-2 shadow-xs transition"
                    >
                      Clear Input
                    </button>
                  </div>
                  <div className="text-[11px] text-slate-500 italic">
                    Physical numeric keyboard input also accepted. No negative marking for NAT questions.
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action Footer Bar */}
          <footer className="px-3 sm:px-5 py-2.5 sm:py-3 bg-slate-100 border-t border-slate-300 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 shrink-0">
            <div className="flex items-center justify-between sm:justify-start gap-2">
              <button
                onClick={handleMarkForReviewAndNext}
                className="flex-1 sm:flex-none px-3 py-2 bg-white hover:bg-purple-50 text-purple-800 border border-purple-400 rounded text-xs font-semibold shadow-xs transition text-center"
              >
                Review &amp; Next
              </button>
              <button
                onClick={handleClearResponse}
                className="flex-1 sm:flex-none px-3 py-2 bg-white hover:bg-rose-50 text-rose-700 border border-rose-300 rounded text-xs font-semibold shadow-xs transition text-center"
              >
                Clear Response
              </button>
            </div>

            <div className="flex items-center justify-between sm:justify-end gap-2">
              <button
                onClick={handlePrevious}
                disabled={currentIndex === 0}
                className={`flex-1 sm:flex-none flex items-center justify-center gap-1 px-3 py-2 rounded text-xs font-semibold transition ${
                  currentIndex === 0
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-xs'
                }`}
              >
                <ChevronLeft size={16} /> Prev
              </button>

              <button
                onClick={handleSaveAndNext}
                className="flex-1 sm:flex-none flex items-center justify-center gap-1 px-4 py-2 bg-[#1a56a5] hover:bg-blue-700 text-white rounded text-xs font-bold shadow-xs transition"
              >
                Save &amp; Next <ChevronRight size={16} />
              </button>

              <button
                onClick={() => setShowSubmitModal(true)}
                className="flex-1 sm:flex-none px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-black uppercase tracking-wider shadow-md transition text-center"
              >
                Submit
              </button>
            </div>
          </footer>
        </div>

        {/* Mobile Backdrop Overlay when Question Palette Drawer is open */}
        {isSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-xs z-40 lg:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        {/* Right: TCS iON Question Palette & Candidate Profile (Mobile Slide-Over Drawer + Desktop Docked) */}
        <div
          className={`
            fixed top-0 bottom-0 right-0 z-50 w-[85vw] max-w-sm bg-white shadow-2xl flex flex-col transition-transform duration-200 ease-in-out
            lg:static lg:z-auto lg:w-80 xl:w-96 lg:shadow-none lg:border-l lg:border-slate-300
            ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          `}
        >
          {/* Candidate Card & Mobile Close Button */}
          <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded bg-[#1a56a5] text-white flex items-center justify-center font-bold text-base sm:text-lg shadow-xs shrink-0">
                {profile.name ? profile.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="min-w-0">
                <div className="font-bold text-xs text-slate-900 truncate">{profile.name}</div>
                <div className="text-[11px] font-mono text-slate-500 truncate">{profile.rollNumber}</div>
                <div className="text-[10px] text-blue-700 font-medium truncate">{profile.branch}</div>
              </div>
            </div>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-500 lg:hidden"
              title="Close Palette"
            >
              <X size={18} />
            </button>
          </div>

          {/* Symbol Legend Counter */}
          <div className="p-3 border-b border-slate-200 bg-slate-50/60 space-y-2 text-xs">
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded bg-[#27ae60] text-white font-bold flex items-center justify-center text-[10px]">
                  {statusCounts.answered}
                </span>
                <span className="text-slate-700">Answered</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded bg-[#e74c3c] text-white font-bold flex items-center justify-center text-[10px]">
                  {statusCounts.notAnswered}
                </span>
                <span className="text-slate-700">Not Answered</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded bg-slate-200 text-slate-700 font-bold flex items-center justify-center border text-[10px]">
                  {statusCounts.notVisited}
                </span>
                <span className="text-slate-700">Not Visited</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#8e44ad] text-white font-bold flex items-center justify-center text-[10px]">
                  {statusCounts.marked}
                </span>
                <span className="text-slate-700">Marked for Review</span>
              </div>
              <div className="flex items-center gap-2 col-span-2">
                <div className="relative w-5 h-5 rounded-full bg-[#8e44ad] text-white font-bold flex items-center justify-center text-[10px]">
                  {statusCounts.answeredAndMarked}
                  <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 bg-emerald-500 rounded-full border border-white" />
                </div>
                <span className="text-slate-700 truncate">
                  Ans &amp; Marked for Review (Evaluated)
                </span>
              </div>
            </div>
          </div>

          {/* Section Selector / Filter for palette */}
          <div className="px-3 py-2 bg-slate-100 border-b border-slate-200 text-xs font-bold text-slate-700 flex items-center justify-between">
            <span>Question Palette ({allQuestions.length})</span>
            <span className="text-slate-500 text-[11px] font-normal">{currentSectionName}</span>
          </div>

          {/* Question Grid */}
          <div className="flex-1 overflow-y-auto p-3">
            <div className="grid grid-cols-5 gap-2">
              {allQuestions.map((_, idx) => renderPaletteButton(idx))}
            </div>
          </div>

          {/* Bottom Quick Actions inside palette */}
          <div className="p-3 bg-slate-50 border-t border-slate-200 space-y-2">
            <button
              onClick={() => setShowSubmitModal(true)}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-bold text-xs uppercase tracking-wider shadow transition"
            >
              Submit Examination
            </button>
            <button
              onClick={onExitExam}
              className="w-full py-1.5 text-xs text-rose-700 hover:underline text-center"
            >
              Exit to Inventory (Abandon Test)
            </button>
          </div>
        </div>
      </div>

      {/* Proctoring Tab Switch Warning Toast */}
      {showTabWarning && (
        <div className="fixed bottom-4 left-4 z-50 bg-rose-600 text-white px-4 py-3 rounded-lg shadow-xl flex items-center gap-3 animate-bounce">
          <AlertTriangle size={20} className="shrink-0 text-amber-300" />
          <div className="text-xs">
            <strong>Warning: Window blur detected!</strong>
            <p>Switching tabs is monitored during CBT examination. Alert count: {tabSwitchCount}</p>
          </div>
          <button
            onClick={() => setShowTabWarning(false)}
            className="ml-2 text-white/80 hover:text-white font-bold text-xs"
          >
            ✕
          </button>
        </div>
      )}

      {/* Modals */}
      <GateCalculatorModal isOpen={showCalculator} onClose={() => setShowCalculator(false)} />
      <QuestionPaperModal
        isOpen={showQuestionPaper}
        paper={paper}
        onClose={() => setShowQuestionPaper(false)}
        onJumpToQuestion={(idx) => jumpToQuestion(idx)}
      />
      <InstructionsModal isOpen={showInstructions} onClose={() => setShowInstructions(false)} />
      {zoomImage && (
        <ImageZoomModal
          isOpen={true}
          imageUrl={zoomImage}
          onClose={() => setZoomImage(null)}
          title={`Question ${currentIndex + 1} Diagram`}
        />
      )}
      <SubmitConfirmationModal
        isOpen={showSubmitModal}
        paper={buildPaperWithResponses()}
        onClose={() => setShowSubmitModal(false)}
        onConfirm={() => handleFinalSubmit()}
        onCancel={() => setShowSubmitModal(false)}
      />
    </div>
  );
};
