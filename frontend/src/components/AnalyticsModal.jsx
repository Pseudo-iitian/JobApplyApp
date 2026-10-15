import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  X, 
  RefreshCw, 
  Target, 
  TrendingUp, 
  Mail, 
  Briefcase, 
  Award, 
  CheckCircle2, 
  Sparkles,
  Zap
} from 'lucide-react';
import { api } from '../api';

export default function AnalyticsModal({ onClose }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await api.getJobAnalytics();
      setAnalytics(data);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const total = analytics?.total_jobs || 0;
  const statusCounts = analytics?.status_counts || {};
  const sources = analytics?.sources || [];
  const avgScore = analytics?.average_match_score || 0;
  const highMatch = analytics?.high_match_count || 0;
  const directContacts = analytics?.direct_contact_count || 0;
  const last24h = analytics?.discovered_last_24h || 0;
  const last7d = analytics?.discovered_last_7d || 0;

  const funnelStages = [
    { key: 'DISCOVERED', label: 'Discovered', color: 'bg-sky-500', textColor: 'text-sky-400' },
    { key: 'APPLIED', label: 'Applied', color: 'bg-amber-500', textColor: 'text-amber-400' },
    { key: 'SCREENING', label: 'Screening', color: 'bg-purple-500', textColor: 'text-purple-400' },
    { key: 'INTERVIEWING', label: 'Interviewing', color: 'bg-indigo-500', textColor: 'text-indigo-400' },
    { key: 'OFFER', label: 'Offer', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-3 sm:p-4 animate-in fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="px-5 sm:px-6 py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-base sm:text-lg text-white">Job Hunter Analytics</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Real-time ATS Funnel
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Pipeline health, source distribution, and AI match rate analytics
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={fetchAnalytics}
              disabled={loading}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition disabled:opacity-50"
              title="Refresh Analytics"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
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
          {loading && !analytics ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin" />
              <p className="text-sm text-slate-400">Computing pipeline analytics...</p>
            </div>
          ) : (
            <>
              {/* Stat Cards Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <span className="text-xs font-medium">Total Tracked</span>
                    <Briefcase className="w-4 h-4 text-sky-400" />
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl sm:text-3xl font-extrabold text-white">{total}</span>
                    <span className="text-xs font-semibold text-emerald-400">+{last24h} today</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">{last7d} added in last 7 days</p>
                </div>

                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <span className="text-xs font-medium">Avg Match Score</span>
                    <Target className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400">{avgScore}%</span>
                    <span className="text-xs text-slate-400">ATS rating</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Weighted candidate alignment</p>
                </div>

                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <span className="text-xs font-medium">High Matches (&gt;=80%)</span>
                    <Award className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl sm:text-3xl font-extrabold text-white">{highMatch}</span>
                    <span className="text-xs text-indigo-400">
                      {total > 0 ? Math.round((highMatch / total) * 100) : 0}% of total
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Priority application targets</p>
                </div>

                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 mb-2">
                    <span className="text-xs font-medium">Direct HR Contacts</span>
                    <Mail className="w-4 h-4 text-pink-400" />
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl sm:text-3xl font-extrabold text-white">{directContacts}</span>
                    <span className="text-xs text-pink-400">Emails &amp; Forms</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Skip ATS queues directly</p>
                </div>
              </div>

              {/* Recruitment Funnel Progress */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-sky-400" />
                    <h4 className="text-sm font-semibold text-white">Application Pipeline Funnel</h4>
                  </div>
                  <span className="text-xs text-slate-400">Total in Kanban: {total}</span>
                </div>

                <div className="space-y-3">
                  {funnelStages.map((stage) => {
                    const count = statusCounts[stage.key] || 0;
                    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                    return (
                      <div key={stage.key} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className={`font-medium ${stage.textColor}`}>{stage.label}</span>
                          <span className="text-slate-300 font-semibold">{count} ({pct}%)</span>
                        </div>
                        <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${stage.color} rounded-full transition-all duration-500`}
                            style={{ width: `${Math.max(pct, count > 0 ? 3 : 0)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Source Distribution & Best Practices */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Sources breakdown */}
                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-5">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-amber-400" />
                    <span>Discovered Sources</span>
                  </h4>
                  {sources.length === 0 ? (
                    <p className="text-xs text-slate-500 py-6 text-center">No jobs found yet</p>
                  ) : (
                    <div className="space-y-2.5">
                      {sources.map((item, idx) => {
                        const count = item.count;
                        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                        return (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <span className="text-slate-300 truncate max-w-[200px]" title={item.source}>
                              {item.source}
                            </span>
                            <div className="flex items-center space-x-2">
                              <span className="text-slate-500 text-[11px]">{pct}%</span>
                              <span className="px-2 py-0.5 bg-slate-800 text-slate-200 rounded font-mono text-[11px]">
                                {count}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Pro Tips / Insights */}
                <div className="bg-gradient-to-br from-indigo-950/40 via-slate-950 to-slate-950 border border-indigo-500/20 rounded-xl p-5 flex flex-col justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-2 flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                      <span>Smart Application Strategy</span>
                    </h4>
                    <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                      Maximizing callback rates with JobApplyApp AI:
                    </p>
                    <ul className="space-y-2 text-xs text-slate-300">
                      <li className="flex items-start space-x-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span><strong>1-Click AI Tailor:</strong> Generates job-specific bullet points and ATS keywords matching the exact role requirements.</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span><strong>Direct Outreach:</strong> Use the generated HR email draft for posts with direct recruiter emails.</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span><strong>Chrome Extension / Bookmarklet:</strong> Autofill long application forms in under 3 seconds.</span>
                      </li>
                    </ul>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500">
                    Background hunter scans continuously every 5 minutes.
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-950 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
