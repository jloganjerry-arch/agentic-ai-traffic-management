import React from 'react';

export function HardwareStatusRow({ node_id, role, status, latency_ms, firmware, publish_topic, gpio_states, last_ack_time }) {
  return (
    <div className="glass-panel p-3 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
      <div className="flex items-center space-x-3">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
        <div>
          <span className="font-mono font-bold text-slate-200">{node_id}</span>
          <span className="text-slate-400 block text-[10px]">{role} • <span className="text-cyan-400 font-mono">{gpio_states || 'GPIO 18: HIGH'}</span></span>
        </div>
      </div>

      <div className="flex items-center space-x-4 font-mono text-[11px]">
        <span className="text-slate-400 hidden sm:inline">{publish_topic || 'traffic/signals'}</span>
        <span className="text-cyan-400">{latency_ms}ms ACK</span>
        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 text-[10px] border border-emerald-800">
          {status}
        </span>
      </div>
    </div>
  );
}
