import React, { useState, useEffect } from 'react';
import { Terminal, RefreshCw, X, Play, Clock, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { api } from '../api';

export default function HunterLogsModal({ onClose, onTriggerSearch, isSearching }) {
  const [data, setData] = useState({ scheduler: {}, logs: [] });
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const res = await api.getHunterStatus();
      setData(res);
    } catch (err) {
      console.error("Failed to fetch hunter status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const scheduler = data.scheduler || {};
  const logs = data.logs || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-3 sm:p-4 animate-in fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-4 sm:px-6 py-3 sm:py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between gap-2">
          <div className="flex items-center space-x-2.5 sm:space-x-3 min-w-0">
            <div className="p-2 bg-emerald-950/80 border border-emerald-500/30 rounded-xl text-emerald-400 shrink-0">
              <Terminal className="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 sm:gap-2">
                <h3 className="font-bold text-sm sm:text-base text-white truncate">Hunter Terminal</h3>
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-500/30 shrink-0">
                  <span className="relative flex h-1.5 w-1.5 sm:h-2 sm:w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 sm:h-2 sm:w-2 bg-emerald-500"></span>
                  </span>
                  24/7
                </span>
              </div>
              <p className="text-[11px] sm:text-xs text-slate-400 truncate hidden sm:block">
                Live inspection: LinkedIn Jobs Sections & Live Recruiter Hiring Posts (#hiring)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-1.5 sm:space-x-2 shrink-0">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-2 sm:px-2.5 py-1.5 rounded-lg text-[11px] sm:text-xs font-medium border transition ${
                autoRefresh
                  ? "bg-emerald-950/60 border-emerald-500/30 text-emerald-300"
                  : "bg-slate-800 border-slate-700 text-slate-400"
              }`}
            >
              {autoRefresh ? "Auto ON" : "Paused"}
            </button>
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="p-1.5 sm:p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
              title="Refresh logs"
            >
              <RefreshCw className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${loading ? "animate-spin text-sky-400" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 sm:p-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Status Metrics Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 p-3 sm:p-4 bg-slate-900/90 border-b border-slate-800 text-xs">
          <div className="bg-slate-800/60 p-2 sm:p-2.5 rounded-xl border border-slate-700/60">
            <span className="text-slate-400 block text-[10px] sm:text-[11px]">Interval Cycle</span>
            <span className="font-semibold text-slate-100 flex items-center gap-1 mt-0.5 text-xs">
              <Clock className="w-3.5 h-3.5 text-sky-400" />
              Every {scheduler.interval_minutes || 5} Minutes
            </span>
          </div>

          <div className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/60">
            <span className="text-slate-400 block text-[11px]">Total Hunt Cycles</span>
            <span className="font-semibold text-sky-300 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />
              {scheduler.total_runs || 0} Runs
            </span>
          </div>

          <div className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/60">
            <span className="text-slate-400 block text-[11px]">Last Execution</span>
            <span className="font-semibold text-slate-200 truncate mt-0.5 block">
              {scheduler.last_run_at || "Just now"}
            </span>
          </div>

          <div className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/60 flex items-center justify-between">
            <div>
              <span className="text-slate-400 block text-[11px]">Trigger Immediately</span>
              <span className="font-semibold text-emerald-300 text-[11px]">No Waiting</span>
            </div>
            <button
              onClick={onTriggerSearch}
              disabled={isSearching}
              className="px-2.5 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-white font-medium rounded-lg shadow transition flex items-center gap-1 text-[11px]"
            >
              <Play className={`w-3 h-3 ${isSearching ? "animate-spin" : ""}`} />
              {isSearching ? "Hunting..." : "Run Now"}
            </button>
          </div>
        </div>

        {/* Live Terminal Console */}
        <div className="flex-1 p-4 bg-slate-950 font-mono text-xs overflow-y-auto space-y-1.5 scrollbar-thin select-text">
          {logs.length === 0 ? (
            <div className="text-slate-500 py-8 text-center italic font-sans">
              No recent scraper logs yet. Click "Run Now" to trigger an instant hunt cycle!
            </div>
          ) : (
            logs.map((item, idx) => {
              const isError = item.level === "ERROR";
              const isWarning = item.level === "WARNING";
              return (
                <div 
                  key={idx} 
                  className={`flex items-start space-x-2 py-0.5 leading-relaxed ${
                    isError 
                      ? "text-rose-400" 
                      : isWarning 
                      ? "text-amber-300" 
                      : item.message.includes("✨") || item.message.includes("🎯")
                      ? "text-emerald-300 font-semibold"
                      : item.message.includes("🚫")
                      ? "text-slate-400 italic"
                      : "text-slate-300"
                  }`}
                >
                  <span className="text-slate-600 select-none shrink-0">[{item.time}]</span>
                  <span className="break-all">{item.message}</span>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 sm:px-6 py-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 gap-2">
          <div className="flex items-center space-x-2 min-w-0">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="truncate text-[11px]">Strict 1-2 YOE Filter Active: Java Developer & Spring Boot SDE-1</span>
          </div>
          <button
            onClick={onClose}
            className="px-3 sm:px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition shrink-0"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
