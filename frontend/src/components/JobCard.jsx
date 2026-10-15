import React, { useState } from 'react';
import { 
  Building2, 
  MapPin, 
  Mail, 
  ExternalLink, 
  Sparkles, 
  Copy, 
  Check, 
  Trash2, 
  Layers,
  FileSpreadsheet,
  GripVertical,
  Clock,
  Users,
  BrainCircuit,
  Zap,
  Share2
} from 'lucide-react';

const ALL_STAGES = [
  { id: "DISCOVERED", label: "📥 Discovered" },
  { id: "APPLIED", label: "📝 Applied" },
  { id: "SCREENING", label: "📞 HR Screening" },
  { id: "INTERVIEWING", label: "💻 Tech Interview" },
  { id: "OFFER", label: "🎉 Offer" },
  { id: "REJECTED", label: "❌ Rejected / Archive" }
];

export default function JobCard({ 
  job, 
  onStatusChange, 
  onDelete, 
  onOpenTailor,
  onOpenInterviewPrep
}) {
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [copiedReferral, setCopiedReferral] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const copyEmail = (e) => {
    e.stopPropagation();
    if (job.hr_email) {
      navigator.clipboard.writeText(job.hr_email);
      setCopiedEmail(true);
      setTimeout(() => setCopiedEmail(false), 2000);
    }
  };

  const handleDragStart = (e) => {
    e.dataTransfer.setData('text/plain', String(job.id));
    e.dataTransfer.effectAllowed = 'move';
    setIsDragging(true);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  const isRealPost = (job.source && job.source.includes('#hiring')) || 
    (job.apply_link && (job.apply_link.includes('/posts/') || job.apply_link.includes('activity-') || job.apply_link.includes('/feed/update/'))) ||
    Boolean(job.post_url);
  const isLinkedIn = !isRealPost && ((job.source && job.source.includes('LinkedIn')) || (job.apply_link && job.apply_link.includes('linkedin.com')));
  const isInstahyre = (job.source && job.source.includes('Instahyre')) || (job.apply_link && job.apply_link.includes('instahyre.com'));
  const isNaukri = (job.source && job.source.includes('Naukri')) || (job.apply_link && job.apply_link.includes('naukri.com'));
  const isIndeed = (job.source && job.source.includes('Indeed')) || (job.apply_link && job.apply_link.includes('indeed.com'));

  // Tech stack micro-tags extraction
  const extractTechTags = () => {
    const text = `${job.title || ''} ${job.description || ''}`.toLowerCase();
    const tags = [];
    if (text.includes("java 17") || text.includes("java 21") || text.includes("core java") || text.includes("java")) tags.push("Java");
    if (text.includes("spring boot") || text.includes("springboot") || text.includes("spring")) tags.push("Spring Boot");
    if (text.includes("microservice") || text.includes("micro-service")) tags.push("Microservices");
    if (text.includes("kafka")) tags.push("Kafka");
    if (text.includes("docker") || text.includes("kubernetes") || text.includes("k8s")) tags.push("Docker");
    if (text.includes("postgres") || text.includes("postgresql") || text.includes("sql")) tags.push("PostgreSQL");
    if (text.includes("redis")) tags.push("Redis");
    if (text.includes("aws") || text.includes("cloud")) tags.push("AWS");
    if (text.includes("rest") || text.includes("api")) tags.push("REST API");
    return tags.slice(0, 4);
  };

  const techTags = extractTechTags();

  // Freshness check: posted today or within last 24h
  const isUrgentFresh = () => {
    const s = (job.posted_date_str || '').toLowerCase();
    return s.includes("hour") || s.includes("minute") || s.includes("just") || s.includes("today") || s.includes("1d") || s.includes("1 day");
  };

  const urgent = isUrgentFresh();

  // Referral LinkedIn search URL & note copy
  const cleanCompany = (job.company || '').replace(/[^a-zA-Z0-9\s]/g, '').trim();
  const referralSearchUrl = `https://www.linkedin.com/search/results/people/?keywords=software%20engineer%20${encodeURIComponent(cleanCompany)}&origin=GLOBAL_SEARCH_HEADER`;

  const copyReferralNote = (e) => {
    e.stopPropagation();
    const note = `Hi! I noticed the ${job.title} opening at ${job.company}. Given my 2 years of hands-on experience in Java, Spring Boot, Microservices, and PostgreSQL, I would love to contribute to the engineering team. Could you please consider referring my profile? Happy to share my resume. Thanks! - Abhishek Verma`;
    navigator.clipboard.writeText(note);
    setCopiedReferral(true);
    setTimeout(() => setCopiedReferral(false), 2000);
  };

  return (
    <div 
      draggable={true}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      className={`bg-slate-800/95 hover:bg-slate-800 border ${
        isDragging ? "border-sky-400 opacity-50 scale-95" : "border-slate-700/80 hover:border-slate-600"
      } rounded-xl p-4 shadow-md hover:shadow-xl transition-all flex flex-col justify-between group cursor-grab active:cursor-grabbing select-none`}
    >
      
      {/* Top Header: Drag Handle, Title, Company, Delete */}
      <div>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start space-x-2 flex-1 min-w-0">
            {/* Grab handle indicator (desktop) */}
            <div className="mt-1 text-slate-500 group-hover:text-sky-400 transition cursor-grab hidden sm:block shrink-0">
              <GripVertical className="w-4 h-4" />
            </div>
            
            <div className="flex-1 min-w-0">
              {/* Full readable title (no truncation) */}
              <h4 className="font-semibold text-sm text-slate-100 group-hover:text-sky-300 transition leading-snug break-words">
                {job.title}
              </h4>
              <p className="text-xs text-slate-300 font-medium flex items-center gap-1.5 mt-1">
                <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="truncate">{job.company}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-1 shrink-0">
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/30 whitespace-nowrap">
              {job.match_score || 92}% Fit
            </span>
            <button
              onClick={() => onDelete(job.id)}
              className="text-slate-500 hover:text-rose-400 p-1.5 rounded hover:bg-slate-700/60 transition min-w-[28px] min-h-[28px] flex items-center justify-center"
              title="Delete ticket"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Experience, Date & Source Badges */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
          {/* Urgency Badge if posted < 24h */}
          {urgent && (
            <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-extrabold flex items-center gap-1 animate-pulse shadow-sm">
              <Zap className="w-3 h-3 text-amber-400 fill-amber-400" />
              Just Posted
            </span>
          )}

          {/* Posted Date Badge */}
          <span className="px-2 py-0.5 rounded-md bg-emerald-950/70 text-emerald-300 border border-emerald-500/30 text-[11px] font-semibold flex items-center gap-1 shadow-sm">
            <Clock className="w-3 h-3 text-emerald-400" />
            {job.posted_date_str || "Recently"}
          </span>
          <span className="px-2.5 py-1 rounded-md bg-amber-950/70 text-amber-300 border border-amber-500/30 font-semibold text-[11px] flex items-center gap-1 shadow-sm">
            🎯 {job.experience_str || "2 Years Exp"}
          </span>
          <span className="px-2 py-0.5 rounded-md bg-slate-700/50 text-slate-300 text-[11px] flex items-center gap-1">
            <MapPin className="w-3 h-3 text-slate-400" />
            {job.location || "India / Remote"}
          </span>
          {isRealPost ? (
            <span className="px-2 py-0.5 rounded-md bg-cyan-950/90 text-cyan-300 border border-cyan-500/40 text-[10px] font-bold flex items-center gap-1 shadow-sm">
              🔥 Recruiter LinkedIn Post
            </span>
          ) : isLinkedIn ? (
            <span className="px-2 py-0.5 rounded-md bg-sky-950/80 text-sky-300 border border-sky-500/30 text-[10px] font-semibold">
              LinkedIn
            </span>
          ) : isInstahyre ? (
            <span className="px-2 py-0.5 rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 text-[10px] font-semibold">
              Instahyre
            </span>
          ) : isNaukri ? (
            <span className="px-2 py-0.5 rounded-md bg-blue-950/80 text-blue-300 border border-blue-500/30 text-[10px] font-semibold">
              Naukri
            </span>
          ) : isIndeed ? (
            <span className="px-2 py-0.5 rounded-md bg-indigo-950/80 text-indigo-300 border border-indigo-500/30 text-[10px] font-semibold">
              Indeed
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-md bg-purple-950/80 text-purple-300 border border-purple-500/30 text-[10px] font-semibold">
              {job.source || "Direct Portal"}
            </span>
          )}
        </div>

        {/* Tech Stack Micro-Pills */}
        {techTags.length > 0 && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1">
            {techTags.map((tag, idx) => (
              <span 
                key={idx}
                className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-900/80 text-slate-300 border border-slate-700/60 font-mono"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Contact Links & Direct Apply Actions */}
        <div className="mt-3 space-y-2 pt-2.5 border-t border-slate-700/70">
          
          {/* 1. Direct Career / Application Portal Link */}
          {job.apply_link && (job.apply_link !== job.post_url) ? (
            <a
              href={job.apply_link}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between text-xs px-3 py-2 rounded-lg font-semibold transition shadow-sm bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30"
            >
              <span className="flex items-center space-x-1.5 truncate">
                <ExternalLink className="w-3.5 h-3.5 shrink-0 text-emerald-200" />
                <span className="truncate font-bold">
                  🔗 Apply on Career Portal
                </span>
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-white/20 ml-1">
                Apply ↗
              </span>
            </a>
          ) : null}

          {/* 2. Original LinkedIn Hiring Post Permalink (for referrals / DM) */}
          {(job.post_url || (job.apply_link && (!job.apply_link.includes('http') || job.apply_link === job.post_url))) ? (
            <a
              href={job.post_url || job.apply_link}
              target="_blank"
              rel="noreferrer"
              className={`flex items-center justify-between text-xs px-3 py-2 rounded-lg font-semibold transition shadow-sm ${
                job.apply_link && job.apply_link !== job.post_url
                  ? "bg-slate-700 hover:bg-slate-600 text-sky-300 border border-slate-600"
                  : isLinkedIn
                  ? "bg-sky-600 hover:bg-sky-500 text-white shadow-sky-900/30"
                  : isInstahyre
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30"
                  : isNaukri
                  ? "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/30"
                  : isIndeed
                  ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-900/30"
                  : "bg-purple-600 hover:bg-purple-500 text-white"
              }`}
            >
              <span className="flex items-center space-x-1.5 truncate">
                <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">
                  {job.apply_link && job.apply_link !== job.post_url
                    ? "💬 Open LinkedIn Post (Referral/DM)"
                    : isRealPost
                    ? "Open LinkedIn Hiring Post"
                    : isLinkedIn
                    ? "Apply on LinkedIn (Direct Post)"
                    : isInstahyre
                    ? "Apply on Instahyre (Direct Post)"
                    : isNaukri
                    ? "Apply on Naukri (Direct Post)"
                    : isIndeed
                    ? "Apply on Indeed (Direct Post)"
                    : "Direct Application Page"}
                </span>
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-white/20 ml-1">
                Post ↗
              </span>
            </a>
          ) : !job.apply_link ? (
            <div className="text-[11px] text-slate-500 italic px-1">
              No external link attached
            </div>
          ) : null}

          {/* 3. Find Referrals on LinkedIn (1-Click Search + Copy Note) */}
          <div className="flex items-center justify-between text-xs px-2.5 py-1.5 rounded-lg bg-sky-950/40 border border-sky-500/30 text-sky-200">
            <a
              href={referralSearchUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1.5 hover:underline truncate"
              title={`Find Software Engineers & Managers at ${job.company} on LinkedIn`}
            >
              <Users className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <span className="font-semibold truncate">Find Referrals at {job.company} ↗</span>
            </a>
            <button
              onClick={copyReferralNote}
              className="px-2 py-0.5 bg-sky-800/80 hover:bg-sky-700 text-sky-100 rounded text-[10px] font-semibold flex items-center gap-1 shrink-0 ml-1 transition"
              title="Copy pre-written LinkedIn referral request message"
            >
              {copiedReferral ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedReferral ? "Copied" : "Note"}</span>
            </button>
          </div>

          {/* 4. Direct HR Gmail Action (Opens Gmail Web, Never Outlook) */}
          {job.hr_email && (
            <div className="flex items-center justify-between text-xs px-2.5 py-2 rounded-lg bg-red-950/30 border border-red-500/30 text-red-200 shadow-sm gap-2">
              <div className="flex items-center space-x-2 truncate min-w-0">
                <div className="w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                  <Mail className="w-3 h-3 text-red-400" />
                </div>
                <div className="truncate min-w-0">
                  <div className="text-[10px] text-red-400 font-semibold uppercase tracking-wider flex items-center gap-1">
                    <span>Direct HR Email</span>
                    <span className="text-[9px] bg-red-500/20 text-red-300 px-1 rounded">Gmail</span>
                  </div>
                  <a 
                    href={`https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(job.hr_email)}&su=${encodeURIComponent(`Application: ${job.title} - 2 Years Exp (Java / Spring Boot)`)}&body=${encodeURIComponent(`Dear Hiring Team,\n\nI am writing to express my interest in the ${job.title} role at ${job.company}.\n\nI have 2 years of hands-on experience in Java, Spring Boot, Microservices, and PostgreSQL.\n\nPlease find my resume attached for your consideration.\n\nBest regards,\nAbhishek Verma`)}`}
                    target="_blank"
                    rel="noreferrer"
                    className="truncate hover:underline font-mono text-[11px] text-white font-medium block"
                    title="Click to open pre-filled compose window in Google Gmail (Bypasses Outlook)"
                  >
                    {job.hr_email}
                  </a>
                </div>
              </div>
              <div className="flex items-center space-x-1 shrink-0 ml-1">
                <a
                  href={`https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(job.hr_email)}&su=${encodeURIComponent(`Application: ${job.title} - 2 Years Exp (Java / Spring Boot)`)}&body=${encodeURIComponent(`Dear Hiring Team,\n\nI am writing to express my interest in the ${job.title} role at ${job.company}.\n\nI have 2 years of hands-on experience in Java, Spring Boot, Microservices, and PostgreSQL.\n\nPlease find my resume attached for your consideration.\n\nBest regards,\nAbhishek Verma`)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2 py-1 rounded bg-red-600 hover:bg-red-500 text-white font-bold text-[10px] flex items-center gap-1 transition shadow"
                  title="Open in Gmail"
                >
                  Gmail ↗
                </a>
                <button
                  onClick={copyEmail}
                  className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition"
                  title="Copy HR Email address"
                >
                  {copiedEmail ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          )}

          {/* 5. Google Form Link (if extracted) */}
          {job.google_form_url && (
            <a
              href={job.google_form_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between text-xs px-2.5 py-1.5 rounded-lg bg-purple-950/40 border border-purple-500/20 text-purple-200 hover:bg-purple-900/30 transition"
            >
              <span className="flex items-center space-x-1.5 truncate">
                <FileSpreadsheet className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                <span className="font-medium truncate">Google Application Form</span>
              </span>
              <ExternalLink className="w-3 h-3 text-purple-300 shrink-0 ml-1" />
            </a>
          )}
        </div>
      </div>

      {/* Card Footer Actions: Tailor Resume + Prep Interview + Stage Switcher */}
      <div className="mt-4 pt-3 border-t border-slate-700/70 flex items-center justify-between gap-1.5">
        {/* Tailor Resume Button */}
        <button
          onClick={() => onOpenTailor(job)}
          className="flex-1 min-w-0 flex items-center justify-center space-x-1 px-2.5 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-semibold text-[11px] shadow transition active:scale-95"
          title="AI ATS resume tailor & PDF download"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-300 shrink-0" />
          <span className="truncate">Tailor</span>
        </button>

        {/* Prep Interview Button */}
        {onOpenInterviewPrep && (
          <button
            onClick={() => onOpenInterviewPrep(job)}
            className="flex-1 min-w-0 flex items-center justify-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 border border-slate-600 text-amber-300 font-semibold text-[11px] shadow transition active:scale-95"
            title="Generate AI Technical Interview Prep Cheat Sheet"
          >
            <BrainCircuit className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate">Prep</span>
          </button>
        )}

        {/* Any Stage Dropdown Switcher */}
        <div className="relative shrink-0">
          <select
            value={job.status}
            onChange={(e) => onStatusChange(job.id, e.target.value)}
            className="bg-slate-700/80 hover:bg-slate-700 text-slate-200 text-[11px] font-medium rounded-lg px-2 py-1.5 border border-slate-600 focus:outline-none focus:border-sky-400 transition cursor-pointer max-w-[110px] sm:max-w-none truncate"
            title="Change Jira Stage"
          >
            {ALL_STAGES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

    </div>
  );
}
