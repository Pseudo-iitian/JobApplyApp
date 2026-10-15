import React, { useState } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  FolderSearch, 
  CheckCircle2, 
  AlertCircle,
  Code,
  Calendar,
  Sparkles
} from 'lucide-react';
import { api } from '../api';

export default function ResumeModal({ 
  activeResume, 
  onClose, 
  onRefreshResume 
}) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'path'
  const [file, setFile] = useState(null);
  const [filePath, setFilePath] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState({ type: '', text: '' });

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setStatusMessage({ type: 'error', text: 'Please select a PDF file.' });
      return;
    }
    setLoading(true);
    setStatusMessage({ type: '', text: '' });

    try {
      await api.uploadResumeFile(file);
      setStatusMessage({ type: 'success', text: 'Resume uploaded and parsed successfully!' });
      onRefreshResume();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handlePathUpload = async (e) => {
    e.preventDefault();
    if (!filePath.trim()) {
      setStatusMessage({ type: 'error', text: 'Please enter a valid file path.' });
      return;
    }
    setLoading(true);
    setStatusMessage({ type: '', text: '' });

    try {
      await api.uploadResumeByPath(filePath.trim());
      setStatusMessage({ type: 'success', text: 'Resume loaded from path and parsed successfully!' });
      onRefreshResume();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  let parsedSkills = [];
  if (activeResume && activeResume.skills) {
    try {
      parsedSkills = JSON.parse(activeResume.skills);
    } catch (e) {
      parsedSkills = [];
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl max-h-[92vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm sm:text-base text-white">Resume Management</h3>
              <p className="text-[11px] sm:text-xs text-slate-400">Upload PDF or provide absolute local file path</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 sm:p-6 space-y-5 sm:space-y-6 overflow-y-auto">
          
          {/* Active Resume Card */}
          {activeResume ? (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Active Resume Loaded
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(activeResume.uploaded_at).toLocaleDateString()}
                </span>
              </div>
              <div className="text-sm font-semibold text-slate-200">{activeResume.filename}</div>
              
              <div className="flex items-center gap-4 text-xs text-slate-300">
                <span className="flex items-center gap-1 text-amber-300">
                  <Calendar className="w-3.5 h-3.5" /> Exp: {activeResume.experience_years || 2} Years
                </span>
                <span className="text-slate-400 truncate max-w-xs">
                  {activeResume.file_path || "Uploaded via browser"}
                </span>
              </div>

              {/* Parsed Skills */}
              {parsedSkills.length > 0 && (
                <div className="pt-2 border-t border-slate-800">
                  <span className="text-[11px] font-medium text-slate-400 block mb-2">Detected Tech Skills:</span>
                  <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                    {parsedSkills.map((skill, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-sky-950/60 border border-sky-500/30 text-sky-300 rounded text-[11px]">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-center text-xs text-slate-400">
              No active resume found. Upload your resume or specify file path below.
            </div>
          )}

          {/* Tab Chooser: File Upload vs File Path */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('upload')}
              className={`pb-2.5 px-4 text-xs font-semibold transition border-b-2 flex items-center gap-2 ${
                activeTab === 'upload'
                  ? "border-sky-500 text-sky-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Upload className="w-3.5 h-3.5" /> Upload PDF File
            </button>
            <button
              onClick={() => setActiveTab('path')}
              className={`pb-2.5 px-4 text-xs font-semibold transition border-b-2 flex items-center gap-2 ${
                activeTab === 'path'
                  ? "border-sky-500 text-sky-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <FolderSearch className="w-3.5 h-3.5" /> Local File Path
            </button>
          </div>

          {/* Option 1: Direct File Upload */}
          {activeTab === 'upload' && (
            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-700 hover:border-sky-500/60 rounded-xl p-6 text-center cursor-pointer transition">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                  className="hidden"
                  id="resumeFileInput"
                />
                <label htmlFor="resumeFileInput" className="cursor-pointer flex flex-col items-center">
                  <Upload className="w-8 h-8 text-sky-400 mb-2" />
                  <span className="text-xs text-slate-200 font-medium">
                    {file ? file.name : "Click to browse or drop your PDF resume here"}
                  </span>
                  <span className="text-[11px] text-slate-500 mt-1">PDF format only (Max 10MB)</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading || !file}
                className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold text-xs transition"
              >
                {loading ? "Parsing Resume..." : "Upload & Parse Resume"}
              </button>
            </form>
          )}

          {/* Option 2: Provide Local File Path */}
          {activeTab === 'path' && (
            <form onSubmit={handlePathUpload} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">
                  Absolute Path on your machine:
                </label>
                <input
                  type="text"
                  placeholder="/home/abhishek_verma/Documents/Resume_Java_2YOE.pdf"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:outline-none rounded-xl px-3.5 py-2.5 text-xs text-slate-200 placeholder-slate-600 transition"
                />
                <p className="text-[11px] text-slate-500 mt-1.5">
                  App will read and extract skills directly from this local file.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !filePath.trim()}
                className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold text-xs transition"
              >
                {loading ? "Reading File..." : "Load Resume From Path"}
              </button>
            </form>
          )}

          {/* Status Message */}
          {statusMessage.text && (
            <div className={`p-3 rounded-xl text-xs flex items-center space-x-2 ${
              statusMessage.type === 'success' 
                ? "bg-emerald-950/60 border border-emerald-500/30 text-emerald-300" 
                : "bg-rose-950/60 border border-rose-500/30 text-rose-300"
            }`}>
              {statusMessage.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
              <span>{statusMessage.text}</span>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
