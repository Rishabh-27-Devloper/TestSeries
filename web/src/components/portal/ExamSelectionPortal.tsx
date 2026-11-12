import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  Stethoscope,
  CheckCircle2,
  BarChart3,
  User,
  ShieldCheck,
  ChevronRight,
  BookOpen,
  HelpCircle,
  Clock,
  Calculator,
  Ban,
  Layers,
  Maximize,
  Minimize,
} from 'lucide-react';
import type { PaperIndexItem, UserProfile } from '../../types';
import { isFullscreen, toggleFullscreen, subscribeToFullscreen } from '../../utils/fullscreen';

interface ExamSelectionPortalProps {
  papers: PaperIndexItem[];
  profile: UserProfile;
  onSelectExam: (exam: 'GATE' | 'NEET') => void;
  onOpenDashboard: () => void;
  onOpenProfile: () => void;
}

export const ExamSelectionPortal: React.FC<ExamSelectionPortalProps> = ({
  papers,
  profile,
  onSelectExam,
  onOpenDashboard,
  onOpenProfile,
}) => {
  const gatePapers = papers.filter((p) => (p.examType || 'GATE').toUpperCase() === 'GATE');
  const neetPapers = papers.filter((p) => {
    const et = (p.examType || '').toUpperCase();
    return et === 'NEET' || et === 'NEET UG';
  });

  const [isFs, setIsFs] = useState(() => isFullscreen());

  useEffect(() => {
    return subscribeToFullscreen((active) => {
      setIsFs(active);
    });
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* 1. Global Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#1a56a5] text-white flex items-center justify-center font-black text-xl shadow-md">
              C
            </div>
            <div>
              <div className="font-extrabold text-slate-900 text-base leading-tight tracking-tight">
                CBT Examination Simulator
              </div>
              <div className="text-[11px] text-slate-500 font-medium">
                Offline Test Series Platform &bull; Multi-Exam Portal (Layer 1)
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={() => toggleFullscreen()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition text-slate-700 text-xs font-semibold"
              title={isFs ? 'Exit Full Screen' : 'Enter Full Screen'}
            >
              {isFs ? <Minimize size={15} className="text-amber-600" /> : <Maximize size={15} className="text-slate-600" />}
              <span className="hidden sm:inline">{isFs ? 'Exit Fullscreen' : 'Fullscreen'}</span>
            </button>

            <button
              onClick={onOpenProfile}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition text-slate-700 text-xs font-semibold"
              title="Edit Profile"
            >
              <User size={15} className="text-[#1a56a5]" />
              <span className="hidden sm:inline">{profile.name || 'Candidate'}</span>
            </button>

            <button
              onClick={onOpenDashboard}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a56a5] hover:bg-blue-700 text-white transition text-xs font-bold shadow-xs"
              title="View Performance Analytics"
            >
              <BarChart3 size={15} />
              <span className="hidden sm:inline">Performance Dashboard</span>
            </button>
          </div>
        </div>
      </header>

      {/* 2. Hero Banner (Solid Color, No AI Gradient) */}
      <section className="bg-[#1a56a5] text-white py-10 px-4 sm:px-6 shadow-sm">
        <div className="max-w-5xl mx-auto text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-white/90 border border-white/20 text-xs font-semibold uppercase tracking-wider">
            <Layers size={14} /> Official Examination Gateway (Layer 1)
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Select Examination Portal
          </h1>
          <p className="text-sm sm:text-base text-blue-100 max-w-2xl mx-auto leading-relaxed">
            Choose your target competitive examination below. Papers, question palettes, scoring rules,
            and past attempt analytics are completely separated into dedicated portals.
          </p>
        </div>
      </section>

      {/* 3. Exam Cards Grid */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 -mt-6 pb-12 flex-1 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ========================================================================= */}
          {/* CARD 1: GATE EC */}
          {/* ========================================================================= */}
          <div className="bg-white rounded-2xl border-2 border-slate-200 hover:border-blue-500 shadow-md hover:shadow-xl transition-all duration-200 flex flex-col overflow-hidden">
            <div className="p-6 sm:p-7 flex-1 flex flex-col justify-between space-y-5">
              {/* Header Badge & Counts */}
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase bg-blue-50 text-blue-800 border border-blue-200">
                    ★ Primary &amp; Active
                  </span>
                  <span className="text-xs font-bold text-slate-500">
                    <strong className="text-blue-900 font-extrabold text-sm">{gatePapers.length}</strong> Papers Available
                  </span>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 rounded-xl bg-blue-100 text-[#1a56a5] flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <GraduationCap size={26} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 leading-snug">
                      GATE (Graduate Aptitude Test in Engineering)
                    </h2>
                    <p className="text-xs text-blue-700 font-semibold mt-0.5">
                      Electronics &amp; Communication Engineering (EC)
                    </p>
                  </div>
                </div>

                <p className="text-xs text-slate-600 mt-3 leading-relaxed">
                  Official Previous Year Papers (PYQ 2000–2026) and 72 Topic-wise Chapter Tests with full
                  formulas, high-resolution diagram slices, virtual scientific calculator, and TCS iON layout.
                </p>
              </div>

              {/* Overview Chips */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-50 text-blue-900 font-semibold border border-blue-100">
                  <Clock size={13} className="text-blue-700" /> 31 Full-Length PYQs
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sky-50 text-sky-900 font-semibold border border-sky-100">
                  <BookOpen size={13} className="text-sky-700" /> 72 Topic-Wise Tests
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 font-semibold border border-emerald-100">
                  <HelpCircle size={13} className="text-emerald-700" /> 4,780+ Questions
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-900 font-semibold border border-indigo-100">
                  <Calculator size={13} className="text-indigo-700" /> Virtual Calculator Allowed
                </span>
              </div>

              {/* Feature Checklist */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-2 text-xs text-slate-700">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-emerald-600 shrink-0" />
                  <span>Strict TCS iON Examination Interface &amp; Countdown Timer</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-emerald-600 shrink-0" />
                  <span>Official GATE TCS iON Scientific Virtual Calculator Included</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-emerald-600 shrink-0" />
                  <span>Automatic Negative Marking (+1/+2, -0.33/-0.67 penalties)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-emerald-600 shrink-0" />
                  <span>Full support for MCQ, MSQ &amp; NAT Numerical questions</span>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => onSelectExam('GATE')}
                className="w-full py-3.5 px-6 rounded-xl bg-[#1a56a5] hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-sm transition-all duration-150 flex items-center justify-center gap-2 shadow-sm hover:shadow"
              >
                <span>Enter GATE Portal</span>
                <ChevronRight size={18} />
              </button>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* CARD 2: NEET UG */}
          {/* ========================================================================= */}
          <div className="bg-white rounded-2xl border-2 border-slate-200 hover:border-teal-500 shadow-md hover:shadow-xl transition-all duration-200 flex flex-col overflow-hidden">
            <div className="p-6 sm:p-7 flex-1 flex flex-col justify-between space-y-5">
              {/* Header Badge & Counts */}
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase bg-teal-50 text-teal-800 border border-teal-200">
                    🩺 Medical CBT 2026+
                  </span>
                  <span className="text-xs font-bold text-slate-500">
                    <strong className="text-teal-900 font-extrabold text-sm">{neetPapers.length}</strong> Papers Available
                  </span>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 rounded-xl bg-teal-100 text-[#0d9488] flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <Stethoscope size={26} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 leading-snug">
                      NEET UG (National Eligibility cum Entrance Test)
                    </h2>
                    <p className="text-xs text-teal-700 font-semibold mt-0.5">
                      Undergraduate Pre-Medical Entrance Examination
                    </p>
                  </div>
                </div>

                <p className="text-xs text-slate-600 mt-3 leading-relaxed">
                  Official Full-Length PYQs (AIPMT 1988–2026) and 95 Topic-wise Physics, Chemistry, and
                  Biology chapter tests adhering strictly to the latest NTA Computer-Based Testing guidelines.
                </p>
              </div>

              {/* Overview Chips */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-teal-50 text-teal-900 font-semibold border border-teal-100">
                  <Clock size={13} className="text-teal-700" /> 51 Full-Length PYQs
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-900 font-semibold border border-emerald-100">
                  <BookOpen size={13} className="text-emerald-700" /> 95 Topic-Wise Tests
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-cyan-50 text-cyan-900 font-semibold border border-cyan-100">
                  <HelpCircle size={13} className="text-cyan-700" /> 18,870+ Questions
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 text-amber-900 font-semibold border border-amber-200">
                  <ShieldCheck size={13} className="text-amber-700" /> ⚠️ 15 Out of Syllabus Tagged
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-rose-50 text-rose-900 font-semibold border border-rose-200">
                  <Ban size={13} className="text-rose-700" /> No Calculator (Strict NTA Mode)
                </span>
              </div>

              {/* Feature Checklist */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-2 text-xs text-slate-700">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-teal-600 shrink-0" />
                  <span>Full AIPMT / NEET UG PYQ Archive (1988 through 2026)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-teal-600 shrink-0" />
                  <span>95 Topic-wise Tests (Physics, Chemistry &amp; Biology / Botany / Zoology)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-teal-600 shrink-0" />
                  <span>Standard NTA +4.0 / -1.0 Negative Evaluation Scheme</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-teal-600 shrink-0" />
                  <span>15 Out-of-Syllabus Chapters Tagged &amp; Badged for Practice</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-teal-600 shrink-0" />
                  <span>Virtual Calculator disabled in accordance with NEET examination rules</span>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => onSelectExam('NEET')}
                className="w-full py-3.5 px-6 rounded-xl bg-[#0d9488] hover:bg-teal-700 active:bg-teal-800 text-white font-bold text-sm transition-all duration-150 flex items-center justify-center gap-2 shadow-sm hover:shadow"
              >
                <span>Enter NEET Portal</span>
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Security & System Info Footer Note */}
        <div className="mt-8 p-4 bg-white rounded-xl border border-slate-200 text-slate-500 text-xs flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-emerald-600 shrink-0" />
            <span>
              <strong>Private &amp; Offline Isolated:</strong> Test scores, timings, and question responses are saved
              securely in your browser's private local storage.
            </span>
          </div>
          <div className="text-[11px] text-slate-400">
            Total 249 Examination Papers &bull; 23,650+ Questions
          </div>
        </div>
      </main>
    </div>
  );
};
