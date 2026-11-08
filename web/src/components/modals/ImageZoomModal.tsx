import { useState } from 'react';
import { X, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface ImageZoomModalProps {
  isOpen: boolean;
  imageUrl: string;
  title?: string;
  onClose: () => void;
}

export const ImageZoomModal: React.FC<ImageZoomModalProps> = ({
  isOpen,
  imageUrl,
  title = 'Question Diagram',
  onClose,
}) => {
  const [scale, setScale] = useState(1);

  if (!isOpen) return null;

  const zoomIn = () => setScale((s) => Math.min(s + 0.25, 3));
  const zoomOut = () => setScale((s) => Math.max(s - 0.25, 0.5));
  const resetZoom = () => setScale(1);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="relative flex flex-col bg-white rounded-lg shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden border border-slate-300">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#1a56a5] text-white">
          <div className="font-semibold text-base">{title}</div>
          <div className="flex items-center gap-2">
            <button
              onClick={zoomOut}
              className="p-1.5 hover:bg-white/20 rounded transition text-white"
              title="Zoom Out"
            >
              <ZoomOut size={18} />
            </button>
            <span className="text-xs font-mono px-1">{Math.round(scale * 100)}%</span>
            <button
              onClick={zoomIn}
              className="p-1.5 hover:bg-white/20 rounded transition text-white"
              title="Zoom In"
            >
              <ZoomIn size={18} />
            </button>
            <button
              onClick={resetZoom}
              className="p-1.5 hover:bg-white/20 rounded transition text-white text-xs flex items-center gap-1"
              title="Reset"
            >
              <RotateCcw size={16} />
            </button>
            <div className="h-4 w-px bg-white/30 mx-1" />
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-red-500 rounded transition text-white"
              title="Close (Esc)"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Image Content Container */}
        <div className="flex-1 overflow-auto p-4 bg-slate-100 flex items-center justify-center min-h-[400px]">
          <img
            src={imageUrl}
            alt={title}
            style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}
            className="transition-transform duration-100 max-w-full max-h-[75vh] object-contain shadow-sm bg-white rounded border border-slate-200"
          />
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 flex justify-between items-center">
          <span>Click outside or Esc to close. Scroll to pan when zoomed.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#1a56a5] text-white rounded font-medium hover:bg-blue-700 text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
