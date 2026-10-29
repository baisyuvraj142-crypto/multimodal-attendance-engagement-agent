import React, { useEffect, useState } from 'react';
import { Download, FileText, Table, Users, Clock, Activity, ShieldCheck, HeartHandshake } from 'lucide-react';

export default function Analytics({ apiBase, sessions = [], selectedSessionId, onSelectSession }) {
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(false);

  const activeId = selectedSessionId || (sessions[0] ? sessions[0].id : null);

  useEffect(() => {
    if (activeId) {
      fetchTrends(activeId);
    }
  }, [activeId, apiBase]);

  const fetchTrends = async (sessionId) => {
    try {
      setLoading(true);
      const res = await fetch(`${apiBase}/api/sessions/${sessionId}/trends`);
      if (res.ok) {
        const data = await res.json();
        setTrends(data);
      }
    } catch (err) {
      console.warn("Could not fetch trends:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header & Export Controls */}
      <div className="glass-panel p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Select Session:</label>
          <select
            value={activeId || ''}
            onChange={(e) => onSelectSession(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-cyan-500"
          >
            {sessions.length === 0 && <option value="">No sessions recorded yet</option>}
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title} ({s.id}) — {s.start_time ? s.start_time.substring(0, 10) : ''}
              </option>
            ))}
          </select>
        </div>

        {activeId && (
          <div className="flex items-center gap-3">
            <a
              href={`${apiBase}/api/sessions/${activeId}/report.pdf`}
              download
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-950 transition active:scale-95"
            >
              <FileText className="w-3.5 h-3.5" />
              Download PDF Report
            </a>

            <a
              href={`${apiBase}/api/sessions/${activeId}/export.csv`}
              download
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition active:scale-95"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV Ledger
            </a>
          </div>
        )}
      </div>

      {loading && (
        <div className="text-center text-slate-400 py-12 text-xs">
          Loading analytics and reflective logs...
        </div>
      )}

      {trends && !loading && (
        <>
          {/* Engagement Distribution Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="glass-card p-4 border-l-4 border-l-emerald-500">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block">High Engagement Phase</span>
              <span className="text-2xl font-bold text-emerald-400 mt-1 block">
                {trends.distribution?.high_percentage ?? 0}%
              </span>
              <span className="text-[11px] text-slate-500">Active dialogue & sustained visual focus</span>
            </div>

            <div className="glass-card p-4 border-l-4 border-l-cyan-500">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block">Moderate / Lecture Phase</span>
              <span className="text-2xl font-bold text-cyan-400 mt-1 block">
                {trends.distribution?.medium_percentage ?? 0}%
              </span>
              <span className="text-[11px] text-slate-500">Quiet attentive listening & note-taking</span>
            </div>

            <div className="glass-card p-4 border-l-4 border-l-amber-500">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block">Attention Ebb Phase</span>
              <span className="text-2xl font-bold text-amber-400 mt-1 block">
                {trends.distribution?.low_percentage ?? 0}%
              </span>
              <span className="text-[11px] text-slate-500">Opportunities for pedagogical reset</span>
            </div>
          </div>

          {/* Temporal Profile Chart */}
          <div className="glass-panel p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white">Temporal Attention & Acoustic Trend Profile</h3>
              </div>
              <div className="flex items-center gap-4 text-[11px]">
                <span className="flex items-center gap-1.5 text-cyan-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                  Visual Attention
                </span>
                <span className="flex items-center gap-1.5 text-purple-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span>
                  Audio Energy
                </span>
              </div>
            </div>

            {/* Custom SVG Line / Bar Visualization */}
            <div className="h-48 w-full bg-slate-900/60 rounded-lg p-3 flex items-end gap-1.5 border border-slate-800 overflow-x-auto">
              {trends.timeline && trends.timeline.length > 0 ? (
                trends.timeline.slice(-30).map((t, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1 min-w-[14px] group relative">
                    {/* Tooltip */}
                    <div className="absolute -top-10 hidden group-hover:flex flex-col bg-slate-950 border border-slate-700 px-2 py-1 rounded text-[10px] text-slate-200 z-10 whitespace-nowrap shadow-lg">
                      <span>Attention: {t.attention}%</span>
                      <span>Noise: {t.noise_db} dB</span>
                    </div>

                    {/* Bar visualization */}
                    <div
                      className="w-full bg-cyan-500/80 rounded-t transition-all hover:bg-cyan-400"
                      style={{ height: `${Math.max(8, t.attention)}%` }}
                    ></div>
                    <span className="text-[9px] text-slate-500 font-mono">
                      {t.timestamp.substring(14, 19)}
                    </span>
                  </div>
                ))
              ) : (
                <div className="w-full h-full flex items-center justify-center text-xs text-slate-500">
                  Timeline data is generated as the session progresses.
                </div>
              )}
            </div>
          </div>

          {/* Student Reflective Summaries (NFR-2 & Acceptance Criteria 4) */}
          <div className="glass-panel p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <HeartHandshake className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-semibold text-white">Student Reflective Session Summaries</h3>
              </div>
              <span className="text-[11px] text-emerald-400 bg-emerald-950/60 px-2.5 py-0.5 rounded border border-emerald-800/40">
                Ethical Policy: Zero Grades & Zero Ranking
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              In accordance with EduSense AI's privacy and non-punitive ethics charter, individual students receive constructive learning reflections based on presence continuity, with no grading or peer comparisons.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              {trends.student_summaries && trends.student_summaries.length > 0 ? (
                trends.student_summaries.map((s, idx) => (
                  <div key={idx} className="glass-card p-4 flex flex-col gap-2.5 border-slate-800">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-cyan-400" />
                        <span className="font-bold text-xs text-white">{s.label}</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.attendance_status === 'Present'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}>
                        {s.attendance_status} ({s.presence_seconds}s)
                      </span>
                    </div>

                    <div className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
                      <span className="text-slate-400 font-semibold block mb-0.5">Reflective Note:</span>
                      {s.reflective_summary}
                    </div>

                    <div className="text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800 pt-1.5">
                      <span>Consistency: <strong className="text-slate-200">{s.consistency}</strong></span>
                      <span className="italic">{s.activity_trend}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="col-span-2 text-xs text-slate-500 py-6 text-center italic">
                  No participant attendance summaries recorded for this session yet.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
