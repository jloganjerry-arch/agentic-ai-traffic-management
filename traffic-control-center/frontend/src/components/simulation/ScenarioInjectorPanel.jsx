import React, { useState } from 'react';
import axios from 'axios';
import { 
  Zap, 
  Siren, 
  AlertTriangle, 
  CloudRain, 
  RotateCcw, 
  Sparkles, 
  ShieldAlert, 
  Activity,
  CheckCircle2,
  Cpu
} from 'lucide-react';
import { useTrafficOverview } from '../../api/queries/useTrafficOverview';
import { useScenarioStore } from '../../store/scenarioStore';

const SCENARIOS = [
  {
    id: 'normal',
    label: 'Nominal Baseline',
    icon: RotateCcw,
    color: 'from-slate-600 to-slate-800',
    borderColor: 'border-slate-700',
    activeGlow: 'shadow-[0_0_20px_rgba(100,116,139,0.4)]',
    badge: 'bg-slate-700/40 text-slate-300',
    description: 'Standard urban traffic distribution with balanced green phase allocations across all 4 corridors.',
    impact: 'Nominal baseline traffic flow (30s NS / 30s EW).'
  },
  {
    id: 'rush_hour',
    label: 'Rush Hour Surge',
    icon: Zap,
    color: 'from-amber-600 to-orange-700',
    borderColor: 'border-amber-500/50',
    activeGlow: 'shadow-[0_0_25px_rgba(245,158,11,0.45)]',
    badge: 'bg-amber-500/20 text-amber-300 border border-amber-500/40',
    description: 'Spikes vehicle influx by up to 2.2x on the selected approach, triggering AI green phase expansion.',
    impact: 'AI expands green duration from 30s to 55s on high-density corridor.'
  },
  {
    id: 'emergency_corridor',
    label: 'Emergency Dispatch',
    icon: Siren,
    color: 'from-red-600 to-rose-800',
    borderColor: 'border-red-500/50',
    activeGlow: 'shadow-[0_0_25px_rgba(239,68,68,0.5)]',
    badge: 'bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse',
    description: 'Dispatches high-priority ambulance with immediate 90s Green Wave preemption along its route.',
    impact: 'Instant Green Wave preemption; conflicting signals locked RED.'
  },
  {
    id: 'accident_blockage',
    label: 'Accident / Blockage',
    icon: AlertTriangle,
    color: 'from-purple-600 to-indigo-800',
    borderColor: 'border-purple-500/50',
    activeGlow: 'shadow-[0_0_25px_rgba(168,85,247,0.45)]',
    badge: 'bg-purple-500/20 text-purple-300 border border-purple-500/40',
    description: 'Simulates a stalled vehicle with flashing hazard lights, prompting AI queue throttling & rerouting.',
    impact: 'Approach capacity reduced by 60%; AI redistributes green split.'
  },
  {
    id: 'weather_hazard',
    label: 'Adverse Weather (Rain)',
    icon: CloudRain,
    color: 'from-cyan-600 to-blue-800',
    borderColor: 'border-cyan-500/50',
    activeGlow: 'shadow-[0_0_25px_rgba(6,182,212,0.45)]',
    badge: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40',
    description: 'Reduces surface traction and speeds by 40%, extending yellow and all-red clearance intervals for safety.',
    impact: 'Speeds reduced to 20 km/h; yellow clearance extended by +4s.'
  }
];

/**
 * ScenarioInjectorPanel - Interactive Stress-Testing Preset Control Panel.
 * Allows operators to dynamically inject extreme traffic anomalies and observe
 * real-time multi-agent AI adaptation across the simulation.
 */
