import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Copy, 
  Check, 
  Save, 
  ExternalLink, 
  User, 
  CheckCircle, 
  X, 
  Layers, 
  MousePointer, 
  ShieldCheck,
  FolderOpen,
  Bookmark,
  Building2,
  Phone,
  Mail,
  MapPin,
  Briefcase,
  Clock
} from 'lucide-react';
import { api } from '../api';

export default function AutoApplyModal({ isOpen, onClose, onRefreshJobs }) {
  const [activeTab, setActiveTab] = useState('EXTENSION'); // EXTENSION, PROFILE
  const [profile, setProfile] = useState({
    full_name: 'Abhishek Verma',
    email: 'abhishek.verma.6561@gmail.com',
    phone: '6307801566',
    current_company: 'Rapipay Fintech Private Limited',
    current_designation: 'Backend Software Engineer',
    total_experience: '2+ Years',
    current_ctc: '9.5 LPA',
    expected_ctc: '15 LPA',
    notice_period: 'Serving Notice Period (30 Days)',
    location: 'Noida, Uttar Pradesh',
    linkedin_url: 'https://www.linkedin.com/in/abhishek-verma-backend',
    github_url: 'https://github.com/AbhishekVerma-dev',
    cover_letter_template: 'Backend Software Engineer with 2+ years of enterprise experience building scalable fintech platforms using Java, Spring Boot, Microservices, PostgreSQL, Kafka, and Redis.'
  });

  const [copiedPath, setCopiedPath] = useState(false);
  const [copiedBookmarklet, setCopiedBookmarklet] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const backendHost = typeof window !== "undefined" && window.location ? `${window.location.protocol}//${window.location.hostname}:8000` : "http://localhost:8000";
  const EXTENSION_PATH = "<cloned_directory>/JobApplyApp/extension";
  const BOOKMARKLET_CODE = `javascript:(function(){if(window.__JOBAPPLY_INJECTED__){const f=document.getElementById('jobapply-autofill-fab');if(f){f.click();return;}}const s=document.createElement('script');s.src='${backendHost}/extension/content.js?v='+Date.now();const c=document.createElement('link');c.rel='stylesheet';c.href='${backendHost}/extension/content.css?v='+Date.now();document.head.appendChild(c);document.body.appendChild(s);setTimeout(()=>{const f=document.getElementById('jobapply-autofill-fab');if(f)f.click();},350);})();`;

  useEffect(() => {
    if (isOpen) {
      fetchProfile();
    }
  }, [isOpen]);

  const fetchProfile = async () => {
    try {
      const data = await api.getAutoApplyProfile();
      if (data) {
        setProfile((prev) => ({
          ...prev,
          ...data,
          phone: (data.phone || '6307801566').replace(/\D/g, '').slice(-10) // Strictly 10 digits
        }));
      }
    } catch (err) {
      console.error("Failed to load profile:", err);
    }
  };

  const handleCopyPath = () => {
    navigator.clipboard.writeText(EXTENSION_PATH);
    setCopiedPath(true);
    setTimeout(() => setCopiedPath(false), 2500);
  };

  const handleCopyBookmarklet = () => {
    navigator.clipboard.writeText(BOOKMARKLET_CODE);
    setCopiedBookmarklet(true);
    setTimeout(() => setCopiedBookmarklet(false), 2500);
  };

  const handleProfileChange = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await api.updateAutoApplyProfile(profile);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert("Failed to save profile: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40 gap-2">
          <div className="flex items-center space-x-2.5 sm:space-x-3 min-w-0">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-sky-600 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20 shrink-0">
              <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-amber-300" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm sm:text-base font-bold text-white flex items-center gap-1.5 sm:gap-2 truncate">
                <span className="truncate">1-Click Form Autofill Hub</span>
                <span className="text-[10px] sm:text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shrink-0">
                  Chrome Extension
                </span>
              </h2>
              <p className="text-[11px] sm:text-xs text-slate-400 truncate">
                Floating icon on any page (Virtusa, Workday, Naukri, LinkedIn) fills fields in 1-Click.
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-3 sm:px-6 pt-2 overflow-x-auto no-scrollbar flex-nowrap">
          <button
            onClick={() => setActiveTab('EXTENSION')}
            className={`flex items-center space-x-2 px-3 sm:px-4 py-2.5 text-xs font-semibold rounded-t-xl transition border-b-2 shrink-0 whitespace-nowrap ${
              activeTab === 'EXTENSION'
                ? "border-emerald-500 text-emerald-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <MousePointer className="w-3.5 h-3.5" />
            <span>⚡ Floating Icon & Extension</span>
          </button>

          <button
            onClick={() => setActiveTab('PROFILE')}
            className={`flex items-center space-x-2 px-3 sm:px-4 py-2.5 text-xs font-semibold rounded-t-xl transition border-b-2 shrink-0 whitespace-nowrap ${
              activeTab === 'PROFILE'
                ? "border-sky-500 text-sky-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>👤 Candidate Autofill Profile</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-4 sm:p-6 overflow-y-auto flex-1 space-y-5 sm:space-y-6">

          {/* TAB 1: EXTENSION SETUP & BOOKMARKLET */}
          {activeTab === 'EXTENSION' && (
            <div className="space-y-6">
              
              {/* How it works banner */}
              <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-sky-950/40 p-5 rounded-2xl border border-emerald-500/30 flex items-start gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-sky-500 to-emerald-500 flex items-center justify-center shrink-0 shadow-lg shadow-emerald-500/30 text-white font-bold text-xl">
                  ⚡
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    How The Floating "Gol Icon" Works
                  </h3>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                    Jab aap kisi bhi job page (e.g. <strong>Virtusa</strong>, <strong>Workday</strong>, <strong>Naukri</strong>, <strong>LinkedIn</strong>) par honge, screen ke right side me ek <strong>round floating icon (⚡)</strong> dikhai dega. Usko click karte hi aapka:
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2 text-[11px] text-slate-200 font-medium">
                    <span className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Title (Mr.) & Full Name</span>
                    <span className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Phone: 6307801566 (10 Digits)</span>
                    <span className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Country & State (UP)</span>
                    <span className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> City (Noida) & Zip (201301)</span>
                    <span className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Company (Rapipay) & 2 Yrs</span>
                    <span className="flex items-center gap-1.5"><CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Notice Period (30 Days)</span>
                  </div>
                </div>
              </div>

              {/* Option A: Install Chrome Extension (Permanent) */}
              <div className="bg-slate-950/70 p-5 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-sky-400" />
                    Option 1: Load Chrome Extension in 10 Seconds (Permanent)
                  </h4>
                  <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                    Recommended
                  </span>
                </div>

                <div className="space-y-3 text-xs text-slate-300">
                  <div className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-slate-800 text-sky-400 flex items-center justify-center font-bold text-[11px] shrink-0">1</span>
                    <span>Google Chrome me new tab kholein aur open karein: <code className="text-sky-300 bg-slate-900 px-2 py-0.5 rounded font-mono">chrome://extensions</code></span>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-slate-800 text-sky-400 flex items-center justify-center font-bold text-[11px] shrink-0">2</span>
                    <span>Top-right corner me <strong>"Developer mode"</strong> ka toggle switch ON karein.</span>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-slate-800 text-sky-400 flex items-center justify-center font-bold text-[11px] shrink-0">3</span>
                    <span>Top-left me <strong>"Load unpacked"</strong> button par click karein aur ye folder select karein:</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs text-sky-300">
                  <span className="truncate flex-1">{EXTENSION_PATH}</span>
                  <button
                    onClick={handleCopyPath}
                    className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold flex items-center gap-1.5 text-xs transition active:scale-95 shrink-0"
                  >
                    {copiedPath ? <Check className="w-3.5 h-3.5 text-white" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedPath ? "Copied!" : "Copy Path"}</span>
                  </button>
                </div>
              </div>

              {/* Option B: Instant Bookmarklet (Zero Install) */}
              <div className="bg-slate-950/70 p-5 rounded-2xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <Bookmark className="w-4 h-4 text-amber-400" />
                    Option 2: Instant Bookmarklet (Zero Install — Run Right Now on Virtusa)
                  </h4>
                  <span className="text-[11px] font-bold text-amber-300 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
                    Instant 1-Click
                  </span>
                </div>

                <p className="text-xs text-slate-400">
                  Agar aap abhi bina extension install kiye Virtusa wale page ko fill karna chahte hain, toh ye script copy karein aur browser Console me ya Bookmarks bar me chala dijiye:
                </p>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyBookmarklet}
                    className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition active:scale-95"
                  >
                    {copiedBookmarklet ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    <span>{copiedBookmarklet ? "Bookmarklet Script Copied to Clipboard!" : "📋 Copy 1-Click Bookmarklet Script"}</span>
                  </button>
                </div>
                <span className="text-[11px] text-slate-500 block">
                  💡 Virtusa tab par jayein &rarr; Right-click &rarr; Inspect (DevTools) &rarr; Console tab me paste karke Enter dabayein, saari details turant fill ho jayengi!
                </span>
              </div>

            </div>
          )}

          {/* TAB 2: PROFILE DATA */}
          {activeTab === 'PROFILE' && (
            <form onSubmit={handleSaveProfile} className="space-y-5">
              
              <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Candidate Profile for 1-Click Autofill
                  </h4>
                  <p className="text-[11px] text-slate-400">
                    The floating icon automatically pulls these values when autofilling forms.
                  </p>
                </div>
                {saveSuccess && (
                  <span className="text-xs text-emerald-400 font-bold flex items-center gap-1.5 animate-fadeIn">
                    <CheckCircle className="w-4 h-4" /> Saved Successfully!
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Full Name:</label>
                  <input
                    type="text"
                    value={profile.full_name || ''}
                    onChange={(e) => handleProfileChange('full_name', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Email:</label>
                  <input
                    type="email"
                    value={profile.email || ''}
                    onChange={(e) => handleProfileChange('email', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Phone Number (10 Digits Strictly):</label>
                  <input
                    type="tel"
                    value={profile.phone || ''}
                    onChange={(e) => handleProfileChange('phone', e.target.value.replace(/\D/g, '').slice(-10))}
                    placeholder="6307801566"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                  <span className="text-[10px] text-amber-400 mt-0.5 block">
                    Virtusa &amp; corporate portals error out if more than 10 digits. Fixed to 10 digits.
                  </span>
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Current Company:</label>
                  <input
                    type="text"
                    value={profile.current_company || ''}
                    onChange={(e) => handleProfileChange('current_company', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Current Designation:</label>
                  <input
                    type="text"
                    value={profile.current_designation || ''}
                    onChange={(e) => handleProfileChange('current_designation', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Total Experience:</label>
                  <input
                    type="text"
                    value={profile.total_experience || ''}
                    onChange={(e) => handleProfileChange('total_experience', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Current CTC:</label>
                  <input
                    type="text"
                    value={profile.current_ctc || ''}
                    onChange={(e) => handleProfileChange('current_ctc', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Expected CTC:</label>
                  <input
                    type="text"
                    value={profile.expected_ctc || ''}
                    onChange={(e) => handleProfileChange('expected_ctc', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">Notice Period:</label>
                  <input
                    type="text"
                    value={profile.notice_period || ''}
                    onChange={(e) => handleProfileChange('notice_period', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-300 block mb-1">City / Location:</label>
                  <input
                    type="text"
                    value={profile.location || ''}
                    onChange={(e) => handleProfileChange('location', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="font-semibold text-slate-300 block mb-1">LinkedIn Profile:</label>
                  <input
                    type="url"
                    value={profile.linkedin_url || ''}
                    onChange={(e) => handleProfileChange('linkedin_url', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-medium focus:border-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-6 py-2.5 rounded-xl font-bold text-xs bg-emerald-600 hover:bg-emerald-500 text-white flex items-center space-x-2 transition shadow-lg shadow-emerald-950/50 active:scale-95"
                >
                  <Save className="w-4 h-4" />
                  <span>{isSaving ? "Saving..." : "Save Profile Details"}</span>
                </button>
              </div>

            </form>
          )}

        </div>

      </div>
    </div>
  );
}
