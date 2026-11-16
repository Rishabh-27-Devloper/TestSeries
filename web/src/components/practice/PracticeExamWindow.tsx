import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Clock,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  SkipForward,
  ChevronRight,
  Maximize,
  Minimize,
  Award,
  Zap,
  ZoomIn,
  X,
} from 'lucide-react';
import type {
  PracticeQuestion,
  PracticeTopicItem,
  PracticeQuestionAttempt,
  UserProfile,
} from '../../types';
import {
  getPracticeQuestion,
  savePracticeAttempt,
  getPracticeState,
  resolveImageUrl,
  getFallbackImageUrl,
} from '../../utils/storage';
import { isFullscreen, toggleFullscreen, subscribeToFullscreen } from '../../utils/fullscreen';

interface PracticeExamWindowProps {
  topic: PracticeTopicItem;
  profile: UserProfile;
  onFinishTopic: () => void;
  onExitPractice: () => void;
}

export const PracticeExamWindow: React.FC<PracticeExamWindowProps> = ({
  topic,
  profile,
  onFinishTopic,
  onExitPractice,
}) => {
  // Question pool: questions that are NOT yet mastered (solved correctly)
  const [questionPool, setQuestionPool] = useState<string[]>([]);
  const [currentPoolIndex, setCurrentPoolIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [currentQuestion, setCurrentQuestion] = useState<PracticeQuestion | null>(null);

  // User input & feedback state for current question
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [selectedMsqOptions, setSelectedMsqOptions] = useState<string[]>([]);
  const [natAnswer, setNatAnswer] = useState<string>('');
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [isCorrect, setIsCorrect] = useState<boolean>(false);
  const [zoomImage, setZoomImage] = useState<string | null>(null);

  // Forward timer / stopwatch per question
  const [secondsSpent, setSecondsSpent] = useState<number>(0);
  const timerRef = useRef<any>(null);

  // Session summary stats
  const [sessionCorrectCount, setSessionCorrectCount] = useState<number>(0);
  const [sessionWrongCount, setSessionWrongCount] = useState<number>(0);
  const [sessionSkippedCount, setSessionSkippedCount] = useState<number>(0);
  const [sessionTotalTime, setSessionTotalTime] = useState<number>(0);
  const [sessionCompleted, setSessionCompleted] = useState<boolean>(false);

  // Fullscreen state
  const [isFs, setIsFs] = useState(() => isFullscreen());

  useEffect(() => {
    return subscribeToFullscreen((active) => {
      setIsFs(active);
    });
  }, []);

  // Initialize question pool: filter out questions already mastered (solved correctly)
  useEffect(() => {
    const userState = getPracticeState(profile.name);
    const solvedSet = new Set(userState.solvedQuestionIds || []);

    // Eligible questions = questions in topic that are NOT yet solved correctly
    let eligible = topic.questionIds.filter((qid) => !solvedSet.has(qid));

    if (eligible.length === 0) {
      // All questions already mastered in this topic! Provide full topic for revision
      eligible = [...topic.questionIds];
    }

    // Shuffle randomly so questions pop up randomly as requested
    const shuffled = [...eligible].sort(() => Math.random() - 0.5);
    setQuestionPool(shuffled);
    setCurrentPoolIndex(0);
    setLoading(false);
  }, [topic, profile.name]);

  // Load question data when currentPoolIndex or questionPool changes
  const loadQuestion = useCallback(async (qid: string) => {
    try {
      setLoading(true);
      const q = await getPracticeQuestion(qid);
      setCurrentQuestion(q);
      setSelectedOption('');
      setSelectedMsqOptions([]);
      setNatAnswer('');
      setIsSubmitted(false);
      setIsCorrect(false);
      setSecondsSpent(0);
    } catch (err) {
      console.error('Failed to load practice question:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (questionPool.length > 0 && currentPoolIndex < questionPool.length) {
      loadQuestion(questionPool[currentPoolIndex]);
    } else if (questionPool.length > 0 && currentPoolIndex >= questionPool.length) {
      setSessionCompleted(true);
    }
  }, [questionPool, currentPoolIndex, loadQuestion]);

  // Forward timer / stopwatch ticking
  useEffect(() => {
    if (!isSubmitted && !sessionCompleted && !loading) {
      timerRef.current = setInterval(() => {
        setSecondsSpent((s) => s + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isSubmitted, sessionCompleted, loading]);

  // Format seconds to mm:ss
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Evaluate candidate answer
  const evaluateAnswer = (): boolean => {
    if (!currentQuestion) return false;
    const correct = currentQuestion.correctAnswer;
    if (correct === null || correct === undefined || correct === '') {
      // If no answer key in PDF, mark as submitted/accepted
      return true;
    }

    if (currentQuestion.type === 'MCQ') {
      return String(selectedOption).trim().toUpperCase() === String(correct).trim().toUpperCase();
    }

    if (currentQuestion.type === 'MSQ') {
      const correctArr = Array.isArray(correct)
        ? correct.map((c) => String(c).trim().toUpperCase())
        : String(correct).split(',').map((c) => c.trim().toUpperCase());
      const userArr = selectedMsqOptions.map((c) => c.trim().toUpperCase());
      if (correctArr.length !== userArr.length) return false;
      return correctArr.every((c) => userArr.includes(c));
    }

    if (currentQuestion.type === 'NAT') {
      const userVal = parseFloat(natAnswer.trim());
      if (isNaN(userVal)) return false;
      if (currentQuestion.toleranceMin !== null && currentQuestion.toleranceMin !== undefined &&
          currentQuestion.toleranceMax !== null && currentQuestion.toleranceMax !== undefined) {
        return userVal >= currentQuestion.toleranceMin && userVal <= currentQuestion.toleranceMax;
      }
      const correctVal = parseFloat(String(correct).trim());
      if (isNaN(correctVal)) return false;
      return Math.abs(userVal - correctVal) <= 0.05;
    }

    return false;
  };

  // Handle Submit Answer
  const handleSubmitAnswer = () => {
    if (!currentQuestion || isSubmitted) return;
    const correct = evaluateAnswer();
    setIsCorrect(correct);
    setIsSubmitted(true);

    let userResponse: any = null;
    if (currentQuestion.type === 'MCQ') userResponse = selectedOption;
    else if (currentQuestion.type === 'MSQ') userResponse = selectedMsqOptions;
    else if (currentQuestion.type === 'NAT') userResponse = natAnswer;

    const attempt: PracticeQuestionAttempt = {
      id: `att_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      questionId: currentQuestion.questionId,
      subject: currentQuestion.subject,
      chapter: currentQuestion.chapter,
      topic: currentQuestion.topic,
      marks: currentQuestion.marks,
      type: currentQuestion.type,
      userResponse,
      correctAnswer: currentQuestion.correctAnswer,
      status: correct ? 'CORRECT' : 'WRONG',
      timeSpentSeconds: secondsSpent,
      timestamp: new Date().toISOString(),
    };

    savePracticeAttempt(attempt, profile.name);

    if (correct) {
      setSessionCorrectCount((c) => c + 1);
    } else {
      setSessionWrongCount((w) => w + 1);
    }
    setSessionTotalTime((t) => t + secondsSpent);
  };

  // Handle Skip Question
  const handleSkipQuestion = () => {
    if (!currentQuestion) return;

    const attempt: PracticeQuestionAttempt = {
      id: `att_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      questionId: currentQuestion.questionId,
      subject: currentQuestion.subject,
      chapter: currentQuestion.chapter,
      topic: currentQuestion.topic,
      marks: currentQuestion.marks,
      type: currentQuestion.type,
      userResponse: null,
      correctAnswer: currentQuestion.correctAnswer,
      status: 'SKIPPED',
      timeSpentSeconds: secondsSpent,
      timestamp: new Date().toISOString(),
    };

    savePracticeAttempt(attempt, profile.name);
    setSessionSkippedCount((s) => s + 1);
    setSessionTotalTime((t) => t + secondsSpent);

    // Proceed directly to next question in pool
    setCurrentPoolIndex((i) => i + 1);
  };

  // Handle Next Question
  const handleNextQuestion = () => {
    setCurrentPoolIndex((i) => i + 1);
  };

  // On-screen Keypad click for NAT
  const handleKeypadPress = (val: string) => {
    if (isSubmitted) return;
    if (val === 'CLEAR') {
      setNatAnswer('');
    } else if (val === 'BACK') {
      setNatAnswer((prev) => prev.slice(0, -1));
    } else if (val === '+/-') {
      setNatAnswer((prev) => (prev.startsWith('-') ? prev.substring(1) : '-' + prev));
    } else {
      setNatAnswer((prev) => prev + val);
    }
  };

  // If session is complete (all questions in pool answered/skipped)
  if (sessionCompleted) {
    const totalAttempted = sessionCorrectCount + sessionWrongCount;
    const accuracy = totalAttempted > 0 ? Math.round((sessionCorrectCount / totalAttempted) * 100) : 0;
    const avgTime = totalAttempted > 0 ? Math.round(sessionTotalTime / (totalAttempted + sessionSkippedCount)) : 0;

    return (
      <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center p-4 font-sans">
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6 sm:p-8 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto shadow-inner">
            <Award size={36} />
          </div>

          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-bold uppercase tracking-wider mb-2">
              <Zap size={14} /> Practice Topic Completed
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">
              {topic.topicName}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {topic.subject} &bull; {topic.chapter}
            </p>
          </div>

          {/* Session Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <div className="text-[10px] font-bold text-slate-500 uppercase">Correct</div>
              <div className="text-2xl font-black text-emerald-600 mt-1">{sessionCorrectCount}</div>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <div className="text-[10px] font-bold text-slate-500 uppercase">Wrong</div>
              <div className="text-2xl font-black text-rose-600 mt-1">{sessionWrongCount}</div>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <div className="text-[10px] font-bold text-slate-500 uppercase">Skipped</div>
              <div className="text-2xl font-black text-amber-600 mt-1">{sessionSkippedCount}</div>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <div className="text-[10px] font-bold text-slate-500 uppercase">Accuracy</div>
              <div className="text-2xl font-black text-purple-700 mt-1">{accuracy}%</div>
            </div>
          </div>

          <div className="bg-purple-50 rounded-xl p-3.5 border border-purple-100 flex items-center justify-between text-xs text-purple-900">
            <span className="flex items-center gap-1.5 font-medium">
              <Clock size={15} /> Total Session Time:
            </span>
            <span className="font-bold">{formatTime(sessionTotalTime)} (Avg {avgTime}s / question)</span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <button
              onClick={onFinishTopic}
              className="w-full sm:flex-1 py-3 px-4 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs transition shadow-md"
            >
              Practice Another Topic
            </button>
            <button
              onClick={onExitPractice}
              className="w-full sm:flex-1 py-3 px-4 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs transition"
            >
              Exit to Topics List
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isOptionSelected =
    currentQuestion?.type === 'MCQ'
      ? Boolean(selectedOption)
      : currentQuestion?.type === 'MSQ'
      ? selectedMsqOptions.length > 0
      : Boolean(natAnswer.trim());

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans select-none">
      {/* 1. Practice Top Navigation Bar */}
      <header className="bg-purple-900 text-white border-b border-purple-950 sticky top-0 z-30 shadow-md">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 h-14 sm:h-16 flex items-center justify-between gap-3">
          {/* Back & Topic Information */}
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <button
              onClick={onExitPractice}
              className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition shrink-0"
              title="Return to Topics"
            >
              <ArrowLeft size={16} />
              <span className="hidden sm:inline ml-1">Topics</span>
            </button>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-extrabold text-amber-300 uppercase tracking-wider shrink-0">
                  {topic.subject}
                </span>
                <span className="text-white/40 hidden sm:inline">&bull;</span>
                <span className="text-xs font-medium text-purple-200 truncate hidden sm:inline">
                  DPP #{topic.dppNumber}
                </span>
              </div>
              <h1 className="text-xs sm:text-sm font-bold text-white truncate max-w-xs sm:max-w-md">
                {topic.topicName}
              </h1>
            </div>
          </div>

          {/* Question Counter, Marks, Stopwatch, Fullscreen */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {/* Question Counter */}
            <div className="text-[11px] sm:text-xs font-bold text-purple-200 bg-white/10 px-2.5 py-1 rounded-lg">
              <span>Q {currentPoolIndex + 1}</span>
              <span className="text-purple-300 font-normal"> / {questionPool.length}</span>
            </div>

            {/* Marks Badge */}
            <div className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[11px] font-extrabold bg-amber-400 text-slate-950">
              {currentQuestion?.marks || 1} {currentQuestion?.marks === 1 ? 'Mark' : 'Marks'}
            </div>

            {/* Live Forward Stopwatch (Forward Counted) */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-mono font-bold text-xs shadow-xs border ${
                isSubmitted
                  ? 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40'
                  : 'bg-black/30 text-white border-white/20'
              }`}
              title="Time spent on this question"
            >
              <Clock size={14} className={isSubmitted ? 'text-emerald-300' : 'text-amber-300 animate-pulse'} />
              <span>{formatTime(secondsSpent)}</span>
            </div>

            {/* Fullscreen Toggle */}
            <button
              onClick={() => toggleFullscreen()}
              className="p-1.5 sm:px-2 sm:py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white transition text-xs font-semibold"
              title={isFs ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            >
              {isFs ? <Minimize size={14} /> : <Maximize size={14} />}
            </button>
          </div>
        </div>
      </header>

      {/* 2. Main Question Practice Pane */}
      <main className="max-w-5xl mx-auto px-4 py-6 flex-1 w-full flex flex-col gap-5">
        {loading || !currentQuestion ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-500 text-sm">
            <div className="w-8 h-8 border-3 border-purple-600 border-t-transparent rounded-full animate-spin mb-3" />
            Loading practice question...
          </div>
        ) : (
          <>
            {/* Question Container Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
              {/* Question Header Strip */}
              <div className="bg-slate-50 border-b border-slate-200 px-5 py-3 flex items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-slate-800">
                    Question #{currentQuestion.questionNumber}
                  </span>
                  <span className="text-slate-400">&bull;</span>
                  <span className="px-2 py-0.5 rounded font-bold bg-slate-200 text-slate-700">
                    {currentQuestion.type}
                  </span>
                  <span className="px-2 py-0.5 rounded font-bold bg-purple-100 text-purple-800">
                    +{currentQuestion.marks} Marks
                  </span>
                </div>

                <button
                  onClick={() => setZoomImage(resolveImageUrl(currentQuestion.imageUrl))}
                  className="flex items-center gap-1 text-[11px] font-semibold text-purple-700 hover:text-purple-900 bg-purple-50 hover:bg-purple-100 px-2 py-1 rounded transition"
                  title="Zoom Question Slice"
                >
                  <ZoomIn size={13} /> Zoom
                </button>
              </div>

              {/* Question Body: High-resolution Slice */}
              <div className="p-4 sm:p-6 flex flex-col items-center bg-slate-50/50 border-b border-slate-100">
                <div className="relative max-w-full overflow-x-auto rounded-lg bg-white p-2 border border-slate-200 shadow-2xs">
                  <img
                    src={resolveImageUrl(currentQuestion.imageUrl)}
                    onError={(e) => {
                      const target = e.currentTarget;
                      const fallback = getFallbackImageUrl(currentQuestion.imageUrl);
                      if (target.src !== fallback) {
                        target.src = fallback;
                      }
                    }}
                    alt={`Question ${currentQuestion.questionNumber}`}
                    className="max-h-[460px] w-auto object-contain cursor-zoom-in"
                    onClick={() => setZoomImage(resolveImageUrl(currentQuestion.imageUrl))}
                  />
                </div>
              </div>

              {/* Answer Input Section */}
              <div className="p-5 sm:p-6 bg-white space-y-4">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Select or Enter Your Answer:
                </div>

                {/* Case 1: Multiple Choice Question (MCQ) */}
                {currentQuestion.type === 'MCQ' && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {['A', 'B', 'C', 'D'].map((opt) => {
                      const isSelected = selectedOption === opt;
                      let btnStyle = 'border-slate-200 hover:border-purple-400 hover:bg-purple-50/50 text-slate-800';
                      if (isSelected) {
                        btnStyle = 'border-purple-600 bg-purple-50 text-purple-900 ring-2 ring-purple-600/30';
                      }
                      if (isSubmitted) {
                        const isCorrectOption = String(currentQuestion.correctAnswer || '').toUpperCase() === opt;
                        if (isCorrectOption) {
                          btnStyle = 'border-emerald-500 bg-emerald-50 text-emerald-900 ring-2 ring-emerald-500 font-extrabold';
                        } else if (isSelected) {
                          btnStyle = 'border-rose-400 bg-rose-50 text-rose-900 line-through';
                        }
                      }

                      return (
                        <button
                          key={opt}
                          disabled={isSubmitted}
                          onClick={() => setSelectedOption(opt)}
                          className={`p-3.5 rounded-xl border text-sm font-bold flex items-center justify-center gap-2 transition ${btnStyle}`}
                        >
                          <span className="w-6 h-6 rounded-full bg-slate-200/80 flex items-center justify-center text-xs">
                            {opt}
                          </span>
                          <span>Option ({opt})</span>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Case 2: Multiple Select Question (MSQ) */}
                {currentQuestion.type === 'MSQ' && (
                  <div className="space-y-2">
                    <p className="text-xs text-slate-500 italic">Select one or more options that are correct.</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {['A', 'B', 'C', 'D'].map((opt) => {
                        const isChecked = selectedMsqOptions.includes(opt);
                        return (
                          <button
                            key={opt}
                            disabled={isSubmitted}
                            onClick={() => {
                              setSelectedMsqOptions((prev) =>
                                prev.includes(opt) ? prev.filter((x) => x !== opt) : [...prev, opt]
                              );
                            }}
                            className={`p-3.5 rounded-xl border text-sm font-bold flex items-center justify-center gap-2 transition ${
                              isChecked
                                ? 'border-purple-600 bg-purple-50 text-purple-900 ring-2 ring-purple-600/30'
                                : 'border-slate-200 hover:border-purple-400 text-slate-800'
                            }`}
                          >
                            <span className="w-5 h-5 rounded border flex items-center justify-center text-xs">
                              {isChecked ? '✓' : ''}
                            </span>
                            <span>Option ({opt})</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Case 3: Numerical Answer Type (NAT) */}
                {currentQuestion.type === 'NAT' && (
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                      <div className="flex-1">
                        <label className="block text-xs font-semibold text-slate-600 mb-1">
                          Enter Numerical Value:
                        </label>
                        <input
                          type="text"
                          disabled={isSubmitted}
                          placeholder="e.g. 25.5 or -12"
                          value={natAnswer}
                          onChange={(e) => setNatAnswer(e.target.value)}
                          className="w-full px-4 py-2.5 text-base font-mono font-bold rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent bg-slate-50"
                        />
                      </div>
                    </div>

                    {/* Quick On-Screen Numerical Keypad */}
                    {!isSubmitted && (
                      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 max-w-sm">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                          On-Screen Numeric Keypad
                        </div>
                        <div className="grid grid-cols-4 gap-1.5 font-mono text-xs font-bold">
                          {['7', '8', '9', 'BACK', '4', '5', '6', 'CLEAR', '1', '2', '3', '+/-', '0', '.', '00', ''].map(
                            (k, i) =>
                              k ? (
                                <button
                                  key={i}
                                  type="button"
                                  onClick={() => handleKeypadPress(k)}
                                  className="py-2 rounded-lg bg-white border border-slate-200 hover:bg-purple-50 hover:border-purple-300 text-slate-800 active:scale-95 transition"
                                >
                                  {k}
                                </button>
                              ) : (
                                <div key={i} />
                              )
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Instant Answer Reveal Card on Submit */}
                {isSubmitted && (
                  <div
                    className={`rounded-xl p-4 sm:p-5 border transition-all duration-300 space-y-3 ${
                      isCorrect
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                        : 'bg-rose-50 border-rose-300 text-rose-950'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isCorrect ? (
                          <CheckCircle2 size={22} className="text-emerald-600 shrink-0" />
                        ) : (
                          <XCircle size={22} className="text-rose-600 shrink-0" />
                        )}
                        <div>
                          <div className="font-extrabold text-sm sm:text-base">
                            {isCorrect ? 'Correct Answer! (+ ' + currentQuestion.marks + ' Marks)' : 'Incorrect Answer'}
                          </div>
                          <div className="text-xs text-slate-600 mt-0.5">
                            Time Taken: <strong className="font-bold">{formatTime(secondsSpent)}</strong>
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                          Official Key
                        </span>
                        <span className="text-base font-black text-slate-900 font-mono">
                          {Array.isArray(currentQuestion.correctAnswer)
                            ? currentQuestion.correctAnswer.join(', ')
                            : currentQuestion.correctAnswer || 'Provided in PDF'}
                        </span>
                      </div>
                    </div>

                    {currentQuestion.explanation && (
                      <div className="pt-2 border-t border-slate-200/60 text-xs text-slate-700 leading-relaxed">
                        <span className="font-bold text-slate-900">Notes: </span>
                        {currentQuestion.explanation}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Bottom Action Bar: Skip or Submit / Next */}
              <div className="bg-slate-50 border-t border-slate-200 px-5 py-4 flex items-center justify-between gap-3">
                {!isSubmitted ? (
                  <>
                    <button
                      onClick={handleSkipQuestion}
                      className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-bold transition shadow-2xs"
                      title="Skip this question (will reappear in future practice)"
                    >
                      <SkipForward size={14} /> Skip Question
                    </button>

                    <button
                      onClick={handleSubmitAnswer}
                      disabled={!isOptionSelected}
                      className={`inline-flex items-center gap-1.5 px-6 py-2.5 rounded-xl text-xs font-bold transition shadow-md ${
                        isOptionSelected
                          ? 'bg-purple-700 hover:bg-purple-800 text-white cursor-pointer'
                          : 'bg-slate-300 text-slate-500 cursor-not-allowed shadow-none'
                      }`}
                    >
                      <CheckCircle2 size={15} /> Submit Answer
                    </button>
                  </>
                ) : (
                  <>
                    <div className="text-xs text-slate-500 font-medium hidden sm:block">
                      {isCorrect
                        ? 'Mastered! This question will not appear again in this topic.'
                        : 'Recorded in your practice analytics.'}
                    </div>

                    <button
                      onClick={handleNextQuestion}
                      className="ml-auto inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white text-xs font-extrabold transition shadow-md"
                    >
                      <span>Next Question</span>
                      <ChevronRight size={16} />
                    </button>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </main>

      {/* Zoom Modal for diagrams/slices */}
      {zoomImage && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs"
          onClick={() => setZoomImage(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] bg-white rounded-xl p-3 shadow-2xl overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setZoomImage(null)}
              className="absolute top-2 right-2 p-1.5 bg-black/70 hover:bg-black text-white rounded-full transition z-10"
              title="Close Zoom"
            >
              <X size={16} />
            </button>
            <img src={zoomImage} alt="Zoomed Question" className="w-full h-auto object-contain rounded-lg" />
          </div>
        </div>
      )}
    </div>
  );
};
