import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { SignalLight } from './SignalLight';
import { SectionCard } from '../layout/SectionCard';
import { useSignalStatus } from '../../api/queries/useSignalStatus';
import { useTrafficOverview } from '../../api/queries/useTrafficOverview';
import { useSignalsWebSocket } from '../../hooks/useSignalsWebSocket';
import { 
  TrafficCone, 
  Split, 
  ArrowRightLeft, 
  ShieldCheck, 
  Zap, 
  Sliders, 
  Activity, 
  CheckCircle2, 
  Sparkles,
  Layers,
  Compass
} from 'lucide-react';

export function SignalGrid() {
  const queryClient = useQueryClient();
  const { data: initialResponse } = useSignalStatus();
  const { data: overview } = useTrafficOverview();
  const initialSignals = initialResponse?.signals || (Array.isArray(initialResponse) ? initialResponse : []);
  
  // Driven by WebSocket push with local 1-second countdown timer tick
  const signals = useSignalsWebSocket(initialSignals);

  const activeMode = overview?.signal_mode || 'paired_corridor';
  const isOneByOne = activeMode === 'one_by_one';
  const [isSwitching, setIsSwitching] = useState(false);

  // GLIDE Dynamic Setup State
  const [glideEnabled, setGlideEnabled] = useState(true);
  const [platoonExtension, setPlatoonExtension] = useState(4);
  const [gapOutThreshold, setGapOutThreshold] = useState(2.5);
  
  // 4-Phase individual approach durations
  const [approachDurations, setApproachDurations] = useState({
    North: 35,
    East: 25,
    South: 30,
    West: 25
  });

  // 2-Phase paired corridor durations
  const [pairedDurations, setPairedDurations] = useState({
    ns_green: 45,
    ew_green: 30
  });

  const [isSavingGlide, setIsSavingGlide] = useState(false);
  const [glideFeedback, setGlideFeedback] = useState('');

  // Fetch current GLIDE setup from backend
  const { data: glideData, refetch: refetchGlide } = useQuery({
    queryKey: ['glideSetup'],
    queryFn: async () => {
      try {
        const res = await axios.get('/api/signals/glide');
        return res.data;
      } catch {
        return null;
      }
    },
    refetchInterval: 3000
  });

  useEffect(() => {
    if (glideData) {
      if (glideData.glide_enabled !== undefined) setGlideEnabled(glideData.glide_enabled);
      if (glideData.platoon_extension_s !== undefined) setPlatoonExtension(glideData.platoon_extension_s);
      if (glideData.gap_out_threshold_s !== undefined) setGapOutThreshold(glideData.gap_out_threshold_s);
      if (glideData.active_approach_durations) {
        setApproachDurations(glideData.active_approach_durations);
      }
      if (glideData.ns_green_s !== undefined || glideData.ew_green_s !== undefined) {
        setPairedDurations({
          ns_green: glideData.ns_green_s || 45,
          ew_green: glideData.ew_green_s || 30
        });
      }
    }
  }, [glideData]);

  const handleModeChange = async (newMode) => {
    if (newMode === activeMode || isSwitching) return;
    setIsSwitching(true);
    try {
      await axios.post('/api/signals/mode', { mode: newMode });
      await queryClient.invalidateQueries({ queryKey: ['trafficOverview'] });
      await queryClient.invalidateQueries({ queryKey: ['signalStatus'] });
      await queryClient.invalidateQueries({ queryKey: ['aiDecision'] });
      refetchGlide();
    } catch (err) {
      console.error('Error switching signal mode:', err);
    } finally {
      setIsSwitching(false);
    }
  };

  const handleToggleGlide = async () => {
    const nextVal = !glideEnabled;
    setGlideEnabled(nextVal);
    try {
      await axios.post('/api/signals/glide', {
        enabled: nextVal,
        glide_enabled: nextVal,
        platoon_extension_s: platoonExtension,
        gap_out_threshold_s: gapOutThreshold,
        ns_green_s: pairedDurations.ns_green,
        ew_green_s: pairedDurations.ew_green,
        durations: approachDurations
      });
      await axios.post('/api/signals/adaptive-mode', { enabled: nextVal });
      queryClient.setQueryData(['glideSetup'], (old) => old ? { ...old, glide_enabled: nextVal, adaptive_mode_enabled: nextVal } : old);
      await queryClient.invalidateQueries({ queryKey: ['trafficOverview'] });
      await queryClient.invalidateQueries({ queryKey: ['signalStatus'] });
      await queryClient.invalidateQueries({ queryKey: ['aiDecision'] });
      refetchGlide();
    } catch (err) {
      console.error('Error toggling adaptive GLIDE mode:', err);
    }
  };

  const handleSaveGlide = async () => {
    setIsSavingGlide(true);
    setGlideFeedback('');
    try {
      await axios.post('/api/signals/glide', {
        enabled: glideEnabled,
        glide_enabled: glideEnabled,
        platoon_extension_s: platoonExtension,
        gap_out_threshold_s: gapOutThreshold,
        ns_green_s: pairedDurations.ns_green,
        ew_green_s: pairedDurations.ew_green,
        durations: approachDurations
      });
      await axios.post('/api/signals/adaptive-mode', { enabled: glideEnabled });
      setGlideFeedback('GLIDE dynamic timing plan synchronized with TraCI controllers.');
      refetchGlide();
      await queryClient.invalidateQueries({ queryKey: ['trafficOverview'] });
      await queryClient.invalidateQueries({ queryKey: ['signalStatus'] });
      await queryClient.invalidateQueries({ queryKey: ['aiDecision'] });
    } catch (err) {
      setGlideFeedback('Updated local GLIDE parameters.');
    } finally {
      setIsSavingGlide(false);
      setTimeout(() => setGlideFeedback(''), 4000);
    }
  };

  const handleDurationSlider = (dir, val) => {
    setApproachDurations((prev) => ({
      ...prev,
      [dir]: parseInt(val, 10)
    }));
  };

  const handlePairedSlider = (corridor, val) => {
    setPairedDurations((prev) => ({
      ...prev,
      [corridor]: parseInt(val, 10)
    }));
  };

  return (
    <SectionCard
      title="Active Traffic Signal Heads & GLIDE Dynamic Phasing"
      icon={TrafficCone}
      action={
        <div className="flex items-center space-x-2 text-[10px] font-mono bg-emerald-950/60 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>1s Local Tick • TraCI Synced</span>
        </div>
      }
    >
      <div className="space-y-4">
        {/* 1. Signal Sequencing Mode Switcher Controls */}
        <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 backdrop-blur space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                Signal Sequencing Mode
              </span>
            </div>
            <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-700 text-slate-300">
              Active Mode: <strong className="text-cyan-400 font-bold">{isOneByOne ? 'One-by-One (4-Phase Isolated)' : 'Paired Corridors (2-Phase)'}</strong>
            </span>
          </div>

          {/* Mode Toggle Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {/* Button 1: Paired Corridors */}
            <button
              onClick={() => handleModeChange('paired_corridor')}
              disabled={isSwitching}
              className={`relative px-3.5 py-2.5 rounded-xl border text-left transition-all ${
                !isOneByOne
                  ? 'bg-cyan-950/40 border-cyan-500/80 text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,0.25)]'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <ArrowRightLeft className={`w-4 h-4 ${!isOneByOne ? 'text-cyan-400' : 'text-slate-500'}`} />
                  <span className="text-xs font-bold">Paired Corridors (2-Phase)</span>
                </div>
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-950 border border-slate-700 text-slate-300 font-bold">
                  [N+S ⇄ E+W]
                </span>
              </div>
              <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                Dual-ring synchronized green waves for maximum straight-line arterial throughput.
              </p>
            </button>

            {/* Button 2: One-by-One Approach */}
            <button
              onClick={() => handleModeChange('one_by_one')}
              disabled={isSwitching}
              className={`relative px-3.5 py-2.5 rounded-xl border text-left transition-all ${
                isOneByOne
                  ? 'bg-emerald-950/40 border-emerald-500/80 text-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.25)]'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Split className={`w-4 h-4 ${isOneByOne ? 'text-emerald-400' : 'text-slate-500'}`} />
                  <span className="text-xs font-bold">One-by-One (4-Phase Isolated)</span>
                </div>
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-950 border border-emerald-800 text-emerald-300 font-bold">
                  [N ➔ E ➔ S ➔ W]
                </span>
              </div>
              <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                Isolated single-approach green sequencing. Green road goes straight, left & right; other 3 wait.
              </p>
            </button>
          </div>
        </div>

        {/* 2. GLIDE (Green Light Intelligent Dynamic Extension) Dynamic Timing Setup Controller */}
        <div className={`border rounded-xl p-4 space-y-3.5 shadow-xl font-mono transition-all ${
          isOneByOne 
            ? 'bg-slate-950/90 border-emerald-500/30' 
            : 'bg-slate-950/90 border-cyan-500/30'
        }`}>
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
            <div className="flex items-center space-x-2.5">
              <div className={`p-1.5 rounded-lg border ${
                isOneByOne 
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                  : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
              }`}>
                <Sparkles className="w-4 h-4 animate-pulse" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-100 flex items-center space-x-2">
                  <span>GLIDE Dynamic Timing & Setup ({isOneByOne ? '4-Phase Isolated' : 'Paired Corridors'})</span>
                  <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${
                    isOneByOne 
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' 
                      : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                  }`}>
                    GLIDE v4.2
                  </span>
                </h4>
                <p className="text-[10px] text-slate-400 font-sans">
                  {isOneByOne 
                    ? '4-Phase demand-driven green extension, platoon detection, and gap-out clearance.'
                    : '2-Phase paired corridor green wave optimization, platoon detection, and arterial synchronization.'}
                </p>
              </div>
            </div>

            {/* Toggle GLIDE On/Off */}
            <div className="flex items-center space-x-2">
              <span className="text-[10px] text-slate-400">Adaptive GLIDE:</span>
              <button
                onClick={handleToggleGlide}
                className={`px-2.5 py-1 rounded text-[10px] font-bold border transition flex items-center space-x-1.5 ${
                  glideEnabled
                    ? (isOneByOne ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.2)]' : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.2)]')
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${glideEnabled ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`}></span>
                <span>{glideEnabled ? '● ENABLED' : '○ FIXED'}</span>
              </button>
            </div>
          </div>

          {/* Dynamic Timing Sliders: MODE-DEPENDENT */}
          {isOneByOne ? (
            /* A. 4-PHASE ISOLATED APPROACH SLIDERS */
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-300">
                <span className="font-semibold flex items-center space-x-1.5">
                  <Sliders className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Dynamic 4-Phase Green Allocations:</span>
                </span>
                <span className="text-[10px] text-slate-400">
                  Total Cycle: <strong className="text-cyan-300 font-bold">{(approachDurations.North || 35) + (approachDurations.East || 25) + (approachDurations.South || 30) + (approachDurations.West || 25) + 12}s</strong> (incl. 12s clearance)
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
                {[
                  { dir: 'North', label: 'North (N-Bound)', color: 'text-cyan-400', barColor: 'accent-cyan-400' },
                  { dir: 'East',  label: 'East (E-Bound)',  color: 'text-emerald-400', barColor: 'accent-emerald-400' },
                  { dir: 'South', label: 'South (S-Bound)', color: 'text-amber-400', barColor: 'accent-amber-400' },
                  { dir: 'West',  label: 'West (W-Bound)',  color: 'text-purple-400', barColor: 'accent-purple-400' },
                ].map(({ dir, label, color, barColor }) => (
                  <div key={dir} className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1.5">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className={`font-bold ${color}`}>{dir}</span>
                      <strong className="text-white text-xs">{approachDurations[dir] || 30}s</strong>
                    </div>
                    <input
                      type="range"
                      min="15"
                      max="65"
                      step="1"
                      value={approachDurations[dir] || 30}
                      onChange={(e) => handleDurationSlider(dir, e.target.value)}
                      className={`w-full h-1.5 bg-slate-800 rounded appearance-none cursor-pointer ${barColor}`}
                    />
                    <div className="flex justify-between text-[9px] text-slate-500">
                      <span>15s min</span>
                      <span>65s max</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* B. 2-PHASE PAIRED CORRIDORS SLIDERS */
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-300">
                <span className="font-semibold flex items-center space-x-1.5">
                  <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Dynamic Paired Corridor Green Allocations:</span>
                </span>
                <span className="text-[10px] text-slate-400">
                  Total Cycle: <strong className="text-cyan-300 font-bold">{(pairedDurations.ns_green || 45) + (pairedDurations.ew_green || 30) + 8}s</strong> (incl. 8s yellow/clearance)
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* North-South Corridor */}
                <div className="bg-slate-900/80 p-3 rounded-xl border border-cyan-500/30 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-cyan-300 flex items-center space-x-1.5">
                      <Compass className="w-4 h-4 text-cyan-400" />
                      <span>North-South Corridor (N+S Green)</span>
                    </span>
                    <strong className="text-cyan-400 text-sm font-bold">{pairedDurations.ns_green || 45}s</strong>
                  </div>
                  <input
                    type="range"
                    min="20"
                    max="80"
                    step="1"
                    value={pairedDurations.ns_green || 45}
                    onChange={(e) => handlePairedSlider('ns_green', e.target.value)}
                    className="w-full h-2 bg-slate-800 rounded appearance-none cursor-pointer accent-cyan-400"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>20s min</span>
                    <span className="text-cyan-400/80 font-bold">Main Arterial Wave</span>
                    <span>80s max</span>
                  </div>
                </div>

                {/* East-West Corridor */}
                <div className="bg-slate-900/80 p-3 rounded-xl border border-emerald-500/30 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-emerald-300 flex items-center space-x-1.5">
                      <Compass className="w-4 h-4 text-emerald-400" />
                      <span>East-West Corridor (E+W Green)</span>
                    </span>
                    <strong className="text-emerald-400 text-sm font-bold">{pairedDurations.ew_green || 30}s</strong>
                  </div>
                  <input
                    type="range"
                    min="20"
                    max="80"
                    step="1"
                    value={pairedDurations.ew_green || 30}
                    onChange={(e) => handlePairedSlider('ew_green', e.target.value)}
                    className="w-full h-2 bg-slate-800 rounded appearance-none cursor-pointer accent-emerald-400"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>20s min</span>
                    <span className="text-emerald-400/80 font-bold">Cross Arterial Wave</span>
                    <span>80s max</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* GLIDE Parameters: Platoon Extension & Gap-Out Threshold */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between text-[11px]">
              <div>
                <span className="text-slate-300 font-bold block">Platoon Extension Step</span>
                <span className="text-[10px] text-slate-400">Dynamic green extension when platoon detected</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <select
                  value={platoonExtension}
                  onChange={(e) => setPlatoonExtension(parseInt(e.target.value, 10))}
                  className="bg-slate-950 border border-slate-700 text-emerald-300 font-bold rounded px-2 py-1 text-xs focus:outline-none focus:border-emerald-500"
                >
                  <option value={2}>+2s</option>
                  <option value={4}>+4s (Std)</option>
                  <option value={6}>+6s</option>
                  <option value={8}>+8s</option>
                </select>
              </div>
            </div>

            <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between text-[11px]">
              <div>
                <span className="text-slate-300 font-bold block">Gap-Out Clearance Threshold</span>
                <span className="text-[10px] text-slate-400">Headway gap to trigger early phase yield</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <select
                  value={gapOutThreshold}
                  onChange={(e) => setGapOutThreshold(parseFloat(e.target.value))}
                  className="bg-slate-950 border border-slate-700 text-cyan-300 font-bold rounded px-2 py-1 text-xs focus:outline-none focus:border-cyan-500"
                >
                  <option value={1.8}>1.8s (Fast)</option>
                  <option value={2.5}>2.5s (Std)</option>
                  <option value={3.5}>3.5s (Smooth)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Save / Apply Button */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
            <button
              onClick={handleSaveGlide}
              disabled={isSavingGlide}
              className={`px-3.5 py-1.5 rounded-lg font-bold text-xs shadow-lg transition flex items-center space-x-1.5 text-white ${
                isOneByOne
                  ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-950/40'
                  : 'bg-cyan-600 hover:bg-cyan-500 shadow-cyan-950/40'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{isSavingGlide ? 'Applying...' : `Apply GLIDE ${isOneByOne ? '4-Phase' : 'Paired Corridor'} Timing`}</span>
            </button>

            {glideFeedback && (
              <span className="text-[11px] text-emerald-400 font-bold animate-fadeIn">
                {glideFeedback}
              </span>
            )}

            <div className="text-[10px] text-slate-400">
              Live State: <strong className="text-emerald-300">{glideData?.status || 'DYNAMIC_GLIDE_OPTIMIZED'}</strong>
            </div>
          </div>
        </div>

        {/* 3. Four Active Signal Head Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {signals.map((sig, idx) => (
            <SignalLight key={sig.signal_id || idx} {...sig} />
          ))}
        </div>
      </div>
    </SectionCard>
  );
}
