import React, { useState } from 'react';
import { ArrowLeft, CheckSquare, Square, ShieldCheck } from 'lucide-react';
import type { ExamPaper, UserProfile, Question } from '../../types';
import { getUserProfile } from '../../utils/storage';

interface InstructionsViewProps {
  paper: ExamPaper;
  onStartExam: () => void;
  onCancel: () => void;
}

export const InstructionsView: React.FC<InstructionsViewProps> = ({
  paper,
  onStartExam,
  onCancel,
}) => {
  const [agreed, setAgreed] = useState(false);
  const profile: UserProfile = getUserProfile();

  const allQuestions: Question[] = paper.sections.flatMap((s) => s.questions);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-[#1a56a5] text-white px-6 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <button
            onClick={onCancel}
            className="p-1.5 hover:bg-white/20 rounded-md transition text-white"
            title="Return to Paper Inventory"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="font-bold text-lg leading-tight">{paper.title}</h1>
            <p className="text-xs text-blue-100">
              GATE CBT Examination Platform • Total Duration: {paper.durationMinutes} Minutes
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-semibold">{profile.name}</div>
            <div className="text-[11px] text-blue-200">{profile.branch || 'GATE EC'}</div>
          </div>
          <div className="w-9 h-9 rounded-full bg-white/20 border border-white/30 flex items-center justify-center font-bold text-sm">
            {profile.name ? profile.name.charAt(0).toUpperCase() : 'U'}
          </div>
        </div>
      </header>

      {/* Main Instructions Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 flex flex-col justify-between">
        <div className="bg-white rounded-lg shadow-sm border border-slate-300 p-6 sm:p-8 space-y-6 text-slate-800 text-sm leading-relaxed">
          <div className="border-b pb-3 flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900">General Examination Instructions</h2>
            <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-[#1a56a5] rounded border border-blue-200">
              {allQuestions.length} Questions | {paper.totalMarks} Marks
            </span>
          </div>

          <div className="space-y-4">
            <h3 className="font-bold text-base text-slate-900">Please read the instructions carefully:</h3>
            <ol className="list-decimal list-inside space-y-2.5 pl-2 text-slate-700">
              <li>
                Total duration of this examination is <strong>{paper.durationMinutes} minutes</strong>.
              </li>
              <li>
                The countdown clock will be displayed at the top right of your screen. When the timer
                reaches zero, the exam will end automatically and evaluate your score.
              </li>
              <li>
                The Question Palette on the right of screen shows the status of each question using
                official TCS iON symbols:
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 p-3 bg-slate-50 border rounded-md text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded bg-slate-200 text-slate-700 font-bold flex items-center justify-center border text-[11px]">
                      1
                    </span>
                    <span>Not Visited</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded bg-[#e74c3c] text-white font-bold flex items-center justify-center text-[11px]">
                      2
                    </span>
                    <span>Not Answered</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded bg-[#27ae60] text-white font-bold flex items-center justify-center text-[11px]">
                      3
                    </span>
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-[#8e44ad] text-white font-bold flex items-center justify-center text-[11px]">
                      4
                    </span>
                    <span>Marked for Review</span>
                  </div>
                  <div className="flex items-center gap-2 sm:col-span-2">
                    <div className="relative w-6 h-6 rounded-full bg-[#8e44ad] text-white font-bold flex items-center justify-center text-[11px]">
                      5
                      <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border border-white" />
                    </div>
                    <span>
                      Answered &amp; Marked for Review (<strong>will be evaluated</strong>)
                    </span>
                  </div>
                </div>
              </li>
              <li>
                <strong>Multiple Choice Questions (MCQ):</strong> Select 1 option. Negative marks
                apply (-33% for 1-mark, -67% for 2-mark).
              </li>
              <li>
                <strong>Multiple Select Questions (MSQ):</strong> Select all correct options. No
                partial credit, no negative marking.
              </li>
              <li>
                <strong>Numerical Answer Type (NAT):</strong> Enter real value with virtual numeric
                keypad. No negative marking.
              </li>
              <li>
                An on-screen <strong>GATE Virtual Scientific Calculator</strong> is accessible via
                the top bar calculator button.
              </li>
            </ol>
          </div>

          {/* Declaration check box */}
          <div className="pt-4 border-t border-slate-200">
            <label
              onClick={() => setAgreed(!agreed)}
              className="flex items-start gap-3 p-4 bg-blue-50/70 border border-blue-200 rounded-lg cursor-pointer hover:bg-blue-50 transition select-none"
            >
              <div className="mt-0.5 text-[#1a56a5]">
                {agreed ? <CheckSquare size={20} /> : <Square size={20} />}
              </div>
              <div className="text-xs text-slate-800 leading-normal">
                <strong>Declaration:</strong> I have read and understood all the instructions given
                above. I confirm that I am sitting for the exam under standard test conditions, and I
                understand that leaving or switching tabs may log proctoring alerts.
              </div>
            </label>
          </div>
        </div>

        {/* Bottom actions */}
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={onCancel}
            className="px-5 py-2.5 border border-slate-300 rounded-lg bg-white text-slate-700 font-semibold text-xs hover:bg-slate-50 transition"
          >
            ← Back to Inventory
          </button>

          <button
            onClick={() => {
              if (agreed) onStartExam();
            }}
            disabled={!agreed}
            className={`flex items-center gap-2 px-8 py-3 rounded-lg font-bold text-sm shadow-md transition ${
              agreed
                ? 'bg-[#1a56a5] hover:bg-blue-700 text-white cursor-pointer'
                : 'bg-slate-300 text-slate-500 cursor-not-allowed shadow-none'
            }`}
          >
            <ShieldCheck size={18} />
            I am ready to begin
          </button>
        </div>
      </main>
    </div>
  );
};
