import React, { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Volume2, AlertCircle } from 'lucide-react';

export default function AudioCapture({ isActive, onAudioChunk, audioMetrics }) {
  const [hasPermission, setHasPermission] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [meterLevel, setMeterLevel] = useState(0);

  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);

  useEffect(() => {
    if (!isActive) {
      stopAudioCapture();
      return;
    }

    startAudioCapture();

    return () => {
      stopAudioCapture();
    };
  }, [isActive]);

  const startAudioCapture = async () => {
    try {
      setErrorMsg(null);
      // NFR-1: Explicit browser microphone permission prompt
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: false
        }
      });
      streamRef.current = stream;
      setHasPermission(true);

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      // Process chunks via ScriptProcessor (or AudioWorklet)
      const processor = audioCtx.createScriptProcessor(2048, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (!isActive) return;
        const inputData = e.inputBuffer.getChannelData(0);

        // Calculate instantaneous RMS for UI meter
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);
        setMeterLevel(Math.min(100, Math.round(rms * 400)));

        // Convert float32 to int16 PCM byte buffer for transmission
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Convert to base64 string
        const bytes = new Uint8Array(pcm16.buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        const base64Audio = window.btoa(binary);

        if (onAudioChunk) {
          onAudioChunk(base64Audio);
        }
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);
    } catch (err) {
      console.warn("Audio capture error:", err);
      setErrorMsg("Microphone access unavailable or denied. Fallback audio simulation enabled.");
      setHasPermission(false);
    }
  };

  const stopAudioCapture = () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setMeterLevel(0);
    setHasPermission(false);
  };

  return (
    <div className="glass-card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isActive && hasPermission ? (
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 rec-indicator"></span>
              <Mic className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Audio Capture Active</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <MicOff className="w-4 h-4 text-slate-500" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Microphone Standby</span>
            </div>
          )}
        </div>
        <div className="text-xs text-slate-400">16 kHz Mono Normalized</div>
      </div>

      {/* Real-time Level Meter */}
      <div className="flex items-center gap-3">
        <Volume2 className="w-4 h-4 text-slate-400 shrink-0" />
        <div className="flex-1 bg-slate-800 rounded-full h-2.5 overflow-hidden border border-slate-700">
          <div
            className={`h-full transition-all duration-75 ${
              meterLevel > 70 ? 'bg-amber-400' : 'bg-cyan-400'
            }`}
            style={{ width: `${meterLevel}%` }}
          ></div>
        </div>
        <span className="text-xs font-mono text-slate-300 w-12 text-right">
          {audioMetrics ? `${audioMetrics.noise_db} dB` : '-50.0 dB'}
        </span>
      </div>

      {/* Acoustic State Badge */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-800 text-xs">
        <span className="text-slate-400">Acoustic State:</span>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          audioMetrics?.state === 'active speech'
            ? 'bg-purple-900/60 text-purple-300 border border-purple-500/30'
            : audioMetrics?.state === 'background noise'
            ? 'bg-amber-900/60 text-amber-300 border border-amber-500/30'
            : 'bg-slate-800 text-slate-400'
        }`}>
          {audioMetrics?.state ? audioMetrics.state.toUpperCase() : 'SILENCE'}
        </span>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-950/40 p-2 rounded border border-amber-800/40">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}
