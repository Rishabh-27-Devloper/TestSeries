import React, { useState, useMemo } from 'react';
import {
  Clock,
  CheckCircle2,
  XCircle,
  SkipForward,
  Award,
  Zap,
  Search,
  Layers,
} from 'lucide-react';
import type { UserProfile } from '../../types';
import { getPracticeStats } from '../../utils/storage';

interface PracticeAnalyticsViewProps {
  profile: UserProfile;
}

const SUBJECT_OPTIONS = [
  { id: 'ALL', label: 'All Subjects' },
  { id: 'Digital Electronics', label: 'Digital' },
  { id: 'Control System', label: 'Control' },
  { id: 'Signal and System', label: 'Signals' },
  { id: 'Network Theory', label: 'Networks' },
  { id: 'Analog Electronics', label: 'Analog' },
  { id: 'Communication Systems', label: 'Comm' },
];

export const PracticeAnalyticsView: React.FC<PracticeAnalyticsViewProps> = ({ profile }) => {
  const [selectedSubject, setSelectedSubject] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'CORRECT' | 'WRONG' | 'SKIPPED'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Load stats
  const stats = useMemo(() => {
    return getPracticeStats(profile.name, selectedSubject === 'ALL' ? undefined : selectedSubject);
  }, [profile.name, selectedSubject]);

  // Format seconds to text (e.g. 45s, 1m 20s)
  const formatTime = (secs: number) => {
    if (!secs || secs <= 0) return '0s';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    if (m === 0) return `${s}s`;
    return `${m}m ${s}s`;
  };

  // Filter history log
  const filteredHistory = useMemo(() => {
    return stats.history.filter((h) => {
      if (statusFilter !== 'ALL' && h.status !== statusFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesQid = h.questionId.toLowerCase().includes(q);
        const matchesTopic = h.topic.toLowerCase().includes(q);
        const matchesSub = h.subject.toLowerCase().includes(q);
        if (!matchesQid && !matchesTopic && !matchesSub) return false;
      }
      return true;
    });
  }, [stats.history, statusFilter, searchQuery]);

  return (
    <div className="space-y-6">
      {/* 1. KPI Metric Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Questions Encountered */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Encountered</span>
            <Layers size={15} className="text-purple-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{stats.encounteredCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Total Practice Views</div>
        </div>

        {/* Questions Answered */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Answered</span>
            <CheckCircle2 size={15} className="text-blue-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{stats.answeredCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {stats.skippedCount} Skipped ({stats.encounteredCount > 0 ? Math.round((stats.skippedCount / stats.encounteredCount) * 100) : 0}%)
          </div>
        </div>

        {/* Accuracy Rate */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Accuracy</span>
            <Award size={15} className="text-amber-500" />
          </div>
          <div className="text-2xl font-black text-purple-700">{stats.accuracyPercentage}%</div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            <span className="text-emerald-600 font-bold">{stats.correctCount} Correct</span> &bull;{' '}
            <span className="text-rose-600 font-bold">{stats.wrongCount} Wrong</span>
          </div>
        </div>

        {/* 1-Mark Average Time */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">1-Mark Avg Time</span>
            <Clock size={15} className="text-indigo-600" />
          </div>
          <div className="text-2xl font-black text-indigo-700">{formatTime(stats.avgTime1MarkSeconds)}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Conceptual / Short</div>
        </div>

        {/* 2-Mark Average Time */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">2-Mark Avg Time</span>
            <Clock size={15} className="text-purple-600" />
          </div>
          <div className="text-2xl font-black text-purple-800">{formatTime(stats.avgTime2MarkSeconds)}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Complex / Numerical</div>
        </div>
      </div>

      {/* 2. Secondary Analytics Row: Time Extremes & Solved Questions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-purple-100 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-purple-900">Overall Average Time</div>
            <div className="text-2xl font-black text-purple-950 mt-1">{formatTime(stats.avgTimeSeconds)}</div>
            <div className="text-xs text-purple-700 mt-0.5">Across all attempted questions</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-200/60 flex items-center justify-center text-purple-800">
            <Clock size={24} />
          </div>
        </div>

        <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl border border-emerald-100 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-emerald-900">Fastest (Min Time)</div>
            <div className="text-2xl font-black text-emerald-950 mt-1">{formatTime(stats.minTimeSeconds)}</div>
            <div className="text-xs text-emerald-700 mt-0.5">Quickest correct deliberation</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-200/60 flex items-center justify-center text-emerald-800">
            <Zap size={24} />
          </div>
        </div>

        <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-100 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-amber-900">Longest (Max Time)</div>
            <div className="text-2xl font-black text-amber-950 mt-1">{formatTime(stats.maxTimeSeconds)}</div>
            <div className="text-xs text-amber-700 mt-0.5">Most deliberate problem solving</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-200/60 flex items-center justify-center text-amber-800">
            <Clock size={24} />
          </div>
        </div>
      </div>

      {/* 3. Detailed Per-Question Time History Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Table Filter Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          <div>
            <h3 className="font-extrabold text-slate-900 text-base leading-tight">
              Per-Question Practice Time History
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Each question has its individually recorded forward time, marks, and response status
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Subject Filter */}
            <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 text-xs overflow-x-auto max-w-full">
              {SUBJECT_OPTIONS.map((sub) => (
                <button
                  key={sub.id}
                  onClick={() => setSelectedSubject(sub.id)}
                  className={`px-2 py-1 rounded-md font-semibold transition whitespace-nowrap ${
                    selectedSubject === sub.id ? 'bg-purple-700 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {sub.label}
                </button>
              ))}
            </div>

            {/* Status Filter */}
            <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 text-xs">
              {(['ALL', 'CORRECT', 'WRONG', 'SKIPPED'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-md font-semibold transition ${
                    statusFilter === st ? 'bg-purple-700 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {st === 'ALL' ? 'All' : st}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative min-w-[180px]">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search history..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-purple-600"
              />
            </div>
          </div>
        </div>

        {/* History Table */}
        <div className="overflow-x-auto">
          {filteredHistory.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs space-y-2">
              <Clock size={32} className="mx-auto text-slate-300" />
              <p className="font-medium text-slate-600">No practice attempts recorded matching the filters.</p>
              <p className="text-[11px]">Start a practice session from Practice Mode to log your question times!</p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Time &amp; Date</th>
                  <th className="py-3 px-4">Question ID</th>
                  <th className="py-3 px-4">Subject &bull; Topic</th>
                  <th className="py-3 px-4 text-center">Marks</th>
                  <th className="py-3 px-4 text-center">Type</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right font-extrabold">Recorded Time</th>
                  <th className="py-3 px-4 text-center">Answer / Key</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredHistory.map((h) => {
                  let statusBadge = (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                      <SkipForward size={11} /> Skipped
                    </span>
                  );
                  if (h.status === 'CORRECT') {
                    statusBadge = (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        <CheckCircle2 size={11} /> Correct
                      </span>
                    );
                  } else if (h.status === 'WRONG') {
                    statusBadge = (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                        <XCircle size={11} /> Wrong
                      </span>
                    );
                  }

                  const dateFormatted = new Date(h.timestamp).toLocaleDateString([], {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  });

                  return (
                    <tr key={h.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3 px-4 text-slate-500 whitespace-nowrap">{dateFormatted}</td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-800 whitespace-nowrap">
                        {h.questionId}
                      </td>
                      <td className="py-3 px-4 max-w-xs truncate">
                        <div className="font-bold text-slate-900 truncate">{h.topic}</div>
                        <div className="text-[10px] text-slate-400 truncate">{h.subject}</div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          h.marks === 1 ? 'bg-indigo-50 text-indigo-700' : 'bg-purple-50 text-purple-800'
                        }`}>
                          {h.marks}M
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                          {h.type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center whitespace-nowrap">{statusBadge}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1">
                          <Clock size={12} className="text-slate-400" />
                          {formatTime(h.timeSpentSeconds)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center text-slate-700">
                        {h.status === 'SKIPPED' ? (
                          <span className="text-slate-400 italic text-[11px]">—</span>
                        ) : (
                          <span className="font-mono text-xs font-semibold">
                            {Array.isArray(h.userResponse) ? h.userResponse.join(',') : h.userResponse || '—'}
                            {h.correctAnswer && (
                              <span className="text-slate-400 text-[10px] ml-1">
                                (Key: {Array.isArray(h.correctAnswer) ? h.correctAnswer.join(',') : h.correctAnswer})
                              </span>
                            )}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
