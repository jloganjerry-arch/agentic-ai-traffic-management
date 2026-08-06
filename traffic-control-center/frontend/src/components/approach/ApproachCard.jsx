import React from 'react';

export function ApproachCard({ approach, vehicle_count, avg_speed, queue_len, density, status }) {
  return (
    <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm text-slate-100">{approach}</h3>
        <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
          status === 'Optimal' ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800' : 'bg-amber-950/60 text-amber-400 border border-amber-800'
        }`}>
          {status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
          <span className="text-slate-400 block text-[10px]">Vehicles</span>
          <span className="font-mono text-slate-200 font-semibold">{vehicle_count}</span>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
          <span className="text-slate-400 block text-[10px]">Speed</span>
          <span className="font-mono text-cyan-400 font-semibold">{avg_speed} km/h</span>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
          <span className="text-slate-400 block text-[10px]">Queue</span>
          <span className="font-mono text-amber-400 font-semibold">{queue_len} m</span>
        </div>
        <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
          <span className="text-slate-400 block text-[10px]">Density</span>
          <span className="font-mono text-slate-200 font-semibold">{density} v/km</span>
        </div>
      </div>
    </div>
  );
}
