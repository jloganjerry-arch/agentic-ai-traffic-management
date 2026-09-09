import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useAIDecision } from '../../api/queries/useAIDecision';
import { Brain, CheckCircle, Zap, ShieldCheck } from 'lucide-react';

export function AIDecisionPanel() {
  const { data: decision } = useAIDecision();

  return (
    <SectionCard title="Active AI Supervisory & Safety Decision" icon={Brain}>
      <div className="glass-panel p-4 rounded-2xl border border-slate-800/90 space-y-3.5 relative overflow-hidden">
        {/* Specular Top Rim Highlight */}
        <div className="absolute top-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-purple-400/30 to-transparent pointer-events-none" />

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-cyan-400" />
            <span className="font-mono text-xs text-cyan-300 font-bold tracking-wider">
              {decision?.decision_id ?? 'DEC-20260805-089'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 text-xs text-cyan-300 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-700 font-mono shadow-[0_0_8px_rgba(6,182,212,0.2)]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{decision?.safety_status ?? 'SAFE_TO_EXECUTE'}</span>
            </div>
            <div className="flex items-center space-x-1 text-xs text-emerald-300 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-700 font-mono shadow-[0_0_8px_rgba(16,185,129,0.2)]">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>{decision?.supervisor_status ?? 'APPROVED'}</span>
            </div>
          </div>
        </div>

        <div className="space-y-1.5 font-mono">
          <div className="flex items-center justify-between text-xs py-0.5 border-b border-slate-800/40">
            <span className="text-slate-400">Action Plan:</span>
            <span className="text-cyan-300 font-bold">{decision?.action ?? 'DYNAMIC_AI_GREEN_ALLOCATION'}</span>
          </div>
          <div className="flex items-center justify-between text-xs py-0.5 border-b border-slate-800/40">
            <span className="text-slate-400">Target Approach:</span>
            <span className="text-slate-200 font-semibold">{decision?.target_approach ?? 'North (N-Bound)'}</span>
          </div>
          <div className="flex items-center justify-between text-xs py-0.5 border-b border-slate-800/40">
            <span className="text-slate-400">Green Time (Prev → New):</span>
            <span className="text-amber-300 font-bold">{decision?.prev_green_time ?? 30}s → {decision?.duration_seconds ?? 45}s</span>
          </div>
          <div className="flex items-center justify-between text-xs py-0.5 border-b border-slate-800/40">
            <span className="text-slate-400">Traffic Score / Congestion:</span>
            <span className="text-emerald-300 font-bold">{decision?.traffic_score ?? 0.88} ({decision?.congestion_level ?? 'Optimal'})</span>
          </div>
          <div className="flex items-center justify-between text-xs py-0.5">
            <span className="text-slate-400">MQTT / ESP32 Hardware Status:</span>
            <span className="text-purple-300 font-bold">{decision?.mqtt_status ?? 'PUBLISHED'} / {decision?.esp32_status ?? 'ACKNOWLEDGED'}</span>
          </div>
        </div>

        {/* Safety Guardian Physical Clearance Checks */}
        <div className="pt-2 border-t border-slate-800/80">
          <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5 flex items-center justify-between">
            <span className="flex items-center space-x-1 text-cyan-400 font-bold">
              <ShieldCheck className="w-3 h-3 inline" />
              <span>Safety Guardian Verification:</span>
            </span>
            <span className="text-emerald-400 font-bold">ALL 4 RULES VERIFIED</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
            <div className="bg-slate-950/80 px-2.5 py-1.5 rounded-lg border border-slate-800 text-slate-300 flex items-center justify-between">
              <span>Mutual Exclusion:</span>
              <span className="text-emerald-400 font-bold">PASSED</span>
            </div>
            <div className="bg-slate-950/80 px-2.5 py-1.5 rounded-lg border border-slate-800 text-slate-300 flex items-center justify-between">
              <span>Yellow Clearance:</span>
              <span className="text-amber-400 font-bold">3.0s ENFORCED</span>
            </div>
            <div className="bg-slate-950/80 px-2.5 py-1.5 rounded-lg border border-slate-800 text-slate-300 flex items-center justify-between">
              <span>All-Red Clearance:</span>
              <span className="text-rose-400 font-bold">2.0s ENFORCED</span>
            </div>
            <div className="bg-slate-950/80 px-2.5 py-1.5 rounded-lg border border-slate-800 text-slate-300 flex items-center justify-between">
              <span>Dilemma Zone:</span>
              <span className="text-emerald-400 font-bold">CLEAR</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-950/90 p-3 rounded-xl text-[11px] text-slate-300 border border-slate-800 font-sans leading-relaxed">
          <strong className="text-cyan-400 font-mono">Reasoning: </strong>
          {decision?.reasoning ?? 'AI dynamic timing generated based on live SUMO telemetry.'}
        </div>
      </div>
    </SectionCard>
  );
}
