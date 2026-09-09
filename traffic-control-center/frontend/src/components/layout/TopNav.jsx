import React, { useState, useEffect } from 'react';
import { useLiveClock } from '../../hooks/useLiveClock';
import { useConnectionStore } from '../../store/connectionStore';
import { useUIStore } from '../../store/uiStore';
import { wsSignals } from '../../api/websocket';
import {
  Activity,
  Radio,
  Cpu,
  Server,
  MapPin,
  ChevronDown,
  BookOpen,
  Sparkles,
  Zap
} from 'lucide-react';
import { SystemGuideModal } from './SystemGuideModal';

export function TopNav() {
  const clock = useLiveClock();
  const { sumoStatus, fastApiStatus, mqttStatus } = useConnectionStore();
  const { activeWorkspace, setActiveWorkspace, liveTicker, setLiveTicker } = useUIStore();
  const [selectedJunction, setSelectedJunction] = useState('J1-HUB');
  const [isGuideOpen, setIsGuideOpen] = useState(false);

  // Subscribe to live WebSocket signal and adaptive decision events for the top ticker
  useEffect(() => {
    const unsubscribe = wsSignals.subscribe((data) => {
      if (data.event === 'signal_state_sync' || data.event === 'SIGNAL_UPDATE') {
        const activeSignal = data.signals?.find((s) => s.state === 'GREEN') || data.signals?.[0];
        if (activeSignal && activeSignal.adaptive_reason) {
          const reasonText = activeSignal.adaptive_reason;
          const actionText = activeSignal.adaptive_action || 'OPTIMIZED';
          const dir = activeSignal.direction || 'Corridor';
          const rem = activeSignal.remaining_time ?? activeSignal.timer_remaining ?? '';
          setLiveTicker(
            `[ADAPTIVE AI] ${dir} Phase: ${actionText} (${rem}s remaining) — ${reasonText}`
          );
        } else if (data.adaptive_status) {
          setLiveTicker(
            `[SUPERVISOR] Autonomous dynamic optimization nominal (${data.adaptive_status})`
          );
        }
      }
    });

    return () => unsubscribe();
  }, [setLiveTicker]);

  const workspaceLabels = {
    tactical: { name: 'Tactical Cockpit', color: 'text-cyan-400 border-cyan-500/40 bg-cyan-950/40' },
    agents: { name: 'AI Agent Brain', color: 'text-purple-400 border-purple-500/40 bg-purple-950/40' },
    analytics: { name: 'Corridor Analytics', color: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/40' },
    hardware: { name: 'Edge & Hardware', color: 'text-blue-400 border-blue-500/40 bg-blue-950/40' },
    unified: { name: 'Unified Panoramic', color: 'text-amber-400 border-amber-500/40 bg-amber-950/40' },
  };

  const currentWs = workspaceLabels[activeWorkspace] || workspaceLabels.tactical;

  return (
    <header className="h-16 border-b border-slate-800 bg-[#0F172A]/95 backdrop-blur-md px-4 md:px-6 flex items-center justify-between sticky top-0 z-50 select-none">
      {/* Brand & Workspace Indicator */}
      <div className="flex items-center space-x-4 md:space-x-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.2)]">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-semibold text-slate-100 text-sm md:text-base tracking-wide">
                Traffic Control Center
              </h1>
              <span
                className={`hidden sm:inline-flex text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${currentWs.color}`}
              >
                {currentWs.name}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Autonomous Multi-Agent Intersection Management
            </p>
          </div>
        </div>

        {/* Junction Selector Dropdown */}
        <div className="hidden xl:flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
          <MapPin className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">Junction:</span>
          <div className="relative">
            <select
              value={selectedJunction}
              onChange={(e) => setSelectedJunction(e.target.value)}
              className="bg-transparent text-slate-100 font-mono font-semibold focus:outline-none cursor-pointer pr-4 appearance-none"
            >
              <option value="J1-HUB" className="bg-slate-900 text-slate-100">J1 - Central Hub (Active)</option>
              <option value="J2-NORTH" className="bg-slate-900 text-slate-100">J2 - North Corridor (Standby)</option>
              <option value="J3-EAST" className="bg-slate-900 text-slate-100">J3 - East Expressway (Standby)</option>
            </select>
            <ChevronDown className="w-3 h-3 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Cyber Incident Live Ticker (Center Bar) */}
      <div className="hidden lg:flex flex-1 max-w-xl mx-4 items-center space-x-2 bg-slate-950/80 border border-slate-800/80 rounded-lg px-3 py-1.5 overflow-hidden">
        <div className="flex items-center space-x-1.5 text-cyan-400 shrink-0">
          <Zap className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-cyan-300">
            INCIDENT TICKER:
          </span>
        </div>
        <div className="text-[11px] text-slate-300 font-mono truncate animate-fade-in" title={liveTicker}>
          {liveTicker}
        </div>
      </div>

      {/* Status Indicators & Operators Controls */}
      <div className="flex items-center space-x-3 md:space-x-4">
        {/* Status Indicators */}
        <div className="hidden 2xl:flex items-center space-x-2.5 text-xs">
          <div className="flex items-center space-x-1.5 bg-slate-900/60 px-3 py-1.5 rounded-full border border-slate-800">
            <Server className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">Provider:</span>
            <span className="text-emerald-400 font-medium font-mono">{sumoStatus}</span>
          </div>

          <div className="flex items-center space-x-1.5 bg-slate-900/60 px-3 py-1.5 rounded-full border border-slate-800">
            <Radio className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">FastAPI:</span>
            <span className="text-emerald-400 font-medium font-mono">{fastApiStatus}</span>
          </div>

          <div className="flex items-center space-x-1.5 bg-slate-900/60 px-3 py-1.5 rounded-full border border-slate-800">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">MQTT:</span>
            <span className="text-emerald-400 font-medium font-mono">{mqttStatus}</span>
          </div>
        </div>

        {/* System Operator Guide Button */}
        <button
          onClick={() => setIsGuideOpen(true)}
          className="flex items-center space-x-1.5 bg-gradient-to-r from-cyan-950/80 to-blue-950/80 hover:from-cyan-900/90 hover:to-blue-900/90 text-cyan-300 hover:text-white px-3 py-1.5 rounded-lg border border-cyan-500/40 hover:border-cyan-400 text-xs font-semibold shadow-[0_0_12px_rgba(6,182,212,0.15)] transition-all cursor-pointer"
          title="Open Master System & Operational Guide"
        >
          <BookOpen className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="hidden md:inline">System Guide</span>
          <span className="md:hidden">Guide</span>
        </button>

        {/* Live Clock */}
        <div className="font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-500/30 px-3 py-1.5 rounded-md text-xs sm:text-sm font-semibold tracking-wider">
          {clock}
        </div>
      </div>

      {/* Interactive System Guide Modal */}
      <SystemGuideModal isOpen={isGuideOpen} onClose={() => setIsGuideOpen(false)} />
    </header>
  );
}
