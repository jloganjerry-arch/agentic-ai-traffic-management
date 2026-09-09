import React from 'react';

export function AgentCard({ id, name, alias, status, last_ping, latency_ms, icon: Icon, description, task, stage, decision_id }) {
  const isActive = (status || 'ACTIVE').toUpperCase() === 'ACTIVE';

  return (
    <div className={`glass-panel-interactive p-3.5 rounded-2xl border transition-all duration-200 space-y-2.5 relative overflow-hidden group ${
      isActive ? 'border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.08)]' : 'border-slate-800/80'
    }`}>
      {/* Top subtle highlight */}
      <div className={`absolute top-0 left-3 right-3 h-[1px] bg-gradient-to-r from-transparent via-purple-400/25 to-transparent pointer-events-none ${isActive ? 'opacity-100' : 'opacity-30'}`} />

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {Icon && (
            <div className={`p-1.5 rounded-lg border transition-colors ${
              isActive 
                ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' 
                : 'bg-slate-900 border-slate-800 text-slate-400'
            }`}>
              <Icon className="w-4 h-4 shrink-0" />
            </div>
          )}
          <div>
            <h3 className="font-bold text-xs text-slate-100 leading-tight font-mono">{name}</h3>
            {alias && <span className="text-[10px] font-mono text-cyan-400 font-semibold">({alias})</span>}
          </div>
        </div>
        <span className={`text-[9px] px-2 py-0.5 rounded font-mono font-bold border shrink-0 ${
          isActive 
            ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700/80 shadow-[0_0_8px_rgba(16,185,129,0.25)]' 
            : 'bg-slate-900 text-slate-400 border-slate-700'
        }`}>
          {status || 'ACTIVE'}
        </span>
      </div>

      <p className="text-[11px] text-slate-300 leading-relaxed line-clamp-2" title={task || description}>
        {task || description}
      </p>

      {decision_id && (
        <div className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/60 truncate">
          DECISION: {decision_id}
        </div>
      )}

      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-800/80 font-mono">
        <span className="text-slate-400">Stage: <strong className="text-slate-200">{stage || 'Monitoring'}</strong></span>
        <span className="bg-slate-900/90 px-1.5 py-0.5 rounded border border-slate-800 text-cyan-300 font-semibold">{latency_ms ?? 5}ms</span>
      </div>
    </div>
  );
}
