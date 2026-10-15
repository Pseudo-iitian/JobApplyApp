import React, { useState, useEffect } from 'react';
import { 
  HelpCircle, 
  X, 
  Sparkles, 
  Check, 
  Copy, 
  RefreshCw, 
  Building2, 
  BrainCircuit, 
  Layers, 
  MessageSquare,
  BookOpen,
  Award
} from 'lucide-react';
import { api } from '../api';

export default function InterviewPrepModal({ job, onClose }) {
  const [prepData, setPrepData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const fetchPrep = async () => {
    try {
      setLoading(true);
      const data = await api.getInterviewPrep(job.id);
      setPrepData(data);
    } catch (err) {
      console.error("Failed to load interview prep:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrep();
  }, [job.id]);

  const handleCopyAll = () => {
    if (!prepData) return;
    let text = `🎯 INTERVIEW PREP CHEAT SHEET: ${job.title} @ ${job.company}\n\n`;
    text += `=== TOP TECHNICAL QUESTIONS ===\n`;
    (prepData.top_technical_questions || []).forEach((q, idx) => {
      text += `${idx + 1}. [${q.category || 'Tech'}] ${q.question}\n   💡 Key Answer: ${q.hint}\n\n`;
    });
    text += `=== ARCHITECTURE TALKING POINTS ===\n`;
    (prepData.architecture_talking_points || []).forEach((pt, idx) => {
      text += `• ${pt}\n`;
    });
    text += `\n=== QUESTIONS TO ASK THE INTERVIEWER ===\n`;
    (prepData.smart_questions_to_ask_interviewer || []).forEach((q, idx) => {
      text += `• ${q}\n`;
    });

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-3 sm:p-4 animate-in fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="px-5 sm:px-6 py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-base sm:text-lg text-white">Interview Prep Cheat Sheet</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  AI Tailored
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                <Building2 className="w-3.5 h-3.5 text-slate-500" />
                <span className="font-medium text-slate-300">{job.company}</span>
                <span>•</span>
                <span className="truncate">{job.title}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyAll}
              disabled={loading || !prepData}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50"
              title="Copy entire sheet to clipboard"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy All"}</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-6 flex-1">
          {loading && !prepData ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3">
              <RefreshCw className="w-8 h-8 text-amber-400 animate-spin" />
              <p className="text-sm text-slate-300 font-medium">Analyzing job description & generating interview questions...</p>
              <p className="text-xs text-slate-500">Groq LLM is tailoring 2 YOE Java & Microservices scenarios</p>
            </div>
          ) : prepData ? (
            <>
              {/* Section 1: Top Technical Questions */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-sky-400" />
                    <span>Top Expected Technical Questions</span>
                  </h4>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {prepData.top_technical_questions?.length || 0} Key Scenarios
                  </span>
                </div>

                <div className="space-y-3">
                  {(prepData.top_technical_questions || []).map((q, idx) => (
                    <div 
                      key={idx}
                      className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-2 hover:border-slate-700 transition"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2">
                          <span className="font-mono text-xs font-bold text-sky-400 bg-sky-950/50 px-1.5 py-0.5 rounded border border-sky-500/20 shrink-0">
                            Q{idx + 1}
                          </span>
                          <p className="text-xs sm:text-sm font-semibold text-slate-100 leading-snug">
                            {q.question}
                          </p>
                        </div>
                        {q.category && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 shrink-0 whitespace-nowrap">
                            {q.category}
                          </span>
                        )}
                      </div>

                      {q.hint && (
                        <div className="ml-6 sm:ml-7 pl-3 border-l-2 border-emerald-500/40 py-1 bg-emerald-950/20 rounded-r-lg">
                          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            <span>Core Concept to Highlight:</span>
                          </div>
                          <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
                            {q.hint}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 2: Architecture Talking Points */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 sm:p-5 space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  <span>Architecture &amp; Scalability Talking Points</span>
                </h4>
                <p className="text-xs text-slate-400">
                  Mention these architectural patterns to demonstrate senior engineering maturity beyond 2 YOE:
                </p>
                <ul className="space-y-2 text-xs text-slate-300">
                  {(prepData.architecture_talking_points || []).map((pt, idx) => (
                    <li key={idx} className="flex items-start gap-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                      <Award className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Section 3: Smart Questions for Interviewer */}
              <div className="bg-gradient-to-br from-indigo-950/30 via-slate-950 to-slate-950 border border-indigo-500/20 rounded-xl p-4 sm:p-5 space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-indigo-400" />
                  <span>Smart Questions to Ask the Interviewer</span>
                </h4>
                <p className="text-xs text-slate-400">
                  Ask these at the end of your round to leave a lasting impression of curiosity and ownership:
                </p>
                <div className="space-y-2">
                  {(prepData.smart_questions_to_ask_interviewer || []).map((q, idx) => (
                    <div key={idx} className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 italic leading-relaxed">
                      "{q}"
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs">
              Unable to generate prep sheet. Please try again.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-950 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition"
          >
            Close Sheet
          </button>
        </div>

      </div>
    </div>
  );
}
