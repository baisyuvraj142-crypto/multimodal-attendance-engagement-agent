import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, Video, Upload, Users, Activity, Sparkles, AlertTriangle, Info, Clock, ShieldCheck, HelpCircle } from 'lucide-react';
import AudioCapture from './AudioCapture';

export default function LiveSession({ apiBase, wsBase, currentSession, onStartSession, onEndSession }) {
  const [videoMode, setVideoMode] = useState('webcam'); // 'webcam' | 'file' | 'simulation'
  const [isCapturing, setIsCapturing] = useState(false);
  const [sessionTime, setSessionTime] = useState(0);
  
  // Real-time telemetry state
  const [liveOverlay, setLiveOverlay] = useState(null);
  const [activeTracks, setActiveTracks] = useState([]);
  const [engagementData, setEngagementData] = useState({
    overall_score: 0,
    attention_component: 0,
    movement_component: 0,
    audio_component: 0,
    level: 'Inactive',
    explanation: 'Start a session to begin live multimodal tracking.'
  });
  const [audioMetrics, setAudioMetrics] = useState({ noise_db: -50.0, speech_ratio: 0.0, state: 'silence' });
  const [suggestions, setSuggestions] = useState([]);
  const [liveInsight, setLiveInsight] = useState({ source: 'EduSense Agent', insight: 'Awaiting session activation...' });
  const [errorMsg, setErrorMsg] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const frameIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const latestAudioChunkRef = useRef(null);

  // Session clock timer
  useEffect(() => {
    if (currentSession && currentSession.status === 'active') {
      setIsCapturing(true);
      timerIntervalRef.current = setInterval(() => {
        setSessionTime((prev) => prev + 1);
      }, 1000);
    } else {
      setIsCapturing(false);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      setSessionTime(0);
      stopMediaStream();
    }

    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [currentSession]);

  // WebSocket connection management
  useEffect(() => {
    if (!currentSession || currentSession.status !== 'active') {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    const wsUrl = `${wsBase}/ws/live?session_id=${currentSession.id}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[Live WebSocket] Connected to session:", currentSession.id);
      setErrorMsg(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'live_sync') {
          if (data.overlay_frame) setLiveOverlay(data.overlay_frame);
          if (data.active_tracks) setActiveTracks(data.active_tracks);
          if (data.engagement) setEngagementData(data.engagement);
          if (data.fused) setAudioMetrics({
            noise_db: data.fused.audio_noise_db,
            speech_ratio: data.fused.audio_speech_ratio,
            state: data.fused.audio_state
          });
          if (data.suggestions && data.suggestions.length > 0) {
            setSuggestions((prev) => {
              const combined = [...data.suggestions, ...prev];
              // Keep latest 10 unique suggestions
              const seen = new Set();
              return combined.filter(item => {
                const k = item.rule_id + item.timestamp;
                return seen.has(k) ? false : seen.add(k);
              }).slice(0, 10);
            });
          }
          if (data.live_insight && data.live_insight.insight) {
            setLiveInsight(data.live_insight);
          }
        }
      } catch (err) {
        console.error("WebSocket message parsing error:", err);
      }
    };

    ws.onerror = (e) => {
      console.warn("WebSocket error:", e);
      setErrorMsg("WebSocket connection disrupted. Reconnecting...");
    };

    ws.onclose = () => {
      console.log("[Live WebSocket] Closed.");
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [currentSession, wsBase]);

  // Media Capture & Frame Transmission
  useEffect(() => {
    if (!isCapturing) {
      stopMediaStream();
      return;
    }

    if (videoMode === 'webcam') {
      startWebcam();
    }

    // Start frame loop (~10 FPS to meet NFR-3)
    frameIntervalRef.current = setInterval(() => {
      captureAndSendFrame();
    }, 100);

    return () => {
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
      stopMediaStream();
    };
  }, [isCapturing, videoMode]);

  const startWebcam = async () => {
    try {
      setErrorMsg(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { max: 15 } }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }
    } catch (err) {
      console.warn("Webcam access error:", err);
      setErrorMsg("Camera access denied or unavailable. You can use 'Pre-recorded Video' or 'Simulation' mode.");
    }
  };

  const stopMediaStream = () => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
  };

  const captureAndSendFrame = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    if (videoMode === 'simulation') {
      // Generate synthetic simulated frame to test edge-cases without physical camera
      sendSimulatedData();
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState !== 4) return;

    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const frameBase64 = canvas.toDataURL('image/jpeg', 0.65);
    const audioChunk = latestAudioChunkRef.current;
    latestAudioChunkRef.current = null; // consume chunk

    wsRef.current.send(JSON.stringify({
      frame: frameBase64,
      audio: audioChunk
    }));
  };

  // Synthetic demo generator for testing offline or camera-less environments
  const sendSimulatedData = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    // Draw canvas with test pattern
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      canvas.width = 640;
      canvas.height = 480;
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(0, 0, 640, 480);
      
      // Draw simulated student silhouettes
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(200, 220, 60, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(160, 290, 80, 100);

      ctx.fillStyle = '#34d399';
      ctx.beginPath();
      ctx.arc(440, 230, 65, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(395, 305, 90, 100);

      ctx.fillStyle = '#f8fafc';
      ctx.font = '16px monospace';
      ctx.fillText('EduSense AI - Multi-Participant Simulation Test', 130, 60);

      const frameBase64 = canvas.toDataURL('image/jpeg', 0.65);
      wsRef.current.send(JSON.stringify({
        frame: frameBase64,
        audio: latestAudioChunkRef.current
      }));
      latestAudioChunkRef.current = null;
    }
  };

  const handleAudioChunk = (base64Chunk) => {
    latestAudioChunkRef.current = base64Chunk;
  };

  const handleVideoFileUpload = (e) => {
    const file = e.target.files[0];
    if (file && videoRef.current) {
      stopMediaStream();
      setVideoMode('file');
      videoRef.current.srcObject = null;
      videoRef.current.src = URL.createObjectURL(file);
      videoRef.current.loop = true;
      videoRef.current.play().catch(() => {});
    }
  };

  const formatTimer = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const presentCount = activeTracks.filter(t => t.attendance_status === 'Present').length;

  return (
    <div className="flex flex-col gap-6">
      {/* Top Session Control Bar */}
      <div className="glass-panel p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Active Session</span>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {currentSession ? currentSession.title : 'No Session Active'}
              {currentSession?.status === 'active' && (
                <span className="flex h-2.5 w-2.5 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
              )}
            </h2>
          </div>

          {currentSession?.status === 'active' && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 font-mono text-cyan-400 text-sm">
              <Clock className="w-4 h-4 text-slate-400" />
              <span>{formatTimer(sessionTime)}</span>
            </div>
          )}
        </div>

        {/* Video Mode Selector */}
        <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => { setVideoMode('webcam'); if (isCapturing) startWebcam(); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition ${
              videoMode === 'webcam' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            Webcam
          </button>
          
          <label className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium cursor-pointer transition ${
            videoMode === 'file' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
          }`}>
            <Upload className="w-3.5 h-3.5" />
            Upload Video
            <input type="file" accept="video/*" onChange={handleVideoFileUpload} className="hidden" />
          </label>

          <button
            onClick={() => { setVideoMode('simulation'); stopMediaStream(); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition ${
              videoMode === 'simulation' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Simulation Mode
          </button>
        </div>

        {/* Session Action Buttons */}
        <div className="flex items-center gap-3">
          {!currentSession || currentSession.status !== 'active' ? (
            <button
              onClick={onStartSession}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-lg shadow-emerald-950/40 transition active:scale-95"
            >
              <Play className="w-4 h-4 fill-white" />
              Start Session
            </button>
          ) : (
            <button
              onClick={onEndSession}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 font-semibold text-white shadow-lg shadow-rose-950/40 transition active:scale-95"
            >
              <Square className="w-4 h-4 fill-white" />
              End Session
            </button>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-amber-950/50 border border-amber-500/30 rounded-lg text-amber-200 text-xs flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="underline ml-4">Dismiss</button>
        </div>
      )}

      {/* Primary 4 Metric HUD Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Verified Attendance */}
        <div className="glass-card p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase tracking-wider font-semibold">
            <span>Presence-Based Attendance</span>
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-cyan-400">{presentCount}</span>
            <span className="text-sm text-slate-400">/ {activeTracks.length} Tracked</span>
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Threshold: 60s continuous / accumulated</span>
          </div>
        </div>

        {/* Metric 2: Engagement Score */}
        <div className="glass-card p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase tracking-wider font-semibold">
            <span>Engagement Index</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold ${
              engagementData.overall_score >= 70 ? 'text-emerald-400' :
              engagementData.overall_score >= 40 ? 'text-amber-400' : 'text-rose-400'
            }`}>
              {engagementData.overall_score.toFixed(1)}%
            </span>
            <span className="text-xs px-2 py-0.5 rounded font-semibold bg-slate-800 text-slate-300">
              {engagementData.level}
            </span>
          </div>
          <div className="text-xs text-slate-400">
            Fused vision + vocal interaction
          </div>
        </div>

        {/* Metric 3: Acoustic Noise Level */}
        <div className="glass-card p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase tracking-wider font-semibold">
            <span>Room Acoustic Decibels</span>
            <span className="text-xs text-purple-400 font-mono">16 kHz</span>
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-purple-400">
              {audioMetrics.noise_db.toFixed(1)}
            </span>
            <span className="text-sm text-slate-400">dB</span>
          </div>
          <div className="text-xs text-slate-400">
            VAD Ratio: {(audioMetrics.speech_ratio * 100).toFixed(0)}%
          </div>
        </div>

        {/* Metric 4: Sound Environment State */}
        <div className="glass-card p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase tracking-wider font-semibold">
            <span>Acoustic Pattern</span>
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
          </div>
          <div className="my-2">
            <span className={`text-xl font-bold uppercase ${
              audioMetrics.state === 'active speech' ? 'text-emerald-400' :
              audioMetrics.state === 'background noise' ? 'text-amber-400' : 'text-slate-300'
            }`}>
              {audioMetrics.state}
            </span>
          </div>
          <div className="text-xs text-slate-400">
            {audioMetrics.state === 'active speech' ? 'Active classroom dialogue' :
             audioMetrics.state === 'background noise' ? 'Ambient chatter / rustle' : 'Attentive silence / listening'}
          </div>
        </div>
      </div>

      {/* Main Dual View: Camera/Detection Stream + Pedagogical Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Video with Overlays */}
        <div className="lg:col-span-2 glass-panel p-4 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-white">Live Multimodal Stream</span>
              {isCapturing && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>
                  LIVE ON-DEVICE PROCESSING
                </span>
              )}
            </div>
            <span className="text-xs text-slate-400">OpenCV Haar + DeepSORT Tracking</span>
          </div>

          <div className="relative aspect-video bg-black rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center">
            {/* Hidden native video and processing canvas */}
            <video ref={videoRef} className="hidden" playsInline muted autoPlay />
            <canvas ref={canvasRef} className="hidden" />

            {/* Display rendered overlay with bounding boxes */}
            {liveOverlay ? (
              <img src={liveOverlay} alt="Live Classroom Stream" className="w-full h-full object-contain" />
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500 gap-3 p-8 text-center">
                <Video className="w-12 h-12 text-slate-600 stroke-1" />
                <div className="text-sm">
                  {currentSession?.status === 'active'
                    ? 'Initializing video pipeline and tracking detector...'
                    : 'Start a session to activate the live webcam or pre-recorded stream.'}
                </div>
              </div>
            )}

            {/* Privacy indicator overlay (NFR-1) */}
            <div className="absolute bottom-2 left-2 px-2.5 py-1 bg-black/70 backdrop-blur rounded text-[10px] text-slate-300 flex items-center gap-1.5 border border-white/10">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              <span>Privacy Shield: Processed locally, zero raw video stored</span>
            </div>
          </div>

          {/* Audio capture component directly below stream */}
          <AudioCapture
            isActive={isCapturing}
            onAudioChunk={handleAudioChunk}
            audioMetrics={audioMetrics}
          />
        </div>

        {/* Right 1 Col: AI Suggestions & Agent Insights */}
        <div className="flex flex-col gap-4">
          {/* Pedagogical Insights Box */}
          <div className="glass-panel p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span className="font-semibold text-sm text-white">AI Teaching Co-Pilot</span>
              </div>
              <span className="text-[11px] text-cyan-400 font-mono bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {liveInsight.source}
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed italic bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              "{liveInsight.insight}"
            </p>
          </div>

          {/* Explainability Scoring Breakdown */}
          <div className="glass-card p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
              <span>Scoring Contribution (Explainable AI)</span>
              <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="flex flex-col gap-2 pt-1 text-xs">
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Visual Attention (45%)</span>
                  <span className="font-mono text-cyan-300">{engagementData.attention_component.toFixed(1)}</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div className="bg-cyan-400 h-1.5 rounded-full" style={{ width: `${engagementData.attention_component}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Movement Stability (20%)</span>
                  <span className="font-mono text-emerald-300">{engagementData.movement_component.toFixed(1)}</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div className="bg-emerald-400 h-1.5 rounded-full" style={{ width: `${engagementData.movement_component}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Vocal Interaction (35%)</span>
                  <span className="font-mono text-purple-300">{engagementData.audio_component.toFixed(1)}</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div className="bg-purple-400 h-1.5 rounded-full" style={{ width: `${engagementData.audio_component}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Real-time Advisory Suggestions Stream */}
          <div className="glass-panel p-4 flex flex-col gap-3 flex-1">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span className="font-semibold text-sm text-white">Live Recommendations</span>
              </div>
              <span className="text-xs text-slate-400">{suggestions.length} triggered</span>
            </div>

            <div className="flex flex-col gap-2.5 max-h-[340px] overflow-y-auto pr-1">
              {suggestions.length === 0 ? (
                <div className="text-xs text-slate-500 italic py-6 text-center">
                  Classroom dynamics stable. Recommendations will trigger automatically upon attention drops or acoustic anomalies.
                </div>
              ) : (
                suggestions.map((s, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border text-xs flex flex-col gap-1 transition ${
                      s.type === 'alert'
                        ? 'bg-rose-950/40 border-rose-800/60 text-rose-200'
                        : s.type === 'warning'
                        ? 'bg-amber-950/40 border-amber-800/60 text-amber-200'
                        : 'bg-cyan-950/40 border-cyan-800/60 text-cyan-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold flex items-center gap-1.5">
                        {s.type === 'alert' && <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />}
                        {s.type === 'warning' && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
                        {s.type === 'info' && <Info className="w-3.5 h-3.5 text-cyan-400" />}
                        {s.title || s.rule_id}
                      </span>
                      <span className="text-[10px] opacity-60 font-mono">
                        {s.timestamp ? s.timestamp.substring(11, 19) : ''}
                      </span>
                    </div>
                    <p className="text-[11px] leading-relaxed opacity-90">{s.message}</p>
                    {s.explanation && (
                      <span className="text-[10px] opacity-70 italic mt-0.5 border-t border-white/10 pt-1">
                        Trigger: {s.explanation}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
