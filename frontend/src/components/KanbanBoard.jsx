import React, { useState } from 'react';
import JobCard from './JobCard';
import { 
  Search, 
  Mail, 
  FileSpreadsheet, 
  Inbox, 
  CheckCircle, 
  Clock, 
  Trophy, 
  XCircle, 
  ExternalLink, 
  Layers, 
  Bot, 
  RefreshCw, 
  Sparkles,
  SlidersHorizontal,
  X,
  Smartphone,
  Columns3
} from 'lucide-react';

const COLUMNS = [
  { id: 'DISCOVERED', title: 'Discovered / New', shortTitle: 'Discovered', icon: Inbox, color: 'border-sky-500/50 bg-sky-500/10 text-sky-400' },
  { id: 'APPLIED', title: 'Applied', shortTitle: 'Applied', icon: Clock, color: 'border-amber-500/50 bg-amber-500/10 text-amber-400' },
  { id: 'SCREENING', title: 'HR Screening', shortTitle: 'HR Screen', icon: Mail, color: 'border-purple-500/50 bg-purple-500/10 text-purple-400' },
  { id: 'INTERVIEWING', title: 'Tech Interview', shortTitle: 'Interview', icon: CheckCircle, color: 'border-blue-500/50 bg-blue-500/10 text-blue-400' },
  { id: 'OFFER', title: 'Offer Received', shortTitle: 'Offer', icon: Trophy, color: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' },
  { id: 'REJECTED', title: 'Archived / Rejected', shortTitle: 'Archived', icon: XCircle, color: 'border-slate-500/50 bg-slate-500/10 text-slate-400' }
];

export default function KanbanBoard({ 
  jobs, 
  onStatusChange, 
  onDeleteJob, 
  onOpenTailor,
  onOpenInterviewPrep,
  onOpenAutoApply,
  onRefreshJobs,
  isLoading
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterEmailOnly, setFilterEmailOnly] = useState(false);
  const [filterFormOnly, setFilterFormOnly] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState('ALL');
  const [sortBy, setSortBy] = useState('latest');
  const [dragOverCol, setDragOverCol] = useState(null);

  // Mobile navigation state
  const [activeMobileStage, setActiveMobileStage] = useState('DISCOVERED');
  const [mobileViewMode, setMobileViewMode] = useState('single'); // 'single' (focused active tab) or 'swipe' (horizontal carousel)
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  // Helper to distinguish genuine LinkedIn Recruiter Posts vs standard Job View listings
  const isPostJob = (j) => {
    const src = (j.source || '').toLowerCase();
    const link = (j.apply_link || '').toLowerCase();
    const postUrl = (j.post_url || '').toLowerCase();
    return src.includes('#hiring') || 
           link.includes('/posts/') || 
           link.includes('activity-') || 
           link.includes('/feed/update/') || 
           postUrl.includes('/posts/') || 
           postUrl.includes('activity-');
  };

  // Dynamic platform counts
  const platformCounts = {
    ALL: jobs.length,
    POSTS: jobs.filter(isPostJob).length,
    LINKEDIN: jobs.filter(j => !isPostJob(j) && ((j.source || '').toLowerCase().includes('linkedin') || (j.apply_link || '').includes('linkedin.com'))).length,
    INSTAHYRE: jobs.filter(j => (j.source || '').toLowerCase().includes('instahyre') || (j.apply_link || '').includes('instahyre.com')).length,
    NAUKRI: jobs.filter(j => (j.source || '').toLowerCase().includes('naukri') || (j.apply_link || '').includes('naukri.com')).length,
    INDEED: jobs.filter(j => (j.source || '').toLowerCase().includes('indeed') || (j.apply_link || '').includes('indeed.com')).length,
    GLASSDOOR: jobs.filter(j => (j.source || '').toLowerCase().includes('glassdoor') || (j.source || '').toLowerCase().includes('portal') || (j.apply_link || '').includes('arbeitnow')).length,
  };

  // Filter and sort jobs (Latest posted always on top by default)
  const sortedAndFilteredJobs = [...jobs]
    .filter((job) => {
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = !q || 
        (job.title && job.title.toLowerCase().includes(q)) ||
        (job.company && job.company.toLowerCase().includes(q)) ||
        (job.location && job.location.toLowerCase().includes(q)) ||
        (job.description && job.description.toLowerCase().includes(q));

      if (!matchesSearch) return false;
      if (filterEmailOnly && !job.hr_email) return false;
      if (filterFormOnly && !job.google_form_url) return false;

      // Multi-Platform Filtering
      if (selectedPlatform !== 'ALL') {
        const src = (job.source || '').toLowerCase();
        const link = (job.apply_link || '').toLowerCase();
        const isPost = isPostJob(job);

        if (selectedPlatform === 'POSTS') {
          if (!isPost) return false;
        } else if (selectedPlatform === 'LINKEDIN') {
          if (isPost || (!src.includes('linkedin') && !link.includes('linkedin.com'))) return false;
        } else if (selectedPlatform === 'INSTAHYRE') {
          if (!src.includes('instahyre') && !link.includes('instahyre.com')) return false;
        } else if (selectedPlatform === 'NAUKRI') {
          if (!src.includes('naukri') && !link.includes('naukri.com')) return false;
        } else if (selectedPlatform === 'INDEED') {
          if (!src.includes('indeed') && !link.includes('indeed.com')) return false;
        } else if (selectedPlatform === 'GLASSDOOR') {
          if (!src.includes('glassdoor') && !src.includes('portal') && !link.includes('arbeitnow')) return false;
        }
      }

      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'latest') {
        const dateA = new Date(a.posted_at || a.created_at || 0).getTime();
        const dateB = new Date(b.posted_at || b.created_at || 0).getTime();
        if (dateB !== dateA) return dateB - dateA;
        return b.id - a.id;
      }
      if (sortBy === 'match') {
        return (b.match_score || 0) - (a.match_score || 0);
      }
      if (sortBy === 'company') {
        return (a.company || '').localeCompare(b.company || '');
      }
      return 0;
    });

  const activeFilterCount = (filterEmailOnly ? 1 : 0) + (filterFormOnly ? 1 : 0) + (selectedPlatform !== 'ALL' ? 1 : 0);

  // Render a specific column
  const renderColumn = (col, customWidthClass = "") => {
    const colJobs = sortedAndFilteredJobs.filter((j) => j.status === col.id);
    const Icon = col.icon;
    const isOver = dragOverCol === col.id;

    return (
      <div
        key={col.id}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
          setDragOverCol(col.id);
        }}
        onDragLeave={() => {
          if (dragOverCol === col.id) setDragOverCol(null);
        }}
        onDrop={(e) => {
          e.preventDefault();
          const jobId = Number(e.dataTransfer.getData('text/plain'));
          if (jobId) {
            onStatusChange(jobId, col.id);
          }
          setDragOverCol(null);
        }}
        className={`bg-slate-900/90 border ${
          isOver 
            ? "border-sky-400 bg-sky-950/30 ring-2 ring-sky-500/30 scale-[1.01]" 
            : "border-slate-800"
        } rounded-2xl flex flex-col shadow-xl transition-all overflow-hidden ${customWidthClass}`}
      >
        {/* Column Header */}
        <div className="p-3 sm:p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/70 sticky top-0 z-10 backdrop-blur-sm">
          <div className="flex items-center space-x-2 min-w-0">
            <span className={`p-1.5 rounded-lg border ${col.color} shrink-0`}>
              <Icon className="w-3.5 h-3.5" />
            </span>
            <span className="font-bold text-xs text-slate-100 truncate">{col.title}</span>
          </div>
          <span className="text-xs font-black px-2 py-0.5 rounded-full bg-slate-800 text-slate-200 border border-slate-700 shrink-0 ml-2">
            {colJobs.length}
          </span>
        </div>

        {/* Column Tickets Container */}
        <div className="p-2.5 sm:p-3 space-y-3 overflow-y-auto flex-1 flex flex-col min-h-[160px] touch-scroll">
          {colJobs.length === 0 ? (
            <div className={`py-12 sm:py-16 text-center text-xs rounded-xl border border-dashed transition-all flex flex-col items-center justify-center my-2 ${
              isOver ? "border-sky-400 text-sky-300 bg-sky-500/10" : "border-slate-800/80 text-slate-600"
            }`}>
              <Layers className="w-5 h-5 mb-1.5 opacity-40" />
              <span>{isOver ? "Drop ticket here" : "No tickets in this stage"}</span>
            </div>
          ) : (
            colJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onStatusChange={onStatusChange}
                onDelete={onDeleteJob}
                onOpenTailor={onOpenTailor}
                onOpenInterviewPrep={onOpenInterviewPrep}
              />
            ))
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col p-3 sm:p-5 lg:p-6 max-w-[1920px] mx-auto w-full transition-all">
      
      {/* Search & Filter Toolbar */}
      <div className="mb-4 sm:mb-6 bg-slate-900/85 p-3 sm:p-4 rounded-2xl border border-slate-800 shadow-lg space-y-3">
        
        {/* Top Toolbar Row: Search Bar + Sort + Mobile Filters Toggle + Refresh */}
        <div className="flex items-center justify-between gap-2.5 flex-wrap">
          
          {/* Search Input */}
          <div className="relative flex-1 min-w-[200px] sm:min-w-[260px] max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
            <input
              type="text"
              placeholder="Search role, company (Java, Capco, Rapipay)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl pl-9 pr-8 py-2 text-xs text-slate-200 placeholder-slate-500 transition"
            />
            {searchQuery && (
              <button 
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-white"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Right Toolbar Actions */}
          <div className="flex items-center gap-2 shrink-0">
            
            {/* Sort Selector Dropdown */}
            <div className="flex items-center space-x-1 bg-slate-950/90 px-2.5 py-1.5 rounded-xl border border-slate-700/80 text-xs shadow-inner">
              <Clock className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-transparent text-sky-300 font-semibold focus:outline-none cursor-pointer text-xs"
              >
                <option value="latest" className="bg-slate-900 text-slate-100">🕒 Latest</option>
                <option value="match" className="bg-slate-900 text-slate-100">🎯 Fit Score</option>
                <option value="company" className="bg-slate-900 text-slate-100">🏢 Company</option>
              </select>
            </div>

            {/* Mobile Filter Sheet Toggle Button */}
            <button
              onClick={() => setShowMobileFilters(!showMobileFilters)}
              className={`xl:hidden flex items-center space-x-1 px-2.5 py-1.5 rounded-xl border text-xs font-semibold transition ${
                showMobileFilters || activeFilterCount > 0
                  ? "bg-sky-600/20 text-sky-300 border-sky-500/50"
                  : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
              }`}
              title="Toggle Filters"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Filters</span>
              {activeFilterCount > 0 && (
                <span className="w-4 h-4 rounded-full bg-sky-500 text-[10px] font-bold text-white flex items-center justify-center">
                  {activeFilterCount}
                </span>
              )}
            </button>

            {/* Total Jobs Badge */}
            <span className="px-2.5 py-1.5 rounded-xl bg-slate-950 text-slate-300 font-semibold border border-slate-800 text-xs shrink-0">
              {sortedAndFilteredJobs.length} <span className="text-slate-500 hidden sm:inline">of {jobs.length}</span>
            </span>

            {/* Refresh Button */}
            {onRefreshJobs && (
              <button
                onClick={onRefreshJobs}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-sky-300 border border-slate-700 transition active:scale-95 shrink-0"
                title="Reload Jobs from Database"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            )}

          </div>

        </div>

        {/* Platform Horizontal Scrollable Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar touch-scroll py-0.5">
          <button
            onClick={() => setSelectedPlatform('ALL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition ${
              selectedPlatform === 'ALL'
                ? 'bg-sky-500 text-white shadow-sm'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({platformCounts.ALL})
          </button>
          <button
            onClick={() => setSelectedPlatform('LINKEDIN')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition ${
              selectedPlatform === 'LINKEDIN'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            🔵 LinkedIn ({platformCounts.LINKEDIN})
          </button>
          <button
            onClick={() => setSelectedPlatform('POSTS')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition ${
              selectedPlatform === 'POSTS'
                ? 'bg-rose-600 text-white shadow-sm ring-1 ring-rose-400'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            🔥 LinkedIn Posts ({platformCounts.POSTS})
          </button>
          <button
            onClick={() => setSelectedPlatform('INSTAHYRE')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition ${
              selectedPlatform === 'INSTAHYRE'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            🟢 Instahyre ({platformCounts.INSTAHYRE})
          </button>
          <button
            onClick={() => setSelectedPlatform('NAUKRI')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition ${
              selectedPlatform === 'NAUKRI'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            🔷 Naukri ({platformCounts.NAUKRI})
          </button>
          <button
            onClick={() => setSelectedPlatform('INDEED')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition ${
              selectedPlatform === 'INDEED'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            🟣 Indeed ({platformCounts.INDEED})
          </button>
          <button
            onClick={() => setSelectedPlatform('GLASSDOOR')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition ${
              selectedPlatform === 'GLASSDOOR'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            🔶 Glassdoor & Dev ({platformCounts.GLASSDOOR})
          </button>
        </div>

        {/* Secondary Filter Chips Row (Visible on Desktop OR when toggled on Mobile) */}
        <div className={`flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/60 ${showMobileFilters ? "block" : "hidden xl:flex"}`}>
          
          <button
            onClick={() => setFilterEmailOnly(!filterEmailOnly)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
              filterEmailOnly
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/50"
                : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
            }`}
          >
            <Mail className="w-3.5 h-3.5 text-emerald-400" />
            <span>Has HR Email</span>
          </button>

          <button
            onClick={() => setFilterFormOnly(!filterFormOnly)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
              filterFormOnly
                ? "bg-purple-500/20 text-purple-300 border-purple-500/50"
                : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
            }`}
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-purple-400" />
            <span>Has Google Form</span>
          </button>

          {/* 1-Click Form Autofill Pill */}
          {onOpenAutoApply && (
            <button
              onClick={onOpenAutoApply}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 via-teal-600 to-sky-600 hover:from-emerald-500 hover:to-sky-500 text-white shadow-md shadow-emerald-950/50 transition active:scale-95 shrink-0"
              title="1-Click Chrome Autofill Extension & Floating Icon"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
              <span>⚡ 1-Click Autofill Hub</span>
            </button>
          )}

          <span className="hidden 2xl:inline text-[11px] text-slate-500 ml-auto">
            💡 Drag & Drop tickets across columns or use the 1-click stage dropdown on each card
          </span>

        </div>

      </div>

      {/* Mobile Stage Selector Tabs (< xl Viewport) */}
      <div className="xl:hidden mb-4 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <div className="font-semibold text-slate-300 flex items-center gap-1.5">
            <span>Stages</span>
            <span className="text-[10px] text-slate-500 font-mono">(Tap to switch)</span>
          </div>

          {/* Mode Switcher: Single Stage vs Horizontal Swipe */}
          <div className="flex items-center space-x-1 bg-slate-900 border border-slate-800 p-1 rounded-xl text-[11px]">
            <button
              onClick={() => setMobileViewMode('single')}
              className={`flex items-center gap-1 px-2 py-1 rounded-lg font-medium transition ${
                mobileViewMode === 'single'
                  ? 'bg-sky-500 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Show active stage in full width"
            >
              <Smartphone className="w-3 h-3" />
              <span>Single</span>
            </button>
            <button
              onClick={() => setMobileViewMode('swipe')}
              className={`flex items-center gap-1 px-2 py-1 rounded-lg font-medium transition ${
                mobileViewMode === 'swipe'
                  ? 'bg-sky-500 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Swipe horizontally across all 6 columns"
            >
              <Columns3 className="w-3 h-3" />
              <span>Swipe</span>
            </button>
          </div>
        </div>

        {/* Scrollable Stage Pills */}
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar touch-scroll pb-1">
          {COLUMNS.map((col) => {
            const count = sortedAndFilteredJobs.filter(j => j.status === col.id).length;
            const isActive = activeMobileStage === col.id;
            const Icon = col.icon;

            return (
              <button
                key={col.id}
                onClick={() => setActiveMobileStage(col.id)}
                className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold shrink-0 transition border ${
                  isActive
                    ? `${col.color} bg-slate-900 shadow-md ring-1 ring-sky-400/40`
                    : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{col.shortTitle}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ml-1 ${
                  isActive ? 'bg-sky-500 text-white' : 'bg-slate-800 text-slate-300'
                }`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Loading / Empty States */}
      {isLoading ? (
        <div className="mb-6 p-8 rounded-2xl bg-slate-900/90 border border-slate-800 text-center space-y-3 animate-fadeIn">
          <div className="flex justify-center">
            <div className="w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full animate-spin" />
          </div>
          <div className="text-sm font-semibold text-slate-300">Loading jobs from server...</div>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Fetching your tracked Java Developer openings from database.
          </p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="mb-6 p-8 rounded-2xl bg-slate-900/90 border border-slate-800 text-center space-y-3 animate-fadeIn">
          <div className="text-3xl">🔎</div>
          <div className="text-base font-bold text-slate-200">No jobs found yet — Hunter is searching!</div>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            The 24/7 Auto-Hunter is scanning LinkedIn, Naukri, Indeed, Instahyre & Glassdoor. New jobs appear automatically.
          </p>
          {onRefreshJobs && (
            <button
              onClick={onRefreshJobs}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-sky-600/30"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reload Jobs Now</span>
            </button>
          )}
        </div>
      ) : null}

      {/* ========================================================================= */}
      {/* KANBAN BOARD DISPLAY */}
      {/* ========================================================================= */}

      {/* 1. Desktop & Ultrawide Layout (>= xl): Smooth Horizontal Flexboard */}
      <div className="hidden xl:flex flex-nowrap overflow-x-auto gap-4 pb-6 items-start touch-scroll w-full">
        {COLUMNS.map((col) => renderColumn(col, "w-[320px] 2xl:w-[350px] shrink-0 max-h-[calc(100vh-210px)]"))}
      </div>

      {/* 2. Mobile / Tablet Layout (< xl): Single Stage Mode OR Swipe Carousel */}
      <div className="xl:hidden w-full">
        {mobileViewMode === 'single' ? (
          /* Single Stage View (Full Width, Clear, Uncluttered) */
          <div className="w-full">
            {COLUMNS.filter(c => c.id === activeMobileStage).map(col => 
              renderColumn(col, "w-full min-h-[500px] max-h-[calc(100vh-270px)]")
            )}
          </div>
        ) : (
          /* Horizontal Swipe Carousel Mode */
          <div className="flex flex-nowrap overflow-x-auto snap-x snap-mandatory gap-3 pb-6 touch-scroll w-full">
            {COLUMNS.map((col) => renderColumn(col, "w-[88vw] sm:w-[340px] snap-center shrink-0 max-h-[calc(100vh-260px)]"))}
          </div>
        )}
      </div>

    </div>
  );
}
