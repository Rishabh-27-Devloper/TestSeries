import type { ExamResult, PaperIndexItem, UserProfile } from '../types';

const PROFILE_KEY = 'test_series_user_profile';
const ATTEMPTS_KEY = 'test_series_attempts';

const DEFAULT_PROFILE: UserProfile = {
  name: 'Prakhar Shukla',
  rollNumber: 'GATE25-EC001',
  phoneNumber: '+91 9123456789',
  email: 'prakhar@gate.ac.in',
  targetYear: 'GATE 2025',
  branch: 'Electronics & Communication',
};

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

export async function loadInitialAttempts(): Promise<ExamResult[]> {
  const existing = getAllAttempts();
  if (existing.length > 0) return existing;

  // Load bundled sample attempts
  try {
    const resp = await fetch('/data/attempts_manifest.json');
    if (resp.ok) {
      const attempts: ExamResult[] = await resp.json();
      if (Array.isArray(attempts) && attempts.length > 0) {
        localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(attempts));
        return attempts;
      }
    }
  } catch (e) {
    console.warn('Could not load attempts manifest', e);
  }
  return [];
}

export function getAllAttempts(): ExamResult[] {
  try {
    const data = localStorage.getItem(ATTEMPTS_KEY);
    if (data) {
      const list: ExamResult[] = JSON.parse(data);
      return list.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
    }
  } catch (e) {
    console.error('Failed to load attempts', e);
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

export function resolveImageUrl(imgUrl?: string): string {
  if (!imgUrl) return '';
  if (imgUrl.startsWith('data:') || imgUrl.startsWith('http://') || imgUrl.startsWith('https://')) {
    return imgUrl;
  }
  const clean = imgUrl.replace(/^(\.\/|\/)/, '').replace(/\\/g, '/');
  // First try local public path; if that fails or when hosted online, GitHub raw can be used as fallback
  return `/${clean}`;
}

export function getFallbackImageUrl(imgUrl?: string): string {
  if (!imgUrl) return '';
  const clean = imgUrl.replace(/^(\.\/|\/)/, '').replace(/\\/g, '/');
  return `https://raw.githubusercontent.com/Rishabh-27-Devloper/TestSeries/main/${clean}`;
}

export const storage = {
  getUserProfile,
  saveUserProfile,
  loadInitialAttempts,
  getAllAttempts,
  saveAttempt,
  getAttemptsForPaper,
  getAttemptsSummaryForPaper,
  getPaperIndex,
  getPaper,
  resolveImageUrl,
  getFallbackImageUrl,
};
