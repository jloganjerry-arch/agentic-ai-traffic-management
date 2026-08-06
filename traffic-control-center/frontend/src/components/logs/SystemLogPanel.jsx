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
        <div className="flex items-center space-x-2 text-[10px] font-mono bg-cyan-950/60 text-cyan-400 px-2 py-0.5 rounded border border-cyan-800">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
          <span>WS Connected</span>
        </div>
      }
    >
      <div className="h-[200px] overflow-y-auto bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs space-y-2">
        {logs.map((log, idx) => (
          <div key={idx} className="flex items-start space-x-2 text-[11px]">
            <span className="text-slate-500 font-medium">[{log.timestamp}]</span>
            <span className={`px-1 rounded text-[9px] font-bold ${
              log.level === 'INFO' ? 'bg-cyan-950 text-cyan-400' : 'bg-red-950 text-red-400'
            }`}>
              {log.level}
            </span>
            <span className="text-slate-400 font-semibold">&lt;{log.source}&gt;</span>
            <span className="text-slate-200">{log.message}</span>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
