import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { SectionCard } from '../layout/SectionCard';
import { IntersectionRenderer } from './IntersectionRenderer';
import { SimulationHUD } from './SimulationHUD';
import { VehicleDetailModal } from './VehicleDetailModal';

import { useApproachData } from '../../api/queries/useApproachData';
import { useSignalStatus } from '../../api/queries/useSignalStatus';
import { useSignalsWebSocket } from '../../hooks/useSignalsWebSocket';
import { useTrafficOverview } from '../../api/queries/useTrafficOverview';
import { useAgentStatus } from '../../api/queries/useAgentStatus';
import { useHardwareStatus } from '../../api/queries/useHardwareStatus';
import { useScenarioStore } from '../../store/scenarioStore';
import { useEmergencyControl } from '../../api/queries/useEmergencyControl';

import { 
  MonitorPlay, 
  Play, 
  Pause, 
  RefreshCw, 
  FastForward, 
  Siren, 
  Truck, 
  ShieldAlert, 
  Zap, 
  Layers, 
  CheckCircle2 
} from 'lucide-react';

/**
 * SumoSimulationPanel - State-of-the-Art Smart City Simulation Control Center.
 * Integrates 4-Phase Isolated / 2-Phase Signal Mode switcher, direct Emergency Vehicle Dispatch
 * (Ambulance, Fire Truck, Police), 60 FPS vector canvas, real-time TraCI telemetry, and HUD.
 */
