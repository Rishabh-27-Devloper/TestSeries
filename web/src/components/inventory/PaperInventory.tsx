import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  BarChart3,
  Sparkles,
} from 'lucide-react';
import type { PaperIndexItem, UserProfile } from '../../types';
import { PaperCard } from './PaperCard';
import { getAllAttempts, getUserProfile } from '../../utils/storage';

interface PaperInventoryProps {
  papers: PaperIndexItem[];
  onSelectPaper: (paper: PaperIndexItem) => void;
  onOpenDashboard: () => void;
  onOpenProfile: () => void;
}

const POPULAR_SUBJECTS = [
  'Digital Circuits',
  'Signals and Systems',
  'Control Systems',
  'Analog Circuits',
  'Electronic Devices & Circuits',
  'Communications',
  'Electromagnetics',
  'Networks',
  'Engineering Mathematics',
  'General Aptitude',
  'Full Length (PYQs)',
];

function checkSubjectOrChapterMatch(paper: PaperIndexItem, targetChapter: string): boolean {
  if (targetChapter === 'ALL') return true;

  const t = targetChapter.toLowerCase().trim();
  const s = (paper.subject || '').toLowerCase().trim();
  const c = (paper.chapter || '').toLowerCase().trim();
  const title = (paper.title || '').toLowerCase().trim();
  const cat = (paper.category || '').toLowerCase().trim();

  // Core Subject / Category semantic matchers
  if (t === 'full length (pyqs)' || t === 'full length' || t === 'pyq') {
    return cat === 'pyq' || c.includes('full length') || title.includes('official examination');
  }
  if (t === 'electronic devices & circuits' || t === 'electronic devices') {
    return (
      s.includes('electronic devices') ||
      c.includes('electronic devices') ||
      title.includes('electronic devices') ||
      ['bjt and fet', 'bipolar junction transistor', 'mosfet', 'pn junction', 'semiconductor physics'].includes(c)
    );
  }
  if (t === 'signals and systems' || t === 'signals & systems') {
    return s.includes('signal') || c.includes('signal') || title.includes('signal');
  }
  if (t === 'control systems') {
    return s.includes('control') || c.includes('control') || title.includes('control');
  }
  if (t === 'digital circuits') {
    return s.includes('digital') || c.includes('digital') || title.includes('digital');
  }
  if (t === 'communications' || t === 'communication') {
    return s.includes('communication') || c.includes('communication') || title.includes('communication');
  }
  if (t === 'analog circuits') {
    return s.includes('analog') || c.includes('analog') || title.includes('analog');
  }
  if (t === 'electromagnetics') {
    return (
      s.includes('electromagnet') ||
      c.includes('electromagnet') ||
      title.includes('electromagnet') ||
      ['antennas', 'waveguides', 'transmission lines'].includes(c)
    );
  }
  if (t === 'networks') {
    return s.includes('network') || c.includes('network') || title.includes('network');
  }
  if (t === 'engineering mathematics') {
    return (
      s.includes('math') ||
      c.includes('math') ||
      title.includes('math') ||
      ['calculus', 'linear algebra', 'differential equations', 'probability', 'complex variable', 'transform theory', 'numerical methods'].includes(c)
    );
  }
  if (t === 'general aptitude') {
    return s.includes('aptitude') || c.includes('aptitude') || title.includes('aptitude') || c.includes('verbal') || c.includes('numerical');
  }

  // Exact or contains match on chapter, subject, or title
  return s === t || c === t || s.includes(t) || c.includes(t) || title.includes(t);
}

