import React from 'react';
import { Clock, HelpCircle, Award, CheckCircle2, RotateCcw, ArrowRight, BookOpen } from 'lucide-react';
import type { PaperIndexItem } from '../../types';
import { getAttemptsSummaryForPaper } from '../../utils/storage';

interface PaperCardProps {
  paper: PaperIndexItem;
  onSelect: (paper: PaperIndexItem) => void;
  onQuickView?: (paper: PaperIndexItem) => void;
}

export const PaperCard: React.FC<PaperCardProps> = ({ paper, onSelect, onQuickView }) => {
  const summary = getAttemptsSummaryForPaper(paper.paperId);
  const isAttempted = summary.attemptCount > 0;
  const last = summary.lastAttempt;
  const best = summary.bestAttempt;

  return (
    <div
      className={`group flex flex-col justify-between bg-white rounded-lg transition-all duration-200 shadow-xs hover:shadow-md ${
        isAttempted
          ? 'border-2 border-emerald-500/80 bg-gradient-to-b from-emerald-50/20 to-white'
          : 'border border-slate-200 hover:border-blue-400'
      }`}
    >
      <div className="p-5">
        {/* Top badges bar */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-100 text-[#1a56a5] border border-blue-200 truncate max-w-[160px]">
            {paper.chapter || paper.subject || 'GATE EC'}
          </span>

          {isAttempted ? (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-300">
              <CheckCircle2 size={12} className="text-emerald-700" />
              ATTEMPTED ({summary.attemptCount}x)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
              NOT ATTEMPTED
            </span>
          )}
        </div>

        {/* Exam Title */}
        <h3
          className="font-bold text-slate-900 text-base leading-snug line-clamp-2 min-h-[2.75rem] group-hover:text-[#1a56a5] transition-colors"
          title={paper.title}
        >
          {paper.title}
        </h3>

        {/* Paper Quick Specs */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 mt-3 pt-3 border-t border-slate-100 text-xs text-slate-600">
          <div className="flex items-center gap-1">
            <HelpCircle size={14} className="text-slate-400" />
            <span>
              <strong className="text-slate-800">{paper.totalQuestions}</strong> Questions
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Award size={14} className="text-slate-400" />
            <span>
              <strong className="text-slate-800">{paper.totalMarks}</strong> Marks
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Clock size={14} className="text-slate-400" />
            <span>
              <strong className="text-slate-800">{paper.durationMinutes}</strong> mins
            </span>
          </div>
        </div>

        {/* Attempt Statistics Subsection - ONLY SHOWN IF ATTEMPTED */}
        {isAttempted && last && best && (
          <div className="mt-3.5 pt-3 border-t border-emerald-100 bg-emerald-50/50 rounded-lg p-2.5 space-y-2 text-xs">
            {/* Last Attempt */}
            <div className="flex items-center justify-between">
              <span className="text-slate-600 font-medium">Last Attempt:</span>
              <div className="text-right">
                <span className="font-bold text-slate-900">
                  {last.scoreObtained.toFixed(2)} / {last.totalMarks}
                </span>{' '}
                <span className="text-[11px] text-slate-500">
                  ({last.percentageScore.toFixed(1)}% | {last.accuracyPercentage.toFixed(0)}% acc)
                </span>
              </div>
            </div>

            {/* Best Attempt */}
            <div className="flex items-center justify-between">
              <span className="text-emerald-800 font-semibold flex items-center gap-1">
                <Award size={12} className="text-emerald-600" /> Best Score:
              </span>
              <div className="text-right">
                <span className="font-bold text-emerald-900">
                  {best.scoreObtained.toFixed(2)} / {best.totalMarks}
                </span>{' '}
                <span className="text-[11px] text-emerald-700">
                  ({best.percentageScore.toFixed(1)}% | {best.accuracyPercentage.toFixed(0)}% acc)
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="p-4 bg-slate-50/80 border-t border-slate-100 rounded-b-lg flex items-center justify-between gap-2">
        {onQuickView ? (
          <button
            onClick={() => onQuickView(paper)}
            className="px-2.5 py-1.5 text-xs text-slate-600 hover:text-blue-700 font-medium flex items-center gap-1 hover:bg-slate-200/60 rounded transition"
            title="Preview pattern and syllabus"
          >
            <BookOpen size={13} />
            Pattern
          </button>
        ) : (
          <span className="text-[11px] text-slate-400 font-mono truncate">
            {paper.paperId.slice(0, 18)}...
          </span>
        )}

        <button
          onClick={() => onSelect(paper)}
          className={`flex items-center justify-center gap-1.5 px-4 py-2 rounded font-semibold text-xs transition shadow-xs ${
            isAttempted
              ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
              : 'bg-[#1a56a5] hover:bg-blue-700 text-white'
          }`}
        >
          {isAttempted ? (
            <>
              <RotateCcw size={13} />
              Retake Test
            </>
          ) : (
            <>
              Start Test
              <ArrowRight size={13} />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
