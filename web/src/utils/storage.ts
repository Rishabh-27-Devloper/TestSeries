import type {
  ExamResult,
  PaperIndexItem,
  UserProfile,
  PracticeIndex,
  PracticeQuestion,
  PracticeQuestionAttempt,
  PracticeUserStats,
} from '../types';

const PROFILE_KEY = 'test_series_user_profile';
const ATTEMPTS_KEY = 'test_series_user_attempts';
const PRACTICE_STATE_KEY = 'test_series_practice_state';

const DEFAULT_PROFILE: UserProfile = {
  name: 'Candidate',
  phoneNumber: '+91 9123456789',
  email: 'candidate@gate.ac.in',
  targetYear: 'GATE 2026',
  branch: 'Electronics & Communication',
};

export function cleanImagePath(imgUrl?: string): string {
  if (!imgUrl) return '';
  let clean = imgUrl.replace(/\\/g, '/');
  // Strip any Windows absolute or local parent prefixes (e.g. C:/Users/.../data/papers/)
  const dataIdx = clean.indexOf('data/papers/');
  if (dataIdx !== -1) {
    clean = clean.substring(dataIdx);
  }
  return clean.replace(/^(\.\/|\/)/, '');
}

export function getUserProfile(): UserProfile {
  try {
    const data = localStorage.getItem(PROFILE_KEY);
    if (data) {
      const parsed = JSON.parse(data);
      delete parsed.rollNumber;
      return { ...DEFAULT_PROFILE, ...parsed };
    }
  } catch (e) {
    console.error('Failed to load user profile', e);
  }
  return DEFAULT_PROFILE;
}

export function saveUserProfile(profile: UserProfile): void {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } catch (e) {
    console.error('Failed to save user profile', e);
  }
}

export function getAllAttempts(): ExamResult[] {
  try {
    let data = localStorage.getItem(ATTEMPTS_KEY);
    // Backward compatibility: If empty, check if there were legacy attempts keys
    if (!data) {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && (k.startsWith('test_series_attempts_') || k === 'test_series_attempts')) {
          data = localStorage.getItem(k);
          if (data) {
            localStorage.setItem(ATTEMPTS_KEY, data);
            break;
          }
        }
      }
    }
    if (data) {
      const list: ExamResult[] = JSON.parse(data);
      return list.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
    }
  } catch (e) {
    console.error('Failed to load user attempts', e);
  }
  return [];
}

export function saveAttempt(result: ExamResult): void {
  try {
    const list = getAllAttempts();
    const updated = [result, ...list];
    localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to save attempt', e);
  }
}

export function getAttemptsByExam(examType: string): ExamResult[] {
  const norm = (examType || '').trim().toUpperCase();
  return getAllAttempts().filter((a) => {
    const aType = (a.examType || '').trim().toUpperCase();
    if (norm === 'NEET' || norm === 'NEET UG') {
      return aType === 'NEET' || aType === 'NEET UG';
    }
    return aType === norm;
  });
}

export function clearUserAttempts(examType?: string): void {
  try {
    if (!examType) {
      localStorage.removeItem(ATTEMPTS_KEY);
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const k = localStorage.key(i);
        if (k && (k.startsWith('test_series_attempts_') || k === 'test_series_attempts')) {
          localStorage.removeItem(k);
        }
      }
    } else {
      const norm = examType.trim().toUpperCase();
      const all = getAllAttempts();
      const remaining = all.filter((a) => {
        const aType = (a.examType || '').trim().toUpperCase();
        if (norm === 'NEET' || norm === 'NEET UG') {
          return aType !== 'NEET' && aType !== 'NEET UG';
        }
        return aType !== norm;
      });
      localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(remaining));
    }
  } catch (e) {
    console.error('Failed to clear user attempts', e);
  }
}

export function deleteAttemptsForPaper(paperId: string): void {
  try {
    const list = getAllAttempts();
    const updated = list.filter((a) => a.paperId !== paperId);
    localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to delete attempts for paper', e);
  }
}

export function deleteSingleAttempt(timestamp: string, paperId?: string): void {
  try {
    const list = getAllAttempts();
    const updated = list.filter(
      (a) => !(a.timestamp === timestamp && (!paperId || a.paperId === paperId))
    );
    localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to delete single attempt', e);
  }
}

export function getAttemptsForPaper(paperId: string): ExamResult[] {
  return getAllAttempts().filter((a) => a.paperId === paperId);
}

