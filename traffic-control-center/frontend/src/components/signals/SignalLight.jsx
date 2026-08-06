import React from 'react';

export function SignalLight({ signal_id, direction, state, timer_remaining, mode }) {
  return (
    <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
      <div>
        <div className="flex items-center space-x-2">
          <span className="font-mono text-xs font-bold text-slate-300">{signal_id}</span>
          <span className="text-xs text-slate-400">({direction})</span>
        </div>
        <p className="text-[10px] text-slate-500 mt-1">Mode: {mode}</p>
      </div>

      <div className="flex items-center space-x-4">
        {/* Lights Housing */}
        <div className="bg-slate-950 px-2 py-1 rounded-full border border-slate-800 flex items-center space-x-1.5">
          <div className={`w-3.5 h-3.5 rounded-full ${state === 'RED' ? 'bg-red-500 shadow-[0_0_8px_#ef4444]' : 'bg-red-950 opacity-40'}`}></div>
          <div className={`w-3.5 h-3.5 rounded-full ${state === 'YELLOW' ? 'bg-amber-400 shadow-[0_0_8px_#f59e0b]' : 'bg-amber-950 opacity-40'}`}></div>
          <div className={`w-3.5 h-3.5 rounded-full ${state === 'GREEN' ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : 'bg-emerald-950 opacity-40'}`}></div>
        </div>

        {/* Countdown */}
        <div className="font-mono text-lg font-bold text-slate-100 min-w-[32px] text-right">
          {timer_remaining}s
        </div>
      </div>
    </div>
  );
}
