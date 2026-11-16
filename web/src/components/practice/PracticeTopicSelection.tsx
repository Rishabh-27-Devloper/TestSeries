import React, { useState, useMemo } from 'react';
import {
  CheckCircle2,
  BarChart3,
  ArrowLeft,
  Search,
  RotateCcw,
  Play,
  Zap,
  Maximize,
  Minimize,
  Sparkles,
} from 'lucide-react';
import type {
  PracticeIndex,
  PracticeTopicItem,
  UserProfile,
} from '../../types';
import { getPracticeState, resetPracticeTopic } from '../../utils/storage';
import { isFullscreen, toggleFullscreen, subscribeToFullscreen } from '../../utils/fullscreen';

interface PracticeTopicSelectionProps {
  practiceIndex: PracticeIndex;
  profile: UserProfile;
  onSelectTopic: (topic: PracticeTopicItem) => void;
  onBackToPortal: () => void;
  onOpenDashboard: () => void;
  onOpenProfile: () => void;
}

export const PracticeTopicSelection: React.FC<PracticeTopicSelectionProps> = ({
  practiceIndex,
  profile,
  onSelectTopic,
  onBackToPortal,
  onOpenDashboard,
  onOpenProfile,
}) => {
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isFs, setIsFs] = useState(() => isFullscreen());
  const [version, setVersion] = useState(0);

  React.useEffect(() => {
    return subscribeToFullscreen((active) => {
      setIsFs(active);
    });
  }, []);

  // Load user's solved question IDs
  const userPracticeState = useMemo(() => {
    return getPracticeState(profile.name);
  }, [profile.name, version]);

  const solvedSet = useMemo(() => {
    return new Set(userPracticeState.solvedQuestionIds || []);
  }, [userPracticeState]);

  // Aggregate topics across subjects
  const allTopics = useMemo(() => {
    const list: (PracticeTopicItem & { subjectName: string; subjectId: string })[] = [];
    practiceIndex.subjects.forEach((s) => {
      s.topics.forEach((t) => {
        list.push({ ...t, subjectName: s.subjectName, subjectId: s.subjectId });
      });
    });
    return list;
  }, [practiceIndex]);

  // Filtered topics
  const filteredTopics = useMemo(() => {
    return allTopics.filter((t) => {
      if (selectedSubjectId !== 'ALL' && t.subjectId !== selectedSubjectId) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = t.topicName.toLowerCase().includes(q);
        const matchesChapter = t.chapter.toLowerCase().includes(q);
        const matchesSubject = t.subjectName.toLowerCase().includes(q);
        if (!matchesName && !matchesChapter && !matchesSubject) return false;
      }
      return true;
    });
  }, [allTopics, selectedSubjectId, searchQuery]);

  // Overall statistics
  const totalQuestionsAll = practiceIndex.totalQuestions;
  const totalSolvedAll = solvedSet.size;
  const overallPercentage =
    totalQuestionsAll > 0 ? Math.round((totalSolvedAll / totalQuestionsAll) * 100) : 0;

  const handleResetTopic = (e: React.MouseEvent, topic: PracticeTopicItem) => {
    e.stopPropagation();
    if (confirm(`Reset practice progress for "${topic.topicName}"? Solved questions will reappear in practice.`)) {
      resetPracticeTopic(topic.questionIds, profile.name);
      setVersion((v) => v + 1);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* 1. Main Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={onBackToPortal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-bold transition shrink-0 shadow-2xs"
              title="Return to Main Portal"
            >
              <ArrowLeft size={15} />
              <span className="hidden sm:inline">Main Portal</span>
            </button>

            <div className="w-10 h-10 rounded-xl bg-purple-700 text-white flex items-center justify-center font-black text-xl shadow-md shrink-0">
              <Zap size={22} className="text-amber-300" />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="font-extrabold text-slate-900 text-base leading-tight tracking-tight truncate">
                  Practice Mode &bull; Topic DPP Bank
                </h1>
                <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 uppercase tracking-wider">
                  1,900 Questions
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium truncate">
                Forward Stopwatch &bull; Instant Answer Reveal &bull; Mastered Question Filtration
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <button
              onClick={() => toggleFullscreen()}
              className="flex items-center gap-1.5 px-2.5 py-1.5 sm:px-3 sm:py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
              title={isFs ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            >
              {isFs ? <Minimize size={14} className="text-amber-600" /> : <Maximize size={14} className="text-slate-600" />}
              <span className="hidden md:inline">{isFs ? 'Exit Fullscreen' : 'Fullscreen'}</span>
            </button>

            <button
              onClick={onOpenDashboard}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-700 hover:bg-purple-800 text-white transition text-xs font-bold shadow-xs"
              title="View Practice Analytics"
            >
              <BarChart3 size={15} />
              <span className="hidden sm:inline">Practice Analytics</span>
            </button>

            <button
              onClick={onOpenProfile}
              className="flex items-center gap-1.5 p-1.5 sm:px-3 sm:py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition"
              title="Candidate Profile"
            >
              <div className="w-6 h-6 rounded-full bg-purple-700 text-white flex items-center justify-center text-xs font-bold">
                {profile.name ? profile.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="hidden sm:inline font-semibold">{profile.name}</span>
            </button>
          </div>
        </div>
      </header>

      {/* 2. Hero Progress Banner */}
      <section className="bg-purple-900 text-white py-8 px-4 sm:px-6 shadow-sm">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <div className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-white/10 text-white/90 border border-white/20">
              <Sparkles size={14} className="text-amber-300" />
              Topic-wise Daily Practice Problems (DPP)
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Master GATE EC Concepts Topic by Topic
            </h2>
            <p className="text-sm text-purple-200 max-w-2xl leading-relaxed">
              Pick any topic below. Questions pop up randomly with forward stopwatch timers. Submit your
              answer for immediate validation and answer key reveals. Questions solved correctly are permanently
              mastered and will not repeat.
            </p>
          </div>

          {/* Quick Mastery Progress Metric Card */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 sm:p-5 border border-white/20 w-full md:w-80 shrink-0 text-center md:text-left space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider font-bold text-purple-200">Total Mastery</span>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                {overallPercentage}% Completed
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-white">{totalSolvedAll}</span>
              <span className="text-xs text-purple-200">/ {totalQuestionsAll} Questions Solved</span>
            </div>
            <div className="w-full bg-black/30 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-emerald-400 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${overallPercentage}%` }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* 3. Filter & Search Controls */}
      <div className="bg-white border-b border-slate-200 sticky top-16 z-20 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Subject Switcher Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
            <button
              onClick={() => setSelectedSubjectId('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                selectedSubjectId === 'ALL'
                  ? 'bg-purple-700 text-white shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              All Subjects ({allTopics.length})
            </button>
            {practiceIndex.subjects.map((sub) => (
              <button
                key={sub.subjectId}
                onClick={() => setSelectedSubjectId(sub.subjectId)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                  selectedSubjectId === sub.subjectId
                    ? 'bg-purple-700 text-white shadow-xs'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
              >
                {sub.subjectName} ({sub.topicsCount})
              </button>
            ))}
          </div>

          {/* Search Bar */}
          <div className="relative min-w-[240px] sm:min-w-[280px]">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search topic or chapter..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent text-xs text-slate-800 placeholder-slate-400"
            />
          </div>
        </div>
      </div>

      {/* 4. Topic Cards Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex-1 w-full">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Showing {filteredTopics.length} Practice Topics
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredTopics.map((topic) => {
            // Count how many questions in this topic are solved
            const topicSolvedCount = topic.questionIds.filter((qid) => solvedSet.has(qid)).length;
            const topicTotalCount = topic.questionCount;
            const remainingCount = Math.max(0, topicTotalCount - topicSolvedCount);
            const topicPct =
              topicTotalCount > 0 ? Math.round((topicSolvedCount / topicTotalCount) * 100) : 0;
            const isCompleted = topicSolvedCount === topicTotalCount && topicTotalCount > 0;

            return (
              <div
                key={topic.topicId}
                onClick={() => onSelectTopic(topic)}
                className={`group bg-white rounded-xl border p-5 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-2xs hover:shadow-md ${
                  isCompleted
                    ? 'border-emerald-300 hover:border-emerald-500 bg-emerald-50/20'
                    : 'border-slate-200 hover:border-purple-500'
                }`}
              >
                <div>
                  {/* Card Header: Subject Tag & DPP # */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800 truncate">
                      {topic.subjectName}
                    </span>
                    <span className="text-[10px] font-semibold text-slate-500 uppercase">
                      DPP #{topic.dppNumber}
                    </span>
                  </div>

                  {/* Topic Title */}
                  <h3 className="font-bold text-slate-900 text-sm group-hover:text-purple-700 transition leading-snug line-clamp-2">
                    {topic.topicName}
                  </h3>

                  {/* Chapter subtitle */}
                  <p className="text-xs text-slate-500 mt-1 line-clamp-1">
                    {topic.chapter}
                  </p>

                  {/* Badges: Marks & Questions */}
                  <div className="flex items-center gap-2 mt-3 text-[11px] text-slate-600 font-medium">
                    <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 font-bold">
                      {topic.questionCount} Questions
                    </span>
                    <span className="text-slate-400">&bull;</span>
                    <span>{topic.oneMarkCount} (1M)</span>
                    <span className="text-slate-400">&bull;</span>
                    <span>{topic.twoMarkCount} (2M)</span>
                  </div>
                </div>

                {/* Progress Bar & Actions */}
                <div className="mt-5 pt-3 border-t border-slate-100 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500 font-medium">
                      {isCompleted ? (
                        <span className="text-emerald-700 font-bold flex items-center gap-1">
                          <CheckCircle2 size={13} /> Mastered (100%)
                        </span>
                      ) : (
                        <span>
                          <strong className="text-slate-800">{topicSolvedCount}</strong> / {topicTotalCount} Solved ({remainingCount} Left)
                        </span>
                      )}
                    </span>
                    <span className="font-extrabold text-slate-700">{topicPct}%</span>
                  </div>

                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isCompleted ? 'bg-emerald-500' : 'bg-purple-600'
                      }`}
                      style={{ width: `${topicPct}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    {topicSolvedCount > 0 ? (
                      <button
                        onClick={(e) => handleResetTopic(e, topic)}
                        className="text-[11px] text-slate-500 hover:text-rose-600 flex items-center gap-1 font-semibold transition"
                        title="Reset progress to practice all questions again"
                      >
                        <RotateCcw size={12} /> Reset
                      </button>
                    ) : (
                      <span className="text-[11px] text-slate-400">Unattempted</span>
                    )}

                    <button
                      onClick={() => onSelectTopic(topic)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-700 group-hover:bg-purple-800 text-white text-xs font-bold transition shadow-2xs"
                    >
                      <Play size={12} fill="currentColor" />
                      <span>{topicSolvedCount > 0 ? (isCompleted ? 'Review' : 'Resume') : 'Practice'}</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
};
