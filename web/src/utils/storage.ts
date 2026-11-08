import type { ExamResult, PaperIndexItem, UserProfile } from '../types';

const PROFILE_KEY = 'test_series_user_profile';

const DEFAULT_PROFILE: UserProfile = {
  name: 'Candidate',
  rollNumber: 'GATE25-EC001',
  phoneNumber: '+91 9123456789',
  email: 'candidate@gate.ac.in',
  targetYear: 'GATE 2025',
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
    if (data) return JSON.parse(data);
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

// User-specific storage key generator to ensure attempts never mix between candidates
export function getUserAttemptsKey(rollNumber?: string): string {
  const roll = rollNumber || getUserProfile().rollNumber || 'DEFAULT';
  const cleanRoll = roll.trim().toUpperCase().replace(/[^A-Z0-9_-]/g, '_');
  return `test_series_attempts_${cleanRoll}`;
}

export function getAllAttempts(rollNumber?: string): ExamResult[] {
  try {
    const key = getUserAttemptsKey(rollNumber);
    const data = localStorage.getItem(key);
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
    const key = getUserAttemptsKey(result.rollNumber);
    const list = getAllAttempts(result.rollNumber);
    const updated = [result, ...list];
    localStorage.setItem(key, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to save attempt', e);
  }
}

export function clearUserAttempts(rollNumber?: string): void {
  try {
    const key = getUserAttemptsKey(rollNumber);
    localStorage.removeItem(key);
  } catch (e) {
    console.error('Failed to clear user attempts', e);
  }
}

export function getAttemptsForPaper(paperId: string, rollNumber?: string): ExamResult[] {
  return getAllAttempts(rollNumber).filter((a) => a.paperId === paperId);
}

export function getAttemptsSummaryForPaper(paperId: string, rollNumber?: string): {
  attemptCount: number;
  lastAttempt?: ExamResult;
  bestAttempt?: ExamResult;
} {
  const list = getAttemptsForPaper(paperId, rollNumber);
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
  getUserAttemptsKey,
  getAllAttempts,
  saveAttempt,
  clearUserAttempts,
  getAttemptsForPaper,
  getAttemptsSummaryForPaper,
  getPaperIndex,
  getPaper,
  cleanImagePath,
  resolveImageUrl,
  getFallbackImageUrl,
};
