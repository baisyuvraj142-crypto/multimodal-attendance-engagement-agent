import React, { useState, useEffect } from 'react';
import { Video, BarChart3, UserCheck, ShieldCheck, Sparkles, Plus, GraduationCap } from 'lucide-react';
import LiveSession from './components/LiveSession';
import Analytics from './components/Analytics';
import TeacherProfile from './components/TeacherProfile';

export default function App() {
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'analytics' | 'profile'
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [showStartModal, setShowStartModal] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState('Lecture 04: Neural Attention & Multimodal Transformers');

  const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
  const WS_BASE = window.location.hostname === 'localhost' ? 'ws://localhost:8000' : `ws://${window.location.host}`;

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0 && !selectedSessionId) {
          setSelectedSessionId(data[0].id);
        }
      }
    } catch (err) {
      console.warn("Could not load sessions:", err);
    }
  };

  const handleStartSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newSessionTitle || 'Interactive Lecture Session',
          teacher_id: 'teacher_1'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentSession(data);
        setSelectedSessionId(data.id);
        setShowStartModal(false);
        setActiveTab('live');
        fetchSessions();
      }
    } catch (err) {
      console.error("Error starting session:", err);
    }
  };

  const handleEndSession = async () => {
    if (!currentSession) return;
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${currentSession.id}/end`, {
        method: 'POST'
      });
      if (res.ok) {
        setCurrentSession(null);
        fetchSessions();
      }
    } catch (err) {
      console.error("Error ending session:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-950/60">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-extrabold tracking-tight text-white">EduSense AI</h1>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded-full">
                Multimodal Agent
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Classroom Attendance & Pedagogical Intelligence</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1.5 bg-slate-950/70 p-1.5 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('live')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition ${
              activeTab === 'live'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Video className="w-4 h-4" />
            Live Session
            {currentSession?.status === 'active' && (
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition ${
              activeTab === 'analytics'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Analytics & Reports
          </button>

          <button
            onClick={() => setActiveTab('profile')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition ${
              activeTab === 'profile'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            Teacher Profile
          </button>
        </nav>

        {/* Privacy Notice Badge & Action */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Privacy Compliant (Derived Metrics Only)</span>
          </div>

          {!currentSession && (
            <button
              onClick={() => setShowStartModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white shadow-sm transition active:scale-95"
            >
              <Plus className="w-4 h-4" />
              New Session
            </button>
          )}
        </div>
      </header>

      {/* Main Content View */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === 'live' && (
          <LiveSession
            apiBase={API_BASE}
            wsBase={WS_BASE}
            currentSession={currentSession}
            onStartSession={() => setShowStartModal(true)}
            onEndSession={handleEndSession}
          />
        )}

        {activeTab === 'analytics' && (
          <Analytics
            apiBase={API_BASE}
            sessions={sessions}
            selectedSessionId={selectedSessionId}
            onSelectSession={setSelectedSessionId}
          />
        )}

        {activeTab === 'profile' && (
          <TeacherProfile
            apiBase={API_BASE}
            teacherId="teacher_1"
          />
        )}
      </main>

      {/* Modal for Starting New Session */}
      {showStartModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-panel max-w-md w-full p-6 border-slate-700 flex flex-col gap-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-cyan-400" />
                <h3 className="font-bold text-white text-base">Launch Classroom Session</h3>
              </div>
              <button
                onClick={() => setShowStartModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-xs text-slate-400 font-semibold mb-1 block">Lecture Topic / Title</label>
                <input
                  type="text"
                  value={newSessionTitle}
                  onChange={(e) => setNewSessionTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. Distributed Systems & Consensus"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold mb-1 block">Assigned Instructor</label>
                <input
                  type="text"
                  disabled
                  value="Dr. Sarah Mitchell (School of CS & AI)"
                  className="w-full bg-slate-900/50 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-400 cursor-not-allowed"
                />
              </div>

              <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  Attendance requires cumulative continuous presence of 60 seconds (intermittent appearances accumulate). Raw video/audio is processed in memory and never stored.
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowStartModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleStartSession}
                className="px-5 py-2 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-950 transition active:scale-95"
              >
                Start Intelligence Agent
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-4 px-6 text-center text-xs text-slate-500 flex flex-wrap items-center justify-between gap-3">
        <span>EduSense AI v1.0 • Prepared for SkillWallet – Generative AI with Google Cloud</span>
        <div className="flex items-center gap-4 text-[11px]">
          <span>FastAPI</span>
          <span>•</span>
          <span>OpenCV Haar + DeepSORT</span>
          <span>•</span>
          <span>16kHz Audio VAD</span>
          <span>•</span>
          <span>Groq LLM Fallback</span>
        </div>
      </footer>
    </div>
  );
}
