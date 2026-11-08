import React, { useState } from 'react';
import { X, User, Save, Check } from 'lucide-react';
import type { UserProfile } from '../../types';
import { getUserProfile, saveUserProfile } from '../../utils/storage';

interface UserProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProfileUpdated?: (profile: UserProfile) => void;
}

export const UserProfileModal: React.FC<UserProfileModalProps> = ({
  isOpen,
  onClose,
  onProfileUpdated,
}) => {
  const [profile, setProfile] = useState<UserProfile>(getUserProfile());
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

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
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#1a56a5] text-white">
          <div className="flex items-center gap-2">
            <User size={20} />
            <h2 className="font-semibold text-base">Candidate Profile</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-red-500 rounded transition text-white"
            title="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-4 text-sm">
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
              placeholder="e.g. John Doe"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Roll / Registration Number
            </label>
            <input
              type="text"
              required
              value={profile.rollNumber}
              onChange={(e) => setProfile({ ...profile, rollNumber: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-[#1a56a5] focus:border-transparent outline-none text-slate-800 font-mono"
              placeholder="e.g. GATE25-EC001"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Branch / Discipline
              </label>
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
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Target Year
              </label>
              <select
                value={profile.targetYear}
                onChange={(e) => setProfile({ ...profile, targetYear: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-[#1a56a5] focus:border-transparent outline-none text-slate-800"
              >
                <option value="GATE 2025">GATE 2025</option>
                <option value="GATE 2026">GATE 2026</option>
                <option value="GATE 2027">GATE 2027</option>
              </select>
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
              placeholder="student@gate.ac.in"
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
                saved ? 'bg-emerald-600' : 'bg-[#1a56a5] hover:bg-blue-700'
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
