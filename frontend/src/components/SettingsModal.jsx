import React, { useState, useEffect } from 'react';
import { 
  X, 
  Settings, 
  Clock, 
  Search, 
  MapPin, 
  CheckCircle2, 
  Activity,
  Sliders,
  User,
  DollarSign,
  FileText
} from 'lucide-react';
import { api } from '../api';

export default function SettingsModal({ onClose, onSettingsUpdated }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    full_name: "Abhishek Verma",
    email: "abhishek.verma.6561@gmail.com",
    phone: "+91-6307801566",
    resume_path: "/home/abhishek_verma/Desktop/Abhishek_Verma_Resume.pdf",
    current_ctc: "6 LPA",
    expected_ctc: "12 - 15 LPA",
    keywords: "Spring Boot, Java Developer, Microservices, Backend Developer",
    target_experience: 2.0,
    experience_tolerance: 0.5,
    location: "All India, Remote, Noida, Bangalore, Pune, Hyderabad, Gurgaon",
    auto_scrape_enabled: true,
    scrape_interval_minutes: 30
  });
  const [msg, setMsg] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getSettings();
        if (data) setSettings((prev) => ({ ...prev, ...data }));
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMsg('');
    try {
      const updated = await api.updateSettings(settings);
      setSettings(updated);
      setMsg('Profile & Job Hunter Preferences saved to AWS RDS!');
      if (onSettingsUpdated) onSettingsUpdated();
      setTimeout(() => setMsg(''), 3000);
    } catch (err) {
      setMsg('Failed to update settings: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl max-h-[92vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm sm:text-base text-white">Candidate Profile & Hunter Preferences</h3>
              <p className="text-[11px] sm:text-xs text-slate-400">Configure your professional profile, CTC, keywords, and 24/7 scraper</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400">Loading settings from AWS RDS...</div>
        ) : (
          <form onSubmit={handleSave} className="p-4 sm:p-6 space-y-4 overflow-y-auto">
            
            {/* Candidate Identity */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Full Name:</label>
                <input
                  type="text"
                  value={settings.full_name || ""}
                  onChange={(e) => setSettings({ ...settings, full_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200"
                  placeholder="Abhishek Verma"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Email Address:</label>
                <input
                  type="email"
                  value={settings.email || ""}
                  onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200"
                  placeholder="abhishek.verma.6561@gmail.com"
                />
              </div>
            </div>

            {/* CTC Expectations */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Current CTC:</label>
                <input
                  type="text"
                  value={settings.current_ctc || ""}
                  onChange={(e) => setSettings({ ...settings, current_ctc: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200"
                  placeholder="e.g. 6 LPA"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Expected CTC:</label>
                <input
                  type="text"
                  value={settings.expected_ctc || ""}
                  onChange={(e) => setSettings({ ...settings, expected_ctc: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200"
                  placeholder="e.g. 12 - 15 LPA"
                />
              </div>
            </div>

            {/* Resume File Path */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Active Resume Path on Machine:</label>
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-sky-400 shrink-0" />
                <input
                  type="text"
                  value={settings.resume_path || ""}
                  onChange={(e) => setSettings({ ...settings, resume_path: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200 font-mono"
                  placeholder="/home/abhishek_verma/Desktop/Abhishek_Verma_Resume.pdf"
                />
              </div>
            </div>

            {/* Target Keywords */}
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 mb-1">
                <label className="text-xs font-semibold text-slate-300">
                  Target Backend Keywords (Comma-separated):
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setSettings({
                      ...settings,
                      keywords: "Java Developer, Spring Boot, Java Backend, SDE 1, Java Microservices, Java 17, PostgreSQL, REST API",
                      location: "Noida, Gurgaon, Delhi NCR, Bangalore, Pune, Hyderabad, Remote, Pan India",
                      target_experience: 2.0
                    });
                  }}
                  className="text-[11px] text-sky-400 hover:text-sky-300 font-semibold bg-sky-950/60 px-2 py-0.5 rounded border border-sky-500/30 transition flex items-center gap-1 self-start sm:self-auto"
                >
                  ✨ Auto-Fill Best 2 YOE Keywords
                </button>
              </div>
              <input
                type="text"
                value={settings.keywords}
                onChange={(e) => setSettings({ ...settings, keywords: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200"
                placeholder="Spring Boot, Java Developer, Microservices, Backend Developer"
              />
            </div>

            {/* Target Experience & Locations */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Target Experience:</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="10"
                    value={settings.target_experience}
                    onChange={(e) => setSettings({ ...settings, target_experience: parseFloat(e.target.value) || 2.0 })}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200"
                  />
                  <span className="text-xs text-amber-300 font-semibold px-2.5 py-1 bg-amber-950/60 border border-amber-500/20 rounded-lg">
                    {settings.target_experience} Yrs
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Preferred Locations:</label>
                <input
                  type="text"
                  value={settings.location}
                  onChange={(e) => setSettings({ ...settings, location: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2 text-xs text-slate-200"
                  placeholder="All India, Remote, Noida, Bangalore, Pune, Hyderabad"
                />
              </div>
            </div>

            {/* LinkedIn Live Search Banner */}
            <div className="bg-sky-950/40 p-3.5 rounded-xl border border-sky-500/30 flex items-start space-x-3">
              <div className="p-2 rounded-lg bg-sky-600 text-white mt-0.5">
                <Search className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <span className="text-xs font-bold text-sky-200 block">LinkedIn India Hunter Active</span>
                <p className="text-[11px] text-slate-300 mt-0.5 leading-relaxed">
                  Continuously queries live LinkedIn job posts for <strong>Spring Boot & Java Backend Developer</strong> in India with direct apply links and HR contact extraction.
                </p>
              </div>
            </div>

            {/* 24/7 Background Scheduler Configuration */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 pt-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-white block">24/7 Automated Background Hunter</span>
                  <span className="text-[11px] text-slate-400">Continuously searches online portals and triggers instant alerts.</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.auto_scrape_enabled}
                    onChange={(e) => setSettings({ ...settings, auto_scrape_enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </label>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1">Hunt Frequency:</label>
                <select
                  value={settings.scrape_interval_minutes}
                  onChange={(e) => setSettings({ ...settings, scrape_interval_minutes: parseInt(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:border-sky-500 focus:outline-none"
                >
                  <option value={1}>⚡ Every 1 Minute (Real-time Live Stream)</option>
                  <option value={2}>🚀 Every 2 Minutes (Rapid Hunt)</option>
                  <option value={5}>Every 5 Minutes (Active)</option>
                  <option value={15}>Every 15 Minutes</option>
                  <option value={30}>Every 30 Minutes</option>
                </select>
              </div>
            </div>

            {msg && (
              <div className="p-3 bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 rounded-xl text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{msg}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={saving}
              className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white font-semibold text-xs transition shadow-md shadow-sky-900/30"
            >
              {saving ? "Saving to AWS RDS..." : "Save Profile & Preferences"}
            </button>
          </form>
        )}

      </div>
    </div>
  );
}
