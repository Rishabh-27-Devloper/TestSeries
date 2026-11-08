import React, { useState } from 'react';
import { X, CheckCircle2, AlertTriangle, Filter } from 'lucide-react';
import type { ExamPaper, Question } from '../../types';
import { isQuestionAnswered } from '../../utils/evaluator';

interface SubmitConfirmationModalProps {
  isOpen: boolean;
  paper: ExamPaper;
  onConfirm: () => void;
  onCancel: () => void;
  onClose?: () => void;
}

export const SubmitConfirmationModal: React.FC<SubmitConfirmationModalProps> = ({
  isOpen,
  paper,
  onConfirm,
  onCancel,
}) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'details'>('summary');
  const [filterType, setFilterType] = useState('All Questions');

  if (!isOpen) return null;

  const allQuestions: Question[] = paper.sections.flatMap((s) => s.questions);

  // Filtered detailed questions
  const filteredQuestions = allQuestions.filter((q) => {
    if (filterType === 'MSQ Questions Only') return q.type === 'MSQ';
    if (filterType === 'MCQ Questions Only') return q.type === 'MCQ';
    if (filterType === 'NAT Questions Only') return q.type === 'NAT';
    if (filterType === 'Answered Questions Only') return isQuestionAnswered(q.candidateAnswer);
    if (filterType === 'Unattempted Questions Only') return !isQuestionAnswered(q.candidateAnswer);
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-xl border border-slate-300 bg-white shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-blue-900 bg-[#1a56a5] px-6 py-3.5 text-white">
          <div>
            <h3 className="text-base font-bold tracking-tight">Exam Summary & Submission</h3>
            <p className="text-xs text-blue-100">{paper.title}</p>
          </div>
          <button
            onClick={onCancel}
            className="rounded p-1 hover:bg-white/20 transition-colors"
            title="Return to Exam"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 bg-slate-100 px-6 pt-3">
          <button
            onClick={() => setActiveTab('summary')}
            className={`border-b-2 px-5 py-2.5 text-sm font-semibold transition-all ${
              activeTab === 'summary'
                ? 'border-[#1a56a5] bg-white text-[#1a56a5] rounded-t-lg shadow-sm'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            📊 Section Summary (TCS iON)
          </button>
          <button
            onClick={() => setActiveTab('details')}
            className={`border-b-2 px-5 py-2.5 text-sm font-semibold transition-all ${
              activeTab === 'details'
                ? 'border-[#1a56a5] bg-white text-[#1a56a5] rounded-t-lg shadow-sm'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            📑 Detailed Question Status & Responses
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
          {activeTab === 'summary' ? (
            <div className="space-y-4">
              <div className="rounded-lg border border-slate-300 bg-white shadow-sm overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100 font-bold text-slate-800 border-b border-slate-300">
                    <tr>
                      <th className="p-3 border-r border-slate-300">Section Name</th>
                      <th className="p-3 text-center border-r border-slate-300">Total Questions</th>
                      <th className="p-3 text-center border-r border-slate-300 text-green-700 bg-green-50/50">Answered</th>
                      <th className="p-3 text-center border-r border-slate-300 text-red-700 bg-red-50/50">Not Answered</th>
                      <th className="p-3 text-center border-r border-slate-300 text-purple-700 bg-purple-50/50">Marked for Review</th>
                      <th className="p-3 text-center border-r border-slate-300 text-purple-800 bg-purple-50/80">Ans & Marked (Evaluated)</th>
                      <th className="p-3 text-center text-slate-600">Not Visited</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {paper.sections.map((sec) => {
                      const totalQ = sec.questions.length;
                      const answered = sec.questions.filter((q) => isQuestionAnswered(q.candidateAnswer)).length;
                      const marked = sec.questions.filter((q) => q.status === 'MARKED_FOR_REVIEW').length;
                      const ansMarked = sec.questions.filter((q) => q.status === 'ANSWERED_AND_MARKED').length;
                      const notVisited = sec.questions.filter((q) => q.status === 'NOT_VISITED').length;
                      const notAnswered = Math.max(0, totalQ - answered - notVisited - marked);

                      return (
                        <tr key={sec.sectionId} className="hover:bg-slate-50/80 transition-colors">
                          <td className="p-3 font-semibold text-slate-800 border-r border-slate-200">{sec.sectionName}</td>
                          <td className="p-3 text-center font-bold border-r border-slate-200">{totalQ}</td>
                          <td className="p-3 text-center font-bold text-green-700 border-r border-slate-200 bg-green-50/20">{answered}</td>
                          <td className="p-3 text-center font-bold text-red-700 border-r border-slate-200 bg-red-50/20">{notAnswered}</td>
                          <td className="p-3 text-center font-bold text-purple-700 border-r border-slate-200 bg-purple-50/20">{marked}</td>
                          <td className="p-3 text-center font-bold text-purple-800 border-r border-slate-200 bg-purple-50/40">{ansMarked}</td>
                          <td className="p-3 text-center font-semibold text-slate-600">{notVisited}</td>
                        </tr>
                      );
                    })}

                    {/* Total Row */}
                    <tr className="bg-slate-100 font-bold border-t-2 border-slate-300 text-slate-900">
                      <td className="p-3 border-r border-slate-300">TOTAL</td>
                      <td className="p-3 text-center border-r border-slate-300">{allQuestions.length}</td>
                      <td className="p-3 text-center text-green-700 border-r border-slate-300 bg-green-100/40">
                        {allQuestions.filter((q) => isQuestionAnswered(q.candidateAnswer)).length}
                      </td>
                      <td className="p-3 text-center text-red-700 border-r border-slate-300 bg-red-100/40">
                        {allQuestions.filter((q) => !isQuestionAnswered(q.candidateAnswer) && q.status !== 'NOT_VISITED' && q.status !== 'MARKED_FOR_REVIEW').length}
                      </td>
                      <td className="p-3 text-center text-purple-700 border-r border-slate-300 bg-purple-100/40">
                        {allQuestions.filter((q) => q.status === 'MARKED_FOR_REVIEW').length}
                      </td>
                      <td className="p-3 text-center text-purple-800 border-r border-slate-300 bg-purple-100/60">
                        {allQuestions.filter((q) => q.status === 'ANSWERED_AND_MARKED').length}
                      </td>
                      <td className="p-3 text-center text-slate-600">
                        {allQuestions.filter((q) => q.status === 'NOT_VISITED').length}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-sm text-amber-950 mb-1">Important Submission Note</p>
                  <p>
                    Once submitted, you cannot change your answers. Questions labeled <b>Answered</b> and{' '}
                    <b>Answered & Marked for Review</b> will be counted for evaluation. Questions marked for review without an answer will <b>not</b> be evaluated.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Filter controls */}
              <div className="flex items-center space-x-3 bg-white p-3 rounded-lg border border-slate-200">
                <Filter className="h-4 w-4 text-slate-500" />
                <span className="text-xs font-bold text-slate-700">Filter View:</span>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="rounded border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 shadow-sm focus:border-blue-600 focus:outline-none"
                >
                  <option value="All Questions">All Questions ({allQuestions.length})</option>
                  <option value="MSQ Questions Only">MSQ Questions Only</option>
                  <option value="MCQ Questions Only">MCQ Questions Only</option>
                  <option value="NAT Questions Only">NAT Questions Only</option>
                  <option value="Answered Questions Only">Answered Questions Only</option>
                  <option value="Unattempted Questions Only">Unattempted Questions Only</option>
                </select>
              </div>

              {/* Detail Table */}
              <div className="rounded-lg border border-slate-300 bg-white shadow-sm overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100 font-bold text-slate-800 border-b border-slate-300">
                    <tr>
                      <th className="p-2.5 w-16 text-center border-r border-slate-300">Q No.</th>
                      <th className="p-2.5 border-r border-slate-300">Section</th>
                      <th className="p-2.5 w-20 text-center border-r border-slate-300">Type</th>
                      <th className="p-2.5 w-28 text-center border-r border-slate-300">Status</th>
                      <th className="p-2.5 border-r border-slate-300">Your Selection / Response</th>
                      <th className="p-2.5 w-24 text-center">Marks (+ / -)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {filteredQuestions.map((q) => {
                      const isAns = isQuestionAnswered(q.candidateAnswer);
                      let responseStr = '—';
                      if (isAns) {
                        if (Array.isArray(q.candidateAnswer)) {
                          responseStr = q.candidateAnswer.map((x) => `Option (${x})`).join(', ');
                        } else if (q.type === 'MCQ') {
                          responseStr = `Option (${q.candidateAnswer})`;
                        } else {
                          responseStr = String(q.candidateAnswer);
                        }
                      }

                      return (
                        <tr key={q.questionNumber} className="hover:bg-slate-50 transition-colors">
                          <td className="p-2.5 text-center font-bold text-slate-800 border-r border-slate-200">{q.questionNumber}</td>
                          <td className="p-2.5 text-slate-700 border-r border-slate-200 truncate max-w-xs">{q.sectionName}</td>
                          <td className="p-2.5 text-center font-semibold text-slate-600 border-r border-slate-200">{q.type}</td>
                          <td className="p-2.5 text-center border-r border-slate-200">
                            {isAns ? (
                              <span className="rounded bg-green-100 px-2 py-0.5 text-[11px] font-bold text-green-800">
                                Answered
                              </span>
                            ) : (
                              <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                                Unattempted
                              </span>
                            )}
                          </td>
                          <td className="p-2.5 font-medium border-r border-slate-200">
                            {isAns ? (
                              <span className="font-bold text-blue-900 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                                {responseStr}
                              </span>
                            ) : (
                              <span className="italic text-slate-400">None</span>
                            )}
                          </td>
                          <td className="p-2.5 text-center font-semibold text-slate-700">
                            +{q.positiveMarks} / -{q.negativeMarks}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-slate-200 bg-white px-6 py-4">
          <button
            onClick={onCancel}
            className="rounded border border-slate-300 bg-white px-5 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-100 transition"
          >
            Cancel & Return to Exam
          </button>
          <button
            onClick={onConfirm}
            className="rounded bg-green-600 px-7 py-2.5 text-sm font-bold text-white shadow-md hover:bg-green-700 active:scale-95 transition flex items-center space-x-2"
          >
            <CheckCircle2 className="h-4 w-4" />
            <span>Yes, Submit Examination</span>
          </button>
        </div>
      </div>
    </div>
  );
};
