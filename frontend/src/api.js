const API_HOST = (typeof window !== "undefined" && window.location)
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : "http://localhost:8000";

export const API_BASE = `${API_HOST}/api`;
export const WS_BASE = `${API_HOST.replace(/^http/, 'ws')}/api/notifications/ws`;

async function fetchWithTimeout(url, options = {}, timeoutMs = 25000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timer);
    return res;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

export const api = {
  getDownloadTailoredResumeUrl(jobId) {
    return `${API_BASE}/jobs/${jobId}/download-tailored-resume`;
  },

  // Jobs
  async getJobs(statusFilter = null) {
    const url = statusFilter ? `${API_BASE}/jobs?status_filter=${statusFilter}` : `${API_BASE}/jobs`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error("Failed to fetch jobs");
    return res.json();
  },

  async updateJobStatus(jobId, status) {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    if (!res.ok) throw new Error("Failed to update job status");
    return res.json();
  },

  async deleteJob(jobId) {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete job");
    return true;
  },

  async triggerSearch() {
    const res = await fetch(`${API_BASE}/jobs/trigger-search`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to trigger job search");
    return res.json();
  },

  async getHunterStatus() {
    const res = await fetch(`${API_BASE}/jobs/hunter-status`);
    if (!res.ok) throw new Error("Failed to fetch hunter status");
    return res.json();
  },

  async getJobAnalytics() {
    const res = await fetchWithTimeout(`${API_BASE}/jobs/analytics`);
    if (!res.ok) throw new Error("Failed to fetch job analytics");
    return res.json();
  },

  async tailorResume(jobId) {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/tailor-resume`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to generate tailored resume");
    return res.json();
  },

  async getInterviewPrep(jobId) {
    const res = await fetchWithTimeout(`${API_BASE}/jobs/${jobId}/interview-prep`, { method: "POST" }, 30000);
    if (!res.ok) throw new Error("Failed to generate interview prep cheat sheet");
    return res.json();
  },

  // Resume
  async getActiveResume() {
    const res = await fetchWithTimeout(`${API_BASE}/resume/active`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error("Failed to fetch active resume");
    return res.json();
  },

  async uploadResumeFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetchWithTimeout(`${API_BASE}/resume/upload`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to upload resume file");
    }
    return res.json();
  },

  async uploadResumeByPath(filePath) {
    const res = await fetchWithTimeout(`${API_BASE}/resume/file-path`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_path: filePath })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to load resume from path");
    }
    return res.json();
  },

  // Notifications
  async getNotifications() {
    const res = await fetchWithTimeout(`${API_BASE}/notifications`);
    if (!res.ok) throw new Error("Failed to fetch notifications");
    return res.json();
  },

  async markNotificationRead(id) {
    const res = await fetchWithTimeout(`${API_BASE}/notifications/${id}/read`, { method: "PATCH" });
    if (!res.ok) throw new Error("Failed to mark notification as read");
    return res.json();
  },

  async markAllNotificationsRead() {
    const res = await fetchWithTimeout(`${API_BASE}/notifications/mark-all-read`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to mark all notifications read");
    return res.json();
  },

  async clearNotifications() {
    const res = await fetchWithTimeout(`${API_BASE}/notifications/clear`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to clear notifications");
    return res.json();
  },

  // Settings
  async getSettings() {
    const res = await fetchWithTimeout(`${API_BASE}/settings`);
    if (!res.ok) throw new Error("Failed to fetch settings");
    return res.json();
  },

  async updateSettings(data) {
    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Failed to update settings");
    return res.json();
  },

  // Auto-Apply Agent
  async getAutoApplyProfile() {
    const res = await fetch(`${API_BASE}/auto-apply/profile`);
    if (!res.ok) throw new Error("Failed to fetch auto-apply profile");
    return res.json();
  },

  async updateAutoApplyProfile(data) {
    const res = await fetch(`${API_BASE}/auto-apply/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Failed to update auto-apply profile");
    return res.json();
  },

  async getAutoApplyCredentials() {
    const res = await fetch(`${API_BASE}/auto-apply/credentials`);
    if (!res.ok) throw new Error("Failed to fetch credentials");
    return res.json();
  },

  async getAutoApplyLogs() {
    const res = await fetch(`${API_BASE}/auto-apply/logs`);
    if (!res.ok) throw new Error("Failed to fetch auto-apply logs");
    return res.json();
  },

  async runAutoApply(batchSize = 5, autoOpenBrowser = true) {
    const res = await fetch(`${API_BASE}/auto-apply/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ batch_size: batchSize, auto_open_browser: autoOpenBrowser })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Auto-Apply Agent failed to execute");
    }
    return res.json();
  },

  async stopAutoApply() {
    const res = await fetch(`${API_BASE}/auto-apply/stop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to stop Auto-Apply Agent");
    }
    return res.json();
  },

  async getAutoApplyStatus() {
    const res = await fetch(`${API_BASE}/auto-apply/status`);
    if (!res.ok) throw new Error("Failed to fetch agent status");
    return res.json();
  }
};
