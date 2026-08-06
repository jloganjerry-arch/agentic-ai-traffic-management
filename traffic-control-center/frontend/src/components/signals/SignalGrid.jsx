import React from 'react';
import { SignalLight } from './SignalLight';
import { SectionCard } from '../layout/SectionCard';
import { useSignalStatus } from '../../api/queries/useSignalStatus';
import { useSignalsWebSocket } from '../../hooks/useSignalsWebSocket';
import { TrafficCone } from 'lucide-react';

export function SignalGrid() {
  const { data: initialResponse } = useSignalStatus();
  const initialSignals = initialResponse?.signals || (Array.isArray(initialResponse) ? initialResponse : []);
  
  // Driven by WebSocket push with local 1-second countdown timer tick
  const signals = useSignalsWebSocket(initialSignals);

  return (
    <SectionCard
      title="Active Traffic Signal Heads (WS-Synced)"
      icon={TrafficCone}
      action={
        <div className="flex items-center space-x-2 text-[10px] font-mono bg-emerald-950/60 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>1s Local Tick</span>
        </div>
      }
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {signals.map((sig, idx) => (
          <SignalLight key={sig.signal_id || idx} {...sig} />
        ))}
      </div>
    </SectionCard>
  );
}
