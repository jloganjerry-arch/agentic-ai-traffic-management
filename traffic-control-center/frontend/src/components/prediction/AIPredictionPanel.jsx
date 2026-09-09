import React, { useState } from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useAIPredictions } from '../../api/queries/useAIPredictions';
import { TrendingUp, Clock, AlertTriangle, ShieldCheck, Zap, Gauge, Sparkles } from 'lucide-react';

export function AIPredictionPanel() {
  const { data: predictionsData, isLoading } = useAIPredictions();
  const [selectedHorizon, setSelectedHorizon] = useState(15);

  const horizons = predictionsData?.horizons ?? {};
  const currentPrediction = horizons[`horizon_${selectedHorizon}m`] ?? {
    horizon_minutes: selectedHorizon,
    target_time: '--:--:--',
    projected_vehicle_count: 42,
    projected_avg_speed_kmh: 28.5,
    projected_queue_length_m: 18.4,
    projected_density_veh_km: 22.0,
    projected_congestion_level: 'Moderate',
    projected_level_of_service: 'C',
    bottleneck_risk_score: 38,
    primary_risk_approach: 'North (N-Bound)',
    confidence: 0.92,
    action_code: 'ADAPTIVE_SPLIT_BALANCING',
    ai_recommendation: 'Enable adaptive phase balancing for N-S and E-W corridors.'
  };

  const getStatusBadge = (level) => {
    switch (level) {
      case 'Congested':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: AlertTriangle,
          label: 'SEVERE BOTTLENECK PREDICTED'
        };
      case 'Moderate':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: Gauge,
          label: 'MODERATE CONGESTION BUILDUP'
        };
      default:
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: ShieldCheck,
          label: 'OPTIMAL FLOW EXPECTED'
        };
    }
  };

  const statusInfo = getStatusBadge(currentPrediction.projected_congestion_level);
  const StatusIcon = statusInfo.icon;

  return (
    <SectionCard title="AI Congestion Prediction Engine" icon={TrendingUp}>
      <div className="space-y-4">
        {/* Header & Horizon Time Tabs */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-950/80 p-3 rounded-2xl border border-slate-800/90 shadow-inner">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
            <span className="text-xs font-bold text-slate-200 font-mono uppercase tracking-wider">Forecast Horizon:</span>
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            {[15, 30, 60].map((mins) => {
              const active = selectedHorizon === mins;
              return (
                <button
                  key={mins}
                  onClick={() => setSelectedHorizon(mins)}
                  className={`flex-1 sm:flex-none flex items-center justify-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold font-mono transition-all duration-200 cursor-pointer ${
                    active
                      ? 'bg-gradient-to-r from-cyan-950 to-blue-900 text-cyan-200 border border-cyan-500/80 shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                      : 'bg-slate-900/90 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800'
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>+{mins} Min</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Prediction Main Grid */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/90 space-y-4 relative overflow-hidden">
          {/* Specular Top Rim Highlight */}
          <div className="absolute top-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/25 to-transparent pointer-events-none" />

          {/* Top Status & Risk Gauge Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2.5">
              <div className={`flex items-center space-x-1.5 text-xs font-mono font-bold px-3 py-1 rounded-full border shadow-sm ${statusInfo.bg}`}>
                <StatusIcon className="w-3.5 h-3.5" />
                <span>{statusInfo.label}</span>
              </div>
              <span className="text-[11px] font-mono text-slate-400">
                Target: <strong className="text-slate-200">{currentPrediction.target_time}</strong>
              </span>
            </div>

            {/* Risk Score Indicator */}
            <div className="flex items-center space-x-2.5 bg-slate-950/90 px-3.5 py-1.5 rounded-xl border border-slate-800 shadow-inner">
              <span className="text-[11px] text-slate-400 font-semibold font-mono uppercase tracking-wider">Bottleneck Risk:</span>
              <div className="flex items-center space-x-2">
                <span className={`text-xs font-mono font-black ${
                  currentPrediction.bottleneck_risk_score > 60 ? 'text-rose-400' :
                  currentPrediction.bottleneck_risk_score > 30 ? 'text-amber-400' : 'text-emerald-400'
                }`}>
                  {currentPrediction.bottleneck_risk_score}%
                </span>
                <div className="w-16 h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 shadow-sm ${
                      currentPrediction.bottleneck_risk_score > 60 ? 'bg-rose-500 shadow-[0_0_8px_#f43f5e]' :
                      currentPrediction.bottleneck_risk_score > 30 ? 'bg-amber-500 shadow-[0_0_8px_#f59e0b]' : 'bg-emerald-500 shadow-[0_0_8px_#10b981]'
                    }`}
                    style={{ width: `${currentPrediction.bottleneck_risk_score}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Projected Telemetry Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold font-mono">Predicted Volume</span>
              <div className="text-lg font-mono font-bold text-cyan-300 mt-1">
                {currentPrediction.projected_vehicle_count} <span className="text-[10px] text-slate-400 font-normal">veh</span>
              </div>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold font-mono">Projected Avg Speed</span>
              <div className="text-lg font-mono font-bold text-emerald-300 mt-1">
                {currentPrediction.projected_avg_speed_kmh} <span className="text-[10px] text-slate-400 font-normal">km/h</span>
              </div>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold font-mono">Projected Queue</span>
              <div className="text-lg font-mono font-bold text-amber-300 mt-1">
                {currentPrediction.projected_queue_length_m} <span className="text-[10px] text-slate-400 font-normal">m</span>
              </div>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold font-mono">Level of Service</span>
              <div className="flex items-center justify-between mt-1">
                <span className="text-lg font-mono font-bold text-purple-300">
                  Grade {currentPrediction.projected_level_of_service}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {(currentPrediction.confidence * 100).toFixed(0)}% Conf.
                </span>
              </div>
            </div>
          </div>

          {/* Risk Focus & AI Strategy Recommendation */}
          <div className="bg-slate-950/90 p-3.5 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400 font-semibold">Primary Bottleneck Focus:</span>
              <span className="text-rose-400 font-bold bg-rose-950/50 px-2 py-0.5 rounded border border-rose-900/60">{currentPrediction.primary_risk_approach}</span>
            </div>

            <div className="flex items-start space-x-2.5 pt-2 border-t border-slate-800/80">
              <Zap className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div className="text-xs text-slate-300 leading-relaxed font-sans">
                <span className="text-cyan-400 font-bold font-mono">AI Recommended Action: </span>
                {currentPrediction.ai_recommendation}
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
