import React from 'react';
import { TopNav } from './TopNav';
import { useHeartbeatWebSocket } from '../../hooks/useHeartbeatWebSocket';

export function DashboardShell({ children }) {
  // Subscribe to heartbeat WebSocket channel to maintain live top nav badges
  useHeartbeatWebSocket();

  return (
    <div className="min-h-screen bg-[#0B1221] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      <TopNav />
      <main className="flex-1 p-4 md:p-6 space-y-6 max-w-[1800px] w-full mx-auto">
        {children}
      </main>
    </div>
  );
}
