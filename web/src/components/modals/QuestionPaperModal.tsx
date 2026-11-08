import React from 'react';
import { X, FileText } from 'lucide-react';
import type { ExamPaper, Question } from '../../types';
import { resolveImageUrl, getFallbackImageUrl } from '../../utils/storage';

interface QuestionPaperModalProps {
  isOpen: boolean;
  paper: ExamPaper | null;
  onClose: () => void;
  onJumpToQuestion?: (qIndex: number) => void;
}

export const QuestionPaperModal: React.FC<QuestionPaperModalProps> = ({
  isOpen,
  paper,
  onClose,
  onJumpToQuestion,
}) => {
  if (!isOpen || !paper) return null;

  const allQuestions: Question[] = paper.sections.flatMap((s) => s.questions);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="flex flex-col bg-white rounded-lg shadow-2xl max-w-5xl w-full h-[90vh] overflow-hidden border border-slate-300">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#1a56a5] text-white">
          <div className="flex items-center gap-2">
            <FileText size={20} />
            <h2 className="font-semibold text-lg">Question Paper - {paper.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-red-500 rounded transition text-white"
            title="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Info bar */}
        <div className="bg-blue-50 px-5 py-2.5 border-b border-blue-100 flex flex-wrap items-center justify-between text-xs text-blue-900 font-medium">
          <div>
            Total Questions: <span className="font-bold">{allQuestions.length}</span> | Total Marks:{' '}
            <span className="font-bold">{paper.totalMarks}</span> | Duration:{' '}
            <span className="font-bold">{paper.durationMinutes} mins</span>
          </div>
          <div className="text-slate-600">
            Click &quot;Go to Question&quot; on any item to jump directly to it in the test interface.
          </div>
        </div>

        {/* Scrollable Questions list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50">
          {allQuestions.map((q: Question, idx: number) => {
            const imgSrc = q.imageUrl ? resolveImageUrl(q.imageUrl) : null;
            const neg =
              q.negativeMarks ||
              (q.type === 'MCQ' ? (q.positiveMarks === 1 ? 0.33 : 0.67) : 0);

            return (
              <div
                key={q.questionId || idx}
                id={`qp-q-${idx}`}
                className="bg-white border border-slate-300 rounded-lg p-5 shadow-sm space-y-3"
              >
                {/* Question metadata header */}
                <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                  <div className="flex items-center gap-3">
                    <span className="bg-[#1a56a5] text-white font-bold text-xs px-2.5 py-1 rounded">
                      Q.{idx + 1}
                    </span>
                    <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {q.type}
                    </span>
                    <span className="text-xs text-slate-600 font-medium">
                      Section: <strong className="text-slate-800">{q.sectionName}</strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-emerald-700 font-semibold">Marks: +{q.positiveMarks}</span>
                    <span className="text-rose-700 font-semibold">Negative: -{neg.toFixed(2)}</span>
                    {onJumpToQuestion && (
                      <button
                        onClick={() => {
                          onJumpToQuestion(idx);
                          onClose();
                        }}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-xs shadow-xs"
                      >
                        Go to Question ➔
                      </button>
                    )}
                  </div>
                </div>

                {/* Question image or text */}
                <div className="py-2">
                  {imgSrc ? (
                    <img
                      src={imgSrc}
                      alt={`Question ${idx + 1}`}
                      onError={(e) => {
                        const fb = getFallbackImageUrl(q.imageUrl);
                        if (fb && e.currentTarget.src !== fb) e.currentTarget.src = fb;
                      }}
                      className="w-full h-auto object-contain rounded border border-slate-200 bg-white shadow-xs"
                      loading="lazy"
                    />
                  ) : (
                    <p className="text-sm text-slate-800 whitespace-pre-wrap font-sans">
                      {q.questionText || 'Question content not available.'}
                    </p>
                  )}
                </div>

                {/* Question Options or NAT hint */}
                {q.type !== 'NAT' && q.options && q.options.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t border-slate-100">
                    {q.options.map((opt) => (
                      <div
                        key={opt.id}
                        className="flex items-start gap-2 p-2 rounded bg-slate-50 border border-slate-200 text-xs text-slate-700"
                      >
                        <span className="font-bold text-blue-800">({opt.id})</span>
                        <span>{opt.text}</span>
                      </div>
                    ))}
                  </div>
                )}
                {q.type === 'NAT' && (
                  <div className="text-xs text-slate-500 italic bg-amber-50 p-2 rounded border border-amber-200">
                    Numerical Answer Type (NAT) question. Virtual keypad answer input.
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-white border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-1.5 bg-[#1a56a5] text-white rounded font-medium text-sm hover:bg-blue-700 transition"
          >
            Close Question Paper
          </button>
        </div>
      </div>
    </div>
  );
};
