import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import KanbanBoard from './components/KanbanBoard';
import NotificationDropdown from './components/NotificationDropdown';
import TailorModal from './components/TailorModal';
import ResumeModal from './components/ResumeModal';
import SettingsModal from './components/SettingsModal';
import HunterLogsModal from './components/HunterLogsModal';
import AutoApplyModal from './components/AutoApplyModal';
import AnalyticsModal from './components/AnalyticsModal';
import InterviewPrepModal from './components/InterviewPrepModal';
import { api, WS_BASE } from './api';
import { Bell, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [activeResume, setActiveResume] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // UI Modals
  const [showNotifications, setShowNotifications] = useState(false);
  const [showResumeModal, setShowResumeModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [showAutoApplyModal, setShowAutoApplyModal] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [tailorJob, setTailorJob] = useState(null);
  const [prepJob, setPrepJob] = useState(null);
  
  // Status states
  const [isSearching, setIsSearching] = useState(false);
  const [liveToast, setLiveToast] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch initial data
  const loadJobs = useCallback(async () => {
    try {
      const data = await api.getJobs();
      if (Array.isArray(data)) {
        setJobs(data);
      }
    } catch (err) {
      console.error("Failed to load jobs:", err);
      // Automatically retry immediately if server was starting up
      try {
        await new Promise(r => setTimeout(r, 1000));
        const retryData = await api.getJobs();
        if (Array.isArray(retryData)) {
          setJobs(retryData);
        }
      } catch (retryErr) {
        console.error("Retry failed to load jobs:", retryErr);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadResume = useCallback(async () => {
    try {
      const data = await api.getActiveResume();
      setActiveResume(data);
    } catch (err) {
      console.error("No active resume:", err);
    }
  }, []);

  const loadNotifications = useCallback(async () => {
    try {
      const data = await api.getNotifications();
      setNotifications(data);
      const unread = data.filter((n) => !n.is_read).length;
      setUnreadCount(unread);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    }
  }, []);

  useEffect(() => {
    loadJobs();
    loadResume();
    loadNotifications();

    // Guard: ensure loading spinner is never permanently stuck
    const safetyTimer = setTimeout(() => {
      setIsLoading(false);
    }, 8000);

    return () => clearTimeout(safetyTimer);
  }, [loadJobs, loadResume, loadNotifications]);

  // Establish resilient WebSocket with auto-reconnection for 24/7 Realtime Alerts
  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;
    let isUnmounted = false;

    const connectWs = () => {
      if (isUnmounted) return;
      try {
        ws = new WebSocket(WS_BASE);

        ws.onopen = () => {
          console.log("WebSocket connected to JobApplyApp 24/7 stream.");
          if (window.Notification && Notification.permission === "default") {
            try { Notification.requestPermission(); } catch (e) {}
          }
          // Refresh jobs immediately upon connection/reconnection
          loadJobs();
          loadNotifications();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.event === "NEW_JOB_FOUND") {
              // Play gentle notification sound
              try {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (AudioCtx) {
                  const ctx = new AudioCtx();
                  const osc = ctx.createOscillator();
                  const gain = ctx.createGain();
                  osc.connect(gain);
                  gain.connect(ctx.destination);
                  osc.type = "sine";
                  osc.frequency.setValueAtTime(587.33, ctx.currentTime);
                  osc.frequency.setValueAtTime(880, ctx.currentTime + 0.1);
                  gain.gain.setValueAtTime(0.15, ctx.currentTime);
                  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
                  osc.start();
                  osc.stop(ctx.currentTime + 0.35);
                }
              } catch (soundErr) {}

              // Desktop browser notification if permitted
              if (window.Notification && Notification.permission === "granted") {
                new Notification(`🎯 ${data.job.title}`, {
                  body: `${data.job.company} (${data.job.experience_str}) - Discovered!`,
                  icon: "/favicon.ico"
                });
              }

              setLiveToast({
                title: "🎯 New 2-Year Java Job Found!",
                message: `${data.job.title} at ${data.job.company} (${data.job.experience_str})`
              });
              setTimeout(() => setLiveToast(null), 6000);
              loadJobs();
              loadNotifications();
            } else if (data.event === "JOB_STATUS_UPDATED" || data.event === "JOB_STATUS_CHANGED") {
              loadJobs();
            }
          } catch (e) {
            console.error("WS parse error:", e);
          }
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            reconnectTimeout = setTimeout(connectWs, 3000);
          }
        };

        ws.onerror = () => {
          if (ws) ws.close();
        };
      } catch (e) {
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connectWs, 3000);
        }
      }
    };

    connectWs();

    return () => {
      isUnmounted = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, [loadJobs, loadNotifications]);

  // Actions
  const handleStatusChange = async (jobId, newStatus) => {
    const previousJobs = [...jobs];
    // Instant Optimistic UI Update (0ms response time)
    setJobs((prev) =>
      prev.map((j) => (j.id === jobId ? { ...j, status: newStatus } : j))
    );
    try {
      await api.updateJobStatus(jobId, newStatus);
      loadNotifications();
    } catch (err) {
      console.error("Failed to update status on AWS RDS:", err);
      // Rollback on network/DB error
      setJobs(previousJobs);
      setLiveToast({
        title: "Update Failed",
        message: "Could not save status change. Reverted to previous stage."
      });
      setTimeout(() => setLiveToast(null), 4000);
    }
  };

  const handleDeleteJob = async (jobId) => {
    const previousJobs = [...jobs];
    // Instant Optimistic Deletion
    setJobs((prev) => prev.filter((j) => j.id !== jobId));
    try {
      await api.deleteJob(jobId);
    } catch (err) {
      console.error("Failed to delete job on AWS RDS:", err);
      setJobs(previousJobs);
      setLiveToast({
        title: "Delete Failed",
        message: "Could not delete job ticket. Restored."
      });
      setTimeout(() => setLiveToast(null), 4000);
    }
  };

  const handleTriggerSearch = async () => {
    setIsSearching(true);
    try {
      const res = await api.triggerSearch();
      await loadJobs();
      await loadNotifications();
      const count = res.new_jobs_count || 0;
      setLiveToast({
        title: count > 0 ? "🎯 Hunt Cycle Completed!" : "✔ Hunt Cycle Finished",
        message: count > 0 
          ? `Discovered and added ${count} new 2-year Java developer roles to AWS RDS!` 
          : "Checked LinkedIn & developer feeds. All qualified postings already tracked."
      });
      setTimeout(() => setLiveToast(null), 6000);
    } catch (err) {
      console.error("Job search trigger failed:", err);
      setLiveToast({
        title: "Hunt Cycle Failed",
        message: "Network or scraping notice. Please check live logs."
      });
      setTimeout(() => setLiveToast(null), 5000);
    } finally {
      setIsSearching(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await api.markNotificationRead(id);
      loadNotifications();
    } catch (err) {
      console.error("Mark read error:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      loadNotifications();
    } catch (err) {
      console.error("Mark all read error:", err);
    }
  };

  const handleClearNotifications = async () => {
    try {
      await api.clearNotifications();
      loadNotifications();
    } catch (err) {
      console.error("Clear notifications error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* Top Navbar */}
      <Navbar
        onOpenResume={() => setShowResumeModal(true)}
        onOpenSettings={() => setShowSettingsModal(true)}
        onOpenLogs={() => setShowLogsModal(true)}
        onOpenAnalytics={() => setShowAnalyticsModal(true)}
        onOpenAutoApply={() => setShowAutoApplyModal(true)}
        onTriggerSearch={handleTriggerSearch}
        isSearching={isSearching}
        unreadCount={unreadCount}
        onToggleNotifications={() => setShowNotifications(!showNotifications)}
        activeResume={activeResume}
      />

      {/* Realtime Toast Banner */}
      {liveToast && (
        <div className="fixed bottom-4 sm:bottom-6 right-4 sm:right-6 left-4 sm:left-auto z-50 bg-gradient-to-r from-sky-600 to-indigo-600 border border-sky-400/40 text-white p-3.5 sm:p-4 rounded-2xl shadow-2xl flex items-center space-x-3.5 max-w-md animate-in slide-in-from-bottom-5">
          <div className="p-2 bg-white/20 rounded-xl shrink-0">
            <Bell className="w-5 h-5 text-white animate-bounce" />
          </div>
          <div className="flex-1 min-w-0">
            <h5 className="font-bold text-xs uppercase tracking-wide text-sky-200 truncate">{liveToast.title}</h5>
            <p className="text-xs text-white mt-0.5 font-medium line-clamp-2">{liveToast.message}</p>
          </div>
        </div>
      )}

      {/* Notification Drawer Dropdown */}
      {showNotifications && (
        <NotificationDropdown
          notifications={notifications}
          onClose={() => setShowNotifications(false)}
          onMarkRead={handleMarkRead}
          onMarkAllRead={handleMarkAllRead}
          onClearAll={handleClearNotifications}
        />
      )}

      {/* Main Kanban Content */}
      <main className="flex-1 flex flex-col">
        <KanbanBoard
          jobs={jobs}
          onStatusChange={handleStatusChange}
          onDeleteJob={handleDeleteJob}
          onOpenTailor={(job) => setTailorJob(job)}
          onOpenInterviewPrep={(job) => setPrepJob(job)}
          onOpenAutoApply={() => setShowAutoApplyModal(true)}
          onRefreshJobs={loadJobs}
          isLoading={isLoading}
        />
      </main>

      {/* Modals */}
      {tailorJob && (
        <TailorModal
          job={tailorJob}
          onClose={() => setTailorJob(null)}
        />
      )}

      {prepJob && (
        <InterviewPrepModal
          job={prepJob}
          onClose={() => setPrepJob(null)}
        />
      )}

      {showResumeModal && (
        <ResumeModal
          activeResume={activeResume}
          onClose={() => setShowResumeModal(false)}
          onRefreshResume={() => {
            loadResume();
            loadJobs();
          }}
        />
      )}

      {showSettingsModal && (
        <SettingsModal
          onClose={() => setShowSettingsModal(false)}
          onSettingsUpdated={() => {
            loadJobs();
          }}
        />
      )}

      {showLogsModal && (
        <HunterLogsModal
          onClose={() => setShowLogsModal(false)}
          onTriggerSearch={handleTriggerSearch}
          isSearching={isSearching}
        />
      )}

      {showAutoApplyModal && (
        <AutoApplyModal
          isOpen={showAutoApplyModal}
          onClose={() => setShowAutoApplyModal(false)}
          onRefreshJobs={loadJobs}
        />
      )}

      {showAnalyticsModal && (
        <AnalyticsModal
          onClose={() => setShowAnalyticsModal(false)}
        />
      )}

    </div>
  );
}
