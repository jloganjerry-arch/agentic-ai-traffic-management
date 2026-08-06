import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardShell } from './components/layout/DashboardShell';
import { OverviewGrid } from './components/overview/OverviewGrid';
import { SumoSimulationPanel } from './components/simulation/SumoSimulationPanel';
import { ApproachGrid } from './components/approach/ApproachGrid';
import { SignalGrid } from './components/signals/SignalGrid';
import { AgentPipelineFlow } from './components/agents/AgentPipelineFlow';
import { TrendChart } from './components/charts/TrendChart';
import { DatasetTable } from './components/dataset/DatasetTable';
import { HardwareGrid } from './components/hardware/HardwareGrid';
import { SystemLogPanel } from './components/logs/SystemLogPanel';
import { AIDecisionPanel } from './components/decision/AIDecisionPanel';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardShell>
        {/* Section 1: Overview Cards (8 primary metrics) */}
        <OverviewGrid />

        {/* Section 5: Multi-Agent Pipeline Status Flow */}
        <AgentPipelineFlow />

        {/* 12-Column Responsive Layout Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Section 2: SUMO Simulation Control Panel (Full Width) */}
          <div className="col-span-12">
            <SumoSimulationPanel />
          </div>

          {/* Section 3: Approach Analytics Breakdown */}
          <div className="col-span-12 lg:col-span-6">
            <ApproachGrid />
          </div>

          {/* Section 4: Signal Heads & Live Countdown Timers */}
          <div className="col-span-12 lg:col-span-6">
            <SignalGrid />
          </div>

          {/* Section 6: Historical Time-Series Trends */}
          <div className="col-span-12">
            <TrendChart />
          </div>

          {/* Section 7: Live TraCI Dataset V2.5 Preview */}
          <div className="col-span-12 xl:col-span-6">
            <DatasetTable />
          </div>

          {/* Section 8: Hardware Microcontrollers (ESP32) */}
          <div className="col-span-12 xl:col-span-6">
            <HardwareGrid />
          </div>

          {/* Section 10: Executive AI Supervisor Decision */}
          <div className="col-span-12 xl:col-span-6">
            <AIDecisionPanel />
          </div>

          {/* Section 9: Real-time Event Log Console */}
          <div className="col-span-12 xl:col-span-6">
            <SystemLogPanel />
          </div>
        </div>
      </DashboardShell>
    </QueryClientProvider>
  );
}
