import React from 'react';

export function AgentCard({ id, name, status, last_ping, latency_ms, icon: Icon, description, task, stage, decision_id }) {
  return (
    <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          {Icon && <Icon className="w-5 h-5 text-cyan-400" />}
          <h3 className="font-semibold text-sm text-slate-100">{name}</h3>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 font-mono">
          {status || 'ACTIVE'}
        </span>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed truncate" title={task || description}>{task || description}</p>

      {decision_id && (
        <div className="text-[10px] font-mono text-cyan-400/90 truncate">
          ID: {decision_id}
        </div>
      )}

      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/60 font-mono">
        <span>Stage: {stage || 'Monitoring'}</span>
        <span>Latency: {latency_ms ?? 5}ms</span>
      </div>
    </div>
  );
}