export function getAttemptsSummaryForPaper(paperId: string): {
  attemptCount: number;
  lastAttempt?: ExamResult;
  bestAttempt?: ExamResult;
} {
  const list = getAttemptsForPaper(paperId);
  if (list.length === 0) {
    return { attemptCount: 0 };
  }
  const lastAttempt = list[0];
  const bestAttempt = [...list].sort((a, b) => b.scoreObtained - a.scoreObtained)[0];
  return {
    attemptCount: list.length,
    lastAttempt,
    bestAttempt,
  };
}

export async function getPaperIndex(): Promise<PaperIndexItem[]> {
  try {
    const resp = await fetch('/data/papers_index.json');
    if (resp.ok) {
      return await resp.json();
    }
  } catch (e) {
    console.error('Failed to fetch papers_index.json', e);
  }
  return [];
}

export async function getPaper(jsonPath: string): Promise<any> {
  const cleanPath = jsonPath.startsWith('/') ? jsonPath : `/${jsonPath}`;
  const resp = await fetch(cleanPath);
  if (!resp.ok) {
    throw new Error(`Failed to load exam paper from ${cleanPath}`);
  }
  return await resp.json();
}

/**
 * Resolves question diagram slice images.
 * Always attempts local server path first for practice assets or local dev.
 * In production, resolves to GitHub Raw CDN mirror so all slices load reliably.
 */
export function resolveImageUrl(imgUrl?: string): string {
  if (!imgUrl) return '';
  if (imgUrl.startsWith('data:') || imgUrl.startsWith('http://') || imgUrl.startsWith('https://')) {
    return imgUrl;
  }
  const clean = cleanImagePath(imgUrl);

  const isLocalhost =
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.hostname.startsWith('192.168.') ||
      window.location.hostname.startsWith('10.') ||
      window.location.hostname.endsWith('.local'));

  // If it's a practice asset, it is bundled in the public web distribution, so serve from current domain first
  if (isLocalhost || clean.startsWith('assets/practice') || clean.startsWith('data/practice')) {
    return `/${clean}`;
  }

  // Deployed / Production on Vercel, Netlify, etc. -> Direct GitHub Raw CDN
  return `https://raw.githubusercontent.com/Rishabh-27-Devloper/TestSeries/main/${clean}`;
}

/**
 * Secondary mirror fallback using GitHub Raw CDN in case of network restriction or 404
 */
export function getFallbackImageUrl(imgUrl?: string): string {
  if (!imgUrl) return '';
  const clean = cleanImagePath(imgUrl);

  // If local /assets/practice/... failed, fall back to GitHub Raw (web/public path first, then root)
  if (clean.startsWith('assets/practice') || clean.startsWith('data/practice')) {
    return `https://raw.githubusercontent.com/Rishabh-27-Devloper/TestSeries/main/web/public/${clean}`;
  }

  return `https://raw.githubusercontent.com/Rishabh-27-Devloper/TestSeries/main/${clean}`;
}

// ============================================================================
// PRACTICE MODE STORAGE HELPERS
// ============================================================================

function getPracticeStorageKey(userName?: string): string {
  const profile = getUserProfile();
  const name = userName || profile.name || 'default';
  const clean = name.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  return `${PRACTICE_STATE_KEY}_${clean}`;
}

export async function getPracticeIndex(): Promise<PracticeIndex | null> {
  try {
    const resp = await fetch('/data/practice/practice_index.json');
    if (resp.ok) {
      return await resp.json();
    }
  } catch (e) {
    console.error('Failed to fetch practice_index.json', e);
  }
  return null;
}

export async function getPracticeQuestion(questionId: string): Promise<PracticeQuestion | null> {
  try {
    const resp = await fetch(`/data/practice/questions/${questionId}.json`);
    if (resp.ok) {
      return await resp.json();
    }
  } catch (e) {
    console.error(`Failed to fetch practice question ${questionId}`, e);
  }
  return null;
}

export function getPracticeState(userName?: string): {
  solvedQuestionIds: string[];
  history: PracticeQuestionAttempt[];
} {
  try {
    const key = getPracticeStorageKey(userName);
    const data = localStorage.getItem(key);
    if (data) {
      const parsed = JSON.parse(data);
      return {
        solvedQuestionIds: Array.isArray(parsed.solvedQuestionIds) ? parsed.solvedQuestionIds : [],
        history: Array.isArray(parsed.history) ? parsed.history : [],
      };
    }
  } catch (e) {
    console.error('Failed to load practice state', e);
  }
  return { solvedQuestionIds: [], history: [] };
}

