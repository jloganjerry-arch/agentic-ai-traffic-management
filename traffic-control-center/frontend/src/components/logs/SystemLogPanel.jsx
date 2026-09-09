import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useLogsWebSocket } from '../../hooks/useLogsWebSocket';
import { Terminal } from 'lucide-react';

export function SystemLogPanel() {
  const initialLogs = [
    { timestamp: new Date().toLocaleTimeString(), level: 'INFO', source: 'SupervisorAgent', message: 'System initialization complete. Pipeline ready.' }
  ];
  
  // Real-time WebSocket log stream (not polled)
  const logs = useLogsWebSocket(initialLogs);

  return (
    <SectionCard
      title="System & Agent Event Logs (Live Stream)"
      icon={Terminal}
      action={
        <div className="flex items-center space-x-2 text-[10px] font-mono bg-cyan-950/70 text-cyan-300 px-3 py-1 rounded-lg border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
          <span>WS STREAM NOMINAL</span>
        </div>
      }
    >
      <div className="h-[220px] overflow-y-auto terminal-screen p-3.5 rounded-xl border border-slate-800/90 font-mono text-xs space-y-2 scrollbar-thin">
        {logs.map((log, idx) => (
          <div key={idx} className="flex items-start space-x-2.5 text-[11px] leading-relaxed transition-opacity">
            <span className="text-slate-500 font-medium shrink-0">[{log.timestamp}]</span>
            <span className={`px-1.5 py-0.2 rounded text-[9px] font-black shrink-0 ${
              log.level === 'INFO'
                ? 'bg-cyan-950/90 text-cyan-400 border border-cyan-800/60'
                : (log.level === 'WARN'
                    ? 'bg-amber-950/90 text-amber-400 border border-amber-800/60'
                    : 'bg-rose-950/90 text-rose-400 border border-rose-800/60')
            }`}>
              {log.level}
            </span>
            <span className="text-purple-300 font-semibold shrink-0">&lt;{log.source}&gt;</span>
            <span className="text-slate-200 break-all">{log.message}</span>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