export function SumoSimulationPanel() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [simSpeed, setSimSpeed] = useState(1);
  const [tick, setTick] = useState(0);
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  const { data: approachesResponse } = useApproachData();
  const approaches = approachesResponse?.approaches || (Array.isArray(approachesResponse) ? approachesResponse : []);
  const telemetryVehicles = React.useMemo(() => {
    if (approachesResponse?.vehicles && Array.isArray(approachesResponse.vehicles) && approachesResponse.vehicles.length > 0) {
      return approachesResponse.vehicles;
    }
    if (Array.isArray(approaches) && approaches.length > 0) {
      const extracted = [];
      approaches.forEach(app => {
        if (app.vehicles && Array.isArray(app.vehicles)) {
          extracted.push(...app.vehicles);
        }
      });
      return extracted;
    }
    return [];
  }, [approachesResponse, approaches]);

  const { data: initialSignalsResponse } = useSignalStatus();
  const initialSignals = initialSignalsResponse?.signals || (Array.isArray(initialSignalsResponse) ? initialSignalsResponse : []);
  const signals = useSignalsWebSocket(initialSignals);

  const { data: overview, refetch: refetchOverview } = useTrafficOverview();
  const { data: agentStatusResponse } = useAgentStatus();
  const agentStatus = agentStatusResponse?.agent_status || (Array.isArray(agentStatusResponse) ? agentStatusResponse : []);
  const { data: hardwareResponse } = useHardwareStatus();
  const hardwareStatus = hardwareResponse?.hardware_status || (Array.isArray(hardwareResponse) ? hardwareResponse : []);

  const { 
    activeScenario, 
    scenarioApproach, 
    emergencyVehicleType, 
    emergencyActive, 
    emergencyRoute, 
    signalMode, 
    setSignalMode, 
    setEmergencyDispatch, 
    setScenario 
  } = useScenarioStore();

  const { triggerEmergencyCorridor } = useEmergencyControl();

  // Animation Frame Tick Loop for smooth micro-movements
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setTick((t) => (t + 1) % 1000);
    }, 40 / simSpeed);
    return () => clearInterval(interval);
  }, [isPlaying, simSpeed]);

  // Toggle between 4-Phase (1-by-1) and 2-Phase (Paired) mode
  const handleToggleSignalMode = async (newMode) => {
    setSignalMode(newMode);
    try {
      await axios.post('/api/signals/mode', { mode: newMode });
      refetchOverview();
    } catch (err) {
      console.warn('Backend signal mode update:', err);
    }
  };

  // Quick Dispatch for specific Emergency Vehicles
  const handleQuickEmergencyDispatch = async (vType) => {
    const route = emergencyRoute || 'North-South';
    const nextActive = !emergencyActive || emergencyVehicleType !== vType;

    setEmergencyDispatch(vType, route, nextActive);

    triggerEmergencyCorridor.mutate({
      active: nextActive,
      direction: route,
      vehicle_type: vType
    });
  };

  return (
    <SectionCard
      title="Live Network Geometry & Simulation Feed (Smart City Control)"
      icon={MonitorPlay}
      action={
        <div className="flex flex-wrap items-center gap-2">
          {/* 1. Signal Sequencing Mode Toggle (4-Phase vs 2-Phase) */}
          <div className="flex items-center bg-slate-950 px-1.5 py-1 rounded-lg border border-slate-800 text-xs font-mono">
            <span className="text-slate-500 mr-2 text-[10px] hidden lg:inline">MODE:</span>
            <button
              onClick={() => handleToggleSignalMode('one_by_one')}
              className={`px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center space-x-1 ${
                (signalMode === 'one_by_one' || overview?.signal_mode === 'one_by_one')
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="4-Phase (1-by-1): Only the green junction goes right, left, straight; others wait"
            >
              <span>4-Phase (1-by-1)</span>
            </button>
            <button
              onClick={() => handleToggleSignalMode('paired_corridor')}
              className={`px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center space-x-1 ml-1 ${
                (signalMode !== 'one_by_one' && overview?.signal_mode !== 'one_by_one')
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="2-Phase: Paired Corridors (North+South & East+West)"
            >
              <span>2-Phase (Paired)</span>
            </button>
          </div>

          {/* 2. Simulation Speed & Playback Toolbar */}
          <div className="flex items-center space-x-1 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800 text-xs font-mono">
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
              title="Reset Simulation View"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      }
    >
      <div className="space-y-3.5">
        {/* Quick Emergency Dispatch Bar right above Canvas */}
        <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-2.5 flex flex-wrap items-center justify-between gap-2.5 font-mono text-xs">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400">
              <Siren className="w-4 h-4 animate-pulse" />
            </div>
            <span className="text-slate-300 font-bold text-xs">Emergency Green Corridor:</span>
          </div>

          {/* Direct Emergency Vehicle Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleQuickEmergencyDispatch('ambulance')}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 border ${
                emergencyActive && emergencyVehicleType === 'ambulance'
                  ? 'bg-rose-600 text-white border-rose-400 shadow-[0_0_12px_rgba(239,68,68,0.5)] animate-pulse'
                  : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border-slate-700'
              }`}
            >
              <span>🚑</span>
              <span>Ambulance</span>
            </button>

            <button
              onClick={() => handleQuickEmergencyDispatch('fire')}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 border ${
                emergencyActive && emergencyVehicleType === 'fire'
                  ? 'bg-red-600 text-white border-red-400 shadow-[0_0_12px_rgba(220,38,38,0.5)] animate-pulse'
                  : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border-slate-700'
              }`}
            >
              <span>🚒</span>
              <span>Fire Truck</span>
            </button>

            <button
              onClick={() => handleQuickEmergencyDispatch('police')}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 border ${
                emergencyActive && emergencyVehicleType === 'police'
                  ? 'bg-blue-600 text-white border-blue-400 shadow-[0_0_12px_rgba(37,99,235,0.5)] animate-pulse'
                  : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border-slate-700'
              }`}
            >
              <span>🚓</span>
              <span>Police</span>
            </button>
          </div>

          <div className="text-[11px] text-slate-400 hidden sm:block">
            {emergencyActive ? (
              <span className="text-emerald-400 font-bold flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Locked Green Wave • Cross Roads Holding RED</span>
              </span>
            ) : (
              <span>Click vehicle to trigger priority green corridor</span>
            )}
          </div>
        </div>

        {/* HUD & Status Bar Banner */}
        <SimulationHUD
          overview={overview}
          signals={signals}
          agentStatus={agentStatus}
          hardwareStatus={hardwareStatus}
        />

        {/* 4-Way Smart City Intersection Visualizer Canvas */}
        <div className="h-[480px] w-full rounded-2xl relative overflow-hidden flex items-center justify-center border border-slate-800/90 shadow-2xl bg-[#080D1A]">
          <IntersectionRenderer
            approaches={approaches}
            signals={signals}
            telemetryVehicles={telemetryVehicles}
            simTick={tick}
            onSelectVehicle={setSelectedVehicle}
            selectedVehicleId={selectedVehicle?.id}
            activeScenario={activeScenario || overview?.active_scenario || 'normal'}
            scenarioApproach={scenarioApproach || 'North'}
          />
        </div>

        {/* Vehicle Detail Telemetry Inspector Modal */}
        {selectedVehicle && (
          <VehicleDetailModal
            vehicle={selectedVehicle}
            onClose={() => setSelectedVehicle(null)}
          />
        )}
      </div>
    </SectionCard>
  );
}
