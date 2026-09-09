import React from 'react';
import { Siren, Zap } from 'lucide-react';

export function SignalLight({ signal_id, direction, state, timer_remaining, mode }) {
  const isEmergencyMode = mode === 'EMERGENCY_GREEN_CORRIDOR' || mode === 'Emergency Green Corridor';
  const isAdaptiveMode = !isEmergencyMode && (mode === 'AI-Adaptive' || mode === 'AI-Optimized' || mode === 'Autonomous Adaptive' || mode?.includes('Adaptive'));

  const normalizedState = (state || 'RED').toUpperCase();
  const timerDisplay = timer_remaining > 0 ? `${timer_remaining}s` : (normalizedState === 'YELLOW' ? 'CLEAR' : normalizedState);

  return (
    <div className={`glass-panel p-4 rounded-2xl border flex items-center justify-between transition-all duration-300 ${
      isEmergencyMode
        ? 'border-rose-500/60 bg-rose-950/30 shadow-[0_0_20px_rgba(244,63,94,0.15)]'
        : (normalizedState === 'YELLOW' 
            ? 'border-amber-500/50 bg-amber-950/20 shadow-[0_0_20px_rgba(245,158,11,0.12)]' 
            : (normalizedState === 'GREEN'
                ? 'border-emerald-500/40 bg-emerald-950/15 shadow-[0_0_20px_rgba(16,185,129,0.1)]'
                : 'border-slate-800/90'))
    }`}>
      <div>
        <div className="flex items-center space-x-2">
          <span className="font-mono text-xs font-bold text-slate-200">{signal_id}</span>
          <span className="text-xs text-slate-400 font-semibold font-mono">({direction})</span>
        </div>

        <div className="flex items-center space-x-1.5 mt-1.5">
          {isEmergencyMode ? (
            <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-bold text-rose-400 bg-rose-950/90 px-2.5 py-0.5 rounded-full border border-rose-600 animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.4)]">
              <Siren className="w-3 h-3" />
              <span>EMERGENCY CORRIDOR</span>
            </span>
          ) : normalizedState === 'YELLOW' ? (
            <span className="inline-flex items-center space-x-1.5 text-[10px] font-mono font-bold text-amber-300 bg-amber-950/80 px-2.5 py-0.5 rounded-full border border-amber-500/70 shadow-[0_0_10px_rgba(245,158,11,0.3)]">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
              <span>YELLOW CLEARANCE</span>
            </span>
          ) : isAdaptiveMode ? (
            <span className="inline-flex items-center space-x-1 text-[10px] font-mono text-cyan-300 bg-cyan-950/70 px-2.5 py-0.5 rounded-full border border-cyan-700">
              <Zap className="w-3 h-3 text-cyan-400" />
              <span>ADAPTIVE TIMING</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1.5 text-[10px] font-mono text-slate-400 bg-slate-900/90 px-2.5 py-0.5 rounded-full border border-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
              <span>FIXED SCHEDULE</span>
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Lights Optical LED Housing */}
        <div className="bg-black/90 p-2 rounded-2xl border border-slate-800 flex items-center space-x-2.5 shadow-inner">
          <div className={`w-4 h-4 rounded-full transition-all duration-300 ${
            normalizedState === 'RED' ? 'optical-led-red' : 'bg-red-950/40 opacity-25'
          }`} />
          <div className={`w-4 h-4 rounded-full transition-all duration-300 ${
            normalizedState === 'YELLOW' ? 'optical-led-yellow' : 'bg-amber-950/40 opacity-25'
          }`} />
          <div className={`w-4 h-4 rounded-full transition-all duration-300 ${
            normalizedState === 'GREEN' ? 'optical-led-green' : 'bg-emerald-950/40 opacity-25'
          }`} />
        </div>

        {/* Countdown / State Badge */}
        <div className={`font-mono text-xs font-black min-w-[48px] text-center px-2.5 py-1.5 rounded-xl border transition-all duration-200 ${
          normalizedState === 'YELLOW'
            ? 'bg-amber-950/90 text-amber-300 border-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.4)] animate-pulse'
            : (normalizedState === 'GREEN'
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/80 shadow-[0_0_12px_rgba(16,185,129,0.35)]'
                : 'bg-rose-950/40 text-rose-300/80 border-rose-900/60')
        }`}>
          {timerDisplay}
        </div>
      </div>
    </div>
  );
}
