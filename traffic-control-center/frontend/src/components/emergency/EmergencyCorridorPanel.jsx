import React, { useState, useEffect } from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useTrafficOverview } from '../../api/queries/useTrafficOverview';
import { useEmergencyControl } from '../../api/queries/useEmergencyControl';
import { useScenarioStore } from '../../store/scenarioStore';
import { ShieldAlert, Siren, Truck, ShieldCheck, Zap, AlertCircle, RefreshCw, Compass } from 'lucide-react';

export function EmergencyCorridorPanel() {
  const { data: overview, refetch } = useTrafficOverview();
  const { triggerEmergencyCorridor } = useEmergencyControl();
  const { 
    emergencyVehicleType, 
    emergencyActive, 
    emergencyRoute, 
    setEmergencyDispatch 
  } = useScenarioStore();

  const [selectedVehicleType, setSelectedVehicleType] = useState(emergencyVehicleType || 'ambulance');
  const [selectedCorridor, setSelectedCorridor] = useState(emergencyRoute || 'North-South');

  useEffect(() => {
    if (emergencyVehicleType) {
      setSelectedVehicleType(emergencyVehicleType);
    }
    if (emergencyRoute) {
      setSelectedCorridor(emergencyRoute);
    }
  }, [emergencyVehicleType, emergencyRoute]);

  const emergencyCount = overview?.emergency_vehicle_count ?? (emergencyActive ? 1 : 0);
  const isCorridorActive = emergencyActive || overview?.ai_control_mode === 'EMERGENCY_GREEN_CORRIDOR';

  const handleSelectVehicle = (vId) => {
    setSelectedVehicleType(vId);
    if (isCorridorActive) {
      setEmergencyDispatch(vId, selectedCorridor, true);
      triggerEmergencyCorridor.mutate({
        active: true,
        direction: selectedCorridor,
        vehicle_type: vId,
      });
    }
  };

  const handleSelectCorridor = (cId) => {
    setSelectedCorridor(cId);
    if (isCorridorActive) {
      setEmergencyDispatch(selectedVehicleType, cId, true);
      triggerEmergencyCorridor.mutate({
        active: true,
        direction: cId,
        vehicle_type: selectedVehicleType,
      });
    }
  };

  const handleActivateCorridor = () => {
    setEmergencyDispatch(selectedVehicleType, selectedCorridor, true);
    triggerEmergencyCorridor.mutate({
      active: true,
      direction: selectedCorridor,
      vehicle_type: selectedVehicleType,
    }, {
      onSuccess: () => refetch()
    });
  };

  const handleDeactivateCorridor = () => {
    setEmergencyDispatch(selectedVehicleType, selectedCorridor, false);
    triggerEmergencyCorridor.mutate({
      active: false,
      direction: selectedCorridor,
      vehicle_type: selectedVehicleType,
    }, {
      onSuccess: () => refetch()
    });
  };

  return (
    <SectionCard title="Emergency Vehicle Green Corridor Mode" icon={ShieldAlert}>
      <div className="glass-panel p-4 rounded-2xl border border-slate-800/90 space-y-4 relative overflow-hidden">
        {/* Specular Top Rim Highlight */}
        <div className="absolute top-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-rose-500/30 to-transparent pointer-events-none" />

        {isCorridorActive && (
          <div className="absolute inset-0 bg-rose-500/10 backdrop-blur-[1px] pointer-events-none border-2 border-rose-500/40 rounded-2xl animate-pulse" />
        )}

        {/* Top Status Header */}
        <div className="flex flex-col 2xl:flex-row items-start 2xl:items-center justify-between gap-2.5 border-b border-slate-800 pb-3 relative z-10">
          <div className="flex items-center space-x-3">
            <div className={`p-2.5 rounded-xl transition-all ${
              isCorridorActive 
                ? 'bg-rose-500 text-white border border-rose-400 animate-bounce shadow-[0_0_15px_#f43f5e]' 
                : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
            }`}>
              <Siren className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="text-sm font-bold text-slate-100 whitespace-nowrap font-mono">Green Corridor Dispatcher</h4>
                <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border whitespace-nowrap ${
                  isCorridorActive
                    ? 'bg-rose-950/90 text-rose-300 border-rose-500 animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.4)]'
                    : 'bg-emerald-950/60 text-emerald-300 border-emerald-700/80'
                }`}>
                  {isCorridorActive ? '● LOCKED GREEN CORRIDOR' : '● STANDBY MODE'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Grants continuous green signal preemption for emergency responders. Cross traffic locked at RED.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 bg-slate-950/90 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono shrink-0 shadow-inner">
            <Truck className="w-4 h-4 text-amber-400" />
            <span className="text-slate-200 font-semibold whitespace-nowrap">
              {emergencyCount} Active Emergency Vehicles
            </span>
          </div>
        </div>

        {/* Control Selection Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 relative z-10">
          {/* Emergency Vehicle Type Selection */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1.5 font-mono uppercase tracking-wider">
              <Truck className="w-3.5 h-3.5 text-cyan-400" />
              <span>Select Emergency Vehicle:</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'ambulance', label: 'Ambulance 🚑' },
                { id: 'fire', label: 'Fire Truck 🚒' },
                { id: 'police', label: 'Police 🚓' },
              ].map((v) => (
                <button
                  key={v.id}
                  onClick={() => handleSelectVehicle(v.id)}
                  className={`px-2.5 py-2 rounded-xl text-xs font-semibold font-mono transition-all cursor-pointer ${
                    selectedVehicleType === v.id
                      ? 'bg-gradient-to-r from-rose-950 to-red-900 text-rose-200 border border-rose-500/80 font-bold shadow-[0_0_12px_rgba(244,63,94,0.3)]'
                      : 'bg-slate-950/80 text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-slate-800'
                  }`}
                >
                  {v.label}
                </button>
              ))}
            </div>
          </div>

          {/* Corridor Direction Selection */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1.5 font-mono uppercase tracking-wider">
              <Compass className="w-3.5 h-3.5 text-cyan-400" />
              <span>Target Green Corridor Route:</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: 'North-South', label: 'North-South Corridor' },
                { id: 'East-West', label: 'East-West Corridor' },
              ].map((c) => (
                <button
                  key={c.id}
                  onClick={() => handleSelectCorridor(c.id)}
                  className={`px-2.5 py-2 rounded-xl text-xs font-semibold font-mono transition-all cursor-pointer ${
                    selectedCorridor === c.id
                      ? 'bg-gradient-to-r from-cyan-950 to-blue-900 text-cyan-200 border border-cyan-500/80 font-bold shadow-[0_0_12px_rgba(6,182,212,0.3)]'
                      : 'bg-slate-950/80 text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-slate-800'
                  }`}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Dispatch Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-800/80 relative z-10">
          <button
            onClick={handleActivateCorridor}
            disabled={triggerEmergencyCorridor.isPending}
            className={`w-full sm:w-auto flex-1 flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-black font-mono tracking-wider uppercase transition-all shadow-lg cursor-pointer active:scale-95 ${
              isCorridorActive
                ? 'bg-rose-600 text-white shadow-[0_0_20px_rgba(244,63,94,0.6)] hover:bg-rose-500'
                : 'bg-gradient-to-r from-rose-600 via-rose-700 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white shadow-[0_0_15px_rgba(244,63,94,0.35)]'
            }`}
          >
            {triggerEmergencyCorridor.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Siren className="w-4 h-4" />
            )}
            <span>{isCorridorActive ? 'RE-ENGAGE GREEN CORRIDOR' : 'ACTIVATE GREEN CORRIDOR'}</span>
          </button>

          {isCorridorActive && (
            <button
              onClick={handleDeactivateCorridor}
              disabled={triggerEmergencyCorridor.isPending}
              className="w-full sm:w-auto flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-slate-900/90 text-slate-200 hover:bg-slate-800 border border-slate-700 hover:border-emerald-500/50 font-mono transition-all cursor-pointer active:scale-95 shadow-md"
            >
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>RESUME AI ADAPTIVE MODE</span>
            </button>
          )}
        </div>

        {/* Live Corridor Status Explanation */}
        <div className="bg-slate-950/90 p-3 rounded-xl border border-slate-800 text-[11px] text-slate-300 leading-relaxed flex items-start space-x-2.5 relative z-10">
          <AlertCircle className={`w-4 h-4 shrink-0 mt-0.5 ${isCorridorActive ? 'text-rose-400' : 'text-cyan-400'}`} />
          <div>
            <span className="font-bold text-slate-200 font-mono uppercase tracking-wider">
              {isCorridorActive ? 'Active Corridor Lock: ' : 'Emergency Protocol: '}
            </span>
            {isCorridorActive
              ? `Locked GREEN preemption active for ${selectedVehicleType.toUpperCase()} on ${selectedCorridor}. All cross roads held at solid RED until vehicle clears.`
              : `Select Ambulance, Fire Truck, or Police and activate corridor to grant instant green preemption in the live simulation.`}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
