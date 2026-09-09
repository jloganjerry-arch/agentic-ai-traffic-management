import React from 'react';

export function ApproachCard({ approach, vehicle_count, avg_speed, queue_len, density, status }) {
  const isOptimal = (status || 'Optimal') === 'Optimal';

  return (
    <div className="glass-panel-interactive p-4 rounded-2xl border border-slate-800/90 space-y-3.5 relative overflow-hidden group">
      {/* Specular Top Rim Highlight */}
      <div className="absolute top-0 left-4 right-4 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/25 to-transparent pointer-events-none" />

      <div className="flex items-center justify-between">
        <h3 className="font-bold text-sm text-slate-100 font-mono tracking-wide">{approach}</h3>
        <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-mono font-bold border ${
          isOptimal 
            ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700/80 shadow-[0_0_8px_rgba(16,185,129,0.2)]' 
            : 'bg-amber-950/80 text-amber-300 border-amber-700/80 shadow-[0_0_8px_rgba(245,158,11,0.2)]'
        }`}>
          ● {status || 'Optimal'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase">Vehicles</span>
          <span className="font-mono text-slate-100 font-bold text-sm">{vehicle_count}</span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase">Speed</span>
          <span className="font-mono text-cyan-300 font-bold text-sm">{avg_speed} <span className="text-[10px] text-slate-400 font-normal">km/h</span></span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase">Queue</span>
          <span className="font-mono text-amber-300 font-bold text-sm">{queue_len} <span className="text-[10px] text-slate-400 font-normal">m</span></span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase">Density</span>
          <span className="font-mono text-slate-200 font-bold text-sm">{density} <span className="text-[10px] text-slate-400 font-normal">v/km</span></span>
        </div>
      </div>
    </div>
  );
}
