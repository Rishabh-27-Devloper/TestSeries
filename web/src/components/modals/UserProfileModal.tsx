import React, { useState } from 'react';
import { X, User, Save, Check, GraduationCap, Stethoscope } from 'lucide-react';
import type { UserProfile } from '../../types';
import { getUserProfile, saveUserProfile } from '../../utils/storage';

interface UserProfileModalProps {
  isOpen: boolean;
  selectedExam?: 'GATE' | 'NEET';
  onClose: () => void;
  onProfileUpdated?: (profile: UserProfile) => void;
}

export const UserProfileModal: React.FC<UserProfileModalProps> = ({
  isOpen,
  selectedExam,
  onClose,
  onProfileUpdated,
}) => {
  const [profile, setProfile] = useState<UserProfile>(() => {
    const p = getUserProfile();
    if (selectedExam && !p.targetExam) {
      p.targetExam = selectedExam;
    }
    return p;
  });
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const activeExam = profile.targetExam || selectedExam || 'GATE';

  const handleSelectExam = (exam: 'GATE' | 'NEET') => {
    if (exam === 'NEET') {
      setProfile({
        ...profile,
        targetExam: 'NEET',
        branch: 'NEET UG (Medical Entrance)',
        targetYear: profile.targetYear.includes('202') ? profile.targetYear.replace('GATE', 'NEET') : 'NEET 2026',
      });
    } else {
      setProfile({
        ...profile,
        targetExam: 'GATE',
        branch: 'Electronics & Communication',
        targetYear: profile.targetYear.includes('202') ? profile.targetYear.replace('NEET', 'GATE') : 'GATE 2026',
      });
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    saveUserProfile(profile);
    if (onProfileUpdated) {
      onProfileUpdated(profile);
    }
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="flex flex-col bg-white rounded-lg shadow-2xl max-w-md w-full overflow-hidden border border-slate-300">
        {/* Header */}
        <div className={`flex items-center justify-between px-5 py-3.5 ${activeExam === 'NEET' ? 'bg-teal-700' : 'bg-[#1a56a5]'} text-white transition-colors`}>
          <div className="flex items-center gap-2">
            <User size={20} />
            <h2 className="font-semibold text-base">Candidate Profile</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/20 rounded transition text-white"
            title="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-4 text-sm">
          {/* Target Exam Portal Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1.5">
              Target Examination
            </label>
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-lg">
              <button
                type="button"
                onClick={() => handleSelectExam('GATE')}
                className={`py-1.5 px-3 rounded-md text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                  activeExam === 'GATE'
                    ? 'bg-[#1a56a5] text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-200'
                }`}
              >
                <GraduationCap size={15} />
                <span>GATE EC</span>
              </button>
              <button
                type="button"
                onClick={() => handleSelectExam('NEET')}
                className={`py-1.5 px-3 rounded-md text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                  activeExam === 'NEET'
                    ? 'bg-teal-700 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-200'
                }`}
              >
                <Stethoscope size={15} />
                <span>NEET UG</span>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Candidate Full Name
            </label>
            <input
              type="text"
              required
              value={profile.name}
              onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-[#1a56a5] focus:border-transparent outline-none text-slate-800"
              placeholder="e.g. Anand Shukla"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                {activeExam === 'NEET' ? 'Academic Stream' : 'Branch / Discipline'}
              </label>
              {activeExam === 'NEET' ? (
                <select
                  value={profile.branch}
                  onChange={(e) => setProfile({ ...profile, branch: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-teal-700 focus:border-transparent outline-none text-slate-800"
                >
                  <option value="NEET UG (Medical Entrance)">NEET UG Aspirant</option>
                  <option value="Class 11 Pre-Medical">Class 11 Pre-Medical</option>
                  <option value="Class 12 Pre-Medical">Class 12 Pre-Medical</option>
                  <option value="Dropper / Repeater Batch">Dropper / Repeater</option>
                </select>
              ) : (
                <select
                  value={profile.branch}
                  onChange={(e) => setProfile({ ...profile, branch: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-[#1a56a5] focus:border-transparent outline-none text-slate-800"
                >
                  <option value="Electronics & Communication">GATE EC (ECE)</option>
                  <option value="Electrical Engineering">GATE EE</option>
                  <option value="Computer Science">GATE CS/IT</option>
                  <option value="Instrumentation">GATE IN</option>
                  <option value="Mechanical">GATE ME</option>
                  <option value="Civil">GATE CE</option>
                </select>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Target Year
              </label>
              {activeExam === 'NEET' ? (
                <select
                  value={profile.targetYear}
                  onChange={(e) => setProfile({ ...profile, targetYear: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-teal-700 focus:border-transparent outline-none text-slate-800"
                >
                  <option value="NEET 2025">NEET 2025</option>
                  <option value="NEET 2026">NEET 2026</option>
                  <option value="NEET 2027">NEET 2027</option>
                </select>
              ) : (
                <select
                  value={profile.targetYear}
                  onChange={(e) => setProfile({ ...profile, targetYear: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-[#1a56a5] focus:border-transparent outline-none text-slate-800"
                >
                  <option value="GATE 2025">GATE 2025</option>
                  <option value="GATE 2026">GATE 2026</option>
                  <option value="GATE 2027">GATE 2027</option>
                </select>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Email / Contact
            </label>
            <input
              type="email"
              value={profile.email || ''}
              onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-[#1a56a5] focus:border-transparent outline-none text-slate-800"
              placeholder={activeExam === 'NEET' ? 'student@neet.nta.ac.in' : 'student@gate.ac.in'}
            />
          </div>

          <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-slate-300 text-slate-600 rounded hover:bg-slate-100 font-medium text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saved}
              className={`flex items-center gap-1.5 px-5 py-2 text-white rounded font-medium text-xs transition ${
                saved
                  ? 'bg-emerald-600'
                  : activeExam === 'NEET'
                  ? 'bg-teal-700 hover:bg-teal-800'
                  : 'bg-[#1a56a5] hover:bg-blue-700'
              }`}
            >
              {saved ? (
                <>
                  <Check size={16} /> Saved!
                </>
              ) : (
                <>
                  <Save size={16} /> Save Profile
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