export function ScenarioInjectorPanel({ onScenarioChange }) {
  const { data: overview, refetch } = useTrafficOverview();
  const { activeScenario, scenarioApproach, scenarioIntensity, scenarioImpact, setScenario } = useScenarioStore();
  const [selectedApproach, setSelectedApproach] = useState(scenarioApproach || 'North');
  const [intensity, setIntensity] = useState(scenarioIntensity || 1.8);
  const [isInjecting, setIsInjecting] = useState(false);

  const handleInject = async (scenarioId) => {
    setIsInjecting(true);
    const scenarioObj = SCENARIOS.find(s => s.id === scenarioId) || SCENARIOS[0];
    const impactText = scenarioObj.impact;
    
    // Update local store immediately for instant 60 FPS response
    setScenario(scenarioId, selectedApproach, parseFloat(intensity), impactText);

    try {
      const response = await axios.post('/api/v1/simulation/scenario', {
        scenario: scenarioId,
        approach: selectedApproach,
        intensity: parseFloat(intensity),
        details: { timestamp: new Date().toISOString() }
      });

      if (response.data?.description) {
        setScenario(scenarioId, selectedApproach, parseFloat(intensity), response.data.description);
      }
      if (onScenarioChange) {
        onScenarioChange(scenarioId, selectedApproach);
      }
      refetch();
    } catch (err) {
      console.warn('Backend scenario notification (running in local simulation mode):', err);
      if (onScenarioChange) {
        onScenarioChange(scenarioId, selectedApproach);
      }
    } finally {
      setIsInjecting(false);
    }
  };

  const activeObj = SCENARIOS.find(s => s.id === activeScenario) || SCENARIOS[0];
  const aiFeedback = scenarioImpact || activeObj.impact;

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800/90 shadow-2xl space-y-4 relative overflow-hidden">
      {/* Specular Top Rim Highlight */}
      <div className="absolute top-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/25 to-transparent pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col 2xl:flex-row 2xl:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-start sm:items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shrink-0 mt-0.5 sm:mt-0">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-wide whitespace-nowrap">
                Traffic Scenario Injector
              </h2>
              <span className="whitespace-nowrap shrink-0 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_8px_rgba(6,182,212,0.15)]">
                AI Stress-Testing
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Inject real-time traffic anomalies and evaluate autonomous multi-agent adaptation
            </p>
          </div>
        </div>

        {/* Target Approach & Intensity Controls */}
        <div className="flex items-center flex-wrap gap-2.5 sm:gap-3 bg-slate-950/90 px-3.5 py-2 rounded-xl border border-slate-800 text-xs font-mono shrink-0 shadow-inner w-fit">
          <div className="flex items-center space-x-2">
            <span className="text-slate-400 text-[11px] whitespace-nowrap font-medium">Target:</span>
            <select
              value={selectedApproach}
              onChange={(e) => setSelectedApproach(e.target.value)}
              className="bg-slate-900 text-cyan-400 font-semibold border border-slate-700/80 rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-500 text-xs cursor-pointer hover:border-slate-600 transition-colors"
            >
              <option value="North">North (N-Bound)</option>
              <option value="South">South (S-Bound)</option>
              <option value="East">East (E-Bound)</option>
              <option value="West">West (W-Bound)</option>
            </select>
          </div>

          <div className="h-4 w-px bg-slate-800 shrink-0" />

          <div className="flex items-center space-x-2">
            <span className="text-slate-400 text-[11px] whitespace-nowrap font-medium">Surge:</span>
            <span className="text-amber-400 font-bold whitespace-nowrap min-w-[2.2rem]">{intensity}x</span>
            <input
              type="range"
              min="1.0"
              max="2.5"
              step="0.2"
              value={intensity}
              onChange={(e) => setIntensity(e.target.value)}
              className="w-16 sm:w-20 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 align-middle"
            />
          </div>
        </div>
      </div>

      {/* Scenario Presets Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {SCENARIOS.map((sc) => {
          const Icon = sc.icon;
          const isActive = (activeScenario || 'normal') === sc.id;

          return (
            <button
              key={sc.id}
              onClick={() => handleInject(sc.id)}
              disabled={isInjecting}
              className={`relative text-left p-3.5 rounded-xl border transition-all duration-200 flex flex-col justify-between group overflow-hidden ${
                isActive
                  ? `bg-gradient-to-br ${sc.color} ${sc.borderColor} ${sc.activeGlow} scale-[1.02]`
                  : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/40'
              }`}
            >
              {/* Active Glow Bar */}
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-cyan-400 animate-pulse"></div>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className={`p-2 rounded-lg ${isActive ? 'bg-black/30 text-white' : 'bg-slate-900 text-slate-300 group-hover:text-cyan-400'} transition`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  {isActive && (
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400"></span>
                    </span>
                  )}
                </div>

                <div>
                  <h3 className={`text-xs font-bold ${isActive ? 'text-white' : 'text-slate-200 group-hover:text-cyan-300'}`}>
                    {sc.label}
                  </h3>
                  <p className={`text-[11px] leading-tight mt-1 line-clamp-2 ${isActive ? 'text-slate-100' : 'text-slate-400'}`}>
                    {sc.description}
                  </p>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between text-[10px] font-mono">
                <span className={isActive ? 'text-white font-bold' : 'text-slate-500 group-hover:text-slate-400'}>
                  {isActive ? 'ACTIVE NOW' : 'Click to Inject'}
                </span>
                <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${sc.badge}`}>
                  {sc.id === 'normal' ? 'NOMINAL' : 'TEST'}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Live AI Adaptation & Impact Feedback Banner */}
      <div className="bg-slate-950/90 border border-cyan-500/30 rounded-xl p-3.5 flex flex-col xl:flex-row xl:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-start sm:items-center space-x-3 min-w-0 flex-1">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 shrink-0 mt-0.5 sm:mt-0">
            <Cpu className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
              <span className="text-slate-400 text-[11px] whitespace-nowrap shrink-0">Active Simulation State:</span>
              <strong className="text-cyan-300 font-bold uppercase tracking-wider whitespace-nowrap">{activeObj.label}</strong>
              <span className="text-slate-600 hidden sm:inline">•</span>
              <span className="text-emerald-400 flex items-center space-x-1 whitespace-nowrap shrink-0 text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span>AI Agents Synchronized</span>
              </span>
            </div>
            <p className="text-slate-300 text-[11px] mt-1 leading-snug">
              {aiFeedback || activeObj.impact}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0 self-start sm:self-auto pt-2 xl:pt-0 border-t border-slate-800/60 xl:border-t-0 w-full xl:w-auto justify-between xl:justify-end">
          <span className="text-[11px] text-slate-400 font-mono whitespace-nowrap">Real-time Telemetry:</span>
          <div className="flex items-center space-x-1.5">
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400 text-[11px] font-bold whitespace-nowrap">
              {overview?.level_of_service ? `LOS ${overview.level_of_service}` : 'LOS A'}
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-amber-300 text-[11px] font-bold whitespace-nowrap">
              {overview?.total_vehicle_count ? `${overview.total_vehicle_count} Veh` : '18 Veh'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