export const PaperInventory: React.FC<PaperInventoryProps> = ({
  papers,
  onSelectPaper,
  onOpenDashboard,
  onOpenProfile,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChapter, setSelectedChapter] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState<'ALL' | 'ATTEMPTED' | 'UNATTEMPTED'>('ALL');
  const [sortBy, setSortBy] = useState<'DEFAULT' | 'NAME' | 'QUESTIONS' | 'MARKS'>('DEFAULT');
  const [quickViewPaper, setQuickViewPaper] = useState<PaperIndexItem | null>(null);

  const profile: UserProfile = getUserProfile();
  const allAttempts = useMemo(
    () => getAllAttempts(profile.rollNumber),
    [profile.rollNumber]
  );
  const attemptedPaperIds = useMemo(
    () => new Set(allAttempts.map((a) => a.paperId)),
    [allAttempts]
  );

  // Extract unique chapters and topics (excluding 'Full Length')
  const chaptersList = useMemo(() => {
    const set = new Set<string>();
    papers.forEach((p) => {
      if (p.chapter && p.chapter.trim() && p.chapter.trim().toLowerCase() !== 'full length') {
        set.add(p.chapter.trim());
      }
    });
    return Array.from(set).sort();
  }, [papers]);

  // Filter & sort logic
  const filteredPapers = useMemo(() => {
    return papers
      .filter((paper) => {
        // Search term matching
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase().trim();
          const matchName = paper.title.toLowerCase().includes(q);
          const matchChapter = (paper.chapter || '').toLowerCase().includes(q);
          const matchSubject = (paper.subject || '').toLowerCase().includes(q);
          const matchId = paper.paperId.toLowerCase().includes(q);
          if (!matchName && !matchChapter && !matchSubject && !matchId) return false;
        }

        // Chapter & Subject filter
        if (!checkSubjectOrChapterMatch(paper, selectedChapter)) {
          return false;
        }

        // Status filter
        const isAttempted = attemptedPaperIds.has(paper.paperId);
        if (selectedStatus === 'ATTEMPTED' && !isAttempted) return false;
        if (selectedStatus === 'UNATTEMPTED' && isAttempted) return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'NAME') return a.title.localeCompare(b.title);
        if (sortBy === 'QUESTIONS') return b.totalQuestions - a.totalQuestions;
        if (sortBy === 'MARKS') return b.totalMarks - a.totalMarks;
        return 0;
      });
  }, [papers, searchQuery, selectedChapter, selectedStatus, sortBy, attemptedPaperIds]);

  // Aggregate stats
  const totalQuestions = useMemo(
    () => papers.reduce((sum, p) => sum + (p.totalQuestions || 0), 0),
    [papers]
  );
  const totalHours = useMemo(
    () => Math.round(papers.reduce((sum, p) => sum + (p.durationMinutes || 0), 0) / 60),
    [papers]
  );

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Main Navigation Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#1a56a5] text-white flex items-center justify-center font-black text-xl shadow-xs">
              G
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-slate-900 text-lg leading-tight">GATE CBT Exam Portal</h1>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                  {profile.branch ? profile.branch.split(' ')[0] : 'EC'} 2025/2026
                </span>
              </div>
              <p className="text-xs text-slate-500">Official TCS iON Architecture &amp; Grading Standards</p>
            </div>
          </div>

          {/* User & Dashboard Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenDashboard}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-slate-200 hover:border-blue-400 bg-white hover:bg-blue-50/50 text-slate-700 text-xs font-semibold transition"
            >
              <BarChart3 size={15} className="text-[#1a56a5]" />
              <span className="hidden sm:inline">Analytics &amp; History</span>
            </button>

            <button
              onClick={onOpenProfile}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition"
              title="Edit Profile"
            >
              <div className="w-6 h-6 rounded-full bg-[#1a56a5] text-white flex items-center justify-center text-xs font-bold">
                {profile.name ? profile.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="hidden md:inline font-semibold text-slate-800">{profile.name}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Stats Banner */}
      <section className="bg-gradient-to-r from-[#1a56a5] via-blue-800 to-indigo-900 text-white py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-400/20 text-blue-200 border border-blue-300/30">
              <Sparkles size={13} className="text-amber-300" />
              100+ Hours of GATE CBT Practice Compiled
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Test Series &amp; Full Syllabus Mock Papers
            </h2>
            <p className="text-sm text-blue-100 max-w-2xl leading-relaxed">
              Standardized with official GATE markings (+1, +2, -0.33, -0.67), MSQ multi-select validation,
              NAT decimal range checks, and full virtual scientific calculator.
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full md:w-auto">
            <div className="bg-white/10 backdrop-blur-xs rounded-lg p-3 text-center border border-white/10">
              <div className="text-2xl font-black">{papers.length}</div>
              <div className="text-[11px] text-blue-200 uppercase font-medium">Test Papers</div>
            </div>
            <div className="bg-white/10 backdrop-blur-xs rounded-lg p-3 text-center border border-white/10">
              <div className="text-2xl font-black">{attemptedPaperIds.size}</div>
              <div className="text-[11px] text-emerald-300 uppercase font-medium">Attempted</div>
            </div>
            <div className="bg-white/10 backdrop-blur-xs rounded-lg p-3 text-center border border-white/10">
              <div className="text-2xl font-black">{totalQuestions.toLocaleString()}+</div>
              <div className="text-[11px] text-blue-200 uppercase font-medium">Questions</div>
            </div>
            <div className="bg-white/10 backdrop-blur-xs rounded-lg p-3 text-center border border-white/10">
              <div className="text-2xl font-black">{totalHours}h+</div>
              <div className="text-[11px] text-amber-300 uppercase font-medium">Practice</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Filter & Inventory Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Controls Bar: Search & Filters */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
            {/* Search Input */}
            <div className="relative md:col-span-5">
              <Search
                size={16}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by topic, chapter, subject (e.g. Boolean, FFT, EDC)..."
                className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-[#1a56a5] focus:border-transparent outline-none text-slate-800 placeholder-slate-400"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Chapter Filter Dropdown */}
            <div className="md:col-span-4">
              <div className="relative">
                <select
                  value={selectedChapter}
                  onChange={(e) => setSelectedChapter(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-[#1a56a5] outline-none text-slate-800 bg-white"
                >
                  <option value="ALL">📚 All Subjects &amp; Chapters ({papers.length} Papers)</option>
                  <optgroup label="Core Subjects">
                    {POPULAR_SUBJECTS.map((subj) => (
                      <option key={subj} value={subj}>
                        {subj}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="Specific Chapters &amp; Topics">
                    {chaptersList.map((chap) => (
                      <option key={chap} value={chap}>
                        {chap}
                      </option>
                    ))}
                  </optgroup>
                </select>
              </div>
            </div>

            {/* Status Filter */}
            <div className="md:col-span-3">
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value as any)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-[#1a56a5] outline-none text-slate-800 bg-white font-medium"
              >
                <option value="ALL">⚡ All Tests ({papers.length})</option>
                <option value="ATTEMPTED">✓ Attempted Only ({attemptedPaperIds.size})</option>
                <option value="UNATTEMPTED">○ Unattempted Only ({papers.length - attemptedPaperIds.size})</option>
              </select>
            </div>
          </div>

          {/* Quick Filter Pill Chips */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
            <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar w-full sm:w-auto py-1">
              <span className="font-semibold text-slate-700 flex items-center gap-1 shrink-0">
                <Filter size={12} /> Popular:
              </span>
              {POPULAR_SUBJECTS.map((subj) => {
                const isSelected = selectedChapter === subj;
                return (
                  <button
                    key={subj}
                    onClick={() => setSelectedChapter(isSelected ? 'ALL' : subj)}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition shrink-0 whitespace-nowrap ${
                      isSelected
                        ? 'bg-[#1a56a5] text-white shadow-xs font-semibold'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {subj}
                  </button>
                );
              })}
            </div>

            <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
              <span className="text-slate-500">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="text-xs border border-slate-200 rounded px-2 py-1 bg-white outline-none text-slate-700 font-medium"
              >
                <option value="DEFAULT">Default Order</option>
                <option value="NAME">Paper Name (A-Z)</option>
                <option value="QUESTIONS">Question Count (High-Low)</option>
                <option value="MARKS">Total Marks (High-Low)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Papers Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <div className="flex items-center flex-wrap gap-2">
              <span>
                Showing <strong className="text-slate-900">{filteredPapers.length}</strong> of{' '}
                {papers.length} papers
              </span>
              {selectedChapter !== 'ALL' && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-800 font-semibold text-[11px] border border-blue-200">
                  <span>Filtered: {selectedChapter}</span>
                  <button
                    onClick={() => setSelectedChapter('ALL')}
                    className="hover:text-blue-950 font-bold ml-1 text-sm leading-none"
                    title="Remove filter"
                  >
                    ×
                  </button>
                </span>
              )}
            </div>
            {(selectedChapter !== 'ALL' || selectedStatus !== 'ALL' || searchQuery) && (
              <button
                onClick={() => {
                  setSelectedChapter('ALL');
                  setSelectedStatus('ALL');
                  setSearchQuery('');
                }}
                className="text-blue-600 hover:underline font-medium"
              >
                Reset All Filters
              </button>
            )}
          </div>

          {filteredPapers.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
                <Search size={24} />
              </div>
              <h3 className="font-bold text-slate-800 text-base">No Matching Papers Found</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No papers matched your current search filters. Try adjusting your search keyword or chapter selection.
              </p>
              <button
                onClick={() => {
                  setSelectedChapter('ALL');
                  setSelectedStatus('ALL');
                  setSearchQuery('');
                }}
                className="px-4 py-2 bg-[#1a56a5] text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition"
              >
                Clear Search &amp; Show All
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredPapers.map((paper) => (
                <PaperCard
                  key={paper.paperId}
                  paper={paper}
                  onSelect={onSelectPaper}
                  onQuickView={(p) => setQuickViewPaper(p)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Quick View Pattern Modal */}
      {quickViewPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base">{quickViewPaper.title}</h3>
              <button
                onClick={() => setQuickViewPaper(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-600">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Subject / Chapter:</span>
                <span>{quickViewPaper.chapter || quickViewPaper.subject}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Total Questions:</span>
                <span className="font-bold text-slate-900">{quickViewPaper.totalQuestions} Questions</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Total Maximum Marks:</span>
                <span className="font-bold text-slate-900">{quickViewPaper.totalMarks} Marks</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Allotted Duration:</span>
                <span className="font-bold text-slate-900">{quickViewPaper.durationMinutes} Minutes</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Grading Scheme:</span>
                <span>GATE Standard (+1, +2, -0.33, -0.67)</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                onClick={() => setQuickViewPaper(null)}
                className="px-4 py-2 border border-slate-300 rounded text-xs font-semibold text-slate-700 hover:bg-slate-100"
              >
                Close
              </button>
              <button
                onClick={() => {
                  const p = quickViewPaper;
                  setQuickViewPaper(null);
                  onSelectPaper(p);
                }}
                className="px-5 py-2 bg-[#1a56a5] hover:bg-blue-700 text-white rounded text-xs font-semibold"
              >
                Start Examination ➔
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          <p>© 2026 GATE CBT Examination System. Designed according to official TCS iON CBT Specifications.</p>
          <p className="mt-1 text-slate-400">
            Electronic Devices, Communications, Signals &amp; Systems, Digital Electronics, Controls &amp; Mathematics.
          </p>
        </div>
      </footer>
    </div>
  );
};
