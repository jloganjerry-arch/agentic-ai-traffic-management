import { Eye, LineChart, Sliders, ShieldAlert, ShieldCheck } from 'lucide-react';

export const AGENT_METADATA = {
  'agent-1': {
    name: 'Traffic Monitoring Agent',
    alias: 'Sentinel',
    icon: Eye,
    description: 'Ingests raw telemetry from SUMO/Vision providers & computes real-time approach stats.',
  },
  'agent-2': {
    name: 'Traffic Analysis Agent',
    alias: 'Detective',
    icon: LineChart,
    description: 'Analyzes density, vehicle queue trends & predicts Level of Service (LOS A-F).',
  },
  'agent-3': {
    name: 'Signal Optimization Agent',
    alias: 'Mastermind',
    icon: Sliders,
    description: 'Generates optimal split-time proposals using multi-factor weighted scoring (15s-75s).',
  },
  'agent-4': {
    name: 'Supervisor Agent',
    alias: 'Commander',
    icon: ShieldAlert,
    description: 'Enforces policy bounds (10s-90s), starvation prevention & emergency overrides.',
  },
  'agent-5': {
    name: 'Traffic Safety Agent',
    alias: 'Safety Guardian',
    icon: ShieldCheck,
    description: 'Validates physical stopping distances, dilemma zones, clearance & mutual exclusion.',
  },
};

