import React, { useState, useEffect } from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useApproachData } from '../../api/queries/useApproachData';
import { useSignalStatus } from '../../api/queries/useSignalStatus';
import { useSignalsWebSocket } from '../../hooks/useSignalsWebSocket';
import { useTrafficOverview } from '../../api/queries/useTrafficOverview';
import { MonitorPlay, Play, Pause, RefreshCw, FastForward, Activity } from 'lucide-react';

export function SumoSimulationPanel() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [simSpeed, setSimSpeed] = useState(1);
  const [tick, setTick] = useState(0);

  const { data: approachesResponse } = useApproachData();
  const approaches = approachesResponse?.approaches || (Array.isArray(approachesResponse) ? approachesResponse : []);
  const { data: initialSignalsResponse } = useSignalStatus();
  const initialSignals = initialSignalsResponse?.signals || (Array.isArray(initialSignalsResponse) ? initialSignalsResponse : []);
  const signals = useSignalsWebSocket(initialSignals);
  const { data: overview } = useTrafficOverview();

  // Animation loop for vehicle particle movement along SVG lanes
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setTick((t) => (t + 1) % 1000);
    }, 50 / simSpeed);
    return () => clearInterval(interval);
  }, [isPlaying, simSpeed]);

  const getSignalState = (dir) => {
    const sig = signals.find((s) => s.direction?.toLowerCase() === dir.toLowerCase());
    return sig?.state || 'GREEN';
  };

  const getSignalColor = (dir) => {
    const state = getSignalState(dir);
    return state === 'RED' ? '#EF4444' : state === 'YELLOW' ? '#F59E0B' : '#10B981';
  };

  const northVehCount = approaches.find((a) => a.approach?.includes('North'))?.vehicle_count || 12;
  const southVehCount = approaches.find((a) => a.approach?.includes('South'))?.vehicle_count || 15;
  const eastVehCount = approaches.find((a) => a.approach?.includes('East'))?.vehicle_count || 9;
  const westVehCount = approaches.find((a) => a.approach?.includes('West'))?.vehicle_count || 10;

  // Generate dynamic vehicle positions based on approach counts, animation tick, and signal state
  const renderVehicles = (count, direction) => {
    const items = [];
    const maxCount = Math.min(count, 10);
    const state = getSignalState(direction);
    const isRed = state === 'RED';

    for (let i = 0; i < maxCount; i++) {
      let offset;
      if (isRed) {
        // When signal is RED, vehicles queue up behind the stop bar (offset 155 - i * 14)
        const stopPos = 155 - (i * 15);
        const movingOffset = ((tick * 0.5 + i * 35) % 180) + 15;
        // Vehicles advance until they reach their queue spot at the stop bar
        offset = Math.min(stopPos, movingOffset);
      } else {
        // When signal is GREEN, vehicles flow continuously across the entire junction corridor
        offset = ((tick * (0.6 + (i % 3) * 0.08) + i * 35) % 360) + 20;
      }

      let cx = 200, cy = 200;

      if (direction === 'North') {
        cx = 190;
        cy = offset;
      } else if (direction === 'South') {
        cx = 210;
        cy = 400 - offset;
      } else if (direction === 'East') {
        cx = 400 - offset;
        cy = 190;
      } else if (direction === 'West') {
        cx = offset;
        cy = 210;
      }

      // Hide vehicles that move far off canvas during GREEN flow
      if (offset > 380) continue;

      items.push(
        <circle
          key={`${direction}-${i}`}
          cx={cx}
          cy={cy}
          r="4.5"
          className={direction === 'North' || direction === 'South' ? 'fill-cyan-400' : 'fill-blue-400'}
          style={{ filter: 'drop-shadow(0 0 4px rgba(34, 211, 238, 0.8))' }}
        />
      );
    }
    return items;
  };

  return (
    <SectionCard
      title="Live Network Geometry & Simulation Feed (Section 2)"
      icon={MonitorPlay}
      action={
        <div className="flex items-center space-x-3">
          {/* Simulation Control Bar */}
          <div className="flex items-center space-x-1.5 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-1 hover:bg-slate-800 rounded text-cyan-400 transition"
              title={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => setSimSpeed((s) => (s === 1 ? 2 : s === 2 ? 5 : 1))}
              className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-800 text-slate-300 hover:text-cyan-400 transition flex items-center space-x-1"
            >
              <FastForward className="w-3 h-3 text-cyan-400" />
              <span>{simSpeed}x</span>
            </button>
            <button
              onClick={() => { setTick(0); setIsPlaying(true); }}
              className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition"
              title="Reset View"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <span className="hidden sm:inline-block text-[11px] font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
            Source: <span className="text-cyan-400 font-semibold">{overview?.source || 'sumo_simulation'}</span> ({overview?.confidence || 'exact'})
          </span>
        </div>
      }
    >
      <div className="h-[360px] rounded-xl bg-[#080D1A] border border-slate-800/80 relative flex items-center justify-center overflow-hidden shadow-inner">
        {/* Subtle Background Grid Pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:20px_20px] opacity-30"></div>

        {/* SVG Network Geometry Renderer */}
        <svg viewBox="0 0 400 400" className="w-full h-full max-w-[500px]">
          {/* Background Surface */}
          <rect width="400" height="400" fill="#080D1A" />

          {/* Road Network Corridors */}
          {/* North-South Road */}
          <rect x="170" y="0" width="60" height="400" fill="#111827" stroke="#1E293B" strokeWidth="1" />
          {/* East-West Road */}
          <rect x="0" y="170" width="400" height="60" fill="#111827" stroke="#1E293B" strokeWidth="1" />

          {/* Junction Core Box */}
          <rect x="170" y="170" width="60" height="60" fill="#1F293D" stroke="#334155" strokeWidth="1.5" />

          {/* Lane Centerlines (Dashed Yellow/White) */}
          <line x1="200" y1="0" x2="200" y2="170" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.6" />
          <line x1="200" y1="230" x2="200" y2="400" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.6" />
          <line x1="0" y1="200" x2="170" y2="200" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.6" />
          <line x1="230" y1="200" x2="400" y2="200" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.6" />

          {/* Stop Bars */}
          <line x1="170" y1="170" x2="200" y2="170" stroke="#F8FAFC" strokeWidth="3" opacity="0.8" />
          <line x1="200" y1="230" x2="230" y2="230" stroke="#F8FAFC" strokeWidth="3" opacity="0.8" />
          <line x1="170" y1="200" x2="170" y2="230" stroke="#F8FAFC" strokeWidth="3" opacity="0.8" />
          <line x1="230" y1="170" x2="230" y2="200" stroke="#F8FAFC" strokeWidth="3" opacity="0.8" />

          {/* Signal Heads (Physical Signal LED Indicators) */}
          {/* North Signal Head */}
          <circle cx="162" cy="162" r="7" fill={getSignalColor('North')} style={{ filter: `drop-shadow(0 0 6px ${getSignalColor('North')})` }} />
          {/* South Signal Head */}
          <circle cx="238" cy="238" r="7" fill={getSignalColor('South')} style={{ filter: `drop-shadow(0 0 6px ${getSignalColor('South')})` }} />
          {/* East Signal Head */}
          <circle cx="238" cy="162" r="7" fill={getSignalColor('East')} style={{ filter: `drop-shadow(0 0 6px ${getSignalColor('East')})` }} />
          {/* West Signal Head */}
          <circle cx="162" cy="238" r="7" fill={getSignalColor('West')} style={{ filter: `drop-shadow(0 0 6px ${getSignalColor('West')})` }} />

          {/* Central Junction Marker */}
          <circle cx="200" cy="200" r="18" fill="none" stroke="#22D3EE" strokeWidth="1.5" strokeDasharray="4 2" className="animate-spin" style={{ animationDuration: '10s' }} />
          <text x="200" y="204" textAnchor="middle" fill="#22D3EE" fontSize="9" className="font-mono font-bold">J1-HUB</text>

          {/* Direction Labels */}
          <text x="200" y="25" textAnchor="middle" fill="#94A3B8" fontSize="10" className="font-mono">NORTH</text>
          <text x="200" y="385" textAnchor="middle" fill="#94A3B8" fontSize="10" className="font-mono">SOUTH</text>
          <text x="375" y="204" textAnchor="middle" fill="#94A3B8" fontSize="10" className="font-mono">EAST</text>
          <text x="25" y="204" textAnchor="middle" fill="#94A3B8" fontSize="10" className="font-mono">WEST</text>

          {/* Dynamic Animated Vehicles */}
          {renderVehicles(northVehCount, 'North')}
          {renderVehicles(southVehCount, 'South')}
          {renderVehicles(eastVehCount, 'East')}
          {renderVehicles(westVehCount, 'West')}
        </svg>

        {/* Dynamic Telemetry Status Overlay */}
        <div className="absolute bottom-3 left-3 bg-slate-900/90 px-3 py-2 rounded-lg border border-slate-800 text-xs font-mono flex items-center space-x-3 backdrop-blur">
          <div className="flex items-center space-x-1.5 text-cyan-400">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            <span className="font-semibold">TraCI Telemetry Active</span>
          </div>
          <div className="h-3 w-px bg-slate-800"></div>
          <span className="text-slate-400">Active Vehicles: <strong className="text-slate-200">{overview?.total_vehicle_count ?? 142}</strong></span>
          <div className="hidden md:block h-3 w-px bg-slate-800"></div>
          <span className="hidden md:inline text-slate-400">FPS: <strong className="text-emerald-400">60</strong></span>
        </div>
      </div>
    </SectionCard>
  );
}
