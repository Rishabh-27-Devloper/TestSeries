import type { ExamResult, PaperIndexItem, UserProfile } from '../types';

const PROFILE_KEY = 'test_series_user_profile';
const ATTEMPTS_KEY = 'test_series_user_attempts';

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
 * On local dev, attempts local path first.
 * In production (Vercel / Netlify), resolves to fast GitHub Raw CDN mirror so all 5,000 slices load without bundling ~500MB into client.
 */
export function resolveImageUrl(imgUrl?: string): string {
  if (!imgUrl) return '';
  if (imgUrl.startsWith('data:') || imgUrl.startsWith('http://') || imgUrl.startsWith('https://')) {
    return imgUrl;
  }
  const clean = cleanImagePath(imgUrl);

  const isLocalhost =
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  if (isLocalhost) {
    return `/${clean}`;
  }

  // Deployed / Production on Vercel, Netlify, etc. -> Direct GitHub Raw CDN
  return `https://raw.githubusercontent.com/Rishabh-27-Devloper/TestSeries/main/${clean}`;
}

/**
 * Secondary mirror fallback using jsDelivr global CDN in case of network restriction on raw.githubusercontent.com
 */
export function getFallbackImageUrl(imgUrl?: string): string {
  if (!imgUrl) return '';
  const clean = cleanImagePath(imgUrl);
  return `https://cdn.jsdelivr.net/gh/Rishabh-27-Devloper/TestSeries@main/${clean}`;
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
};
