import React from 'react';

export function OverviewCard({ label, value, unit, icon: Icon, trend, confidence, statusColor = 'text-cyan-400' }) {
  return (
    <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between relative overflow-hidden">
      <div>
        <div className="flex items-center space-x-2 mb-1">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">{label}</p>
          {confidence && (
            <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${
              confidence === 'exact'
                ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/80'
                : 'bg-amber-950/80 text-amber-400 border border-amber-800/80'
            }`}>
              {confidence}
            </span>
          )}
        </div>
        <div className="flex items-baseline space-x-1">
          <span className={`text-2xl font-bold font-mono ${statusColor}`}>{value}</span>
          {unit && <span className="text-xs text-slate-500 font-normal">{unit}</span>}
        </div>
        {trend && <p className="text-[10px] text-slate-400 mt-1">{trend}</p>}
      </div>
      {Icon && (
        <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-slate-300">
          <Icon className="w-5 h-5" />
        </div>
      )}
    </div>
  );
}
