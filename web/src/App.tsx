import { useState, useEffect } from 'react';
import type { ExamPaper, ExamResult, PaperIndexItem } from './types';
import { storage } from './utils/storage';
import { PaperInventory } from './components/inventory/PaperInventory';
import { InstructionsView } from './components/exam/InstructionsView';
import { CbtExamWindow } from './components/exam/CbtExamWindow';
import { StudentDashboard } from './components/dashboard/StudentDashboard';
import { UserProfileModal } from './components/modals/UserProfileModal';
import { Loader2 } from 'lucide-react';

type AppView = 'INVENTORY' | 'INSTRUCTIONS' | 'EXAM' | 'DASHBOARD';

export function App() {
  const [view, setView] = useState<AppView>('INVENTORY');
  const [papers, setPapers] = useState<PaperIndexItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingPaper, setLoadingPaper] = useState<boolean>(false);
  const [currentPaper, setCurrentPaper] = useState<ExamPaper | null>(null);
  const [currentResult, setCurrentResult] = useState<ExamResult | null>(null);
  const [showProfileModal, setShowProfileModal] = useState<boolean>(false);

  // Initialize data on mount
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        // Load sample attempts if none exist
        await storage.loadInitialAttempts();
        // Fetch paper catalog index
        const index = await storage.getPaperIndex();
        setPapers(index);
      } catch (err) {
        console.error('Failed to initialize test series web application', err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Handler: Select paper from Inventory
  const handleSelectPaper = async (paperSummary: PaperIndexItem) => {
    try {
      setLoadingPaper(true);
      const paperData: ExamPaper = await storage.getPaper(paperSummary.jsonPath);
      setCurrentPaper(paperData);
      setView('INSTRUCTIONS');
    } catch (err) {
      console.error('Failed to load paper:', err);
      alert(`Could not load examination paper. Please try again.`);
    } finally {
      setLoadingPaper(false);
    }
  };

  // Handler: Retake an exam from Dashboard
  const handleRetakeExam = async (paperId: string) => {
    const paperSummary = papers.find((p) => p.paperId === paperId);
    if (paperSummary) {
      await handleSelectPaper(paperSummary);
    } else {
      alert(`Paper information not found for ${paperId}`);
    }
  };

  // Handler: Open Dashboard from Top Bar
  const handleOpenDashboard = () => {
    const attempts = storage.getAllAttempts();
    if (attempts.length > 0) {
      setCurrentResult(attempts[0]);
      setView('DASHBOARD');
    } else {
      alert('No test attempts recorded yet. Attempt a paper to view performance analytics.');
    }
  };

  // Loading Screen
  if (loading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-50 font-sans">
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-[#1a56a5] text-white flex items-center justify-center font-black text-2xl shadow-lg">
            G
          </div>
          <div className="flex items-center gap-2 text-slate-700 text-sm font-semibold">
            <Loader2 className="animate-spin text-[#1a56a5]" size={20} />
            <span>Loading GATE CBT Test Series Platform...</span>
          </div>
          <p className="text-xs text-slate-400">Loading 100+ Test Papers &amp; Question Database</p>
        </div>
      </div>
    );
  }

  // Loading Paper Transition Screen
  if (loadingPaper) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-50 font-sans">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin text-[#1a56a5]" size={36} />
          <div className="text-base font-bold text-slate-800">
            Preparing Examination Paper &amp; Slices...
          </div>
          <p className="text-xs text-slate-500">Configuring TCS iON Test Engine &amp; Timers</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* View 1: Paper Inventory (Layer 2) */}
      {view === 'INVENTORY' && (
        <PaperInventory
          papers={papers}
          onSelectPaper={handleSelectPaper}
          onOpenDashboard={handleOpenDashboard}
          onOpenProfile={() => setShowProfileModal(true)}
        />
      )}

      {/* View 2: Pre-Exam Instructions & Declaration */}
      {view === 'INSTRUCTIONS' && currentPaper && (
        <InstructionsView
          paper={currentPaper}
          onStartExam={() => setView('EXAM')}
          onCancel={() => setView('INVENTORY')}
        />
      )}

      {/* View 3: Live CBT Examination Window (Layer 3) */}
      {view === 'EXAM' && currentPaper && (
        <CbtExamWindow
          paper={currentPaper}
          onFinishExam={(result) => {
            setCurrentResult(result);
            setView('DASHBOARD');
          }}
          onExitExam={() => {
            if (confirm('Are you sure you want to abandon this exam? Progress will not be evaluated.')) {
              setView('INVENTORY');
            }
          }}
        />
      )}

      {/* View 4: Student Performance Dashboard */}
      {view === 'DASHBOARD' && currentResult && (
        <StudentDashboard
          currentResult={currentResult}
          onRetakeExam={handleRetakeExam}
          onBackToInventory={() => setView('INVENTORY')}
          onLoadPastAttempt={(att) => setCurrentResult(att)}
        />
      )}

      {/* Global Candidate Profile Modal */}
      <UserProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
      />
    </div>
  );
}

export default App;
