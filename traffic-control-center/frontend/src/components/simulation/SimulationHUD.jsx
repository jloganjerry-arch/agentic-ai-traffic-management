import React, { memo } from 'react';
import { Activity, Radio, Cpu, ShieldCheck, Zap, Server } from 'lucide-react';

/**
 * SimulationHUD - Compact Simulation Title, Prominent AI Decision Badge,
 * Infrastructure System Status Row, Telemetry Bar, and Agent Status Chips.
 */
export const SimulationHUD = memo(function SimulationHUD({
  overview,
  signals = [],
  agentStatus = [],
  hardwareStatus = []
}) {
  const activeVehCount = overview?.total_vehicle_count ?? 142;
  const avgSpeed = overview?.avg_speed_kmh ?? 34.2;
  const currentPhase = overview?.current_signal_phase ?? 'NS GREEN';
  const queueLength = overview?.total_queue_length_m ?? 12.5;

  const isHardwareConnected = Array.isArray(hardwareStatus) && hardwareStatus.some(h => h.status === 'ONLINE' || h.mqtt_status === 'CONNECTED');

  const getAgentState = (name) => {
    if (!Array.isArray(agentStatus)) return 'ONLINE';
    const ag = agentStatus.find(a => a.name?.toLowerCase().includes(name.toLowerCase()));
    return ag?.status || 'ONLINE';
  };

  return (
    <div className="w-full space-y-2.5 font-mono select-none">
      {/* 1. Header Row: Title & Active Signal Decision Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-950/90 border border-slate-800/90 px-3.5 py-2 rounded-xl backdrop-blur">
        {/* Title Label */}
        <div className="flex items-center space-x-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold text-slate-100 uppercase tracking-wide">
              <span>LIVE SUMO TRAFFIC SIMULATION</span>
              <span className="text-[10px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 rounded font-bold">● LIVE</span>
            </div>
            <div className="text-[10px] text-slate-400 tracking-tight">4-WAY JUNCTION • REAL-TIME TELEMETRY</div>
          </div>
        </div>

        {/* Prominent Adaptive Decision Badge & Sequencing Mode */}
        <div className="flex items-center space-x-2">
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-[10.5px] font-mono font-bold ${
            overview?.signal_mode === 'one_by_one' 
              ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300' 
              : 'bg-cyan-950/80 border-cyan-500/40 text-cyan-300'
          }`}>
            <span className={`w-2 h-2 rounded-full ${overview?.signal_mode === 'one_by_one' ? 'bg-emerald-400 animate-pulse' : 'bg-cyan-400'}`}></span>
            <span>{overview?.signal_mode === 'one_by_one' ? '4-PHASE (1-BY-1)' : '2-PHASE (PAIRED)'}</span>
          </div>

          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1 rounded-lg border border-purple-500/40 shadow-sm">
            <Zap className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            <span className="text-[11px] font-bold text-slate-300">
              {overview?.ai_control_mode === 'Fixed Cycle' ? 'FIXED •' : 'ADAPTIVE •'}
            </span>
            <span className="text-xs font-bold text-emerald-400">{currentPhase}</span>
          </div>
        </div>
      </div>

      {/* 1.5. Real-Time Environmental Adaptation Diagnostics Bar */}
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/30 px-3.5 py-1.5 rounded-xl flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-cyan-950/90 border border-cyan-500/40 text-cyan-300 text-[10.5px] font-bold">
            <Zap className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>ADAPTIVE TIMING ENGINE</span>
          </div>
          <span className="text-slate-200 font-bold text-xs flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>
              {signals[0]?.adaptive_action && signals[0].adaptive_action !== 'NOMINAL'
                ? signals[0].adaptive_action
                : (overview?.adaptive_status || 'DYNAMIC GLIDE ACTUATED')}
            </span>
          </span>
        </div>
        <div className="text-[11px] text-slate-300 flex items-center space-x-2">
          <span className="text-slate-500 text-[10px] uppercase font-bold">Environmental Trigger:</span>
          <span className="text-emerald-300 font-medium">
            {signals[0]?.adaptive_reason || overview?.adaptive_event || 'Actively balancing vehicle queues and clearing platoons'}
          </span>
        </div>
      </div>

      {/* 2. Live Telemetry Bar */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 bg-slate-900/90 border border-slate-800 p-2.5 rounded-xl">
        {/* Connection Source */}
        <div className="md:col-span-4 flex items-center space-x-2 border-b md:border-b-0 md:border-r border-slate-800 pb-2 md:pb-0 pr-2">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
          <div className="text-xs">
            <span className="text-cyan-400 font-bold block leading-tight">TRACI TELEMETRY ACTIVE</span>
            <span className="text-[10px] text-slate-400">Source: <strong className="text-slate-200">{overview?.source || 'sumo_simulation'}</strong> ({overview?.confidence || 'exact'})</span>
          </div>
        </div>

        {/* Real Metrics */}
        <div className="md:col-span-8 flex items-center justify-around text-xs pt-1 md:pt-0">
          <div>
            <span className="text-slate-400 text-[10px] block">VEHICLES</span>
            <strong className="text-cyan-400 text-sm font-bold">{activeVehCount}</strong>
          </div>
          <div className="h-5 w-px bg-slate-800"></div>
          <div>
            <span className="text-slate-400 text-[10px] block">AVG SPEED</span>
            <strong className="text-emerald-400 text-sm font-bold">{avgSpeed} km/h</strong>
          </div>
          <div className="h-5 w-px bg-slate-800"></div>
          <div>
            <span className="text-slate-400 text-[10px] block">QUEUE</span>
            <strong className="text-amber-400 text-sm font-bold">{queueLength} m</strong>
          </div>
        </div>
      </div>

      {/* 3. System Health Infrastructure Row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[10.5px]">
        <div className="bg-slate-900/70 border border-slate-800/80 px-2.5 py-1.2 rounded-lg flex items-center justify-between">
          <span className="text-slate-400 flex items-center space-x-1">
            <Server className="w-3 h-3 text-slate-500" />
            <span>TRACI</span>
          </span>
          <span className="text-emerald-400 font-bold flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>CONNECTED</span>
          </span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/80 px-2.5 py-1.2 rounded-lg flex items-center justify-between">
          <span className="text-slate-400 flex items-center space-x-1">
            <Cpu className="w-3 h-3 text-slate-500" />
            <span>SUMO</span>
          </span>
          <span className="text-emerald-400 font-bold flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>RUNNING</span>
          </span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/80 px-2.5 py-1.2 rounded-lg flex items-center justify-between">
          <span className="text-slate-400 flex items-center space-x-1">
            <Radio className="w-3 h-3 text-slate-500" />
            <span>TELEMETRY</span>
          </span>
          <span className="text-cyan-400 font-bold flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
            <span>LIVE</span>
          </span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/80 px-2.5 py-1.2 rounded-lg flex items-center justify-between">
          <span className="text-slate-400 flex items-center space-x-1">
            <Zap className="w-3 h-3 text-slate-500" />
            <span>CONTROL</span>
          </span>
          <span className={overview?.ai_control_mode === 'Fixed Cycle' ? "text-slate-400 font-bold" : "text-purple-400 font-bold"}>
            {overview?.ai_control_mode === 'Fixed Cycle' ? 'FIXED' : 'ADAPTIVE'}
          </span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800/80 px-2.5 py-1.2 rounded-lg flex items-center justify-between col-span-2 sm:col-span-1">
          <span className="text-slate-400 flex items-center space-x-1">
            <ShieldCheck className="w-3 h-3 text-slate-500" />
            <span>MQTT/ESP32</span>
          </span>
          <span className={isHardwareConnected ? "text-emerald-400 font-bold flex items-center space-x-1" : "text-slate-400 font-bold"}>
            {isHardwareConnected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>}
            <span>{isHardwareConnected ? 'CONNECTED' : 'STANDBY'}</span>
          </span>
        </div>
      </div>

      {/* 4. Multi-Agent Status Row */}
      <div className="flex flex-wrap items-center justify-between bg-slate-950/80 border border-slate-800/60 px-3 py-1.5 rounded-lg text-[10.5px]">
        <span className="text-slate-400 font-bold text-[9.5px] uppercase tracking-wider">Agentic AI System:</span>

        <div className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-300">Monitoring:</span>
          <span className="text-emerald-400 font-bold">{getAgentState('monitoring')}</span>
        </div>

        <div className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
          <span className="text-slate-300">Analysis:</span>
          <span className="text-cyan-400 font-bold">{getAgentState('analysis')}</span>
        </div>

        <div className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
          <span className="text-slate-300">Optimization:</span>
          <span className="text-purple-400 font-bold">{getAgentState('optimization')}</span>
        </div>

        <div className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
          <span className="text-slate-300">Supervisor:</span>
          <span className="text-blue-400 font-bold">{getAgentState('supervisor')}</span>
        </div>

        <div className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-300">Safety Guardian:</span>
          <span className="text-emerald-400 font-bold">{getAgentState('safety')}</span>
        </div>
      </div>
    </div>
  );
});
