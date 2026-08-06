import { Eye, LineChart, Sliders, ShieldAlert } from 'lucide-react';

export const AGENT_METADATA = {
  'agent-1': {
    name: 'Traffic Monitoring Agent',
    icon: Eye,
    description: 'Ingests raw telemetry from SUMO/Vision providers & computes real-time approach stats.',
  },
  'agent-2': {
    name: 'Traffic Analysis Agent',
    icon: LineChart,
    description: 'Analyzes density, vehicle queue trends & predicts bottleneck spots.',
  },
  'agent-3': {
    name: 'Signal Optimization Agent',
    icon: Sliders,
    description: 'Generates optimal split-time proposals for intersection signal heads.',
  },
  'agent-4': {
    name: 'Supervisor Agent',
    icon: ShieldAlert,
    description: 'Enforces hard safety constraints, validates timings & dispatches hardware signals.',
  },
};
