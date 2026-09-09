import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { AgentCard } from './AgentCard';
import { AGENT_METADATA } from './agentConfig';
import { useAgentStatus } from '../../api/queries/useAgentStatus';
import { Cpu, ArrowRight } from 'lucide-react';

export function AgentPipelineFlow() {
  const { data: responseData } = useAgentStatus();
  const agents = responseData?.agents || (Array.isArray(responseData) ? responseData : []);
  const displayAgents = agents.length > 0 ? agents : [
    { id: 'agent-1', name: 'Traffic Monitoring Agent', role: 'Telemetry Ingestion', status: 'ACTIVE', latency_ms: 5, task: 'Reading SUMO Telemetry', stage: 'Monitoring' },
    { id: 'agent-2', name: 'Traffic Analysis Agent', role: 'Congestion Analytics', status: 'ACTIVE', latency_ms: 8, task: 'Calculating Density & LOS', stage: 'Analysis' },
    { id: 'agent-3', name: 'Signal Optimization Agent', role: 'Timing Plan Generator', status: 'ACTIVE', latency_ms: 12, task: 'Computing Green Duration', stage: 'Optimization' },
    { id: 'agent-4', name: 'Supervisor Agent', role: 'Policy & Fairness', status: 'ACTIVE', latency_ms: 4, task: 'Validating Policy Constraints', stage: 'Supervisor' },
    { id: 'agent-5', name: 'Traffic Safety Agent', role: 'Physical Clearance Gatekeeper', status: 'ACTIVE', latency_ms: 3, task: 'Dilemma Zone & Collision Verification', stage: 'Safety' },
  ];

  return (
    <SectionCard
      title="Multi-Agent Pipeline Architecture"
      icon={Cpu}
      action={
        <div className="flex items-center space-x-2 text-[10px] font-mono bg-purple-950/60 text-purple-300 px-3 py-1 rounded-lg border border-purple-800/80 shadow-[0_0_12px_rgba(168,85,247,0.15)]">
          <span className="w-2 h-2 rounded-full bg-purple-400" />
          <span>Active Architecture: 5-Agent Collaborative Pipeline</span>
        </div>
      }
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 relative">
        {displayAgents.map((agent, idx) => {
          const meta = AGENT_METADATA[agent.id] || {};
          return (
            <div key={agent.id || idx} className="relative">
              <AgentCard
                {...agent}
                alias={meta.alias}
                icon={meta.icon}
                description={meta.description}
              />
              {idx < displayAgents.length - 1 && (
                <div className="hidden lg:flex absolute -right-2.5 top-1/2 -translate-y-1/2 z-20 p-1 rounded-full bg-slate-950 border border-cyan-500/40 text-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.3)]">
                  <ArrowRight className="w-3 h-3" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}
