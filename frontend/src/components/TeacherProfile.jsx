import React, { useEffect, useState } from 'react';
import { Award, TrendingUp, CheckCircle, Lightbulb, BookOpen, User, BarChart2 } from 'lucide-react';

export default function TeacherProfile({ apiBase, teacherId = 'teacher_1' }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfile();
  }, [teacherId, apiBase]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiBase}/api/teachers/${teacherId}/profile`);
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch (err) {
      console.warn("Could not fetch teacher profile:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-slate-400 p-8 text-center text-sm">Loading teacher profile...</div>;
  }

  if (!profile) {
    return <div className="text-slate-400 p-8 text-center text-sm">Teacher profile not found.</div>;
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top Banner Card */}
      <div className="glass-panel p-6 flex flex-wrap items-center justify-between gap-6 border-l-4 border-l-cyan-500">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center text-white shadow-lg shadow-cyan-950/50">
            <User className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">{profile.name}</h2>
            <div className="flex items-center gap-3 text-slate-400 text-xs mt-1">
              <span>{profile.department}</span>
              <span>•</span>
              <span>ID: {profile.teacher_id}</span>
              <span>•</span>
              <span>{profile.sessions_conducted} Sessions Conducted</span>
            </div>
          </div>
        </div>

        {/* Effectiveness Score Pill */}
        <div className="flex items-center gap-6 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <div className="text-right">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block">Teacher Effectiveness</span>
            <span className="text-3xl font-extrabold text-cyan-400">{profile.effectiveness_score}</span>
            <span className="text-xs text-slate-400"> / 100</span>
          </div>
          <div className="border-l border-slate-800 pl-4 flex flex-col justify-center">
            <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" />
              {profile.comparison_summary}
            </span>
            <span className="text-[11px] text-slate-500">Dept Baseline: {profile.department_benchmark}%</span>
          </div>
        </div>
      </div>

      {/* Two Column Grid: Strengths & Growth Areas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Identified Strengths */}
        <div className="glass-panel p-5 flex flex-col gap-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5">
            <Award className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">Demonstrated Pedagogical Strengths</h3>
          </div>
          <div className="flex flex-col gap-2.5 pt-1">
            {profile.strengths?.map((str, idx) => (
              <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-900/50 p-3 rounded-lg border border-slate-800">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{str}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Actionable Tips */}
        <div className="glass-panel p-5 flex flex-col gap-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">Suggested Growth & Pacing Tweaks</h3>
          </div>
          <div className="flex flex-col gap-2.5 pt-1">
            {profile.actionable_tips?.map((tip, idx) => (
              <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-900/50 p-3 rounded-lg border border-slate-800">
                <Lightbulb className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{tip}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Historical Sessions Table */}
      <div className="glass-panel p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">Class History & Pacing Comparison</h3>
          </div>
          <span className="text-xs text-slate-400">Past Lecture Performance</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <th className="pb-3 px-3">Date</th>
                <th className="pb-3 px-3">Session Title</th>
                <th className="pb-3 px-3">Average Engagement</th>
                <th className="pb-3 px-3">Attendance Rate</th>
                <th className="pb-3 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {profile.historical_trend?.map((h, i) => (
                <tr key={i} className="hover:bg-slate-900/40 transition">
                  <td className="py-3 px-3 font-mono text-slate-400">{h.date}</td>
                  <td className="py-3 px-3 font-medium text-white">{h.title}</td>
                  <td className="py-3 px-3">
                    <span className="font-mono text-cyan-400 font-semibold">{h.engagement}%</span>
                  </td>
                  <td className="py-3 px-3">
                    <span className="font-mono text-emerald-400 font-semibold">{h.attendance}%</span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 rounded text-[11px] border border-emerald-800">
                      Completed
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
