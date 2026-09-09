import React from 'react';

export function OverviewCard({ label, value, unit, icon: Icon, trend, confidence, statusColor = 'text-cyan-400' }) {
  return (
    <div className="glass-panel-interactive p-4 rounded-2xl border border-slate-800/90 flex items-center justify-between relative overflow-hidden group cursor-default">
      {/* Specular Top Rim Highlight */}
      <div className="absolute top-0 left-4 right-4 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/25 to-transparent pointer-events-none" />

      <div>
        <div className="flex items-center space-x-2 mb-1.5">
          <p className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider font-mono">{label}</p>
          {confidence && (
            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold border ${
              confidence === 'exact'
                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800/80'
                : 'bg-amber-950/80 text-amber-400 border-amber-800/80'
            }`}>
              {confidence}
            </span>
          )}
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className={`text-2xl lg:text-3xl font-black font-mono tracking-tight drop-shadow-sm transition-colors duration-200 ${statusColor}`}>{value}</span>
          {unit && <span className="text-xs text-slate-400 font-mono font-medium">{unit}</span>}
        </div>
        {trend && <p className="text-[10px] text-slate-400 mt-1 font-sans">{trend}</p>}
      </div>

      {Icon && (
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-700/60 text-cyan-400 group-hover:text-cyan-300 group-hover:border-cyan-500/40 group-hover:bg-cyan-950/30 group-hover:shadow-[0_0_15px_rgba(6,182,212,0.25)] transition-all duration-300 shrink-0">
          <Icon className="w-5 h-5" />
        </div>
      )}
    </div>
  );
}
