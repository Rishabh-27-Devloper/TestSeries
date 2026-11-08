import React from 'react';
import { X, BookOpen, AlertTriangle } from 'lucide-react';

interface InstructionsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const InstructionsModal: React.FC<InstructionsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="flex flex-col bg-white rounded-lg shadow-2xl max-w-4xl w-full h-[85vh] overflow-hidden border border-slate-300">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#1a56a5] text-white">
          <div className="flex items-center gap-2">
            <BookOpen size={20} />
            <h2 className="font-semibold text-lg">General Examination Instructions</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-red-500 rounded transition text-white"
            title="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm text-slate-700 leading-relaxed bg-white">
          {/* General instructions */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-900 border-b pb-1">
              General Instructions:
            </h3>
            <ol className="list-decimal list-inside space-y-2 pl-2">
              <li>
                The clock will be set at the server. The countdown timer at the top right corner of
                screen will display the remaining time available for you to complete the
                examination. When the timer reaches zero, the examination will end automatically.
              </li>
              <li>
                The Question Palette displayed on the right side of screen will show the status of
                each question using one of the following symbols:
              </li>
            </ol>
          </div>

          {/* Symbol Legend */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
            <h4 className="font-bold text-slate-800 text-sm">Question Palette Symbols:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-sm bg-slate-200 text-slate-800 font-bold flex items-center justify-center border border-slate-300 shadow-xs">
                  1
                </span>
                <span>You have not visited the question yet.</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-sm bg-[#e74c3c] text-white font-bold flex items-center justify-center shadow-xs">
                  2
                </span>
                <span>You have not answered the question.</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-sm bg-[#27ae60] text-white font-bold flex items-center justify-center shadow-xs">
                  3
                </span>
                <span>You have answered the question.</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-[#8e44ad] text-white font-bold flex items-center justify-center shadow-xs">
                  4
                </span>
                <span>You have NOT answered the question, but marked for review.</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="relative w-8 h-8 rounded-full bg-[#8e44ad] text-white font-bold flex items-center justify-center shadow-xs">
                  5
                  <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border border-white" />
                </div>
                <span>
                  The question is <strong>Answered &amp; Marked for Review</strong> (evaluated in
                  final score).
                </span>
              </div>
            </div>
          </div>

          {/* Navigating to a Question */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-900 border-b pb-1">
              Navigating to a Question:
            </h3>
            <ul className="list-disc list-inside space-y-2 pl-2">
              <li>
                Click on the question number in the Question Palette to go directly to that question.
              </li>
              <li>
                Click on <strong>Save &amp; Next</strong> to save your answer for the current
                question and proceed to the next question.
              </li>
              <li>
                Click on <strong>Mark for Review &amp; Next</strong> to save your answer for the
                current question, mark it for review, and proceed to the next.
              </li>
            </ul>
          </div>

          {/* Answering a Question */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-900 border-b pb-1">
              Answering a Question:
            </h3>
            <ul className="list-disc list-inside space-y-2 pl-2">
              <li>
                <strong>Multiple Choice Questions (MCQ):</strong> Select one option by clicking on
                the radio button corresponding to your choice. Negative marking applies (-33% for
                1-mark, -67% for 2-mark questions).
              </li>
              <li>
                <strong>Multiple Select Questions (MSQ):</strong> Select one or more correct options
                by clicking the checkboxes. No negative marking, but all correct options must be
                selected for marks.
              </li>
              <li>
                <strong>Numerical Answer Type (NAT):</strong> Use the on-screen virtual keypad to
                enter numeric value (including decimal and negative signs). No negative marking.
              </li>
              <li>
                To deselect your chosen answer, click on the <strong>Clear Response</strong> button.
              </li>
            </ul>
          </div>

          {/* Warning box */}
          <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded text-amber-900 flex items-start gap-3">
            <AlertTriangle className="shrink-0 text-amber-600 mt-0.5" size={20} />
            <div className="text-xs leading-relaxed">
              <strong>Notice on Auto-Submission:</strong> Do not refresh or close the browser tab.
              When the examination duration ends, your answers will be automatically evaluated and
              persisted to your dashboard.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-[#1a56a5] text-white rounded font-medium text-sm hover:bg-blue-700 transition"
          >
            Understood &amp; Close
          </button>
        </div>
      </div>
    </div>
  );
};
