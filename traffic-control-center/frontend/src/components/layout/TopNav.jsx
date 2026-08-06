import React, { useState } from 'react';
import { useLiveClock } from '../../hooks/useLiveClock';
import { useConnectionStore } from '../../store/connectionStore';
import { Activity, Radio, Cpu, Server, MapPin, ChevronDown } from 'lucide-react';

export function TopNav() {
  const clock = useLiveClock();
  const { sumoStatus, fastApiStatus, mqttStatus } = useConnectionStore();
  const [selectedJunction, setSelectedJunction] = useState('J1-HUB');

  return (
    <header className="h-16 border-b border-slate-800 bg-[#0F172A]/90 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="font-semibold text-slate-100 text-base md:text-lg tracking-wide">
              Traffic Control Center
            </h1>
            <p className="text-[11px] text-slate-400">Autonomous Multi-Agent Intersection Management</p>
          </div>
        </div>

        {/* Multi-Intersection Selector Dropdown (Future Scalability Ready) */}
        <div className="hidden md:flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
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

      <div className="flex items-center space-x-6">
        {/* Status Indicators */}
        <div className="hidden lg:flex items-center space-x-3 text-xs">
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

        {/* Live Clock */}
        <div className="font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-500/30 px-3 py-1.5 rounded-md text-sm font-semibold tracking-wider">
          {clock}
        </div>
      </div>
    </header>
  );
}
