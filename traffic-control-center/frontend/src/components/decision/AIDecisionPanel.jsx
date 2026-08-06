import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useAIDecision } from '../../api/queries/useAIDecision';
import { Brain, CheckCircle, Zap } from 'lucide-react';

export function AIDecisionPanel() {
  const { data: decision } = useAIDecision();

  return (
    <SectionCard title="Active AI Supervisory Decision" icon={Brain}>
      <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-cyan-400" />
            <span className="font-mono text-xs text-slate-300 font-semibold">
              {decision?.decision_id ?? 'DEC-20260805-089'}
            </span>
          </div>
          <div className="flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/60 px-2.5 py-0.5 rounded border border-emerald-800 font-mono">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{decision?.supervisor_status ?? 'APPROVED'}</span>
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Action Plan:</span>
            <span className="font-mono text-cyan-400 font-semibold">{decision?.action ?? 'DYNAMIC_AI_GREEN_ALLOCATION'}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Target Approach:</span>
            <span className="text-slate-200">{decision?.target_approach ?? 'North (N-Bound)'}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Green Time (Prev → New):</span>
            <span className="font-mono text-amber-400 font-semibold">{decision?.prev_green_time ?? 30}s → {decision?.duration_seconds ?? 45}s</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Traffic Score / Congestion:</span>
            <span className="font-mono text-emerald-400 font-semibold">{decision?.traffic_score ?? 0.88} ({decision?.congestion_level ?? 'Optimal'})</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">MQTT / ESP32 Status:</span>
            <span className="font-mono text-indigo-400 font-semibold">{decision?.mqtt_status ?? 'PUBLISHED'} / {decision?.esp32_status ?? 'ACKNOWLEDGED'}</span>
          </div>
        </div>

        <div className="bg-slate-950 p-2.5 rounded text-[11px] text-slate-300 border border-slate-800/80 leading-relaxed">
          <span className="text-slate-400 font-semibold">Reasoning: </span>
          {decision?.reasoning ?? 'AI dynamic timing generated based on live SUMO telemetry.'}
        </div>
      </div>
    </SectionCard>
  );
}