export function savePracticeAttempt(
  attempt: PracticeQuestionAttempt,
  userName?: string
): void {
  try {
    const key = getPracticeStorageKey(userName);
    const state = getPracticeState(userName);

    // If solved correctly, permanently record in solved list so it doesn't appear again
    if (attempt.status === 'CORRECT' && !state.solvedQuestionIds.includes(attempt.questionId)) {
      state.solvedQuestionIds.push(attempt.questionId);
    }

    // Add to history (newest first)
    state.history.unshift(attempt);

    // Cap history at 2,000 items to avoid quota issues
    if (state.history.length > 2000) {
      state.history = state.history.slice(0, 2000);
    }

    localStorage.setItem(key, JSON.stringify(state));
  } catch (e) {
    console.error('Failed to save practice attempt', e);
  }
}

export function resetPracticeTopic(questionIds: string[], userName?: string): void {
  try {
    const key = getPracticeStorageKey(userName);
    const state = getPracticeState(userName);
    const removeSet = new Set(questionIds);
    state.solvedQuestionIds = state.solvedQuestionIds.filter((id) => !removeSet.has(id));
    localStorage.setItem(key, JSON.stringify(state));
  } catch (e) {
    console.error('Failed to reset practice topic', e);
  }
}

export function getPracticeStats(
  userName?: string,
  filterSubject?: string,
  filterTopic?: string
): PracticeUserStats {
  const state = getPracticeState(userName);
  let history = state.history;

  if (filterSubject) {
    history = history.filter((h) => h.subject.toLowerCase() === filterSubject.toLowerCase());
  }
  if (filterTopic) {
    history = history.filter((h) => h.topic.toLowerCase() === filterTopic.toLowerCase());
  }

  const encounteredCount = history.length;
  const answeredAttempts = history.filter((h) => h.status !== 'SKIPPED');
  const answeredCount = answeredAttempts.length;
  const skippedCount = history.filter((h) => h.status === 'SKIPPED').length;
  const correctCount = history.filter((h) => h.status === 'CORRECT').length;
  const wrongCount = history.filter((h) => h.status === 'WRONG').length;

  const accuracyPercentage =
    answeredCount > 0 ? Math.round((correctCount / answeredCount) * 1000) / 10 : 0;

  const totalTimeSpentSeconds = history.reduce((sum, h) => sum + (h.timeSpentSeconds || 0), 0);
  const avgTimeSeconds =
    encounteredCount > 0 ? Math.round(totalTimeSpentSeconds / encounteredCount) : 0;

  const oneMarkAttempts = history.filter((h) => h.marks === 1);
  const twoMarkAttempts = history.filter((h) => h.marks === 2);

  const avgTime1MarkSeconds =
    oneMarkAttempts.length > 0
      ? Math.round(
          oneMarkAttempts.reduce((sum, h) => sum + (h.timeSpentSeconds || 0), 0) /
            oneMarkAttempts.length
        )
      : 0;

  const avgTime2MarkSeconds =
    twoMarkAttempts.length > 0
      ? Math.round(
          twoMarkAttempts.reduce((sum, h) => sum + (h.timeSpentSeconds || 0), 0) /
            twoMarkAttempts.length
        )
      : 0;

  const validTimes = history
    .map((h) => h.timeSpentSeconds)
    .filter((t) => typeof t === 'number' && t > 0);
  const minTimeSeconds = validTimes.length > 0 ? Math.min(...validTimes) : 0;
  const maxTimeSeconds = validTimes.length > 0 ? Math.max(...validTimes) : 0;

  return {
    encounteredCount,
    answeredCount,
    skippedCount,
    correctCount,
    wrongCount,
    accuracyPercentage,
    totalTimeSpentSeconds,
    avgTimeSeconds,
    avgTime1MarkSeconds,
    avgTime2MarkSeconds,
    minTimeSeconds,
    maxTimeSeconds,
    solvedQuestionIds: state.solvedQuestionIds,
    history,
  };
}

export const storage = {
  getUserProfile,
  saveUserProfile,
  getAllAttempts,
  getAttemptsByExam,
  saveAttempt,
  clearUserAttempts,
  deleteAttemptsForPaper,
  deleteSingleAttempt,
  getAttemptsForPaper,
  getAttemptsSummaryForPaper,
  getPaperIndex,
  getPaper,
  cleanImagePath,
  resolveImageUrl,
  getFallbackImageUrl,
  getPracticeIndex,
  getPracticeQuestion,
  getPracticeState,
  savePracticeAttempt,
  resetPracticeTopic,
  getPracticeStats,
};
