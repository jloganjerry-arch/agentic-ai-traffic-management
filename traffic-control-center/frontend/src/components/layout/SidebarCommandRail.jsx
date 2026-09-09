import React from 'react';
import {
  Activity,
  Cpu,
  BarChart3,
  Layers,
  Terminal,
  Siren,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Sparkles,
  Zap,
  ShieldCheck
} from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useScenarioStore } from '../../store/scenarioStore';
import { useConnectionStore } from '../../store/connectionStore';
import { useEmergencyControl } from '../../api/queries/useEmergencyControl';

export function SidebarCommandRail() {
  const {
    activeWorkspace,
    setActiveWorkspace,
    isSidebarCollapsed,
    toggleSidebar
  } = useUIStore();

  const { emergencyActive, emergencyRoute, emergencyVehicleType, setEmergencyDispatch } = useScenarioStore();
  const { sumoStatus, mqttStatus } = useConnectionStore();
  const { triggerEmergencyCorridor } = useEmergencyControl();

  const navigationItems = [
    {
      id: 'tactical',
      label: 'Tactical Cockpit',
      shortLabel: 'Tactical',
      description: 'SUMO 2D canvas, signal heads, scenarios & emergency override',
      icon: Activity,
      badge: 'LIVE',
      badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
    },
    {
      id: 'agents',
      label: 'AI Agent Brain',
      shortLabel: 'Agents',
      description: '5-Agent pipeline observability, supervisor decisions & safety audit',
      icon: Cpu,
      badge: '5 AGENTS',
      badgeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
    },
    {
      id: 'analytics',
      label: 'Corridor Analytics',
      shortLabel: 'Analytics',
      description: 'Approach heatmaps, congestion forecasts (+15m/+30m) & trends',
      icon: BarChart3,
      badge: '+60m AI',
      badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    },
    {
      id: 'hardware',
      label: 'Edge & Hardware',
      shortLabel: 'Hardware',
      description: 'ESP32 microcontrollers, MQTT latency, TraCI dataset & console',
      icon: Terminal,
      badge: 'ESP32',
      badgeColor: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    },
    {
      id: 'unified',
      label: 'Unified Panoramic',
      shortLabel: 'Unified',
      description: 'All 13 system panels arranged in full panoramic wall display',
      icon: Layers,
      badge: 'ALL-IN-1',
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    },
  ];

  const handleQuickEmergencyTrigger = (direction) => {
    const nextActive = !emergencyActive;
    setEmergencyDispatch('ambulance', direction, nextActive);
    triggerEmergencyCorridor.mutate({
      active: nextActive,
      direction: direction,
      vehicle_type: 'ambulance',
    });
  };

  return (
    <aside
      className={`relative z-40 flex flex-col shrink-0 h-full max-h-[calc(100vh-4rem)] border-r border-slate-800/80 bg-[#0B1221]/95 backdrop-blur-md transition-all duration-300 select-none overflow-hidden ${isSidebarCollapsed ? 'w-[76px]' : 'w-[268px]'
        }`}
    >
      {/* Sidebar Top Header: Brand & Collapse Toggle */}
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-slate-800/80 px-3.5">
        {!isSidebarCollapsed && (
          <div className="flex items-center space-x-2 overflow-hidden">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="truncate">
              <div className="text-xs font-bold tracking-wider text-slate-200 uppercase font-mono">
                Command Rail
              </div>
              <div className="text-[10px] text-slate-400">Next-Gen ATMC</div>
            </div>
          </div>
        )}

        <button
          onClick={toggleSidebar}
          type="button"
          className={`flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-400 transition-all hover:border-cyan-500/40 hover:bg-slate-800 hover:text-cyan-300 cursor-pointer ${isSidebarCollapsed ? 'mx-auto' : ''
            }`}
          title={isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isSidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Scrollable Menu Content (Emergency HUD + Navigation Workspaces) */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin flex flex-col">
        {/* EMERGENCY HUD (PROMINENT TOP POSITION - LARGER SIZE FOR RAPID FIRST-RESPONDER ACCESS) */}
        <div className="p-2.5 border-b border-slate-800/80 bg-slate-950/40 shrink-0">
          {!isSidebarCollapsed ? (
            <div className="bg-gradient-to-b from-rose-950/70 via-rose-950/30 to-slate-900/90 border-2 border-rose-500/50 rounded-2xl p-3 shadow-[0_0_20px_rgba(244,63,94,0.22)] space-y-2.5">
              {/* Header with larger icon and title */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`p-1.5 rounded-lg ${emergencyActive ? 'bg-rose-500 text-white animate-bounce' : 'bg-rose-500/20 text-rose-400'}`}>
                    <Siren className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="text-xs font-black tracking-wider uppercase font-mono text-rose-200">
                      EMERGENCY HUD
                    </div>
                    <div className="text-[9px] text-rose-300/70 font-sans">
                      Fast First-Responder Access
                    </div>
                  </div>
                </div>
                <span
                  className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-md border ${emergencyActive
                      ? 'bg-rose-600 text-white border-rose-400 animate-pulse shadow-[0_0_8px_#f43f5e]'
                      : 'bg-rose-950/80 text-rose-300 border-rose-800'
                    }`}
                >
                  {emergencyActive ? 'ACTIVE' : 'READY'}
                </span>
              </div>

              {/* Action Buttons with Larger Touch/Click Targets */}
              {emergencyActive ? (
                <div className="space-y-2 pt-1">
                  <div className="bg-rose-950/60 border border-rose-500/50 rounded-xl p-2.5 text-xs text-rose-100">
                    <div className="font-bold flex items-center space-x-1.5 font-mono text-rose-200">
                      <Zap className="h-4 w-4 text-rose-400 animate-pulse" />
                      <span>LOCKED: {emergencyRoute}</span>
                    </div>
                    <div className="text-slate-300 text-[10px] mt-1">
                      Priority Vehicle: <span className="font-bold text-white uppercase">{emergencyVehicleType}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleQuickEmergencyTrigger(emergencyRoute)}
                    className="w-full py-2.5 px-3 bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-slate-100 rounded-xl text-xs font-mono font-bold border border-slate-700 hover:border-emerald-500/50 transition-all flex items-center justify-center space-x-1.5 shadow-md cursor-pointer"
                  >
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    <span>DISENGAGE PREEMPTION</span>
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => handleQuickEmergencyTrigger('North-South')}
                    className="py-2.5 px-2 bg-gradient-to-br from-rose-900/90 to-red-950 hover:from-rose-800 hover:to-red-900 text-white rounded-xl text-[11px] font-mono font-black border border-rose-500/60 hover:border-rose-400 transition-all flex flex-col items-center justify-center space-y-0.5 shadow-[0_0_12px_rgba(244,63,94,0.25)] hover:shadow-[0_0_16px_rgba(244,63,94,0.4)] active:scale-95 cursor-pointer"
                    title="Grant instant green wave preemption for North-South ambulance"
                  >
                    <span className="text-sm">🚑</span>
                    <span className="tracking-wide">NS AMBULANCE</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickEmergencyTrigger('East-West')}
                    className="py-2.5 px-2 bg-gradient-to-br from-rose-900/90 to-red-950 hover:from-rose-800 hover:to-red-900 text-white rounded-xl text-[11px] font-mono font-black border border-rose-500/60 hover:border-rose-400 transition-all flex flex-col items-center justify-center space-y-0.5 shadow-[0_0_12px_rgba(244,63,94,0.25)] hover:shadow-[0_0_16px_rgba(244,63,94,0.4)] active:scale-95 cursor-pointer"
                    title="Grant instant green wave preemption for East-West ambulance"
                  >
                    <span className="text-sm">🚑</span>
                    <span className="tracking-wide">EW AMBULANCE</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Collapsed Mini Emergency Trigger - Prominent Top Location & Larger Size */
            <div className="flex flex-col items-center py-1">
              <button
                type="button"
                onClick={() => handleQuickEmergencyTrigger('North-South')}
                className={`flex h-12 w-12 items-center justify-center rounded-2xl border-2 transition-all cursor-pointer shadow-lg ${emergencyActive
                    ? 'bg-rose-600 border-rose-300 text-white animate-pulse shadow-[0_0_18px_rgba(244,63,94,0.8)] scale-105'
                    : 'bg-gradient-to-b from-rose-950 to-red-950 border-rose-500/70 text-rose-300 hover:border-rose-400 hover:scale-110 hover:text-white shadow-[0_0_12px_rgba(244,63,94,0.35)]'
                  }`}
                title={
                  emergencyActive
                    ? `Emergency Active on ${emergencyRoute} - Click to Disengage`
                    : 'EMERGENCY HUD: 1-Click Fast Preemption (NS Ambulance)'
                }
              >
                <Siren className="h-6 w-6" />
              </button>
              <span className="text-[9px] font-mono font-bold text-rose-400 mt-1 uppercase">
                {emergencyActive ? 'EMERG' : 'SOS'}
              </span>
            </div>
          )}
        </div>

        {/* Operational Workspace Navigation */}
        <nav className="space-y-1.5 p-2">
          <div className="px-2 py-1">
            {!isSidebarCollapsed ? (
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase font-mono">
                Operational Workspaces
              </span>
            ) : (
              <div className="h-1" />
            )}
          </div>

          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeWorkspace === item.id;

            return (
              <button
                key={item.id}
                type="button"
                data-workspace={item.id}
                onClick={() => setActiveWorkspace(item.id)}
                className={`group relative flex w-full items-center rounded-xl p-2.5 text-left transition-all cursor-pointer ${isActive
                    ? 'bg-gradient-to-r from-cyan-950/60 to-slate-900/80 border border-cyan-500/40 text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,0.12)]'
                    : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200 border border-transparent hover:border-slate-800'
                  } ${isSidebarCollapsed ? 'justify-center' : 'space-x-3'}`}
                title={isSidebarCollapsed ? `${item.label}: ${item.description}` : undefined}
              >
                {/* Active Indicator Glow Bar */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
                )}

                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-all ${isActive
                      ? 'bg-cyan-500/20 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                      : 'bg-slate-900/90 text-slate-400 group-hover:text-cyan-300 group-hover:bg-slate-800'
                    }`}
                >
                  <Icon className="h-5 w-5" />
                </div>

                {!isSidebarCollapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-xs font-semibold truncate ${isActive ? 'text-white' : 'text-slate-300'
                          }`}
                      >
                        {item.label}
                      </span>
                      {item.badge && (
                        <span
                          className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ml-1 shrink-0 ${item.badgeColor}`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400 truncate leading-tight mt-0.5">
                      {item.description}
                    </p>
                  </div>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Telemetry Micro-Pill at Bottom */}
      <div className="shrink-0 border-t border-slate-800/60 px-3 py-2 text-[10px] text-slate-400 flex items-center justify-between">
        {!isSidebarCollapsed ? (
          <>
            <div className="flex items-center space-x-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="font-mono text-slate-300">SUMO: {sumoStatus}</span>
            </div>
            <span className="font-mono text-cyan-400">MQTT: {mqttStatus}</span>
          </>
        ) : (
          <div className="mx-auto flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" title={`SUMO: ${sumoStatus}`} />
        )}
      </div>
    </aside>
  );
}
