import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { AgentCard } from './AgentCard';
import { AGENT_METADATA } from './agentConfig';
import { useAgentStatus } from '../../api/queries/useAgentStatus';
import { Cpu, ArrowRight } from 'lucide-react';

export function AgentPipelineFlow() {
  const { data: responseData } = useAgentStatus();
  const agents = responseData?.agents || (Array.isArray(responseData) ? responseData : []);
  const pipelineStage = responseData?.pipeline_stage || 'SUPERVISORY_EXECUTION';

  return (
    <SectionCard
      title="Multi-Agent Pipeline Architecture"
      icon={Cpu}
      action={
        <div className="flex items-center space-x-2 text-[10px] font-mono bg-indigo-950/60 text-indigo-300 px-2.5 py-0.5 rounded border border-indigo-800">
          <span>Stage: {pipelineStage}</span>
        </div>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
        {agents.map((agent, idx) => {
          const meta = AGENT_METADATA[agent.id] || {};
          return (
            <div key={agent.id || idx} className="relative">
              <AgentCard
                {...agent}
                icon={meta.icon}
                description={meta.description}
              />
              {idx < agents.length - 1 && (
                <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 p-1 rounded-full bg-slate-900 border border-slate-700 text-cyan-400">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}
