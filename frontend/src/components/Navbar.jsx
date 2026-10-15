import React, { useState } from 'react';
import { 
  Briefcase, 
  Search, 
  FileText, 
  Settings as SettingsIcon, 
  Bell, 
  Activity, 
  CheckCircle2,
  RefreshCw,
  Terminal,
  Bot,
  Sparkles,
  Menu,
  X,
  ChevronRight
} from 'lucide-react';

export default function Navbar({ 
  onOpenResume, 
  onOpenSettings, 
  onOpenLogs,
  onOpenAutoApply,
  onTriggerSearch, 
  isSearching,
  unreadCount,
  onToggleNotifications,
  activeResume
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleMobileAction = (actionFn) => {
    setMobileMenuOpen(false);
    actionFn();
  };

  return (
    <header className="sticky top-0 z-30 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 px-3 sm:px-6 py-2.5 sm:py-3 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* App Title & 24/7 Live Status */}
        <div className="flex items-center space-x-2.5 sm:space-x-4 min-w-0">
          <div className="flex items-center space-x-2 sm:space-x-2.5 min-w-0">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 shrink-0">
              <Briefcase className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="font-bold text-base sm:text-lg tracking-tight text-white flex items-center gap-1.5 sm:gap-2 truncate">
                <span className="truncate">JobApplyApp</span>
                <span className="text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20 shrink-0">
                  AI Hunter
                </span>
              </h1>
              <p className="text-[10px] sm:text-xs text-slate-400 truncate hidden xs:block">
                Jira Kanban & 24/7 Automated Application Tracker
              </p>
            </div>
          </div>

          {/* 24/7 Daemon Indicator (Visible on lg+ screens) */}
          <button 
            onClick={onOpenLogs}
            className="hidden xl:flex items-center space-x-2 px-3 py-1 bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-500/30 rounded-full text-emerald-400 text-xs transition cursor-pointer"
            title="Click to view 24/7 Live Hunter Terminal"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-medium">24/7 Auto-Hunter Active</span>
          </button>
        </div>

        {/* Action Controls (Desktop lg+) */}
        <div className="hidden lg:flex items-center space-x-2.5">
          
          {/* 1-Click Form Autofill Extension Button */}
          <button
            onClick={onOpenAutoApply}
            className="flex items-center space-x-1.5 px-3 py-2 bg-gradient-to-r from-emerald-600 via-teal-600 to-sky-600 hover:from-emerald-500 hover:to-sky-500 text-white rounded-lg text-xs font-bold transition shadow-lg shadow-emerald-950/40 active:scale-95"
            title="1-Click Form Autofill for Virtusa, Workday, Naukri, LinkedIn, Greenhouse"
          >
            <Sparkles className="w-4 h-4 text-amber-300 animate-pulse" />
            <span>⚡ 1-Click Autofill</span>
          </button>

          {/* Scan Now Button */}
          <button
            onClick={onTriggerSearch}
            disabled={isSearching}
            className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all shadow-md ${
              isSearching
                ? "bg-slate-800 text-slate-400 cursor-not-allowed"
                : "bg-sky-600 hover:bg-sky-500 text-white shadow-sky-600/20 active:scale-95"
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSearching ? "animate-spin text-sky-400" : ""}`} />
            <span>{isSearching ? "Hunting..." : "Hunt Jobs Now"}</span>
          </button>

          {/* Live Terminal Button */}
          <button
            onClick={onOpenLogs}
            className="flex items-center space-x-1.5 px-2.5 py-2 bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-emerald-300 rounded-lg text-xs font-medium transition"
            title="Live Hunter Logs & Scheduler Status"
          >
            <Terminal className="w-3.5 h-3.5 text-emerald-400" />
            <span>Hunter Logs</span>
          </button>

          {/* Resume Upload / Active Status */}
          <button
            onClick={onOpenResume}
            className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-200 rounded-lg text-xs font-medium transition"
          >
            <FileText className="w-3.5 h-3.5 text-sky-400" />
            <span>
              {activeResume ? (
                <span className="flex items-center gap-1">
                  Resume ({activeResume.experience_years || 2}y)
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                </span>
              ) : (
                "Resume"
              )}
            </span>
          </button>

          {/* Settings Button */}
          <button
            onClick={onOpenSettings}
            className="p-2 bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-300 rounded-lg text-xs transition"
            title="Search & 24/7 Interval Settings"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>

          {/* Notifications Bell */}
          <button
            onClick={onToggleNotifications}
            className="relative p-2 bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-300 rounded-lg text-xs transition"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

        </div>

        {/* Mobile / Tablet Quick Bar (< lg) */}
        <div className="flex lg:hidden items-center space-x-2">
          
          {/* Mobile Autofill Quick Pill */}
          <button
            onClick={onOpenAutoApply}
            className="flex items-center space-x-1 px-2.5 py-1.5 bg-gradient-to-r from-emerald-600 to-sky-600 text-white rounded-lg text-xs font-bold shadow-md shadow-emerald-950/40 active:scale-95"
            title="1-Click Form Autofill"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
            <span className="text-[11px]">Autofill</span>
          </button>

          {/* Quick Hunt Trigger on Mobile */}
          <button
            onClick={onTriggerSearch}
            disabled={isSearching}
            className={`p-2 rounded-lg text-xs transition shadow-sm ${
              isSearching
                ? "bg-slate-800 text-slate-400"
                : "bg-sky-600 hover:bg-sky-500 text-white active:scale-95"
            }`}
            title="Hunt Jobs Now"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSearching ? "animate-spin text-sky-200" : ""}`} />
          </button>

          {/* Notifications Bell */}
          <button
            onClick={onToggleNotifications}
            className="relative p-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs transition"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {/* Mobile Menu Hamburger Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-4 h-4 text-sky-400" /> : <Menu className="w-4 h-4" />}
          </button>

        </div>

      </div>

      {/* Mobile Drawer / Expandable Menu Overlay */}
      {mobileMenuOpen && (
        <div className="lg:hidden mt-3 pt-3 border-t border-slate-800 space-y-2 animate-in slide-in-from-top-3 duration-150">
          
          {/* Active Status Badge in Menu */}
          <div 
            onClick={() => handleMobileAction(onOpenLogs)}
            className="flex items-center justify-between p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs cursor-pointer"
          >
            <div className="flex items-center space-x-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-semibold">24/7 Hunter Daemon Active</span>
            </div>
            <span className="text-[10px] text-emerald-400/80 font-mono">View Logs →</span>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1">
            
            {/* 1-Click Autofill */}
            <button
              onClick={() => handleMobileAction(onOpenAutoApply)}
              className="flex items-center space-x-2 p-2.5 rounded-xl bg-slate-800/90 border border-slate-700 text-slate-100 text-xs font-semibold hover:border-emerald-500/50 transition text-left"
            >
              <Sparkles className="w-4 h-4 text-emerald-400 shrink-0" />
              <div className="min-w-0">
                <div className="truncate">1-Click Autofill</div>
                <div className="text-[10px] text-slate-400 font-normal truncate">Extension & Floating</div>
              </div>
            </button>

            {/* Instant Search */}
            <button
              onClick={() => handleMobileAction(onTriggerSearch)}
              disabled={isSearching}
              className="flex items-center space-x-2 p-2.5 rounded-xl bg-slate-800/90 border border-slate-700 text-slate-100 text-xs font-semibold hover:border-sky-500/50 transition text-left"
            >
              <RefreshCw className={`w-4 h-4 text-sky-400 shrink-0 ${isSearching ? "animate-spin" : ""}`} />
              <div className="min-w-0">
                <div className="truncate">{isSearching ? "Searching..." : "Hunt Jobs Now"}</div>
                <div className="text-[10px] text-slate-400 font-normal truncate">Run scraper cycle</div>
              </div>
            </button>

            {/* Hunter Logs Terminal */}
            <button
              onClick={() => handleMobileAction(onOpenLogs)}
              className="flex items-center space-x-2 p-2.5 rounded-xl bg-slate-800/90 border border-slate-700 text-slate-100 text-xs font-semibold hover:border-emerald-500/50 transition text-left"
            >
              <Terminal className="w-4 h-4 text-emerald-400 shrink-0" />
              <div className="min-w-0">
                <div className="truncate">Hunter Logs</div>
                <div className="text-[10px] text-slate-400 font-normal truncate">Live agent terminal</div>
              </div>
            </button>

            {/* Resume Upload */}
            <button
              onClick={() => handleMobileAction(onOpenResume)}
              className="flex items-center space-x-2 p-2.5 rounded-xl bg-slate-800/90 border border-slate-700 text-slate-100 text-xs font-semibold hover:border-sky-500/50 transition text-left"
            >
              <FileText className="w-4 h-4 text-sky-400 shrink-0" />
              <div className="min-w-0">
                <div className="truncate">Resume (2y Exp)</div>
                <div className="text-[10px] text-slate-400 font-normal truncate">{activeResume ? "Loaded" : "Upload"}</div>
              </div>
            </button>

            {/* Settings */}
            <button
              onClick={() => handleMobileAction(onOpenSettings)}
              className="col-span-2 flex items-center justify-between p-2.5 rounded-xl bg-slate-800/90 border border-slate-700 text-slate-100 text-xs font-semibold hover:border-sky-500/50 transition"
            >
              <div className="flex items-center space-x-2">
                <SettingsIcon className="w-4 h-4 text-indigo-400 shrink-0" />
                <span>Search Keywords, Locations & Profile Settings</span>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500" />
            </button>

          </div>
        </div>
      )}

    </header>
  );
}
