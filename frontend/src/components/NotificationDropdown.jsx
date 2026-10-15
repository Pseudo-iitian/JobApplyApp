import React from 'react';
import { Bell, Check, Trash2, X, ExternalLink, Briefcase } from 'lucide-react';

export default function NotificationDropdown({ 
  notifications, 
  onClose, 
  onMarkRead, 
  onMarkAllRead, 
  onClearAll 
}) {
  return (
    <>
      {/* Mobile backdrop to easily close when tapping outside */}
      <div 
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs sm:hidden"
        onClick={onClose}
      />
      <div className="fixed inset-x-3 top-16 sm:inset-auto sm:right-6 sm:top-16 sm:w-96 max-w-full sm:max-w-[90vw] bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl z-50 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
        <div className="flex items-center space-x-2">
          <Bell className="w-4 h-4 text-sky-400" />
          <span className="font-semibold text-sm text-white">Live Job Alerts</span>
          <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">
            {notifications.length}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {notifications.length > 0 && (
            <>
              <button
                onClick={onMarkAllRead}
                className="text-xs text-sky-400 hover:text-sky-300 font-medium"
                title="Mark all read"
              >
                Read All
              </button>
              <button
                onClick={onClearAll}
                className="text-slate-400 hover:text-rose-400 p-1"
                title="Clear all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </>
          )}
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Notifications List */}
      <div className="max-h-96 overflow-y-auto divide-y divide-slate-800/60">
        {notifications.length === 0 ? (
          <div className="py-10 text-center text-slate-500 text-xs flex flex-col items-center">
            <Bell className="w-8 h-8 stroke-1 text-slate-600 mb-2" />
            No notifications yet. The 24/7 background worker is hunting jobs!
          </div>
        ) : (
          notifications.map((notif) => (
            <div
              key={notif.id}
              onClick={() => !notif.is_read && onMarkRead(notif.id)}
              className={`p-3.5 text-xs transition cursor-pointer flex space-x-3 ${
                notif.is_read ? "bg-slate-900/40 text-slate-400" : "bg-sky-950/30 text-slate-200 border-l-2 border-sky-500"
              } hover:bg-slate-800/60`}
            >
              <div className="mt-0.5">
                <Briefcase className={`w-4 h-4 ${notif.is_read ? "text-slate-500" : "text-sky-400"}`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">{notif.title}</span>
                  {!notif.is_read && (
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
                  )}
                </div>
                <div className="mt-1 text-slate-400 text-[11px] leading-relaxed">
                  {(() => {
                    const emailRegex = /([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/g;
                    if (!notif.message || !notif.message.match(emailRegex)) {
                      return notif.message;
                    }
                    const parts = notif.message.split(emailRegex);
                    return parts.map((part, i) => {
                      if (part.match(emailRegex)) {
                        return (
                          <a
                            key={i}
                            href={`https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(part)}&su=${encodeURIComponent(`Application - Java Backend Developer (2 Years Exp)`)}`}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-red-400 hover:text-red-300 font-semibold underline mx-1 inline-flex items-center gap-0.5"
                            title="Compose directly in Gmail (Never Outlook)"
                          >
                            <span>{part}</span>
                            <span className="text-[9px] bg-red-600/30 text-red-200 px-1 py-0.2 rounded font-sans">Gmail ↗</span>
                          </a>
                        );
                      }
                      return part;
                    });
                  })()}
                </div>
                <span className="mt-1.5 block text-[10px] text-slate-500">
                  {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
    </>
  );
}
