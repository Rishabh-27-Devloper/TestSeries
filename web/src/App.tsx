import { useState, useEffect } from 'react';
import type {
  ExamPaper,
  ExamResult,
  PaperIndexItem,
  PracticeIndex,
  PracticeTopicItem,
} from './types';
import { storage } from './utils/storage';
import { ExamSelectionPortal } from './components/portal/ExamSelectionPortal';
import { PaperInventory } from './components/inventory/PaperInventory';
import { InstructionsView } from './components/exam/InstructionsView';
import { CbtExamWindow } from './components/exam/CbtExamWindow';
import { StudentDashboard } from './components/dashboard/StudentDashboard';
import { PracticeTopicSelection } from './components/practice/PracticeTopicSelection';
import { PracticeExamWindow } from './components/practice/PracticeExamWindow';
import { UserProfileModal } from './components/modals/UserProfileModal';
import { Loader2 } from 'lucide-react';

type AppView =
  | 'PORTAL'
  | 'INVENTORY'
  | 'INSTRUCTIONS'
  | 'EXAM'
  | 'DASHBOARD'
  | 'PRACTICE_SELECTION'
  | 'PRACTICE_SESSION';

export function App() {
  const [view, setView] = useState<AppView>('PORTAL');
  const [selectedExam, setSelectedExam] = useState<'GATE' | 'NEET'>('GATE');
  const [papers, setPapers] = useState<PaperIndexItem[]>([]);
  const [practiceIndex, setPracticeIndex] = useState<PracticeIndex | null>(null);
  const [selectedPracticeTopic, setSelectedPracticeTopic] = useState<PracticeTopicItem | null>(null);
  const [dashboardTab, setDashboardTab] = useState<'SCORECARD' | 'SOLUTIONS' | 'TRENDS' | 'PRACTICE'>('SCORECARD');
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingPaper, setLoadingPaper] = useState<boolean>(false);
  const [currentPaper, setCurrentPaper] = useState<ExamPaper | null>(null);
  const [currentResult, setCurrentResult] = useState<ExamResult | null>(null);
  const [showProfileModal, setShowProfileModal] = useState<boolean>(false);
  const [profile, setProfile] = useState(() => storage.getUserProfile());

  // Initialize data on mount
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        // Fetch paper catalog index & practice bank index
        const [index, pIndex] = await Promise.all([
          storage.getPaperIndex(),
          storage.getPracticeIndex(),
        ]);
        setPapers(index);
        setPracticeIndex(pIndex);
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
  const handleOpenDashboard = (tab: 'SCORECARD' | 'SOLUTIONS' | 'TRENDS' | 'PRACTICE' = 'SCORECARD') => {
    setDashboardTab(tab);
    const attempts = storage.getAllAttempts();
    if (attempts.length > 0) {
      // Prefer an attempt matching currently selected exam if available
      const matched = attempts.find(
        (a) => (a.examType || '').toUpperCase() === selectedExam.toUpperCase()
      );
      setCurrentResult(matched || attempts[0]);
      setView('DASHBOARD');
    } else {
      // Create empty mock scorecard so candidate can view practice analytics directly
      const dummyResult: ExamResult = {
        paperId: 'practice_summary',
        paperTitle: 'Practice Analytics Mode',
        examType: 'GATE',
        studentName: profile.name,
        timestamp: new Date().toISOString(),
        durationTakenSeconds: 0,
        totalMarks: 0,
        scoreObtained: 0,
        positiveMarks: 0,
        negativeMarks: 0,
        totalQuestions: 0,
        attemptedCount: 0,
        correctCount: 0,
        incorrectCount: 0,
        unattemptedCount: 0,
        accuracyPercentage: 0,
        percentageScore: 0,
        sectionScores: {},
        evaluations: [],
      };
      setCurrentResult(dummyResult);
      setDashboardTab('PRACTICE');
      setView('DASHBOARD');
    }
  };

  // Filter papers for currently selected exam portal (Strict separation)
  const currentPortalPapers = papers.filter((p) => {
    const et = (p.examType || 'GATE').toUpperCase();
    if (selectedExam === 'NEET') {
      return et === 'NEET' || et === 'NEET UG';
    }
    return et === 'GATE';
  });

  // Loading Screen
  if (loading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-50 font-sans">
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-[#1a56a5] text-white flex items-center justify-center font-black text-2xl shadow-lg">
            C
          </div>
          <div className="flex items-center gap-2 text-slate-700 text-sm font-semibold">
            <Loader2 className="animate-spin text-[#1a56a5]" size={20} />
            <span>Loading CBT Examination Simulator Platform...</span>
          </div>
          <p className="text-xs text-slate-400">Loading GATE EC &amp; NEET UG Archive (249 Papers &amp; 23,650+ Questions)</p>
        </div>
      </div>
    );
  }

  // Loading Paper Transition Screen
  if (loadingPaper) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-50 font-sans">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className={`animate-spin ${selectedExam === 'NEET' ? 'text-teal-700' : 'text-[#1a56a5]'}`} size={36} />
          <div className="text-base font-bold text-slate-800">
            Preparing Examination Paper &amp; Slices...
          </div>
          <p className="text-xs text-slate-500">Configuring CBT Test Engine &amp; Timers</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* View 0: Multi-Exam Selection Portal (Layer 1) */}
      {view === 'PORTAL' && (
        <ExamSelectionPortal
          papers={papers}
          profile={profile}
          onSelectExam={(exam) => {
            setSelectedExam(exam);
            setView('INVENTORY');
          }}
          onOpenPracticeMode={() => setView('PRACTICE_SELECTION')}
          onOpenDashboard={() => handleOpenDashboard('SCORECARD')}
          onOpenProfile={() => setShowProfileModal(true)}
        />
      )}

      {/* View 1: Paper Inventory (Layer 2) - Completely Separated by Exam */}
      {view === 'INVENTORY' && (
        <PaperInventory
          key={`${profile.name}_${selectedExam}`}
          papers={currentPortalPapers}
          selectedExam={selectedExam}
          onSelectPaper={handleSelectPaper}
          onOpenPracticeMode={() => setView('PRACTICE_SELECTION')}
          onOpenDashboard={() => handleOpenDashboard('SCORECARD')}
          onOpenProfile={() => setShowProfileModal(true)}
          onBackToPortal={() => setView('PORTAL')}
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
            setDashboardTab('SCORECARD');
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
          selectedExam={selectedExam}
          initialTab={dashboardTab}
          onRetakeExam={handleRetakeExam}
          onBackToInventory={() => setView(selectedPracticeTopic ? 'PRACTICE_SELECTION' : 'INVENTORY')}
          onLoadPastAttempt={(att) => setCurrentResult(att)}
        />
      )}

      {/* View 5: Practice Mode Topic Selection */}
      {view === 'PRACTICE_SELECTION' && practiceIndex && (
        <PracticeTopicSelection
          practiceIndex={practiceIndex}
          profile={profile}
          onSelectTopic={(topic) => {
            setSelectedPracticeTopic(topic);
            setView('PRACTICE_SESSION');
          }}
          onBackToPortal={() => setView('PORTAL')}
          onOpenDashboard={() => handleOpenDashboard('PRACTICE')}
          onOpenProfile={() => setShowProfileModal(true)}
        />
      )}

      {/* View 6: Live Practice Mode Examination / Stopwatch Window */}
      {view === 'PRACTICE_SESSION' && selectedPracticeTopic && (
        <PracticeExamWindow
          topic={selectedPracticeTopic}
          profile={profile}
          onFinishTopic={() => setView('PRACTICE_SELECTION')}
          onExitPractice={() => setView('PRACTICE_SELECTION')}
        />
      )}

      {/* Global Candidate Profile Modal */}
      <UserProfileModal
        isOpen={showProfileModal}
        selectedExam={selectedExam}
        onClose={() => setShowProfileModal(false)}
        onProfileUpdated={(updated) => setProfile(updated)}
      />
    </div>
  );
}

export default App;
