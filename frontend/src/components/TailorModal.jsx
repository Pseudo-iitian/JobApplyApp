import React, { useState, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  Copy, 
  Check, 
  Mail, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw,
  Send,
  Download
} from 'lucide-react';
import { api } from '../api';

export default function TailorModal({ job, onClose }) {
  const [loading, setLoading] = useState(true);
  const [tailoredData, setTailoredData] = useState(null);
  const [activeTab, setActiveTab] = useState('summary'); // summary, bullets, email, cover
  const [copiedItem, setCopiedItem] = useState('');

  useEffect(() => {
    async function loadTailorData() {
      try {
        setLoading(true);
        const data = await api.tailorResume(job.id);
        setTailoredData(data);
      } catch (err) {
        console.error("Failed to tailor resume:", err);
      } finally {
        setLoading(false);
      }
    }
    if (job) {
      loadTailorData();
    }
  }, [job]);

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedItem(key);
    setTimeout(() => setCopiedItem(''), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-4xl max-h-[92vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/70 gap-2">
          <div className="flex items-center space-x-2.5 sm:space-x-3 min-w-0">
            <div className="p-2 sm:p-2.5 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white shadow-lg shadow-sky-500/20 shrink-0">
              <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <div className="min-w-0">
              <h3 className="font-bold text-sm sm:text-base text-white flex items-center gap-1.5 sm:gap-2 truncate">
                <span className="truncate">AI Resume Tailoring</span>
                <span className="text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20 shrink-0">
                  2 Yrs Exp
                </span>
              </h3>
              <p className="text-[11px] sm:text-xs text-slate-400 truncate">
                Customizing for <span className="text-slate-200 font-semibold">{job.title}</span> at <span className="text-slate-200 font-semibold">{job.company}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 shrink-0">
            {tailoredData && (
              <a
                href={`http://localhost:8000/api/jobs/${job.id}/download-tailored-resume`}
                target="_blank"
                rel="noreferrer"
                download
                className="flex items-center space-x-1.5 px-2.5 sm:px-3.5 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-950/40 transition active:scale-95"
                title="Download customized ATS PDF resume"
              >
                <Download className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                <span className="hidden sm:inline">Download Tailored PDF</span>
                <span className="sm:hidden">PDF</span>
              </a>
            )}
            <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center space-y-4">
            <RefreshCw className="w-9 h-9 text-sky-400 animate-spin" />
            <p className="text-sm text-slate-300 font-medium">Analyzing Job Description & Tailoring Java Experience...</p>
            <p className="text-xs text-slate-500">Injecting target keywords and optimizing ATS score</p>
          </div>
        ) : tailoredData ? (
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 sm:space-y-6">
            
            {/* Top Match Score & Overview Banner */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
              {/* ATS Score */}
              <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl flex items-center space-x-4">
                <div className="relative w-14 h-14 flex items-center justify-center rounded-full bg-emerald-500/10 border-2 border-emerald-500/40 text-emerald-400 font-black text-xl shrink-0">
                  {tailoredData.match_score}%
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">ATS Match Score</span>
                  <span className="text-sm font-bold text-slate-200">Excellent 2-Year Fit</span>
                </div>
              </div>

              {/* Rationale */}
              <div className="md:col-span-2 bg-slate-950/80 border border-slate-800 p-4 rounded-xl flex flex-col justify-center">
                <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5 mb-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Fit Analysis
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {tailoredData.summary_of_match}
                </p>
              </div>
            </div>

            {/* Missing Keywords Checklist */}
            {tailoredData.missing_keywords && tailoredData.missing_keywords.length > 0 && (
              <div className="bg-amber-950/20 border border-amber-500/20 p-4 rounded-xl">
                <span className="text-xs font-semibold text-amber-300 flex items-center gap-1.5 mb-2">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" /> Recommended Keywords to Highlight in Resume:
                </span>
                <div className="flex flex-wrap gap-2">
                  {tailoredData.missing_keywords.map((kw, idx) => (
                    <span key={idx} className="px-2.5 py-1 bg-amber-900/40 text-amber-200 border border-amber-500/30 rounded-lg text-xs font-medium">
                      + {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Tab Navigation */}
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 overflow-x-auto no-scrollbar flex-nowrap">
              <button
                onClick={() => setActiveTab('summary')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 whitespace-nowrap ${
                  activeTab === 'summary' ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Tailored Summary
              </button>
              <button
                onClick={() => setActiveTab('bullets')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 whitespace-nowrap ${
                  activeTab === 'bullets' ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                ATS Experience Bullets
              </button>
              <button
                onClick={() => setActiveTab('email')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 whitespace-nowrap ${
                  activeTab === 'email' ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                HR Cold Email Draft
              </button>
              <button
                onClick={() => setActiveTab('cover')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 whitespace-nowrap ${
                  activeTab === 'cover' ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Cover Letter
              </button>
            </div>

            {/* Tab Content Display */}
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 relative">
              
              {/* Tab 1: Summary */}
              {activeTab === 'summary' && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Targeted Professional Summary</span>
                    <button
                      onClick={() => copyToClipboard(tailoredData.tailored_summary, 'summary')}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 font-medium transition"
                    >
                      {copiedItem === 'summary' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedItem === 'summary' ? "Copied" : "Copy Summary"}</span>
                    </button>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {tailoredData.tailored_summary}
                  </p>
                </div>
              )}

              {/* Tab 2: Bullets */}
              {activeTab === 'bullets' && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Optimized Java 2-Yr Experience Bullets</span>
                    <button
                      onClick={() => copyToClipboard(tailoredData.tailored_experience_bullets.join('\n• '), 'bullets')}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 font-medium transition"
                    >
                      {copiedItem === 'bullets' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedItem === 'bullets' ? "Copied" : "Copy All Bullets"}</span>
                    </button>
                  </div>
                  <ul className="space-y-3">
                    {tailoredData.tailored_experience_bullets.map((bullet, idx) => (
                      <li key={idx} className="flex items-start space-x-2.5 text-sm text-slate-200">
                        <span className="text-sky-400 font-bold mt-0.5">•</span>
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Tab 3: HR Email Draft */}
              {activeTab === 'email' && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Ready-To-Send HR Email Pitch</span>
                    <button
                      onClick={() => copyToClipboard(tailoredData.hr_email_draft, 'email')}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 font-medium transition"
                    >
                      {copiedItem === 'email' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedItem === 'email' ? "Copied" : "Copy Email"}</span>
                    </button>
                  </div>
                  {job.hr_email && (
                    <div className="mb-3 p-2.5 rounded-xl bg-sky-950/40 border border-sky-500/20 text-xs text-sky-300 flex items-center justify-between">
                      <span>Recipient: <strong>{job.hr_email}</strong></span>
                      <a
                        href={`https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(job.hr_email)}&su=${encodeURIComponent(`Application: ${job.title} - 2 Years Exp (Java / Spring Boot)`)}&body=${encodeURIComponent(tailoredData.hr_email_draft)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-md shadow-red-950/40 transition active:scale-95"
                        title="Open compose window in Google Gmail"
                      >
                        <Mail className="w-3.5 h-3.5" /> Open in Gmail
                      </a>
                    </div>
                  )}
                  <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                    {tailoredData.hr_email_draft}
                  </pre>
                </div>
              )}

              {/* Tab 4: Cover Letter */}
              {activeTab === 'cover' && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Custom Cover Letter</span>
                    <button
                      onClick={() => copyToClipboard(tailoredData.tailored_cover_letter, 'cover')}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 font-medium transition"
                    >
                      {copiedItem === 'cover' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedItem === 'cover' ? "Copied" : "Copy Cover Letter"}</span>
                    </button>
                  </div>
                  <pre className="text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed">
                    {tailoredData.tailored_cover_letter}
                  </pre>
                </div>
              )}

            </div>

          </div>
        ) : (
          <div className="py-12 text-center text-rose-400 text-xs">
            Failed to load AI tailoring suggestions. Please try again.
          </div>
        )}

      </div>
    </div>
  );
}
