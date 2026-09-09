import React from 'react';
import { TopNav } from './TopNav';
import { SidebarCommandRail } from './SidebarCommandRail';
import { useHeartbeatWebSocket } from '../../hooks/useHeartbeatWebSocket';

export function DashboardShell({ children }) {
  // Subscribe to heartbeat WebSocket channel to maintain live top nav badges
  useHeartbeatWebSocket();

  return (
    <div className="h-screen bg-[#0B1221] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200 overflow-hidden">
      <TopNav />
      <div className="flex flex-1 h-[calc(100vh-4rem)] overflow-hidden">
        <SidebarCommandRail />
        <main className="flex-1 h-full overflow-y-auto p-3 sm:p-5 space-y-6 max-w-[1850px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
